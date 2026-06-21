"""
Academics app URL patterns.

Included by admin_panel under prefix 'academics/'.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.academics import views

app_name = "academics"

urlpatterns = [
    # Sessions
    path("sessions/create/", views.session_create, name="session_create"),
    path("sessions/<int:pk>/", views.session_detail, name="session_detail"),
    path("sessions/<int:pk>/edit/", views.session_edit, name="session_edit"),
    path("sessions/<int:pk>/toggle-status/", views.session_toggle_status, name="session_toggle_status"),
    path(
        "sessions/<int:pk>/delete/",
        role_required("Admin")(views.session_delete),
        name="session_delete",
    ),
    path("sessions/<int:pk>/enrollments/", views.session_enrollments, name="session_enrollments"),
    path(
        "sessions/<int:pk>/revenue/",
        role_required("Admin")(views.session_revenue),
        name="session_revenue",
    ),

    # Subjects
    path("subjects/create/", views.subject_create, name="subject_create"),
    path("subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),

    # Teacher Assignments
    path("assignments/create/", views.assignment_create, name="assignment_create"),
    path("assignments/<int:pk>/edit/", views.assignment_edit, name="assignment_edit"),
    path(
        "assignments/<int:pk>/delete/",
        role_required("Admin")(views.assignment_delete),
        name="assignment_delete",
    ),
]
