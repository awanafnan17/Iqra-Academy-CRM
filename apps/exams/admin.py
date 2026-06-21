"""
Exams admin - Exam, ExamResult, GradeConfig.
"""

from django.contrib import admin

from apps.exams.models import Exam, ExamResult, GradeConfig


class ExamResultInline(admin.TabularInline):
    """Inline for exam results within an exam."""

    model = ExamResult
    extra = 0
    readonly_fields = ("created_at", "updated_at", "percentage", "rank")


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    """Exam admin with exam result inline."""

    list_display = (
        "name",
        "session",
        "subject",
        "exam_type",
        "total_marks",
        "exam_date",
        "is_published",
    )
    list_filter = ("exam_type", "session", "subject", "is_published")
    search_fields = ("name", "session__name", "subject__name")
    ordering = ("-exam_date", "name")
    readonly_fields = ("created_at", "updated_at", "created_by")
    date_hierarchy = "exam_date"
    inlines = [ExamResultInline]
    autocomplete_fields = ("session", "subject")


@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    """Standalone exam result admin."""

    list_display = (
        "student",
        "exam",
        "marks_obtained",
        "percentage",
        "grade",
        "rank",
        "is_absent",
    )
    list_filter = ("is_absent", "grade")
    search_fields = (
        "student__full_name",
        "exam__name",
    )
    ordering = ("-marks_obtained",)
    readonly_fields = ("created_at", "updated_at", "percentage", "rank")


@admin.register(GradeConfig)
class GradeConfigAdmin(admin.ModelAdmin):
    """Grade configuration admin ordered by sort_order."""

    list_display = (
        "grade_name",
        "session",
        "min_percentage",
        "max_percentage",
        "grade_point",
        "sort_order",
    )
    list_filter = ("session",)
    search_fields = ("grade_name",)
    ordering = ("sort_order",)
    readonly_fields = ("created_at", "updated_at")
    autocomplete_fields = ("session",)
