import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase
from django.utils import timezone

from apps.academics.models import Session
from apps.students.models import Student, Enrollment
from apps.students.services import EnrollmentService
from apps.attendance.models import AttendanceRecord
from apps.exams.models import Exam, ExamResult
from apps.finance.models import Payment
from apps.core.models import AuditLog

User = get_user_model()


class AcademicOperationsTests(TransactionTestCase):
    def setUp(self):
        super().setUp()

        self.staff_user = User.objects.create_user(
            username="staff_ops@test.com", email="staff_ops@test.com", password="password"
        )

        # Create source and target sessions
        self.session_src = Session.objects.create(
            name="CSS Morning Batch",
            status="Active",
            roll_prefix="CSS-M",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="Batch 1",
            max_capacity=50,
        )

        self.session_tgt = Session.objects.create(
            name="CSS Evening Batch",
            status="Active",
            roll_prefix="CSS-E",
            fee=Decimal("1200.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="Batch 2",
            max_capacity=50,
        )

        self.student = Student.objects.create(full_name="Zayn Malik")

        # Enroll student in source session
        self.enrollment = EnrollmentService.create_enrollment(
            student_id=self.student.id,
            session_id=self.session_src.id,
            user=self.staff_user,
        )

    def test_calculate_academic_score_with_no_data(self):
        """A student with no logged attendance, exams, or payments should default to 100.00 score."""
        score = EnrollmentService.calculate_academic_score(self.student.id, self.session_src.id)
        self.assertEqual(score, Decimal("100.00"))

    def test_calculate_academic_score_with_partial_data(self):
        """Verifies the weighted average performance score calculation.

        Attendance: 30% weight
        Exams: 50% weight
        Fee compliance: 20% weight
        """
        # 1. Log Attendance: 1 Present, 1 Absent -> 50% (30% weight -> 15.0)
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session_src,
            date=timezone.localdate() - datetime.timedelta(days=1),
            status="Present",
            marked_by=self.staff_user
        )
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session_src,
            date=timezone.localdate(),
            status="Absent",
            marked_by=self.staff_user
        )

        # 2. Log Exam Result: 80% (50% weight -> 40.0)
        exam = Exam.objects.create(
            session=self.session_src,
            name="Midterm 1",
            total_marks=Decimal("100.00"),
            exam_date=timezone.localdate(),
        )
        ExamResult.objects.create(
            exam=exam,
            student=self.student,
            marks_obtained=Decimal("80.00"),
        )

        # 3. Log Payment: total payable = 1000 fee + 200 reg_fee = 1200.
        # Pay 600 -> 50% compliance (20% weight -> 10.0)
        # Expected total score = 15.0 + 40.0 + 10.0 = 65.00
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("600.00"),
            payment_date=timezone.localdate(),
            payment_status="confirmed"
        )

        score = EnrollmentService.calculate_academic_score(self.student.id, self.session_src.id)
        self.assertEqual(score, Decimal("65.00"))

    def test_transfer_student_to_session_success(self):
        """Verifies that transferring student to a new session operates atomically and regenerates roll prefix."""
        new_enrollment = EnrollmentService.transfer_student_to_session(
            student_id=self.student.id,
            new_session_id=self.session_tgt.id,
            user=self.staff_user
        )

        self.student.refresh_from_db()
        self.enrollment.refresh_from_db()

        # Check source enrollment is soft deleted and status set to Transferred
        self.assertEqual(self.enrollment.status, "Transferred")
        self.assertTrue(self.enrollment.is_deleted)

        # Check new enrollment is active and maps to new session
        self.assertEqual(new_enrollment.status, "Active")
        self.assertEqual(new_enrollment.session_id, self.session_tgt.id)

        # Check roll number is regenerated with new session prefix
        self.assertEqual(self.student.roll_number, "CSS-E-01")

        # Verify AuditLog entries exist
        logs = AuditLog.objects.filter(model_name="students.Enrollment", object_id=str(new_enrollment.id))
        self.assertTrue(logs.exists())
