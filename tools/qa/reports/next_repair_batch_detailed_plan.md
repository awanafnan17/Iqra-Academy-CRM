# Next Repair Batch Detailed Plan

*Generated: 2026-06-21 14:40:00*  
**Settings Module**: `config.settings.test`  
**Status**: **NEXT_BATCH_PLAN_READY**

---

## 1. Remaining Open Issues

The following 9 baseline issues from the original release readiness audit remain open:

| Issue ID | Severity | Module | Description | Proposed Batch |
|---|---|---|---|---|
| **RR-004** | CRITICAL | Exams | Grade config list, create, and edit view stubs. | Batch 2C |
| **RR-006** | HIGH | Core | Audit log list and detail view stubs. | Batch 2D |
| **RR-007** | HIGH | Documents | Trailing slash path bypass on PDF comparison page. | Batch 2A |
| **RR-008** | HIGH | Dashboard | Double mounting Reports namespace path collision. | Batch 2A |
| **RR-009** | MEDIUM | Documents | Hardcoded URLs in PDF comparison templates. | Batch 2A |
| **RR-010** | HIGH | Reports | N+1 query loop inside Success Report PDF view. | Batch 2B |
| **RR-011** | HIGH | Reports | N+1 query loop inside Teacher Workload PDF view. | Batch 2B |
| **RR-014** | MEDIUM | Reports | Registrar blocked from transcript PDFs. | Batch 2A |
| **RR-005** | HIGH | AI Engine | Dropout risk dashboard and predictions stubs. | AI Cleanup Later |

---

## 2. Recommended Next Implementation Batch: Batch 2A

We recommend executing **Batch 2A (Security/Routing Cleanup)** first.

### Why Batch 2A should go first
1.  **Security & Path Normalization**: Resolving the trailing slash bug (`RR-007`) ensures the system's core authorization middleware is robust and behaves consistently, preventing accidental 404 blockages for authorized users.
2.  **Clean Routing Foundation**: Fixing the double-mounted reports routing (`RR-008`) eliminates the risk of URL reversing collisions and namespace conflicts, which must be resolved before other report view optimizations (such as `RR-010`, `RR-011`) are worked on.
3.  **Role Completeness**: Unlocking student transcripts for Registrars (`RR-014`) completes Registrar access boundaries without broadening their permissions.
4.  **Low Risk & Safe**: The changes are strictly logic/routing changes in Python and HTML templates. There is absolutely zero database migration risk, zero finance logic alterations, and the scope is small and highly verifiable.

---

## 3. Separation of Issues (What NOT to group together)
- **Do NOT group Exams Grade Config (Batch 2C) with Security/Routing (Batch 2A)**: Exams grade configuration is a new functional feature requiring views, forms, templates, and validations for overlapping ranges. Grouping it with core security routing risks bloating the patch and complicating regression verification.
- **Do NOT group N+1 Reports Performance (Batch 2B) with Audit Log UI (Batch 2D)**: Database optimizations in PDF generators require dedicated query-count profiling and performance testing. Combining them with the implementation of a new read-only audit log dashboard introduces unrelated logic and raises validation overhead.
- **Do NOT group AI Engine Dashboard (`RR-005`) with Core Academic Modules**: The AI prediction engine is non-critical for core school operations. It should be treated as a low-priority polish item and deferred to the final phase.

---

## 4. Candidate Batch Details & Technical Plans

---

### Candidate Batch 2A — Security/Routing Cleanup

#### Issues Covered
- `RR-007` PDF comparison trailing-slash middleware issue
- `RR-008` Double-mounted reports namespace path collision
- `RR-009` Hardcoded PDF comparison URLs
- `RR-014` Registrar transcript PDF permission

#### Files Likely to Change
- `apps/core/middleware.py` (modify `PanelAccessMiddleware` path checking and add exceptions)
- `apps/reports/views.py` (allow Registrar role in `StudentTranscriptPDFView` logic)
- `templates/documents/pdf_comparison.html` (replace hardcoded URL paths with dynamic template tags)
- `apps/dashboard/urls_admin.py` (rename reports dashboard route prefix to `/panel/admin/dashboard-reports/` to resolve conflict)
- `config/urls.py` (verify clean report mount point)

