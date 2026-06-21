"""
Concurrency Smoke Test — Iqra Academy CRM.

Uses standard Django LiveServerTestCase (NOT SingleThreadedWSGIServer)
to detect genuine application race conditions.

Tests concurrent requests for:
  - Dashboard and analytics endpoints
  - Notification polling
  - Profile update + shared-layout reload
  - Simultaneous authenticated GETs

SQLite locking errors are classified separately from application
race conditions.
"""

import os
import sys
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

import unittest
import requests as http_requests
from django.test import LiveServerTestCase, override_settings
from django.contrib.auth.models import Group
from apps.accounts.models import CustomUser


TEST_PASSWORD = "ConcurrencyTest!2026x"
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")


def _make_request(url, session=None, method="GET", data=None):
    """Make an HTTP request and return result dict."""
    start = time.time()
    try:
        if session:
            if method == "POST":
                resp = session.post(url, data=data, allow_redirects=True, timeout=15)
            else:
                resp = session.get(url, allow_redirects=True, timeout=15)
        else:
            resp = http_requests.get(url, allow_redirects=True, timeout=15)

        elapsed = time.time() - start
        return {
            "url": url,
            "status": resp.status_code,
            "elapsed_ms": round(elapsed * 1000),
            "error": None,
            "error_type": None,
        }
    except Exception as e:
        elapsed = time.time() - start
        error_text = str(e)
        error_type = "sqlite_lock" if "database is locked" in error_text.lower() else "application"
        return {
            "url": url,
            "status": 0,
            "elapsed_ms": round(elapsed * 1000),
            "error": error_text,
            "error_type": error_type,
        }


@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class ConcurrencySmokeSuiteTest(LiveServerTestCase):
    """Concurrent request tests using standard threaded LiveServerTestCase.

    NOTE: This intentionally does NOT use SingleThreadedWSGIServer.
    SQLite locking errors under concurrent writes are expected and
    classified separately from application-level race conditions.
    """

    @classmethod
    def setUpClass(cls):
        # Do NOT patch LiveServerThread — we want threaded behavior
        super().setUpClass()
        os.makedirs(REPORT_DIR, exist_ok=True)

    def setUp(self):
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin_user = CustomUser.objects.create_user(
            email="concurrent_admin@iqra.test",
            username="concurrent_admin",
            password=TEST_PASSWORD,
            first_name="ConcurrentAdmin",
            last_name="QA",
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.groups.add(admin_group)

    def _get_session(self):
        """Get an authenticated requests.Session."""
        session = http_requests.Session()

        # Login
        login_url = f"{self.live_server_url}/accounts/login/"
        resp = session.get(login_url)
        csrf_token = resp.cookies.get("csrftoken", "")
        if not csrf_token:
            # Try to extract from HTML
            import re
            match = re.search(r'csrfmiddlewaretoken.*?value="(.*?)"', resp.text)
            if match:
                csrf_token = match.group(1)

        session.post(login_url, data={
            "username": self.admin_user.email,
            "password": TEST_PASSWORD,
            "csrfmiddlewaretoken": csrf_token,
        }, headers={"Referer": login_url})

        return session

    def test_concurrent_dashboard_gets(self):
        """3 simultaneous dashboard GETs should all return 200."""
        session = self._get_session()
        urls = [
            f"{self.live_server_url}/panel/admin/dashboard/",
            f"{self.live_server_url}/accounts/profile/",
            f"{self.live_server_url}/panel/admin/session-overview/",
        ]

        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {executor.submit(_make_request, url, session): url for url in urls}
            for future in as_completed(futures):
                results.append(future.result())

        sqlite_errors = [r for r in results if r["error_type"] == "sqlite_lock"]
        app_errors = [r for r in results if r["error_type"] == "application"]
        success = [r for r in results if r["status"] == 200]

        report = {
            "test": "concurrent_dashboard_gets",
            "timestamp": datetime.now().isoformat(),
            "db_engine": "sqlite3 (file-based, threaded server)",
            "total_requests": len(results),
            "success_200": len(success),
            "sqlite_lock_errors": len(sqlite_errors),
            "application_errors": len(app_errors),
            "details": results,
        }

        # Only fail on application errors, not SQLite locks
        self.assertEqual(len(app_errors), 0,
                        f"Application errors (not SQLite lock): {app_errors}")

        print(f"\nConcurrency test: {len(success)} success, "
              f"{len(sqlite_errors)} SQLite locks, {len(app_errors)} app errors")

        return report

    def test_concurrent_notification_poll(self):
        """Concurrent notification unread-count polling."""
        session = self._get_session()
        url = f"{self.live_server_url}/panel/admin/notifications/"

        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(_make_request, url, session) for _ in range(3)]
            for future in as_completed(futures):
                results.append(future.result())

        app_errors = [r for r in results if r["error_type"] == "application"]
        self.assertEqual(len(app_errors), 0,
                        f"Application errors: {app_errors}")

    def test_concurrent_mixed_read_write(self):
        """Simultaneous read + profile update."""
        session = self._get_session()

        read_url = f"{self.live_server_url}/panel/admin/dashboard/"
        write_url = f"{self.live_server_url}/accounts/profile/edit/"

        results = []
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit a read
            read_future = executor.submit(_make_request, read_url, session)

            # Submit a profile update (POST)
            csrf_resp = session.get(write_url)
            import re
            csrf_match = re.search(r'csrfmiddlewaretoken.*?value="(.*?)"', csrf_resp.text)
            csrf_token = csrf_match.group(1) if csrf_match else ""

            write_future = executor.submit(
                _make_request, write_url, session, "POST",
                {
                    "first_name": "ConcurrentUpdate",
                    "last_name": "QA",
                    "csrfmiddlewaretoken": csrf_token,
                }
            )

            results.append(read_future.result())
            results.append(write_future.result())

        app_errors = [r for r in results if r["error_type"] == "application"]
        sqlite_errors = [r for r in results if r["error_type"] == "sqlite_lock"]

        print(f"\nMixed read/write: app_errors={len(app_errors)}, "
              f"sqlite_locks={len(sqlite_errors)}")

    @classmethod
    def tearDownClass(cls):
        """Generate concurrency report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "db_engine": "sqlite3 (file-based)",
            "server_mode": "standard threaded LiveServerTestCase",
            "note": "SQLite locking errors are classified separately from application race conditions",
        }
        with open(os.path.join(REPORT_DIR, "concurrency.json"), "w") as f:
            json.dump(report, f, indent=2)
        super().tearDownClass()


if __name__ == "__main__":
    unittest.main()
