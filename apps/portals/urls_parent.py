"""
Guardian (Parent) portal URL configuration.

Accessible by Guardian role only.
"""

from django.urls import path
from apps.portals import views_parent as views
from apps.reports import views as reports_views

app_name = "guardian_portal"

urlpatterns = [
    path("dashboard/", views.GuardianDashboardView.as_view(), name="dashboard"),
    path("children/", views.GuardianChildrenView.as_view(), name="my_children"),

    # Child-scoped URLs
    path("child/<int:student_id>/profile/", views.GuardianChildDetailView.as_view(), name="child_detail"),
    path("child/<int:student_id>/attendance/", views.GuardianChildAttendanceView.as_view(), name="child_attendance"),
    path("child/<int:student_id>/fees/", views.GuardianChildFeesView.as_view(), name="child_payments"),
    path("child/<int:student_id>/exams/", views.GuardianChildExamsView.as_view(), name="child_exams"),
    path("child/<int:student_id>/transcript/", views.child_transcript, name="child_transcript"),
    path("child/<int:student_id>/transcript/pdf/", reports_views.StudentTranscriptPDFView.as_view(), name="child_transcript_pdf"),
    path("child/<int:student_id>/fees/<int:payment_id>/receipt/", views.GuardianChildFeeReceiptPDFView.as_view(), name="download_receipt"),

    # Backward compatibility mappings
    path("children/<int:student_id>/", views.GuardianChildDetailView.as_view(), name="child_detail_old"),
    path("children/<int:student_id>/attendance/", views.GuardianChildAttendanceView.as_view(), name="child_attendance_old"),
    path("children/<int:student_id>/payments/", views.GuardianChildFeesView.as_view(), name="child_payments_old"),
    path("children/<int:student_id>/exams/", views.GuardianChildExamsView.as_view(), name="child_exams_old"),

    # Notifications
    path("notifications/", views.GuardianNotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/", views.GuardianNotificationDetailView.as_view(), name="notification_detail"),
    path("notifications/mark-read/", views.GuardianNotificationMarkReadView.as_view(), name="notification_mark_read"),
]
