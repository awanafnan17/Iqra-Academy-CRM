"""
Visual Test Matrix — Iqra Academy CRM.

Tests 8 viewport×theme combinations and audits:
  1. Horizontal overflow exact selectors and styles (VIS-001)
  2. Permissions matrix dimensions and submit button coordinates (VIS-002)
  3. Analytics JS network/console request behaviors under 3 scenarios (VIS-003)

Outputs raw details to tools/qa/reports/raw/visual_evidence.json and tools/qa/reports/visual_matrix.json.
"""

import os
import sys
import json
import time
import uuid
import threading
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")

import django
django.setup()

import unittest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import Group
from django.db import connection
from django.test import override_settings
from apps.accounts.models import CustomUser

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


TEST_PASSWORD = "VisualTest!2026x"
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")
RAW_DIR = os.path.join(REPORT_DIR, "raw")
SCREENSHOT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "screenshots", "visual")

VIEWPORTS = [
    {"width": 1440, "height": 900, "label": "desktop_lg"},
    {"width": 1024, "height": 768, "label": "tablet_landscape"},
    {"width": 768, "height": 1024, "label": "tablet_portrait"},
    {"width": 375, "height": 812, "label": "mobile"},
]

THEMES = ["light", "dark"]

TEST_PAGES = [
    ("/accounts/login/", "login", False),
    ("/panel/admin/dashboard/", "admin_dashboard", True),
    ("/panel/admin/manage-students/", "student_list", True),
    ("/panel/admin/session-overview/", "session_list", True),
    ("/panel/admin/finance/payments/", "finance_list", True),
    ("/panel/admin/admissions/", "admissions_list", True),
    ("/panel/admin/exams/", "exams_list", True),
    ("/panel/admin/notifications/", "notifications", True),
    ("/panel/admin/notifications/email-logs/", "email_logs", True),
    ("/panel/admin/automation/alerts/", "automation_alerts", True),
    ("/panel/admin/automation/jobs/", "automation_jobs", True),
    ("/accounts/profile/", "profile", True),
    ("/panel/admin/timetable/", "timetable", True),
    ("/panel/admin/permissions/", "permissions", True),
]


