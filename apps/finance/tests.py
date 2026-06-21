import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session
from apps.students.models import Student, Enrollment
from apps.finance.models import Payment
from apps.finance.services import get_pending_dues

User = get_user_model()


class PendingDuesTests(TestCase):
    def setUp(self):
        super().setUp()

        # Create roles/groups
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_accountant, _ = Group.objects.get_or_create(name="Accountant")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin_dues@test.com", email="admin_dues@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.accountant_user = User.objects.create_user(
            username="accountant_dues@test.com", email="accountant_dues@test.com", password="password"
        )
        self.accountant_user.groups.add(self.group_accountant)

        self.teacher_user = User.objects.create_user(
            username="teacher_dues@test.com", email="teacher_dues@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Create sessions
        self.session_a = Session.objects.create(
            name="Session A",
            status="Active",
            fee=Decimal("1500.00"),
            registration_fee=Decimal("500.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
        )

        # Create students
        self.student_1 = Student.objects.create(
            full_name="Ahmed Hassan",
            roll_number="IICE-001",
        )
        self.student_2 = Student.objects.create(
            full_name="Jane Smith",
            roll_number="IICE-002",
        )

        # Enrollments
        self.enrollment_1 = Enrollment.objects.create(
            student=self.student_1,
            session=self.session_a,
            status="Active",
            due_date=timezone.localdate() + datetime.timedelta(days=5),
        )
        self.enrollment_2 = Enrollment.objects.create(
            student=self.student_2,
            session=self.session_a,
            status="Active",
            due_date=timezone.localdate() + datetime.timedelta(days=5),
        )

    def test_get_pending_dues_returns_outstanding_only(self):
        """get_pending_dues should return only students with outstanding balance > 0."""
        # Enrollment 1 has total payable = 1500 + 500 = 2000. It has 0 paid, so outstanding_balance = 2000.
        # Let's make Enrollment 2 fully paid by creating a payment of 2000.
        Payment.objects.create(
            enrollment=self.enrollment_2,
            amount=Decimal("2000.00"),
            payment_date=timezone.localdate(),
            payment_status="confirmed",
            is_late_fee_payment=False,
        )

        dues = get_pending_dues()

        # Should only return enrollment 1 (outstanding = 2000)
        self.assertEqual(len(dues), 1)
        self.assertEqual(dues[0]["roll_number"], "IICE-001")
        self.assertEqual(dues[0]["student_name"], "Ahmed Hassan")
        self.assertEqual(dues[0]["session_name"], "Session A")
        self.assertEqual(dues[0]["outstanding_balance"], Decimal("2000.00"))

    def test_get_pending_dues_excludes_inactive_enrollments(self):
        """get_pending_dues should only return active enrollments."""
        # Change enrollment 1 status to Completed
        self.enrollment_1.status = "Completed"
        self.enrollment_1.save()

        # Change enrollment 2 status to Frozen
        self.enrollment_2.status = "Frozen"
        self.enrollment_2.save()

        dues = get_pending_dues()

        # Since no active enrollments exist, it should return an empty list
        self.assertEqual(len(dues), 0)

    def test_view_access_restrictions(self):
        """Admin and Accountant roles can access the Pending Dues view, others are denied (404)."""
        admin_url = reverse("admin_panel:pending_dues")
        accounts_url = reverse("accounts_panel:pending_dues")

        # Test Admin access
        self.client.force_login(self.admin_user)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 200)

        # Test Accountant access
        self.client.force_login(self.accountant_user)
        response = self.client.get(accounts_url)
        self.assertEqual(response.status_code, 200)

        # Test Teacher access (should be denied)
        self.client.force_login(self.teacher_user)
        response = self.client.get(admin_url)
        self.assertEqual(response.status_code, 404)

        response = self.client.get(accounts_url)
        self.assertEqual(response.status_code, 404)
