"""
Academics admin - Session, Subject, TeacherAssignment.
"""

from django.contrib import admin

from apps.academics.models import Session, Subject, TeacherAssignment


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    """Session admin with soft-delete manager override.

    Uses all_objects to show both active and soft-deleted sessions.
    """

    list_display = (
        "name",
        "code",
        "session_type",
        "status",
        "fee",
        "start_date",
        "end_date",
        "is_deleted",
    )
    list_filter = ("session_type", "status", "is_deleted")
    search_fields = ("name", "code")
    ordering = ("-start_date",)
    readonly_fields = ("created_at", "updated_at", "deleted_at", "deleted_by")
    date_hierarchy = "start_date"

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    """Subject admin with is_active filter."""

    list_display = ("name", "code", "session", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "code")
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("session",)


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    """Teacher assignment admin with autocomplete fields."""

    list_display = (
        "teacher",
        "session",
        "subject",
        "assigned_from",
        "assigned_until",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = (
        "teacher__username",
        "teacher__first_name",
        "teacher__last_name",
        "session__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("teacher", "session", "subject")