#### Risks
- **Migration Risk**: None. No database schemas or models are added or modified.
- **Security Risk**: Low. Restores intended permissions to the Registrar for transcripts and normalizes slash matching. Does not broaden any access rights to other roles.

#### Verification & Test Plan
1.  **Unit Tests**:
    - Extend `ReportingEngineTests.test_student_transcript_pdf_access_rules` to assert that Registrar receives HTTP 200 and unprivileged roles receive HTTP 404.
    - Write a middleware test in `SystemHardeningTests` validating both `/panel/admin/pdf-comparison` and `/panel/admin/pdf-comparison/` are allowed for Registrar.
2.  **Manual Check**:
    - Log in as Registrar and verify that both `/panel/admin/pdf-comparison` and `/panel/admin/pdf-comparison/` load without 404.
    - Reverse reverse URL names using `manage.py shell` to confirm no namespace collisions exist.

---

### Candidate Batch 2B — Reports Performance

#### Issues Covered
- `RR-010` Success Report PDF N+1 query
- `RR-011` Teacher Workload PDF N+1 query

#### Files Likely to Change
- `apps/reports/views.py` (refactor loops inside `SuccessReportPDFView` and `TeacherWorkloadPDFView`)

#### Risks
- **Migration Risk**: None.
- **Security Risk**: None.
- **Data Integrity Risk**: Low. Optimizations must preserve the exact PDF layout, calculated aggregates, and values.

#### Verification & Test Plan
1.  **Query-Count Tests**:
    - Add tests to `apps/reports/tests.py` using Django's `self.assertNumQueries()` context manager.
    - Seed different numbers of achievements/assignments and verify that the query count remains flat (constant) instead of scaling linearly ($O(N)$).
2.  **Manual Check**:
    - Generate both PDF reports as Admin and visually compare them before/after optimization to ensure layout and contents are identical.

---

### Candidate Batch 2C — Exams Grade Config

#### Issues Covered
- `RR-004` Grade config list/create/edit stubs

#### Files Likely to Change
- `apps/exams/views.py` (implement `grade_config_list`, `grade_config_create`, `grade_config_edit` controllers)
- `apps/exams/urls.py` (ensure proper mapping)
- `apps/exams/forms.py` (NEW file; create `GradeConfigForm` mapping fields and overlap clean checks)
- `templates/exams/grade_config_list.html` (NEW template for layout)
- `templates/exams/grade_config_form.html` (NEW template for creation and editing)

#### Risks
- **Migration Risk**: None. Uses the existing `GradeConfig` model.
- **Security Risk**: Medium. Must restrict access to Admin and Principal.

#### Verification & Test Plan
1.  **Form Validation Tests**:
    - Assert that saving overlapping grade ranges for the same session (or global) fails form validation with a clear error message.
2.  **Access Control Tests**:
    - Assert that unauthorized roles (Teacher, Registrar, Accountant, Student, Guardian) are blocked from accessing grade config CRUD routes.

---

### Candidate Batch 2D — Audit Log UI

#### Issues Covered
- `RR-006` Audit log list/detail stubs

#### Files Likely to Change
- `apps/core/views.py` (implement `audit_log_list` and `audit_log_detail` controllers)
- `templates/core/audit_log_list.html` (NEW template with filter controls)
- `templates/core/audit_log_detail.html` (NEW template formatting JSON changes)

#### Risks
- **Migration Risk**: None.
- **Security Risk**: Low. Read-only view restricted strictly to Admin.

#### Verification & Test Plan
1.  **View Verification Tests**:
    - Assert that accessing audit log list/details endpoints is restricted to Admin only (throwing 404 for others).
    - Seed audit logs and verify that JSON serialization displays fields properly.
