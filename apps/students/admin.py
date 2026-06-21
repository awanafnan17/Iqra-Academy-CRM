"""
Students admin - Student, Lead, Enrollment, StudentDocument, Guardian.
"""

from django.contrib import admin

from apps.students.models import (
    Enrollment,
    Guardian,
    Lead,
    Student,
    StudentDocument,
)


class StudentDocumentInline(admin.TabularInline):
    """Inline for student documents."""

    model = StudentDocument
    extra = 0
    readonly_fields = ("created_at", "updated_at")


class GuardianInline(admin.StackedInline):
    """Inline for student guardians."""

    model = Guardian
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    """Student admin with soft-delete manager override and inlines.

    Uses all_objects to show both active and soft-deleted students.
    """

    list_display = (
        "full_name",
        "roll_number",
        "gender",
        "status",
        "is_deleted",
    )
    list_filter = ("gender", "status", "is_deleted")
    search_fields = ("full_name", "roll_number", "father_name", "phone")
    ordering = ("full_name",)
    readonly_fields = ("created_at", "updated_at", "deleted_at", "deleted_by")
    inlines = [StudentDocumentInline, GuardianInline]

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Lead management admin."""

    list_display = (
        "name",
        "phone",
        "email",
        "inquiry_source",
        "status",
        "interested_session",
        "follow_up_date",
        "handled_by",
    )
    list_filter = ("status", "inquiry_source", "inquiry_date")
    search_fields = ("name", "phone", "email")
    ordering = ("-inquiry_date",)
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "inquiry_date"
    autocomplete_fields = ("interested_session", "converted_student", "handled_by")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """Enrollment admin with soft-delete manager override.

    Uses all_objects to show both active and soft-deleted enrollments.
    """

    list_display = (
        "student",
        "session",
        "status",
        "registration_date",
        "fee",
        "discount",
        "is_deleted",
    )
    list_filter = ("status", "is_deleted")
    search_fields = (
        "student__full_name",
        "student__roll_number",
        "session__name",
    )
    ordering = ("-registration_date",)
    readonly_fields = ("created_at", "updated_at", "deleted_at", "deleted_by")
    autocomplete_fields = ("student", "session")

    def get_queryset(self, request):
        return self.model.all_objects.all()


@admin.register(StudentDocument)
class StudentDocumentAdmin(admin.ModelAdmin):
    """Standalone student document admin."""

    list_display = (
        "student",
        "document_type",
        "title",
        "file_size",
        "uploaded_by",
        "created_at",
    )
    list_filter = ("document_type",)
    search_fields = ("student__full_name", "title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    """Standalone guardian admin."""

    list_display = (
        "full_name",
        "student",
        "relationship",
        "phone",
        "is_primary",
        "is_emergency_contact",
    )
    list_filter = ("relationship", "is_primary")
    search_fields = ("full_name", "phone", "student__full_name")
    ordering = ("full_name",)
    readonly_fields = ("created_at", "updated_at")
