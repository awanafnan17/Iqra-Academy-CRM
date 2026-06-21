# CRM-Wide Coverage Matrix

*Generated: 2026-06-21 01:56:22*

## Discovery Coverage Summary
- **Models Discovered**: 37 (Audited: 24)
- **Forms Discovered**: 19 (Audited: 19)
- **Routes Discovered**: 277 (Audited: 87)
- **Templates Discovered**: 124 (Audited: 110)

## Models Discovered vs Audited
| Model Label | Classification | Status | Coverage Check Reason |
|---|---|---|---|
| `academics.ClassSchedule` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `academics.Session` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `academics.Subject` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `academics.TeacherAssignment` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `accounts.CustomUser` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `accounts.UserProfile` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `achievements.Achievement` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `admissions.AdmissionApplication` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `admissions.AdmissionDocument` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `ai_engine.ModelVersion` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `ai_engine.PredictionLog` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `attendance.AttendanceLock` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `attendance.AttendanceRecord` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `core.AuditLog` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `core.RolePermission` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `documents.ComparisonJob` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `documents.ComparisonResult` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `exams.Exam` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `exams.ExamResult` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `exams.GradeConfig` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.Expense` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.ExpenseCategory` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.FeeStructure` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `finance.Installment` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.InstallmentPlan` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.Payment` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `finance.Refund` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `notifications.EmailLog` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `notifications.Notification` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `notifications.NotificationTemplate` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `staff.FacultyProfile` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `students.Enrollment` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `students.Guardian` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `students.Lead` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `students.Student` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |
| `students.StudentAchievement` | model | **UNAUDITED** | No behavioral or state persistence tests cover this model under tools/qa/. |
| `students.StudentDocument` | model | **AUDITED** | Explicitly referenced and asserted in the QA test suite. |

## Forms Discovered vs Audited
| Form Class | Classification | Status | Coverage Check Reason |
|---|---|---|---|
| `academics.ClassScheduleForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `academics.SessionForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `accounts.UserProfileForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `admissions.AdmissionApplicationForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `finance.ExpenseCategoryForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `finance.ExpenseForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `finance.InstallmentPlanForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `finance.PaymentForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `finance.RefundForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `notifications.NotificationTemplateForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `staff.FacultyAssignSessionForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `staff.FacultyProfileForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `staff.UserCreateForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.EnrollmentForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.GuardianForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.LeadForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.StudentCreateForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.StudentDocumentForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |
| `students.StudentForm` | form | **AUDITED** | Form fields and mutation tests verify data propagation. |

