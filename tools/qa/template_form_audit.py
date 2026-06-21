"""
Template Form Audit — Introspects all Django templates for form patterns.

Scans all templates for <form> tags and verifies:
- CSRF token presence
- Method attribute (GET/POST)
- Action attribute
- enctype for file uploads
- Submit button presence
- data-testid attributes

Usage:
    python tools/qa/template_form_audit.py
"""

import os
import sys
import re
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATE_DIR = os.path.join(PROJECT_ROOT, "templates")
REPORT_DIR = os.path.join(PROJECT_ROOT, "tools", "qa", "reports")


def find_templates():
    """Find all HTML template files."""
    templates = []
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for f in files:
            if f.endswith('.html'):
                templates.append(os.path.join(root, f))
    # Also check app-level templates
    apps_dir = os.path.join(PROJECT_ROOT, "apps")
    for root, dirs, files in os.walk(apps_dir):
        if "templates" in root.split(os.sep):
            for f in files:
                if f.endswith('.html'):
                    templates.append(os.path.join(root, f))
    return templates


def audit_template(filepath):
    """Audit a single template for form issues."""
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    rel_path = os.path.relpath(filepath, PROJECT_ROOT)
    findings = []

    # Find all form tags
    form_pattern = re.compile(r'<form\b([^>]*)>', re.IGNORECASE | re.DOTALL)
    forms = list(form_pattern.finditer(content))

    if not forms:
        return findings

    for i, form_match in enumerate(forms):
        form_attrs = form_match.group(1)
        form_start = form_match.start()

        # Find the closing </form>
        end_pattern = re.compile(r'</form>', re.IGNORECASE)
        end_match = end_pattern.search(content, form_start)
        form_end = end_match.end() if end_match else len(content)
        form_body = content[form_start:form_end]

        form_info = {
            "file": rel_path,
            "form_index": i + 1,
            "line": content[:form_start].count('\n') + 1,
            "issues": [],
            "details": {},
        }

        # Check method
        method_match = re.search(r'method=["\'](\w+)["\']', form_attrs, re.IGNORECASE)
        method = method_match.group(1).upper() if method_match else "GET"
        form_info["details"]["method"] = method

        # Check action
        action_match = re.search(r'action=["\']([^"\']*)["\']', form_attrs, re.IGNORECASE)
        action = action_match.group(1) if action_match else ""
        form_info["details"]["action"] = action

        # Check CSRF token (required for POST forms)
        has_csrf = "{% csrf_token %}" in form_body or "csrf_token" in form_body
        form_info["details"]["has_csrf"] = has_csrf
        if method == "POST" and not has_csrf:
            form_info["issues"].append("CRITICAL: POST form missing {% csrf_token %}")

        # Check enctype for file uploads
        has_file_input = re.search(r'type=["\']file["\']', form_body, re.IGNORECASE)
        has_enctype = "multipart/form-data" in form_attrs
        form_info["details"]["has_file_input"] = bool(has_file_input)
        form_info["details"]["has_enctype"] = has_enctype
        if has_file_input and not has_enctype:
            form_info["issues"].append("File input without enctype='multipart/form-data'")

        # Check submit button
        has_submit = bool(re.search(
            r'type=["\']submit["\']|<button\b(?![^>]*type=["\']button["\'])',
            form_body, re.IGNORECASE
        ))
        form_info["details"]["has_submit"] = has_submit
        if not has_submit:
            form_info["issues"].append("Form has no visible submit button")

        # Check data-testid on submit
        submit_match = re.search(r'<button[^>]*type=["\']submit["\'][^>]*>', form_body, re.IGNORECASE)
        if submit_match:
            has_testid = "data-testid" in submit_match.group(0)
            form_info["details"]["submit_has_testid"] = has_testid

        # Check for empty action on POST
        if method == "POST" and action == "":
            form_info["issues"].append("POST form with empty action (relies on current URL)")

        # Count input fields
        input_count = len(re.findall(r'<input\b', form_body, re.IGNORECASE))
        select_count = len(re.findall(r'<select\b', form_body, re.IGNORECASE))
        textarea_count = len(re.findall(r'<textarea\b', form_body, re.IGNORECASE))
        form_info["details"]["field_counts"] = {
            "inputs": input_count,
            "selects": select_count,
            "textareas": textarea_count,
        }

        findings.append(form_info)

    return findings


def generate_report(all_findings):
    """Generate markdown and JSON reports."""
    os.makedirs(REPORT_DIR, exist_ok=True)

    # Separate issues from clean forms
    forms_with_issues = [f for f in all_findings if f["issues"]]
    clean_forms = [f for f in all_findings if not f["issues"]]

    lines = [
        "# Form Persistence Report — Iqra Academy CRM",
        "",
        f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        f"**Total forms audited: {len(all_findings)}**",
        f"**Forms with issues: {len(forms_with_issues)}**",
        f"**Clean forms: {len(clean_forms)}**",
        "",
    ]

    if forms_with_issues:
        lines.append("## Forms With Issues")
        lines.append("")
        lines.append("| File | Line | Method | Issue |")
        lines.append("|------|------|--------|-------|")
        for f in forms_with_issues:
            for issue in f["issues"]:
                lines.append(f"| `{f['file']}` | {f['line']} | {f['details']['method']} | {issue} |")
        lines.append("")

    # Critical issues summary
    critical = [f for f in forms_with_issues if any("CRITICAL" in i for i in f["issues"])]
    if critical:
        lines.append("## Critical Issues")
        lines.append("")
        for f in critical:
            for issue in f["issues"]:
                if "CRITICAL" in issue:
                    lines.append(f"- **{f['file']}** (line {f['line']}): {issue}")
        lines.append("")

    lines.append("## All Forms Summary")
    lines.append("")
    lines.append("| File | Line | Method | Action | CSRF | Fields | Issues |")
    lines.append("|------|------|--------|--------|------|--------|--------|")
    for f in all_findings:
        fc = f["details"].get("field_counts", {})
        total_fields = fc.get("inputs", 0) + fc.get("selects", 0) + fc.get("textareas", 0)
        issues = len(f["issues"])
        action = f["details"].get("action", "")[:30]
        lines.append(
            f"| `{f['file']}` | {f['line']} | {f['details']['method']} "
            f"| {action} | {'✓' if f['details']['has_csrf'] else '✗'} "
            f"| {total_fields} | {issues} |"
        )

    md_path = os.path.join(REPORT_DIR, "form_persistence_report.md")
    with open(md_path, "w", encoding="utf-8") as fout:
        fout.write("\n".join(lines))

    json_path = os.path.join(REPORT_DIR, "form_persistence_report.json")
    with open(json_path, "w", encoding="utf-8") as fout:
        json.dump(all_findings, fout, indent=2)

    print(f"Form audit report generated:")
    print(f"  Markdown: {md_path}")
    print(f"  JSON:     {json_path}")
    print(f"  Total forms: {len(all_findings)}")
    print(f"  Issues found: {len(forms_with_issues)}")

    return all_findings


def main():
    templates = find_templates()
    all_findings = []
    for t in templates:
        findings = audit_template(t)
        all_findings.extend(findings)
    generate_report(all_findings)
    return all_findings


if __name__ == "__main__":
    main()
