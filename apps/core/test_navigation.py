from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

User = get_user_model()

class NavigationIntegrationTests(TestCase):
    def setUp(self):
        super().setUp()
        
        # Create groups
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_registrar = Group.objects.create(name="Registrar")
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_accountant = Group.objects.create(name="Accountant")
        self.group_student = Group.objects.create(name="Student")
        self.group_guardian = Group.objects.create(name="Guardian")

        # Create users
        self.admin_user = User.objects.create_user(username="admin@test.com", email="admin@test.com", password="password123")
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(username="principal@test.com", email="principal@test.com", password="password123")
        self.principal_user.groups.add(self.group_principal)

        self.registrar_user = User.objects.create_user(username="registrar@test.com", email="registrar@test.com", password="password123")
        self.registrar_user.groups.add(self.group_registrar)

        self.teacher_user = User.objects.create_user(username="teacher@test.com", email="teacher@test.com", password="password123")
        self.teacher_user.groups.add(self.group_teacher)

        self.accountant_user = User.objects.create_user(username="accountant@test.com", email="accountant@test.com", password="password123")
        self.accountant_user.groups.add(self.group_accountant)

        self.student_user = User.objects.create_user(username="student@test.com", email="student@test.com", password="password123")
        self.student_user.groups.add(self.group_student)

        self.guardian_user = User.objects.create_user(username="guardian@test.com", email="guardian@test.com", password="password123")
        self.guardian_user.groups.add(self.group_guardian)

        # Create profiles
        from apps.students.models import Student, Guardian
        student_profile = Student.objects.create(
            full_name="Test Student",
            email="student@test.com",
            portal_user=self.student_user,
            status="Active"
        )
        Guardian.objects.create(
            student=student_profile,
            full_name="Test Guardian",
            email="guardian@test.com",
            portal_user=self.guardian_user
        )

    def test_new_routes_reverse(self):
        """Verify all new navigation URLs reverse successfully."""
        self.assertEqual(reverse("admin_panel:audit:audit_log_list"), "/panel/admin/audit/")
        self.assertEqual(reverse("admin_panel:ai_engine:prediction_list"), "/panel/admin/ai/predictions/")
        self.assertEqual(reverse("admin_panel:ai_engine:model_version_list"), "/panel/admin/ai/models/")
        self.assertEqual(reverse("admin_panel:ai_engine:dropout_risk_dashboard"), "/panel/admin/ai/dropout-risk/")
        self.assertEqual(reverse("admin_panel:attendance:attendance_overview"), "/panel/admin/attendance/")
        self.assertEqual(reverse("admin_panel:attendance:low_attendance_report"), "/panel/admin/attendance/low-attendance/")
        self.assertEqual(reverse("admin_panel:exams:grade_config_list"), "/panel/admin/exams/grade-config/")

    def test_admin_sidebar_and_dashboard_links(self):
        """Verify that Admin sidebar contains all 7 links and dashboard card links to dropout dashboard."""
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Assert all 7 links exist in sidebar HTML
        self.assertContains(response, 'href="/panel/admin/audit/"')
        self.assertContains(response, 'href="/panel/admin/ai/predictions/"')
        self.assertContains(response, 'href="/panel/admin/ai/models/"')
        self.assertContains(response, 'href="/panel/admin/ai/dropout-risk/"')
        self.assertContains(response, 'href="/panel/admin/attendance/"')
        self.assertContains(response, 'href="/panel/admin/attendance/low-attendance/"')
        self.assertContains(response, 'href="/panel/admin/exams/grade-config/"')

        # Assert dashboard metrics card links to dropout risk dashboard
        self.assertContains(response, 'href="/panel/admin/ai/dropout-risk/"')

    def test_principal_sidebar_and_dashboard_links(self):
        """Verify that Principal sidebar contains only allowed 3 links and dashboard card links correctly."""
        self.client.force_login(self.principal_user)
        response = self.client.get(reverse("admin_panel:dashboard"))
        self.assertEqual(response.status_code, 200)

        # Principal should see the 3 allowed links
        self.assertContains(response, 'href="/panel/admin/ai/dropout-risk/"')
        self.assertContains(response, 'href="/panel/admin/attendance/low-attendance/"')
        self.assertContains(response, 'href="/panel/admin/exams/grade-config/"')

        # Principal should NOT see the 4 forbidden links
        self.assertNotContains(response, 'href="/panel/admin/audit/"')
        self.assertNotContains(response, 'href="/panel/admin/ai/predictions/"')
        self.assertNotContains(response, 'href="/panel/admin/ai/models/"')
        self.assertNotContains(response, 'href="/panel/admin/attendance/"')

        # Assert dashboard metrics card links to dropout risk dashboard for Principal
        self.assertContains(response, 'href="/panel/admin/ai/dropout-risk/"')

    def test_unauthorized_roles_cannot_see_new_links(self):
        """Verify that Registrar, Teacher, Accountant, Student, Guardian do not see unauthorized new links."""
        roles_to_test = [
            (self.registrar_user, reverse("registrar_panel:dashboard")),
            (self.teacher_user, reverse("teacher_panel:dashboard")),
            (self.accountant_user, reverse("accounts_panel:dashboard")),
            (self.student_user, reverse("student_portal:dashboard")),
            (self.guardian_user, reverse("guardian_portal:dashboard")),
        ]

        forbidden_links = [
            'href="/panel/admin/audit/"',
            'href="/panel/admin/ai/predictions/"',
            'href="/panel/admin/ai/models/"',
            'href="/panel/admin/ai/dropout-risk/"',
            'href="/panel/admin/attendance/"',
            'href="/panel/admin/attendance/low-attendance/"',
            'href="/panel/admin/exams/grade-config/"',
        ]

        for user, dashboard_url in roles_to_test:
            self.client.force_login(user)
            response = self.client.get(dashboard_url)
            self.assertEqual(response.status_code, 200)
            for link in forbidden_links:
                self.assertNotContains(response, link)

    def test_page_access_controls(self):
        """Verify that page routing enforces role access controls for all new pages."""
        pages = [
            ("admin_panel:audit:audit_log_list", {}, ["Admin"], ["Principal", "Teacher"]),
            ("admin_panel:ai_engine:prediction_list", {}, ["Admin"], ["Principal", "Teacher"]),
            ("admin_panel:ai_engine:model_version_list", {}, ["Admin"], ["Principal", "Teacher"]),
            ("admin_panel:ai_engine:dropout_risk_dashboard", {}, ["Admin", "Principal"], ["Teacher"]),
            ("admin_panel:attendance:attendance_overview", {}, ["Admin", "Principal"], ["Teacher"]),
            ("admin_panel:attendance:low_attendance_report", {}, ["Admin", "Principal"], ["Teacher"]),
            ("admin_panel:exams:grade_config_list", {}, ["Admin", "Principal"], ["Teacher"]),
        ]

        user_map = {
            "Admin": self.admin_user,
            "Principal": self.principal_user,
            "Teacher": self.teacher_user,
        }

        for url_name, kwargs, allowed_roles, denied_roles in pages:
            url = reverse(url_name, kwargs=kwargs)
            
            # Test allowed
            for role in allowed_roles:
                user = user_map[role]
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200, f"Role {role} should have access to {url_name} ({url})")
            
            # Test denied
            for role in denied_roles:
                user = user_map[role]
                self.client.force_login(user)
                response = self.client.get(url)
                self.assertEqual(response.status_code, 404, f"Role {role} should NOT have access to {url_name} ({url})")
