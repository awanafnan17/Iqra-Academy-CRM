# Route Permission Matrix

This matrix maps access permissions for the 8 CRM user roles against key panel URL prefixes and specific functional routes.

---

## Panel-Level Access Matrix

| Role | Admin Panel (`/panel/admin/`) | Principal Panel (`/panel/principal/`) | Registrar Panel (`/panel/registrar/`) | Teacher Panel (`/panel/teacher/`) | Accounts Panel (`/panel/accounts/`) | Student Portal (`/portal/student/`) | Guardian Portal (`/portal/guardian/`) | Anonymous / Public |
|---|---|---|---|---|---|---|---|---|
| **Admin** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | **ALLOW** | DENIED | DENIED | DENIED |
| **Principal** | **ALLOW** | **ALLOW** | DENIED | DENIED | DENIED | DENIED | DENIED | DENIED |
| **Registrar** | **PARTIAL** | DENIED | **ALLOW** | DENIED | DENIED | DENIED | DENIED | DENIED |
| **Teacher** | DENIED | DENIED | DENIED | **ALLOW** | DENIED | DENIED | DENIED | DENIED |
| **Accountant** | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED | DENIED | DENIED |
| **Student** | DENIED | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED | DENIED |
| **Guardian** | DENIED | DENIED | DENIED | DENIED | DENIED | DENIED | **ALLOW** | DENIED |
| **Anonymous** | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | REDIRECT | **ALLOW** |

---

## Detailed Route Access Rules

| Route / Prefix | View / Action | Admin | Principal | Registrar | Teacher | Accountant | Student | Guardian | Anon |
|---|---|---|---|---|---|---|---|---|---|
| `/apply/` | Public Admissions Form | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | ALLOW | **ALLOW** |
| `/panel/admin/dashboard/` | Main Dashboard | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/permissions/` | Permission Matrix View | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/users/` | User Management views | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/students/` | View Student List | **ALLOW** | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/students/create/` | Register Student Form | **ALLOW** | 404 | **ALLOW** | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/students/<int:pk>/edit/`| Edit Student Form | **ALLOW** | 404 | **ALLOW** | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/pdf-comparison/` | Run PDF Candidate Match | **ALLOW** | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/documents/jobs/` | PDF jobs direct include | **ALLOW** | **ALLOW** | **404 (BUG)**| 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/admissions/<int:pk>/approve/` | Approve Admission (POST) | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/exams/<int:pk>/publish/` | Publish Exam (POST) | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/reports/` | Reports Dashboard View | **ALLOW** | **ALLOW** | 404 | 404 | 404 | 404 | 404 | 302 |
| `/panel/admin/reports/student/<id>/transcript/pdf/`| Transcript PDF View | **ALLOW** | **ALLOW** | **404 (BUG)**| 404 | 404 | 404 | 404 | 302 |
| `/panel/accounts/dashboard/` | Accountant Panel Home | **ALLOW** | 404 | 404 | 404 | **ALLOW** | 404 | 404 | 302 |
| `/portal/student/dashboard/` | Student Portal Home | 404 | 404 | 404 | 404 | 404 | **ALLOW** | 404 | 302 |
| `/portal/guardian/dashboard/` | Guardian Portal Home | 404 | 404 | 404 | 404 | 404 | 404 | **ALLOW** | 302 |

> **Security Note**: In compliance with our security hardening policies, unauthorized staff access to routes raises `Http404` rather than `Http403` to mask the route's existence on the system.
