"""
Academics models - Session, Subject, TeacherAssignment.

Session represents a course offering with fee structure and late fee config.
Subject enables multi-subject exams and teacher assignment by subject.
TeacherAssignment links teachers to sessions and controls access scope.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.core.abstract_models import AuditMixin, SoftDeleteMixin, TimestampMixin


# ---------------------------------------------------------------
#  Upload path helpers
# ---------------------------------------------------------------

def session_photo_path(instance, filename):
    """Generate safe upload path for session photos."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
    safe_name = slugify(instance.name or "session")
    return f"session_photos/{safe_name}.{ext}"


# ---------------------------------------------------------------
#  Session
# ---------------------------------------------------------------

class Session(TimestampMixin, SoftDeleteMixin, AuditMixin, models.Model):
    """A course or session offered by the academy.

    Session types:
    - time_period: Fixed duration course with start/end dates.
    - monthly: Recurring monthly billing session.

    Late fee configuration is per-session because different
    courses may have different penalty structures.
    """

    SESSION_TYPE_CHOICES = [
        ("time_period", "Time Period Session"),
        ("monthly", "Monthly Session"),
    ]
    SESSION_CATEGORY_CHOICES = [
        ("CSS", "CSS"),
        ("PPSC_FPSC", "PPSC/FPSC"),
        ("PMS", "PMS"),
        ("OLEVEL", "O-Level"),
        ("ALEVEL", "A-Level"),
        ("IELTS", "IELTS"),
        ("CADET_COLLEGE", "Cadet College"),
        ("PTE", "PTE"),
        ("MINISTERIAL", "Ministerial"),
        ("OTHER", "Other"),
    ]
    STATUS_CHOICES = [
        ("Active", "Active"),
        ("Inactive", "Inactive"),
        ("Completed", "Completed"),
    ]

    name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Session or course name.",
    )
    session_category = models.CharField(
        max_length=20,
        choices=SESSION_CATEGORY_CHOICES,
        default="OTHER",
        help_text="Classification category for this session.",
    )
    academic_year = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text="Academic year (e.g. 2026, 2026-2027).",
    )
    batch_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        help_text="Batch identifier or number.",
    )
    max_capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum seat capacity (ERP Operations).",
    )
    is_admission_open = models.BooleanField(
        default=True,
        help_text="Designates whether new student registrations are open.",
    )
    code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        db_index=True,
        help_text="Short code for roll number generation. Uniqueness enforced in clean().",
    )
    roll_prefix = models.CharField(
        max_length=10,
        default="",
        blank=True,
        help_text="Prefix used for session-based automatic roll number generation."
    )
    session_type = models.CharField(
        max_length=15,
        choices=SESSION_TYPE_CHOICES,
        default="time_period",
        help_text="Whether this is a fixed-duration or monthly-billing session.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Session description and details.",
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Session start date.",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Session end date.",
    )
    photo = models.ImageField(
        upload_to=session_photo_path,
        null=True,
        blank=True,
        help_text="Session display photo.",
    )
    fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Base fee for this session.",
    )
    registration_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="One-time registration fee.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="Active",
        db_index=True,
        help_text="Current session status.",
    )
    max_students = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Enrollment capacity. Null means unlimited.",
    )

    # Late fee policy
    late_fee_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Late fee charged per overdue period. 0 means no late fee.",
    )
    late_fee_grace_days = models.PositiveIntegerField(
        default=10,
        help_text="Days after due_day before late fee is applied.",
    )
    late_fee_maximum = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Maximum cumulative late fee. 0 means no cap.",
    )
    due_day = models.PositiveSmallIntegerField(
        default=10,
        help_text="Day of month payments are due (1-28).",
    )

    class Meta:
        ordering = ["-start_date", "name"]
        indexes = [
            models.Index(
                fields=["status", "start_date"],
                name="idx_session_status_start",
            ),
        ]
        verbose_name = "Session"
        verbose_name_plural = "Sessions"

    def clean(self):
        super().clean()
        if self.code:
            qs = Session.all_objects.filter(code=self.code)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "code": f"Session code '{self.code}' is already in use."
                })
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({
                "end_date": "End date must be on or after start date."
            })
        if not (1 <= self.due_day <= 28):
            raise ValidationError({
                "due_day": "Due day must be between 1 and 28."
            })

    def __str__(self):
        return f"{self.name} ({self.get_session_type_display()})"


# ---------------------------------------------------------------
#  Subject
# ---------------------------------------------------------------

