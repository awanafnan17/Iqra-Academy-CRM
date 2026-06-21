"""
Browser Crawler — Authenticated page crawler for Iqra Academy CRM.

Two modes:
  - DISCOVERY: Continues after failures, records all findings.
  - ENFORCEMENT: Fails the test when unexpected 500/404/broken reverse found.

Usage:
    # Discovery mode (default)
    python -m pytest tools/qa/test_browser_crawl.py -v -s

    # Enforcement mode
    QA_ENFORCE=1 python -m pytest tools/qa/test_browser_crawl.py -v -s
"""

import os
import sys
import json
import re
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

import unittest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import Group
from django.test import override_settings
from apps.accounts.models import CustomUser

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


TEST_PASSWORD = "CrawlTest!2026x"
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "screenshots", "crawl")

# Enforcement mode flag
ENFORCE_MODE = os.environ.get("QA_ENFORCE", "0") == "1"

# URLs to skip (destructive or external)
SKIP_PATTERNS = [
    r"^/admin/",           # Django admin
    r"/logout",            # Would terminate session
    r"/delete/",           # Destructive
    r"/toggle-activation/",
    r"/toggle-lock/",
    r"/reset-password/",
    r"/approve/",
    r"/reject/",
    r"/convert/",
    r"/publish/",
    r"/review/",
    r"/toggle-status/",
    r"\.pdf$",
    r"\.csv$",
    r"/export/",
    r"/api/",
    r"/create-login/",
    r"/mark-read/",
    r"/installments/\d+/pay/",
]


