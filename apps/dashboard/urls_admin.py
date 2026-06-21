"""
Admin panel master URL configuration.

Accessible by Admin and Principal roles.
Panel-level access enforced by PanelAccessMiddleware.
View-level Admin-only restrictions enforced by @role_required("Admin")
in individual app URL files.
"""

from django.urls import include, path
from django.views.generic import RedirectView

from apps.dashboard import views
from apps.finance import views as finance_views
from apps.students import views as student_views
from apps.academics import views as academics_views
from apps.documents import views as documents_views
from apps.achievements.views import SuccessDashboardView

app_name = "admin_panel"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    path("permissions/", views.permission_matrix, name="permissions"),
    path("session-overview/", views.session_overview, name="session_overview"),
    path("faculty-overview/", views.faculty_overview, name="faculty_overview"),
    path("timetable-overview/", views.timetable_overview, name="timetable_overview"),
    path("exam-overview/", views.exam_overview, name="exam_overview"),
    path("success/", SuccessDashboardView.as_view(), name="success_dashboard"),
    path("session/<int:pk>/results/", views.session_result_summary, name="session_result_summary"),
    path("pending-dues/", finance_views.PendingDuesView.as_view(), name="pending_dues"),
    path("users/", include("apps.accounts.urls_admin")),

    # Timetable
    path("timetable/", academics_views.timetable_list, name="timetable_list"),
    path("timetable/create/", academics_views.timetable_create, name="timetable_create"),
    path("timetable/<int:pk>/edit/", academics_views.timetable_edit, name="timetable_edit"),
    path("timetable/<int:pk>/toggle-status/", academics_views.timetable_toggle_status, name="timetable_toggle_status"),


    # ERP Grouped Navigation Shortcuts / Direct Routes
    path("students/<int:pk>/reset-password/", student_views.student_reset_password, name="student_reset_password"),
    path("students/<int:pk>/create-login/", student_views.student_create_login, name="student_create_login"),
    path("add-student/", student_views.student_create, name="add_student"),
    path("manage-students/", student_views.student_list, name="manage_students"),
    path("add-session/", academics_views.session_create, name="add_session"),
    # Session Management Direct Paths (Stage 5)
    path("sessions/", views.session_overview, name="session_list"),
    path("sessions/create/", academics_views.session_create, name="session_create"),
    path("sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path("sessions/<int:pk>/edit/", academics_views.session_edit, name="session_edit"),
    path("sessions/<int:pk>/results/", views.session_result_summary, name="session_result"),
    path("manage-faculty/", include("apps.staff.urls")),
    path("analytics/", views.AdminAnalyticsView.as_view(), name="analytics"),
    path("automation/alerts/", views.AutomationAlertsView.as_view(), name="automation_alerts"),
    path("automation/jobs/", views.AutomationJobsView.as_view(), name="automation_jobs"),
    path("reports-dashboard/", views.reports_dashboard_proxy, name="reports_dashboard"),
    path("finance/installments/<int:pk>/pay/", finance_views.InstallmentPayView.as_view(), name="installment_pay"),


    # Module includes
    path("students/", include("apps.students.urls")),
    path("academics/", include("apps.academics.urls")),
    path("attendance/", include("apps.attendance.urls")),
    path("exams/", include("apps.exams.urls")),
    path("finance/", include("apps.finance.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("documents/", include("apps.documents.urls")),
    path("ai/", include("apps.ai_engine.urls")),
    path("dashboard-reports/", include("apps.dashboard.urls_reports")),
    path("audit/", include("apps.core.urls_audit")),
    path("pdf-comparison/", documents_views.pdf_comparison, name="pdf_comparison"),
    path("pdf-comparison/export/<int:job_id>/", documents_views.export_comparison_csv, name="export_comparison_csv"),
    path("pdf-comparison/export-preview/", documents_views.export_preview_csv, name="export_preview_csv"),
    path("admissions/", include("apps.admissions.urls")),
]

