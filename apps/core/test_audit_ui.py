import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from apps.core.models import AuditLog

User = get_user_model()


@override_settings(ROOT_URLCONF="config.urls")
class AuditLogUITests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed roles/groups
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_registrar = Group.objects.create(name="Registrar")
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_student = Group.objects.create(name="Student")
        self.group_guardian = Group.objects.create(name="Guardian")
        self.group_accountant = Group.objects.create(name="Accountant")

        # Users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(
            username="principal@test.com", email="principal@test.com", password="password"
        )
        self.principal_user.groups.add(self.group_principal)

        self.registrar_user = User.objects.create_user(
            username="registrar@test.com", email="registrar@test.com", password="password"
        )
        self.registrar_user.groups.add(self.group_registrar)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.accountant_user = User.objects.create_user(
            username="accountant@test.com", email="accountant@test.com", password="password"
        )
        self.accountant_user.groups.add(self.group_accountant)

        self.student_user = User.objects.create_user(
            username="student@test.com", email="student@test.com", password="password"
        )
        self.student_user.groups.add(self.group_student)

        self.guardian_user = User.objects.create_user(
            username="guardian@test.com", email="guardian@test.com", password="password"
        )
        self.guardian_user.groups.add(self.group_guardian)

        # Seed initial audit logs
        self.log_1 = AuditLog.objects.create(
            user=self.admin_user,
            action="create",
            model_name="students.Student",
            object_id="101",
            changes=json.dumps({"full_name": [None, "Ahmed Khan"]}),
            ip_address="127.0.0.1",
            user_agent="Mozilla/5.0",
            timestamp=timezone.now()
        )

        self.log_2 = AuditLog.objects.create(
            user=self.admin_user,
            action="update",
            model_name="academics.Session",
            object_id="202",
            changes=json.dumps({"status": ["Draft", "Active"]}),
            ip_address="192.168.1.1",
            user_agent="Chrome/100",
            timestamp=timezone.now()
        )

    def test_admin_can_open_audit_log_list(self):
        """Verify that Admin is allowed to load the audit log list page."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:audit:audit_log_list"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_open_audit_log_detail(self):
        """Verify that Admin is allowed to view audit log details."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk}))
        self.assertEqual(response.status_code, 200)

    def test_blocked_roles(self):
        """Verify that Principal, Registrar, Teacher, Accountant, Student, Guardian are blocked from list/details."""
        blocked_users = [
            self.principal_user,
            self.registrar_user,
            self.teacher_user,
            self.accountant_user,
            self.student_user,
            self.guardian_user,
        ]

        list_url = reverse("admin_panel:audit:audit_log_list")
        detail_url = reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk})

        for user in blocked_users:
            self.client.force_login(user)
            # Check list view
            response = self.client.get(list_url)
            self.assertEqual(response.status_code, 404, f"User {user.username} was not blocked from audit log list.")
            
            # Check detail view
            response = self.client.get(detail_url)
            self.assertEqual(response.status_code, 404, f"User {user.username} was not blocked from audit log detail.")

    def test_anonymous_redirects_to_login(self):
        """Verify that anonymous requests are redirected to the login page."""
        self.client.logout()
        response = self.client.get(reverse("admin_panel:audit:audit_log_list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

        response = self.client.get(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_list_displays_seeded_logs(self):
        """Verify that list view contains the data from seeded logs."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:audit:audit_log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "students.Student")
        self.assertContains(response, "academics.Session")
        self.assertContains(response, "127.0.0.1")
        self.assertContains(response, "192.168.1.1")

    def test_detail_displays_seeded_data(self):
        """Verify that detail page displays structured changes and model metadata."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "students.Student")
        self.assertContains(response, "101")
        self.assertContains(response, "127.0.0.1")
        self.assertContains(response, "Mozilla/5.0")
        self.assertContains(response, "Ahmed Khan")

    def test_filters_work(self):
        """Verify action, user, model_name, and search filters restrict the output list."""
        self.client.force_login(self.admin_user)

        # 1. Action filter
        response = self.client.get(reverse("admin_panel:audit:audit_log_list") + "?action=create")
        self.assertContains(response, "students.Student")
        self.assertNotContains(response, "academics.Session")

        # 2. Model Name filter
        response = self.client.get(reverse("admin_panel:audit:audit_log_list") + "?model_name=academics.Session")
        self.assertNotContains(response, "students.Student")
        self.assertContains(response, "academics.Session")

        # 3. User filter
        response = self.client.get(reverse("admin_panel:audit:audit_log_list") + "?user=admin@test.com")
        self.assertContains(response, "students.Student")
        self.assertContains(response, "academics.Session")

        # 4. General search filter (changes payload search)
        response = self.client.get(reverse("admin_panel:audit:audit_log_list") + "?search_text=Ahmed")
        self.assertContains(response, "students.Student")
        self.assertNotContains(response, "academics.Session")

    def test_pagination_works(self):
        """Verify that pagination limits records per page and generates links."""
        self.client.force_login(self.admin_user)
        # Seed 30 more audit logs
        for i in range(30):
            AuditLog.objects.create(
                user=self.admin_user,
                action="update",
                model_name="students.Student",
                object_id=str(1000 + i),
                timestamp=timezone.now()
            )

        response = self.client.get(reverse("admin_panel:audit:audit_log_list"))
        # 32 total records, should display 25 on page 1
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj), 25)
        self.assertTrue(page_obj.has_next())

        # Load page 2
        response_page2 = self.client.get(reverse("admin_panel:audit:audit_log_list") + "?page=2")
        page_obj_2 = response_page2.context["page_obj"]
        self.assertEqual(len(page_obj_2), 7)
        self.assertTrue(page_obj_2.has_previous())

    def test_missing_audit_log_returns_404(self):
        """Verify detail view returns 404 for non-existent PKs."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": 999999}))
        self.assertEqual(response.status_code, 404)

    def test_get_does_not_mutate_records(self):
        """Verify GET request does not modify database log count or fields."""
        self.client.force_login(self.admin_user)
        before_count = AuditLog.objects.count()
        response = self.client.get(reverse("admin_panel:audit:audit_log_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(AuditLog.objects.count(), before_count)

        response_detail = self.client.get(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk}))
        self.assertEqual(response_detail.status_code, 200)
        self.assertEqual(AuditLog.objects.count(), before_count)

    def test_post_does_not_mutate_records(self):
        """Verify POST requests to audit list/detail are rejected or do not add/modify database log entries."""
        self.client.force_login(self.admin_user)
        before_count = AuditLog.objects.count()
        
        # POST to list view should either fail or do nothing
        response = self.client.post(reverse("admin_panel:audit:audit_log_list"), {"action": "delete"})
        self.assertEqual(AuditLog.objects.count(), before_count)

        # POST to detail view should either fail or do nothing
        response = self.client.post(reverse("admin_panel:audit:audit_log_detail", kwargs={"pk": self.log_1.pk}), {"action": "delete"})
        self.assertEqual(AuditLog.objects.count(), before_count)
