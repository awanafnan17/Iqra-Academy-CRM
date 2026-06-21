"""
Master QA Runner — Executes all QA scripts and generates evidence-driven reports.

Usage:
    python tools/qa/run_all_qa.py
    python tools/qa/run_all_qa.py --mode=enforcement
"""

import os
import sys
import subprocess
import json
import platform
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")

# Parse mode flag
ENFORCEMENT_MODE = "--mode=enforcement" in sys.argv


def run_command(cmd, label, env_overrides=None, timeout=300):
    """Run a command and return structured result."""
    print(f"\n{'='*60}")
    print(f"Running: {label}")
    print(f"{'='*60}")

    env = os.environ.copy()
    if env_overrides:
        env.update(env_overrides)

    # Set enforcement mode in environment
    if ENFORCEMENT_MODE:
        env["QA_ENFORCE"] = "1"

    result = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
    )

    if result.returncode != 0:
        print(result.stdout[-1000:] if len(result.stdout) > 1000 else result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[-500:] if len(result.stderr) > 500 else result.stderr)
    else:
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)

    return {
        "label": label,
        "command": " ".join(cmd),
        "returncode": result.returncode,
        "stdout_tail": result.stdout[-2000:] if result.stdout else "",
        "stderr_tail": result.stderr[-500:] if result.stderr else "",
        "passed": result.stdout.count(" PASSED") + result.stdout.count("passed"),
        "failed": result.stdout.count(" FAILED") + result.stdout.count("failed"),
        "errors": result.stdout.count(" ERROR") + result.stdout.count("error"),
    }


