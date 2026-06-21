# Post-Repair Rebaseline Audit Report (After Batch 1B)

*Generated: 2026-06-21 14:30:00*  
**Database**: `db_demo.sqlite3` / `db_test.sqlite3`  
**Settings Module**: `config.settings.test`  
**Audit Rebaseline Status**: **REBASELINE_PASSED_OPEN_ISSUES_REMAIN**

---

## 1. Executive Summary

Following the successful implementation of Repair Batch 1A and the sub-batches of Repair Batch 1B (1B-1, 1B-2, 1B-3A, and 1B-3B), a comprehensive rebaseline audit was conducted. This audit validates that the core blockers and academics/attendance stubs have been successfully replaced with fully functional production-grade code, while maintaining database integrity and strict security configurations.

*   **Total Original Issues**: 14
*   **Closed / Verified Issues**: 5
*   **Still-Open Issues**: 9
*   **New Regressions**: 0
*   **Full Test-Suite Result**: 249/249 tests passed (100% pass rate)
*   **Migration Check Result**: Clean dry-run ("No changes detected")

---

## 2. Verification of Closed Issues

The following baseline issues from the original audit are verified as **Closed** and confirmed fully functioning:

### `RR-001` Admissions Mutation GET Hardening (Closed)
*   **Verification**: GET requests to `AdmissionReviewView`, `AdmissionApproveView`, `AdmissionRejectView`, and `AdmissionConvertView` now raise `Http404` instead of returning HTTP 405 Method Not Allowed. This masks the existence of these administrative endpoints from scanners in compliance with system security hardening policies.
*   **Evidence**: Test `test_mutation_get_requests_rejected` in `SystemHardeningTests` passes successfully.

### `RR-002` Academics Module Stubs (Closed)
*   **Verification**: All placeholder plain-text stubs in the Academics module have been replaced. Full functional views and HTML templates now support:
    *   Subject Create and Edit (Admin/Principal only)
    *   Teacher Assignment Create, Edit, and Delete (Delete restricted to Admin only)
    *   Session Soft Delete (Admin only)
    *   Session Enrollments view (Admin/Principal/Registrar/Teacher)
    *   Session Revenue view (Admin only)
*   **Evidence**: 33/33 tests in `apps/academics/tests.py` pass successfully.

### `RR-003` Attendance Module Stubs (Closed)
*   **Verification**: All placeholder plain-text stubs in the Attendance module have been replaced. Staff and teachers can now perform the daily marking and lock/unlock workflow:
    *   Attendance Overview (Admin/Principal only)
    *   Attendance Mark (Admin/Principal/Teacher)
    *   Attendance Sheet (Admin/Principal/Teacher)
    *   Attendance Lock (Admin/Principal)
    *   Attendance Unlock (Admin only)
    *   Attendance Analytics (Admin/Principal/Teacher; Teacher restricted to assigned sessions only)
    *   Low Attendance Report (Admin/Principal only)
*   **Evidence**: 18/18 tests in `apps/attendance/tests.py` pass successfully.

### `RR-012` Student List Pagination (Closed)
*   **Verification**: The student list view (`student_list`) now implements Django's `Paginator` with a threshold of 25 records per page, preserving query search terms and status filters.
*   **Evidence**: Test `test_student_list_pagination` in `RepairBatch1RegressionTests` passes successfully.

### `RR-013` Student Creation Session Dropdown (Closed)
*   **Verification**: Mismatch between lowercase string `"active"` and database choice `"Active"` in `StudentCreateForm` has been corrected. Active sessions populate the dropdown choice list correctly.
*   **Evidence**: Test `test_student_create_session_dropdown` in `RepairBatch1RegressionTests` passes successfully.

---

## 3. Middleware & Role Safety Audit

The modification of access controls in `apps/core/middleware.py` was thoroughly verified:

