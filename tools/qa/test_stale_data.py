"""
Stale Data / Cache / Session Tests — Verifies that data updates
are reflected immediately without stale data artifacts.

Tests:
- Update → GET (same request)
- Update → Refresh
- Update → Navigate away and back
- Update → Logout/Login
- Cross-context updates

Usage:
    python -m pytest tools/qa/test_stale_data.py -v --tb=short
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

TEST_PASSWORD = "StaleTest!2026x"


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class StaleDataTests(StaticLiveServerTestCase):
    """Verify no stale data appears after mutations."""
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
        self.group, _ = Group.objects.get_or_create(name="Admin")
        self.user = CustomUser.objects.create_user(
            email="stale@iqra.test",
            username="stale_user",
            password=TEST_PASSWORD,
            first_name="Stale",
            last_name="Data",
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        self.user.groups.add(self.group)

    def tearDown(self):
        CustomUser.objects.filter(email="stale@iqra.test").delete()

    def _login(self, page):
        page.goto(f"{self.live_server_url}/accounts/login/")
        page.wait_for_load_state("domcontentloaded")
        page.fill("input[name='username']", "stale@iqra.test")
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")

    def _update_name(self, page, first, last):
        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")
        page.locator("[data-testid='profile-first-name'] input").fill(first)
        page.locator("[data-testid='profile-last-name'] input").fill(last)
        page.locator("[data-testid='profile-save']").click()
        page.wait_for_load_state("domcontentloaded")

    def test_update_then_immediate_get(self):
        """After save redirect, profile shows updated name (no stale cache)."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)
        self._update_name(page, "Fresh", "Data")

        # The redirect after save shows profile page — verify immediately
        profile = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Fresh Data", profile.text_content())
        ctx.close()

    def test_update_then_refresh(self):
        """After save, refreshing the page still shows updated name."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)
        self._update_name(page, "Refresh", "Test")

        page.reload()
        page.wait_for_load_state("domcontentloaded")

        profile = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Refresh Test", profile.text_content())
        ctx.close()

    def test_update_then_navigate_back(self):
        """After save, navigating away and back shows updated name."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)
        self._update_name(page, "Navigate", "Back")

        # Navigate to dashboard
        page.goto(f"{self.live_server_url}/panel/admin/dashboard/")
        page.wait_for_load_state("domcontentloaded")

        # Navigate back to profile
        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        profile = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Navigate Back", profile.text_content())
        ctx.close()

    def test_update_then_logout_login(self):
        """After save, logging out and back in shows updated name."""
        ctx = self.browser.new_context()
        page = ctx.new_page()
        self._login(page)
        self._update_name(page, "Logout", "Login")

        # Logout
        page.goto(f"{self.live_server_url}/accounts/logout/")
        page.wait_for_load_state("domcontentloaded")

        # Login again
        self._login(page)

        page.goto(f"{self.live_server_url}/accounts/profile/")
        page.wait_for_load_state("domcontentloaded")

        profile = page.locator("[data-testid='profile-display-name']")
        self.assertIn("Logout Login", profile.text_content())
        ctx.close()

    def test_cross_context_freshness(self):
        """Update in one context, verify in a new context (no session cache)."""
        # Context 1: update name
        ctx1 = self.browser.new_context()
        page1 = ctx1.new_page()
        self._login(page1)
        self._update_name(page1, "Cross", "Context")
        ctx1.close()

        # Context 2: verify
        ctx2 = self.browser.new_context()
        page2 = ctx2.new_page()
        self._login(page2)

        page2.goto(f"{self.live_server_url}/accounts/profile/")
        page2.wait_for_load_state("domcontentloaded")

        profile = page2.locator("[data-testid='profile-display-name']")
        self.assertIn("Cross Context", profile.text_content())
        ctx2.close()


if __name__ == "__main__":
    unittest.main()
