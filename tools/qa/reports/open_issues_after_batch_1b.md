# Open Issues After Repair Batch 1B

This document lists the 9 remaining open issues from the original release-readiness audit that have not yet been repaired.

---

## 1. Summary of Remaining Open Issues

*   **Total Open Issues**: 9
*   **By Severity**:
    *   **CRITICAL**: 1
    *   **HIGH**: 6
    *   **MEDIUM**: 2
    *   **LOW**: 0

---

## 2. Detailed Breakdown of Open Issues

### 1. `RR-004` Grade Config List, Create, and Edit View Stubs
*   **Severity**: CRITICAL
*   **Module**: Exams
*   **Impact**: Academic staff cannot customize grade boundaries in the UI. Systems fall back to static logic, preventing customization of grading systems for specific sessions.
*   **Location**: `apps/exams/views.py` (lines 38-40) and associated urls/templates.
*   **Recommended Fix**: Implement full django form views for GradeConfig and design the list/form templates.

### 2. `RR-010` N+1 Query Performance in Success Report PDF Generation
*   **Severity**: HIGH
*   **Module**: Reports
*   **Impact**: Generates a database query inside a loop for each achievement record to retrieve active enrollments. With hundreds or thousands of students, this triggers database starvation.
*   **Location**: `apps/reports/views.py` (lines 298-300).
*   **Recommended Fix**: Prefetch or select related active enrollments on the student queryset before the loop.

### 3. `RR-011` N+1 Query Performance in Teacher Workload PDF Generation
*   **Severity**: HIGH
*   **Module**: Reports
*   **Impact**: Query duplication occurs because a filter method is called inside a loop over the prefetched related manager `teaching_assignments`.
*   **Location**: `apps/reports/views.py` (line 171).
*   **Recommended Fix**: Filter teaching assignments in Python memory using list comprehensions instead of database queries.

### 4. `RR-006` Audit Log List and Detail View Stubs
*   **Severity**: HIGH
*   **Module**: Core
*   **Impact**: Admins cannot view or filter system activity logs, creating security visibility gaps.
*   **Location**: `apps/core/views.py` (lines 46-47) and associated template files.
*   **Recommended Fix**: Implement log view classes, filtering parameters, and standard dashboard templates.

### 5. `RR-007` Trailing Slash Middleware Bypass on PDF Comparison
*   **Severity**: HIGH
*   **Module**: Documents
*   **Impact**: Registrar requesting `/panel/admin/pdf-comparison` receives an HTTP 404 instead of access allowed because of the missing trailing slash mismatch in PanelAccessMiddleware prefix matching.
*   **Location**: `apps/core/middleware.py` (PanelAccessMiddleware checks).
*   **Recommended Fix**: Normalize request paths by stripping the trailing slash before executing prefix access checks.

### 6. `RR-008` Overlapping Reports Namespace and Path Conflicts
*   **Severity**: HIGH
*   **Module**: Dashboard / Reports
*   **Impact**: Double mounting of prefix `/panel/admin/reports/` creates potential routing confusion, namespace collision, and controller bypass risk.
*   **Location**: `config/urls.py` and `apps/dashboard/urls_admin.py`.
*   **Recommended Fix**: Consolidate reports routing under a single urlconf.

### 7. `RR-005` AI Engine Prediction Views Stubs
*   **Severity**: HIGH
*   **Module**: AI Engine
*   **Impact**: The Dropout risk dashboard and predictions analytics pages are plain-text placeholders.
*   **Location**: `apps/ai_engine/views.py`.
*   **Recommended Fix**: Wire view metrics to database model histories (`PredictionLog`) and render visual charts.

### 8. `RR-014` Registrar Blocked from Transcripts
*   **Severity**: MEDIUM
*   **Module**: Reports
*   **Impact**: Registrar role is blocked from viewing student transcript PDFs despite managing student records.
*   **Location**: `apps/reports/views.py` (role checks in `StudentTranscriptPDFView`).
*   **Recommended Fix**: Add `"Registrar"` to the allowed staff roles check.

### 9. `RR-009` Hardcoded URLs in PDF Comparison Templates
*   **Severity**: MEDIUM
*   **Module**: Documents
*   **Impact**: Inflexible URLs in HTML templates prevent routing reconfiguration.
*   **Location**: `templates/documents/pdf_comparison.html`.
*   **Recommended Fix**: Replace hardcoded URL paths with dynamic `{% url %}` tags.
