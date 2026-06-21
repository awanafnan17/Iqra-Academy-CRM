"""
Attendance models - AttendanceRecord and AttendanceLock.

AttendanceRecord references Student and Session directly (not
through Enrollment) to preserve historical attendance data even
after enrollment withdrawal.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.abstract_models import TimestampMixin


class AttendanceRecord(TimestampMixin, models.Model):
    """Daily attendance record for a student in a session.

    References Student and Session directly rather than through
    Enrollment so that attendance history is preserved even if
    the enrollment is withdrawn or transferred.
    """

    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
        ("Late", "Late"),
        ("Excused", "Excused"),
    ]

    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        help_text="Which session this attendance is for.",
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="attendance_records",
        help_text="Which student.",
    )
    date = models.DateField(
        db_index=True,
        help_text="Date of attendance.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        help_text="Attendance status for this date.",
    )
    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marked_attendances",
        help_text="Staff or teacher who marked attendance.",
    )
    remarks = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Optional note (e.g., reason for absence).",
    )

    class Meta:
        unique_together = [("session", "student", "date")]
        ordering = ["-date"]
        indexes = [
            models.Index(
                fields=["session", "date"],
                name="idx_attend_session_date",
            ),
            models.Index(
                fields=["student", "session"],
                name="idx_attend_student_session",
            ),
        ]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"

    def __str__(self):
        return f"{self.student.full_name} - {self.session.name} - {self.date} ({self.status})"


class AttendanceLock(models.Model):
    """Prevents retroactive attendance changes after a deadline.

    The service layer checks for a lock before allowing
    attendance modifications.
    """

    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.CASCADE,
        related_name="attendance_locks",
        help_text="Which session is locked.",
    )
    date = models.DateField(
        help_text="Which date is locked.",
    )
    locked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attendance_locks_created",
        help_text="Who locked this date. Null if user was deleted.",
    )
    locked_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the lock was applied.",
    )
    reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason for locking.",
    )

    class Meta:
        unique_together = [("session", "date")]
        verbose_name = "Attendance Lock"
        verbose_name_plural = "Attendance Locks"

    def __str__(self):
        return f"Lock: {self.session.name} - {self.date}"
