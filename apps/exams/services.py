import datetime
from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Count, Avg, Max, Min
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404

from apps.academics.models import Session, Subject, TeacherAssignment
from apps.students.models import Student, Enrollment
from apps.exams.models import Exam, ExamResult, GradeConfig


def _validate_teacher_scope(user, exam=None, session_id=None, subject_id=None):
    """Ensure teachers can only act on exams/subjects they are assigned to.

    Admins and Principals bypass these checks.
    """
    if user.is_superuser:
        return
    if user.groups.filter(name__in=["Admin", "Principal"]).exists():
        return

    if not user.groups.filter(name="Teacher").exists():
        raise Http404("Access denied: Not a teacher.")

    if exam is not None:
        if isinstance(exam, (int, str)):
            try:
                exam = Exam.objects.get(pk=exam)
            except Exam.DoesNotExist:
                raise Http404("Exam not found.")
        session_id = exam.session_id
        subject_id = exam.subject_id

    if session_id is None:
        raise Http404("Session is required for teacher scope verification.")

    query = Q(teacher=user, session_id=session_id, is_active=True)
    if subject_id is not None:
        query &= Q(subject_id=subject_id)

    has_assignment = TeacherAssignment.objects.filter(query).exists()
    if not has_assignment:
        raise Http404("Access denied: No active teacher assignment for this session and subject.")


def _get_grade_for_percentage(session, percentage):
    """Retrieve the correct grade from GradeConfig boundaries.

    Checks for overlapping grade ranges and raises ValidationError if detected.
    """
    # Check for overlapping ranges for the active session
    if session:
        session_configs = list(GradeConfig.objects.filter(session=session).order_by("min_percentage"))
        for i in range(len(session_configs) - 1):
            if session_configs[i].max_percentage >= session_configs[i+1].min_percentage:
                raise ValidationError("Overlapping grade ranges detected for this session.")

    # Check for overlapping global ranges
    global_configs = list(GradeConfig.objects.filter(session__isnull=True).order_by("min_percentage"))
    for i in range(len(global_configs) - 1):
        if global_configs[i].max_percentage >= global_configs[i+1].min_percentage:
            raise ValidationError("Overlapping global grade ranges detected.")

    config = None
    if session:
        config = GradeConfig.objects.filter(
            session=session,
            min_percentage__lte=percentage,
            max_percentage__gte=percentage
        ).first()

    if not config:
        config = GradeConfig.objects.filter(
            session__isnull=True,
            min_percentage__lte=percentage,
            max_percentage__gte=percentage
        ).first()

    return config.grade_name if config else "F"


def _recalculate_exam_ranking(exam):
    """Compute and update competition ranks (1,1,3) for present students.

    Absent students are excluded from the ranking calculation and their rank is set to None.
    This is executed inside a transaction.
    """
    with transaction.atomic():
        # Present results sorted by marks obtained descending
        present_results = list(
            ExamResult.objects.filter(exam=exam, is_absent=False).order_by("-marks_obtained")
        )

        current_rank = 1
        last_marks = None
        for index, res in enumerate(present_results):
            if last_marks is not None and res.marks_obtained < last_marks:
                current_rank = index + 1
            res.rank = current_rank
            res.full_clean()
            res.save()
            last_marks = res.marks_obtained

        # Absent results get percentage=0.00, grade="F", rank=None
        absent_results = ExamResult.objects.filter(exam=exam, is_absent=True)
        for res in absent_results:
            res.percentage = Decimal("0.00")
            res.grade = "F"
            res.rank = None
            res.full_clean()
            res.save()


def create_exam(session_id, subject_id, name, exam_date, total_marks, passing_marks, exam_type, created_by):
    """Create a new exam verifying teacher assignments first."""
    _validate_teacher_scope(created_by, session_id=session_id, subject_id=subject_id)

    if passing_marks == "" or passing_marks is None:
        passing_marks = None
    else:
        passing_marks = Decimal(str(passing_marks))

    if exam_date == "":
        exam_date = None

    with transaction.atomic():
        exam = Exam(
            session_id=session_id,
            subject_id=subject_id,
            name=name,
            exam_date=exam_date,
            total_marks=Decimal(str(total_marks)),
            passing_marks=passing_marks,
            exam_type=exam_type,
            created_by=created_by,
            updated_by=created_by
        )
        exam.full_clean()
        exam.save()
        return exam


