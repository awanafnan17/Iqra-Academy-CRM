# Route Registry & Exclusion Manifest

*Generated: 2026-06-20 02:44:40*

## Summary

| Metric | Count |
|--------|-------|
| Total registered URLs | 482 |
| Panel routes | 239 |
| Account routes | 7 |
| Portal routes | 32 |

## Classification Breakdown

| Type | Count |
|------|-------|
| ajax_json | 1 |
| create_form | 29 |
| destructive_post | 28 |
| export_download | 6 |
| parameterized_get | 87 |
| static_get | 108 |
| update_form | 19 |

## Exclusion Manifest

| Route Name | Pattern | Classification | Parameters | Reason Excluded | Separate Test |
|------------|---------|----------------|------------|-----------------|---------------|
| :admin_panel:users:user_toggle_activation | `/panel/admin/users/<int:pk>/toggle-activation/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:users:user_toggle_lock | `/panel/admin/users/<int:pk>/toggle-lock/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:users:user_reset_password | `/panel/admin/users/<int:pk>/reset-password/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:timetable_toggle_status | `/panel/admin/timetable/<int:pk>/toggle-status/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:student_reset_password | `/panel/admin/students/<int:pk>/reset-password/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:student_create_login | `/panel/admin/students/<int:pk>/create-login/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:students:student_delete | `/panel/admin/students/<int:pk>/delete/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:students:lead_convert | `/panel/admin/students/leads/<int:pk>/convert/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:academics:session_toggle_status | `/panel/admin/academics/sessions/<int:pk>/toggle-status/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:academics:session_delete | `/panel/admin/academics/sessions/<int:pk>/delete/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:academics:assignment_delete | `/panel/admin/academics/assignments/<int:pk>/delete/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:exams:exam_publish | `/panel/admin/exams/<int:pk>/publish/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:finance:payment_delete | `/panel/admin/finance/payments/<int:pk>/delete/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:finance:expense_approve | `/panel/admin/finance/expenses/<int:pk>/approve/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:finance:expense_reject | `/panel/admin/finance/expenses/<int:pk>/reject/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:notifications:notification_mark_read | `/panel/admin/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |
| :admin_panel:reports:export_students_csv | `/panel/admin/reports/export/students/` | export_download | False | Binary output; tested via Django client | Yes |
| :admin_panel:reports:export_payments_csv | `/panel/admin/reports/export/payments/` | export_download | False | Binary output; tested via Django client | Yes |
| :admin_panel:reports:export_attendance_csv | `/panel/admin/reports/export/attendance/` | export_download | False | Binary output; tested via Django client | Yes |
| :admin_panel:export_comparison_csv | `/panel/admin/pdf-comparison/export/<int:job_id>/` | export_download | True | Binary output; tested via Django client | Yes |
| :admin_panel:admissions:admission_approve | `/panel/admin/admissions/<int:pk>/approve/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:admissions:admission_reject | `/panel/admin/admissions/<int:pk>/reject/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:admissions:admission_convert | `/panel/admin/admissions/<int:pk>/convert/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :admin_panel:admissions:admission_export | `/panel/admin/admissions/export/` | export_download | False | Binary output; tested via Django client | Yes |
| :teacher_panel:notification_mark_read | `/panel/teacher/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |
| :accounts_panel:notification_mark_read | `/panel/accounts/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |
| :registrar_panel:lead_convert | `/panel/registrar/leads/<int:pk>/convert/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :registrar_panel:notification_mark_read | `/panel/registrar/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |
| :registrar_panel:admissions:admission_approve | `/panel/registrar/admissions/<int:pk>/approve/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :registrar_panel:admissions:admission_reject | `/panel/registrar/admissions/<int:pk>/reject/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :registrar_panel:admissions:admission_convert | `/panel/registrar/admissions/<int:pk>/convert/` | destructive_post | True | Modifies data; tested via Django client | Yes |
| :registrar_panel:admissions:admission_export | `/panel/registrar/admissions/export/` | export_download | False | Binary output; tested via Django client | Yes |
| :student_portal:notification_mark_read | `/portal/student/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |
| :guardian_portal:notification_mark_read | `/portal/guardian/notifications/mark-read/` | destructive_post | False | Modifies data; tested via Django client | Yes |

