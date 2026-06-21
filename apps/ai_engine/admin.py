"""
AI Engine admin - ModelVersion, PredictionLog.
"""

from django.contrib import admin

from apps.ai_engine.models import ModelVersion, PredictionLog


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    """Model version admin with type and active status filters."""

    list_display = (
        "model_type",
        "version",
        "is_active",
        "accuracy_score",
        "precision_score",
        "recall_score",
        "training_samples",
        "trained_at",
    )
    list_filter = ("model_type", "is_active")
    search_fields = ("version", "notes")
    ordering = ("-trained_at",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(PredictionLog)
class PredictionLogAdmin(admin.ModelAdmin):
    """Fully read-only prediction log viewer.

    No records may be added, changed, or deleted through the admin.
    """

    list_display = (
        "prediction_type",
        "model_version",
        "target_model",
        "target_object_id",
        "confidence_score",
        "risk_level",
        "is_acknowledged",
        "created_at",
    )
    list_filter = ("prediction_type", "risk_level", "is_acknowledged")
    search_fields = ("target_model", "target_object_id")
    ordering = ("-created_at",)
    readonly_fields = (
        "prediction_type",
        "model_version",
        "target_model",
        "target_object_id",
        "input_features",
        "prediction_value",
        "confidence_score",
        "risk_level",
        "is_acknowledged",
        "acknowledged_by",
        "acknowledged_at",
        "expires_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