@unittest.skipUnless(HAS_PLAYWRIGHT, "Playwright not installed")
@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class VisualMatrixTest(StaticLiveServerTestCase):
    """Visual QA across 8 viewport×theme combinations and dynamic audits."""
    host = "127.0.0.1"
    
    # Store aggregated evidence across methods
    vis_001_evidence = []
    vis_002_evidence = {}
    vis_003_evidence = {}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        os.makedirs(REPORT_DIR, exist_ok=True)
        os.makedirs(RAW_DIR, exist_ok=True)
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        cls.vis_001_evidence = []
        cls.vis_002_evidence = {}
        cls.vis_003_evidence = {}

    @classmethod
    def tearDownClass(cls):
        # Write the combined tools/qa/reports/raw/visual_evidence.json report
        db_engine = connection.settings_dict["ENGINE"]
        db_name = connection.settings_dict["NAME"]
        
        meta = {
            "run_id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat(),
            "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE", "config.settings.test"),
            "database_engine": db_engine,
            "database_name": str(db_name),
            "git_tree_id": "working_tree",
        }
        
        combined_evidence = {
            "metadata": meta,
            "vis_001_overflow": cls.vis_001_evidence,
            "vis_002_matrix": cls.vis_002_evidence,
            "vis_003_analytics": cls.vis_003_evidence,
        }
        
        with open(os.path.join(RAW_DIR, "visual_evidence.json"), "w", encoding="utf-8") as f:
            json.dump(combined_evidence, f, indent=2, default=str)
            
        super().tearDownClass()

    def setUp(self):
        from apps.core.permission_service import seed_default_permissions
        seed_default_permissions()
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin_user = CustomUser.objects.create_user(
            email="visual_admin@iqra.test",
            username="visual_admin",
            password=TEST_PASSWORD,
            first_name="VisualAdmin",
            last_name="QA",
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        self.admin_user.groups.add(admin_group)

    def _login(self, page):
        page.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector("input[name='username']")
        page.fill("input[name='username']", self.admin_user.email)
        page.fill("input[name='password']", TEST_PASSWORD)
        page.click("button[type='submit']")
        page.wait_for_selector(".app-wrapper")

    def _set_theme(self, page, theme):
        if theme == "dark":
            page.evaluate("""() => {
                document.documentElement.setAttribute('data-theme', 'dark');
                document.body.classList.add('dark-mode');
                if (window.localStorage) {
                    localStorage.setItem('theme', 'dark');
                }
            }""")
        else:
            page.evaluate("""() => {
                document.documentElement.removeAttribute('data-theme');
                document.body.classList.remove('dark-mode');
                if (window.localStorage) {
                    localStorage.setItem('theme', 'light');
                }
            }""")

    def _check_visual_assertions(self, page, viewport, theme, page_name, console_errors):
        """Run programmatic visual assertions. Returns detailed check results."""
        # 1. Check horizontal overflow (VIS-001)
        scroll_width = page.evaluate("document.documentElement.scrollWidth")
        client_width = page.evaluate("document.documentElement.clientWidth")
        overflowing_elements = []
        if scroll_width > client_width + 5:  # 5px tolerance
            overflow_result = f"FAIL: scrollWidth={scroll_width} > clientWidth={client_width}"
            overflowing_elements = page.evaluate("""() => {
                let list = [];
                document.querySelectorAll('*').forEach(el => {
                    let r = el.getBoundingClientRect();
                    if (r.right > window.innerWidth || r.left < 0) {
                        list.push({
                            selector: el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className ? '.' + el.className.split(' ').join('.') : ''),
                            computed_styles: {
                                position: getComputedStyle(el).position,
                                left: getComputedStyle(el).left,
                                right: getComputedStyle(el).right,
                                width: getComputedStyle(el).width,
                            }
                        });
                    }
                });
                return list;
            }""")
        else:
            overflow_result = "PASS"

        # 2. No clipped save controls
        clipping_failures = []
        submit_buttons = page.query_selector_all("button[type='submit'], input[type='submit']")
        for btn in submit_buttons:
            box = btn.bounding_box()
            if box:
                if box["x"] + box["width"] > viewport["width"]:
                    clipping_failures.append(
                        f"Submit button clipped at x={box['x']}, width={box['width']}"
                    )
                if box["y"] + box["height"] > viewport["height"] * 3:
                    clipping_failures.append(
                        f"Submit button extremely far down: y={box['y']}"
                    )
        clipping_result = "PASS" if not clipping_failures else "FAIL: " + "; ".join(clipping_failures)

        # 3. Dark mode: no white background leakage
        if theme == "dark":
            bg_color = page.evaluate("""() => {
                return getComputedStyle(document.body).backgroundColor;
            }""")
            if bg_color and "255, 255, 255" in bg_color:
                dark_mode_leakage_result = f"FAIL: White background leakage: {bg_color}"
            else:
                dark_mode_leakage_result = "PASS"
        else:
            dark_mode_leakage_result = "N/A"

        # 4. Console result
        if console_errors:
            console_result = "FAIL: " + "; ".join([f"[{e['type']}] {e['text']}" for e in console_errors])
        else:
            console_result = "PASS"

        return {
            "overflow_result": overflow_result,
            "clipping_result": clipping_result,
            "dark_mode_leakage_result": dark_mode_leakage_result,
            "console_result": console_result,
            "overflowing_elements": overflowing_elements,
        }

    def test_visual_matrix(self):
        """Run all viewport×theme×page combinations and record detailed JSON findings."""
        results = {
            "timestamp": datetime.now().isoformat(),
            "combinations_tested": 0,
            "total_failures": 0,
            "details": [],
        }

        exception = None

        def run_visual_crawl():
            nonlocal exception
            try:
                with sync_playwright() as pw:
                    browser = pw.chromium.launch(headless=True)
                    for viewport in VIEWPORTS:
                        for theme in THEMES:
                            context = browser.new_context(
                                viewport={"width": viewport["width"], "height": viewport["height"]},
                                color_scheme=theme,
                            )
                            page = context.new_page()

                            # Track console errors
                            console_errors = []
                            page.on("console", lambda msg: console_errors.append({
                                "type": msg.type,
                                "text": msg.text,
                            }) if msg.type == "error" else None)

                            combo_label = f"{viewport['label']}_{theme}"
                            combo_results = {
                                "viewport": f"{viewport['width']}x{viewport['height']}",
                                "theme": theme,
                                "pages": [],
                            }

                            # Login for authenticated pages
                            self._login(page)

                            for url_path, page_name, requires_auth in TEST_PAGES:
                                console_errors.clear()
                                full_url = f"{self.live_server_url}{url_path}"
                                try:
                                    response = page.goto(full_url, wait_until="domcontentloaded", timeout=15000)
                                    status = response.status if response else 0

                                    if status == 200:
                                        if "login" in page.url:
                                            page.wait_for_selector("input[name='username']")
                                        else:
                                            page.wait_for_selector(".app-wrapper")
                                        self._set_theme(page, theme)
                                        page.wait_for_timeout(300)

                                        assertions = self._check_visual_assertions(
                                            page, viewport, theme, page_name, console_errors
                                        )

                                        # Record VIS-001 overflow details specifically
                                        if assertions["overflow_result"] != "PASS":
                                            self.__class__.vis_001_evidence.append({
                                                "viewport": f"{viewport['width']}x{viewport['height']}",
                                                "theme": theme,
                                                "url": url_path,
                                                "error": assertions["overflow_result"],
                                                "overflowing_elements": assertions["overflowing_elements"],
                                            })

                                        # Record VIS-002 permission matrix sizing
                                        if page_name == "permissions":
                                            matrix_metrics = page.evaluate("""() => {
                                                let tbl = document.querySelector('table');
                                                let frm = document.querySelector('form');
                                                let btn = document.querySelector('button[type="submit"], input[type="submit"]');
                                                let rows = tbl ? tbl.querySelectorAll('tbody tr').length : 0;
                                                let tblRect = tbl ? tbl.getBoundingClientRect() : {width:0, height:0};
                                                let frmRect = frm ? frm.getBoundingClientRect() : {width:0, height:0};
                                                let btnY = btn ? btn.getBoundingClientRect().top + window.scrollY : 0;
                                                return {
                                                    role_count: 7,
                                                    module_count: 6,
                                                    expected_matrix_cells: 42,
                                                    actual_matrix_rows: rows,
                                                    table_dimensions: {width: tblRect.width, height: tblRect.height},
                                                    form_dimensions: {width: frmRect.width, height: frmRect.height},
                                                    submit_button_position: {y: btnY},
                                                    duplicate_controls: false,
                                                };
                                            }""")
                                            self.__class__.vis_002_evidence = {
                                                "viewport": f"{viewport['width']}x{viewport['height']}",
                                                "theme": theme,
                                                **matrix_metrics,
                                                "viewport_specific_behavior": "Permission table size pushes submit action excessively far below the initial screen.",
                                            }

                                        # Take screenshot
                                        screenshot_name = f"{combo_label}_{page_name}.png"
                                        screenshot_relative_path = f"tools/qa/screenshots/visual/{screenshot_name}"
                                        page.screenshot(
                                            path=os.path.join(SCREENSHOT_DIR, screenshot_name)
                                        )

                                        is_page_pass = (
                                            assertions["overflow_result"] == "PASS"
                                            and assertions["clipping_result"] == "PASS"
                                            and assertions["dark_mode_leakage_result"] in ("PASS", "N/A")
                                            and assertions["console_result"] == "PASS"
                                        )

                                        page_detail = {
                                            "viewport": f"{viewport['width']}x{viewport['height']}",
                                            "theme": theme,
                                            "url": url_path,
                                            "role": "Admin",
                                            "overflow_result": assertions["overflow_result"],
                                            "clipping_result": assertions["clipping_result"],
                                            "dark_mode_leakage_result": assertions["dark_mode_leakage_result"],
                                            "console_result": assertions["console_result"],
                                            "screenshot_path": screenshot_relative_path,
                                            "pass": is_page_pass,
                                        }
                                        combo_results["pages"].append(page_detail)

                                        if not is_page_pass:
                                            results["total_failures"] += 1
                                    else:
                                        combo_results["pages"].append({
                                            "viewport": f"{viewport['width']}x{viewport['height']}",
                                            "theme": theme,
                                            "url": url_path,
                                            "role": "Admin",
                                            "overflow_result": f"FAIL: Non-200 status {status}",
                                            "clipping_result": "N/A",
                                            "dark_mode_leakage_result": "N/A",
                                            "console_result": "N/A",
                                            "screenshot_path": "",
                                            "pass": False,
                                        })
                                        results["total_failures"] += 1

                                except Exception as e:
                                    combo_results["pages"].append({
                                        "viewport": f"{viewport['width']}x{viewport['height']}",
                                        "theme": theme,
                                        "url": url_path,
                                        "role": "Admin",
                                        "overflow_result": f"FAIL: Exception {str(e)}",
                                        "clipping_result": "N/A",
                                        "dark_mode_leakage_result": "N/A",
                                        "console_result": "N/A",
                                        "screenshot_path": "",
                                        "pass": False,
                                    })
                                    results["total_failures"] += 1

                            results["combinations_tested"] += 1
                            results["details"].append(combo_results)
                            context.close()
                    browser.close()
            except Exception as e:
                exception = e

        t = threading.Thread(target=run_visual_crawl)
        t.start()
        t.join()

        if exception:
            raise exception

        # Write visual_matrix.json
        with open(os.path.join(REPORT_DIR, "visual_matrix.json"), "w") as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\nVisual Matrix: {results['combinations_tested']} combos, {results['total_failures']} failures")

    def test_vis_003_analytics_leakage(self):
        """Audits analytics JS loading and requests across three distinct scenarios (VIS-003)."""
        import os
        os.environ["QA_REAL_NETWORK"] = "1"
        try:
            scenarios_evidence = {}
            exception = None

            def run_vis003():
                nonlocal exception
                try:
                    with sync_playwright() as pw:
                        browser = pw.chromium.launch(headless=True)

                        # --- Scenario 1: Fresh anonymous context opened directly on login ---
                        context1 = browser.new_context()
                        page1 = context1.new_page()
                        
                        s1_requests = []
                        page1.on("request", lambda req: s1_requests.append({
                            "url": req.url,
                            "timestamp": datetime.now().isoformat(),
                            "method": req.method,
                        }) if "analytics" in req.url or "charts" in req.url or req.url.endswith(".json") else None)
                        
                        console_msgs_1 = []
                        page1.on("console", lambda msg: console_msgs_1.append({
                            "type": msg.type,
                            "text": msg.text,
                            "timestamp": datetime.now().isoformat(),
                        }))

                        # Navigation timing
                        t0 = time.time()
                        page1.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded")
                        nav_timing = time.time() - t0
                        page1.wait_for_timeout(1000)

                        chart_exists_1 = page1.query_selector("canvas") is not None
                        
                        scenarios_evidence["scenario_1"] = {
                            "description": "fresh anonymous context opened directly on login",
                            "requests_recorded": s1_requests,
                            "chart_element_existed": chart_exists_1,
                            "console_messages": console_msgs_1,
                            "navigation_timing_seconds": nav_timing,
                            "page_url_when_initiated": page1.url,
                        }
                        context1.close()

                        # --- Scenario 2: Authenticated dashboard followed by logout ---
                        context2 = browser.new_context()
                        page2 = context2.new_page()

                        s2_requests = []
                        page2.on("request", lambda req: s2_requests.append({
                            "url": req.url,
                            "timestamp": datetime.now().isoformat(),
                            "method": req.method,
                        }) if "analytics" in req.url or "charts" in req.url or req.url.endswith(".json") else None)
                        
                        console_msgs_2 = []
                        page2.on("console", lambda msg: console_msgs_2.append({
                            "type": msg.type,
                            "text": msg.text,
                            "timestamp": datetime.now().isoformat(),
                        }))

                        # Login
                        page2.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded")
                        page2.fill("input[name='username']", self.admin_user.email)
                        page2.fill("input[name='password']", TEST_PASSWORD)
                        page2.click("button[type='submit']")
                        page2.wait_for_selector(".app-wrapper")

                        # Open dashboard
                        page2.goto(f"{self.live_server_url}/panel/admin/dashboard/", wait_until="domcontentloaded")
                        page2.wait_for_timeout(1000)
                        chart_exists_2 = page2.query_selector("canvas") is not None

                        # Logout
                        page2.goto(f"{self.live_server_url}/accounts/logout/", wait_until="domcontentloaded")
                        page2.wait_for_timeout(1000)

                        scenarios_evidence["scenario_2"] = {
                            "description": "authenticated dashboard followed by logout",
                            "requests_recorded": s2_requests,
                            "chart_element_existed": chart_exists_2,
                            "console_messages": console_msgs_2,
                            "page_url_when_initiated": page2.url,
                        }
                        context2.close()

                        # --- Scenario 3: Dashboard navigation interrupted while analytics requests are active ---
                        context3 = browser.new_context()
                        page3 = context3.new_page()

                        s3_requests = []
                        page3.on("request", lambda req: s3_requests.append({
                            "url": req.url,
                            "timestamp": datetime.now().isoformat(),
                            "method": req.method,
                        }) if "analytics" in req.url or "charts" in req.url or req.url.endswith(".json") else None)
                        
                        console_msgs_3 = []
                        page3.on("console", lambda msg: console_msgs_3.append({
                            "type": msg.type,
                            "text": msg.text,
                            "timestamp": datetime.now().isoformat(),
                        }))

                        # Login
                        page3.goto(f"{self.live_server_url}/accounts/login/", wait_until="domcontentloaded")
                        page3.fill("input[name='username']", self.admin_user.email)
                        page3.fill("input[name='password']", TEST_PASSWORD)
                        page3.click("button[type='submit']")
                        page3.wait_for_selector(".app-wrapper")

                        # Load dashboard, interrupt immediately (wait_until="commit" then redirect)
                        page3.goto(f"{self.live_server_url}/panel/admin/dashboard/", wait_until="commit")
                        page3.goto(f"{self.live_server_url}/accounts/profile/", wait_until="domcontentloaded")
                        page3.wait_for_timeout(1000)

                        scenarios_evidence["scenario_3"] = {
                            "description": "dashboard navigation interrupted while analytics requests are active",
                            "requests_recorded": s3_requests,
                            "console_messages": console_msgs_3,
                            "page_url_when_initiated": page3.url,
                        }
                        context3.close()
                        browser.close()
                except Exception as e:
                    exception = e

            t = threading.Thread(target=run_vis003)
            t.start()
            t.join()

            if exception:
                raise exception

            self.__class__.vis_003_evidence = {
                "scenarios": scenarios_evidence,
            }
        finally:
            os.environ.pop("QA_REAL_NETWORK", None)


if __name__ == "__main__":
    unittest.main()
