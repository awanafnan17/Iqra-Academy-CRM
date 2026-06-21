# Final Route Permission Matrix

This document maps the security and routing permissions for all 8 user roles (Admin, Principal, Registrar, Teacher, Accountant, Student, Guardian, and Anonymous) across the core pages of the Iqra Academy CRM. All results are verified live by Django test environment simulations.

## 1. Summary of Access Control Rules

- **Access Denied Response:** In order to mask route existence from unauthorized users, all endpoints return `404 Not Found` upon access failures for logged-in users instead of `403 Forbidden`.
- **Anonymous/Unauthenticated Redirects:** Unauthenticated requests consistently return a `302 Found` redirect pointing to the login page.
- **Registrar Special Exemptions:** In accordance with specific administrative exceptions, the `Registrar` is explicitly permitted to access:
  - PDF Comparison (`/panel/admin/pdf-comparison/`)
  - Student document upload (`/panel/registrar/students/<pk>/documents/upload/`)
  - Academic Transcript PDF (`/panel/admin/reports/student/<pk>/transcript/pdf/`)

---

## 2. Live Verification Matrix

| Page / URL Name | Admin | Principal | Registrar | Teacher | Accountant | Student | Guardian | Anonymous |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Admin Dashboard** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Principal Dashboard** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Registrar Dashboard** | `404` | `404` | `200` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Teacher Dashboard** | `404` | `404` | `404` | `200` | `404` | `404` | `404` | `302 (-> login)` |
| **Accounts Dashboard** | `404` | `404` | `404` | `404` | `200` | `404` | `404` | `302 (-> login)` |
| **Student Portal Dashboard** | `404` | `404` | `404` | `404` | `404` | `200` | `404` | `302 (-> login)` |
| **Guardian Portal Dashboard** | `404` | `404` | `404` | `404` | `404` | `404` | `200` | `302 (-> login)` |
| **Admissions List** | `200` | `404` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Manage Students** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Session Overview** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Attendance Overview** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Exams Overview** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Reports Dashboard** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Finance Payments List** | `200` | `200` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **PDF Comparison** | `200` | `200` | `200` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **Audit Logs List** | `200` | `404` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **AI Engine Predictions** | `200` | `404` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **CNIC/Document Upload (Admin/Principal)** | `302 (-> documents)` | `302 (-> documents)` | `404` | `404` | `404` | `404` | `404` | `302 (-> login)` |
| **CNIC/Document Upload (Registrar)** | `404` | `404` | `302 (-> detail)` | `404` | `404` | `404` | `404` | `302 (-> login)` |
