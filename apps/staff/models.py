from django.db import models
from django.conf import settings
from apps.core.abstract_models import AuditMixin, TimestampMixin


class FacultyProfile(TimestampMixin, AuditMixin, models.Model):
    """Faculty profile linking customized user models with specific designation and session scopes."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="faculty_profile",
        help_text="User account for the faculty member."
    )
    designation = models.CharField(
        max_length=100,
        help_text="Designation (e.g. Senior Lecturer, Assistant Professor)."
    )
    department = models.CharField(
        max_length=100,
        help_text="Department (e.g. Computer Science, English)."
    )
    assigned_sessions = models.ManyToManyField(
        "academics.Session",
        blank=True,
        related_name="faculty_members",
        help_text="Sessions assigned to this faculty member."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this faculty member is active."
    )
    profile_picture = models.ImageField(
        upload_to="faculty/profile_pictures/",
        blank=True,
        null=True,
        help_text="Faculty profile picture. Allowed: JPG, PNG, WEBP. Max 2 MB."
    )

    class Meta:
        verbose_name = "Faculty Profile"
        verbose_name_plural = "Faculty Profiles"

    def __str__(self):
        return f"{self.user.username} ({self.designation} - {self.department})"
