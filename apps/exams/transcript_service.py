import datetime
from decimal import Decimal
from django.db.models import Q
from django.core.exceptions import ValidationError

from apps.students.models import Student, Enrollment
from apps.exams.models import Exam, ExamResult, GradeConfig
from apps.academics.models import Subject
from apps.attendance.services import AttendanceService
from apps.students.services import EnrollmentService
from apps.exams.services import _get_grade_for_percentage


def generate_student_transcript(student_id):
    """Generate structured transcript data for a student in their active/latest session."""
    student = Student.objects.filter(pk=student_id).first()
    if not student:
        raise ValidationError("Student not found.")

    # Find student's active enrollment session
    enrollment = Enrollment.objects.filter(student_id=student_id, status="Active").first()
    if not enrollment:
        # Fallback to latest enrollment
        enrollment = Enrollment.objects.filter(student_id=student_id).order_by("-registration_date").first()

    from apps.achievements.models import Achievement
    achievements_qs = Achievement.objects.filter(student_id=student_id)
    ach_list = []
    for ach in achievements_qs:
        ach_list.append({
            "exam_type": ach.exam_type,
            "year": ach.year,
            "rank": ach.rank,
        })

    if not enrollment:
        return {
            "student_id": student.id,
            "student_name": student.full_name,
            "roll_number": student.roll_number,
            "session_name": "No Active Session",
            "session_id": None,
            "subject_results": [],
            "overall_obtained_marks": Decimal("0.00"),
            "overall_total_marks": Decimal("0.00"),
            "overall_percentage": Decimal("0.00"),
            "overall_grade": "F",
            "overall_result": "Fail",
            "gpa": Decimal("0.00"),
            "rank": 1,
            "attendance_percentage": Decimal("0.00"),
            "academic_score": Decimal("0.00"),
            "achievements": ach_list,
        }

    session = enrollment.session

    # Fetch all published exams for this session
    published_exams = Exam.objects.filter(session=session, status="Published")

    # Fetch all subjects for this session
    subjects = Subject.objects.filter(Q(session=session) | Q(session__isnull=True), is_active=True)

    # Let's group exams by subject
    subject_results = []
    total_obtained_marks = Decimal("0.00")
    total_max_marks = Decimal("0.00")

    # We only care about subjects that have published exams
    for subject in subjects:
        subject_exams = published_exams.filter(subject=subject)
        if not subject_exams.exists():
            continue

        # Get results for this student
        student_results = ExamResult.objects.filter(student_id=student_id, exam__in=subject_exams)

        obtained_sum = Decimal("0.00")
        total_sum = Decimal("0.00")
        exams_data = []

        for res in student_results:
            exams_data.append({
                "exam_id": res.exam.id,
                "exam_name": res.exam.name,
                "exam_type": res.exam.exam_type,
                "marks_obtained": res.marks_obtained,
                "total_marks": res.exam.total_marks,
                "percentage": res.percentage,
                "grade": res.grade,
                "rank": res.rank,
                "is_absent": res.is_absent,
                "remarks": res.remarks
            })
            if not res.is_absent:
                obtained_sum += res.marks_obtained
            total_sum += res.exam.total_marks

        if total_sum > 0:
            subject_percentage = (obtained_sum / total_sum * Decimal("100")).quantize(Decimal("0.01"))
            subject_grade = _get_grade_for_percentage(session, subject_percentage)

            # Resolve grade point
            grade_cfg = GradeConfig.objects.filter(
                session=session,
                grade_name=subject_grade
            ).first()
            if not grade_cfg:
                grade_cfg = GradeConfig.objects.filter(
                    session__isnull=True,
                    grade_name=subject_grade
                ).first()

            grade_point = grade_cfg.grade_point if grade_cfg else Decimal("0.00")
        else:
            subject_percentage = Decimal("0.00")
            subject_grade = "F"
            grade_point = Decimal("0.00")

        total_obtained_marks += obtained_sum
        total_max_marks += total_sum

        subject_results.append({
            "subject_id": subject.id,
            "subject_name": subject.name,
            "subject_code": subject.code,
            "obtained_marks": obtained_sum,
            "total_marks": total_sum,
            "percentage": subject_percentage,
            "grade": subject_grade,
            "grade_point": grade_point,
            "exams": exams_data
        })

    # Overall percentage
    if total_max_marks > 0:
        overall_percentage = (total_obtained_marks / total_max_marks * Decimal("100")).quantize(Decimal("0.01"))
    else:
        overall_percentage = Decimal("0.00")

    overall_grade = _get_grade_for_percentage(session, overall_percentage)
    overall_result = "Pass" if overall_percentage >= Decimal("50.00") else "Fail"

    # GPA Calculation (average of subject grade points)
    valid_grade_points = [s["grade_point"] for s in subject_results if s["grade_point"] is not None]
    if valid_grade_points:
        gpa = (sum(valid_grade_points) / len(valid_grade_points)).quantize(Decimal("0.01"))
    else:
        gpa = Decimal("0.00")

    # Attendance
    attendance_pct = AttendanceService.calculate_attendance_percentage(student_id, session.id)
    if attendance_pct is None:
        attendance_display = Decimal("100.00")
    else:
        attendance_display = Decimal(attendance_pct).quantize(Decimal("0.01"))

    # Academic score
    academic_score = EnrollmentService.calculate_academic_score(student_id, session.id)

    # Rank Calculation
    # Fetch all active students in the session and rank them based on overall percentage of published exams
    active_enrollments = Enrollment.objects.filter(session=session, status="Active")
    student_percentages = []

    for enroll in active_enrollments:
        student_res = ExamResult.objects.filter(student_id=enroll.student_id, exam__in=published_exams)
        s_obtained = Decimal("0.00")
        s_total = Decimal("0.00")
        for r in student_res:
            if not r.is_absent:
                s_obtained += r.marks_obtained
            s_total += r.exam.total_marks

        s_percentage = (s_obtained / s_total * Decimal("100")).quantize(Decimal("0.01")) if s_total > 0 else Decimal("0.00")
        student_percentages.append((enroll.student_id, s_percentage))

    # Sort students by percentage descending (competition ranking)
    student_percentages.sort(key=lambda x: x[1], reverse=True)

    current_rank = 1
    last_pct = None
    ranks_map = {}
    for index, (s_id, pct) in enumerate(student_percentages):
        if last_pct is not None and pct < last_pct:
            current_rank = index + 1
        ranks_map[s_id] = current_rank
        last_pct = pct

    rank = ranks_map.get(student_id, 1)

    return {
        "student_id": student.id,
        "student_name": student.full_name,
        "roll_number": student.roll_number,
        "session_name": session.name,
        "session_id": session.id,
        "subject_results": subject_results,
        "overall_obtained_marks": total_obtained_marks,
        "overall_total_marks": total_max_marks,
        "overall_percentage": overall_percentage,
        "overall_grade": overall_grade,
        "overall_result": overall_result,
        "gpa": gpa,
        "rank": rank,
        "attendance_percentage": attendance_display,
        "academic_score": academic_score,
        "achievements": ach_list,
    }
