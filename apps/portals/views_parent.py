"""
Guardian (Parent) portal views for the Academy CRM.

All queries are scoped to children linked via Guardian records.
"""

import json
import datetime
from decimal import Decimal
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, HttpResponse, JsonResponse
from django.contrib import messages
from django.db.models import Q

from apps.students.models import Student, Guardian, Enrollment
from apps.exams.models import ExamResult
from apps.notifications.models import Notification
from apps.dashboard.services import get_guardian_dashboard_metrics


# -------------------------------------------------------------------
#  Security / Authorization Helpers
# -------------------------------------------------------------------

def get_guardian_or_404(request):
    """Enforces authentication and Guardian role verification."""
    if not request.user.is_authenticated:
        raise Http404("Not authenticated.")
    is_guardian = request.user.groups.filter(name="Guardian").exists() or request.user.is_superuser
    if not is_guardian:
        raise Http404("Not authorized.")

    # Check if there is at least one Guardian record linked by email or user
    guardian_exists = Guardian.objects.filter(
        Q(portal_user=request.user) | Q(email=request.user.email)
    ).exists()
    if not guardian_exists:
        raise Http404("No guardian profile found.")
    return True


def get_child_or_404(request, student_id):
    """Verifies that the requested child student is linked to the guardian."""
    get_guardian_or_404(request)

    is_linked = Guardian.objects.filter(
        Q(portal_user=request.user) | Q(email=request.user.email),
        student_id=student_id
    ).exists()
    if not is_linked:
        raise Http404("Access denied: You are not linked to this student.")

    try:
        return Student.objects.get(pk=student_id)
    except Student.DoesNotExist:
        raise Http404("Student record not found.")


# -------------------------------------------------------------------
#  Guardian Portal CBVs
# -------------------------------------------------------------------