## Browser-Testable Routes (Static GET)

| Route Name | Pattern |
|------------|---------|
| :reports:dashboard | `/panel/admin/reports/` |
| :reports:pending_dues_csv | `/panel/admin/reports/pending-dues/csv/` |
| :reports:pending_dues_pdf | `/panel/admin/reports/pending-dues/pdf/` |
| :reports:student_directory_csv | `/panel/admin/reports/student-directory/csv/` |
| :reports:teacher_workload_csv | `/panel/admin/reports/teacher-workload/csv/` |
| :reports:teacher_workload_pdf | `/panel/admin/reports/teacher-workload/pdf/` |
| :reports:success_csv | `/panel/admin/reports/success/csv/` |
| :reports:success_pdf | `/panel/admin/reports/success/pdf/` |
| :admin_panel:dashboard | `/panel/admin/dashboard/` |
| :admin_panel:permissions | `/panel/admin/permissions/` |
| :admin_panel:session_overview | `/panel/admin/session-overview/` |
| :admin_panel:faculty_overview | `/panel/admin/faculty-overview/` |
| :admin_panel:timetable_overview | `/panel/admin/timetable-overview/` |
| :admin_panel:exam_overview | `/panel/admin/exam-overview/` |
| :admin_panel:success_dashboard | `/panel/admin/success/` |
| :admin_panel:pending_dues | `/panel/admin/pending-dues/` |
| :admin_panel:users:user_list | `/panel/admin/users/` |
| :admin_panel:timetable_list | `/panel/admin/timetable/` |
| :admin_panel:manage_students | `/panel/admin/manage-students/` |
| :admin_panel:session_list | `/panel/admin/sessions/` |
| :admin_panel:staff:faculty_list | `/panel/admin/manage-faculty/` |
| :admin_panel:analytics | `/panel/admin/analytics/` |
| :admin_panel:automation_alerts | `/panel/admin/automation/alerts/` |
| :admin_panel:automation_jobs | `/panel/admin/automation/jobs/` |
| :admin_panel:reports_dashboard | `/panel/admin/reports-dashboard/` |
| :admin_panel:students:student_list | `/panel/admin/students/` |
| :admin_panel:students:lead_list | `/panel/admin/students/leads/` |
| :admin_panel:students:enrollment_list | `/panel/admin/students/enrollments/` |
| :admin_panel:attendance:attendance_overview | `/panel/admin/attendance/` |
| :admin_panel:attendance:low_attendance_report | `/panel/admin/attendance/low-attendance/` |
| :admin_panel:exams:exam_list | `/panel/admin/exams/` |
| :admin_panel:exams:grade_config_list | `/panel/admin/exams/grade-config/` |
| :admin_panel:finance:payment_list | `/panel/admin/finance/payments/` |
| :admin_panel:finance:expense_list | `/panel/admin/finance/expenses/` |
| :admin_panel:finance:expense_category_list | `/panel/admin/finance/expenses/categories/` |
| :admin_panel:finance:refund_list | `/panel/admin/finance/refunds/` |
| :admin_panel:finance:installment_plan_list | `/panel/admin/finance/installments/` |
| :admin_panel:finance:overdue_list | `/panel/admin/finance/overdue/` |
| :admin_panel:finance:late_fee_apply | `/panel/admin/finance/late-fees/apply/` |
| :admin_panel:finance:send_fee_reminder | `/panel/admin/finance/send-fee-reminder/` |
| :admin_panel:notifications:notification_list | `/panel/admin/notifications/` |
| :admin_panel:notifications:notification_bulk_send | `/panel/admin/notifications/bulk-send/` |
| :admin_panel:notifications:template_list | `/panel/admin/notifications/templates/` |
| :admin_panel:notifications:email_log_list | `/panel/admin/notifications/email-logs/` |
|  | `/panel/admin/documents/` |
| :admin_panel:documents:comparison_job_list | `/panel/admin/documents/jobs/` |
| :admin_panel:ai_engine:prediction_list | `/panel/admin/ai/predictions/` |
| :admin_panel:ai_engine:model_version_list | `/panel/admin/ai/models/` |
| :admin_panel:ai_engine:dropout_risk_dashboard | `/panel/admin/ai/dropout-risk/` |
| :admin_panel:reports:report_revenue | `/panel/admin/reports/revenue/` |
| :admin_panel:reports:report_attendance | `/panel/admin/reports/attendance/` |
| :admin_panel:reports:report_enrollment | `/panel/admin/reports/enrollment/` |
| :admin_panel:reports:report_overdue | `/panel/admin/reports/overdue/` |
| :admin_panel:audit:audit_log_list | `/panel/admin/audit/` |
| :admin_panel:pdf_comparison | `/panel/admin/pdf-comparison/` |
| :admin_panel:admissions:admission_list | `/panel/admin/admissions/` |
| :admin_panel:admissions:admission_summary | `/panel/admin/admissions/summary/` |
| :principal_panel:dashboard | `/panel/principal/dashboard/` |
| :teacher_panel:dashboard | `/panel/teacher/dashboard/` |
| :teacher_panel:my_timetable | `/panel/teacher/my-timetable/` |
| :teacher_panel:my_sessions | `/panel/teacher/sessions/` |
| :teacher_panel:my_exams | `/panel/teacher/exams/` |
| :teacher_panel:notification_list | `/panel/teacher/notifications/` |
| :teacher_panel:profile_view | `/panel/teacher/profile/` |
| :accounts_panel:dashboard | `/panel/accounts/dashboard/` |
| :accounts_panel:pending_dues | `/panel/accounts/pending-dues/` |
| :accounts_panel:payment_list | `/panel/accounts/payments/` |
| :accounts_panel:expense_list | `/panel/accounts/expenses/` |
| :accounts_panel:refund_list | `/panel/accounts/refunds/` |
| :accounts_panel:installment_plan_list | `/panel/accounts/installments/` |
| :accounts_panel:overdue_list | `/panel/accounts/overdue/` |
| :accounts_panel:late_fee_apply | `/panel/accounts/late-fees/apply/` |
| :accounts_panel:late_fee_waive | `/panel/accounts/late-fees/waive/` |
| :accounts_panel:expense_category_list | `/panel/accounts/categories/` |
| :accounts_panel:reports_dashboard | `/panel/accounts/reports/` |
| :accounts_panel:pending_dues_csv | `/panel/accounts/reports/pending-dues/csv/` |
| :accounts_panel:pending_dues_pdf | `/panel/accounts/reports/pending-dues/pdf/` |
| :accounts_panel:report_revenue | `/panel/accounts/reports/revenue/` |
| :accounts_panel:report_overdue | `/panel/accounts/reports/overdue/` |
| :accounts_panel:notification_list | `/panel/accounts/notifications/` |
| :registrar_panel:dashboard | `/panel/registrar/dashboard/` |
| :registrar_panel:student_list | `/panel/registrar/students/` |
| :registrar_panel:lead_list | `/panel/registrar/leads/` |
| :registrar_panel:session_list | `/panel/registrar/sessions/` |
| :registrar_panel:notification_list | `/panel/registrar/notifications/` |
| :registrar_panel:admissions:admission_list | `/panel/registrar/admissions/` |
| :registrar_panel:admissions:admission_summary | `/panel/registrar/admissions/summary/` |
| :accounts:login | `/accounts/login/` |
| :accounts:logout | `/accounts/logout/` |
| :accounts:post_login_redirect | `/accounts/post-login/` |
| :accounts:password_change | `/accounts/password/change/` |
| :accounts:password_change_done | `/accounts/password/change/done/` |
| :accounts:profile_view | `/accounts/profile/` |
| :student_portal:dashboard | `/portal/student/dashboard/` |
| :student_portal:profile_view | `/portal/student/profile/` |
| :student_portal:my_enrollment | `/portal/student/enrollment/` |
| :student_portal:my_attendance | `/portal/student/attendance/` |
| :student_portal:my_exams | `/portal/student/exams/` |
| :student_portal:student_transcript | `/portal/student/transcript/` |
| :student_portal:student_transcript_pdf | `/portal/student/transcript/pdf/` |
| :student_portal:my_payments | `/portal/student/payments/` |
| :student_portal:my_fees | `/portal/student/fees/` |
| :student_portal:timetable | `/portal/student/timetable/` |
| :student_portal:notification_list | `/portal/student/notifications/` |
| :student_portal:password_change | `/portal/student/password/` |
| :guardian_portal:dashboard | `/portal/guardian/dashboard/` |
| :guardian_portal:my_children | `/portal/guardian/children/` |
| :guardian_portal:notification_list | `/portal/guardian/notifications/` |

