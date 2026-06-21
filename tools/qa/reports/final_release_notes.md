# Final Release Notes - Version 1.0.0

These release notes outline the features, security hardening, and performance improvements included in the release-ready version of the Iqra Academy CRM.

## Release Highlights

This release delivers a fully functional, secure, and performant school management portal. Highlights include:
* **Production-Grade RBAC:** Strict panel-level prefixes and view-level role checks.
* **O(1) Optimized PDF Exports:** Eliminated query loops during reports generation.
* **Safe AI Integration:** Native database-backed dashboards.
* **Detailed Audit Logging:** Complete traceability for admin actions.

## Feature Breakdown

### 1. Admissions and Student Directory
* Built a conversion pipeline turning applications into active students.
* Implemented sequential, prefix-based roll number generation.
* Added clean pagination to the student directory and session enrollment lists.

### 2. Academics and Attendance
* Created full management interfaces for sessions, subjects, and teacher assignments.
* Implemented digital daily attendance sheets with low-attendance warnings.
* Developed lock/unlock settings for historical attendance.

### 3. Exams and Grades
* Built CRUD views for GradeConfig records.
* Added support for recording student marks and auto-calculating grade keys.
* Integrated dynamic PDF transcript generation.

### 4. Security Hardening
* Hardened state-mutating class-based views to reject GET requests with a 404 response.
* Normalized trailing slashes in URLs to block access bypass attempts.
* Integrated SecurityHardeningMiddleware to inject CSP, Frame-Options, and Referrer-Policy headers.

---

## Mapping of Addressed Issues

* **RR-001 (Admissions Get Hardening):** Mutation CBVs now reject GET with 404.
* **RR-002 (Academics CRUD):** Full implementation of session and subject interfaces.
* **RR-003 (Attendance Sheets):** Complete workflow for marking and analytics.
* **RR-004 (Exams Grade Config):** GradeConfig management interfaces operational.
* **RR-005 (AI Engine Cleanup):** Exchanged placeholders for real database tracking.
* **RR-006 (Audit Logs):** Core log viewing and details inspector created.
* **RR-007 (Trailing Slash Bypass):** URL path normalizations applied in middleware.
* **RR-008 (Reports Path Conflict):** Resolved namespace conflict on dashboard.
* **RR-009 (PDF Hardcoded URLs):** Mapped dynamically via reverse routing tags.
* **RR-010 (Success Report N+1):** Optimized queries via select_related.
* **RR-011 (Teacher Workload N+1):** Prefetched assignments data to reduce DB hits.
* **RR-012 (Student Pagination):** Added standard paginator on lists.
* **RR-013 (Student Dropdown):** Restructured choice widgets.
* **RR-014 (Registrar Transcripts):** Granted registrar roles transcript download access.
