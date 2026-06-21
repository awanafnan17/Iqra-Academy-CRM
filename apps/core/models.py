"""
Core models - AuditLog for system-wide action tracking.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditLog(models.Model):
    """Centralized audit log for compliance and debugging.

    Stores changes as JSON text rather than JSONField for MySQL
    compatibility. Not linked via FK to target objects because
    it must survive deletion of those objects.
    """

    ACTION_CHOICES = [
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("export", "Export"),
        ("password_change", "Password Change"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who performed the action.",
    )
    action = models.CharField(
        max_length=20,
        choices=ACTION_CHOICES,
        db_index=True,
        help_text="Type of action performed.",
    )
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="App label and model name (e.g., students.Student).",
    )
    object_id = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Primary key of the affected object, stored as string.",
    )
    changes = models.TextField(
        null=True,
        blank=True,
        help_text="JSON-serialized diff of changed fields.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request.",
    )
    user_agent = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="Browser user agent string.",
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the action occurred.",
    )

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(
                fields=["user", "timestamp"],
                name="idx_audit_user_time",
            ),
            models.Index(
                fields=["model_name", "object_id"],
                name="idx_audit_model_obj",
            ),
            models.Index(
                fields=["action", "timestamp"],
                name="idx_audit_action_time",
            ),
        ]

    def __str__(self):
        return f"{self.action} on {self.model_name}:{self.object_id} by {self.user} at {self.timestamp}"


class RolePermission(models.Model):
    """Granular permissions mapping module actions to Django Groups/Roles."""
    ROLE_CHOICES = [
        ("Admin", "Admin"),
        ("Principal", "Principal"),
        ("Teacher", "Teacher"),
        ("Accountant", "Accountant"),
        ("Registrar", "Registrar"),
        ("Student", "Student"),
        ("Guardian", "Guardian"),
    ]
    MODULE_CHOICES = [
        ("finance", "Finance"),
        ("exams", "Exams"),
        ("attendance", "Attendance"),
        ("students", "Students"),
        ("notifications", "Notifications"),
        ("users", "Users"),
    ]

    role_name = models.CharField(max_length=20, choices=ROLE_CHOICES, db_index=True)
    module_name = models.CharField(max_length=30, choices=MODULE_CHOICES, db_index=True)

    can_view = models.BooleanField(default=False)
    can_create = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)

    class Meta:
        unique_together = [("role_name", "module_name")]
        indexes = [
            models.Index(fields=["role_name", "module_name"], name="idx_role_mod_perm"),
        ]

    def __str__(self):
        return f"{self.role_name} - {self.module_name} (V:{self.can_view}, C:{self.can_create}, E:{self.can_edit}, D:{self.can_delete}, Ex:{self.can_export}, A:{self.can_approve})"

