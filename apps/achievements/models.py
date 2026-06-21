from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Achievement(models.Model):
    EXAM_TYPE_CHOICES = [
        ("CSS", "CSS"),
        ("PMS", "PMS"),
        ("PPSC", "PPSC"),
        ("FPSC", "FPSC"),
        ("OTHER", "OTHER"),
    ]

    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="student_achievements",
    )
    exam_type = models.CharField(
        max_length=10,
        choices=EXAM_TYPE_CHOICES,
    )
    year = models.IntegerField()
    rank = models.CharField(max_length=100, blank=True, default="")
    source_job = models.ForeignKey(
        "documents.ComparisonJob",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="achievements",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_achievements",
    )
    is_public = models.BooleanField(default=True)
    testimonial = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "exam_type", "year"],
                name="unique_student_exam_year"
            )
        ]
        ordering = ["-year", "exam_type"]
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"

    def clean(self):
        super().clean()
        qs = Achievement.objects.filter(
            student=self.student,
            exam_type=self.exam_type,
            year=self.year
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError(
                "Achievement for this student, exam type, and year already exists."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.exam_type} ({self.year})"
