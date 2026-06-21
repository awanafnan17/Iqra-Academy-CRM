"""
Browser regression test: Profile identity propagation.

Verifies that updating first_name and last_name on /accounts/profile/
propagates the updated display name to ALL shared identity surfaces
across the CRM — navbar, dropdown, profile card, dashboard, and
other pages — including after refresh, navigation, and re-login.

Uses Django's StaticLiveServerTestCase + Playwright for isolated
testing against a temporary SQLite test database.
"""

import os
import sys
import unittest

# ── Django bootstrap ──────────────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")
# Playwright uses an event loop — allow Django ORM calls from async context
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django  # noqa: E402
django.setup()

from django.contrib.staticfiles.testing import StaticLiveServerTestCase  # noqa: E402
from django.contrib.auth.models import Group  # noqa: E402
from django.test import override_settings  # noqa: E402

from apps.accounts.models import CustomUser  # noqa: E402

# Try importing Playwright — skip gracefully if not installed
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


TEST_PASSWORD = "QaTesting!2026x"
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "screenshots")


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class ProfileIdentityPropagationTest(StaticLiveServerTestCase):
    host = "127.0.0.1"
    """Test that profile name updates propagate to all identity surfaces."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        # Launch Playwright browser
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        super().tearDownClass()

    def setUp(self):
        """Create a temporary admin user for testing."""
        # Ensure Admin group exists
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")

        # Create test user with known initial name
        self.user = CustomUser.objects.create_user(
            email="qa_test_admin@iqra.test",
            username="qa_test_admin",
            password=TEST_PASSWORD,
            first_name="OldFirst",
            last_name="OldLast",
            status="Active",
        )
        self.user.groups.add(self.admin_group)
        self.user.is_staff = True
        self.user.is_superuser = True
        self.user.save()

    def tearDown(self):
        """Clean up temporary user."""
        CustomUser.objects.filter(email="qa_test_admin@iqra.test").delete()

    def _login(self, page):
        """Log in via the browser login form."""
        page.goto(f"{self.live_server_url}/accounts/login/")
        page.wait_for_load_state("domcontentloaded")
        # Fill login form — USERNAME_FIELD is email
        page.fill("input[name='username']", "qa_test_admin@iqra.test")
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")

    def _screenshot(self, page, name):
        """Capture a screenshot for debugging evidence."""
        path = os.path.join(SCREENSHOT_DIR, f"{name}.png")
        page.screenshot(path=path, full_page=True)
        return path

    def test_profile_update_propagates_to_all_identity_surfaces(self):
        """
        Full regression test:
        1. Log in
        2. Navigate to profile
        3. Update first/last name
        4. Verify DB persistence
        5. Verify profile card display
        6. Verify navbar display
        7. Verify account menu display
        8. Navigate to other pages — verify identity persists
        9. Refresh — verify identity persists
        10. Logout and re-login — verify identity persists
        11. New browser context — verify identity persists
        """
        context = self.browser.new_context()
        page = context.new_page()

        # ── Step 1: Log in ────────────────────────────────────────
        self._login(page)

        # ── Step 2: Navigate to profile ───────────────────────────
        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        # Verify initial state — should show OldFirst OldLast
        profile_name = page.locator("[data-testid='profile-display-name']")
        self.assertIn("OldFirst", profile_name.text_content())

        # ── Step 3: Update first and last name ────────────────────
        first_name_input = page.locator("[data-testid='profile-first-name'] input")
        last_name_input = page.locator("[data-testid='profile-last-name'] input")

        first_name_input.fill("")
        first_name_input.fill("Ahmed")
        last_name_input.fill("")
        last_name_input.fill("Raza")

        # Save
        page.locator("[data-testid='profile-save']").click()
        page.wait_for_load_state("domcontentloaded")

        self._screenshot(page, "01_after_save")

        # ── Step 4: Verify database persistence ───────────────────
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Ahmed",
                         "first_name not persisted in database")
        self.assertEqual(self.user.last_name, "Raza",
                         "last_name not persisted in database")
        self.assertEqual(self.user.display_name, "Ahmed Raza",
                         "display_name property not returning updated name")
        # Username must NOT have changed
        self.assertEqual(self.user.username, "qa_test_admin",
                         "username was unexpectedly modified")

        # ── Step 5: Verify profile card display ───────────────────
        profile_name = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Ahmed Raza", profile_name.text_content(),
                      "Profile card does not show updated name")

        # ── Step 6: Verify navbar display ─────────────────────────
        navbar_name = page.locator("[data-testid='navbar-user-name']")
        self.assertIn("Ahmed Raza", navbar_name.text_content(),
                      "Navbar does not show updated name")

        # ── Step 7: Verify account menu display ───────────────────
        account_menu = page.locator("[data-testid='account-menu-user-name']")
        self.assertIn("Ahmed Raza", account_menu.text_content(),
                      "Account menu dropdown does not show updated name")

        self._screenshot(page, "02_profile_after_update")

        # ── Step 8: Navigate to other pages ───────────────────────
        # Navigate to dashboard (admin panel)
        page.goto(f"{self.live_server_url}/panel/admin/dashboard/")
        page.wait_for_load_state("domcontentloaded")

        navbar_on_dashboard = page.locator("[data-testid='navbar-user-name']")
        if navbar_on_dashboard.count() > 0:
            self.assertIn("Ahmed Raza", navbar_on_dashboard.text_content(),
                          "Navbar on dashboard does not show updated name")

        self._screenshot(page, "03_dashboard_identity")

        # Navigate to another page — session overview
        page.goto(f"{self.live_server_url}/panel/admin/session-overview/")
        page.wait_for_load_state("domcontentloaded")

        navbar_on_sessions = page.locator("[data-testid='navbar-user-name']")
        if navbar_on_sessions.count() > 0:
            self.assertIn("Ahmed Raza", navbar_on_sessions.text_content(),
                          "Navbar on session overview does not show updated name")

        self._screenshot(page, "04_session_overview_identity")

        # ── Step 9: Refresh the browser ───────────────────────────
        page.reload()
        page.wait_for_load_state("domcontentloaded")

        navbar_after_refresh = page.locator("[data-testid='navbar-user-name']")
        if navbar_after_refresh.count() > 0:
            self.assertIn("Ahmed Raza", navbar_after_refresh.text_content(),
                          "Navbar after refresh does not show updated name")

        self._screenshot(page, "05_after_refresh")

        # ── Step 10: Logout and re-login ──────────────────────────
        page.goto(f"{self.live_server_url}/accounts/logout/")
        page.wait_for_load_state("domcontentloaded")

        self._login(page)

        # Go to profile to check identity
        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        profile_after_relogin = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Ahmed Raza", profile_after_relogin.text_content(),
                      "Profile card after re-login does not show updated name")

        navbar_after_relogin = page.locator("[data-testid='navbar-user-name']")
        self.assertIn("Ahmed Raza", navbar_after_relogin.text_content(),
                      "Navbar after re-login does not show updated name")

        self._screenshot(page, "06_after_relogin")

        # ── Step 11: New browser context ──────────────────────────
        context.close()

        context2 = self.browser.new_context()
        page2 = context2.new_page()

        self._login(page2)

        page2.goto(f"{self.live_server_url}/accounts/profile/")
        page2.wait_for_load_state("domcontentloaded")

        profile_new_ctx = page2.locator("[data-testid='profile-display-name']")
        self.assertIn("Ahmed Raza", profile_new_ctx.text_content(),
                      "Profile in new browser context does not show updated name")

        navbar_new_ctx = page2.locator("[data-testid='navbar-user-name']")
        self.assertIn("Ahmed Raza", navbar_new_ctx.text_content(),
                      "Navbar in new browser context does not show updated name")

        self._screenshot(page2, "07_new_context")

        context2.close()

    def test_username_remains_unchanged_after_profile_update(self):
        """Verify that updating first/last name does not change the username."""
        context = self.browser.new_context()
        page = context.new_page()

        self._login(page)

        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        # Update name
        page.locator("[data-testid='profile-first-name'] input").fill("NewFirst")
        page.locator("[data-testid='profile-last-name'] input").fill("NewLast")
        page.locator("[data-testid='profile-save']").click()
        page.wait_for_load_state("domcontentloaded")

        # Verify username unchanged
        self.user.refresh_from_db()
        self.assertEqual(self.user.username, "qa_test_admin",
                         "Username was changed by profile update!")
        self.assertEqual(self.user.first_name, "NewFirst")
        self.assertEqual(self.user.last_name, "NewLast")

        # Verify the "System Username" field on profile still shows username
        system_username_text = page.text_content("text=System Username")
        # The username should still be visible in the account details section
        page_content = page.content()
        self.assertIn("qa_test_admin", page_content,
                       "System Username 'qa_test_admin' should still appear on profile page")

        context.close()

    def test_display_name_fallback_to_username(self):
        """When first_name and last_name are both blank, display_name falls back to username."""
        context = self.browser.new_context()
        page = context.new_page()

        # Clear the user's name
        self.user.first_name = ""
        self.user.last_name = ""
        self.user.save()

        self._login(page)

        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        # display_name should fall back to username
        profile_name = page.locator("[data-testid='profile-display-name']")
        self.assertIn("qa_test_admin", profile_name.text_content(),
                      "Display name should fall back to username when name is blank")

        navbar_name = page.locator("[data-testid='navbar-user-name']")
        self.assertIn("qa_test_admin", navbar_name.text_content(),
                      "Navbar should fall back to username when name is blank")

        context.close()


if __name__ == "__main__":
    unittest.main()
