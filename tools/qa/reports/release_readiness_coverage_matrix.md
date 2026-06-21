# CRM Release-Readiness Coverage Matrix

This matrix maps each CRM domain module to its database models, forms, templates, routes, and the roles with access permissions.

---

## Module Coverage Grid

| Module | Core Models | Forms | Templates | Core Routes | Allowed Roles | Audit Status / Finding |
|---|---|---|---|---|---|---|
| **Accounts** | `CustomUser`, `UserProfile` | `UserProfileForm`, `LoginForm`, `PasswordChangeForm` | `accounts/profile.html`, `registration/login.html` | `/accounts/profile/`, `/accounts/login/` | All roles | **PASS**: Form validations and login flows verified. |
| **Academics** | `Session`, `Subject`, `TeacherAssignment`, `ClassSchedule` | `SessionForm`, `ClassScheduleForm` | `academics/session_form.html`, `academics/session_detail.html`, `academics/timetable_list.html` | `/panel/admin/academics/sessions/`, `/panel/admin/timetable/` | Admin, Principal, Registrar, Teacher | **CRITICAL BUG**: Lowercase status="active" in StudentCreateForm (RR-013). Multiple views are stubbed (RR-002). |
| **Admissions** | `AdmissionApplication` | `AdmissionApplicationForm` | `admissions/public_form.html`, `admissions/admission_list.html`, `admissions/admission_detail.html` | `/apply/`, `/panel/admin/admissions/` | Admin, Principal, Registrar, Anonymous | **CRITICAL BUG**: CBVs return 405 on GET instead of 404 (RR-001). |
| **Attendance** | `AttendanceRecord`, `AttendanceLock` | None | None | `/panel/admin/attendance/` | Admin, Principal, Teacher, Student, Guardian | **CRITICAL BUG**: Attendance views are plain text stubs (RR-003). |
| **Exams** | `Exam`, `ExamResult`, `GradeConfig` | `ExamForm`, `ExamResultForm` | `exams/exam_list.html`, `exams/exam_detail.html`, `exams/bulk_result_entry.html` | `/panel/admin/exams/` | Admin, Principal, Teacher, Student, Guardian | **CRITICAL BUG**: Grade config views are stubs (RR-004). |
| **Finance** | `Payment`, `Refund`, `InstallmentPlan`, `Installment`, `Expense`, `ExpenseCategory` | `PaymentForm`, `ExpenseForm` | `finance/payment_list.html`, `finance/payment_detail.html`, `finance/ledger.html` | `/panel/accounts/payments/`, `/panel/admin/finance/` | Admin, Principal, Accountant | **PASS**: Installments, ledger calculations, and rate limits verified. |
| **Documents** | `ComparisonJob`, `ComparisonResult`, `StudentDocument` | None | `documents/pdf_comparison.html` | `/panel/admin/pdf-comparison/`, `/panel/admin/documents/jobs/` | Admin, Principal, Registrar | **HIGH BUG**: Trailing slash path bypass (RR-007) and Hardcoded template URLs (RR-009). |
| **Reports** | None | None | `reports/reports_dashboard.html`, `reports/student_transcript_pdf.html` | `/panel/admin/reports/` | Admin, Principal, Accountant, Student, Guardian | **HIGH BUG**: Reports mounted twice (RR-008). N+1 query loops in PDF views (RR-010, RR-011). Registrar transcript block (RR-014). |
| **Portals** | None | None | `portals/student_dashboard.html`, `portals/guardian_dashboard.html` | `/portal/student/`, `/portal/guardian/` | Student, Guardian | **PASS**: Portal isolation and data boundaries verified. |
| **Students** | `Student`, `Guardian` | `StudentForm`, `StudentCreateForm`, `GuardianForm` | `students/student_list.html`, `students/student_detail.html`, `students/student_form.html` | `/panel/admin/students/` | Admin, Principal, Registrar, Student, Guardian | **CRITICAL BUG**: Missing pagination on student directory list (RR-012). |