## Routes Discovered vs Audited
| URL Pattern | Route Name | Classification | Status | Coverage Check Reason |
|---|---|---|---|---|
| `/accounts/login/` | login | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/accounts/logout/` | logout | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/accounts/password/change/` | password_change | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/accounts/password/change/done/` | password_change_done | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/accounts/post-login/` | post_login_redirect | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/accounts/profile/` | profile_view | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/accounts/profile/edit/` | profile_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/categories/` | expense_category_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/categories/create/` | expense_category_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/expenses/` | expense_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/expenses/<int:pk>/` | expense_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/expenses/create/` | expense_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/installments/` | installment_plan_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/installments/<int:pk>/` | installment_plan_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/installments/<int:pk>/pay/` | installment_pay | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/installments/<int:pk>/restructure/` | installment_restructure | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/installments/create/` | installment_plan_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/late-fees/apply/` | late_fee_apply | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/late-fees/waive/` | late_fee_waive | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/notifications/` | notification_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/overdue/` | overdue_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/payments/` | payment_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/payments/<int:pk>/` | payment_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/payments/create/` | payment_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/pending-dues/` | pending_dues | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/refunds/` | refund_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/refunds/create/` | refund_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/reports/` | reports_dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/accounts/reports/overdue/` | report_overdue | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/reports/pending-dues/csv/` | pending_dues_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/reports/pending-dues/pdf/` | pending_dues_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/reports/revenue/` | report_revenue | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/accounts/students/<int:pk>/ledger/` | student_ledger | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/assignments/<int:pk>/delete/` | assignment_delete | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/assignments/<int:pk>/edit/` | assignment_edit | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/assignments/create/` | assignment_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/academics/sessions/<int:pk>/` | session_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/sessions/<int:pk>/delete/` | session_delete | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/sessions/<int:pk>/edit/` | session_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/academics/sessions/<int:pk>/enrollments/` | session_enrollments | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/sessions/<int:pk>/revenue/` | session_revenue | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/sessions/<int:pk>/toggle-status/` | session_toggle_status | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/sessions/create/` | session_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/academics/subjects/<int:pk>/edit/` | subject_edit | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/academics/subjects/create/` | subject_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/add-session/` | add_session | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/add-student/` | add_student | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/admissions/` | admission_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/admissions/<int:pk>/` | admission_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/<int:pk>/approve/` | admission_approve | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/<int:pk>/convert/` | admission_convert | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/<int:pk>/reject/` | admission_reject | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/<int:pk>/review/` | admission_review | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/export/` | admission_export | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/admissions/summary/` | admission_summary | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/ai/dropout-risk/` | dropout_risk_dashboard | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/ai/models/` | model_version_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/ai/predictions/` | prediction_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/ai/predictions/<int:pk>/` | prediction_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/ai/predictions/<int:pk>/acknowledge/` | prediction_acknowledge | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/analytics/` | analytics | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/attendance/` | attendance_overview | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/attendance/<int:session_id>/analytics/` | attendance_analytics | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/attendance/<int:session_id>/lock/` | attendance_lock | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/attendance/<int:session_id>/unlock/` | attendance_unlock | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/attendance/low-attendance/` | low_attendance_report | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/attendance/mark/<int:session_id>/` | attendance_mark | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/audit/` | audit_log_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/audit/<int:pk>/` | audit_log_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/automation/alerts/` | automation_alerts | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/automation/jobs/` | automation_jobs | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/documents/` |  | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/documents/jobs/` | comparison_job_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/documents/jobs/<int:pk>/` | comparison_job_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/documents/jobs/<int:pk>/results/` | comparison_results | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/documents/jobs/create/` | comparison_job_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exam-overview/` | exam_overview | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/exams/` | exam_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/exams/<int:pk>/` | exam_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/<int:pk>/edit/` | exam_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/exams/<int:pk>/publish/` | exam_publish | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/<int:pk>/results/bulk-entry/` | exam_results_bulk_entry | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/<int:pk>/results/entry/` | exam_results_entry | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/<int:pk>/review/` | exam_review | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/<int:pk>/statistics/` | exam_statistics | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/create/` | exam_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/grade-config/` | grade_config_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/grade-config/<int:pk>/edit/` | grade_config_edit | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/exams/grade-config/create/` | grade_config_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/faculty-overview/` | faculty_overview | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/` | expense_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/expenses/<int:pk>/` | expense_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/<int:pk>/approve/` | expense_approve | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/<int:pk>/reject/` | expense_reject | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/categories/` | expense_category_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/categories/create/` | expense_category_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/expenses/create/` | expense_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/installments/` | installment_plan_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/installments/<int:pk>/` | installment_plan_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/installments/<int:pk>/pay/` | installment_pay | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/installments/<int:pk>/restructure/` | installment_restructure | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/installments/create/` | installment_plan_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/installments/pay/<int:pk>/` | installment_pay | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/late-fees/apply/` | late_fee_apply | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/late-fees/waive/<int:pk>/` | late_fee_waive | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/overdue/` | overdue_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/payments/` | payment_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/payments/<int:pk>/` | payment_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/payments/<int:pk>/delete/` | payment_delete | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/finance/payments/create/` | payment_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/refunds/` | refund_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/refunds/create/` | refund_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/finance/send-fee-reminder/` | send_fee_reminder | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/manage-faculty/` | faculty_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/manage-faculty/<int:pk>/assign/` | faculty_assign | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/manage-faculty/create/` | faculty_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/manage-students/` | manage_students | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/notifications/` | notification_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/notifications/<int:pk>/` | notification_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/notifications/bulk-send/` | notification_bulk_send | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/notifications/email-logs/` | email_log_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/notifications/templates/` | template_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/notifications/templates/<int:pk>/edit/` | template_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/notifications/templates/create/` | template_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/notifications/unread-count/` | unread_count_api | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/pdf-comparison/` | pdf_comparison | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/pdf-comparison/export/<int:job_id>/` | export_comparison_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/pending-dues/` | pending_dues | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/permissions/` | permissions | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/reports-dashboard/` | reports_dashboard | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/reports/attendance/` | report_attendance | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/enrollment/` | report_enrollment | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/export/attendance/` | export_attendance_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/export/payments/` | export_payments_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/export/students/` | export_students_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/overdue/` | report_overdue | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/pdf/attendance/<int:session_id>/` | pdf_attendance_report | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/pdf/ledger/<int:enrollment_id>/` | pdf_student_ledger | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/pending-dues/csv/` | pending_dues_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/pending-dues/pdf/` | pending_dues_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/revenue/` | report_revenue | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/session-results/<int:session_id>/csv/` | session_results_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/session-results/<int:session_id>/pdf/` | session_results_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/student-directory/csv/` | student_directory_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/student/<int:student_id>/transcript/pdf/` | student_transcript_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/success/csv/` | success_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/success/pdf/` | success_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/teacher-workload/csv/` | teacher_workload_csv | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/reports/teacher-workload/pdf/` | teacher_workload_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/session-overview/` | session_overview | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/session/<int:pk>/results/` | session_result_summary | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/sessions/` | session_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/sessions/<int:pk>/` | session_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/sessions/<int:pk>/edit/` | session_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/sessions/<int:pk>/results/` | session_result | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/sessions/create/` | session_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/` | student_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/<int:pk>/` | student_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/create-login/` | student_create_login | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/delete/` | student_delete | route | **PARTIALLY AUDITED** | Exclusion manifest applies; verified separately via client requests to prevent session disruption. |
| `/panel/admin/students/<int:pk>/documents/` | student_documents | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/documents/upload/` | student_document_upload | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/edit/` | student_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/<int:pk>/guardians/` | student_guardians | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/ledger/` | student_ledger | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/reset-password/` | student_reset_password | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/<int:pk>/restore/` | student_restore | route | **PARTIALLY AUDITED** | Exclusion manifest applies; verified separately via client requests to prevent session disruption. |
| `/panel/admin/students/create/` | student_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/enrollments/` | enrollment_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/enrollments/<int:pk>/` | enrollment_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/<int:pk>/freeze/` | enrollment_freeze | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/<int:pk>/restore/` | enrollment_restore | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/<int:pk>/transfer/` | enrollment_transfer | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/<int:pk>/unfreeze/` | enrollment_unfreeze | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/<int:pk>/withdraw/` | enrollment_withdraw | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/enrollments/create/` | enrollment_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/students/leads/` | lead_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/leads/<int:pk>/` | lead_detail | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/leads/<int:pk>/convert/` | lead_convert | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/leads/<int:pk>/edit/` | lead_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/students/leads/create/` | lead_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/success/` | success_dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/timetable-overview/` | timetable_overview | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/timetable/` | timetable_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/timetable/<int:pk>/edit/` | timetable_edit | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/timetable/<int:pk>/toggle-status/` | timetable_toggle_status | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/timetable/create/` | timetable_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/users/` | user_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/admin/users/<int:pk>/assign-role/` | user_assign_role | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/users/<int:pk>/assign-session/` | user_assign_session | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/users/<int:pk>/reset-password/` | user_reset_password | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/users/<int:pk>/toggle-activation/` | user_toggle_activation | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/admin/users/<int:pk>/toggle-lock/` | user_toggle_lock | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/principal/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/admissions/` | admission_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/<int:pk>/` | admission_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/<int:pk>/approve/` | admission_approve | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/<int:pk>/convert/` | admission_convert | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/<int:pk>/reject/` | admission_reject | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/<int:pk>/review/` | admission_review | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/export/` | admission_export | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/admissions/summary/` | admission_summary | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/enrollments/<int:pk>/` | enrollment_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/enrollments/create/` | enrollment_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/leads/` | lead_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/leads/<int:pk>/` | lead_detail | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/leads/<int:pk>/convert/` | lead_convert | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/leads/<int:pk>/edit/` | lead_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/leads/create/` | lead_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/notifications/` | notification_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/sessions/` | session_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/sessions/<int:pk>/` | session_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/students/` | student_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/students/<int:pk>/` | student_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/students/<int:pk>/documents/upload/` | student_document_upload | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/students/<int:pk>/edit/` | student_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/registrar/students/<int:pk>/guardians/` | student_guardians | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/registrar/students/create/` | student_create | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/attendance/<int:session_id>/analytics/` | attendance_analytics | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/attendance/mark/<int:session_id>/` | attendance_mark | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/exams/` | my_exams | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/exams/<int:pk>/` | exam_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/exams/<int:pk>/edit/` | exam_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/exams/<int:pk>/results/` | exam_results | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/exams/<int:pk>/results/entry/` | exam_results_entry | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/exams/create/` | exam_create | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/my-timetable/` | my_timetable | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/notifications/` | notification_list | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/notifications/<int:pk>/` | notification_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/profile/` | profile_view | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/profile/edit/` | profile_edit | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/sessions/` | my_sessions | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/panel/teacher/sessions/<int:pk>/` | session_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/panel/teacher/sessions/<int:pk>/students/` | session_students | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/attendance/` | child_attendance | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/exams/` | child_exams | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/fees/` | child_payments | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/fees/<int:payment_id>/receipt/` | download_receipt | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/profile/` | child_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/transcript/` | child_transcript | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/child/<int:student_id>/transcript/pdf/` | child_transcript_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/children/` | my_children | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/children/<int:student_id>/` | child_detail_old | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/children/<int:student_id>/attendance/` | child_attendance_old | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/children/<int:student_id>/exams/` | child_exams_old | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/children/<int:student_id>/payments/` | child_payments_old | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/portal/guardian/notifications/` | notification_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/notifications/<int:pk>/` | notification_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/guardian/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/attendance/` | my_attendance | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/dashboard/` | dashboard | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/portal/student/enrollment/` | my_enrollment | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/exams/` | my_exams | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/exams/<int:pk>/` | exam_result_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/fees/` | my_fees | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/fees/<int:payment_id>/receipt/` | download_receipt | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/notifications/` | notification_list | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/notifications/<int:pk>/` | notification_detail | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/notifications/mark-read/` | notification_mark_read | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/password/` | password_change | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/portal/student/payments/` | my_payments | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/profile/` | profile_view | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/portal/student/timetable/` | timetable | route | **AUDITED** | Accessed or asserted in crawler or authentication matrix. |
| `/portal/student/transcript/` | student_transcript | route | **UNAUDITED** | No automated test makes requests to this route. |
| `/portal/student/transcript/pdf/` | student_transcript_pdf | route | **UNAUDITED** | No automated test makes requests to this route. |

