import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.test import TestCase, override_settings
from django.contrib.auth.models import Group
from django.urls import reverse
from apps.accounts.models import CustomUser
from apps.students.models import Lead, Student
from apps.academics.models import Session

TEST_PASSWORD = "LeadsTest!2026"
DENIED = [302, 403, 404]

@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class RegistrarLeadsTests(TestCase):
    """Functional tests for Registrar leads workflows (DEF-REGISTRAR-01)."""

    @classmethod
    def setUpTestData(cls):
        # Create Registrar role group and user
        cls.registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        cls.registrar_user = CustomUser.objects.create_user(
            email="registrar@iqra.test",
            username="registrar_leads",
            password=TEST_PASSWORD,
            first_name="Registrar",
            last_name="User",
            status="Active",
        )
        cls.registrar_user.groups.add(cls.registrar_group)

        # Create Accountant user (unauthorized role for leads)
        cls.accountant_group, _ = Group.objects.get_or_create(name="Accountant")
        cls.accountant_user = CustomUser.objects.create_user(
            email="accountant@iqra.test",
            username="accountant_leads",
            password=TEST_PASSWORD,
            first_name="Accountant",
            last_name="User",
            status="Active",
        )
        cls.accountant_user.groups.add(cls.accountant_group)

        # Create a Session for Lead association
        cls.session = Session.objects.create(
            name="Session for Leads",
            code="LEADS2026",
            roll_prefix="LD",
            session_type="monthly",
            session_category="Academic",
            academic_year="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
            fee="4000.00",
            status="Active",
        )

    def setUp(self):
        Lead.objects.all().delete()

    def test_registrar_authenticated_get_200(self):
        """1. Registrar authenticated GET returns 200."""
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)
        response = self.client.get(reverse("registrar_panel:lead_list"))
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_roles_receive_denial(self):
        """2. Unauthorized roles receive the intended denial."""
        self.client.login(username=self.accountant_user.email, password=TEST_PASSWORD)
        response = self.client.get(reverse("registrar_panel:lead_list"))
        self.assertIn(response.status_code, DENIED)

    def test_empty_leads_list_renders_correctly(self):
        """3. Empty leads list renders correctly."""
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)
        response = self.client.get(reverse("registrar_panel:lead_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Leads Found")

    def test_populated_leads_list_renders_correctly(self):
        """4. Populated leads list renders correctly."""
        Lead.objects.create(
            name="Jane Doe",
            email="jane@iqra.test",
            phone="03001234567",
            status="New",
            interested_session=self.session,
        )
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)
        response = self.client.get(reverse("registrar_panel:lead_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jane Doe")
        self.assertContains(response, "jane@iqra.test")

    def test_search_and_filter_behavior(self):
        """5. Search/filter behavior works."""
        l1 = Lead.objects.create(
            name="Alice Smith", email="alice@iqra.test", phone="111", status="New"
        )
        l2 = Lead.objects.create(
            name="Bob Jones", email="bob@iqra.test", phone="222", status="Contacted"
        )
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)

        # Filter by query
        response = self.client.get(reverse("registrar_panel:lead_list"), {"q": "Alice"})
        self.assertContains(response, "Alice Smith")
        self.assertNotContains(response, "Bob Jones")

        # Filter by status
        response = self.client.get(reverse("registrar_panel:lead_list"), {"status": "Contacted"})
        self.assertContains(response, "Bob Jones")
        self.assertNotContains(response, "Alice Smith")

    def test_pagination_works_when_applicable(self):
        """6. Pagination works when applicable."""
        for i in range(25):
            Lead.objects.create(name=f"Lead {i}", status="New")
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)
        response = self.client.get(reverse("registrar_panel:lead_list"))
        self.assertEqual(response.status_code, 200)
        # Should contain pagination element
        self.assertContains(response, "pagination")

    def test_linked_detail_action_urls_resolve(self):
        """7. Linked detail/action URLs resolve."""
        lead = Lead.objects.create(name="Resolve Test", status="New")
        self.client.login(username=self.registrar_user.email, password=TEST_PASSWORD)

        # Test Detail page
        detail_url = reverse("registrar_panel:lead_detail", args=[lead.pk])
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)

        # Test Edit page
        edit_url = reverse("registrar_panel:lead_edit", args=[lead.pk])
        response = self.client.get(edit_url)
        self.assertEqual(response.status_code, 200)

        # Test Convert lead to Student
        convert_url = reverse("registrar_panel:lead_convert", args=[lead.pk])
        response = self.client.post(convert_url)
        # Should redirect to student detail
        self.assertEqual(response.status_code, 302)
        lead.refresh_from_db()
        self.assertEqual(lead.status, "Converted")
        self.assertIsNotNone(lead.converted_student)
        self.assertEqual(lead.converted_student.full_name, "Resolve Test")
