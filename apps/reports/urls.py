from django.urls import path
from apps.reports import views

app_name = "reports"

urlpatterns = [
    # Dashboards
    path("", views.ReportsDashboardView.as_view(), name="dashboard"),

    # Exports
    path("pending-dues/csv/", views.PendingDuesExportCSVView.as_view(), name="pending_dues_csv"),
    path("pending-dues/pdf/", views.PendingDuesPDFView.as_view(), name="pending_dues_pdf"),
    path("session-results/<int:session_id>/csv/", views.SessionResultsExportCSVView.as_view(), name="session_results_csv"),
    path("session-results/<int:session_id>/pdf/", views.SessionResultsPDFView.as_view(), name="session_results_pdf"),
    path("student-directory/csv/", views.StudentDirectoryExportCSVView.as_view(), name="student_directory_csv"),
    path("teacher-workload/csv/", views.TeacherWorkloadExportCSVView.as_view(), name="teacher_workload_csv"),
    path("teacher-workload/pdf/", views.TeacherWorkloadPDFView.as_view(), name="teacher_workload_pdf"),

    # Success Reports
    path("success/csv/", views.SuccessReportExportCSVView.as_view(), name="success_csv"),
    path("success/pdf/", views.SuccessReportPDFView.as_view(), name="success_pdf"),

    # Transcripts
    path("student/<int:student_id>/transcript/pdf/", views.StudentTranscriptPDFView.as_view(), name="student_transcript_pdf"),
]