class GuardianDashboardView(View):
    """Overview dashboard showing linked children summaries and unread notifications."""

    def get(self, request, *args, **kwargs):
        get_guardian_or_404(request)
        metrics = get_guardian_dashboard_metrics(request.user)

        context = {
            "metrics": metrics,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_dashboard.html", context)


class GuardianChildrenView(View):
    """Renders a page listing all children linked to this guardian email/user."""

    def get(self, request, *args, **kwargs):
        get_guardian_or_404(request)

        guardians_qs = Guardian.objects.filter(
            Q(portal_user=request.user) | Q(email=request.user.email)
        )
        children = Student.objects.filter(guardians__in=guardians_qs).distinct().prefetch_related("enrollments__session")

        context = {
            "children": children,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_children.html", context)


class GuardianChildDetailView(View):
    """Profile detail page for a specific child."""

    def get(self, request, student_id, *args, **kwargs):
        child = get_child_or_404(request, student_id)
        active_enrollment = Enrollment.objects.filter(student=child, status="Active").first()

        academic_score = "N/A"
        if active_enrollment:
            from apps.students.services import EnrollmentService
            score = EnrollmentService.calculate_academic_score(child.id, active_enrollment.session.id)
            if score is not None:
                academic_score = f"{score:.2f}%"
            else:
                academic_score = "0.00%"

        context = {
            "student": child,
            "active_enrollment": active_enrollment,
            "academic_score": academic_score,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_child_profile.html", context)


class GuardianChildAttendanceView(View):
    """Attendance summary and month-wise details for a child."""

    def get(self, request, student_id, *args, **kwargs):
        child = get_child_or_404(request, student_id)
        active_enrollment = Enrollment.objects.filter(student=child, status="Active").first()

        attendance_records = []
        overall_percentage = 100.0
        monthly_breakdown = []
        chart_months = []
        chart_percentages = []
        color_class = "success"

        if active_enrollment:
            from apps.attendance.models import AttendanceRecord
            attendance_records = AttendanceRecord.objects.filter(
                student=child,
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
            "student": child,
            "active_enrollment": active_enrollment,
            "overall_percentage": overall_percentage,
            "color_class": color_class,
            "monthly_breakdown": monthly_breakdown,
            "chart_months": json.dumps(chart_months),
            "chart_percentages": json.dumps(chart_percentages),
            "attendance_records": attendance_records,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_child_attendance.html", context)


class GuardianChildFeesView(View):
    """Fee ledger details for a child."""

    def get(self, request, student_id, *args, **kwargs):
        child = get_child_or_404(request, student_id)
        active_enrollment = Enrollment.objects.filter(student=child, status="Active").first()

        ledger = None
        if active_enrollment:
            from apps.finance.services import calculate_student_ledger
            ledger = calculate_student_ledger(active_enrollment.id)

        context = {
            "student": child,
            "active_enrollment": active_enrollment,
            "ledger": ledger,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_child_fees.html", context)


class GuardianChildExamsView(View):
    """Exams and published grades for a child."""

    def get(self, request, student_id, *args, **kwargs):
        child = get_child_or_404(request, student_id)
        active_enrollment = Enrollment.objects.filter(student=child, status="Active").first()

        exam_results = []
        overall_score = 100.00

        if active_enrollment:
            from apps.students.services import EnrollmentService
            score = EnrollmentService.calculate_academic_score(child.id, active_enrollment.session_id)
            if score is not None:
                overall_score = round(score, 2)
            else:
                overall_score = 0.00

            exam_results = list(
                ExamResult.objects.filter(
                    student=child,
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
            "student": child,
            "active_enrollment": active_enrollment,
            "exam_results": exam_results,
            "overall_score": overall_score,
            "role": "Guardian",
        }
        return render(request, "portal/guardian_child_exams.html", context)


class GuardianChildFeeReceiptPDFView(View):
    """Generates PDF printable receipt of the given payment for a child."""

    def get(self, request, student_id, payment_id, *args, **kwargs):
        child = get_child_or_404(request, student_id)

        from apps.finance.models import Payment
        from apps.reports.services import generate_pdf_report

        payment = get_object_or_404(Payment, pk=payment_id, payment_status="confirmed", enrollment__student=child)

        context = {
            "payment": payment,
            "student": child,
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
#  Guardian Notification Center Views
# -------------------------------------------------------------------

class GuardianNotificationListView(View):
    def get(self, request, *args, **kwargs):
        get_guardian_or_404(request)
        notifications = Notification.objects.filter(recipient=request.user)
        category_filter = request.GET.get("category")
        if category_filter:
            notifications = notifications.filter(category=category_filter)

        context = {
            "notifications": notifications,
            "selected_category": category_filter,
            "categories": Notification.CATEGORY_CHOICES,
            "role": "Guardian",
        }
        return render(request, "portal/notification_list.html", context)


class GuardianNotificationDetailView(View):
    def get(self, request, pk, *args, **kwargs):
        get_guardian_or_404(request)
        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=["is_read"])

        context = {
            "notification": notification,
            "role": "Guardian",
        }
        return render(request, "portal/notification_detail.html", context)


class GuardianNotificationMarkReadView(View):
    def post(self, request, *args, **kwargs):
        get_guardian_or_404(request)
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == "application/json":
            return JsonResponse({"status": "success"})
        messages.success(request, "All notifications marked as read.")
        return redirect("guardian_portal:notification_list")


# -------------------------------------------------------------------
#  Transcript Compatibility function view
# -------------------------------------------------------------------

def child_transcript(request, student_id):
    """View to display the transcript of a guardian's child."""
    child = get_child_or_404(request, student_id)
    from apps.exams.transcript_service import generate_student_transcript
    transcript = generate_student_transcript(student_id)
    return render(request, "exams/transcript.html", {"transcript": transcript})


# -------------------------------------------------------------------
#  Compatibility Stubs for old imports
# -------------------------------------------------------------------

dashboard = GuardianDashboardView.as_view()
my_children = GuardianChildrenView.as_view()
child_detail = GuardianChildDetailView.as_view()
child_attendance = GuardianChildAttendanceView.as_view()
child_exams = GuardianChildExamsView.as_view()
child_payments = GuardianChildFeesView.as_view()
notification_list = GuardianNotificationListView.as_view()
notification_detail = GuardianNotificationDetailView.as_view()
notification_mark_read = GuardianNotificationMarkReadView.as_view()