## Parameterized Routes (Require Fixtures)

| Route Name | Pattern | View |
|------------|---------|------|
| :reports:session_results_csv | `/panel/admin/reports/session-results/<int:session_id>/csv/` | view |
| :reports:session_results_pdf | `/panel/admin/reports/session-results/<int:session_id>/pdf/` | view |
| :reports:student_transcript_pdf | `/panel/admin/reports/student/<int:student_id>/transcript/pdf/` | view |
| :admin_panel:session_result_summary | `/panel/admin/session/<int:pk>/results/` | session_result_summary |
| :admin_panel:users:user_assign_role | `/panel/admin/users/<int:pk>/assign-role/` | user_assign_role |
| :admin_panel:users:user_assign_session | `/panel/admin/users/<int:pk>/assign-session/` | user_assign_session |
| :admin_panel:session_detail | `/panel/admin/sessions/<int:pk>/` | session_detail |
| :admin_panel:session_result | `/panel/admin/sessions/<int:pk>/results/` | session_result_summary |
| :admin_panel:staff:faculty_assign | `/panel/admin/manage-faculty/<int:pk>/assign/` | view |
| :admin_panel:students:student_detail | `/panel/admin/students/<int:pk>/` | student_detail |
| :admin_panel:students:student_restore | `/panel/admin/students/<int:pk>/restore/` | student_restore |
| :admin_panel:students:student_documents | `/panel/admin/students/<int:pk>/documents/` | student_documents |
| :admin_panel:students:student_document_upload | `/panel/admin/students/<int:pk>/documents/upload/` | student_document_upload |
| :admin_panel:students:student_guardians | `/panel/admin/students/<int:pk>/guardians/` | student_guardians |
| :admin_panel:students:student_ledger | `/panel/admin/students/<int:pk>/ledger/` | student_ledger |
| :admin_panel:students:lead_detail | `/panel/admin/students/leads/<int:pk>/` | lead_detail |
| :admin_panel:students:enrollment_detail | `/panel/admin/students/enrollments/<int:pk>/` | enrollment_detail |
| :admin_panel:students:enrollment_withdraw | `/panel/admin/students/enrollments/<int:pk>/withdraw/` | enrollment_withdraw |
| :admin_panel:students:enrollment_restore | `/panel/admin/students/enrollments/<int:pk>/restore/` | enrollment_restore |
| :admin_panel:students:enrollment_freeze | `/panel/admin/students/enrollments/<int:pk>/freeze/` | enrollment_freeze |
| :admin_panel:students:enrollment_unfreeze | `/panel/admin/students/enrollments/<int:pk>/unfreeze/` | enrollment_unfreeze |
| :admin_panel:students:enrollment_transfer | `/panel/admin/students/enrollments/<int:pk>/transfer/` | enrollment_transfer |
| :admin_panel:academics:session_detail | `/panel/admin/academics/sessions/<int:pk>/` | session_detail |
| :admin_panel:academics:session_enrollments | `/panel/admin/academics/sessions/<int:pk>/enrollments/` | session_enrollments |
| :admin_panel:academics:session_revenue | `/panel/admin/academics/sessions/<int:pk>/revenue/` | session_revenue |
| :admin_panel:attendance:attendance_mark | `/panel/admin/attendance/mark/<int:session_id>/` | attendance_mark |
| :admin_panel:attendance:attendance_sheet | `/panel/admin/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet |
| :admin_panel:attendance:attendance_lock | `/panel/admin/attendance/<int:session_id>/lock/` | attendance_lock |
| :admin_panel:attendance:attendance_unlock | `/panel/admin/attendance/<int:session_id>/unlock/` | attendance_unlock |
| :admin_panel:attendance:attendance_analytics | `/panel/admin/attendance/<int:session_id>/analytics/` | attendance_analytics |
| :admin_panel:exams:exam_detail | `/panel/admin/exams/<int:pk>/` | view |
| :admin_panel:exams:exam_review | `/panel/admin/exams/<int:pk>/review/` | view |
| :admin_panel:exams:exam_results_entry | `/panel/admin/exams/<int:pk>/results/entry/` | view |
| :admin_panel:exams:exam_results_bulk_entry | `/panel/admin/exams/<int:pk>/results/bulk-entry/` | view |
| :admin_panel:exams:exam_statistics | `/panel/admin/exams/<int:pk>/statistics/` | view |
| :admin_panel:finance:payment_detail | `/panel/admin/finance/payments/<int:pk>/` | payment_detail |
| :admin_panel:finance:expense_detail | `/panel/admin/finance/expenses/<int:pk>/` | expense_detail |
| :admin_panel:finance:installment_plan_detail | `/panel/admin/finance/installments/<int:pk>/` | installment_plan_detail |
| :admin_panel:finance:installment_restructure | `/panel/admin/finance/installments/<int:pk>/restructure/` | installment_restructure |
| :admin_panel:finance:late_fee_waive | `/panel/admin/finance/late-fees/waive/<int:pk>/` | late_fee_waive |
| :admin_panel:notifications:notification_detail | `/panel/admin/notifications/<int:pk>/` | view |
| :admin_panel:documents:comparison_job_detail | `/panel/admin/documents/jobs/<int:pk>/` | pdf_comparison |
| :admin_panel:documents:comparison_results | `/panel/admin/documents/jobs/<int:pk>/results/` | pdf_comparison |
| :admin_panel:ai_engine:prediction_detail | `/panel/admin/ai/predictions/<int:pk>/` | prediction_detail |
| :admin_panel:ai_engine:prediction_acknowledge | `/panel/admin/ai/predictions/<int:pk>/acknowledge/` | prediction_acknowledge |
| :admin_panel:reports:pdf_student_ledger | `/panel/admin/reports/pdf/ledger/<int:enrollment_id>/` | pdf_student_ledger |
| :admin_panel:reports:pdf_attendance_report | `/panel/admin/reports/pdf/attendance/<int:session_id>/` | pdf_attendance_report |
| :admin_panel:audit:audit_log_detail | `/panel/admin/audit/<int:pk>/` | audit_log_detail |
| :admin_panel:admissions:admission_detail | `/panel/admin/admissions/<int:pk>/` | view |
| :admin_panel:admissions:admission_review | `/panel/admin/admissions/<int:pk>/review/` | view |
| :teacher_panel:session_detail | `/panel/teacher/sessions/<int:pk>/` | teacher_session_detail |
| :teacher_panel:session_students | `/panel/teacher/sessions/<int:pk>/students/` | teacher_session_students |
| :teacher_panel:attendance_mark | `/panel/teacher/attendance/mark/<int:session_id>/` | attendance_mark |
| :teacher_panel:attendance_sheet | `/panel/teacher/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet |
| :teacher_panel:attendance_analytics | `/panel/teacher/attendance/<int:session_id>/analytics/` | attendance_analytics |
| :teacher_panel:exam_detail | `/panel/teacher/exams/<int:pk>/` | view |
| :teacher_panel:exam_results_entry | `/panel/teacher/exams/<int:pk>/results/entry/` | view |
| :teacher_panel:exam_results | `/panel/teacher/exams/<int:pk>/results/` | view |
| :teacher_panel:notification_detail | `/panel/teacher/notifications/<int:pk>/` | view |
| :accounts_panel:payment_detail | `/panel/accounts/payments/<int:pk>/` | payment_detail |
| :accounts_panel:expense_detail | `/panel/accounts/expenses/<int:pk>/` | expense_detail |
| :accounts_panel:installment_plan_detail | `/panel/accounts/installments/<int:pk>/` | installment_plan_detail |
| :accounts_panel:installment_restructure | `/panel/accounts/installments/<int:pk>/restructure/` | installment_restructure |
| :accounts_panel:student_ledger | `/panel/accounts/students/<int:pk>/ledger/` | student_ledger |
| :registrar_panel:student_detail | `/panel/registrar/students/<int:pk>/` | student_detail |
| :registrar_panel:student_document_upload | `/panel/registrar/students/<int:pk>/documents/upload/` | student_document_upload |
| :registrar_panel:student_guardians | `/panel/registrar/students/<int:pk>/guardians/` | student_guardians |
| :registrar_panel:lead_detail | `/panel/registrar/leads/<int:pk>/` | lead_detail |
| :registrar_panel:enrollment_detail | `/panel/registrar/enrollments/<int:pk>/` | enrollment_detail |
| :registrar_panel:session_detail | `/panel/registrar/sessions/<int:pk>/` | session_detail |
| :registrar_panel:admissions:admission_detail | `/panel/registrar/admissions/<int:pk>/` | view |
| :registrar_panel:admissions:admission_review | `/panel/registrar/admissions/<int:pk>/review/` | view |
| :student_portal:exam_result_detail | `/portal/student/exams/<int:pk>/` | exam_result_detail |
| :student_portal:download_receipt | `/portal/student/fees/<int:payment_id>/receipt/` | view |
| :student_portal:notification_detail | `/portal/student/notifications/<int:pk>/` | view |
| :guardian_portal:child_detail | `/portal/guardian/child/<int:student_id>/profile/` | view |
| :guardian_portal:child_attendance | `/portal/guardian/child/<int:student_id>/attendance/` | view |
| :guardian_portal:child_payments | `/portal/guardian/child/<int:student_id>/fees/` | view |
| :guardian_portal:child_exams | `/portal/guardian/child/<int:student_id>/exams/` | view |
| :guardian_portal:child_transcript | `/portal/guardian/child/<int:student_id>/transcript/` | child_transcript |
| :guardian_portal:child_transcript_pdf | `/portal/guardian/child/<int:student_id>/transcript/pdf/` | view |
| :guardian_portal:download_receipt | `/portal/guardian/child/<int:student_id>/fees/<int:payment_id>/receipt/` | view |
| :guardian_portal:child_detail_old | `/portal/guardian/children/<int:student_id>/` | view |
| :guardian_portal:child_attendance_old | `/portal/guardian/children/<int:student_id>/attendance/` | view |
| :guardian_portal:child_payments_old | `/portal/guardian/children/<int:student_id>/payments/` | view |
| :guardian_portal:child_exams_old | `/portal/guardian/children/<int:student_id>/exams/` | view |
| :guardian_portal:notification_detail | `/portal/guardian/notifications/<int:pk>/` | view |

## Accounting Verification

```
Total panel+account+portal routes: 278
  ajax_json: 1
  create_form: 29
  destructive_post: 28
  export_download: 6
  parameterized_get: 87
  static_get: 108
  update_form: 19
  Total accounted: 278
  Unclassified: 0
```