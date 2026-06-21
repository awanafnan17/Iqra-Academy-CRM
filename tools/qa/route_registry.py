"""
Route Registry — Build a complete route inventory from Django's URL resolver.

Classifies every registered panel route and generates an exclusion manifest.
This replaces manual seed lists with a programmatic approach.

Usage:
    python tools/qa/route_registry.py
"""

import os
import sys
import json
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.urls import URLPattern, URLResolver, get_resolver
import re


REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")

# Route classification patterns
DESTRUCTIVE_PATTERNS = [
    r"/delete/", r"/toggle-activation/", r"/toggle-lock/",
    r"/reset-password/", r"/approve/", r"/reject/",
    r"/convert/", r"/publish/", r"/toggle-status/",
    r"/create-login/", r"/mark-read/",
]
EXPORT_PATTERNS = [r"/export/", r"\.pdf$", r"\.csv$"]
AJAX_PATTERNS = [r"/api/", r"/unread-count/"]
CREATE_FORM_PATTERNS = [r"/create/", r"/add-"]
UPDATE_FORM_PATTERNS = [r"/edit/", r"/pay/"]
SYSTEM_PATTERNS = [r"^/admin/"]

PARAMETERIZED_RE = re.compile(r"<\w+:\w+>|<\w+>")


def extract_all_urls(resolver=None, prefix="", namespace=""):
    """Recursively extract all URL patterns from Django resolver."""
    if resolver is None:
        resolver = get_resolver()

    urls = []
    ns = namespace

    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            new_ns = f"{ns}:{pattern.namespace}" if pattern.namespace else ns
            new_prefix = prefix + str(pattern.pattern)
            urls.extend(extract_all_urls(pattern, new_prefix, new_ns))
        elif isinstance(pattern, URLPattern):
            full_pattern = prefix + str(pattern.pattern)
            url_name = f"{ns}:{pattern.name}" if ns and pattern.name else (pattern.name or "")
            urls.append({
                "pattern": "/" + full_pattern.rstrip("$"),
                "name": url_name,
                "namespace": ns,
                "has_params": bool(PARAMETERIZED_RE.search(full_pattern)),
                "view_name": getattr(pattern.callback, '__name__', str(pattern.callback)),
            })

    return urls


def classify_route(route):
    """Classify a route by type."""
    pattern = route["pattern"]

    # System routes
    for p in SYSTEM_PATTERNS:
        if re.search(p, pattern):
            return "system"

    # AJAX/JSON
    for p in AJAX_PATTERNS:
        if re.search(p, pattern):
            return "ajax_json"

    # Export/download
    for p in EXPORT_PATTERNS:
        if re.search(p, pattern):
            return "export_download"

    # Destructive POST
    for p in DESTRUCTIVE_PATTERNS:
        if re.search(p, pattern):
            return "destructive_post"

    # Create form
    for p in CREATE_FORM_PATTERNS:
        if re.search(p, pattern):
            return "create_form"

    # Update form
    for p in UPDATE_FORM_PATTERNS:
        if re.search(p, pattern):
            return "update_form"

    # Parameterized GET (detail views, etc.)
    if route["has_params"]:
        return "parameterized_get"

    return "static_get"


def generate_registry():
    """Generate the full route registry."""
    all_urls = extract_all_urls()
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Filter to panel routes only
    panel_urls = [u for u in all_urls if u["pattern"].startswith("/panel/")]
    account_urls = [u for u in all_urls if u["pattern"].startswith("/accounts/")]
    portal_urls = [u for u in all_urls if u["pattern"].startswith("/portal/")]

    registry = {
        "timestamp": datetime.now().isoformat(),
        "total_registered": len(all_urls),
        "panel_routes": len(panel_urls),
        "account_routes": len(account_urls),
        "portal_routes": len(portal_urls),
        "routes": [],
    }

    classification_counts = {}

    for route in panel_urls + account_urls + portal_urls:
        route_type = classify_route(route)
        classification_counts[route_type] = classification_counts.get(route_type, 0) + 1
        registry["routes"].append({
            **route,
            "classification": route_type,
        })

    registry["classification_counts"] = classification_counts

    # Write JSON
    json_path = os.path.join(REPORT_DIR, "route_registry.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, default=str)

    # Write markdown exclusion manifest
    lines = [
        "# Route Registry & Exclusion Manifest",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        f"## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|-------|",
        f"| Total registered URLs | {len(all_urls)} |",
        f"| Panel routes | {len(panel_urls)} |",
        f"| Account routes | {len(account_urls)} |",
        f"| Portal routes | {len(portal_urls)} |",
        "",
        f"## Classification Breakdown",
        "",
        f"| Type | Count |",
        f"|------|-------|",
    ]

    for cls_type, count in sorted(classification_counts.items()):
        lines.append(f"| {cls_type} | {count} |")

    lines.extend([
        "",
        "## Exclusion Manifest",
        "",
        "| Route Name | Pattern | Classification | Parameters | Reason Excluded | Separate Test |",
        "|------------|---------|----------------|------------|-----------------|---------------|",
    ])

    for route in registry["routes"]:
        if route["classification"] in ("destructive_post", "export_download", "system"):
            reason = {
                "destructive_post": "Modifies data; tested via Django client",
                "export_download": "Binary output; tested via Django client",
                "system": "Django admin; out of scope",
            }[route["classification"]]
            lines.append(
                f"| {route['name']} | `{route['pattern']}` | "
                f"{route['classification']} | {route['has_params']} | "
                f"{reason} | Yes |"
            )

    lines.extend([
        "",
        "## Browser-Testable Routes (Static GET)",
        "",
        "| Route Name | Pattern |",
        "|------------|---------|",
    ])

    for route in registry["routes"]:
        if route["classification"] == "static_get":
            lines.append(f"| {route['name']} | `{route['pattern']}` |")

    lines.extend([
        "",
        "## Parameterized Routes (Require Fixtures)",
        "",
        "| Route Name | Pattern | View |",
        "|------------|---------|------|",
    ])

    for route in registry["routes"]:
        if route["classification"] == "parameterized_get":
            lines.append(f"| {route['name']} | `{route['pattern']}` | {route['view_name']} |")

    lines.extend([
        "",
        "## Accounting Verification",
        "",
        "```",
        f"Total panel+account+portal routes: {len(panel_urls) + len(account_urls) + len(portal_urls)}",
    ])

    for cls_type, count in sorted(classification_counts.items()):
        lines.append(f"  {cls_type}: {count}")

    accounted = sum(classification_counts.values())
    lines.extend([
        f"  Total accounted: {accounted}",
        f"  Unclassified: {len(panel_urls) + len(account_urls) + len(portal_urls) - accounted}",
        "```",
    ])

    md_path = os.path.join(REPORT_DIR, "route_registry.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Route registry generated:")
    print(f"  Total URLs: {len(all_urls)}")
    print(f"  Panel: {len(panel_urls)}, Account: {len(account_urls)}, Portal: {len(portal_urls)}")
    print(f"  Classifications: {classification_counts}")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")

    return registry


if __name__ == "__main__":
    generate_registry()
