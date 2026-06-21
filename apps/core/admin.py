"""
Core admin - AuditLog (fully read-only).
"""

from django.contrib import admin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Fully read-only audit log viewer.

    No records may be added, changed, or deleted through the admin.
    """

    list_display = (
        "user",
        "action",
        "model_name",
        "object_id",
        "timestamp",
        "ip_address",
    )
    list_filter = ("action", "model_name", "timestamp")
    search_fields = (
        "user__username",
        "model_name",
        "object_id",
        "ip_address",
    )
    ordering = ("-timestamp",)
    date_hierarchy = "timestamp"
    readonly_fields = (
        "user",
        "action",
        "model_name",
        "object_id",
        "changes",
        "ip_address",
        "user_agent",
        "timestamp",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
