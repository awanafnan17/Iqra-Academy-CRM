# Route Permission Matrix (After Batch 1B)

This matrix maps access permissions for all CRM user roles against key panel URL prefixes and specific functional routes, including newly implemented routes from Batch 1B.

---

## Panel-Level Access Matrix

| Role | Admin Panel (`/panel/admin/`) | Principal Panel (`/panel/principal/`) | Registrar Panel (`/panel/registrar/`) | Teacher Panel (`/panel/teacher/`) | Accounts Panel (`/panel/accounts/`) | Student Portal (`/portal/student/`) | Guardian Portal (`/portal/guardian/`) | Anonymous / Public |
|---|---|---|---|---|---|---|---|---|
| **Admin** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | DENIED | DENIED | DENIED |
| **Principal** | **ALLOW** | **ALLOW** | DENIED | DENIED | DENIED | DENIED | DENIED | DENIED |
| **Registrar** | **PARTIAL** (Approved exceptions only) | DENIED | **ALLOW** | DENIED | DENIED | DENIED | DENIED | DENIED |
| **Teacher** | **PARTIAL** (Approved exceptions only) | DENIED | DENIED | **ALLOW** | DENIED | DENIED | DENIED | DENIED |
| **Accountant** | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED | DENIED | DENIED |
| **Student** | DENIED | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED | DENIED |
| **Guardian** | DENIED | DENIED | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED |
| **Anonymous** | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | **ALLOW** |

---

## Detailed Route Access Rules

### Academics Module Routes (Batch 1B-1 & 1B-3)

| Route / Prefix | View / Action | Admin | Principal | Registrar | Teacher | Accountant | Student | Guardian | Anon |
|---|---|---|---|---|---|---|---|---|---|
| `/panel/admin/academics/subjects/create/` | Create Subject | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/subjects/<id>/edit/` | Edit Subject | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/assignments/create/` | Create Teacher Assignment | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/assignments/<id>/edit/` | Edit Teacher Assignment | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/assignments/<id>/delete/`| Delete Teacher Assignment | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/sessions/<id>/delete/` | Soft Delete Session | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/sessions/<id>/enrollments/` | View Session Enrollments (Read-Only) | **ALLOW** | **ALLOW** | **ALLOW** | **ASSIGNED** (1) | 404 | 404 | 404 | 302 |
| `/panel/admin/academics/sessions/<id>/revenue/` | View Session Revenue (Read-Only) | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |

*(1) Teachers can only view enrollments for sessions to which they are actively assigned. Unassigned session requests raise Http404.*

### Attendance Module Routes (Batch 1B-2 & 1B-3)

| Route / Prefix | View / Action | Admin | Principal | Registrar | Teacher | Accountant | Student | Guardian | Anon |
|---|---|---|---|---|---|---|---|---|---|
| `/panel/admin/attendance/` | Attendance Overview | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/mark/<session_id>/` | Mark Daily Attendance | **ALLOW** | **ALLOW** | 404 | **ALLOW** | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/<session_id>/date/<date>/` | Attendance Sheet View | **ALLOW** | **ALLOW** | 404 | **ALLOW** | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/<session_id>/lock/` | Lock Attendance Sheet | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/<session_id>/unlock/` | Unlock Attendance Sheet | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/<session_id>/analytics/` | View Attendance Analytics | **ALLOW** | **ALLOW** | 404 | **ASSIGNED** (2) | 404 | 404 | 404 | 302 |
| `/panel/admin/attendance/low-attendance/` | Low Attendance Report | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |

*(2) Teachers can only view analytics for sessions to which they are actively assigned. Unassigned session requests raise Http404.*

### Core / Other Hardened & Verified Routes

| Route / Prefix | View / Action | Admin | Principal | Registrar | Teacher | Accountant | Student | Guardian | Anon |
|---|---|---|---|---|---|---|---|---|---|
| `/apply/` | Public Admissions Form | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | **ALLOW** |
| `/panel/admin/pdf-comparison/` | PDF Candidate Match | **ALLOW** | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/reports/student/<id>/transcript/pdf/` | Transcript PDF View | **ALLOW** | **ALLOW** | **404 (BUG)** (3)| 404 | 404 | 404 | 404 | 302 |
| `/portal/student/dashboard/` | Student Portal Home | 404 | 404 | 404 | 404 | 404 | **ALLOW** | 404 | 302 |
| `/portal/guardian/dashboard/` | Guardian Portal Home | 404 | 404 | 404 | 404 | 404 | 404 | **ALLOW** | 302 |

*(3) Issue RR-014 remains open; the Registrar is currently blocked from viewing transcript PDFs and gets a 404.*
