"""
Student portal views for the Academy CRM.

All queries are scoped to the authenticated student's own data.
"""

import json
import datetime
from decimal import Decimal
from django import forms
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin

from apps.students.models import Student, Enrollment
from apps.academics.models import ClassSchedule
from apps.exams.models import ExamResult
from apps.notifications.models import Notification
from apps.dashboard.services import get_student_dashboard_metrics
from apps.admissions.models import AdmissionApplication
from apps.core.models import AuditLog


# -------------------------------------------------------------------
#  Security / Authorization Helper
# -------------------------------------------------------------------

def get_student_or_404(request):
    """Enforces authentication and Student role verification."""
    if not request.user.is_authenticated:
        raise Http404("Not authenticated.")

    # Check if user belongs to 'Student' group or is superuser
    is_student = request.user.groups.filter(name="Student").exists() or request.user.is_superuser
    if not is_student:
        raise Http404("Not authorized.")

    student = getattr(request.user, "student_record", None)
    if not student:
        raise Http404("No student profile linked.")
    return student


# -------------------------------------------------------------------
#  Form Definitions
# -------------------------------------------------------------------

class StudentProfileForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Phone Number"})
    )
    address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Current Address"})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email Address"})
    )
    confirm_email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Confirm Email Address"})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        confirm_email = cleaned_data.get("confirm_email")
        if email and confirm_email and email != confirm_email:
            self.add_error("confirm_email", "Email and confirmation email must match.")
        return cleaned_data


# -------------------------------------------------------------------
#  Student portal CBVs
# -------------------------------------------------------------------

class StudentDashboardView(View):
    """Visual dashboard displaying overview stats and admissions progress."""

    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        metrics = get_student_dashboard_metrics(request.user)

        # Admissions Tracking (Phase 9)
        application = AdmissionApplication.objects.filter(converted_student=student).first()
        timeline = []
        if application:
            logs = AuditLog.objects.filter(
                model_name="admissions.AdmissionApplication",
                object_id=str(application.pk)
            ).order_by("created_at")
            for log in logs:
                try:
                    changes = json.loads(log.changes)
                    if "status" in changes:
                        timeline.append({
                            "date": log.created_at,
                            "old": changes["status"].get("old"),
                            "new": changes["status"].get("new"),
                            "by": log.user.get_full_name() if log.user else "System"
                        })
                except Exception:
                    pass

        context = {
            "metrics": metrics,
            "application": application,
            "timeline": timeline,
            "student": student,
            "role": "Student",
        }
        return render(request, "portal/student_dashboard.html", context)


class StudentProfileView(View):
    """Renders profile cards and updates contact details."""

    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        active_enrollment = Enrollment.objects.filter(student=student, status="Active").first()

        academic_score = "N/A"
        if active_enrollment:
            from apps.students.services import EnrollmentService
            score = EnrollmentService.calculate_academic_score(student.id, active_enrollment.session.id)
            if score is not None:
                academic_score = f"{score:.2f}%"
            else:
                academic_score = "0.00%"

        form = StudentProfileForm(initial={
            "phone": student.phone,
            "address": student.address_temporary or "",
            "email": student.email,
            "confirm_email": student.email,
        })

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "academic_score": academic_score,
            "form": form,
            "role": "Student",
        }
        return render(request, "portal/student_profile.html", context)

    def post(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        form = StudentProfileForm(request.POST)

        if form.is_valid():
            from apps.students.services import StudentService
            from apps.core.services import DomainValidationError
            try:
                StudentService.update_student_profile(
                    student_id=student.id,
                    user=request.user,
                    phone=form.cleaned_data["phone"],
                    address=form.cleaned_data["address"],
                    email=form.cleaned_data["email"],
                )
                messages.success(request, "Profile updated successfully.")
                return redirect("student_portal:profile_view")
            except DomainValidationError as e:
                if isinstance(e.errors, dict):
                    for field, errs in e.errors.items():
                        if field in form.fields:
                            form.add_error(field, errs)
                        else:
                            form.add_error(None, errs)
                else:
                    form.add_error(None, str(e.errors))
            except Exception as e:
                form.add_error(None, str(e))

        active_enrollment = Enrollment.objects.filter(student=student, status="Active").first()
        academic_score = "N/A"
        if active_enrollment:
            from apps.students.services import EnrollmentService
            score = EnrollmentService.calculate_academic_score(student.id, active_enrollment.session.id)
            if score is not None:
                academic_score = f"{score:.2f}%"
            else:
                academic_score = "0.00%"

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "academic_score": academic_score,
            "form": form,
            "role": "Student",
        }
        return render(request, "portal/student_profile.html", context)


