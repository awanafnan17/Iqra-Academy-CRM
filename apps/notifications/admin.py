"""
Notifications admin - Notification, NotificationTemplate, EmailLog.
"""

from django.contrib import admin

from apps.notifications.models import EmailLog, Notification, NotificationTemplate


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin with category and read-status filters."""

    list_display = (
        "title",
        "recipient",
        "category",
        "is_read",
        "created_at",
    )
    list_filter = ("is_read", "category")
    search_fields = ("title", "recipient__username")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Notification template admin."""

    list_display = (
        "name",
        "code",
        "channel",
        "is_active",
        "created_at",
    )
    list_filter = ("channel", "is_active")
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """Fully read-only email log viewer.

    No records may be added, changed, or deleted through the admin.
    """

    list_display = (
        "recipient_email",
        "subject",
        "status",
        "sent_at",
        "sent_by",
    )
    list_filter = ("status", "sent_at")
    search_fields = ("recipient_email", "subject")
    ordering = ("-sent_at",)
    readonly_fields = (
        "recipient_email",
        "subject",
        "body_preview",
        "status",
        "error_message",
        "sent_at",
        "notification",
        "sent_by",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
