from django.views import View
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from decimal import Decimal

from apps.core.mixins import RoleRequiredMixin
from apps.academics.models import Session
from apps.students.models import Student, Enrollment, Guardian
from apps.exams.models import ExamResult
from apps.staff.models import FacultyProfile
from apps.reports.services import (
    export_pending_dues_csv,
    export_session_results_csv,
    export_student_directory_csv,
    export_teacher_workload_csv,
    generate_pdf_report,
    export_success_report_csv,
    export_success_report_pdf,
)
from apps.finance.services import get_pending_dues, calculate_student_ledger
from apps.students.services import EnrollmentService
from apps.finance.utils import format_currency


class ReportsDashboardView(RoleRequiredMixin, View):
    """HTML reports panel dashboard for Admin and Principal users."""
    required_roles = ["Admin", "Principal"]
    template_name = "reports/reports_dashboard.html"

    def get(self, request, *args, **kwargs):
        sessions = Session.objects.filter(status="Active").order_by("name")
        is_admin = request.user.is_superuser or request.user.groups.filter(name="Admin").exists()
        is_principal = request.user.groups.filter(name="Principal").exists()

        context = {
            "sessions": sessions,
            "is_admin": is_admin,
            "is_principal": is_principal,
            "panel_type": "admin"
        }
        return render(request, self.template_name, context)


class AccountantReportsDashboardView(RoleRequiredMixin, View):
    """HTML reports panel dashboard restricted for Accountant users."""
    required_roles = ["Accountant"]
    template_name = "reports/reports_dashboard.html"

    def get(self, request, *args, **kwargs):
        context = {
            "is_admin": False,
            "is_principal": False,
            "is_accountant": True,
            "panel_type": "accounts"
        }
        return render(request, self.template_name, context)


