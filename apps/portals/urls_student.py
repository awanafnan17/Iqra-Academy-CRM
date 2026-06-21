"""
Student portal URL configuration.

Accessible by Student role only.
"""

from django.urls import path
from apps.portals import views_student as views
from apps.reports import views as reports_views

app_name = "student_portal"

urlpatterns = [
    path("dashboard/", views.StudentDashboardView.as_view(), name="dashboard"),
    path("profile/", views.StudentProfileView.as_view(), name="profile_view"),
    path("enrollment/", views.my_enrollment, name="my_enrollment"),
    path("attendance/", views.StudentAttendanceView.as_view(), name="my_attendance"),
    path("exams/", views.StudentExamsView.as_view(), name="my_exams"),
    path("exams/<int:pk>/", views.exam_result_detail, name="exam_result_detail"),
    path("transcript/", views.student_transcript, name="student_transcript"),
    path("transcript/pdf/", reports_views.StudentTranscriptPDFView.as_view(), name="student_transcript_pdf"),
    path("payments/", views.my_payments, name="my_payments"),
    path("fees/", views.StudentFeesView.as_view(), name="my_fees"),
    path("fees/<int:payment_id>/receipt/", views.StudentFeeReceiptPDFView.as_view(), name="download_receipt"),
    path("timetable/", views.student_timetable, name="timetable"),
    path("notifications/", views.StudentNotificationListView.as_view(), name="notification_list"),
    path("notifications/<int:pk>/", views.StudentNotificationDetailView.as_view(), name="notification_detail"),
    path("notifications/mark-read/", views.StudentNotificationMarkReadView.as_view(), name="notification_mark_read"),
    path("password/", views.StudentPasswordChangeView.as_view(), name="password_change"),
]