1.  **Registrar Isolation**: The Registrar is permitted to access only the approved admin-prefixed exception URLs:
    *   PDF comparison page: `/panel/admin/pdf-comparison/`
    *   Session enrollments: `/panel/admin/academics/sessions/*/enrollments/`
    *   All other `/panel/admin/...` prefixes correctly raise `Http404` for Registrar.
2.  **Teacher Isolation**: The Teacher is permitted to access session enrollments and attendance analytics *only* for sessions they are actively assigned to as faculty. Accessing unassigned sessions raises `Http404`.
3.  **Staff/Admin Protection**: Student, Guardian, and Anonymous roles are strictly blocked from all staff panels. Anonymous requests redirect to login, while authenticated unauthorized roles receive `Http404`.
4.  **Middleware Safety**: Exceptions are bound to exact URL starts/ends patterns (no loose wildcard rules are present).

---

## 4. Finance Read-Only Audit

The new `session_revenue` view is confirmed as strictly **read-only**:

1.  **Record Count Verification**: DB records for `Payment`, `Refund`, and `Installment` were counted before and after loading the session revenue dashboard as Admin.
    *   *Payments count*: No change.
    *   *Refunds count*: No change.
    *   *Installments count*: No change.
2.  **Calculations & Integrity**: Aggregate figures (Tuition, Late Fees, Total, Refunds, and Net) are fetched solely using the existing backend service functions:
    *   `calculate_session_revenue`
    *   `calculate_student_ledger`
3.  **Role Protection**: Accessing `/panel/admin/academics/sessions/<id>/revenue/` is strictly guarded. Principal, Registrar, Teacher, Accountant, Student, and Guardian receive `Http404`.

---

## 5. Summary of Still-Open Issues

The following 9 baseline issues remain open for future repair batches:

| Issue ID | Severity | Module | Description | Suggested Repair Batch |
|---|---|---|---|---|
| **RR-004** | CRITICAL | Exams | Grade config list, create, and edit view stubs. | Batch 4 |
| **RR-005** | HIGH | AI Engine | Dropout risk dashboard and predictions stubs. | Batch 5 |
| **RR-006** | HIGH | Core | Audit log list and detail view stubs. | Batch 3 |
| **RR-007** | HIGH | Documents | Trailing slash path bypass on PDF comparison page. | Batch 3 |
| **RR-008** | HIGH | Dashboard | Double mounting Reports namespace path collision. | Batch 3 |
| **RR-009** | MEDIUM | Documents | Hardcoded URLs in PDF comparison templates. | Batch 5 |
| **RR-010** | HIGH | Reports | N+1 query loop inside Success Report PDF view. | Batch 2 |
| **RR-011** | HIGH | Reports | N+1 query loop inside Teacher Workload PDF view. | Batch 4 |
| **RR-014** | MEDIUM | Reports | Registrar blocked from viewing student transcripts. | Batch 3 |

---

## 6. Top Remaining Risks

1.  **Exams Grade Config Stubs (RR-004)**: Complete workflow dead end for customizing grading boundaries. Grade lookups will fail back to system defaults, preventing custom exam evaluation.
2.  **Performance N+1 Queries in PDF Reports (RR-010 / RR-011)**: Large graduating batches or full faculty lists will cause slow queries, potentially leading to database connection starvation and gateway timeouts in production.
3.  **Trailing Slash Bypass on PDF Comparison (RR-007)**: Middleware logic check using startswith allows path bypass anomalies where the system throws unexpected 404s for authorized roles depending on trailing slash presence.
4.  **Double Mounted Reports Namespace (RR-008)**: High potential for route collisions and namespace hijack bugs across dashboard layouts.

---

## 7. Next Repair Batch Recommendation

It is highly recommended to proceed with **Batch 2 (Finance & Data Integrity)** and **Batch 3 (Permissions & Security)** to address the N+1 performance bottlenecks and security path issues. Specifically:
- **RR-010** optimization should be resolved to secure PDF export stability.
- **RR-007** and **RR-008** should be resolved to fix permission anomalies and clean up routing configurations.