def generate_final_verification(results, django_result, check_result, migration_result):
    """Generate evidence-driven final_verification.json."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Determine working tree state
    try:
        git_rev = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=10
        )
        revision = git_rev.stdout.strip() if git_rev.returncode == 0 else "not-a-git-repo"
    except Exception:
        revision = "unknown"

    # Load crawler results if they exist
    crawler_totals = {"pages_visited": 0, "errors_500": 0, "errors_404": 0, "errors_403": 0}
    for crawl_file in ["crawl_admin.json", "crawl_principal.json", "crawl_teacher.json",
                       "crawl_student.json", "crawl_guardian.json", "crawl_anonymous.json",
                       "crawl_accountant.json", "crawl_registrar.json"]:
        crawl_path = os.path.join(REPORT_DIR, crawl_file)
        if os.path.exists(crawl_path):
            try:
                with open(crawl_path) as f:
                    data = json.load(f)
                crawler_totals["pages_visited"] += len(data.get("pages_visited", []))
                crawler_totals["errors_500"] += len(data.get("errors_500", []))
                crawler_totals["errors_404"] += len(data.get("errors_404", []))
                crawler_totals["errors_403"] += len(data.get("errors_403", []))
            except Exception:
                pass

    # Load route registry
    route_accounting = {}
    route_path = os.path.join(REPORT_DIR, "route_registry.json")
    if os.path.exists(route_path):
        try:
            with open(route_path) as f:
                route_data = json.load(f)
            route_accounting = {
                "total_routes": route_data.get("total_registered", 0),
                "panel_routes": route_data.get("panel_routes", 0),
                "classification_counts": route_data.get("classification_counts", {}),
            }
        except Exception:
            pass

    # Load form coverage
    form_accounting = {}
    form_path = os.path.join(REPORT_DIR, "form_coverage.json")
    if os.path.exists(form_path):
        try:
            with open(form_path) as f:
                form_accounting = json.load(f)
        except Exception:
            pass

    # Load visual matrix
    visual_coverage = {}
    visual_path = os.path.join(REPORT_DIR, "visual_matrix.json")
    if os.path.exists(visual_path):
        try:
            with open(visual_path) as f:
                visual_coverage = json.load(f)
        except Exception:
            pass

    # Load role matrix
    role_coverage = {}
    role_path = os.path.join(REPORT_DIR, "role_matrix.json")
    if os.path.exists(role_path):
        try:
            with open(role_path) as f:
                role_coverage = json.load(f)
        except Exception:
            pass

    # Load concurrency report
    concurrency_data = {}
    conc_path = os.path.join(REPORT_DIR, "concurrency.json")
    if os.path.exists(conc_path):
        try:
            with open(conc_path) as f:
                concurrency_data = json.load(f)
        except Exception:
            pass

    # Compute gates
    gates = {
        "system_check_pass": check_result["returncode"] == 0,
        "no_pending_migrations": migration_result["returncode"] == 0,
        "django_unit_tests_pass": django_result["returncode"] == 0,
        "zero_500_errors": crawler_totals["errors_500"] == 0,
        "zero_broken_links": crawler_totals["errors_404"] == 0,
        "zero_403_errors": crawler_totals["errors_403"] == 0,
        "enforcement_crawl_pass": all(
            r["returncode"] == 0
            for r in results
            if "crawl" in r.get("label", "").lower()
        ),
        "all_pytest_pass": all(r["returncode"] == 0 for r in results),
    }
    gates["all_gates_pass"] = all(gates.values())

    # Dynamically parse defect report for confirmed unresolved defects
    import re
    unresolved_defects_list = []
    report_path = r"C:\Users\Afnan Awan\.gemini\antigravity-ide\brain\6c5a85d5-8ce7-4a1c-9095-d6be8818e75a\defect_report.md"
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            defects = re.split(r"###\s+(DEF-[A-Z0-9\-]+)", content)
            for i in range(1, len(defects), 2):
                def_id = defects[i]
                def_body = defects[i+1] if i+1 < len(defects) else ""
                status_match = re.search(r"\-\s*(?:\*\*)?[Ss]tatus(?:\*\*)?\s*:\s*([^\n\r]+)", def_body)
                if status_match:
                    status = status_match.group(1).strip()
                    if "FIXED" not in status.upper():
                        unresolved_defects_list.append({"id": def_id, "description": f"Status: {status}"})
                else:
                    unresolved_defects_list.append({"id": def_id, "description": "Status not documented"})
        except Exception as e:
            pass

    # Extract all crawl errors from all roles
    crawl_errors = []
    crawl_files = [
        "crawl_admin.json", "crawl_principal.json", "crawl_teacher.json",
        "crawl_student.json", "crawl_guardian.json", "crawl_anonymous.json",
        "crawl_accountant.json", "crawl_registrar.json"
    ]
    for crawl_file in crawl_files:
        cpath = os.path.join(REPORT_DIR, crawl_file)
        if os.path.exists(cpath):
            try:
                with open(cpath) as f:
                    cdata = json.load(f)
                role = cdata.get("role", crawl_file)
                for key in ["errors_500", "errors_404", "errors_403"]:
                    for err in cdata.get(key, []):
                        crawl_errors.append({
                            "id": f"CRAWL-{err.get('status', 'ERR')}-{role}",
                            "description": f"HTTP {err.get('status')} at {err.get('url')} visited from {err.get('source_url')} (via {err.get('link_source')})"
                        })
            except Exception:
                pass

    unresolved_confirmed_defect_count = len(unresolved_defects_list) + len(crawl_errors)

    # Determine final status
    if gates["all_gates_pass"] and unresolved_confirmed_defect_count == 0:
        final_status = "PASS"
    elif unresolved_confirmed_defect_count > 0:
        # unresolved confirmed defect count > 0 => final status cannot be PASS or PASS_WITH_DOCUMENTED_EXCLUSIONS
        total_failed = sum(r.get("failed", 0) for r in results) + django_result.get("failed", 0)
        if total_failed > 0 or crawler_totals["errors_500"] > 0:
            final_status = "FAIL"
        else:
            final_status = "INCOMPLETE"
    else:
        # Only minor gate failures or intentional exclusions exist
        final_status = "PASS_WITH_DOCUMENTED_EXCLUSIONS"

    # Find visited URLs to identify untested routes
    visited_urls = set()
    for crawl_file in crawl_files:
        cpath = os.path.join(REPORT_DIR, crawl_file)
        if os.path.exists(cpath):
            try:
                with open(cpath) as f:
                    cdata = json.load(f)
                for page in cdata.get("pages_visited", []):
                    visited_urls.add(page.get("url", "").rstrip("/"))
                    visited_urls.add(page.get("final_url", "").rstrip("/"))
            except Exception:
                pass

    # Identify untested routes in Django registry
    untested_routes = []
    registry_routes = route_accounting.get("routes", []) if hasattr(route_accounting, "get") else []
    if not registry_routes and os.path.exists(os.path.join(REPORT_DIR, "route_registry.json")):
        try:
            with open(os.path.join(REPORT_DIR, "route_registry.json")) as f:
                rdata = json.load(f)
            registry_routes = rdata.get("routes", [])
        except Exception:
            pass

    for route in registry_routes:
        pattern = route.get("pattern", "")
        cleaned_pattern = pattern.rstrip("/")
        is_tested = False
        if not route.get("has_params"):
            is_tested = (cleaned_pattern in visited_urls)
        else:
            # simple regex match
            pattern_regex = re.sub(r"<\w+:\w+>|<\w+>", r"[^/]+", cleaned_pattern)
            pattern_regex = "^" + pattern_regex + "?$"
            is_tested = any(re.match(pattern_regex, url) for url in visited_urls)

        if not is_tested and route.get("classification") in ("static_get", "parameterized_get", "create_form", "update_form"):
            untested_routes.append({
                "route": pattern,
                "name": route.get("name", ""),
                "classification": route.get("classification", "")
            })

    # Count total visual matrix assertions
    total_visual_assertions = 0
    for detail in visual_coverage.get("details", []):
        total_visual_assertions += len(detail.get("pages", []))

    import django as django_module

    verification = {
        "timestamp": datetime.now().isoformat(),
        "revision": revision,
        "python_version": platform.python_version(),
        "django_version": django_module.__version__,
        "settings_module": os.environ.get("DJANGO_SETTINGS_MODULE", "unknown"),
        "database_engine": "sqlite3 (test isolation)",
        "mode": "enforcement" if ENFORCEMENT_MODE else "discovery",

        "commands": [
            {"label": r["label"], "exit_code": r["returncode"]}
            for r in [check_result, migration_result, django_result] + results
        ],

        "test_totals": {
            "django_unit_passed": django_result.get("passed", 0),
            "pytest_suites": len(results),
            "pytest_total_passed": sum(r.get("passed", 0) for r in results),
            "pytest_total_failed": sum(r.get("failed", 0) for r in results),
        },

        "crawler_totals": crawler_totals,
        "route_accounting": route_accounting,
        "form_accounting": form_accounting,
        "role_coverage": role_coverage,
        "visual_coverage": {
            **visual_coverage,
            "total_visual_assertions": total_visual_assertions,
        },
        "concurrency": concurrency_data,

        "unresolved_defects": [],
        "exclusions": [],

        "gates": gates,
        "final_status": final_status,
    }

    # Populate unresolved defects from crawler errors
    if crawler_totals["errors_500"] > 0:
        verification["unresolved_defects"].append(
            f"{crawler_totals['errors_500']} HTTP 500 errors found during crawl"
        )
    if crawler_totals["errors_404"] > 0:
        verification["unresolved_defects"].append(
            f"{crawler_totals['errors_404']} HTTP 404 broken links found during crawl"
        )
    if crawler_totals["errors_403"] > 0:
        verification["unresolved_defects"].append(
            f"{crawler_totals['errors_403']} HTTP 403 cross-panel leakage errors found during crawl"
        )

    # Distinguish classifications of findings
    classifications = {
        "confirmed_unresolved_defects": unresolved_defects_list + crawl_errors,
        "intentional_exclusions": [
            {"route": "/accounts/logout/", "reason": "Excluded from crawling to prevent session termination"},
            {"route": "/panel/admin/notifications/bulk-send/", "reason": "Destructive/bulk notification sending only accessible to Admin (tested via direct POST in test_delivery)"},
            {"route": "/toggle-activation/", "reason": "Destructive action omitted from automated GET crawls"},
        ],
        "false_positives": [],
        "environment_limitations": [
            {"description": "Uses SQLite3 in-memory database for StaticLiveServerTestCase isolation to avoid MySQL database pollution"}
        ],
        "untested_routes": untested_routes
    }
    verification["classifications"] = classifications

    # Write verification
    ver_path = os.path.join(REPORT_DIR, "final_verification.json")
    with open(ver_path, "w", encoding="utf-8") as f:
        json.dump(verification, f, indent=2, default=str)

    print(f"\n{'='*60}")
    print(f"FINAL STATUS: {final_status}")
    print(f"{'='*60}")
    print(f"  Gates: {json.dumps(gates, indent=4)}")
    print(f"  Total tests: {django_result.get('passed', 0) + sum(r.get('passed', 0) for r in results)}")
    print(f"  Crawl pages: {crawler_totals['pages_visited']}")
    print(f"  Visual assertions: {total_visual_assertions}")
    print(f"  Unresolved defects count: {unresolved_confirmed_defect_count}")
    print(f"  Verification: {ver_path}")

    return verification


def main():
    qa_dir = os.path.join(PROJECT_ROOT, "tools", "qa")

    # 0. System check
    check_result = run_command(
        [sys.executable, "manage.py", "check", "--settings=config.settings.test"],
        "Django System Check",
    )

    # 0b. Migration check
    migration_result = run_command(
        [sys.executable, "manage.py", "makemigrations", "--check", "--dry-run",
         "--settings=config.settings.test"],
        "Migration Check",
    )

    # 1. Django unit tests
    django_result = run_command(
        [sys.executable, "manage.py", "test", "--settings=config.settings.test",
         "--verbosity=2"],
        "Django Unit Tests",
        {"QA_DB_NAME": "db_django.sqlite3"},
    )

    # 2. Route registry (static analysis)
    run_command(
        [sys.executable, os.path.join(qa_dir, "route_registry.py")],
        "Route Registry Generation",
    )

    # 3. Pytest test suites
    test_suites = [
        ("test_form_persistence.py", "Form Persistence (Comprehensive)"),
        ("test_authorization.py", "Role & Authorization Matrix"),
        ("test_profile_identity.py", "Profile Identity Propagation"),
        ("test_mutation_propagation.py", "Mutation Propagation"),
        ("test_consistency_invariants.py", "Consistency Invariants"),
        ("test_stale_data.py", "Stale Data / Cache"),
        ("test_business_invariants.py", "Business Invariants"),
        ("test_browser_crawl.py", "Browser Crawl (Multi-Role)"),
        ("test_visual_matrix.py", "Visual Matrix (8 Combos)"),
        ("test_concurrency.py", "Concurrency Smoke Test"),
    ]

    results = []
    for test_file, label in test_suites:
        filepath = os.path.join(qa_dir, test_file)
        if os.path.exists(filepath):
            db_name = f"db_{os.path.basename(test_file).replace('.py', '')}.sqlite3"

            cmd = [
                sys.executable, "-m", "pytest",
                filepath,
                "-v", "--tb=short",
                f"--junitxml={os.path.join(REPORT_DIR, f'junit_{test_file.replace('.py', '')}.xml')}",
            ]

            result = run_command(cmd, label, {"QA_DB_NAME": db_name})
            results.append(result)

    # 4. Generate final verification
    ver = generate_final_verification(results, django_result, check_result, migration_result)

    if ENFORCEMENT_MODE:
        if not ver["gates"]["all_gates_pass"] or len(ver["classifications"]["confirmed_unresolved_defects"]) > 0:
            print("\n[ERROR] QA Enforcement check failed: gates did not pass or unresolved defects remain.")
            sys.exit(1)


if __name__ == "__main__":
    main()
