"""
Notifications models - Notification, NotificationTemplate, EmailLog.

Unified dispatch interface supporting email, in-app, and WhatsApp
(stub) channels. Uses lightweight polymorphic references instead
of Django GenericForeignKey to avoid ContentType query overhead.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.core.abstract_models import TimestampMixin


class Notification(TimestampMixin, models.Model):
    """System notification surfaced to users.

    Uses related_model + related_object_id as a lightweight
    polymorphic link without GenericForeignKey. This avoids the
    ContentType join overhead while still enabling navigation
    to the related object in the UI.
    """

    CATEGORY_CHOICES = [
        ("General", "General"),
        ("LateFee", "Late Fee"),
        ("NewEntry", "New Entry"),
        ("Deletion", "Deletion"),
        ("Payment", "Payment"),
        ("Attendance", "Attendance"),
        ("ExamResult", "Exam Result"),
        ("MonthlyRenewal", "Monthly Renewal"),
        ("System", "System"),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User who receives this notification.",
    )
    category = models.CharField(
        max_length=25,
        choices=CATEGORY_CHOICES,
        default="General",
        db_index=True,
        help_text="Notification category for filtering.",
    )
    title = models.CharField(
        max_length=200,
        help_text="Short notification title.",
    )
    content = models.TextField(
        null=True,
        blank=True,
        help_text="Notification body text.",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether the user has read this notification.",
    )
    related_model = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Model name of related object (e.g., students.Student).",
    )
    related_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Primary key of the related object.",
    )
    enrollment = models.ForeignKey(
        "students.Enrollment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Direct FK for enrollment-scoped deduplication.",
    )
    dedup_key = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="YYYY-MM or custom key for deduplication.",
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["recipient", "is_read"],
                name="idx_notif_recipient_read",
            ),
            models.Index(
                fields=["recipient", "-created_at"],
                name="idx_notif_recipient_date",
            ),
            models.Index(
                fields=["enrollment", "category", "dedup_key"],
                name="idx_notif_enroll_dedup",
            ),
        ]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"

    def __str__(self):
        return f"[{self.category}] {self.title} -> {self.recipient}"


class NotificationTemplate(TimestampMixin, models.Model):
    """Reusable notification message template.

    Templates enable non-developer staff to modify notification
    messages without code changes. Variable substitution uses
    Python str.format() syntax with {variable_name} placeholders.
    """

    CHANNEL_CHOICES = [
        ("email", "Email"),
        ("in_app", "In-App"),
        ("whatsapp", "WhatsApp"),
        ("sms", "SMS"),
    ]

    name = models.CharField(
        max_length=100,
        help_text="Human-readable template name.",
    )
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Machine identifier (e.g., fee_reminder, attendance_alert).",
    )
    channel = models.CharField(
        max_length=15,
        choices=CHANNEL_CHOICES,
        default="email",
        help_text="Delivery channel for this template.",
    )
    subject_template = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Subject line with {variable} placeholders.",
    )
    body_template = models.TextField(
        help_text="Body with {variable} placeholders.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this template is enabled.",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Internal notes about when this template is used.",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["channel", "is_active"],
                name="idx_tmpl_channel_active",
            ),
        ]
        verbose_name = "Notification Template"
        verbose_name_plural = "Notification Templates"

    def __str__(self):
        return f"{self.name} [{self.channel}]"


class EmailLog(models.Model):
    """Audit trail for sent emails.

    Separate from Notification because not every notification
    generates an email and not every email is a notification.
    """

    STATUS_CHOICES = [
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("bounced", "Bounced"),
    ]

    recipient_email = models.EmailField(
        db_index=True,
        help_text="Where the email was sent.",
    )
    subject = models.CharField(
        max_length=200,
        help_text="Email subject line.",
    )
    body_preview = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        help_text="First 500 characters of body for quick reference.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="sent",
        db_index=True,
        help_text="Email delivery status.",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error details if delivery failed.",
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the email was dispatched.",
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="email_logs",
        help_text="Linked notification if applicable.",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sent_emails",
        help_text="User who triggered the email.",
    )

    class Meta:
        ordering = ["-sent_at"]
        indexes = [
            models.Index(
                fields=["recipient_email", "sent_at"],
                name="idx_email_recip_date",
            ),
        ]
        verbose_name = "Email Log"
        verbose_name_plural = "Email Logs"

    def __str__(self):
        return f"Email to {self.recipient_email}: {self.subject} ({self.status})"