def update_exam(exam_id, name, exam_date, total_marks, passing_marks, exam_type, user):
    """Update an existing exam verifying teacher assignments first."""
    exam = Exam.objects.get(pk=exam_id)
    _validate_teacher_scope(user, exam=exam)

    if passing_marks == "" or passing_marks is None:
        passing_marks = None
    else:
        passing_marks = Decimal(str(passing_marks))

    if exam_date == "":
        exam_date = None

    with transaction.atomic():
        exam.name = name
        exam.exam_date = exam_date
        exam.total_marks = Decimal(str(total_marks))
        exam.passing_marks = passing_marks
        exam.exam_type = exam_type
        exam.updated_by = user
        exam.full_clean()
        exam.save()
        return exam


def review_exam(exam_id, user):
    """Review an exam, setting status to Under Review. Only Admins/Principals allowed."""
    if not (user.is_superuser or user.groups.filter(name__in=["Admin", "Principal"]).exists()):
        raise PermissionDenied("Only Admin or Principal can review exams.")

    from django.utils import timezone
    with transaction.atomic():
        exam = Exam.objects.get(pk=exam_id)
        exam.status = "Under Review"
        exam.reviewed_by = user
        exam.reviewed_at = timezone.now()
        exam.updated_by = user
        exam.full_clean()
        exam.save()
        return exam


def publish_exam(exam_id, user):
    """Publish an exam, making its results visible. Only Admins allowed."""
    if not (user.is_superuser or user.groups.filter(name="Admin").exists()):
        raise PermissionDenied("Only Admin can publish exams.")

    from django.utils import timezone
    with transaction.atomic():
        exam = Exam.objects.get(pk=exam_id)
        exam.status = "Published"
        exam.reviewed_by = user
        exam.reviewed_at = timezone.now()
        exam.updated_by = user
        exam.full_clean()
        exam.save()
        return exam


def record_exam_result(exam_id, student_id, obtained_marks, status, remarks, user):
    """Record or create a result for a single student."""
    exam = Exam.objects.get(pk=exam_id)
    _validate_teacher_scope(user, exam=exam)
    if exam.status == "Published":
        raise ValidationError("Cannot modify results of a published exam.")

    is_absent = (status == "Absent")

    with transaction.atomic():
        if is_absent:
            marks = Decimal("0.00")
            pct = Decimal("0.00")
            grade = "F"
        else:
            marks = Decimal(str(obtained_marks))
            pct = (marks / exam.total_marks * Decimal("100")).quantize(Decimal("0.01"))
            grade = _get_grade_for_percentage(exam.session, pct)

        result, created = ExamResult.objects.get_or_create(
            exam=exam,
            student_id=student_id,
            defaults={
                "marks_obtained": marks,
                "percentage": pct,
                "grade": grade,
                "is_absent": is_absent,
                "remarks": remarks,
                "entered_by": user
            }
        )

        if not created:
            result.marks_obtained = marks
            result.percentage = pct
            result.grade = grade
            result.is_absent = is_absent
            result.remarks = remarks
            result.entered_by = user

        result.full_clean()
        result.save()

        _recalculate_exam_ranking(exam)
        return result


def update_exam_result(result_id, obtained_marks, status, remarks, user):
    """Update an existing student exam result."""
    result = ExamResult.objects.get(pk=result_id)
    exam = result.exam
    _validate_teacher_scope(user, exam=exam)
    if exam.status == "Published":
        raise ValidationError("Cannot modify results of a published exam.")

    is_absent = (status == "Absent")

    with transaction.atomic():
        if is_absent:
            marks = Decimal("0.00")
            pct = Decimal("0.00")
            grade = "F"
        else:
            marks = Decimal(str(obtained_marks))
            pct = (marks / exam.total_marks * Decimal("100")).quantize(Decimal("0.01"))
            grade = _get_grade_for_percentage(exam.session, pct)

        result.marks_obtained = marks
        result.percentage = pct
        result.grade = grade
        result.is_absent = is_absent
        if remarks is not None:
            result.remarks = remarks
        result.entered_by = user

        result.full_clean()
        result.save()

        _recalculate_exam_ranking(exam)
        return result


