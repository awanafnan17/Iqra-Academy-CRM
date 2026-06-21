"""
Student app URL patterns.

Included by admin_panel under prefix 'students/'.
Role enforcement handled by PanelAccessMiddleware at the panel level.
Admin-only views have additional @role_required("Admin") in URL patterns.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.students import views as student_views
from apps.admissions import views as admission_views

app_name = "students"

urlpatterns = [
    # Student CRUD
    path("", student_views.student_list, name="student_list"),
    path("create/", student_views.student_create, name="student_create"),
    path("<int:pk>/", student_views.student_detail, name="student_detail"),
    path("<int:pk>/edit/", student_views.student_edit, name="student_edit"),
    path(
        "<int:pk>/delete/",
        role_required("Admin")(student_views.student_delete),
        name="student_delete",
    ),
    path(
        "<int:pk>/restore/",
        role_required("Admin")(student_views.student_restore),
        name="student_restore",
    ),
    path("<int:pk>/documents/", student_views.student_documents, name="student_documents"),
    path("<int:pk>/documents/upload/", student_views.student_document_upload, name="student_document_upload"),
    path("<int:pk>/guardians/", student_views.student_guardians, name="student_guardians"),
    path("<int:pk>/ledger/", student_views.student_ledger, name="student_ledger"),

    # Lead management
    path("leads/", student_views.lead_list, name="lead_list"),
    path("leads/create/", student_views.lead_create, name="lead_create"),
    path("leads/<int:pk>/", student_views.lead_detail, name="lead_detail"),
    path("leads/<int:pk>/edit/", student_views.lead_edit, name="lead_edit"),
    path("leads/<int:pk>/convert/", student_views.lead_convert, name="lead_convert"),

    # Enrollment management
    path("enrollments/", student_views.enrollment_list, name="enrollment_list"),
    path("enrollments/create/", student_views.enrollment_create, name="enrollment_create"),
    path("enrollments/<int:pk>/", student_views.enrollment_detail, name="enrollment_detail"),
    path("enrollments/<int:pk>/withdraw/", student_views.enrollment_withdraw, name="enrollment_withdraw"),
    path(
        "enrollments/<int:pk>/restore/",
        role_required("Admin")(student_views.enrollment_restore),
        name="enrollment_restore",
    ),
    path("enrollments/<int:pk>/freeze/", student_views.enrollment_freeze, name="enrollment_freeze"),
    path("enrollments/<int:pk>/unfreeze/", student_views.enrollment_unfreeze, name="enrollment_unfreeze"),
    path(
        "enrollments/<int:pk>/transfer/",
        role_required("Admin")(student_views.enrollment_transfer),
        name="enrollment_transfer",
    ),
]
