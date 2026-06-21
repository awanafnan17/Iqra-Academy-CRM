"""
Core abstract model mixins.

These are abstract base classes that produce no database tables.
All domain models inherit from one or more of these mixins.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class AllObjectsManager(models.Manager):
    """Manager that returns ALL rows including soft-deleted ones."""

    def get_queryset(self):
        return super().get_queryset()


class TimestampMixin(models.Model):
    """Adds created_at and updated_at to any model.

    Uses timezone.now as default (not auto_now_add) so the value
    can be overridden during data migration.
    """

    created_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When this record was created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="When this record was last modified.",
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """Adds soft-delete capability.

    Default manager (objects) excludes deleted rows.
    Use all_objects to include deleted rows for admin recovery.
    Only used on Student, Session, and Enrollment.
    """

    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft delete flag. True means logically deleted.",
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="When this record was soft-deleted.",
    )
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_deleted",
        help_text="User who soft-deleted this record.",
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        abstract = True

    def soft_delete(self, user=None):
        """Mark this record as deleted without removing it from the DB."""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=["is_deleted", "deleted_at", "deleted_by", "updated_at"])


class AuditMixin(models.Model):
    """Tracks who created and last modified a record.

    Nullable because system-generated records (cron jobs, migrations)
    have no user context.
    """

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_created",
        help_text="User who created this record.",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(app_label)s_%(class)s_updated",
        help_text="User who last modified this record.",
    )

    class Meta:
        abstract = True
