"""
Teacher panel URL configuration.

Accessible by Teacher role only.
Panel-level access enforced by PanelAccessMiddleware.
All session/exam views require TeacherAssignment verification
at the view level (not the URL level).
"""

from django.urls import path

from apps.attendance import views as attendance_views
from apps.dashboard import views as dashboard_views
from apps.exams import views as exam_views
from apps.notifications import views as notification_views
from apps.academics import views as academics_views

app_name = "teacher_panel"

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_views.teacher_dashboard, name="dashboard"),
    path("my-timetable/", academics_views.timetable_teacher, name="my_timetable"),

    # Sessions (teacher-specific views)
    path("sessions/", dashboard_views.my_sessions, name="my_sessions"),
    path("sessions/<int:pk>/", dashboard_views.teacher_session_detail, name="session_detail"),
    path("sessions/<int:pk>/students/", dashboard_views.teacher_session_students, name="session_students"),

    # Attendance (scoped to assigned sessions)
    path("attendance/mark/<int:session_id>/", attendance_views.attendance_mark, name="attendance_mark"),
    path(
        "attendance/<int:session_id>/date/<str:date>/",
        attendance_views.attendance_sheet,
        name="attendance_sheet",
    ),
    path(
        "attendance/<int:session_id>/analytics/",
        attendance_views.attendance_analytics,
        name="attendance_analytics",
    ),

    # Exams (scoped to assigned subjects)
    path("exams/", exam_views.exam_list, name="my_exams"),
    path("exams/create/", exam_views.exam_create, name="exam_create"),
    path("exams/<int:pk>/", exam_views.exam_detail, name="exam_detail"),
    path("exams/<int:pk>/edit/", exam_views.exam_edit, name="exam_edit"),
    path("exams/<int:pk>/results/entry/", exam_views.exam_results_entry, name="exam_results_entry"),
    path("exams/<int:pk>/results/", exam_views.exam_results, name="exam_results"),

    # Notifications
    path("notifications/", notification_views.notification_list, name="notification_list"),
    path("notifications/<int:pk>/", notification_views.notification_detail, name="notification_detail"),
    path("notifications/mark-read/", notification_views.notification_mark_read, name="notification_mark_read"),

    # Profile
    path("profile/", dashboard_views.teacher_profile_view, name="profile_view"),
    path("profile/edit/", dashboard_views.teacher_profile_edit, name="profile_edit"),
]