## Templates Discovered vs Audited
| Template Path | Classification | Status | Coverage Check Reason |
|---|---|---|---|
| `academics/session_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `academics/session_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `academics/session_list.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `academics/timetable_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `academics/timetable_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `academics/timetable_student.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `academics/timetable_teacher.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `accounts/login.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `accounts/password_change.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `accounts/password_change_done.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `accounts/profile.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `accounts/user_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `admissions/admission_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `admissions/admission_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `admissions/admission_summary.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `admissions/public_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `admissions/public_success.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `components/card.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `components/form.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `components/modal.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `components/navbar.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `components/sidebar.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `components/table.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `dashboard/accountant.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/admin.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/analytics.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/automation_alerts.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/automation_jobs.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/exam_overview.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/faculty_overview.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/module_placeholder.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `dashboard/permissions.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/placeholder_modules.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `dashboard/principal.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/registrar.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/session_overview.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/success_dashboard.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/teacher.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/teacher_session_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/teacher_session_students.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/teacher_sessions.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `dashboard/timetable_overview.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `documents/pdf_comparison.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/admission_approved.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/admission_rejected.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/admission_welcome.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/base_email.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `emails/fee_reminder.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/general_email.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/low_attendance.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `emails/upcoming_exam.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `errors/404.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `errors/500.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/bulk_result_entry.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/exam_create.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/exam_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/exam_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/exam_statistics.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/result_entry.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/session_results.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `exams/transcript.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/expense_category_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/expense_category_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/expense_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/expense_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/expense_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/installment_plan_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/installment_plan_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/installment_plan_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/installment_plan_restructure.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/overdue_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/payment_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/payment_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/payment_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/pending_dues.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/refund_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `finance/refund_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `layouts/base.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `layouts/panel_base.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `layouts/portal_base.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `notifications/bulk_send_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `notifications/email_log_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `notifications/notification_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `notifications/notification_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `notifications/template_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `notifications/template_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `pages/dashboard_base.html` | template | **UNAUDITED** | Template exists in files but view mapping is missing or unused. |
| `portal/guardian_child_attendance.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/guardian_child_exams.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/guardian_child_fees.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/guardian_child_profile.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/guardian_children.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/guardian_dashboard.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/notification_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/notification_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/password_change.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/payment_receipt_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/student_attendance.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/student_dashboard.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/student_exams.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/student_fees.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `portal/student_profile.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `public/success_stories.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/pending_dues_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/reports_dashboard.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/session_results_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/student_transcript_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/success_report_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `reports/teacher_workload_pdf.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `staff/faculty_assign.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `staff/faculty_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `staff/faculty_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/enrollment_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/enrollment_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/enrollment_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/lead_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/lead_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/lead_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_detail.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_documents.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_form.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_guardians.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_ledger.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |
| `students/student_list.html` | template | **AUDITED** | Template file exists and is rendered by at least one view. |

## Audited Roles & Workflows
- **Roles Audited**: Admin, Principal, Registrar, Accountant, Teacher, Student, Guardian
- **Workflows Audited**: Student Admissions, Student Enrollment, Installments Fee Schedules, Late Fee Penalties & Waivers, Financial Revenue & Refunds
- **Reports & PDF Templates Audited**: Student Transcript PDF, Expense Reports, Daily/Weekly/Monthly Admissions Feature
- **Visual Pages Audited (Viewports 1440, 1024, 768, 375)**: Login Page, Admin Dashboard, Student Details Portal, Permission Control Grid