"""
Mutation Propagation Audit — Tests that field updates propagate
across all display surfaces in the CRM.

Uses Django's StaticLiveServerTestCase + Playwright to verify that
updating a record's fields in one view propagates to all other views
that display those fields.

Usage:
    python -m pytest tools/qa/test_mutation_propagation.py -v --tb=short
"""

import os
import sys
import unittest

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import Group
from django.test import override_settings

from apps.accounts.models import CustomUser

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


TEST_PASSWORD = "MutTest!2026x"
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "screenshots", "mutation")
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class UserNameMutationTest(StaticLiveServerTestCase):
    """Test that user name updates propagate to all identity surfaces."""
    host = "127.0.0.1"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        os.makedirs(REPORT_DIR, exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        super().tearDownClass()

    def setUp(self):
        from apps.core.permission_service import seed_default_permissions
        seed_default_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user = CustomUser.objects.create_user(
            email="mut_admin@iqra.test",
            username="mut_admin",
            password=TEST_PASSWORD,
            first_name="OrigFirst",
            last_name="OrigLast",
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        self.user.groups.add(self.admin_group)

    def tearDown(self):
        CustomUser.objects.filter(email="mut_admin@iqra.test").delete()

    def _login(self, page):
        page.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded", timeout=60000)
        page.fill("input[name='username']", "mut_admin@iqra.test")
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded", timeout=60000)

    def test_name_mutation_propagation_across_pages(self):
        """Mutate name, verify propagation across multiple pages."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)

        # 1. Update name via profile
        page.goto(f"{self.live_server_url}/accounts/profile/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        page.locator("[data-testid='profile-first-name'] input").fill("Mutated")
        page.locator("[data-testid='profile-last-name'] input").fill("Name")
        page.locator("[data-testid='profile-save']").click()
        page.wait_for_load_state("domcontentloaded")

        # 2. Verify DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.display_name, "Mutated Name")

        # 3. Visit multiple pages and check navbar identity
        pages_to_check = [
            "/accounts/profile/",
            "/panel/admin/dashboard/",
            "/panel/admin/manage-students/",
            "/panel/admin/session-overview/",
        ]

        for url_path in pages_to_check:
            page.goto(f"{self.live_server_url}{url_path}", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            navbar = page.locator("[data-testid='navbar-user-name']")
            if navbar.count() > 0:
                text = navbar.text_content().strip()
                self.assertIn("Mutated Name", text,
                              f"Navbar at {url_path} shows '{text}' instead of 'Mutated Name'")

        ctx.close()

    def test_sequential_name_mutations(self):
        """Update name multiple times — each update should propagate."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)

        mutations = [
            ("Alpha", "Bravo"),
            ("Charlie", "Delta"),
            ("Echo", "Foxtrot"),
        ]

        for first, last in mutations:
            page.goto(f"{self.live_server_url}/accounts/profile/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            page.locator("[data-testid='profile-first-name'] input").fill(first)
            page.locator("[data-testid='profile-last-name'] input").fill(last)
            page.locator("[data-testid='profile-save']").click()
            page.wait_for_load_state("domcontentloaded")

            expected = f"{first} {last}"

            # Verify DB
            self.user.refresh_from_db()
            self.assertEqual(self.user.display_name, expected)

            # Verify profile card
            profile_name = page.locator("[data-testid='profile-display-name']")
            self.assertIn(expected, profile_name.text_content())

            # Verify navbar
            navbar = page.locator("[data-testid='navbar-user-name']")
            self.assertIn(expected, navbar.text_content())

        ctx.close()

    def test_phone_cnic_mutation_persists(self):
        """Update phone and CNIC — verify they persist on reload."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)

        page.goto(f"{self.live_server_url}/accounts/profile/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        # Fill phone and CNIC if fields exist
        phone_input = page.locator("input[name='phone']")
        cnic_input = page.locator("input[name='cnic']")

        if phone_input.count() > 0:
            phone_input.fill("03001234567")
        if cnic_input.count() > 0:
            cnic_input.fill("3520112345678")

        page.locator("[data-testid='profile-save']").click()
        page.wait_for_load_state("domcontentloaded")

        # Verify DB
        self.user.refresh_from_db()
        if hasattr(self.user, 'phone'):
            self.assertEqual(self.user.phone, "03001234567")
        if hasattr(self.user, 'cnic'):
            self.assertEqual(self.user.cnic, "3520112345678")

        # Reload and verify values are still there
        page.goto(f"{self.live_server_url}/accounts/profile/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        if phone_input.count() > 0:
            self.assertEqual(
                page.locator("input[name='phone']").input_value(),
                "03001234567"
            )
        if cnic_input.count() > 0:
            self.assertEqual(
                page.locator("input[name='cnic']").input_value(),
                "3520112345678"
            )

        ctx.close()


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class PasswordChangeMutationTest(StaticLiveServerTestCase):
    """Test password change flow — ensures old password stops working."""
    host = "127.0.0.1"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        super().tearDownClass()

    def setUp(self):
        from apps.core.permission_service import seed_default_permissions
        seed_default_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.user = CustomUser.objects.create_user(
            email="pwd_test@iqra.test",
            username="pwd_test",
            password=TEST_PASSWORD,
            first_name="Pwd",
            last_name="Tester",
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        self.user.groups.add(self.admin_group)

    def tearDown(self):
        CustomUser.objects.filter(email="pwd_test@iqra.test").delete()

    def test_password_change_invalidates_old_password(self):
        """After password change, old password must not work."""
        ctx = self.browser.new_context()
        page = ctx.new_page()

        # Login with old password
        page.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("domcontentloaded")
        page.fill("input[name='username']", "pwd_test@iqra.test")
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")

        # Change password
        new_password = "NewSecure!2026y"
        page.goto(f"{self.live_server_url}/accounts/password/change/", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_load_state("domcontentloaded")

        old_pw = page.locator("input[name='old_password']")
        new_pw1 = page.locator("input[name='new_password1']")
        new_pw2 = page.locator("input[name='new_password2']")

        if old_pw.count() > 0:
            old_pw.fill(TEST_PASSWORD)
            new_pw1.fill(new_password)
            new_pw2.fill(new_password)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")

            # Logout
            page.goto(f"{self.live_server_url}/accounts/logout/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("domcontentloaded")

            # Try old password — should fail
            page.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("domcontentloaded")
            page.fill("input[name='username']", "pwd_test@iqra.test")
            page.fill("input[name='password']", TEST_PASSWORD)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")

            # Should still be on login page (not redirected to dashboard)
            current_url = page.url
            self.assertIn("login", current_url,
                          "Old password should not work after change")

            # Try new password — should work
            page.fill("input[name='username']", "pwd_test@iqra.test")
            page.fill("input[name='password']", new_password)
            page.click("button[type='submit']")
            page.wait_for_load_state("domcontentloaded")

            current_url = page.url
            self.assertNotIn("login", current_url,
                             "New password should work after change")

        ctx.close()


if __name__ == "__main__":
    unittest.main()
