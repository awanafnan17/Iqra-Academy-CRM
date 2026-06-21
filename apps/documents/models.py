from django.db import models
from django.conf import settings
from django.utils import timezone

class ComparisonJob(models.Model):
    EXAM_TYPE_CHOICES = [
        ("CSS", "CSS"),
        ("PMS", "PMS"),
        ("PPSC", "PPSC"),
        ("FPSC", "FPSC"),
        ("OTHER", "OTHER"),
    ]

    STATUS_CHOICES = [
        ("Uploaded", "Uploaded"),
        ("Processed", "Processed"),
        ("Failed", "Failed"),
    ]

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comparison_jobs",
        null=True,
        blank=True,
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    file = models.FileField(upload_to="comparison_jobs/", null=True, blank=True)
    exam_type = models.CharField(max_length=10, choices=EXAM_TYPE_CHOICES, default="OTHER")
    total_entries = models.PositiveIntegerField(default=0)
    matched_entries = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="Uploaded")

    class Meta:
        ordering = ["-uploaded_at"]
        verbose_name = "Comparison Job"
        verbose_name_plural = "Comparison Jobs"

    def __str__(self):
        return f"{self.exam_type} Job #{self.id} ({self.status})"


class ComparisonResult(models.Model):
    job = models.ForeignKey(
        ComparisonJob,
        on_delete=models.CASCADE,
        related_name="results",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="comparison_results",
    )
    extracted_name = models.CharField(max_length=255)
    extracted_roll = models.CharField(max_length=50, null=True, blank=True)
    match_confidence = models.FloatField(default=0.0)
    is_exact_match = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-match_confidence"]
        verbose_name = "Comparison Result"
        verbose_name_plural = "Comparison Results"

    def __str__(self):
        return f"{self.extracted_name} -> {self.student or 'No Match'} ({self.match_confidence:.2f})"
