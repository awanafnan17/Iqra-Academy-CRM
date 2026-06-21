"""
Attendance admin - AttendanceRecord, AttendanceLock.
"""

from django.contrib import admin

from apps.attendance.models import AttendanceLock, AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    """Attendance record admin with date hierarchy."""

    list_display = (
        "student",
        "session",
        "date",
        "status",
        "marked_by",
    )
    list_filter = ("status", "date", "session")
    search_fields = (
        "student__full_name",
        "student__roll_number",
    )
    ordering = ("-date",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "date"
    autocomplete_fields = ("student", "session")


@admin.register(AttendanceLock)
class AttendanceLockAdmin(admin.ModelAdmin):
    """Attendance lock admin with locked_by as readonly."""

    list_display = (
        "session",
        "date",
        "locked_by",
        "locked_at",
        "reason",
    )
    list_filter = ("session",)
    search_fields = ("session__name", "reason")
    ordering = ("-locked_at",)
    readonly_fields = ("locked_by",)
    autocomplete_fields = ("session",)