class PendingDuesExportCSVView(RoleRequiredMixin, View):
    """CSV download for outstanding dues. Admin, Accountant & Principal."""
    required_roles = ["Admin", "Accountant", "Principal"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="pending_dues.csv"'
        export_pending_dues_csv(response)
        return response


class PendingDuesPDFView(RoleRequiredMixin, View):
    """PDF generation for outstanding dues. Admin, Accountant & Principal."""
    required_roles = ["Admin", "Accountant", "Principal"]
    template_name = "reports/pending_dues_pdf.html"

    def get(self, request, *args, **kwargs):
        dues = get_pending_dues()
        total_outstanding = sum(item["outstanding_balance"] for item in dues)

        context = {
            "dues": dues,
            "total_outstanding": format_currency(total_outstanding),
            "report_title": "Outstanding Payments Report"
        }

        pdf_content = generate_pdf_report(self.template_name, context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="pending_dues.pdf"'
            return response
        raise Http404("Failed to generate PDF report.")


class SessionResultsExportCSVView(RoleRequiredMixin, View):
    """CSV download for session results. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(Session, pk=session_id)
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="session_results_{session_id}.csv"'
        export_session_results_csv(session_id, response)
        return response


class SessionResultsPDFView(RoleRequiredMixin, View):
    """PDF generation for session results. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]
    template_name = "reports/session_results_pdf.html"

    def get(self, request, session_id, *args, **kwargs):
        session = get_object_or_404(Session, pk=session_id)
        results = (
            ExamResult.objects.filter(exam__session_id=session_id)
            .select_related("exam", "student", "exam__subject")
            .order_by("exam__name", "student__full_name")
        )

        # Calculate session averages
        total_pct = Decimal("0.00")
        count = 0
        for r in results:
            if r.percentage is not None:
                total_pct += r.percentage
                count += 1
        class_average = total_pct / count if count > 0 else Decimal("0.00")

        context = {
            "session": session,
            "results": results,
            "class_average": f"{class_average:.2f}%",
            "total_entries": results.count(),
            "report_title": f"Results Summary: {session.name}"
        }

        pdf_content = generate_pdf_report(self.template_name, context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="session_results_{session_id}.pdf"'
            return response
        raise Http404("Failed to generate PDF report.")


class StudentDirectoryExportCSVView(RoleRequiredMixin, View):
    """CSV download for student directory. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="student_directory.csv"'
        export_student_directory_csv(response)
        return response


class TeacherWorkloadPDFView(RoleRequiredMixin, View):
    """PDF generation for faculty workload. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]
    template_name = "reports/teacher_workload_pdf.html"

    def get(self, request, *args, **kwargs):
        from django.db.models import Prefetch
        from apps.academics.models import TeacherAssignment

        active_assignments = Prefetch(
            "user__teaching_assignments",
            queryset=TeacherAssignment.objects.filter(is_active=True).select_related("session", "subject"),
            to_attr="active_assignments_list"
        )

        profiles = (
            FacultyProfile.objects.filter(is_active=True)
            .select_related("user")
            .prefetch_related(active_assignments)
            .order_by("user__first_name", "user__last_name")
        )

        teacher_workloads = []
        for fp in profiles:
            assignments = getattr(fp.user, "active_assignments_list", [])
            sessions = list(set([ta.session.name for ta in assignments]))
            subjects = list(set([ta.subject.name if ta.subject else "All Subjects" for ta in assignments]))
            teacher_workloads.append({
                "name": fp.user.get_full_name() or fp.user.username,
                "designation": fp.designation,
                "department": fp.department,
                "sessions": sessions,
                "subjects": subjects,
                "total_assignments": len(assignments)
            })

        context = {
            "teacher_workloads": teacher_workloads,
            "report_title": "Faculty Workload & Allocation Summary"
        }

        pdf_content = generate_pdf_report(self.template_name, context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="teacher_workload.pdf"'
            return response
        raise Http404("Failed to generate PDF report.")


class TeacherWorkloadExportCSVView(RoleRequiredMixin, View):
    """CSV download for faculty workload. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="teacher_workload.csv"'
        export_teacher_workload_csv(response)
        return response


class StudentTranscriptPDFView(LoginRequiredMixin, View):
    """PDF transcript generation.

    Enforces permission matrix:
    - Admin/Principal can view any student.
    - Student can only view their own transcript.
    - Guardian can only view transcripts for their linked children.
    """
    template_name = "reports/student_transcript_pdf.html"

    def get(self, request, student_id=None, *args, **kwargs):
        user = request.user

        # Resolve student
        student = None
        if student_id:
            # Check Admin, Principal, or Registrar
            is_staff_allowed = user.is_superuser or user.groups.filter(name__in=["Admin", "Principal", "Registrar"]).exists()
            if is_staff_allowed:
                student = get_object_or_404(Student, pk=student_id)
            else:
                # Check Guardian
                is_guardian = user.groups.filter(name="Guardian").exists()
                if is_guardian and Guardian.objects.filter(portal_user=user, student_id=student_id).exists():
                    student = get_object_or_404(Student, pk=student_id)
                # Check Student
                elif user.groups.filter(name="Student").exists() and Student.objects.filter(portal_user=user, pk=student_id).exists():
                    student = get_object_or_404(Student, pk=student_id)
                else:
                    raise Http404("Access denied to student transcript.")
        else:
            # Logged-in student requesting their own
            if user.groups.filter(name="Student").exists():
                student = get_object_or_404(Student, portal_user=user)
            else:
                raise Http404("Access denied to student transcript.")

        # Gather enrollment & academic performance
        active_enrollment = Enrollment.objects.filter(student=student, status="Active").select_related("session").first()
        results = (
            ExamResult.objects.filter(student=student)
            .select_related("exam", "exam__session", "exam__subject")
            .order_by("exam__exam_date")
        )

        overall_score = Decimal("100.00")
        session_name = "No Active Session"
        if active_enrollment:
            session_name = active_enrollment.session.name
            overall_score = EnrollmentService.calculate_academic_score(student.id, active_enrollment.session_id)

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "session_name": session_name,
            "results": results,
            "overall_score": overall_score,
            "report_title": f"Official Academic Transcript - {student.full_name}"
        }

        pdf_content = generate_pdf_report(self.template_name, context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'inline; filename="transcript_{student.id}.pdf"'
            return response
        raise Http404("Failed to generate transcript PDF.")


class SuccessReportExportCSVView(RoleRequiredMixin, View):
    """CSV download for success/selections report. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="success_report.csv"'
        export_success_report_csv(response)
        return response


class SuccessReportPDFView(RoleRequiredMixin, View):
    """PDF generation for success/selections report. Admin & Principal only."""
    required_roles = ["Admin", "Principal"]

    def get(self, request, *args, **kwargs):
        from django.db.models import Prefetch
        from apps.achievements.models import Achievement
        from apps.students.models import Enrollment

        active_enrollments = Prefetch(
            "student__enrollments",
            queryset=Enrollment.objects.filter(status="Active").select_related("session"),
            to_attr="active_enrollment_list"
        )

        # Prefetch to prevent N+1 queries when building the PDF
        achievements_qs = (
            Achievement.objects.select_related("student")
            .prefetch_related(active_enrollments)
            .order_by("-year", "exam_type")
        )

        achievements_data = []
        for ach in achievements_qs:
            student = ach.student
            active_list = getattr(student, "active_enrollment_list", []) if student else []
            enrollment = active_list[0] if active_list else None
            session_name = enrollment.session.name if enrollment else "No Active Session"
            achievements_data.append({
                "student_name": student.full_name if student else "Unknown",
                "roll_number": student.roll_number if student else "N/A",
                "session_name": session_name,
                "exam_type": ach.exam_type,
                "year": ach.year,
                "rank": ach.rank,
            })

        context = {
            "achievements": achievements_data,
            "report_title": "Student Success & Selections Report"
        }

        pdf_content = export_success_report_pdf(context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = 'inline; filename="success_report.pdf"'
            return response
        raise Http404("Failed to generate success PDF report.")

