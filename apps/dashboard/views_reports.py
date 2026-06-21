"""
Report views for the Academy CRM.

Provides report generation, CSV export, and PDF stub views.
All views are stubs for Phase 1 (RBAC + Routing).
"""

from django.http import HttpResponse


def _stub(name):
    """Create a placeholder view function."""
    def view(request, *args, **kwargs):
        return HttpResponse(
            f"{name} - Coming soon",
            content_type="text/plain",
        )
    view.__name__ = name
    view.__qualname__ = name
    return view


# -------------------------------------------------------------------
#  Report views
# -------------------------------------------------------------------

report_revenue = _stub("report_revenue")
report_attendance = _stub("report_attendance")
report_enrollment = _stub("report_enrollment")
report_overdue = _stub("report_overdue")

# -------------------------------------------------------------------
#  CSV export views
# -------------------------------------------------------------------

export_students_csv = _stub("export_students_csv")
export_payments_csv = _stub("export_payments_csv")
export_attendance_csv = _stub("export_attendance_csv")

# -------------------------------------------------------------------
#  PDF stub views (deferred formatting)
# -------------------------------------------------------------------

pdf_student_ledger = _stub("pdf_student_ledger")
pdf_attendance_report = _stub("pdf_attendance_report")
