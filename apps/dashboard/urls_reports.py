"""
Report URL patterns.

Included by admin_panel under prefix 'reports/'.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.dashboard import views_reports as views

app_name = "reports"

urlpatterns = [
    path(
        "revenue/",
        role_required("Admin")(views.report_revenue),
        name="report_revenue",
    ),
    path("attendance/", views.report_attendance, name="report_attendance"),
    path("enrollment/", views.report_enrollment, name="report_enrollment"),
    path(
        "overdue/",
        role_required("Admin")(views.report_overdue),
        name="report_overdue",
    ),

    # CSV exports
    path(
        "export/students/",
        role_required("Admin")(views.export_students_csv),
        name="export_students_csv",
    ),
    path(
        "export/payments/",
        role_required("Admin")(views.export_payments_csv),
        name="export_payments_csv",
    ),
    path("export/attendance/", views.export_attendance_csv, name="export_attendance_csv"),

    # PDF stubs
    path("pdf/ledger/<int:enrollment_id>/", views.pdf_student_ledger, name="pdf_student_ledger"),
    path("pdf/attendance/<int:session_id>/", views.pdf_attendance_report, name="pdf_attendance_report"),
]
