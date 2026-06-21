import csv
import datetime
from decimal import Decimal
from io import BytesIO
from django.template.loader import get_template
from django.db.models import Prefetch
from django.utils import timezone
from xhtml2pdf import pisa

from apps.finance.services import get_pending_dues, calculate_student_ledger
from apps.finance.utils import format_currency
from apps.students.models import Student, Enrollment
from apps.academics.models import Session, TeacherAssignment
from apps.exams.models import ExamResult
from apps.staff.models import FacultyProfile


def export_pending_dues_csv(file_object):
    """Exports active enrollments with outstanding balance > 0 to a CSV file."""
    writer = csv.writer(file_object)
    writer.writerow(["Student Name", "Roll Number", "Session", "Due Date / Next Due", "Outstanding Balance"])

    dues = get_pending_dues()
    for item in dues:
        due_date_str = item["due_from"].strftime("%Y-%m-%d") if isinstance(item["due_from"], (datetime.date, datetime.datetime)) else str(item["due_from"])
        writer.writerow([
            item["student_name"],
            item["roll_number"] or "-",
            item["session_name"],
            due_date_str,
            format_currency(item["outstanding_balance"])
        ])


def export_session_results_csv(session_id, file_object):
    """Exports student exam results for a specific academic session to a CSV file."""
    writer = csv.writer(file_object)
    writer.writerow([
        "Student Name", "Roll Number", "Exam Name", "Subject",
        "Marks Obtained", "Total Marks", "Percentage (%)", "Grade", "Rank", "Status"
    ])

    results = (
        ExamResult.objects.filter(exam__session_id=session_id)
        .select_related("exam", "student", "exam__subject")
        .order_by("exam__name", "student__full_name")
    )

    for r in results:
        subject_name = r.exam.subject.name if r.exam.subject else "All Subjects"
        status_str = "Absent" if r.is_absent else "Present"
        writer.writerow([
            r.student.full_name,
            r.student.roll_number or "-",
            r.exam.name,
            subject_name,
            r.marks_obtained,
            r.exam.total_marks,
            f"{r.percentage:.2f}" if r.percentage is not None else "-",
            r.grade or "-",
            r.rank or "-",
            status_str
        ])


def export_student_directory_csv(file_object):
    """Exports directory of active non-deleted students to a CSV file."""
    writer = csv.writer(file_object)
    writer.writerow([
        "Roll Number", "Student Name", "Father Name", "Email",
        "CNIC", "Phone", "Status", "Gender", "Selected in Gov Exam"
    ])

    students = Student.objects.filter(is_deleted=False).order_by("full_name")
    for s in students:
        writer.writerow([
            s.roll_number or "-",
            s.full_name,
            s.father_name or "-",
            s.email or "-",
            s.cnic or "-",
            s.phone or "-",
            s.status,
            s.gender or "-",
            "Yes" if s.is_selected else "No"
        ])


def export_teacher_workload_csv(file_object):
    """Exports workload details for active faculty members to a CSV file."""
    writer = csv.writer(file_object)
    writer.writerow([
        "Teacher Name", "Designation", "Department",
        "Active Sessions", "Active Subjects", "Total Active Assignments"
    ])

    # Prefetch active teaching assignments to prevent N+1 queries
    active_assignments_prefetch = Prefetch(
        "user__teaching_assignments",
        queryset=TeacherAssignment.objects.filter(is_active=True).select_related("session", "subject"),
        to_attr="active_assignments"
    )

    profiles = (
        FacultyProfile.objects.filter(is_active=True)
        .select_related("user")
        .prefetch_related(active_assignments_prefetch)
        .order_by("user__first_name", "user__last_name")
    )

    for fp in profiles:
        assignments = getattr(fp.user, "active_assignments", [])
        sessions = ", ".join(list(set([ta.session.name for ta in assignments])))
        subjects = ", ".join(list(set([ta.subject.name if ta.subject else "All Subjects" for ta in assignments])))
        writer.writerow([
            fp.user.get_full_name() or fp.user.username,
            fp.designation,
            fp.department,
            sessions or "None",
            subjects or "None",
            len(assignments)
        ])


def generate_pdf_report(template_name, context):
    """Generates a printable PDF report from a Django template using xhtml2pdf."""
    template = get_template(template_name)
    context["generated_at"] = timezone.now()
    html = template.render(context)

    result = BytesIO()
    # xhtml2pdf pisaDocument compiles the HTML string into the output stream
    pdf = pisa.pisaDocument(BytesIO(html.encode("utf-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


def export_success_report_csv(file_object):
    """Exports success/achievements list to a CSV file."""
    from apps.achievements.models import Achievement
    from apps.students.models import Enrollment

    writer = csv.writer(file_object)
    writer.writerow(["Student Name", "Roll Number", "Session", "Exam Type", "Year", "Rank"])

    achievements = Achievement.objects.select_related("student").order_by("-year", "exam_type")

    for ach in achievements:
        enrollment = Enrollment.objects.filter(student=ach.student, status="Active").select_related("session").first()
        session_name = enrollment.session.name if enrollment else "No Active Session"
        writer.writerow([
            ach.student.full_name,
            ach.student.roll_number or "-",
            session_name,
            ach.exam_type,
            ach.year,
            ach.rank or "-",
        ])


def export_success_report_pdf(context):
    """Generates PDF for achievements list using generate_pdf_report."""
    return generate_pdf_report("reports/success_report_pdf.html", context)