class StudentFeesView(View):
    """Displays outstanding balance, discount, amount paid, payments list, and installments."""

    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        active_enrollment = Enrollment.objects.filter(student=student, status="Active").first()

        ledger = None
        if active_enrollment:
            from apps.finance.services import calculate_student_ledger
            ledger = calculate_student_ledger(active_enrollment.id)

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "ledger": ledger,
            "role": "Student",
        }
        return render(request, "portal/student_fees.html", context)


class StudentAttendanceView(View):
    """Month-wise attendance breakdown table and visual Chart.js chart."""

    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        active_enrollment = Enrollment.objects.filter(student=student, status="Active").first()

        attendance_records = []
        overall_percentage = 100.0
        monthly_breakdown = []
        chart_months = []
        chart_percentages = []
        color_class = "success"

        if active_enrollment:
            from apps.attendance.models import AttendanceRecord
            attendance_records = AttendanceRecord.objects.filter(
                student=student,
                session=active_enrollment.session
            ).order_by("-date")

            total_records = attendance_records.count()
            attended_records = attendance_records.filter(status__in=["Present", "Late"]).count()
            overall_percentage = (attended_records / total_records * 100.0) if total_records > 0 else 100.0
            overall_percentage = round(overall_percentage, 2)

            if overall_percentage >= 75.0:
                color_class = "success"
            elif overall_percentage >= 60.0:
                color_class = "warning"
            else:
                color_class = "danger"

            from collections import defaultdict
            monthly_data = defaultdict(lambda: {"Present": 0, "Absent": 0, "Late": 0, "Excused": 0, "Total": 0})
            for record in attendance_records:
                month_str = record.date.strftime("%B %Y")
                month_key = record.date.strftime("%Y-%m")
                monthly_data[month_key]["name"] = month_str
                monthly_data[month_key][record.status] += 1
                if record.status in ["Present", "Absent", "Late", "Excused"]:
                    monthly_data[month_key]["Total"] += 1

            for key in sorted(monthly_data.keys(), reverse=True):
                data = monthly_data[key]
                present = data["Present"]
                absent = data["Absent"]
                late = data["Late"]
                excused = data["Excused"]
                total = data["Total"]
                pct = (present + late) / total * 100.0 if total > 0 else 100.0
                monthly_breakdown.append({
                    "month_name": data["name"],
                    "present": present,
                    "absent": absent,
                    "late": late,
                    "excused": excused,
                    "total": total,
                    "percentage": round(pct, 2)
                })

            chart_months = [item["month_name"] for item in reversed(monthly_breakdown)]
            chart_percentages = [item["percentage"] for item in reversed(monthly_breakdown)]

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "overall_percentage": overall_percentage,
            "color_class": color_class,
            "monthly_breakdown": monthly_breakdown,
            "chart_months": json.dumps(chart_months),
            "chart_percentages": json.dumps(chart_percentages),
            "attendance_records": attendance_records,
            "role": "Student",
        }
        return render(request, "portal/student_attendance.html", context)


class StudentExamsView(View):
    """Lists published exams and overall academic score."""

    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        active_enrollment = Enrollment.objects.filter(student=student, status="Active").first()

        exam_results = []
        overall_score = 100.00

        if active_enrollment:
            from apps.students.services import EnrollmentService
            score = EnrollmentService.calculate_academic_score(student.id, active_enrollment.session_id)
            if score is not None:
                overall_score = round(score, 2)
            else:
                overall_score = 0.00

            exam_results = list(
                ExamResult.objects.filter(
                    student=student,
                    exam__is_published=True
                ).select_related("exam", "exam__subject").order_by("-exam__exam_date")
            )

            for r in exam_results:
                is_passed = True
                if r.is_absent:
                    is_passed = False
                elif r.exam.passing_marks is not None and r.marks_obtained < r.exam.passing_marks:
                    is_passed = False
                elif r.grade == "F":
                    is_passed = False
                r.is_passed = is_passed

        context = {
            "student": student,
            "active_enrollment": active_enrollment,
            "exam_results": exam_results,
            "overall_score": overall_score,
            "role": "Student",
        }
        return render(request, "portal/student_exams.html", context)


