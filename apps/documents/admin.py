from django.contrib import admin
from apps.documents.models import ComparisonJob, ComparisonResult

class ComparisonResultInline(admin.TabularInline):
    model = ComparisonResult
    extra = 0
    readonly_fields = (
        "student",
        "extracted_name",
        "extracted_roll",
        "match_confidence",
        "is_exact_match",
        "created_at",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ComparisonJob)
class ComparisonJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "exam_type",
        "uploaded_by",
        "uploaded_at",
        "total_entries",
        "matched_entries",
        "status",
    )
    list_filter = ("exam_type", "status")
    search_fields = ("uploaded_by__username", "exam_type")
    ordering = ("-uploaded_at",)
    readonly_fields = ("uploaded_at",)
    inlines = [ComparisonResultInline]


@admin.register(ComparisonResult)
class ComparisonResultAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job",
        "student",
        "extracted_name",
        "extracted_roll",
        "match_confidence",
        "is_exact_match",
        "created_at",
    )
    list_filter = ("is_exact_match", "job__exam_type")
    search_fields = ("extracted_name", "extracted_roll", "student__full_name")
    ordering = ("-match_confidence",)
    readonly_fields = (
        "job",
        "student",
        "extracted_name",
        "extracted_roll",
        "match_confidence",
        "is_exact_match",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
