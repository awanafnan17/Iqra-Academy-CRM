import datetime
from decimal import Decimal
import json

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from apps.core.models import AuditLog
from apps.students.models import Student, Enrollment, Guardian
from apps.academics.models import Session, Subject
from apps.attendance.models import AttendanceRecord
from apps.exams.models import Exam
from apps.notifications.models import Notification, EmailLog
from apps.finance.models import Payment
from apps.automation.services import (
    run_fee_reminders,
    check_low_attendance,
    run_upcoming_exam_alerts,
)

User = get_user_model()


class AutomationAlertsTestCase(TestCase):
    def setUp(self):
        # Create standard user accounts
        self.superadmin = User.objects.create_superuser(
            username="test_superadmin",
            email="superadmin@test.com",
            password="Password@123"
        )

        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@test.com",
            password="Password@123"
        )

        self.guardian_user = User.objects.create_user(
            username="guardian_user",
            email="guardian@test.com",
            password="Password@123"
        )

        # Create Admin group and Admin user
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="Password@123"
        )
        self.admin_user.groups.add(self.admin_group)

        # Create Session
        self.session = Session.objects.create(
            name="Session 2026",
            session_type="time_period",
            fee=Decimal("10000.00"),
            registration_fee=Decimal("1000.00"),
            late_fee_amount=Decimal("100.00"),
            late_fee_grace_days=2,
            start_date=timezone.localdate() - datetime.timedelta(days=10),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            status="Active"
        )

        # Create Subject
        self.subject = Subject.objects.create(
            name="Mathematics",
            code="MATH-101",
            session=self.session
        )

        # Create Student
        self.student = Student.objects.create(
            full_name="Fatima Khan",
            roll_number="AL-01",
            email="student@test.com",
            status="Active",
            portal_user=self.student_user
        )

        # Create Guardian
        self.guardian = Guardian.objects.create(
            student=self.student,
            full_name="Usman Ali",
            relationship="Father",
            email="guardian@test.com",
            portal_user=self.guardian_user,
            is_primary=True
        )

        # Create Enrollment
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            registration_date=timezone.localdate() - datetime.timedelta(days=5),
            due_date=timezone.localdate() - datetime.timedelta(days=1), # overdue since yesterday
            status="Active"
        )

    def test_fee_reminders(self):
        # Fatima owes 11,000 (10,000 fee + 1,000 registration) and has 0 payments.
        # Her due_date is in the past.
        # Run reminders
        reminders_sent = run_fee_reminders()
        self.assertEqual(reminders_sent, 1)

        # Verify notification created
        notif = Notification.objects.filter(recipient=self.student_user, category="finance").first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.title, "Fee Overdue Reminder")

        # Verify email logged
        email_log = EmailLog.objects.filter(recipient_email=self.student.email, subject="Fee Overdue Reminder").first()
        self.assertIsNotNone(email_log)
        self.assertEqual(email_log.status, "sent")

        # Verify AuditLog created
        audit_log = AuditLog.objects.filter(model_name="students.Enrollment", object_id=str(self.enrollment.id)).first()
        self.assertIsNotNone(audit_log)
        self.assertIn("fee_reminder_sent", audit_log.changes)

        # Run it again, verify deduplication works (no new reminders sent today)
        reminders_sent_again = run_fee_reminders()
        self.assertEqual(reminders_sent_again, 0)

    def test_low_attendance_alert(self):
        # Create attendance records: 2 total, 1 present, 1 absent = 50% (< 70%)
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate() - datetime.timedelta(days=2),
            status="Present",
            marked_by=self.superadmin
        )
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate() - datetime.timedelta(days=1),
            status="Absent",
            marked_by=self.superadmin
        )

        # Verify Fatima is not flagged initially
        self.assertFalse(self.student.has_low_attendance)

        # Run check
        flagged_count = check_low_attendance()
        self.assertEqual(flagged_count, 1)

        # Reload student from DB, verify flagged
        self.student.refresh_from_db()
        self.assertTrue(self.student.has_low_attendance)

        # Verify Admin notified
        admin_notif = Notification.objects.filter(recipient=self.admin_user, category="attendance").first()
        self.assertIsNotNone(admin_notif)
        self.assertIn("Low Attendance Alert", admin_notif.title)

        # Run again, verify student remains flagged but flagged_count returned is 0 (idempotent status)
        flagged_count_again = check_low_attendance()
        self.assertEqual(flagged_count_again, 0)

        # Now mark Fatima as present today: 3 total, 2 present, 1 absent = 66.6% (< 70%) -> should stay flagged
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate(),
            status="Present",
            marked_by=self.superadmin
        )
        check_low_attendance()
        self.student.refresh_from_db()
        self.assertTrue(self.student.has_low_attendance)

        # Now mark Fatima as present on another past day: 4 total, 3 present, 1 absent = 75% (>= 70%) -> should unflag
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate() - datetime.timedelta(days=3),
            status="Present",
            marked_by=self.superadmin
        )
        check_low_attendance()
        self.student.refresh_from_db()
        self.assertFalse(self.student.has_low_attendance)

    def test_upcoming_exam_alerts(self):
        # Create exam happening in 2 days
        exam = Exam.objects.create(
            session=self.session,
            subject=self.subject,
            name="Algebra Midterm",
            exam_type="Midterm",
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("40.00"),
            exam_date=timezone.localdate() + datetime.timedelta(days=2),
            is_published=False
        )

        # Run alerts
        alerts_sent = run_upcoming_exam_alerts()
        # 1 to student, 1 to guardian = 2 total
        self.assertEqual(alerts_sent, 2)

        # Verify Student notified
        student_notif = Notification.objects.filter(
            recipient=self.student_user,
            category="exam",
            related_model="exams.Exam",
            related_object_id=exam.id
        ).first()
        self.assertIsNotNone(student_notif)

        # Verify Guardian notified
        guardian_notif = Notification.objects.filter(
            recipient=self.guardian_user,
            category="exam",
            related_model="exams.Exam",
            related_object_id=exam.id
        ).first()
        self.assertIsNotNone(guardian_notif)

        # Run again, verify deduplication works
        alerts_sent_again = run_upcoming_exam_alerts()
        self.assertEqual(alerts_sent_again, 0)