def _classify_error(url_path, status, source_url, role):
    """Return (severity, category) for a failed URL."""
    if status == 500:
        return ("Critical", "server_error")
    elif status == 404:
        return ("High", "broken_link")
    elif status == 403:
        return ("Observation", "permission_denied")
    elif status == 302:
        return ("Low", "redirect")
    return ("Medium", "unknown_error")


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class BrowserCrawlTest(StaticLiveServerTestCase):
    """Crawl all accessible pages for each role and record findings."""
    host = "127.0.0.1"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(REPORT_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        super().tearDownClass()

    def setUp(self):
        """Create test users for every role."""
        from apps.core.permission_service import seed_default_permissions
        seed_default_permissions()
        self.roles = {}
        role_configs = [
            ("Admin",      True,  True),
            ("Principal",  False, False),
            ("Accountant", False, False),
            ("Registrar",  False, False),
            ("Teacher",    False, False),
            ("Student",    False, False),
            ("Guardian",   False, False),
        ]
        for role_name, is_staff, is_superuser in role_configs:
            group, _ = Group.objects.get_or_create(name=role_name)
            user = CustomUser.objects.create_user(
                email=f"crawl_{role_name.lower()}@iqra.test",
                username=f"crawl_{role_name.lower()}",
                password=TEST_PASSWORD,
                first_name=f"Test{role_name}",
                last_name="QA",
                status="Active",
                is_staff=is_staff,
                is_superuser=is_superuser,
            )
            user.groups.add(group)
            self.roles[role_name] = user

        # Create student/guardian records for portal access
        self._setup_portal_users()

    def _setup_portal_users(self):
        """Create Student and Guardian records for portal crawling."""
        try:
            from apps.students.models import Student, Guardian
            student_user = self.roles.get("Student")
            guardian_user = self.roles.get("Guardian")

            if student_user:
                self._student = Student.objects.create(
                    full_name="TestStudent QA",
                    email="student_portal@iqra.test",
                    portal_user=student_user,
                    status="Active",
                )
            if guardian_user and hasattr(self, '_student'):
                Guardian.objects.create(
                    student=self._student,
                    full_name="TestGuardian QA",
                    relationship="Father",
                    phone="03001234567",
                    portal_user=guardian_user,
                )
        except Exception:
            pass  # Portal tests may be limited

    def tearDown(self):
        CustomUser.objects.filter(email__endswith="@iqra.test").delete()

    def _login(self, page, user):
        """Log in via the browser."""
        page.goto(f"{self.live_server_url}/accounts/login/")
        page.wait_for_load_state("domcontentloaded")
        page.fill("input[name='username']", user.email)
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_load_state("domcontentloaded")

    def _should_skip(self, path):
        for pattern in SKIP_PATTERNS:
            if re.search(pattern, path):
                return True
        return False

    def _is_role_inaccessible_url(self, role_name, url_path):
        """Returns True if the URL path points to a panel that this role cannot access."""
        url_path = url_path.lower()
        if role_name == "Admin":
            return False
        elif role_name == "Principal":
            # Principal only has access to /panel/admin/, not other panels or student portal
            if "/panel/accounts/" in url_path or "/panel/registrar/" in url_path or "/panel/teacher/" in url_path or "/portal/" in url_path:
                return True
        elif role_name == "Accountant":
            if "/panel/admin/" in url_path or "/panel/registrar/" in url_path or "/panel/teacher/" in url_path or "/portal/" in url_path:
                return True
        elif role_name == "Registrar":
            if "/panel/admin/" in url_path or "/panel/accounts/" in url_path or "/panel/teacher/" in url_path or "/portal/" in url_path:
                return True
        elif role_name == "Teacher":
            if "/panel/admin/" in url_path or "/panel/accounts/" in url_path or "/panel/registrar/" in url_path or "/portal/" in url_path:
                return True
        elif role_name in ("Student", "Guardian"):
            if "/panel/" in url_path:
                return True
        return False

    def _extract_links(self, page):
        """Extract all internal links from the current page."""
        base_url = self.live_server_url
        links = {}
        anchors = page.query_selector_all("a[href]")
        for anchor in anchors:
            href = anchor.get_attribute("href")
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            source = "navigation"
            # Determine link source
            parent = anchor
            for _ in range(5):
                parent_el = parent.evaluate_handle("el => el.parentElement")
                if not parent_el:
                    break
                tag = parent_el.evaluate("el => el.tagName || ''")
                classes = parent_el.evaluate("el => el.className || ''")
                if "sidebar" in classes.lower():
                    source = "sidebar"
                    break
                elif "navbar" in classes.lower() or "nav" in tag.lower():
                    source = "navbar"
                    break
                parent = parent_el

            if href.startswith("http"):
                parsed = urlparse(href)
                base_parsed = urlparse(base_url)
                if parsed.netloc != base_parsed.netloc:
                    continue
                path = parsed.path
            elif href.startswith("/"):
                path = href
            else:
                current = urlparse(page.url).path
                path = urljoin(current, href)

            if path not in links:
                links[path] = source
        return links

    def _crawl_as_role(self, role_name, user, start_urls):
        """Crawl accessible pages for a given role."""
        context = self.browser.new_context()
        page = context.new_page()

        findings = {
            "role": role_name,
            "mode": "enforcement" if ENFORCE_MODE else "discovery",
            "timestamp": datetime.now().isoformat(),
            "pages_visited": [],
            "errors_500": [],
            "errors_404": [],
            "errors_403": [],
            "console_errors": [],
            "redirect_loops": [],
            "slow_pages": [],
            "empty_pages": [],
            "redirects": [],
            "all_errors": [],  # Unified error list with full detail
        }

        console_errors = []
        page.on("console", lambda msg: console_errors.append({
            "type": msg.type,
            "text": msg.text,
            "url": page.url,
        }) if msg.type in ("error", "warning") else None)

        self._login(page, user)

        visited = set()
        # Track source page for each URL
        to_visit = {url: ("seed", "seed") for url in start_urls}
        max_pages = 60

        while to_visit and len(visited) < max_pages:
            url_path = next(iter(to_visit))
            source_url, link_source = to_visit.pop(url_path)

            if url_path in visited or self._should_skip(url_path):
                continue

            visited.add(url_path)
            full_url = f"{self.live_server_url}{url_path}"

            try:
                start_time = time.time()
                response = page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                load_time = time.time() - start_time

                status = response.status if response else 0
                final_url = urlparse(page.url).path

                page_info = {
                    "url": url_path,
                    "status": status,
                    "load_time_ms": round(load_time * 1000),
                    "final_url": final_url,
                    "title": page.title(),
                    "source_url": source_url,
                    "link_source": link_source,
                }
                findings["pages_visited"].append(page_info)

                # Classify errors
                if status == 500:
                    error_detail = {
                        "url": url_path,
                        "source_url": source_url,
                        "link_source": link_source,
                        "status": status,
                        "expected_status": 200,
                        "title": page.title(),
                        "role": role_name,
                        "severity": "Critical",
                        "category": "server_error",
                    }
                    # Try to capture error text
                    try:
                        error_text = page.text_content("body") or ""
                        error_detail["error_text"] = error_text[:500]
                    except Exception:
                        error_detail["error_text"] = ""

                    findings["errors_500"].append(error_detail)
                    findings["all_errors"].append(error_detail)

                    screenshot_path = os.path.join(
                        SCREENSHOT_DIR,
                        f"{role_name}_500_{url_path.replace('/', '_')}.png"
                    )
                    try:
                        page.screenshot(path=screenshot_path)
                    except Exception:
                        pass

                elif status == 404:
                    error_detail = {
                        "url": url_path,
                        "source_url": source_url,
                        "link_source": link_source,
                        "status": status,
                        "expected_status": 200,
                        "title": page.title(),
                        "role": role_name,
                        "severity": "High",
                        "category": "broken_link",
                    }
                    findings["errors_404"].append(error_detail)
                    findings["all_errors"].append(error_detail)

                elif status == 403:
                    error_detail = {
                        "url": url_path,
                        "source_url": source_url,
                        "link_source": link_source,
                        "status": status,
                        "expected_status": 200,
                        "role": role_name,
                        "severity": "High",
                        "category": "permission_denied",
                    }
                    findings["errors_403"].append(error_detail)
                    findings["all_errors"].append(error_detail)

                # Redirect loop detection
                if final_url != url_path and status < 400:
                    findings["redirects"].append({
                        "from": url_path,
                        "to": final_url,
                        "status": status,
                    })
                    # Check for redirect loops
                    if final_url == url_path or url_path in final_url:
                        findings["redirect_loops"].append({
                            "url": url_path,
                            "final_url": final_url,
                        })

                # Slow pages (> 3s)
                if load_time > 3.0:
                    findings["slow_pages"].append({
                        "url": url_path,
                        "load_time_ms": round(load_time * 1000),
                    })

                # Empty body
                body_text = page.text_content("body") or ""
                if len(body_text.strip()) < 50 and status == 200:
                    findings["empty_pages"].append({
                        "url": url_path,
                        "body_length": len(body_text.strip()),
                    })

                # Discover links from 200 pages
                if status == 200:
                    new_links = self._extract_links(page)
                    for link_path, source_type in new_links.items():
                        if self._is_role_inaccessible_url(role_name, link_path):
                            error_detail = {
                                "url": link_path,
                                "source_url": url_path,
                                "link_source": source_type,
                                "status": 403,
                                "expected_status": 200,
                                "title": "Role-Inaccessible Link Leakage",
                                "role": role_name,
                                "severity": "High",
                                "category": "cross_panel_leakage",
                                "error_text": f"Role {role_name} found link to role-inaccessible panel: {link_path}"
                            }
                            findings["errors_403"].append(error_detail)
                            findings["all_errors"].append(error_detail)
                        elif link_path not in visited and not self._should_skip(link_path):
                            to_visit[link_path] = (url_path, source_type)

            except Exception as e:
                findings["all_errors"].append({
                    "url": url_path,
                    "source_url": source_url,
                    "link_source": link_source,
                    "status": 0,
                    "expected_status": 200,
                    "error": str(e),
                    "role": role_name,
                    "severity": "Critical",
                    "category": "exception",
                })

        # Collect console errors
        findings["console_errors"] = [
            e for e in console_errors
            if e["type"] == "error"
        ]

        context.close()
        return findings

    def _print_summary(self, findings):
        """Print crawl summary."""
        role = findings["role"]
        mode = findings["mode"]
        visited = len(findings["pages_visited"])
        err500 = len(findings["errors_500"])
        err404 = len(findings["errors_404"])
        err403 = len(findings["errors_403"])
        console = len(findings["console_errors"])
        slow = len(findings["slow_pages"])

        print(f"\n{'='*60}")
        print(f"  {role} Crawl ({mode.upper()} mode)")
        print(f"{'='*60}")
        print(f"  Pages visited: {visited}")
        print(f"  500 errors:    {err500}")
        print(f"  404 errors:    {err404}")
        print(f"  403 denied:    {err403}")
        print(f"  Console errs:  {console}")
        print(f"  Slow pages:    {slow}")

        if findings["errors_500"]:
            print(f"\n  [CRITICAL] Server Errors:")
            for e in findings["errors_500"]:
                print(f"    500 {e['url']} (from: {e['source_url']}, via: {e['link_source']})")
        if findings["errors_404"]:
            print(f"\n  [HIGH] Broken Links:")
            for e in findings["errors_404"]:
                print(f"    404 {e['url']} (from: {e['source_url']}, via: {e['link_source']})")

    def _enforce_or_report(self, findings, report_filename):
        """In enforcement mode, fail if unexpected errors found. In discovery, just report."""
        with open(os.path.join(REPORT_DIR, report_filename), "w") as f:
            json.dump(findings, f, indent=2, default=str)

        self._print_summary(findings)

        if ENFORCE_MODE:
            errors = findings["errors_500"] + findings["errors_404"] + findings["errors_403"]
            if errors:
                msg_lines = [
                    f"ENFORCEMENT FAILURE: {len(errors)} errors found for {findings['role']}:"
                ]
                for e in errors:
                    msg_lines.append(
                        f"  {e['status']} {e['url']} (from: {e['source_url']}, via: {e['link_source']})"
                    )
                self.fail("\n".join(msg_lines))

    # ----- Role-specific tests -----

    def test_crawl_admin(self):
        """Crawl as Admin and verify zero errors in enforcement mode."""
        start_urls = [
            "/panel/admin/dashboard/",
            "/accounts/profile/",
            "/panel/admin/manage-students/",
            "/panel/admin/session-overview/",
            "/panel/admin/manage-faculty/",
            "/panel/admin/admissions/",
            "/panel/admin/finance/payments/",
            "/panel/admin/exams/",
            "/panel/admin/attendance/",
            "/panel/admin/notifications/",
            "/panel/admin/notifications/email-logs/",
            "/panel/admin/reports/",
            "/panel/admin/timetable/",
            "/panel/admin/timetable-overview/",
            "/panel/admin/success/",
            "/panel/admin/permissions/",
            "/panel/admin/analytics/",
            "/panel/admin/documents/",
            "/panel/admin/automation/alerts/",
            "/panel/admin/automation/jobs/",
            "/panel/admin/users/",
            "/panel/admin/audit/",
        ]
        findings = self._crawl_as_role("Admin", self.roles["Admin"], start_urls)
        self._enforce_or_report(findings, "crawl_admin.json")

    def test_crawl_principal(self):
        """Crawl as Principal."""
        print("PRINCIPAL GROUPS:", list(self.roles["Principal"].groups.values_list("name", flat=True)))
        start_urls = [
            "/panel/admin/dashboard/",
            "/accounts/profile/",
            "/panel/admin/session-overview/",
            "/panel/admin/manage-students/",
            "/panel/admin/manage-faculty/",
            "/panel/admin/timetable-overview/",
            "/panel/admin/exam-overview/",
        ]
        findings = self._crawl_as_role("Principal", self.roles["Principal"], start_urls)
        self._enforce_or_report(findings, "crawl_principal.json")

    def test_crawl_accountant(self):
        """Crawl as Accountant."""
        start_urls = [
            "/panel/accounts/dashboard/",
            "/accounts/profile/",
            "/panel/accounts/payments/",
            "/panel/accounts/installments/",
            "/panel/accounts/overdue/",
            "/panel/accounts/refunds/",
            "/panel/accounts/pending-dues/",
            "/panel/accounts/reports/",
        ]
        findings = self._crawl_as_role("Accountant", self.roles["Accountant"], start_urls)
        self._enforce_or_report(findings, "crawl_accountant.json")

    def test_crawl_registrar(self):
        """Crawl as Registrar."""
        start_urls = [
            "/panel/registrar/dashboard/",
            "/accounts/profile/",
            "/panel/registrar/leads/",
        ]
        findings = self._crawl_as_role("Registrar", self.roles["Registrar"], start_urls)
        self._enforce_or_report(findings, "crawl_registrar.json")

    def test_crawl_teacher(self):
        """Crawl as Teacher."""
        start_urls = [
            "/panel/teacher/dashboard/",
            "/accounts/profile/",
            "/panel/teacher/sessions/",
            "/panel/teacher/exams/",
            "/panel/teacher/my-timetable/",
            "/panel/teacher/notifications/",
        ]
        findings = self._crawl_as_role("Teacher", self.roles["Teacher"], start_urls)
        self._enforce_or_report(findings, "crawl_teacher.json")

    def test_crawl_student(self):
        """Crawl as Student (portal)."""
        start_urls = [
            "/portal/student/dashboard/",
            "/accounts/profile/",
        ]
        findings = self._crawl_as_role("Student", self.roles["Student"], start_urls)
        self._enforce_or_report(findings, "crawl_student.json")

    def test_crawl_guardian(self):
        """Crawl as Guardian (portal)."""
        start_urls = [
            "/portal/guardian/dashboard/",
            "/accounts/profile/",
        ]
        findings = self._crawl_as_role("Guardian", self.roles["Guardian"], start_urls)
        self._enforce_or_report(findings, "crawl_guardian.json")

    def test_crawl_anonymous(self):
        """Crawl as anonymous user (no login)."""
        context = self.browser.new_context()
        page = context.new_page()

        findings = {
            "role": "Anonymous",
            "mode": "enforcement" if ENFORCE_MODE else "discovery",
            "timestamp": datetime.now().isoformat(),
            "pages_visited": [],
            "errors_500": [],
            "errors_404": [],
            "errors_403": [],
            "console_errors": [],
            "redirect_loops": [],
            "slow_pages": [],
            "empty_pages": [],
            "redirects": [],
            "all_errors": [],
        }

        anon_urls = [
            "/",
            "/accounts/login/",
            "/accounts/register/",
        ]

        for url_path in anon_urls:
            full_url = f"{self.live_server_url}{url_path}"
            try:
                response = page.goto(full_url, wait_until="domcontentloaded", timeout=10000)
                status = response.status if response else 0
                final_url = urlparse(page.url).path

                findings["pages_visited"].append({
                    "url": url_path,
                    "status": status,
                    "final_url": final_url,
                    "title": page.title(),
                    "source_url": "seed",
                    "link_source": "seed",
                })

                if status == 500:
                    findings["errors_500"].append({
                        "url": url_path,
                        "status": 500,
                        "expected_status": 200,
                        "source_url": "seed",
                        "link_source": "seed",
                        "role": "Anonymous",
                        "severity": "Critical",
                        "category": "server_error",
                    })
            except Exception as e:
                findings["all_errors"].append({
                    "url": url_path,
                    "error": str(e),
                    "role": "Anonymous",
                })

        context.close()
        self._enforce_or_report(findings, "crawl_anonymous.json")

    def test_z_crawl_json_gate(self):
        """Gate that reads crawl JSON files and fails on unresolved findings."""
        errors = []
        for filename in os.listdir(REPORT_DIR):
            if filename.startswith("crawl_") and filename.endswith(".json"):
                try:
                    with open(os.path.join(REPORT_DIR, filename)) as f:
                        data = json.load(f)
                    role = data.get("role", filename)
                    for key in ["errors_500", "errors_404", "errors_403"]:
                        for err in data.get(key, []):
                            errors.append(f"{role} [{key}]: {err.get('status')} {err.get('url')} (from: {err.get('source_url')})")
                except Exception as e:
                    pass
        if errors:
            self.fail("Unresolved findings in crawl reports:\n" + "\n".join(errors))

    def test_zz_no_unresolved_defects_in_report(self):
        """Fail if any confirmed defect in defect_report.md is unresolved or status is not FIXED."""
        report_path = r"C:\Users\Afnan Awan\.gemini\antigravity-ide\brain\6c5a85d5-8ce7-4a1c-9095-d6be8818e75a\defect_report.md"
        if not os.path.exists(report_path):
            return  # Skip if not found
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Simple parser to find ### DEF-... and check status
        import re
        defects = re.split(r"###\s+(DEF-[A-Z0-9\-]+)", content)
        unresolved = []
        for i in range(1, len(defects), 2):
            def_id = defects[i]
            def_body = defects[i+1] if i+1 < len(defects) else ""
            status_match = re.search(r"\-\s*(?:\*\*)?[Ss]tatus(?:\*\*)?\s*:\s*([^\n\r]+)", def_body)
            if status_match:
                status = status_match.group(1).strip()
                if "FIXED" not in status.upper():
                    unresolved.append(f"{def_id}: status is {status}")
            else:
                unresolved.append(f"{def_id}: status not documented")
        if unresolved:
            self.fail("Unresolved defects in defect_report.md:\n" + "\n".join(unresolved))


if __name__ == "__main__":
    unittest.main()
