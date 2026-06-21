"""
Exams models - Exam, ExamResult, GradeConfig.

Supports weighted exams, multi-subject sessions, and auto-ranking.
Grade and percentage are denormalized on ExamResult for query
performance and report generation.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.abstract_models import AuditMixin, TimestampMixin


class Exam(TimestampMixin, AuditMixin, models.Model):
    """An examination or assessment within a session.

    The weight field enables weighted averaging (e.g., quiz 10%,
    midterm 30%, final 60%). Defaults to 1.00 for simple
    scenarios where weighting is not needed.
    """

    EXAM_TYPE_CHOICES = [
        ("Quiz", "Quiz"),
        ("Test", "Test"),
        ("Midterm", "Midterm"),
        ("Final", "Final Exam"),
        ("Assignment", "Assignment"),
        ("Project", "Project"),
    ]

    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.CASCADE,
        related_name="exams",
        help_text="Which session this exam belongs to.",
    )
    subject = models.ForeignKey(
        "academics.Subject",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exams",
        help_text="Specific subject if applicable.",
    )
    name = models.CharField(
        max_length=100,
        help_text="Exam name (e.g., Midterm 1, Final Exam).",
    )
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPE_CHOICES,
        default="Test",
        help_text="Type of assessment.",
    )
    total_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Maximum possible marks.",
    )
    passing_marks = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Minimum marks to pass. Null means no passing threshold.",
    )
    exam_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When the exam is held.",
    )
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.00"),
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Weightage for weighted averaging (1.00 = 100%).",
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Whether results are visible to students and parents.",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("Draft", "Draft"),
            ("Under Review", "Under Review"),
            ("Published", "Published"),
        ],
        default="Draft",
        help_text="Approval status of the exam results.",
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_exams",
        help_text="The principal or admin who reviewed the exam results.",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Date and time when the exam was reviewed.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Exam instructions or notes.",
    )

    class Meta:
        ordering = ["-exam_date", "name"]
        indexes = [
            models.Index(
                fields=["session", "subject"],
                name="idx_exam_session_subject",
            ),
        ]
        verbose_name = "Exam"
        verbose_name_plural = "Exams"

    def clean(self):
        super().clean()
        if self.passing_marks and self.total_marks:
            if self.passing_marks > self.total_marks:
                raise ValidationError({
                    "passing_marks": "Passing marks cannot exceed total marks."
                })

    def save(self, *args, **kwargs):
        self.is_published = (self.status == "Published")
        super().save(*args, **kwargs)

    def __str__(self):
        subject_str = f" ({self.subject.name})" if self.subject else ""
        return f"{self.name}{subject_str} - {self.session.name}"


class ExamResult(TimestampMixin, models.Model):
    """Student result for a specific exam.

    Percentage and grade are denormalized for query performance
    and report generation. They are computed in the save method
    but stored to avoid recalculation on every list view.
    """

    exam = models.ForeignKey(
        Exam,
        on_delete=models.CASCADE,
        related_name="results",
        help_text="Which exam.",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="exam_results",
        help_text="Which student.",
    )
    marks_obtained = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Marks scored by the student.",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Auto-calculated: (marks_obtained / total_marks) * 100.",
    )
    grade = models.CharField(
        max_length=5,
        null=True,
        blank=True,
        help_text="Auto-assigned from GradeConfig.",
    )
    rank = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Auto-calculated rank within the exam.",
    )
    is_absent = models.BooleanField(
        default=False,
        help_text="Student was absent for the exam.",
    )
    remarks = models.TextField(
        null=True,
        blank=True,
        help_text="Teacher remarks on performance.",
    )
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="entered_exam_results",
        help_text="Staff or teacher who entered the marks.",
    )

    class Meta:
        unique_together = [("exam", "student")]
        ordering = ["-marks_obtained"]
        indexes = [
            models.Index(
                fields=["exam", "marks_obtained"],
                name="idx_result_exam_marks",
            ),
        ]
        verbose_name = "Exam Result"
        verbose_name_plural = "Exam Results"

    def clean(self):
        super().clean()
        if self.exam and self.exam.status == "Published":
            raise ValidationError("Cannot modify results of a published exam.")
        if self.marks_obtained and self.exam:
            if self.marks_obtained > self.exam.total_marks:
                raise ValidationError({
                    "marks_obtained": (
                        f"Marks obtained ({self.marks_obtained}) cannot exceed "
                        f"total marks ({self.exam.total_marks})."
                    )
                })

    def save(self, *args, **kwargs):
        """Auto-calculate percentage on save."""
        if self.exam and self.exam.total_marks and self.exam.total_marks > 0:
            self.percentage = (
                self.marks_obtained / self.exam.total_marks * Decimal("100")
            ).quantize(Decimal("0.01"))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.full_name} - {self.exam.name}: {self.marks_obtained}/{self.exam.total_marks}"


class GradeConfig(TimestampMixin, models.Model):
    """Grade boundary configuration.

    Per-session grading scales accommodate different programs.
    Global grades (session=null) serve as defaults when a
    session has no custom configuration.
    """

    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="grade_configs",
        help_text="Null means global default grading scale.",
    )
    grade_name = models.CharField(
        max_length=5,
        help_text="Grade label (A+, A, B+, B, etc.).",
    )
    min_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Minimum percentage for this grade (inclusive).",
    )
    max_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("100.00")),
        ],
        help_text="Maximum percentage for this grade (inclusive).",
    )
    grade_point = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPA point value if applicable.",
    )
    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Display ordering (lower = higher grade).",
    )

    class Meta:
        unique_together = [("session", "grade_name")]
        ordering = ["sort_order"]
        indexes = [
            models.Index(
                fields=["session", "min_percentage"],
                name="idx_grade_session_minpct",
            ),
        ]
        verbose_name = "Grade Configuration"
        verbose_name_plural = "Grade Configurations"

    def clean(self):
        super().clean()
        if self.min_percentage and self.max_percentage:
            if self.min_percentage > self.max_percentage:
                raise ValidationError({
                    "min_percentage": "Minimum percentage must be less than or equal to maximum."
                })

    def __str__(self):
        session_str = self.session.name if self.session else "Global"
        return f"{self.grade_name} ({self.min_percentage}-{self.max_percentage}%) - {session_str}"
