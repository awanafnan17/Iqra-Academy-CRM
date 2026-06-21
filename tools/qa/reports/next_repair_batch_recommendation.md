# Next Repair Batch Recommendation (Post-Batch 1B)

Based on the completed rebaseline audit of the Iqra Academy CRM, this document outlines the proposed target issues and strategy for the next phases of release readiness repairs.

---

## 1. Recommendation: Combined Batch 2 & Batch 3

We recommend focusing next on **Batch 2 (Finance & Data Integrity)** and **Batch 3 (Permissions & Security)**. This addresses the remaining critical performance bottlenecks, path bypass vulnerabilities, and key role authorization defects.

---

## 2. Target Issues in Next Batch

| Issue ID | Severity | Module | Description | Action / Recommended Fix |
|---|---|---|---|---|
| **RR-010** | HIGH | Reports | N+1 query loop inside Success Report PDF view. | Prefetch active enrollments on the student queryset inside the view controller before running the render loop. |
| **RR-007** | HIGH | Documents | Trailing slash path bypass on PDF comparison page. | Normalize request paths in `PanelAccessMiddleware` by stripping trailing slashes before running role access validation checks. |
| **RR-008** | HIGH | Dashboard | Double mounting Reports namespace path collision. | Consolidate the Reports URL routing under a single urlconf and namespace inside the main `config/urls.py` routing schema. |
| **RR-014** | MEDIUM | Reports | Registrar blocked from viewing student transcripts. | Add `"Registrar"` to the allowed role check lists in the transcript rendering controller view `StudentTranscriptPDFView`. |
| **RR-006** | HIGH | Core | Audit log list and detail view stubs. | Replace plain-text stubs in `apps/core/views.py` with standard model querying views and database log templates. |

---

## 3. Technical Justification

1.  **Eliminating DB Performance Risks (RR-010)**: Success Report PDFs loop over achievement lists. Without prefetching active student enrollments, generating this report in production with real graduate cohorts will query the database once per row, resulting in high load, long response times, and database connection timeouts.
2.  **Securing Path & Middleware Isolation (RR-007 / RR-008)**:
    *   Path normalizations ensure that the CRM's security middleware behaves consistently regardless of trailing slash presence, preventing unexpected HTTP 404s for authorized staff.
    *   Resolving double-mounted report urls eliminates the potential for route collisions and namespace hijack bugs.
3.  **Completing Registrar Scope (RR-014)**: Registrars are core staff who manage enrollment data. Restoring transcript viewing rights is essential for academic administration.
4.  **Implementing System Visibility (RR-006)**: Implementing audit log interfaces gives administrators clear oversight of database operations, staff logins, and mutations, which is required for security tracking.

---

## 4. Proposed Timeline & Execution

*   **Phase A (Planning)**: Draft implementation plans for these five issues, identifying files to modify (middleware, reports, config URLs, core views) and verification metrics.
*   **Phase B (Execution)**: Implement optimizations first (RR-010), then middleware/routing normalization (RR-007, RR-008, RR-014), and finally core log dashboards (RR-006).
*   **Phase C (Verification)**: Run the CRM test suite (verifying no regressions in existing 249 tests) and perform role-specific endpoint testing.
