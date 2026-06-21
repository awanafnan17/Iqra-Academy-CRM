import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.core.permission_service import seed_default_permissions, has_permission
from apps.core.models import RolePermission, AuditLog
from apps.academics.models import Session, Subject
from apps.exams.models import Exam
from apps.students.models import Student, Enrollment
from apps.finance.models import Payment

User = get_user_model()

class GranularPermissionTests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed Group roles
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_principal, _ = Group.objects.get_or_create(name="Principal")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")
        self.group_accountant, _ = Group.objects.get_or_create(name="Accountant")

        # Seed users
        self.admin_user = User.objects.create_user(
            username="admin_perm@test.com", email="admin_perm@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(
            username="principal_perm@test.com", email="principal_perm@test.com", password="password"
        )
        self.principal_user.groups.add(self.group_principal)

        self.teacher_user = User.objects.create_user(
            username="teacher_perm@test.com", email="teacher_perm@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.accountant_user = User.objects.create_user(
            username="accountant_perm@test.com", email="accountant_perm@test.com", password="password"
        )
        self.accountant_user.groups.add(self.group_accountant)

        # Seed default permission matrix
        seed_default_permissions()

        # Create minimal database objects for view requests
        self.session = Session.objects.create(
            name="Session X",
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
        )
        self.subject = Subject.objects.create(name="English", code="E101")

        # Create an exam
        self.exam = Exam.objects.create(
            session=self.session,
            subject=self.subject,
            name="Midterm",
            exam_date=timezone.localdate(),
            total_marks=100,
            passing_marks=40,
            created_by=self.admin_user,
        )

        # Create payment
        self.student = Student.objects.create(full_name="Fatima Khan")
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
        )
        self.payment = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("500.00"),
            payment_date=timezone.localdate(),
            payment_status="confirmed",
        )

    def test_teachers_cannot_access_finance_create(self):
        """Teacher role should get 404 (denied) on payment creation."""
        url = reverse("admin_panel:finance:payment_create")
        self.client.force_login(self.teacher_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_accountant_cannot_edit_exams(self):
        """Accountant role should get 404 (denied) on exam editing."""
        url = reverse("admin_panel:exams:exam_edit", kwargs={"pk": self.exam.pk})
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_principal_cannot_delete_payments(self):
        """Principal role should get 404 (denied) on payment deletion."""
        url = reverse("admin_panel:finance:payment_delete", kwargs={"pk": self.payment.pk})
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_admin_has_full_control(self):
        """Admin role should bypass granular checks and hit the stubs/views successfully (200)."""
        from unittest.mock import patch
        from django.http import HttpResponse

        self.client.force_login(self.admin_user)

        with patch("apps.exams.views.render", return_value=HttpResponse("Mocked response")):
            # Finance create
            url_create = reverse("admin_panel:finance:payment_create")
            response = self.client.get(url_create)
            self.assertEqual(response.status_code, 200)

            # Finance delete
            url_delete = reverse("admin_panel:finance:payment_delete", kwargs={"pk": self.payment.pk})
            response = self.client.get(url_delete)
            self.assertEqual(response.status_code, 302)

            # Exam edit
            url_edit = reverse("admin_panel:exams:exam_edit", kwargs={"pk": self.exam.pk})
            response = self.client.get(url_edit)
            self.assertEqual(response.status_code, 200)

    def test_permission_modification_logs_audit_trail(self):
        """Modifying the permission matrix should log changes to the central AuditLog."""
        url = reverse("admin_panel:permissions")
        self.client.force_login(self.admin_user)

        # Submit a modification POST request
        post_data = {
            "perm_Teacher_finance_create": "on", # Turn on create for Teacher
        }

        # Clean current audit logs
        AuditLog.objects.all().delete()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 302) # Redirects back

        # Check that AuditLog contains a record of update on core.RolePermission
        logs = AuditLog.objects.filter(model_name="core.RolePermission", action="update")
        self.assertEqual(logs.count(), 1)

        log_entry = logs.first()
        self.assertEqual(log_entry.user, self.admin_user)
        self.assertIn("matrix_update", log_entry.changes)

        # Verify the permission actually updated in DB
        teacher_fin_create = RolePermission.objects.get(role_name="Teacher", module_name="finance")
        self.assertTrue(teacher_fin_create.can_create)