def bulk_result_entry(exam_id, results_list, user):
    """Atomically record results for multiple students and compute rankings in one pass."""
    exam = Exam.objects.get(pk=exam_id)
    _validate_teacher_scope(user, exam=exam)
    if exam.status == "Published":
        raise ValidationError("Cannot modify results of a published exam.")

    with transaction.atomic():
        saved_results = []
        for data in results_list:
            student_id = data.get("student_id")
            obtained_marks = data.get("obtained_marks")
            status = data.get("status")
            remarks = data.get("remarks")

            is_absent = (status == "Absent")

            if is_absent:
                marks = Decimal("0.00")
                pct = Decimal("0.00")
                grade = "F"
            else:
                marks = Decimal(str(obtained_marks))
                pct = (marks / exam.total_marks * Decimal("100")).quantize(Decimal("0.01"))
                grade = _get_grade_for_percentage(exam.session, pct)

            result, created = ExamResult.objects.get_or_create(
                exam=exam,
                student_id=student_id,
                defaults={
                    "marks_obtained": marks,
                    "percentage": pct,
                    "grade": grade,
                    "is_absent": is_absent,
                    "remarks": remarks,
                    "entered_by": user
                }
            )

            if not created:
                result.marks_obtained = marks
                result.percentage = pct
                result.grade = grade
                result.is_absent = is_absent
                if remarks is not None:
                    result.remarks = remarks
                result.entered_by = user

            result.full_clean()
            result.save()
            saved_results.append(result)

        _recalculate_exam_ranking(exam)
        return saved_results


def calculate_exam_statistics(exam_id):
    """Calculate average, high, low marks, pass/fail counts, and grade distributions."""
    exam = Exam.objects.get(pk=exam_id)

    if exam.passing_marks is not None:
        pass_filter = Q(is_absent=False, marks_obtained__gte=exam.passing_marks)
        fail_filter = Q(is_absent=True) | Q(is_absent=False, marks_obtained__lt=exam.passing_marks)
    else:
        pass_filter = Q(pk__in=[])
        fail_filter = Q(pk__in=[])

    stats = ExamResult.objects.filter(exam=exam).aggregate(
        total_students=Count("id"),
        present_count=Count("id", filter=Q(is_absent=False)),
        absent_count=Count("id", filter=Q(is_absent=True)),
        avg_marks=Avg("marks_obtained", filter=Q(is_absent=False)),
        max_marks=Max("marks_obtained", filter=Q(is_absent=False)),
        min_marks=Min("marks_obtained", filter=Q(is_absent=False)),
        pass_count=Count("id", filter=pass_filter),
        fail_count=Count("id", filter=fail_filter)
    )

    total_students = stats["total_students"] or 0
    present_count = stats["present_count"] or 0
    absent_count = stats["absent_count"] or 0
    average_marks = (stats["avg_marks"] or Decimal("0.00")).quantize(Decimal("0.01"))
    highest_marks = stats["max_marks"] or Decimal("0.00")
    lowest_marks = stats["min_marks"] or Decimal("0.00")
    pass_count = stats["pass_count"] or 0
    fail_count = stats["fail_count"] or 0

    grade_counts = list(
        ExamResult.objects.filter(exam=exam)
        .values("grade")
        .annotate(count=Count("id"))
        .order_by("grade")
    )
    grade_distribution = {item["grade"]: item["count"] for item in grade_counts if item["grade"] is not None}

    return {
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "average_marks": average_marks,
        "highest_marks": highest_marks,
        "lowest_marks": lowest_marks,
        "pass_count": pass_count,
        "fail_count": fail_count,
        "grade_distribution": grade_distribution,
    }
