import hashlib
import datetime
import logging
from django.db import transaction
from django.db.models import Count, Value
from django.db.models.functions import Coalesce
from django.core.exceptions import ValidationError
from django.http import Http404
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.notifications.models import Notification, EmailLog

logger = logging.getLogger("crm.notifications")

# Centralized category validation constants
VALID_NOTIFICATION_CATEGORIES = {"system", "academic", "finance", "exam", "attendance", "general"}


def _get_dedup_key(title, content, category, recipient_id):
    raw_str = f"{title}{content or ''}{category}{recipient_id}"
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:50]


def create_notification(recipient, title, message, category, created_by):
    """Create a new notification after validating the category choice and checking for duplicates."""
    if category not in VALID_NOTIFICATION_CATEGORIES:
        raise ValidationError(f"Invalid category: {category}")

    User = get_user_model()
    if not isinstance(recipient, User):
        recipient = User.objects.get(pk=recipient)

    has_dedup = hasattr(Notification, "dedup_key")
    key = _get_dedup_key(title, message, category, recipient.id)
    ten_seconds_ago = timezone.now() - datetime.timedelta(seconds=10)

    with transaction.atomic():
        if has_dedup:
            if Notification.objects.filter(dedup_key=key, created_at__gte=ten_seconds_ago).exists():
                return None
        else:
            if Notification.objects.filter(
                recipient=recipient,
                title=title,
                content=message,
                category=category,
                created_at__gte=ten_seconds_ago
            ).exists():
                return None

        notif = Notification(
            recipient=recipient,
            title=title,
            content=message,
            category=category,
        )
        if has_dedup:
            notif.dedup_key = key

        notif.full_clean(exclude=["category"])
        notif.save()
        return notif


def bulk_notify_users(user_ids, title, message, category, created_by):
    """Atomically create notifications for a bulk list of users using bulk_create.

    Validates all users exist, checks for duplicates, and enforces the 1000 recipient limit.
    """
    logger.info(f"Bulk notification attempt for {len(user_ids)} users. Category: {category}.")

    with transaction.atomic():
        unique_user_ids = list(set(user_ids))

        if len(unique_user_ids) > 1000:
            raise ValidationError("Cannot send notifications to more than 1000 users at once.")

        if category not in VALID_NOTIFICATION_CATEGORIES:
            raise ValidationError(f"Invalid category: {category}")

        User = get_user_model()
        recipients = list(User.objects.filter(pk__in=unique_user_ids).order_by("pk"))
        if len(recipients) != len(unique_user_ids):
            raise ValidationError("One or more recipient users do not exist.")

        has_dedup = hasattr(Notification, "dedup_key")
        ten_seconds_ago = timezone.now() - datetime.timedelta(seconds=10)

        recipient_keys = {}
        for r in recipients:
            key = _get_dedup_key(title, message, category, r.id)
            recipient_keys[r.id] = key

        existing_recipient_ids = set()
        if has_dedup:
            existing_keys = set(
                Notification.objects.filter(
                    dedup_key__in=recipient_keys.values(),
                    created_at__gte=ten_seconds_ago
                ).values_list("dedup_key", flat=True)
            )
            for rid, key in recipient_keys.items():
                if key in existing_keys:
                    existing_recipient_ids.add(rid)
        else:
            existing_recipient_ids = set(
                Notification.objects.filter(
                    recipient__in=recipients,
                    title=title,
                    content=message,
                    category=category,
                    created_at__gte=ten_seconds_ago
                ).values_list("recipient_id", flat=True)
            )

        notifications = []
        for recipient in recipients:
            if recipient.id in existing_recipient_ids:
                continue
            notif = Notification(
                recipient=recipient,
                title=title,
                content=message,
                category=category,
            )
            if has_dedup:
                notif.dedup_key = recipient_keys[recipient.id]
            notif.full_clean(exclude=["category"])
            notifications.append(notif)

        if notifications:
            Notification.objects.bulk_create(notifications)
        return notifications


def mark_notification_read(notification_id, user):
    """Mark a notification as read.

    Verifies that the notification belongs to the user, raising Http404 on violation.
    Uses select_for_update and update_fields to update only the is_read field.
    """
    with transaction.atomic():
        try:
            notif = Notification.objects.select_for_update().get(pk=notification_id)
        except Notification.DoesNotExist:
            raise Http404("Notification not found.")

        if notif.recipient != user:
            raise Http404("Access denied.")

        notif.is_read = True
        notif.save(update_fields=["is_read"])
        return notif


def mark_all_notifications_read(user):
    """Mark all notifications of the user as read."""
    with transaction.atomic():
        Notification.objects.filter(recipient=user, is_read=False).update(is_read=True)


def send_email_notification(notification_id):
    """Send an email notification and log it in EmailLog.

    Email delivery failure records the log but does not raise exceptions.
    """
    try:
        notif = Notification.objects.select_related("recipient").get(pk=notification_id)
    except Notification.DoesNotExist:
        raise Http404("Notification not found.")

    recipient_email = notif.recipient.email or ""
    subject = notif.title
    body = notif.content or ""
    status = "sent"
    error_message = ""

    if not recipient_email:
        status = "failed"
        error_message = "Recipient has no email address."
        logger.warning(f"Email send failed: Recipient user {notif.recipient.id} has no email address.")
    else:
        try:
            # Map notification category to template file
            category_lower = notif.category.lower() if notif.category else "general"
            if category_lower in ("finance", "latefee"):
                template_name = "emails/fee_reminder.html"
            elif category_lower == "attendance":
                template_name = "emails/low_attendance.html"
            elif category_lower == "exam":
                template_name = "emails/upcoming_exam.html"
            else:
                template_name = "emails/general_email.html"

            context = {
                "title": notif.title,
                "content": notif.content,
                "recipient_name": notif.recipient.get_full_name() or notif.recipient.username,
                "portal_url": getattr(settings, "SITE_URL", "http://127.0.0.1:8001/"),
            }
            html_content = render_to_string(template_name, context)

            msg = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "Iqra Academy CRM <notifications@yourdomain.com>"),
                to=[recipient_email]
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send(fail_silently=False)
        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Email send failed for notification {notification_id}: {error_message}")

    with transaction.atomic():
        log = EmailLog(
            recipient_email=recipient_email,
            subject=subject,
            body_preview=body[:500],
            status=status,
            error_message=error_message,
            notification=notif,
        )
        exclude_fields = []
        if not recipient_email:
            exclude_fields.append("recipient_email")
        log.full_clean(exclude=exclude_fields)
        log.save()
        return log


def get_unread_count(user):
    """Return the number of unread notifications for a user."""
    result = Notification.objects.filter(recipient=user, is_read=False).aggregate(
        count=Coalesce(Count("id"), Value(0))
    )
    return result["count"]


def get_user_notifications(user, limit=None):
    """Return all notifications of the user, without soft-delete filtering."""
    qs = Notification.objects.filter(recipient=user).order_by("-created_at")

    # Avoid unnecessary select_related if enrollment is null for all of them
    has_enrollments = Notification.objects.filter(recipient=user, enrollment__isnull=False).exists()
    if has_enrollments:
        qs = qs.select_related("recipient", "enrollment")
    else:
        qs = qs.select_related("recipient")

    if limit is not None:
        qs = qs[:limit]
    return qs
