"""
Route Inventory — Discovers all registered URL patterns in the Iqra Academy CRM.

Outputs a comprehensive markdown report mapping every route to its view,
required HTTP method, URL name, and namespace.

Usage:
    python tools/qa/route_inventory.py
"""

import os
import sys
import json
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.base")

import django
django.setup()

from django.urls import URLPattern, URLResolver, get_resolver


def extract_routes(resolver=None, prefix="", namespace=""):
    """Recursively extract all URL patterns from the Django URL resolver."""
    if resolver is None:
        resolver = get_resolver()

    routes = []
    for pattern in resolver.url_patterns:
        if isinstance(pattern, URLResolver):
            new_prefix = prefix + str(pattern.pattern)
            new_ns = f"{namespace}:{pattern.namespace}" if pattern.namespace else namespace
            routes.extend(extract_routes(pattern, new_prefix, new_ns))
        elif isinstance(pattern, URLPattern):
            full_path = prefix + str(pattern.pattern)
            view_name = ""
            if hasattr(pattern.callback, '__name__'):
                view_name = pattern.callback.__name__
            elif hasattr(pattern.callback, '__class__'):
                view_name = pattern.callback.__class__.__name__
            if hasattr(pattern.callback, 'view_class'):
                view_name = pattern.callback.view_class.__name__

            url_name = pattern.name or ""
            full_name = f"{namespace}:{url_name}" if namespace and url_name else url_name

            # Detect HTTP methods from view
            methods = []
            if hasattr(pattern.callback, 'view_class'):
                vc = pattern.callback.view_class
                for m in ['get', 'post', 'put', 'patch', 'delete']:
                    if hasattr(vc, m):
                        methods.append(m.upper())
            else:
                methods = ["GET", "POST"]  # Default for function views

            routes.append({
                "path": "/" + full_path,
                "view": view_name,
                "url_name": full_name,
                "namespace": namespace,
                "methods": methods,
                "has_parameters": "<" in full_path,
            })

    return routes


def categorize_routes(routes):
    """Categorize routes by module/namespace."""
    categories = {}
    for route in routes:
        ns = route["namespace"] or "root"
        # Simplify namespace
        top_ns = ns.split(":")[0] if ":" in ns else ns
        if top_ns not in categories:
            categories[top_ns] = []
        categories[top_ns].append(route)
    return categories


def generate_markdown_report(routes, categories):
    """Generate a markdown report of all routes."""
    lines = [
        "# Route Inventory — Iqra Academy CRM",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        f"**Total routes discovered: {len(routes)}**",
        "",
    ]

    # Summary table
    lines.append("## Summary by Module")
    lines.append("")
    lines.append("| Module | Routes | Parameterized | Static |")
    lines.append("|--------|--------|--------------|--------|")
    for cat, cat_routes in sorted(categories.items()):
        param = sum(1 for r in cat_routes if r["has_parameters"])
        static = len(cat_routes) - param
        lines.append(f"| {cat} | {len(cat_routes)} | {param} | {static} |")
    lines.append("")

    # Detailed routes per module
    lines.append("## Detailed Route Listing")
    lines.append("")

    for cat, cat_routes in sorted(categories.items()):
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| Path | View | URL Name | Methods | Params |")
        lines.append("|------|------|----------|---------|--------|")
        for r in sorted(cat_routes, key=lambda x: x["path"]):
            methods = ", ".join(r["methods"][:3])
            params = "✓" if r["has_parameters"] else ""
            path = r["path"].replace("|", "\\|")
            lines.append(f"| `{path}` | {r['view']} | {r['url_name']} | {methods} | {params} |")
        lines.append("")

    return "\n".join(lines)


def generate_json_report(routes):
    """Generate a JSON report for machine consumption."""
    return json.dumps(routes, indent=2, default=str)


def main():
    routes = extract_routes()
    categories = categorize_routes(routes)

    # Write markdown report
    md_report = generate_markdown_report(routes, categories)
    report_dir = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")
    os.makedirs(report_dir, exist_ok=True)

    md_path = os.path.join(report_dir, "route_inventory.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    # Write JSON report
    json_path = os.path.join(report_dir, "route_inventory.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(generate_json_report(routes))

    print(f"Route inventory generated:")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")
    print(f"  Total routes: {len(routes)}")

    return routes


if __name__ == "__main__":
    main()
