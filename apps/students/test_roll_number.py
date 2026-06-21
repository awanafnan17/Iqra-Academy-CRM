import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from apps.academics.models import Session
from apps.students.models import Student, Enrollment
from apps.students.services import EnrollmentService

User = get_user_model()


class RollNumberGenerationTests(TestCase):
    def setUp(self):
        super().setUp()

        # Create a mock staff user for enrollment logging
        self.staff_user = User.objects.create_user(
            username="staff_roll@test.com", email="staff_roll@test.com", password="password"
        )

        # Create test session
        self.session = Session.objects.create(
            name="Computer Programming 101",
            status="Active",
            roll_prefix="CP",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
        )

        # Create students
        self.student_1 = Student.objects.create(full_name="Fatima Khan")
        self.student_2 = Student.objects.create(full_name="Usman Ali")
        self.student_3 = Student.objects.create(full_name="Charlie Red")

    def test_sequential_roll_number_generation(self):
        """Enrolling students sequentially should assign roll numbers CP-01, CP-02, CP-03."""
        # Enroll 1st student
        enrollment_1 = EnrollmentService.create_enrollment(
            student_id=self.student_1.id,
            session_id=self.session.id,
            user=self.staff_user,
        )
        self.student_1.refresh_from_db()
        self.assertEqual(self.student_1.roll_number, "CP-01")

        # Enroll 2nd student
        enrollment_2 = EnrollmentService.create_enrollment(
            student_id=self.student_2.id,
            session_id=self.session.id,
            user=self.staff_user,
        )
        self.student_2.refresh_from_db()
        self.assertEqual(self.student_2.roll_number, "CP-02")

        # Enroll 3rd student
        enrollment_3 = EnrollmentService.create_enrollment(
            student_id=self.student_3.id,
            session_id=self.session.id,
            user=self.staff_user,
        )
        self.student_3.refresh_from_db()
        self.assertEqual(self.student_3.roll_number, "CP-03")

    def test_backfill_management_command(self):
        """Management command assign_roll_numbers should backfill missing roll numbers sequentially."""
        # Create enrollment directly without services to bypass roll number generation
        enrollment_1 = Enrollment.objects.create(
            student=self.student_1,
            session=self.session,
            status="Active",
            registration_date=timezone.localdate(),
        )
        enrollment_2 = Enrollment.objects.create(
            student=self.student_2,
            session=self.session,
            status="Active",
            registration_date=timezone.localdate() + datetime.timedelta(days=1),
        )

        # Verify roll numbers are empty/None initially
        self.assertIn(self.student_1.roll_number, [None, ""])
        self.assertIn(self.student_2.roll_number, [None, ""])

        # Run backfill management command
        call_command("assign_roll_numbers")

        # Refresh and verify assigned roll numbers
        self.student_1.refresh_from_db()
        self.student_2.refresh_from_db()
        self.assertEqual(self.student_1.roll_number, "CP-01")
        self.assertEqual(self.student_2.roll_number, "CP-02")

        # Student 3 has no enrollments - should get a fallback format
        call_command("assign_roll_numbers")
        self.student_3.refresh_from_db()
        self.assertEqual(self.student_3.roll_number, f"STUD-{self.student_3.id:02d}")