class StudentFeeReceiptPDFView(View):
    """Generates PDF printable receipt of the given payment."""

    def get(self, request, payment_id, *args, **kwargs):
        if not request.user.is_authenticated:
            raise Http404("Not authenticated.")

        from apps.finance.models import Payment
        from apps.students.models import Guardian
        from apps.reports.services import generate_pdf_report

        payment = get_object_or_404(Payment, pk=payment_id, payment_status="confirmed")
        student = payment.enrollment.student

        is_student_user = request.user.groups.filter(name="Student").exists() and student.portal_user == request.user
        is_guardian_user = request.user.groups.filter(name="Guardian").exists() and Guardian.objects.filter(
            Q(portal_user=request.user) | Q(email=request.user.email),
            student=student
        ).exists()
        is_admin_or_principal = request.user.is_superuser or request.user.groups.filter(name__in=["Admin", "Principal"]).exists()

        from django.db.models import Q
        if not (is_student_user or is_guardian_user or is_admin_or_principal):
            raise Http404("Access denied to fee receipt.")

        context = {
            "payment": payment,
            "student": student,
            "enrollment": payment.enrollment,
            "session": payment.enrollment.session,
            "report_title": f"Payment Receipt - {payment.receipt_number}"
        }

        pdf_content = generate_pdf_report("portal/payment_receipt_pdf.html", context)
        if pdf_content:
            response = HttpResponse(pdf_content, content_type="application/pdf")
            response["Content-Disposition"] = f'attachment; filename="receipt_{payment.receipt_number}.pdf"'
            return response
        raise Http404("Failed to generate receipt PDF.")


# -------------------------------------------------------------------
#  Notification center views
# -------------------------------------------------------------------

class StudentNotificationListView(View):
    def get(self, request, *args, **kwargs):
        student = get_student_or_404(request)
        notifications = Notification.objects.filter(recipient=request.user)
        category_filter = request.GET.get("category")
        if category_filter:
            notifications = notifications.filter(category=category_filter)

        context = {
            "student": student,
            "notifications": notifications,
            "selected_category": category_filter,
            "categories": Notification.CATEGORY_CHOICES,
            "role": "Student",
        }
        return render(request, "portal/notification_list.html", context)


class StudentNotificationDetailView(View):
    def get(self, request, pk, *args, **kwargs):
        student = get_student_or_404(request)
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        context = {
            "student": student,
            "notification": notification,
            "role": "Student",
        }
        return render(request, "portal/notification_detail.html", context)


class StudentNotificationMarkReadView(View):
    def post(self, request, *args, **kwargs):
        get_student_or_404(request)
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == "application/json":
            return JsonResponse({"status": "success"})
        messages.success(request, "All notifications marked as read.")
        return redirect("student_portal:notification_list")


# -------------------------------------------------------------------
#  Django built-in Password Change
# -------------------------------------------------------------------

class StudentPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "portal/password_change.html"
    success_url = reverse_lazy("student_portal:dashboard")
    success_message = "Your password has been changed successfully."

    def dispatch(self, request, *args, **kwargs):
        get_student_or_404(request)
        return super().dispatch(request, *args, **kwargs)


# -------------------------------------------------------------------
#  Compatibility Stubs for old imports
# -------------------------------------------------------------------

dashboard = StudentDashboardView.as_view()
profile_view = StudentProfileView.as_view()
my_attendance = StudentAttendanceView.as_view()
my_exams = StudentExamsView.as_view()
my_payments = StudentFeesView.as_view()
notification_list = StudentNotificationListView.as_view()
notification_detail = StudentNotificationDetailView.as_view()
notification_mark_read = StudentNotificationMarkReadView.as_view()

def my_enrollment(request):
    """Placeholder or redirects to profile."""
    get_student_or_404(request)
    return redirect("student_portal:profile_view")

def exam_result_detail(request, pk):
    """Stub exam detail view, redirects to exams list."""
    get_student_or_404(request)
    return redirect("student_portal:my_exams")

def student_timetable(request):
    """Student weekly timetable view."""
    student = get_student_or_404(request)

    # Retrieve student's active enrollment
    enrollment = Enrollment.objects.filter(
        student=student,
        status="Active"
    ).select_related("session").first()

    schedules = []
    active_session = None
    if enrollment:
        active_session = enrollment.session
        schedules = ClassSchedule.objects.filter(
            session=active_session,
            is_active=True
        ).select_related("subject", "faculty__user").order_by("start_time")

    days_map = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    }
    for s in schedules:
        if s.day_of_week in days_map:
            days_map[s.day_of_week].append(s)

    today_name = datetime.date.today().strftime("%A")
    context = {
        "days_map": days_map,
        "active_session": active_session,
        "today_name": today_name,
        "role": "Student",
    }
    return render(request, "academics/timetable_student.html", context)


def student_transcript(request):
    """View to display the student's official transcript."""
    student = get_student_or_404(request)

    from apps.exams.transcript_service import generate_student_transcript
    transcript = generate_student_transcript(student.id)
    return render(request, "exams/transcript.html", {"transcript": transcript})