class Subject(TimestampMixin, models.Model):
    """Subject catalog for multi-subject sessions.

    When session is null, the subject is global and available
    to all sessions. When session is set, the subject is
    specific to that session.
    """

    name = models.CharField(
        max_length=100,
        help_text="Subject name.",
    )
    code = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Subject code (e.g., MATH101).",
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="subjects",
        help_text="Null means global subject available to all sessions.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Subject description.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this subject is currently offered.",
    )

    class Meta:
        unique_together = [("name", "session")]
        ordering = ["name"]
        verbose_name = "Subject"
        verbose_name_plural = "Subjects"

    def __str__(self):
        if self.session:
            return f"{self.name} ({self.session.name})"
        return f"{self.name} (Global)"


# ---------------------------------------------------------------
#  TeacherAssignment
# ---------------------------------------------------------------

class TeacherAssignment(TimestampMixin, AuditMixin, models.Model):
    """Links a teacher to a session and optionally a subject.

    This is the missing link in the old IICE-CRM. It enables
    proper access scoping: a teacher sees only students in
    their assigned sessions.
    """

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="teaching_assignments",
        help_text="The assigned teacher.",
    )
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="teacher_assignments",
        help_text="The session being taught.",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="teacher_assignments",
        help_text="Specific subject if applicable.",
    )
    assigned_from = models.DateField(
        null=True,
        blank=True,
        help_text="Start of teaching assignment.",
    )
    assigned_until = models.DateField(
        null=True,
        blank=True,
        help_text="End of teaching assignment. Null means ongoing.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this assignment is currently active.",
    )

    class Meta:
        unique_together = [("teacher", "session", "subject")]
        indexes = [
            models.Index(
                fields=["session", "is_active"],
                name="idx_ta_session_active",
            ),
        ]
        verbose_name = "Teacher Assignment"
        verbose_name_plural = "Teacher Assignments"

    def __str__(self):
        subject_str = f" - {self.subject.name}" if self.subject else ""
        return f"{self.teacher.full_name} -> {self.session.name}{subject_str}"


# ---------------------------------------------------------------
#  ClassSchedule
# ---------------------------------------------------------------

class ClassSchedule(TimestampMixin, AuditMixin, models.Model):
    """Timetable class schedule configuration."""

    DAY_OF_WEEK_CHOICES = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
        ("Sunday", "Sunday"),
    ]

    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="schedules",
        help_text="The session for this schedule.",
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="schedules",
        help_text="The subject being taught.",
    )
    faculty = models.ForeignKey(
        "staff.FacultyProfile",
        on_delete=models.CASCADE,
        related_name="schedules",
        help_text="The assigned faculty member.",
    )
    day_of_week = models.CharField(
        max_length=15,
        choices=DAY_OF_WEEK_CHOICES,
        help_text="Day of the week for this class.",
    )
    start_time = models.TimeField(help_text="Start time of the class.")
    end_time = models.TimeField(help_text="End time of the class.")
    classroom = models.CharField(
        max_length=50,
        help_text="Classroom name or identifier.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this schedule is active.",
    )

    class Meta:
        verbose_name = "Class Schedule"
        verbose_name_plural = "Class Schedules"
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.session.name} - {self.subject.name} | {self.day_of_week} ({self.start_time} - {self.end_time})"

    def clean(self):
        super().clean()
        if not self.is_active:
            return

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("Start time must be before end time.")

            # Overlapping schedule for same faculty on same day_of_week
            overlap_faculty = ClassSchedule.objects.filter(
                faculty=self.faculty,
                day_of_week=self.day_of_week,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            if self.pk:
                overlap_faculty = overlap_faculty.exclude(pk=self.pk)
            if overlap_faculty.exists():
                raise ValidationError(
                    f"Faculty member {self.faculty.user.full_name or self.faculty.user.username} is already scheduled on {self.get_day_of_week_display()} between {self.start_time} and {self.end_time}."
                )

            # Overlapping schedule for same classroom on same day_of_week
            overlap_classroom = ClassSchedule.objects.filter(
                classroom=self.classroom,
                day_of_week=self.day_of_week,
                is_active=True,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time
            )
            if self.pk:
                overlap_classroom = overlap_classroom.exclude(pk=self.pk)
            if overlap_classroom.exists():
                raise ValidationError(
                    f"Classroom '{self.classroom}' is already reserved on {self.get_day_of_week_display()} between {self.start_time} and {self.end_time}."
                )

