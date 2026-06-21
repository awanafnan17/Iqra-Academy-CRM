import datetime
import logging
import json
from decimal import Decimal

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.core.models import AuditLog
from apps.students.models import Student, Enrollment
from apps.attendance.services import AttendanceService
from apps.exams.models import Exam
from apps.notifications.models import Notification, EmailLog
from apps.notifications.services import create_notification, send_email_notification
from apps.finance.services import calculate_student_ledger

logger = logging.getLogger("crm.automation")


def run_fee_reminders():
    """Daily fee reminder job.

    Finds active enrollments with outstanding_balance > 0 and due date <= today.
    Sends notification, sends email, and logs in AuditLog.
    """
    today = timezone.localdate()
    active_enrollments = Enrollment.objects.filter(status="Active").select_related("student", "session")
    sent_count = 0

    for enrollment in active_enrollments:
        student = enrollment.student
        session = enrollment.session

        # Determine target due date
        if session.session_type == "time_period":
            due_date = enrollment.due_date
        else:
            due_date = enrollment.next_monthly_due

        if due_date is None or due_date > today:
            continue

        # Calculate balance
        ledger = calculate_student_ledger(enrollment.id)
        outstanding_balance = ledger["outstanding_balance"]

        if outstanding_balance <= 0:
            continue

        title = "Fee Overdue Reminder"
        message = (
            f"Dear {student.full_name}, this is a reminder that you have an outstanding balance "
            f"of PKR {outstanding_balance} for the session '{session.name}' which was due on {due_date}. "
            f"Please clear your dues as soon as possible."
        )

        with transaction.atomic():
            # Check if already sent today to avoid double notifications on same-day reruns
            already_notified = False

            if student.portal_user:
                already_notified = Notification.objects.filter(
                    recipient=student.portal_user,
                    category="finance",
                    title=title,
                    created_at__date=today
                ).exists()

                if not already_notified:
                    notif = create_notification(
                        recipient=student.portal_user,
                        title=title,
                        message=message,
                        category="finance",
                        created_by=None
                    )
                    if notif:
                        send_email_notification(notif.id)
                        sent_count += 1
            else:
                # Fallback directly to email if portal user is not registered
                if student.email:
                    already_notified = EmailLog.objects.filter(
                        recipient_email=student.email,
                        subject=title,
                        sent_at__date=today
                    ).exists()

                    if not already_notified:
                        try:
                            send_mail(
                                subject=title,
                                message=message,
                                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                                recipient_list=[student.email],
                                fail_silently=False,
                            )
                            EmailLog.objects.create(
                                recipient_email=student.email,
                                subject=title,
                                body_preview=message[:500],
                                status="sent"
                            )
                            sent_count += 1
                        except Exception as e:
                            logger.error(f"Failed to send direct email fee reminder to {student.email}: {e}")
                            EmailLog.objects.create(
                                recipient_email=student.email,
                                subject=title,
                                body_preview=message[:500],
                                status="failed",
                                error_message=str(e)
                            )

            # Log to AuditLog (even if user is notified, we log the job execution for this enrollment)
            AuditLog.objects.create(
                user=None,
                action="create",
                model_name="students.Enrollment",
                object_id=str(enrollment.id),
                changes=json.dumps({
                    "action": "fee_reminder_sent",
                    "due_date": str(due_date),
                    "outstanding_balance": str(outstanding_balance)
                })
            )

    logger.info(f"Fee reminder run complete. Dispatched {sent_count} reminders.")
    return sent_count


def check_low_attendance():
    """Daily check to flag students with attendance < 70%.

    If attendance rate < 70%, flags student, notifies admin, and updates dashboard visibility.
    """
    today = timezone.localdate()
    active_enrollments = Enrollment.objects.filter(status="Active").select_related("student", "session")
    admin_group = Group.objects.filter(name="Admin").first()
    admins = admin_group.user_set.all() if admin_group else []
    flagged_count = 0

    for enrollment in active_enrollments:
        student = enrollment.student
        session = enrollment.session

        pct = AttendanceService.calculate_attendance_percentage(student.id, session.id)

        if pct < Decimal("70.00"):
            # Flag student if not already flagged
            if not student.has_low_attendance:
                student.has_low_attendance = True
                student.save(update_fields=["has_low_attendance"])
                flagged_count += 1

                # Log flag update in AuditLog
                AuditLog.objects.create(
                    user=None,
                    action="update",
                    model_name="students.Student",
                    object_id=str(student.id),
                    changes=json.dumps({
                        "has_low_attendance": {"old": False, "new": True},
                        "attendance_percentage": str(pct),
                        "session_id": session.id
                    })
                )

                # Notify all administrators
                title = f"Low Attendance Alert: {student.full_name}"
                message = (
                    f"Warning: Student {student.full_name} ({student.roll_number}) "
                    f"has an attendance rate of {pct}% in active session '{session.name}', "
                    f"which falls below the 70% minimum threshold."
                )

                for admin in admins:
                    # Prevent daily duplicate notifications to same admin for same student
                    already_warned = Notification.objects.filter(
                        recipient=admin,
                        category="attendance",
                        title=title,
                        created_at__date=today
                    ).exists()

                    if not already_warned:
                        notif = create_notification(
                            recipient=admin,
                            title=title,
                            message=message,
                            category="attendance",
                            created_by=None
                        )
                        if notif:
                            send_email_notification(notif.id)
        else:
            # Unflag student if they rose above the threshold
            if student.has_low_attendance:
                student.has_low_attendance = False
                student.save(update_fields=["has_low_attendance"])

                AuditLog.objects.create(
                    user=None,
                    action="update",
                    model_name="students.Student",
                    object_id=str(student.id),
                    changes=json.dumps({
                        "has_low_attendance": {"old": True, "new": False},
                        "attendance_percentage": str(pct),
                        "session_id": session.id
                    })
                )

    logger.info(f"Low attendance checks complete. Newly flagged {flagged_count} students.")
    return flagged_count


