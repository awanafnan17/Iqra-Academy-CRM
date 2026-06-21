"""
AI Engine models - ModelVersion and PredictionLog.

Fully isolated from domain models. Uses lightweight polymorphic
references (target_model + target_object_id) instead of FK
coupling. This ensures the AI engine can be developed, tested,
and deployed independently of the business domain.

Five prediction types:
- dropout: Student dropout risk
- revenue: Revenue forecasting
- performance: Academic performance prediction
- payment_anomaly: Unusual payment pattern detection
- attendance_risk: Attendance risk scoring
"""

from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.abstract_models import TimestampMixin


class ModelVersion(TimestampMixin, models.Model):
    """Tracks the lifecycle of trained ML models.

    When a model is retrained, a new version is created and
    the previous version is deactivated. This enables rollback
    and quality comparison between versions.
    """

    MODEL_TYPE_CHOICES = [
        ("dropout", "Dropout Prediction"),
        ("revenue", "Revenue Prediction"),
        ("performance", "Performance Prediction"),
        ("payment_anomaly", "Payment Anomaly Detection"),
        ("attendance_risk", "Attendance Risk Detection"),
    ]

    model_type = models.CharField(
        max_length=30,
        choices=MODEL_TYPE_CHOICES,
        db_index=True,
        help_text="Which prediction model this version is for.",
    )
    version = models.CharField(
        max_length=20,
        help_text="Semantic version string (e.g., 1.0.0).",
    )
    file_path = models.CharField(
        max_length=500,
        help_text="Path to the serialized model file (.joblib).",
    )
    accuracy_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("1.0000")),
        ],
        help_text="Model accuracy (0.0000 to 1.0000).",
    )
    precision_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("1.0000")),
        ],
        help_text="Model precision (0.0000 to 1.0000).",
    )
    recall_score = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.0000")),
            MaxValueValidator(Decimal("1.0000")),
        ],
        help_text="Model recall (0.0000 to 1.0000).",
    )
    training_samples = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Number of training samples used.",
    )
    feature_list = models.TextField(
        null=True,
        blank=True,
        help_text="JSON list of feature names used in training.",
    )
    is_active = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only one active version per model_type.",
    )
    trained_at = models.DateTimeField(
        default=timezone.now,
        help_text="When this model version was trained.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Training notes, hyperparameters, changelog.",
    )

    class Meta:
        ordering = ["-trained_at"]
        indexes = [
            models.Index(
                fields=["model_type", "is_active"],
                name="idx_modelver_type_active",
            ),
        ]
        verbose_name = "Model Version"
        verbose_name_plural = "Model Versions"

    def save(self, *args, **kwargs):
        """Enforce only one active version per model_type."""
        if self.is_active:
            ModelVersion.objects.filter(
                model_type=self.model_type,
                is_active=True,
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)

    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"{self.get_model_type_display()} v{self.version} ({status})"


class PredictionLog(TimestampMixin, models.Model):
    """Audit trail for all AI predictions.

    Stores both input features and output for reproducibility.
    Uses target_model + target_object_id for lightweight
    polymorphic reference without FK coupling to domain models.
    """

    PREDICTION_TYPE_CHOICES = [
        ("dropout", "Dropout Risk"),
        ("revenue", "Revenue Forecast"),
        ("performance", "Performance Prediction"),
        ("payment_anomaly", "Payment Anomaly"),
        ("attendance_risk", "Attendance Risk"),
    ]
    RISK_LEVEL_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    prediction_type = models.CharField(
        max_length=30,
        choices=PREDICTION_TYPE_CHOICES,
        db_index=True,
        help_text="Category of this prediction.",
    )
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="predictions",
        help_text="Which model version produced this prediction.",
    )
    target_model = models.CharField(
        max_length=50,
        help_text="Target model name (e.g., students.Student).",
    )
    target_object_id = models.PositiveIntegerField(
        db_index=True,
        help_text="Primary key of the target object.",
    )
    input_features = models.TextField(
        null=True,
        blank=True,
        help_text="JSON of input features used for this prediction.",
    )
    prediction_value = models.TextField(
        help_text="JSON of prediction output.",
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Prediction confidence (0.00 to 100.00).",
    )
    risk_level = models.CharField(
        max_length=10,
        choices=RISK_LEVEL_CHOICES,
        null=True,
        blank=True,
        db_index=True,
        help_text="Categorized risk level.",
    )
    is_acknowledged = models.BooleanField(
        default=False,
        help_text="Whether staff has reviewed this prediction.",
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_predictions",
        help_text="Staff who reviewed this prediction.",
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this prediction was acknowledged.",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this prediction becomes stale.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["target_model", "target_object_id"],
                name="idx_pred_target",
            ),
            models.Index(
                fields=["prediction_type", "risk_level"],
                name="idx_pred_type_risk",
            ),
            models.Index(
                fields=["is_acknowledged", "prediction_type"],
                name="idx_pred_ack_type",
            ),
        ]
        verbose_name = "Prediction Log"
        verbose_name_plural = "Prediction Logs"

    def __str__(self):
        risk = f" [{self.risk_level}]" if self.risk_level else ""
        return f"{self.get_prediction_type_display()}{risk} -> {self.target_model}:{self.target_object_id}"
