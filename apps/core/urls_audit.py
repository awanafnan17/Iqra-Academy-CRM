"""
Audit log URL patterns.

Included by admin_panel under prefix 'audit/'. Admin only.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.core import views

app_name = "audit"

urlpatterns = [
    path(
        "",
        role_required("Admin")(views.audit_log_list),
        name="audit_log_list",
    ),
    path(
        "<int:pk>/",
        role_required("Admin")(views.audit_log_detail),
        name="audit_log_detail",
    ),
]