def run_upcoming_exam_alerts():
    """Alert students and guardians of upcoming exams within 3 days.

    If exam date <= today + 3 days, notify enrolled students and guardians.
    """
    today = timezone.localdate()
    three_days_later = today + datetime.timedelta(days=3)

    # Assess exams happening within the 3-day window
    exams = Exam.objects.filter(exam_date__range=(today, three_days_later)).select_related("session", "subject")
    notified_count = 0

    for exam in exams:
        enrollments = Enrollment.objects.filter(session=exam.session, status="Active").select_related("student")

        for enrollment in enrollments:
            student = enrollment.student
            subject_name = exam.subject.name if exam.subject else "All Subjects"
            title = f"Upcoming Exam Notification: {exam.name}"
            message = (
                f"Notice: The exam '{exam.name}' for subject '{subject_name}' "
                f"is scheduled to take place on {exam.exam_date}."
            )

            # 1. Notify Student
            if student.portal_user:
                # Ensure we only send notification once per exam to student
                already_notified = Notification.objects.filter(
                    recipient=student.portal_user,
                    category="exam",
                    related_model="exams.Exam",
                    related_object_id=exam.id
                ).exists()

                if not already_notified:
                    notif = create_notification(
                        recipient=student.portal_user,
                        title=title,
                        message=message,
                        category="exam",
                        created_by=None
                    )
                    if notif:
                        notif.related_model = "exams.Exam"
                        notif.related_object_id = exam.id
                        notif.save(update_fields=["related_model", "related_object_id"])
                        send_email_notification(notif.id)
                        notified_count += 1
            else:
                if student.email:
                    already_notified = EmailLog.objects.filter(
                        recipient_email=student.email,
                        subject=title
                    ).exists()

                    if not already_notified:
                        try:
                            send_mail(
                                subject=title,
                                message=message,
                                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                                recipient_list=[student.email],
                                fail_silently=False,
                            )
                            EmailLog.objects.create(
                                recipient_email=student.email,
                                subject=title,
                                body_preview=message[:500],
                                status="sent"
                            )
                            notified_count += 1
                        except Exception as e:
                            logger.error(f"Failed to send exam direct email to student {student.email}: {e}")

            # 2. Notify Guardian(s)
            guardians = student.guardians.all()
            for guardian in guardians:
                guardian_title = f"Upcoming Exam Notification for {student.full_name}"
                guardian_message = (
                    f"Notice for Guardian: The exam '{exam.name}' for student {student.full_name} "
                    f"is scheduled to take place on {exam.exam_date}."
                )

                if guardian.portal_user:
                    already_notified_guard = Notification.objects.filter(
                        recipient=guardian.portal_user,
                        category="exam",
                        related_model="exams.Exam",
                        related_object_id=exam.id
                    ).exists()

                    if not already_notified_guard:
                        notif_guard = create_notification(
                            recipient=guardian.portal_user,
                            title=guardian_title,
                            message=guardian_message,
                            category="exam",
                            created_by=None
                        )
                        if notif_guard:
                            notif_guard.related_model = "exams.Exam"
                            notif_guard.related_object_id = exam.id
                            notif_guard.save(update_fields=["related_model", "related_object_id"])
                            send_email_notification(notif_guard.id)
                            notified_count += 1
                else:
                    if guardian.email:
                        already_notified_guard = EmailLog.objects.filter(
                            recipient_email=guardian.email,
                            subject=guardian_title
                        ).exists()

                        if not already_notified_guard:
                            try:
                                send_mail(
                                    subject=guardian_title,
                                    message=guardian_message,
                                    from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                                    recipient_list=[guardian.email],
                                    fail_silently=False,
                                )
                                EmailLog.objects.create(
                                    recipient_email=guardian.email,
                                    subject=guardian_title,
                                    body_preview=guardian_message[:500],
                                    status="sent"
                                )
                                notified_count += 1
                            except Exception as e:
                                logger.error(f"Failed to send exam direct email to guardian {guardian.email}: {e}")

    logger.info(f"Exam alerts completed. Sent {notified_count} upcoming notifications.")
    return notified_count
