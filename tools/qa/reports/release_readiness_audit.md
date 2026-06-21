# CRM Release-Readiness QA Audit Report

*Generated: 2026-06-21 05:12:00*  
**Database**: `db_demo.sqlite3` / `db_test.sqlite3`  
**Settings Module**: `config.settings.test`  
**Release Readiness Status**: **NOT_RELEASE_READY**

---

## 1. Summary of Findings
A comprehensive release-readiness audit of the Iqra Academy CRM was conducted across routing, CRUD operations, form validations, workflows, finance transactions, role permissions, UI templates, and performance. 

*   **Total Issues Found**: 14
*   **Issues by Severity**:
    *   **BLOCKER**: 0
    *   **CRITICAL**: 6
    *   **HIGH**: 5
    *   **MEDIUM**: 3
    *   **LOW**: 0

---

## 2. Top 10 Most Dangerous Issues

### 1. [RR-013] Empty Session Dropdown in Student Creation
*   **Severity**: CRITICAL
*   **Module**: Students
*   **Impact**: Registrar and Admin cannot assign any academic session to a student during creation because the session field queryset filters by lowercase `"active"` status.
*   **Reproduction**: Navigate to `/panel/admin/students/create/` and click the "Session" dropdown. It remains empty even though there are active sessions seeded in the database.
*   **Recommended Fix**: Change forms.py line 106 to filter by capitalized status: `status="Active"`.

### 2. [RR-012] Missing Pagination on Student List View
*   **Severity**: CRITICAL
*   **Module**: Students
*   **Impact**: Loading the student list triggers an unpaginated database fetch (`Student.objects.all()`). Under real operations with thousands of student records, this will cause memory exhaustion, database performance degradation, and browser crashes.
*   **Reproduction**: Navigate to `/panel/admin/students/` with large student records.
*   **Recommended Fix**: Implement Django's `Paginator` in `student_list` view.

### 3. [RR-003] Attendance Module Stub Views (7 Stubs)
*   **Severity**: CRITICAL
*   **Module**: Attendance
*   **Impact**: Complete workflow dead end. Staff and Teachers cannot view attendance sheets, mark daily attendance, or lock/unlock attendance in the UI.
*   **Reproduction**: Try to access `/panel/admin/attendance/` or `/panel/admin/attendance/mark/1/`. Returns f"attendance_overview - Coming soon".
*   **Recommended Fix**: Implement the views calling the `AttendanceService` and render the appropriate templates.

### 4. [RR-002] Academics Module Stub Views (8 Stubs)
*   **Severity**: CRITICAL
*   **Module**: Academics
*   **Impact**: Complete workflow dead end. Staff cannot delete sessions, view session enrollments, view session revenue, manage subjects, or assign teachers to courses in the UI.
*   **Reproduction**: Access `/panel/admin/academics/subjects/create/`. Returns "subject_create - Coming soon".
*   **Recommended Fix**: Replace stub functions with database operations and render the template forms.

### 5. [RR-001] GET Requests to Mutating Endpoints Return 405 (Security Check Failure)
*   **Severity**: CRITICAL
*   **Module**: Admissions
*   **Impact**: Violates system security hardening policy. Scan bots and unauthorized users can easily probe and discover mutating admin views (approve, reject, review, convert) because they return HTTP 405 instead of HTTP 404.
*   **Reproduction**: Run `python manage.py test --settings=config.settings.test`. View test failure of `test_mutation_get_requests_rejected`.
*   **Recommended Fix**: Override `dispatch()` or `get()` on CBVs in `apps/admissions/views.py` to raise `Http404` for GET requests.

### 6. [RR-010] N+1 Query Performance in Success Report PDF Generation
*   **Severity**: HIGH
*   **Module**: Reports
*   **Impact**: Generates a database query inside a loop for each achievement record to retrieve active enrollments. With thousands of graduates, this will cause execution timeout and database thread starvation.
*   **Reproduction**: Run Success Selections PDF export from the reports dashboard.
*   **Recommended Fix**: Optimize the queryset by pre-fetching enrollment relations or performing SQL joins.

### 7. [RR-007] Trailing Slash Middleware Bypass on PDF Comparison
*   **Severity**: HIGH
*   **Module**: Documents
*   **Impact**: A Registrar requesting `/panel/admin/pdf-comparison` (no trailing slash) receives an HTTP 404, but `/panel/admin/pdf-comparison/` (with trailing slash) is accessible.
*   **Reproduction**: Log in as Registrar and type the URL without a trailing slash.
*   **Recommended Fix**: Normalize paths inside `PanelAccessMiddleware` using `path.rstrip('/')` before doing access validation.

### 8. [RR-008] Overlapping Reports Namespace and Path Conflicts
*   **Severity**: HIGH
*   **Module**: Dashboard / Reports
*   **Impact**: Overlapping routing registers `/panel/admin/reports/` twice under different namespaces (`reports` and `admin_panel:reports`), causing route confusion and potential controller bypass.
*   **Reproduction**: Perform URL resolving checks programmatically.
*   **Recommended Fix**: Consolidate views under a single URL structure and namespace.

### 9. [RR-005] AI Engine Prediction views (5 Stubs)
*   **Severity**: HIGH
*   **Module**: AI Engine
*   **Impact**: The Dropout risk dashboard and model version listings are empty placeholders.
*   **Reproduction**: Navigate to `/panel/admin/ai/predictions/`. Returns "prediction_list - Coming soon".
*   **Recommended Fix**: Wire the views to fetch data from the `PredictionLog` and `ModelVersion` database models.

### 10. [RR-014] Registrar Blocked from Transcripts
*   **Severity**: MEDIUM
*   **Module**: Reports
*   **Impact**: The Registrar is unable to view or print student transcripts even though they are the role responsible for student data.
*   **Reproduction**: Log in as Registrar and request `/panel/admin/reports/student/1/transcript/pdf/`.
*   **Recommended Fix**: Add `"Registrar"` to the allowed role lists in `StudentTranscriptPDFView`.

---

## 3. Coverage Summary
*   **Total Django URLs**: 485
*   **Fully Audited views**: 460
*   **Stubs/Placeholders**: 25 views (Academics, Attendance, Exams, AI Engine, Core)
*   **Total Models Checked**: 18
*   **Data Integrity Check**: 100% database schema check clean. No duplicate roll numbers or orphan records found in `db_demo.sqlite3`.

---

## 4. Failed Tests
*   `test_mutation_get_requests_rejected (apps.core.test_hardening.SystemHardeningTests)`: Fails because GET requests to admissions CBVs return 405 instead of 404.

---

## 5. Security & Permission Risks
*   **Route Probing**: GET requests to Admissions mutating views return 405, revealing their presence.
*   **Path Bypass**: Trailing slash checks in `PanelAccessMiddleware` can result in unintentional permission block anomalies for authorized roles.
*   **Dual Mounting**: Reports mounted twice creates a potential route hijack risk.

---

## 6. Recommended Action Items
The identified issues must be repaired in the 5 batches specified in `tools/qa/reports/repair_batch_plan.md` to guarantee a safe, reliable deployment.
For specific files, detail views, and route mapping, refer to `tools/qa/reports/release_readiness_coverage_matrix.md` and `tools/qa/reports/route_permission_matrix.md`.
