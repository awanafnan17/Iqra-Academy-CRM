"""
Dashboard views for the Academy CRM.

Provides role-specific dashboard views and teacher-specific
session views. All views are integrated with the dashboard services.
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from apps.core.decorators import role_required
from apps.dashboard.services import (
    get_admin_dashboard_metrics,
    get_principal_dashboard_metrics,
    get_teacher_dashboard_metrics,
    get_accountant_dashboard_metrics,
    get_registrar_dashboard_metrics,
    get_student_dashboard_metrics,
    get_guardian_dashboard_metrics,
)


class BaseDashboardView(View):
    """Base class-based view for all dashboards to ensure O(1) complexity, caching, and reuse logic."""
    role = None
    template_name = None
    service_func = None
    http_method_names = ["get"]

    def get(self, request, *args, **kwargs):
        if not self.service_func:
            raise NotImplementedError("service_func must be set")

        # Enforce authentication explicitly
        if not request.user.is_authenticated:
            raise Http404

        # Short-term caching layer (60 seconds) per role/user
        use_cache = getattr(settings, "ENABLE_DASHBOARD_CACHE", True)
        cache_key = f"dashboard_metrics:{self.role}"
        if self.role in ["Teacher", "Student", "Guardian"]:
            cache_key += f":{request.user.pk}"

        context = None
        if use_cache:
            context = cache.get(cache_key)

        if not context:
            try:
                if self.role in ["Teacher", "Student", "Guardian"]:
                    metrics = self.service_func(request.user)
                else:
                    metrics = self.service_func()
            except Exception:
                metrics = {}

            from decimal import Decimal
            context = {
                "metrics": metrics,
                "role": self.role,
                "confirmed_revenue": metrics.get("confirmed_revenue", Decimal("0.00")),
                "total_revenue": metrics.get("total_revenue", Decimal("0.00")),
                "net_cash_flow": metrics.get("net_cash_flow", Decimal("0.00")),
                "active_students": metrics.get("active_students", 0),
                "pending_admissions": metrics.get("pending_admissions_count", 0),
            }
            if use_cache:
                cache.set(cache_key, context, 60)

        # Return JSON for AJAX requests
        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
            return JsonResponse(context)

        return render(request, self.template_name, context)


@method_decorator(role_required("Admin"), name="dispatch")
class AdminDashboardView(BaseDashboardView):
    role = "Admin"
    template_name = "dashboard/admin.html"
    service_func = staticmethod(get_admin_dashboard_metrics)


@method_decorator(role_required("Principal"), name="dispatch")
class PrincipalDashboardView(BaseDashboardView):
    role = "Principal"
    template_name = "dashboard/principal.html"
    service_func = staticmethod(get_principal_dashboard_metrics)


@method_decorator(role_required("Teacher"), name="dispatch")
class TeacherDashboardView(BaseDashboardView):
    role = "Teacher"
    template_name = "dashboard/teacher.html"
    service_func = staticmethod(get_teacher_dashboard_metrics)


@method_decorator(role_required("Accountant"), name="dispatch")
class AccountantDashboardView(BaseDashboardView):
    role = "Accountant"
    template_name = "dashboard/accountant.html"
    service_func = staticmethod(get_accountant_dashboard_metrics)


@method_decorator(role_required("Registrar"), name="dispatch")
class RegistrarDashboardView(BaseDashboardView):
    role = "Registrar"
    template_name = "dashboard/registrar.html"
    service_func = staticmethod(get_registrar_dashboard_metrics)


@method_decorator(role_required("Student"), name="dispatch")
class StudentDashboardView(BaseDashboardView):
    role = "Student"
    template_name = "portal/student_dashboard.html"
    service_func = staticmethod(get_student_dashboard_metrics)


@method_decorator(role_required("Guardian"), name="dispatch")
class GuardianDashboardView(BaseDashboardView):
    role = "Guardian"
    template_name = "portal/guardian_dashboard.html"
    service_func = staticmethod(get_guardian_dashboard_metrics)


# -------------------------------------------------------------------
#  Shared Router or function views
# -------------------------------------------------------------------

@role_required("Admin", "Principal")
def admin_dashboard(request, *args, **kwargs):
    """Router for the shared admin panel dashboard URL."""
    if request.user.groups.filter(name="Admin").exists():
        return AdminDashboardView.as_view()(request, *args, **kwargs)
    return PrincipalDashboardView.as_view()(request, *args, **kwargs)


teacher_dashboard = TeacherDashboardView.as_view()
principal_dashboard = PrincipalDashboardView.as_view()
accountant_dashboard = AccountantDashboardView.as_view()
registrar_dashboard = RegistrarDashboardView.as_view()
student_dashboard = StudentDashboardView.as_view()
guardian_dashboard = GuardianDashboardView.as_view()


@role_required("Teacher")
def my_sessions(request):
    """List sessions assigned to the logged-in teacher."""
    from apps.academics.models import TeacherAssignment
    from django.db.models import Count

    assignments = (
        TeacherAssignment.objects
        .filter(teacher=request.user, is_active=True)
        .select_related("session", "subject")
    )

    sessions_data = []
    seen_sessions = set()
    for a in assignments:
        if a.session_id not in seen_sessions:
            seen_sessions.add(a.session_id)
            student_count = 0
            try:
                from apps.students.models import Enrollment
                student_count = Enrollment.objects.filter(
                    session=a.session, status="Active"
                ).count()
            except Exception:
                pass
            sessions_data.append({
                "session": a.session,
                "subject": a.subject,
                "student_count": student_count,
                "assigned_from": a.assigned_from,
            })

    context = {
        "sessions": sessions_data,
        "page_title": "My Sessions",
    }
    return render(request, "dashboard/teacher_sessions.html", context)


@role_required("Teacher")
def teacher_session_detail(request, pk):
    """Show details of a session assigned to the teacher."""
    from apps.academics.models import TeacherAssignment, Session
    from django.shortcuts import get_object_or_404

    session = get_object_or_404(Session, pk=pk)

    # Verify teacher is assigned
    if not TeacherAssignment.objects.filter(
        teacher=request.user, session=session, is_active=True
    ).exists():
        raise Http404("You are not assigned to this session.")

    enrollments = []
    try:
        from apps.students.models import Enrollment
        enrollments = Enrollment.objects.filter(
            session=session, status="Active"
        ).select_related("student")
    except Exception:
        pass

    context = {
        "session": session,
        "enrollments": enrollments,
        "page_title": f"Session: {session.name}",
    }
    return render(request, "dashboard/teacher_session_detail.html", context)


@role_required("Teacher")
def teacher_session_students(request, pk):
    """List students in a session assigned to the teacher."""
    from apps.academics.models import TeacherAssignment, Session
    from django.shortcuts import get_object_or_404

    session = get_object_or_404(Session, pk=pk)

    if not TeacherAssignment.objects.filter(
        teacher=request.user, session=session, is_active=True
    ).exists():
        raise Http404("You are not assigned to this session.")

    enrollments = []
    try:
        from apps.students.models import Enrollment
        enrollments = Enrollment.objects.filter(
            session=session, status="Active"
        ).select_related("student")
    except Exception:
        pass

    context = {
        "session": session,
        "enrollments": enrollments,
        "page_title": f"Students: {session.name}",
    }
    return render(request, "dashboard/teacher_session_students.html", context)


@role_required("Teacher")
def teacher_profile_view(request):
    """Teacher profile view — redirects to shared profile."""
    from django.shortcuts import redirect
    return redirect("/accounts/profile/")


@role_required("Teacher")
def teacher_profile_edit(request):
    """Teacher profile edit — redirects to shared profile."""
    from django.shortcuts import redirect
    return redirect("/accounts/profile/")


@role_required("Admin")
def permission_matrix(request):
    """Enables granular control over CRM role permissions.

    Handles GET to view matrix and POST to update atomically with AuditLog logging.
    """
    from apps.core.models import RolePermission
    from apps.core.services import BaseService

    roles = [r[0] for r in RolePermission.ROLE_CHOICES]
    modules = [m[0] for m in RolePermission.MODULE_CHOICES]
    actions = ["view", "create", "edit", "delete", "export", "approve"]

    if request.method == "POST":
        from django.db import transaction

        changes_list = []
        with transaction.atomic():
            for role in roles:
                for module in modules:
                    can_view = request.POST.get(f"perm_{role}_{module}_view") == "on"
                    can_create = request.POST.get(f"perm_{role}_{module}_create") == "on"
                    can_edit = request.POST.get(f"perm_{role}_{module}_edit") == "on"
                    can_delete = request.POST.get(f"perm_{role}_{module}_delete") == "on"
                    can_export = request.POST.get(f"perm_{role}_{module}_export") == "on"
                    can_approve = request.POST.get(f"perm_{role}_{module}_approve") == "on"

                    obj, created = RolePermission.objects.update_or_create(
                        role_name=role,
                        module_name=module,
                        defaults={
                            "can_view": can_view,
                            "can_create": can_create,
                            "can_edit": can_edit,
                            "can_delete": can_delete,
                            "can_export": can_export,
                            "can_approve": can_approve,
                        }
                    )

                    changes_list.append({
                        "role": role,
                        "module": module,
                        "can_view": can_view,
                        "can_create": can_create,
                        "can_edit": can_edit,
                        "can_delete": can_delete,
                        "can_export": can_export,
                        "can_approve": can_approve,
                    })

            user_agent = request.META.get("HTTP_USER_AGENT", "")
            forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
            ip = forwarded.split(",")[0].strip() if forwarded else request.META.get("REMOTE_ADDR", "0.0.0.0")

            BaseService.audit_on_commit(
                user=request.user,
                action="update",
                model_name="core.RolePermission",
                object_id=None,
                changes={"matrix_update": changes_list},
                ip_address=ip,
                user_agent=user_agent
            )

        from django.shortcuts import redirect
        from django.urls import reverse
        from django.contrib import messages
        messages.success(request, "Permissions updated successfully.")
        return redirect(reverse("admin_panel:permissions"))

    permissions_qs = RolePermission.objects.all()

    if not permissions_qs.exists():
        from apps.core.permission_service import seed_default_permissions
        seed_default_permissions()
        permissions_qs = RolePermission.objects.all()

    matrix = {r: {m: None for m in modules} for r in roles}
    for perm in permissions_qs:
        if perm.role_name in matrix and perm.module_name in matrix[perm.role_name]:
            matrix[perm.role_name][perm.module_name] = perm

    context = {
        "matrix": matrix,
        "roles": roles,
        "modules": modules,
        "actions": actions,
        "role": "Admin",
    }
    return render(request, "dashboard/permissions.html", context)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from apps.core.decorators import role_required

@method_decorator(role_required("Admin", "Principal", "Accountant"), name="dispatch")
class AdminAnalyticsView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/analytics.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["role"] = "Admin"
        # We can reuse the metrics helper or return a standard dictionary
        from apps.dashboard.services import get_admin_dashboard_metrics
        context["metrics"] = get_admin_dashboard_metrics()

        from apps.analytics.services import get_teacher_workload
        context["workload"] = get_teacher_workload()

        # Inject Admission Funnel Analytics
        from django.utils import timezone
        from apps.admissions.analytics_service import (
            get_admission_funnel_metrics,
            get_admission_monthly_trend,
            get_session_demand,
            get_admissions_period_metrics,
        )
        context["funnel_metrics"] = get_admission_funnel_metrics()
        context["monthly_trend"] = get_admission_monthly_trend(timezone.now().year)
        context["session_demand"] = get_session_demand()
        context["period_metrics"] = get_admissions_period_metrics()
        return context


@method_decorator(role_required("Admin"), name="dispatch")
class AutomationAlertsView(LoginRequiredMixin, View):
    """Read-only list of system-generated automation alerts.

    Qualifying Notification categories (produced by automation services):
      - LateFee: from run_fee_reminders()
      - Attendance: from check_low_attendance()
      - ExamResult: from run_upcoming_exam_alerts()
      - System: general system alerts

    Ordering: newest first (-created_at)
    Pagination: not implemented (future enhancement)
    Empty state: "No automation alerts have been generated yet."
    Role access: Admin only (enforced by @role_required and sidebar visibility)
    """

    ALERT_CATEGORIES = ["LateFee", "Attendance", "ExamResult", "System"]

    def get(self, request, *args, **kwargs):
        from apps.notifications.models import Notification

        alerts = Notification.objects.filter(
            category__in=self.ALERT_CATEGORIES
        ).select_related("recipient").order_by("-created_at")[:200]

        return render(request, "dashboard/automation_alerts.html", {
            "alerts": alerts,
            "alert_categories": self.ALERT_CATEGORIES,
            "page_title": "System Alerts",
        })


@method_decorator(role_required("Admin"), name="dispatch")
class AutomationJobsView(LoginRequiredMixin, View):
    """Read-only status page for registered automation jobs.

    Shows the 3 registered automation tasks defined in
    apps.automation.tasks with their descriptions.

    Last execution: derived from AuditLog entries written by the
    automation services. Fee reminders write action='create' with
    model_name='students.Enrollment' and changes containing
    '"action": "fee_reminder_sent"'. Attendance checks write
    action='update' with model_name='students.Student' and changes
    containing 'has_low_attendance'. Exam alerts do not write
    AuditLog entries, so last-run is "Not recorded".

    Manual trigger: NOT supported. Celery is not configured in this
    project. Tasks are designed to be run via:
        python manage.py run_automation
    """

    def get(self, request, *args, **kwargs):
        from apps.core.models import AuditLog

        # Attempt to find last execution evidence from AuditLog
        last_fee = AuditLog.objects.filter(
            model_name="students.Enrollment",
            action="create",
            changes__contains="fee_reminder_sent",
        ).order_by("-timestamp").values_list("timestamp", flat=True).first()

        last_attendance = AuditLog.objects.filter(
            model_name="students.Student",
            action="update",
            changes__contains="has_low_attendance",
        ).order_by("-timestamp").values_list("timestamp", flat=True).first()

        jobs = [
            {
                "name": "Fee Reminders",
                "function": "run_fee_reminders()",
                "description": (
                    "Finds active enrollments with outstanding balance and "
                    "due date ≤ today. Sends notification and email to student "
                    "or guardian. Deduplicates by checking existing notifications "
                    "for the same day."
                ),
                "schedule": "Daily (via manage.py run_automation)",
                "last_run": last_fee,
                "last_run_source": "AuditLog" if last_fee else None,
            },
            {
                "name": "Low Attendance Check",
                "function": "check_low_attendance()",
                "description": (
                    "Flags students with attendance below 70% threshold. "
                    "Notifies all administrators. Automatically unflags "
                    "students who rise above the threshold."
                ),
                "schedule": "Daily (via manage.py run_automation)",
                "last_run": last_attendance,
                "last_run_source": "AuditLog" if last_attendance else None,
            },
            {
                "name": "Upcoming Exam Alerts",
                "function": "run_upcoming_exam_alerts()",
                "description": (
                    "Alerts students and guardians of exams scheduled within "
                    "the next 3 days. Sends notification and email. "
                    "Deduplicates by exam ID per recipient."
                ),
                "schedule": "Daily (via manage.py run_automation)",
                "last_run": None,
                "last_run_source": None,
            },
        ]

        return render(request, "dashboard/automation_jobs.html", {
            "jobs": jobs,
            "page_title": "Background Jobs",
            "run_command": "python manage.py run_automation",
        })


@role_required("Admin", "Principal", "Registrar", "Accountant")
def session_overview(request):
    sessions = []
    total_sessions = 0
    active_count = 0

    try:
        from apps.academics.models import Session
        from django.db.models import Count
        sessions = (
            Session.objects
            .annotate(
                student_count=Count(
                    "enrollments",
                    distinct=True,
                )
            )
            .order_by("-created_at")
        )
        total_sessions = sessions.count()
        active_count = sessions.filter(
            status="Active"
        ).count()
    except Exception:
        sessions = []

    context = {
        "sessions": sessions,
        "total_sessions": total_sessions,
        "active_count": active_count,
        "page_title": "Session Overview",
    }
    return render(
        request,
        "dashboard/session_overview.html",
        context,
    )


@role_required("Admin", "Principal")
def session_result_summary(request, pk):
    """Admin/Principal view for session-wide results summary."""
    from apps.academics.models import Session
    from decimal import Decimal
    from django.shortcuts import get_object_or_404

    session = get_object_or_404(Session, pk=pk)

    student_summaries = []
    class_average = Decimal("0.00")
    pass_rate = Decimal("0.00")
    top_performers = []
    total_students = 0

    try:
        from apps.students.models import Enrollment
        from apps.exams.transcript_service import generate_student_transcript

        enrollments = Enrollment.objects.filter(
            session=session, status="Active"
        ).select_related("student")

        total_percentage_sum = Decimal("0.00")
        pass_count = 0

        for enroll in enrollments:
            try:
                summary = generate_student_transcript(enroll.student_id)
                if summary:
                    student_summaries.append(summary)
                    total_percentage_sum += summary.get("overall_percentage", Decimal("0.00"))
                    if summary.get("overall_result") == "Pass":
                        pass_count += 1
            except Exception:
                continue

        total_students = len(student_summaries)
        if total_students > 0:
            class_average = (total_percentage_sum / Decimal(total_students)).quantize(Decimal("0.01"))
            pass_rate = (Decimal(pass_count) / Decimal(total_students) * Decimal("100")).quantize(Decimal("0.01"))

        student_summaries.sort(key=lambda x: x.get("overall_percentage", Decimal("0.00")), reverse=True)

        current_rank = 1
        last_pct = None
        for index, s in enumerate(student_summaries):
            pct = s.get("overall_percentage", Decimal("0.00"))
            if last_pct is not None and pct < last_pct:
                current_rank = index + 1
            s["rank"] = current_rank
            last_pct = pct

        top_performers = student_summaries[:3]

    except Exception:
        pass

    context = {
        "session": session,
        "students": student_summaries,
        "class_average": class_average,
        "pass_rate": pass_rate,
        "top_performers": top_performers,
        "total_students": total_students,
        "page_title": f"Results: {session.name}",
    }
    return render(request, "exams/session_results.html", context)


@role_required("Admin", "Principal")
def faculty_overview(request):
    faculties = []
    total_faculty = 0
    active_count = 0

    try:
        from apps.staff.models import FacultyProfile

        faculty_qs = FacultyProfile.objects.select_related("user").order_by("user__first_name")
        total_faculty = faculty_qs.count()
        active_count = faculty_qs.filter(is_active=True).count()

        for fp in faculty_qs:
            faculties.append({
                "pk": fp.pk,
                "full_name": fp.user.full_name if fp.user else "Unnamed",
                "email": fp.user.email if fp.user else "N/A",
                "phone": fp.user.phone if fp.user and fp.user.phone else "N/A",
                "designation": fp.designation,
                "status": "Active" if fp.is_active else "Inactive",
            })
    except Exception:
        faculties = []

    context = {
        "faculties": faculties,
        "total_faculty": total_faculty,
        "active_count": active_count,
        "page_title": "Faculty Overview",
    }
    return render(request, "dashboard/faculty_overview.html", context)


@role_required("Admin", "Principal")
def timetable_overview(request):
    schedules = []
    total_classes = 0

    try:
        from apps.academics.models import ClassSchedule
        schedules = (
            ClassSchedule.objects
            .select_related("session", "subject", "faculty__user")
            .filter(is_active=True)
            .order_by("day_of_week", "start_time")
        )
        total_classes = schedules.count()
    except Exception:
        schedules = []

    context = {
        "schedules": schedules,
        "total_classes": total_classes,
        "page_title": "Timetable Overview",
    }
    return render(request, "dashboard/timetable_overview.html", context)


@role_required("Admin", "Principal")
def exam_overview(request):
    exams = []
    total_exams = 0
    upcoming_count = 0

    try:
        from apps.exams.models import Exam
        from django.utils import timezone

        exam_qs = Exam.objects.select_related(
            "session", "subject"
        ).order_by("-exam_date")

        total_exams = exam_qs.count()
        today = timezone.localdate()
        upcoming_count = exam_qs.filter(exam_date__gte=today).count()
        exams = exam_qs

    except Exception:
        exams = []

    context = {
        "exams": exams,
        "total_exams": total_exams,
        "upcoming_count": upcoming_count,
        "page_title": "Exam Overview",
    }
    return render(request, "dashboard/exam_overview.html", context)


def session_detail(request, pk):
    from apps.academics.views import session_detail as academics_session_detail
    return academics_session_detail(request, pk)


@role_required("Admin", "Principal")
def reports_dashboard_proxy(request):
    return redirect("reports:dashboard")


