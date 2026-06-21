from datetime import timedelta
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import CustomUser
from apps.accounts.services import UserService
from apps.academics.models import Session, Subject, TeacherAssignment
from apps.core.models import AuditLog, RolePermission
from apps.core.permission_service import seed_default_permissions
from apps.core.services import NotFoundError, BusinessRuleViolation


class UserManagementTestCase(TestCase):
    """Test suite for administrative user management view permissions, service layers, and audit logs."""

    def setUp(self):
        # Ensure Django groups exist in test db
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")
        self.student_group, _ = Group.objects.get_or_create(name="Student")
        Group.objects.get_or_create(name="Principal")
        Group.objects.get_or_create(name="Accountant")
        Group.objects.get_or_create(name="Registrar")
        Group.objects.get_or_create(name="Guardian")

        # Seed groups and permissions
        seed_default_permissions()

        # Create Admin
        self.admin_user = CustomUser.objects.create_user(
            username="admin_test",
            email="admin@test.com",
            first_name="Admin",
            last_name="User",
            password="Password123"
        )
        self.admin_user.groups.add(self.admin_group)

        # Create Teacher
        self.teacher_user = CustomUser.objects.create_user(
            username="teacher_test",
            email="teacher@test.com",
            first_name="Teacher",
            last_name="User",
            password="Password123"
        )
        self.teacher_user.groups.add(self.teacher_group)

        # Create Student
        self.student_user = CustomUser.objects.create_user(
            username="student_test",
            email="student@test.com",
            first_name="Student",
            last_name="User",
            password="Password123"
        )
        self.student_user.groups.add(self.student_group)

        # Create Session and Subject
        self.session = Session.objects.create(
            name="Computer Science 2026",
            code="CS-26",
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + timedelta(days=90),
            fee=15000.00,
        )
        self.subject = Subject.objects.create(
            name="Python Programming",
            code="PY-101",
            session=self.session,
        )

    def test_user_list_permissions(self):
        """Verify that only users with 'users:view' permission can access the user panel."""
        url = reverse("admin_panel:users:user_list")

        # Unauthenticated
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirects to login

        # Authenticated Admin (has permission)
        self.client.login(email="admin@test.com", password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "USER MANAGEMENT ACTIVE")
        self.client.logout()

        # Authenticated Student (no permission)
        self.client.login(email="student@test.com", password="Password123")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)  # Restricted returns 404 to hide path

    def test_service_toggle_activation(self):
        """Verify that toggle_user_activation changes status and logs changes to AuditLog."""
        # Ensure user starts active
        self.assertTrue(self.teacher_user.is_active)
        self.assertEqual(self.teacher_user.status, "Active")

        # Deactivate
        with self.captureOnCommitCallbacks(execute=True):
            UserService.toggle_user_activation(
                user_id=self.teacher_user.pk,
                active=False,
                admin_user=self.admin_user,
                ip_address="127.0.0.1",
                user_agent="TestAgent"
            )

        self.teacher_user.refresh_from_db()
        self.assertFalse(self.teacher_user.is_active)
        self.assertEqual(self.teacher_user.status, "Inactive")

        # Check Audit Log
        audit = AuditLog.objects.filter(
            action="update",
            model_name="accounts.CustomUser",
            object_id=self.teacher_user.pk
        ).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.user, self.admin_user)
        self.assertIn('"new": false', audit.changes)
        self.assertIn('"new": "Inactive"', audit.changes)

        # Self deactivation business rule violation
        with self.assertRaises(BusinessRuleViolation):
            with self.captureOnCommitCallbacks(execute=True):
                UserService.toggle_user_activation(
                    user_id=self.admin_user.pk,
                    active=False,
                    admin_user=self.admin_user
                )

    def test_service_toggle_lock(self):
        """Verify that toggle_user_lock locks/unlocks and logs changes to AuditLog."""
        self.assertFalse(self.teacher_user.is_locked_out)

        # Lock user
        with self.captureOnCommitCallbacks(execute=True):
            UserService.toggle_user_lock(
                user_id=self.teacher_user.pk,
                lock=True,
                admin_user=self.admin_user
            )

        self.teacher_user.refresh_from_db()
        self.assertTrue(self.teacher_user.is_locked_out)
        self.assertEqual(self.teacher_user.failed_login_attempts, 5)

        # Unlock user
        with self.captureOnCommitCallbacks(execute=True):
            UserService.toggle_user_lock(
                user_id=self.teacher_user.pk,
                lock=False,
                admin_user=self.admin_user
            )

        self.teacher_user.refresh_from_db()
        self.assertFalse(self.teacher_user.is_locked_out)
        self.assertEqual(self.teacher_user.failed_login_attempts, 0)

    def test_service_reset_password(self):
        """Verify that reset_user_password changes the password, clears lockout and logs to AuditLog."""
        with self.captureOnCommitCallbacks(execute=True):
            UserService.toggle_user_lock(
                user_id=self.teacher_user.pk,
                lock=True,
                admin_user=self.admin_user
            )
        self.teacher_user.refresh_from_db()
        self.assertTrue(self.teacher_user.is_locked_out)

        # Reset Password
        with self.captureOnCommitCallbacks(execute=True):
            UserService.reset_user_password(
                user_id=self.teacher_user.pk,
                new_password="NewSecurePassword123",
                admin_user=self.admin_user
            )

        self.teacher_user.refresh_from_db()
        self.assertFalse(self.teacher_user.is_locked_out)
        self.assertEqual(self.teacher_user.failed_login_attempts, 0)

        # Confirm password actually works
        login_success = self.client.login(email="teacher@test.com", password="NewSecurePassword123")
        self.assertTrue(login_success)

        # Check password_change action in AuditLog
        audit = AuditLog.objects.filter(
            action="password_change",
            model_name="accounts.CustomUser",
            object_id=self.teacher_user.pk
        ).first()
        self.assertIsNotNone(audit)

    def test_service_assign_user_role(self):
        """Verify that assign_user_role shifts group membership and logs changes."""
        self.assertEqual(self.teacher_user.groups.first().name, "Teacher")

        with self.captureOnCommitCallbacks(execute=True):
            UserService.assign_user_role(
                user_id=self.teacher_user.pk,
                role_name="Accountant",
                admin_user=self.admin_user
            )

        self.teacher_user.refresh_from_db()
        self.assertEqual(self.teacher_user.groups.count(), 1)
        self.assertEqual(self.teacher_user.groups.first().name, "Accountant")

        # Check Audit Log
        audit = AuditLog.objects.filter(
            action="update",
            model_name="accounts.CustomUser",
            object_id=self.teacher_user.pk
        ).first()
        self.assertIsNotNone(audit)
        self.assertIn("roles", audit.changes)

    def test_service_assign_teacher_session(self):
        """Verify that assign_teacher_session allocates session scope and logs changes."""
        # Standard teacher assignment
        with self.captureOnCommitCallbacks(execute=True):
            assignment = UserService.assign_teacher_session(
                teacher_id=self.teacher_user.pk,
                session_id=self.session.pk,
                subject_id=self.subject.pk,
                admin_user=self.admin_user
            )

        self.assertIsNotNone(assignment)
        self.assertTrue(assignment.is_active)
        self.assertEqual(assignment.teacher, self.teacher_user)
        self.assertEqual(assignment.session, self.session)
        self.assertEqual(assignment.subject, self.subject)

        # Check Audit Log
        audit = AuditLog.objects.filter(
            model_name="academics.TeacherAssignment",
            object_id=assignment.pk
        ).first()
        self.assertIsNotNone(audit)

        # Attempt assignment on non-teacher student
        with self.assertRaises(BusinessRuleViolation):
            with self.captureOnCommitCallbacks(execute=True):
                UserService.assign_teacher_session(
                    teacher_id=self.student_user.pk,
                    session_id=self.session.pk,
                    admin_user=self.admin_user
                )

    def test_view_post_restrictions(self):
        """Verify that mutating views reject GET requests with a 404."""
        self.client.login(email="admin@test.com", password="Password123")

        urls = [
            reverse("admin_panel:users:user_toggle_activation", args=[self.teacher_user.pk]),
            reverse("admin_panel:users:user_toggle_lock", args=[self.teacher_user.pk]),
            reverse("admin_panel:users:user_reset_password", args=[self.teacher_user.pk]),
            reverse("admin_panel:users:user_assign_role", args=[self.teacher_user.pk]),
            reverse("admin_panel:users:user_assign_session", args=[self.teacher_user.pk]),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404)

    def test_profile_view_get(self):
        """Verify that profile page renders successfully and passes form instance."""
        self.client.login(email="admin@test.com", password="Password123")
        url = reverse("accounts:profile_view")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "admin_test")
        self.assertIn("form", response.context)

    def test_profile_view_post(self):
        """Verify that posting changes updates user info and redirects."""
        self.client.login(email="admin@test.com", password="Password123")
        url = reverse("accounts:profile_view")
        response = self.client.post(url, {
            "first_name": "UpdatedFirst",
            "last_name": "UpdatedLast",
            "phone": "03001234567",
            "cnic": "38403-1234567-1",
        })
        self.assertEqual(response.status_code, 302)
        self.admin_user.refresh_from_db()
        self.assertEqual(self.admin_user.first_name, "UpdatedFirst")
        self.assertEqual(self.admin_user.last_name, "UpdatedLast")
        self.assertEqual(self.admin_user.phone, "03001234567")
        self.assertEqual(self.admin_user.cnic, "38403-1234567-1")

