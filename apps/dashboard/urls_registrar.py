"""
Registrar (Receptionist) panel URL configuration.

Accessible by Registrar role only.
Panel-level access enforced by PanelAccessMiddleware.
"""

from django.urls import include, path

from apps.academics import views as academic_views
from apps.dashboard import views as dashboard_views
from apps.notifications import views as notification_views
from apps.students import views as student_views

app_name = "registrar_panel"

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_views.registrar_dashboard, name="dashboard"),

    # Students
    path("students/", student_views.student_list, name="student_list"),
    path("students/create/", student_views.student_create, name="student_create"),
    path("students/<int:pk>/", student_views.student_detail, name="student_detail"),
    path("students/<int:pk>/edit/", student_views.student_edit, name="student_edit"),
    path("students/<int:pk>/documents/upload/", student_views.student_document_upload, name="student_document_upload"),
    path("students/<int:pk>/guardians/", student_views.student_guardians, name="student_guardians"),

    # Leads
    path("leads/", student_views.lead_list, name="lead_list"),
    path("leads/create/", student_views.lead_create, name="lead_create"),
    path("leads/<int:pk>/", student_views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/edit/", student_views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/convert/", student_views.lead_convert, name="lead_convert"),

    # Enrollments (create + view only)
    path("enrollments/create/", student_views.enrollment_create, name="enrollment_create"),
    path("enrollments/<int:pk>/", student_views.enrollment_detail, name="enrollment_detail"),

    # Sessions (read-only)
    path("sessions/", dashboard_views.session_overview, name="session_list"),
    path("sessions/<int:pk>/", academic_views.session_detail, name="session_detail"),

    # Notifications
    path("notifications/", notification_views.notification_list, name="notification_list"),
    path("notifications/mark-read/", notification_views.notification_mark_read, name="notification_mark_read"),
    path("admissions/", include("apps.admissions.urls")),
]
