"""
Attendance app URL patterns.

Included by admin_panel under prefix 'attendance/'.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.attendance import views

app_name = "attendance"

urlpatterns = [
    path("", views.attendance_overview, name="attendance_overview"),
    path("mark/<int:session_id>/", views.attendance_mark, name="attendance_mark"),
    path(
        "<int:session_id>/date/<str:date>/",
        views.attendance_sheet,
        name="attendance_sheet",
    ),
    path(
        "<int:session_id>/lock/",
        views.attendance_lock,
        name="attendance_lock",
    ),
    path(
        "<int:session_id>/unlock/",
        role_required("Admin")(views.attendance_unlock),
        name="attendance_unlock",
    ),
    path(
        "<int:session_id>/analytics/",
        views.attendance_analytics,
        name="attendance_analytics",
    ),
    path("low-attendance/", views.low_attendance_report, name="low_attendance_report"),
]
