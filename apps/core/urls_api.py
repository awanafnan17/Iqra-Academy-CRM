"""
Internal API URL patterns (AJAX endpoints).
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.core import views

app_name = "api"

urlpatterns = [
    path(
        "students/search/",
        role_required("Admin", "Principal", "Accountant", "Registrar")(views.api_student_search),
        name="api_student_search",
    ),
    path(
        "sessions/search/",
        role_required("Admin", "Principal", "Accountant", "Registrar")(views.api_session_search),
        name="api_session_search",
    ),
    path(
        "notifications/unread-count/",
        views.api_unread_count,
        name="api_unread_count",
    ),
    path(
        "attendance/bulk-mark/",
        role_required("Admin", "Principal", "Teacher")(views.api_attendance_bulk_mark),
        name="api_attendance_bulk_mark",
    ),
    path(
        "dashboard/stats/",
        role_required("Admin", "Principal", "Accountant", "Registrar")(views.api_dashboard_stats),
        name="api_dashboard_stats",
    ),
]
