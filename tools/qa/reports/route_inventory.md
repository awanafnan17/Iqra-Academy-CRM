# Route Inventory — Iqra Academy CRM

*Generated: 2026-06-21 05:08:09*

**Total routes discovered: 485**

## Summary by Module

| Module | Routes | Parameterized | Static |
|--------|--------|--------------|--------|
|  | 483 | 251 | 232 |
| root | 2 | 0 | 2 |

## Detailed Route Listing

### 

| Path | View | URL Name | Methods | Params |
|------|------|----------|---------|--------|
| `/accounts/login/` | LoginView | :accounts:login | GET, POST, PUT |  |
| `/accounts/logout/` | LogoutView | :accounts:logout | GET, POST |  |
| `/accounts/password/change/` | PasswordChangeView | :accounts:password_change | GET, POST, PUT |  |
| `/accounts/password/change/done/` | PasswordChangeDoneView | :accounts:password_change_done | GET |  |
| `/accounts/post-login/` | post_login_redirect | :accounts:post_login_redirect | GET, POST |  |
| `/accounts/profile/` | profile_view | :accounts:profile_view | GET, POST |  |
| `/accounts/profile/edit/` | profile_edit | :accounts:profile_edit | GET, POST |  |
| `/admin/` | index | :admin:index | GET, POST |  |
| `/admin/(?P<url>.*)$` | catch_all_view |  | GET, POST | ✓ |
| `/admin/^(?P<app_label>auth\|core\|accounts\|academics\|students\|finance\|attendance\|exams\|notifications\|documents\|ai_engine)/$` | app_index | :admin:app_list | GET, POST | ✓ |
| `/admin/academics/session/` | changelist_view | :admin:academics_session_changelist | GET, POST |  |
| `/admin/academics/session/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/academics/session/<path:object_id>/change/` | change_view | :admin:academics_session_change | GET, POST | ✓ |
| `/admin/academics/session/<path:object_id>/delete/` | delete_view | :admin:academics_session_delete | GET, POST | ✓ |
| `/admin/academics/session/<path:object_id>/history/` | history_view | :admin:academics_session_history | GET, POST | ✓ |
| `/admin/academics/session/add/` | add_view | :admin:academics_session_add | GET, POST |  |
| `/admin/academics/subject/` | changelist_view | :admin:academics_subject_changelist | GET, POST |  |
| `/admin/academics/subject/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/academics/subject/<path:object_id>/change/` | change_view | :admin:academics_subject_change | GET, POST | ✓ |
| `/admin/academics/subject/<path:object_id>/delete/` | delete_view | :admin:academics_subject_delete | GET, POST | ✓ |
| `/admin/academics/subject/<path:object_id>/history/` | history_view | :admin:academics_subject_history | GET, POST | ✓ |
| `/admin/academics/subject/add/` | add_view | :admin:academics_subject_add | GET, POST |  |
| `/admin/academics/teacherassignment/` | changelist_view | :admin:academics_teacherassignment_changelist | GET, POST |  |
| `/admin/academics/teacherassignment/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/academics/teacherassignment/<path:object_id>/change/` | change_view | :admin:academics_teacherassignment_change | GET, POST | ✓ |
| `/admin/academics/teacherassignment/<path:object_id>/delete/` | delete_view | :admin:academics_teacherassignment_delete | GET, POST | ✓ |
| `/admin/academics/teacherassignment/<path:object_id>/history/` | history_view | :admin:academics_teacherassignment_history | GET, POST | ✓ |
| `/admin/academics/teacherassignment/add/` | add_view | :admin:academics_teacherassignment_add | GET, POST |  |
| `/admin/accounts/customuser/` | changelist_view | :admin:accounts_customuser_changelist | GET, POST |  |
| `/admin/accounts/customuser/<id>/password/` | user_change_password | :admin:auth_user_password_change | GET, POST | ✓ |
| `/admin/accounts/customuser/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/accounts/customuser/<path:object_id>/change/` | change_view | :admin:accounts_customuser_change | GET, POST | ✓ |
| `/admin/accounts/customuser/<path:object_id>/delete/` | delete_view | :admin:accounts_customuser_delete | GET, POST | ✓ |
| `/admin/accounts/customuser/<path:object_id>/history/` | history_view | :admin:accounts_customuser_history | GET, POST | ✓ |
| `/admin/accounts/customuser/add/` | add_view | :admin:accounts_customuser_add | GET, POST |  |
| `/admin/accounts/userprofile/` | changelist_view | :admin:accounts_userprofile_changelist | GET, POST |  |
| `/admin/accounts/userprofile/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/accounts/userprofile/<path:object_id>/change/` | change_view | :admin:accounts_userprofile_change | GET, POST | ✓ |
| `/admin/accounts/userprofile/<path:object_id>/delete/` | delete_view | :admin:accounts_userprofile_delete | GET, POST | ✓ |
| `/admin/accounts/userprofile/<path:object_id>/history/` | history_view | :admin:accounts_userprofile_history | GET, POST | ✓ |
| `/admin/accounts/userprofile/add/` | add_view | :admin:accounts_userprofile_add | GET, POST |  |
| `/admin/ai_engine/modelversion/` | changelist_view | :admin:ai_engine_modelversion_changelist | GET, POST |  |
| `/admin/ai_engine/modelversion/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/ai_engine/modelversion/<path:object_id>/change/` | change_view | :admin:ai_engine_modelversion_change | GET, POST | ✓ |
| `/admin/ai_engine/modelversion/<path:object_id>/delete/` | delete_view | :admin:ai_engine_modelversion_delete | GET, POST | ✓ |
| `/admin/ai_engine/modelversion/<path:object_id>/history/` | history_view | :admin:ai_engine_modelversion_history | GET, POST | ✓ |
| `/admin/ai_engine/modelversion/add/` | add_view | :admin:ai_engine_modelversion_add | GET, POST |  |
| `/admin/ai_engine/predictionlog/` | changelist_view | :admin:ai_engine_predictionlog_changelist | GET, POST |  |
| `/admin/ai_engine/predictionlog/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/ai_engine/predictionlog/<path:object_id>/change/` | change_view | :admin:ai_engine_predictionlog_change | GET, POST | ✓ |
| `/admin/ai_engine/predictionlog/<path:object_id>/delete/` | delete_view | :admin:ai_engine_predictionlog_delete | GET, POST | ✓ |
| `/admin/ai_engine/predictionlog/<path:object_id>/history/` | history_view | :admin:ai_engine_predictionlog_history | GET, POST | ✓ |
| `/admin/ai_engine/predictionlog/add/` | add_view | :admin:ai_engine_predictionlog_add | GET, POST |  |
| `/admin/attendance/attendancelock/` | changelist_view | :admin:attendance_attendancelock_changelist | GET, POST |  |
| `/admin/attendance/attendancelock/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/attendance/attendancelock/<path:object_id>/change/` | change_view | :admin:attendance_attendancelock_change | GET, POST | ✓ |
| `/admin/attendance/attendancelock/<path:object_id>/delete/` | delete_view | :admin:attendance_attendancelock_delete | GET, POST | ✓ |
| `/admin/attendance/attendancelock/<path:object_id>/history/` | history_view | :admin:attendance_attendancelock_history | GET, POST | ✓ |
| `/admin/attendance/attendancelock/add/` | add_view | :admin:attendance_attendancelock_add | GET, POST |  |
| `/admin/attendance/attendancerecord/` | changelist_view | :admin:attendance_attendancerecord_changelist | GET, POST |  |
| `/admin/attendance/attendancerecord/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/attendance/attendancerecord/<path:object_id>/change/` | change_view | :admin:attendance_attendancerecord_change | GET, POST | ✓ |
| `/admin/attendance/attendancerecord/<path:object_id>/delete/` | delete_view | :admin:attendance_attendancerecord_delete | GET, POST | ✓ |
| `/admin/attendance/attendancerecord/<path:object_id>/history/` | history_view | :admin:attendance_attendancerecord_history | GET, POST | ✓ |
| `/admin/attendance/attendancerecord/add/` | add_view | :admin:attendance_attendancerecord_add | GET, POST |  |
| `/admin/auth/group/` | changelist_view | :admin:auth_group_changelist | GET, POST |  |
| `/admin/auth/group/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/auth/group/<path:object_id>/change/` | change_view | :admin:auth_group_change | GET, POST | ✓ |
| `/admin/auth/group/<path:object_id>/delete/` | delete_view | :admin:auth_group_delete | GET, POST | ✓ |
| `/admin/auth/group/<path:object_id>/history/` | history_view | :admin:auth_group_history | GET, POST | ✓ |
| `/admin/auth/group/add/` | add_view | :admin:auth_group_add | GET, POST |  |
| `/admin/autocomplete/` | autocomplete_view | :admin:autocomplete | GET, POST |  |
| `/admin/core/auditlog/` | changelist_view | :admin:core_auditlog_changelist | GET, POST |  |
| `/admin/core/auditlog/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/core/auditlog/<path:object_id>/change/` | change_view | :admin:core_auditlog_change | GET, POST | ✓ |
| `/admin/core/auditlog/<path:object_id>/delete/` | delete_view | :admin:core_auditlog_delete | GET, POST | ✓ |
| `/admin/core/auditlog/<path:object_id>/history/` | history_view | :admin:core_auditlog_history | GET, POST | ✓ |
| `/admin/core/auditlog/add/` | add_view | :admin:core_auditlog_add | GET, POST |  |
| `/admin/documents/comparisonjob/` | changelist_view | :admin:documents_comparisonjob_changelist | GET, POST |  |
| `/admin/documents/comparisonjob/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/documents/comparisonjob/<path:object_id>/change/` | change_view | :admin:documents_comparisonjob_change | GET, POST | ✓ |
| `/admin/documents/comparisonjob/<path:object_id>/delete/` | delete_view | :admin:documents_comparisonjob_delete | GET, POST | ✓ |
| `/admin/documents/comparisonjob/<path:object_id>/history/` | history_view | :admin:documents_comparisonjob_history | GET, POST | ✓ |
| `/admin/documents/comparisonjob/add/` | add_view | :admin:documents_comparisonjob_add | GET, POST |  |
| `/admin/documents/comparisonresult/` | changelist_view | :admin:documents_comparisonresult_changelist | GET, POST |  |
| `/admin/documents/comparisonresult/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/documents/comparisonresult/<path:object_id>/change/` | change_view | :admin:documents_comparisonresult_change | GET, POST | ✓ |
| `/admin/documents/comparisonresult/<path:object_id>/delete/` | delete_view | :admin:documents_comparisonresult_delete | GET, POST | ✓ |
| `/admin/documents/comparisonresult/<path:object_id>/history/` | history_view | :admin:documents_comparisonresult_history | GET, POST | ✓ |
| `/admin/documents/comparisonresult/add/` | add_view | :admin:documents_comparisonresult_add | GET, POST |  |
| `/admin/exams/exam/` | changelist_view | :admin:exams_exam_changelist | GET, POST |  |
| `/admin/exams/exam/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/exams/exam/<path:object_id>/change/` | change_view | :admin:exams_exam_change | GET, POST | ✓ |
| `/admin/exams/exam/<path:object_id>/delete/` | delete_view | :admin:exams_exam_delete | GET, POST | ✓ |
| `/admin/exams/exam/<path:object_id>/history/` | history_view | :admin:exams_exam_history | GET, POST | ✓ |
| `/admin/exams/exam/add/` | add_view | :admin:exams_exam_add | GET, POST |  |
| `/admin/exams/examresult/` | changelist_view | :admin:exams_examresult_changelist | GET, POST |  |
| `/admin/exams/examresult/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/exams/examresult/<path:object_id>/change/` | change_view | :admin:exams_examresult_change | GET, POST | ✓ |
| `/admin/exams/examresult/<path:object_id>/delete/` | delete_view | :admin:exams_examresult_delete | GET, POST | ✓ |
| `/admin/exams/examresult/<path:object_id>/history/` | history_view | :admin:exams_examresult_history | GET, POST | ✓ |
| `/admin/exams/examresult/add/` | add_view | :admin:exams_examresult_add | GET, POST |  |
| `/admin/exams/gradeconfig/` | changelist_view | :admin:exams_gradeconfig_changelist | GET, POST |  |
| `/admin/exams/gradeconfig/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/exams/gradeconfig/<path:object_id>/change/` | change_view | :admin:exams_gradeconfig_change | GET, POST | ✓ |
| `/admin/exams/gradeconfig/<path:object_id>/delete/` | delete_view | :admin:exams_gradeconfig_delete | GET, POST | ✓ |
| `/admin/exams/gradeconfig/<path:object_id>/history/` | history_view | :admin:exams_gradeconfig_history | GET, POST | ✓ |
| `/admin/exams/gradeconfig/add/` | add_view | :admin:exams_gradeconfig_add | GET, POST |  |
| `/admin/finance/expense/` | changelist_view | :admin:finance_expense_changelist | GET, POST |  |
| `/admin/finance/expense/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/expense/<path:object_id>/change/` | change_view | :admin:finance_expense_change | GET, POST | ✓ |
| `/admin/finance/expense/<path:object_id>/delete/` | delete_view | :admin:finance_expense_delete | GET, POST | ✓ |
| `/admin/finance/expense/<path:object_id>/history/` | history_view | :admin:finance_expense_history | GET, POST | ✓ |
| `/admin/finance/expense/add/` | add_view | :admin:finance_expense_add | GET, POST |  |
| `/admin/finance/expensecategory/` | changelist_view | :admin:finance_expensecategory_changelist | GET, POST |  |
| `/admin/finance/expensecategory/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/expensecategory/<path:object_id>/change/` | change_view | :admin:finance_expensecategory_change | GET, POST | ✓ |
| `/admin/finance/expensecategory/<path:object_id>/delete/` | delete_view | :admin:finance_expensecategory_delete | GET, POST | ✓ |
| `/admin/finance/expensecategory/<path:object_id>/history/` | history_view | :admin:finance_expensecategory_history | GET, POST | ✓ |
| `/admin/finance/expensecategory/add/` | add_view | :admin:finance_expensecategory_add | GET, POST |  |
| `/admin/finance/installment/` | changelist_view | :admin:finance_installment_changelist | GET, POST |  |
| `/admin/finance/installment/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/installment/<path:object_id>/change/` | change_view | :admin:finance_installment_change | GET, POST | ✓ |
| `/admin/finance/installment/<path:object_id>/delete/` | delete_view | :admin:finance_installment_delete | GET, POST | ✓ |
| `/admin/finance/installment/<path:object_id>/history/` | history_view | :admin:finance_installment_history | GET, POST | ✓ |
| `/admin/finance/installment/add/` | add_view | :admin:finance_installment_add | GET, POST |  |
| `/admin/finance/installmentplan/` | changelist_view | :admin:finance_installmentplan_changelist | GET, POST |  |
| `/admin/finance/installmentplan/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/installmentplan/<path:object_id>/change/` | change_view | :admin:finance_installmentplan_change | GET, POST | ✓ |
| `/admin/finance/installmentplan/<path:object_id>/delete/` | delete_view | :admin:finance_installmentplan_delete | GET, POST | ✓ |
| `/admin/finance/installmentplan/<path:object_id>/history/` | history_view | :admin:finance_installmentplan_history | GET, POST | ✓ |
| `/admin/finance/installmentplan/add/` | add_view | :admin:finance_installmentplan_add | GET, POST |  |
| `/admin/finance/payment/` | changelist_view | :admin:finance_payment_changelist | GET, POST |  |
| `/admin/finance/payment/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/payment/<path:object_id>/change/` | change_view | :admin:finance_payment_change | GET, POST | ✓ |
| `/admin/finance/payment/<path:object_id>/delete/` | delete_view | :admin:finance_payment_delete | GET, POST | ✓ |
| `/admin/finance/payment/<path:object_id>/history/` | history_view | :admin:finance_payment_history | GET, POST | ✓ |
| `/admin/finance/payment/add/` | add_view | :admin:finance_payment_add | GET, POST |  |
| `/admin/finance/refund/` | changelist_view | :admin:finance_refund_changelist | GET, POST |  |
| `/admin/finance/refund/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/finance/refund/<path:object_id>/change/` | change_view | :admin:finance_refund_change | GET, POST | ✓ |
| `/admin/finance/refund/<path:object_id>/delete/` | delete_view | :admin:finance_refund_delete | GET, POST | ✓ |
| `/admin/finance/refund/<path:object_id>/history/` | history_view | :admin:finance_refund_history | GET, POST | ✓ |
| `/admin/finance/refund/add/` | add_view | :admin:finance_refund_add | GET, POST |  |
| `/admin/jsi18n/` | i18n_javascript | :admin:jsi18n | GET, POST |  |
| `/admin/login/` | login | :admin:login | GET, POST |  |
| `/admin/logout/` | logout | :admin:logout | GET, POST |  |
| `/admin/notifications/emaillog/` | changelist_view | :admin:notifications_emaillog_changelist | GET, POST |  |
| `/admin/notifications/emaillog/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/notifications/emaillog/<path:object_id>/change/` | change_view | :admin:notifications_emaillog_change | GET, POST | ✓ |
| `/admin/notifications/emaillog/<path:object_id>/delete/` | delete_view | :admin:notifications_emaillog_delete | GET, POST | ✓ |
| `/admin/notifications/emaillog/<path:object_id>/history/` | history_view | :admin:notifications_emaillog_history | GET, POST | ✓ |
| `/admin/notifications/emaillog/add/` | add_view | :admin:notifications_emaillog_add | GET, POST |  |
| `/admin/notifications/notification/` | changelist_view | :admin:notifications_notification_changelist | GET, POST |  |
| `/admin/notifications/notification/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/notifications/notification/<path:object_id>/change/` | change_view | :admin:notifications_notification_change | GET, POST | ✓ |
| `/admin/notifications/notification/<path:object_id>/delete/` | delete_view | :admin:notifications_notification_delete | GET, POST | ✓ |
| `/admin/notifications/notification/<path:object_id>/history/` | history_view | :admin:notifications_notification_history | GET, POST | ✓ |
| `/admin/notifications/notification/add/` | add_view | :admin:notifications_notification_add | GET, POST |  |
| `/admin/notifications/notificationtemplate/` | changelist_view | :admin:notifications_notificationtemplate_changelist | GET, POST |  |
| `/admin/notifications/notificationtemplate/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/notifications/notificationtemplate/<path:object_id>/change/` | change_view | :admin:notifications_notificationtemplate_change | GET, POST | ✓ |
| `/admin/notifications/notificationtemplate/<path:object_id>/delete/` | delete_view | :admin:notifications_notificationtemplate_delete | GET, POST | ✓ |
| `/admin/notifications/notificationtemplate/<path:object_id>/history/` | history_view | :admin:notifications_notificationtemplate_history | GET, POST | ✓ |
| `/admin/notifications/notificationtemplate/add/` | add_view | :admin:notifications_notificationtemplate_add | GET, POST |  |
| `/admin/password_change/` | password_change | :admin:password_change | GET, POST |  |
| `/admin/password_change/done/` | password_change_done | :admin:password_change_done | GET, POST |  |
| `/admin/r/<int:content_type_id>/<path:object_id>/` | shortcut | :admin:view_on_site | GET, POST | ✓ |
| `/admin/students/enrollment/` | changelist_view | :admin:students_enrollment_changelist | GET, POST |  |
| `/admin/students/enrollment/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/students/enrollment/<path:object_id>/change/` | change_view | :admin:students_enrollment_change | GET, POST | ✓ |
| `/admin/students/enrollment/<path:object_id>/delete/` | delete_view | :admin:students_enrollment_delete | GET, POST | ✓ |
| `/admin/students/enrollment/<path:object_id>/history/` | history_view | :admin:students_enrollment_history | GET, POST | ✓ |
| `/admin/students/enrollment/add/` | add_view | :admin:students_enrollment_add | GET, POST |  |
| `/admin/students/guardian/` | changelist_view | :admin:students_guardian_changelist | GET, POST |  |
| `/admin/students/guardian/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/students/guardian/<path:object_id>/change/` | change_view | :admin:students_guardian_change | GET, POST | ✓ |
| `/admin/students/guardian/<path:object_id>/delete/` | delete_view | :admin:students_guardian_delete | GET, POST | ✓ |
| `/admin/students/guardian/<path:object_id>/history/` | history_view | :admin:students_guardian_history | GET, POST | ✓ |
| `/admin/students/guardian/add/` | add_view | :admin:students_guardian_add | GET, POST |  |
| `/admin/students/lead/` | changelist_view | :admin:students_lead_changelist | GET, POST |  |
| `/admin/students/lead/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/students/lead/<path:object_id>/change/` | change_view | :admin:students_lead_change | GET, POST | ✓ |
| `/admin/students/lead/<path:object_id>/delete/` | delete_view | :admin:students_lead_delete | GET, POST | ✓ |
| `/admin/students/lead/<path:object_id>/history/` | history_view | :admin:students_lead_history | GET, POST | ✓ |
| `/admin/students/lead/add/` | add_view | :admin:students_lead_add | GET, POST |  |
| `/admin/students/student/` | changelist_view | :admin:students_student_changelist | GET, POST |  |
| `/admin/students/student/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/students/student/<path:object_id>/change/` | change_view | :admin:students_student_change | GET, POST | ✓ |
| `/admin/students/student/<path:object_id>/delete/` | delete_view | :admin:students_student_delete | GET, POST | ✓ |
| `/admin/students/student/<path:object_id>/history/` | history_view | :admin:students_student_history | GET, POST | ✓ |
| `/admin/students/student/add/` | add_view | :admin:students_student_add | GET, POST |  |
| `/admin/students/studentdocument/` | changelist_view | :admin:students_studentdocument_changelist | GET, POST |  |
| `/admin/students/studentdocument/<path:object_id>/` | RedirectView |  | GET, POST, PUT | ✓ |
| `/admin/students/studentdocument/<path:object_id>/change/` | change_view | :admin:students_studentdocument_change | GET, POST | ✓ |
| `/admin/students/studentdocument/<path:object_id>/delete/` | delete_view | :admin:students_studentdocument_delete | GET, POST | ✓ |
| `/admin/students/studentdocument/<path:object_id>/history/` | history_view | :admin:students_studentdocument_history | GET, POST | ✓ |
| `/admin/students/studentdocument/add/` | add_view | :admin:students_studentdocument_add | GET, POST |  |
| `/api/analytics/aging-report/` | api_aging_report | :analytics:api_aging_report | GET, POST |  |
| `/api/analytics/attendance-trend/` | api_attendance_trend | :analytics:api_attendance_trend | GET, POST |  |
| `/api/analytics/enrollment-growth/` | api_enrollment_growth | :analytics:api_enrollment_growth | GET, POST |  |
| `/api/analytics/lead-funnel/` | api_lead_funnel | :analytics:api_lead_funnel | GET, POST |  |
| `/api/analytics/revenue-trend/` | api_revenue_trend | :analytics:api_revenue_trend | GET, POST |  |
| `/api/attendance/bulk-mark/` | api_attendance_bulk_mark | :api:api_attendance_bulk_mark | GET, POST |  |
| `/api/dashboard/stats/` | api_dashboard_stats | :api:api_dashboard_stats | GET, POST |  |
| `/api/notifications/unread-count/` | api_unread_count | :api:api_unread_count | GET, POST |  |
| `/api/sessions/search/` | api_session_search | :api:api_session_search | GET, POST |  |
| `/api/students/search/` | api_student_search | :api:api_student_search | GET, POST |  |
| `/apply/` | PublicAdmissionFormView | :admissions_public:apply | GET, POST, PUT |  |
| `/apply/success/` | PublicSuccessView | :admissions_public:success | GET |  |
| `/panel/accounts/categories/` | expense_category_list | :accounts_panel:expense_category_list | GET, POST |  |
| `/panel/accounts/categories/create/` | expense_category_create | :accounts_panel:expense_category_create | GET, POST |  |
| `/panel/accounts/dashboard/` | AccountantDashboardView | :accounts_panel:dashboard | GET |  |
| `/panel/accounts/expenses/` | expense_list | :accounts_panel:expense_list | GET, POST |  |
| `/panel/accounts/expenses/<int:pk>/` | expense_detail | :accounts_panel:expense_detail | GET, POST | ✓ |
| `/panel/accounts/expenses/create/` | expense_create | :accounts_panel:expense_create | GET, POST |  |
| `/panel/accounts/installments/` | installment_plan_list | :accounts_panel:installment_plan_list | GET, POST |  |
| `/panel/accounts/installments/<int:pk>/` | installment_plan_detail | :accounts_panel:installment_plan_detail | GET, POST | ✓ |
| `/panel/accounts/installments/<int:pk>/pay/` | installment_pay | :accounts_panel:installment_pay | GET, POST | ✓ |
| `/panel/accounts/installments/<int:pk>/restructure/` | installment_restructure | :accounts_panel:installment_restructure | GET, POST | ✓ |
| `/panel/accounts/installments/create/` | installment_plan_create | :accounts_panel:installment_plan_create | GET, POST |  |
| `/panel/accounts/late-fees/apply/` | late_fee_apply | :accounts_panel:late_fee_apply | GET, POST |  |
| `/panel/accounts/late-fees/waive/` | late_fee_waive | :accounts_panel:late_fee_waive | GET, POST |  |
| `/panel/accounts/notifications/` | NotificationListView | :accounts_panel:notification_list | GET |  |
| `/panel/accounts/notifications/mark-read/` | NotificationMarkReadView | :accounts_panel:notification_mark_read | POST |  |
| `/panel/accounts/overdue/` | overdue_list | :accounts_panel:overdue_list | GET, POST |  |
| `/panel/accounts/payments/` | payment_list | :accounts_panel:payment_list | GET, POST |  |
| `/panel/accounts/payments/<int:pk>/` | payment_detail | :accounts_panel:payment_detail | GET, POST | ✓ |
| `/panel/accounts/payments/create/` | payment_create | :accounts_panel:payment_create | GET, POST |  |
| `/panel/accounts/pending-dues/` | PendingDuesView | :accounts_panel:pending_dues | GET, POST |  |
| `/panel/accounts/refunds/` | refund_list | :accounts_panel:refund_list | GET, POST |  |
| `/panel/accounts/refunds/create/` | refund_create | :accounts_panel:refund_create | GET, POST |  |
| `/panel/accounts/reports/` | AccountantReportsDashboardView | :accounts_panel:reports_dashboard | GET |  |
| `/panel/accounts/reports/overdue/` | report_overdue | :accounts_panel:report_overdue | GET, POST |  |
| `/panel/accounts/reports/pending-dues/csv/` | PendingDuesExportCSVView | :accounts_panel:pending_dues_csv | GET |  |
| `/panel/accounts/reports/pending-dues/pdf/` | PendingDuesPDFView | :accounts_panel:pending_dues_pdf | GET |  |
| `/panel/accounts/reports/revenue/` | report_revenue | :accounts_panel:report_revenue | GET, POST |  |
| `/panel/accounts/students/<int:pk>/ledger/` | student_ledger | :accounts_panel:student_ledger | GET, POST | ✓ |
| `/panel/admin/academics/assignments/<int:pk>/delete/` | assignment_delete | :admin_panel:academics:assignment_delete | GET, POST | ✓ |
| `/panel/admin/academics/assignments/<int:pk>/edit/` | assignment_edit | :admin_panel:academics:assignment_edit | GET, POST | ✓ |
| `/panel/admin/academics/assignments/create/` | assignment_create | :admin_panel:academics:assignment_create | GET, POST |  |
| `/panel/admin/academics/sessions/<int:pk>/` | session_detail | :admin_panel:academics:session_detail | GET, POST | ✓ |
| `/panel/admin/academics/sessions/<int:pk>/delete/` | session_delete | :admin_panel:academics:session_delete | GET, POST | ✓ |
| `/panel/admin/academics/sessions/<int:pk>/edit/` | session_edit | :admin_panel:academics:session_edit | GET, POST | ✓ |
| `/panel/admin/academics/sessions/<int:pk>/enrollments/` | session_enrollments | :admin_panel:academics:session_enrollments | GET, POST | ✓ |
| `/panel/admin/academics/sessions/<int:pk>/revenue/` | session_revenue | :admin_panel:academics:session_revenue | GET, POST | ✓ |
| `/panel/admin/academics/sessions/<int:pk>/toggle-status/` | session_toggle_status | :admin_panel:academics:session_toggle_status | GET, POST | ✓ |
| `/panel/admin/academics/sessions/create/` | session_create | :admin_panel:academics:session_create | GET, POST |  |
| `/panel/admin/academics/subjects/<int:pk>/edit/` | subject_edit | :admin_panel:academics:subject_edit | GET, POST | ✓ |
| `/panel/admin/academics/subjects/create/` | subject_create | :admin_panel:academics:subject_create | GET, POST |  |
| `/panel/admin/add-session/` | session_create | :admin_panel:add_session | GET, POST |  |
| `/panel/admin/add-student/` | student_create | :admin_panel:add_student | GET, POST |  |
| `/panel/admin/admissions/` | AdmissionListView | :admin_panel:admissions:admission_list | GET |  |
| `/panel/admin/admissions/<int:pk>/` | AdmissionDetailView | :admin_panel:admissions:admission_detail | GET | ✓ |
| `/panel/admin/admissions/<int:pk>/approve/` | AdmissionApproveView | :admin_panel:admissions:admission_approve | POST | ✓ |
| `/panel/admin/admissions/<int:pk>/convert/` | AdmissionConvertView | :admin_panel:admissions:admission_convert | POST | ✓ |
| `/panel/admin/admissions/<int:pk>/reject/` | AdmissionRejectView | :admin_panel:admissions:admission_reject | POST | ✓ |
| `/panel/admin/admissions/<int:pk>/review/` | AdmissionReviewView | :admin_panel:admissions:admission_review | POST | ✓ |
| `/panel/admin/admissions/export/` | AdmissionExportCSVView | :admin_panel:admissions:admission_export | GET |  |
| `/panel/admin/admissions/summary/` | AdmissionSummaryView | :admin_panel:admissions:admission_summary | GET |  |
| `/panel/admin/ai/dropout-risk/` | dropout_risk_dashboard | :admin_panel:ai_engine:dropout_risk_dashboard | GET, POST |  |
| `/panel/admin/ai/models/` | model_version_list | :admin_panel:ai_engine:model_version_list | GET, POST |  |
| `/panel/admin/ai/predictions/` | prediction_list | :admin_panel:ai_engine:prediction_list | GET, POST |  |
| `/panel/admin/ai/predictions/<int:pk>/` | prediction_detail | :admin_panel:ai_engine:prediction_detail | GET, POST | ✓ |
| `/panel/admin/ai/predictions/<int:pk>/acknowledge/` | prediction_acknowledge | :admin_panel:ai_engine:prediction_acknowledge | GET, POST | ✓ |
| `/panel/admin/analytics/` | AdminAnalyticsView | :admin_panel:analytics | GET |  |
| `/panel/admin/attendance/` | attendance_overview | :admin_panel:attendance:attendance_overview | GET, POST |  |
| `/panel/admin/attendance/<int:session_id>/analytics/` | attendance_analytics | :admin_panel:attendance:attendance_analytics | GET, POST | ✓ |
| `/panel/admin/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet | :admin_panel:attendance:attendance_sheet | GET, POST | ✓ |
| `/panel/admin/attendance/<int:session_id>/lock/` | attendance_lock | :admin_panel:attendance:attendance_lock | GET, POST | ✓ |
| `/panel/admin/attendance/<int:session_id>/unlock/` | attendance_unlock | :admin_panel:attendance:attendance_unlock | GET, POST | ✓ |
| `/panel/admin/attendance/low-attendance/` | low_attendance_report | :admin_panel:attendance:low_attendance_report | GET, POST |  |
| `/panel/admin/attendance/mark/<int:session_id>/` | attendance_mark | :admin_panel:attendance:attendance_mark | GET, POST | ✓ |
| `/panel/admin/audit/` | audit_log_list | :admin_panel:audit:audit_log_list | GET, POST |  |
| `/panel/admin/audit/<int:pk>/` | audit_log_detail | :admin_panel:audit:audit_log_detail | GET, POST | ✓ |
| `/panel/admin/automation/alerts/` | AutomationAlertsView | :admin_panel:automation_alerts | GET |  |
| `/panel/admin/automation/jobs/` | AutomationJobsView | :admin_panel:automation_jobs | GET |  |
| `/panel/admin/dashboard/` | admin_dashboard | :admin_panel:dashboard | GET, POST |  |
| `/panel/admin/documents/` | RedirectView |  | GET, POST, PUT |  |
| `/panel/admin/documents/jobs/` | pdf_comparison | :admin_panel:documents:comparison_job_list | GET, POST |  |
| `/panel/admin/documents/jobs/<int:pk>/` | pdf_comparison | :admin_panel:documents:comparison_job_detail | GET, POST | ✓ |
| `/panel/admin/documents/jobs/<int:pk>/results/` | pdf_comparison | :admin_panel:documents:comparison_results | GET, POST | ✓ |
| `/panel/admin/documents/jobs/create/` | pdf_comparison | :admin_panel:documents:comparison_job_create | GET, POST |  |
| `/panel/admin/documents/preview/export/` | export_preview_csv | :admin_panel:documents:export_preview_csv | GET, POST |  |
| `/panel/admin/exam-overview/` | exam_overview | :admin_panel:exam_overview | GET, POST |  |
| `/panel/admin/exams/` | ExamListView | :admin_panel:exams:exam_list | GET |  |
| `/panel/admin/exams/<int:pk>/` | ExamDetailView | :admin_panel:exams:exam_detail | GET | ✓ |
| `/panel/admin/exams/<int:pk>/edit/` | ExamEditView | :admin_panel:exams:exam_edit | GET, POST | ✓ |
| `/panel/admin/exams/<int:pk>/publish/` | ExamPublishView | :admin_panel:exams:exam_publish | POST | ✓ |
| `/panel/admin/exams/<int:pk>/results/bulk-entry/` | ExamBulkResultEntryView | :admin_panel:exams:exam_results_bulk_entry | GET, POST | ✓ |
| `/panel/admin/exams/<int:pk>/results/entry/` | ExamResultEntryView | :admin_panel:exams:exam_results_entry | GET, POST | ✓ |
| `/panel/admin/exams/<int:pk>/review/` | ExamReviewView | :admin_panel:exams:exam_review | POST | ✓ |
| `/panel/admin/exams/<int:pk>/statistics/` | ExamStatisticsView | :admin_panel:exams:exam_statistics | GET | ✓ |
| `/panel/admin/exams/create/` | ExamCreateView | :admin_panel:exams:exam_create | GET, POST |  |
| `/panel/admin/exams/grade-config/` | grade_config_list | :admin_panel:exams:grade_config_list | GET, POST |  |
| `/panel/admin/exams/grade-config/<int:pk>/edit/` | grade_config_edit | :admin_panel:exams:grade_config_edit | GET, POST | ✓ |
| `/panel/admin/exams/grade-config/create/` | grade_config_create | :admin_panel:exams:grade_config_create | GET, POST |  |
| `/panel/admin/faculty-overview/` | faculty_overview | :admin_panel:faculty_overview | GET, POST |  |
| `/panel/admin/finance/expenses/` | expense_list | :admin_panel:finance:expense_list | GET, POST |  |
| `/panel/admin/finance/expenses/<int:pk>/` | expense_detail | :admin_panel:finance:expense_detail | GET, POST | ✓ |
| `/panel/admin/finance/expenses/<int:pk>/approve/` | expense_approve | :admin_panel:finance:expense_approve | GET, POST | ✓ |
| `/panel/admin/finance/expenses/<int:pk>/reject/` | expense_reject | :admin_panel:finance:expense_reject | GET, POST | ✓ |
| `/panel/admin/finance/expenses/categories/` | expense_category_list | :admin_panel:finance:expense_category_list | GET, POST |  |
| `/panel/admin/finance/expenses/categories/create/` | expense_category_create | :admin_panel:finance:expense_category_create | GET, POST |  |
| `/panel/admin/finance/expenses/create/` | expense_create | :admin_panel:finance:expense_create | GET, POST |  |
| `/panel/admin/finance/installments/` | installment_plan_list | :admin_panel:finance:installment_plan_list | GET, POST |  |
| `/panel/admin/finance/installments/<int:pk>/` | installment_plan_detail | :admin_panel:finance:installment_plan_detail | GET, POST | ✓ |
| `/panel/admin/finance/installments/<int:pk>/pay/` | InstallmentPayView | :admin_panel:installment_pay | GET, POST | ✓ |
| `/panel/admin/finance/installments/<int:pk>/pay/` | installment_pay | :admin_panel:finance:installment_pay | GET, POST | ✓ |
| `/panel/admin/finance/installments/<int:pk>/restructure/` | installment_restructure | :admin_panel:finance:installment_restructure | GET, POST | ✓ |
| `/panel/admin/finance/installments/create/` | installment_plan_create | :admin_panel:finance:installment_plan_create | GET, POST |  |
| `/panel/admin/finance/installments/pay/<int:pk>/` | installment_pay | :admin_panel:finance:installment_pay | GET, POST | ✓ |
| `/panel/admin/finance/late-fees/apply/` | late_fee_apply | :admin_panel:finance:late_fee_apply | GET, POST |  |
| `/panel/admin/finance/late-fees/waive/<int:pk>/` | late_fee_waive | :admin_panel:finance:late_fee_waive | GET, POST | ✓ |
| `/panel/admin/finance/overdue/` | overdue_list | :admin_panel:finance:overdue_list | GET, POST |  |
| `/panel/admin/finance/payments/` | payment_list | :admin_panel:finance:payment_list | GET, POST |  |
| `/panel/admin/finance/payments/<int:pk>/` | payment_detail | :admin_panel:finance:payment_detail | GET, POST | ✓ |
| `/panel/admin/finance/payments/<int:pk>/delete/` | payment_delete | :admin_panel:finance:payment_delete | GET, POST | ✓ |
| `/panel/admin/finance/payments/create/` | payment_create | :admin_panel:finance:payment_create | GET, POST |  |
| `/panel/admin/finance/refunds/` | refund_list | :admin_panel:finance:refund_list | GET, POST |  |
| `/panel/admin/finance/refunds/create/` | refund_create | :admin_panel:finance:refund_create | GET, POST |  |
| `/panel/admin/finance/send-fee-reminder/` | send_fee_reminder | :admin_panel:finance:send_fee_reminder | GET, POST |  |
| `/panel/admin/manage-faculty/` | FacultyListView | :admin_panel:staff:faculty_list | GET |  |
| `/panel/admin/manage-faculty/<int:pk>/assign/` | FacultyAssignSessionView | :admin_panel:staff:faculty_assign | GET, POST, PUT | ✓ |
| `/panel/admin/manage-faculty/create/` | FacultyCreateView | :admin_panel:staff:faculty_create | GET, POST, PUT |  |
| `/panel/admin/manage-students/` | student_list | :admin_panel:manage_students | GET, POST |  |
| `/panel/admin/notifications/` | NotificationListView | :admin_panel:notifications:notification_list | GET |  |
| `/panel/admin/notifications/<int:pk>/` | NotificationDetailView | :admin_panel:notifications:notification_detail | GET | ✓ |
| `/panel/admin/notifications/bulk-send/` | NotificationBulkSendView | :admin_panel:notifications:notification_bulk_send | GET, POST |  |
| `/panel/admin/notifications/email-logs/` | email_log_list | :admin_panel:notifications:email_log_list | GET, POST |  |
| `/panel/admin/notifications/mark-read/` | NotificationMarkReadView | :admin_panel:notifications:notification_mark_read | POST |  |
| `/panel/admin/notifications/templates/` | template_list | :admin_panel:notifications:template_list | GET, POST |  |
| `/panel/admin/notifications/templates/<int:pk>/edit/` | template_edit | :admin_panel:notifications:template_edit | GET, POST | ✓ |
| `/panel/admin/notifications/templates/create/` | template_create | :admin_panel:notifications:template_create | GET, POST |  |
| `/panel/admin/notifications/unread-count/` | UnreadCountAPIView | :admin_panel:notifications:unread_count_api | GET |  |
| `/panel/admin/pdf-comparison/` | pdf_comparison | :admin_panel:pdf_comparison | GET, POST |  |
| `/panel/admin/pdf-comparison/export-preview/` | export_preview_csv | :admin_panel:export_preview_csv | GET, POST |  |
| `/panel/admin/pdf-comparison/export/<int:job_id>/` | export_comparison_csv | :admin_panel:export_comparison_csv | GET, POST | ✓ |
| `/panel/admin/pending-dues/` | PendingDuesView | :admin_panel:pending_dues | GET, POST |  |
| `/panel/admin/permissions/` | permission_matrix | :admin_panel:permissions | GET, POST |  |
| `/panel/admin/reports-dashboard/` | reports_dashboard_proxy | :admin_panel:reports_dashboard | GET, POST |  |
| `/panel/admin/reports/` | ReportsDashboardView | :reports:dashboard | GET |  |
| `/panel/admin/reports/attendance/` | report_attendance | :admin_panel:reports:report_attendance | GET, POST |  |
| `/panel/admin/reports/enrollment/` | report_enrollment | :admin_panel:reports:report_enrollment | GET, POST |  |
| `/panel/admin/reports/export/attendance/` | export_attendance_csv | :admin_panel:reports:export_attendance_csv | GET, POST |  |
| `/panel/admin/reports/export/payments/` | export_payments_csv | :admin_panel:reports:export_payments_csv | GET, POST |  |
| `/panel/admin/reports/export/students/` | export_students_csv | :admin_panel:reports:export_students_csv | GET, POST |  |
| `/panel/admin/reports/overdue/` | report_overdue | :admin_panel:reports:report_overdue | GET, POST |  |
| `/panel/admin/reports/pdf/attendance/<int:session_id>/` | pdf_attendance_report | :admin_panel:reports:pdf_attendance_report | GET, POST | ✓ |
| `/panel/admin/reports/pdf/ledger/<int:enrollment_id>/` | pdf_student_ledger | :admin_panel:reports:pdf_student_ledger | GET, POST | ✓ |
| `/panel/admin/reports/pending-dues/csv/` | PendingDuesExportCSVView | :reports:pending_dues_csv | GET |  |
| `/panel/admin/reports/pending-dues/pdf/` | PendingDuesPDFView | :reports:pending_dues_pdf | GET |  |
| `/panel/admin/reports/revenue/` | report_revenue | :admin_panel:reports:report_revenue | GET, POST |  |
| `/panel/admin/reports/session-results/<int:session_id>/csv/` | SessionResultsExportCSVView | :reports:session_results_csv | GET | ✓ |
| `/panel/admin/reports/session-results/<int:session_id>/pdf/` | SessionResultsPDFView | :reports:session_results_pdf | GET | ✓ |
| `/panel/admin/reports/student-directory/csv/` | StudentDirectoryExportCSVView | :reports:student_directory_csv | GET |  |
| `/panel/admin/reports/student/<int:student_id>/transcript/pdf/` | StudentTranscriptPDFView | :reports:student_transcript_pdf | GET | ✓ |
| `/panel/admin/reports/success/csv/` | SuccessReportExportCSVView | :reports:success_csv | GET |  |
| `/panel/admin/reports/success/pdf/` | SuccessReportPDFView | :reports:success_pdf | GET |  |
| `/panel/admin/reports/teacher-workload/csv/` | TeacherWorkloadExportCSVView | :reports:teacher_workload_csv | GET |  |
| `/panel/admin/reports/teacher-workload/pdf/` | TeacherWorkloadPDFView | :reports:teacher_workload_pdf | GET |  |
| `/panel/admin/session-overview/` | session_overview | :admin_panel:session_overview | GET, POST |  |
| `/panel/admin/session/<int:pk>/results/` | session_result_summary | :admin_panel:session_result_summary | GET, POST | ✓ |
| `/panel/admin/sessions/` | session_overview | :admin_panel:session_list | GET, POST |  |
| `/panel/admin/sessions/<int:pk>/` | session_detail | :admin_panel:session_detail | GET, POST | ✓ |
| `/panel/admin/sessions/<int:pk>/edit/` | session_edit | :admin_panel:session_edit | GET, POST | ✓ |
| `/panel/admin/sessions/<int:pk>/results/` | session_result_summary | :admin_panel:session_result | GET, POST | ✓ |
| `/panel/admin/sessions/create/` | session_create | :admin_panel:session_create | GET, POST |  |
| `/panel/admin/students/` | student_list | :admin_panel:students:student_list | GET, POST |  |
| `/panel/admin/students/<int:pk>/` | student_detail | :admin_panel:students:student_detail | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/create-login/` | student_create_login | :admin_panel:student_create_login | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/delete/` | student_delete | :admin_panel:students:student_delete | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/documents/` | student_documents | :admin_panel:students:student_documents | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/documents/upload/` | student_document_upload | :admin_panel:students:student_document_upload | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/edit/` | student_edit | :admin_panel:students:student_edit | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/guardians/` | student_guardians | :admin_panel:students:student_guardians | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/ledger/` | student_ledger | :admin_panel:students:student_ledger | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/reset-password/` | student_reset_password | :admin_panel:student_reset_password | GET, POST | ✓ |
| `/panel/admin/students/<int:pk>/restore/` | student_restore | :admin_panel:students:student_restore | GET, POST | ✓ |
| `/panel/admin/students/create/` | student_create | :admin_panel:students:student_create | GET, POST |  |
| `/panel/admin/students/enrollments/` | enrollment_list | :admin_panel:students:enrollment_list | GET, POST |  |
| `/panel/admin/students/enrollments/<int:pk>/` | enrollment_detail | :admin_panel:students:enrollment_detail | GET, POST | ✓ |
| `/panel/admin/students/enrollments/<int:pk>/freeze/` | enrollment_freeze | :admin_panel:students:enrollment_freeze | GET, POST | ✓ |
| `/panel/admin/students/enrollments/<int:pk>/restore/` | enrollment_restore | :admin_panel:students:enrollment_restore | GET, POST | ✓ |
| `/panel/admin/students/enrollments/<int:pk>/transfer/` | enrollment_transfer | :admin_panel:students:enrollment_transfer | GET, POST | ✓ |
| `/panel/admin/students/enrollments/<int:pk>/unfreeze/` | enrollment_unfreeze | :admin_panel:students:enrollment_unfreeze | GET, POST | ✓ |
| `/panel/admin/students/enrollments/<int:pk>/withdraw/` | enrollment_withdraw | :admin_panel:students:enrollment_withdraw | GET, POST | ✓ |
| `/panel/admin/students/enrollments/create/` | enrollment_create | :admin_panel:students:enrollment_create | GET, POST |  |
| `/panel/admin/students/leads/` | lead_list | :admin_panel:students:lead_list | GET, POST |  |
| `/panel/admin/students/leads/<int:pk>/` | lead_detail | :admin_panel:students:lead_detail | GET, POST | ✓ |
| `/panel/admin/students/leads/<int:pk>/convert/` | lead_convert | :admin_panel:students:lead_convert | GET, POST | ✓ |
| `/panel/admin/students/leads/<int:pk>/edit/` | lead_edit | :admin_panel:students:lead_edit | GET, POST | ✓ |
| `/panel/admin/students/leads/create/` | lead_create | :admin_panel:students:lead_create | GET, POST |  |
| `/panel/admin/success/` | SuccessDashboardView | :admin_panel:success_dashboard | GET |  |
| `/panel/admin/timetable-overview/` | timetable_overview | :admin_panel:timetable_overview | GET, POST |  |
| `/panel/admin/timetable/` | timetable_list | :admin_panel:timetable_list | GET, POST |  |
| `/panel/admin/timetable/<int:pk>/edit/` | timetable_edit | :admin_panel:timetable_edit | GET, POST | ✓ |
| `/panel/admin/timetable/<int:pk>/toggle-status/` | timetable_toggle_status | :admin_panel:timetable_toggle_status | GET, POST | ✓ |
| `/panel/admin/timetable/create/` | timetable_create | :admin_panel:timetable_create | GET, POST |  |
| `/panel/admin/users/` | user_list | :admin_panel:users:user_list | GET, POST |  |
| `/panel/admin/users/<int:pk>/assign-role/` | user_assign_role | :admin_panel:users:user_assign_role | GET, POST | ✓ |
| `/panel/admin/users/<int:pk>/assign-session/` | user_assign_session | :admin_panel:users:user_assign_session | GET, POST | ✓ |
| `/panel/admin/users/<int:pk>/reset-password/` | user_reset_password | :admin_panel:users:user_reset_password | GET, POST | ✓ |
| `/panel/admin/users/<int:pk>/toggle-activation/` | user_toggle_activation | :admin_panel:users:user_toggle_activation | GET, POST | ✓ |
| `/panel/admin/users/<int:pk>/toggle-lock/` | user_toggle_lock | :admin_panel:users:user_toggle_lock | GET, POST | ✓ |
| `/panel/principal/dashboard/` | PrincipalDashboardView | :principal_panel:dashboard | GET |  |
| `/panel/registrar/admissions/` | AdmissionListView | :registrar_panel:admissions:admission_list | GET |  |
| `/panel/registrar/admissions/<int:pk>/` | AdmissionDetailView | :registrar_panel:admissions:admission_detail | GET | ✓ |
| `/panel/registrar/admissions/<int:pk>/approve/` | AdmissionApproveView | :registrar_panel:admissions:admission_approve | POST | ✓ |
| `/panel/registrar/admissions/<int:pk>/convert/` | AdmissionConvertView | :registrar_panel:admissions:admission_convert | POST | ✓ |
| `/panel/registrar/admissions/<int:pk>/reject/` | AdmissionRejectView | :registrar_panel:admissions:admission_reject | POST | ✓ |
| `/panel/registrar/admissions/<int:pk>/review/` | AdmissionReviewView | :registrar_panel:admissions:admission_review | POST | ✓ |
| `/panel/registrar/admissions/export/` | AdmissionExportCSVView | :registrar_panel:admissions:admission_export | GET |  |
| `/panel/registrar/admissions/summary/` | AdmissionSummaryView | :registrar_panel:admissions:admission_summary | GET |  |
| `/panel/registrar/dashboard/` | RegistrarDashboardView | :registrar_panel:dashboard | GET |  |
| `/panel/registrar/enrollments/<int:pk>/` | enrollment_detail | :registrar_panel:enrollment_detail | GET, POST | ✓ |
| `/panel/registrar/enrollments/create/` | enrollment_create | :registrar_panel:enrollment_create | GET, POST |  |
| `/panel/registrar/leads/` | lead_list | :registrar_panel:lead_list | GET, POST |  |
| `/panel/registrar/leads/<int:pk>/` | lead_detail | :registrar_panel:lead_detail | GET, POST | ✓ |
| `/panel/registrar/leads/<int:pk>/convert/` | lead_convert | :registrar_panel:lead_convert | GET, POST | ✓ |
| `/panel/registrar/leads/<int:pk>/edit/` | lead_edit | :registrar_panel:lead_edit | GET, POST | ✓ |
| `/panel/registrar/leads/create/` | lead_create | :registrar_panel:lead_create | GET, POST |  |
| `/panel/registrar/notifications/` | NotificationListView | :registrar_panel:notification_list | GET |  |
| `/panel/registrar/notifications/mark-read/` | NotificationMarkReadView | :registrar_panel:notification_mark_read | POST |  |
| `/panel/registrar/sessions/` | session_overview | :registrar_panel:session_list | GET, POST |  |
| `/panel/registrar/sessions/<int:pk>/` | session_detail | :registrar_panel:session_detail | GET, POST | ✓ |
| `/panel/registrar/students/` | student_list | :registrar_panel:student_list | GET, POST |  |
| `/panel/registrar/students/<int:pk>/` | student_detail | :registrar_panel:student_detail | GET, POST | ✓ |
| `/panel/registrar/students/<int:pk>/documents/upload/` | student_document_upload | :registrar_panel:student_document_upload | GET, POST | ✓ |
| `/panel/registrar/students/<int:pk>/edit/` | student_edit | :registrar_panel:student_edit | GET, POST | ✓ |
| `/panel/registrar/students/<int:pk>/guardians/` | student_guardians | :registrar_panel:student_guardians | GET, POST | ✓ |
| `/panel/registrar/students/create/` | student_create | :registrar_panel:student_create | GET, POST |  |
| `/panel/teacher/attendance/<int:session_id>/analytics/` | attendance_analytics | :teacher_panel:attendance_analytics | GET, POST | ✓ |
| `/panel/teacher/attendance/<int:session_id>/date/<str:date>/` | attendance_sheet | :teacher_panel:attendance_sheet | GET, POST | ✓ |
| `/panel/teacher/attendance/mark/<int:session_id>/` | attendance_mark | :teacher_panel:attendance_mark | GET, POST | ✓ |
| `/panel/teacher/dashboard/` | TeacherDashboardView | :teacher_panel:dashboard | GET |  |
| `/panel/teacher/exams/` | ExamListView | :teacher_panel:my_exams | GET |  |
| `/panel/teacher/exams/<int:pk>/` | ExamDetailView | :teacher_panel:exam_detail | GET | ✓ |
| `/panel/teacher/exams/<int:pk>/edit/` | ExamEditView | :teacher_panel:exam_edit | GET, POST | ✓ |
| `/panel/teacher/exams/<int:pk>/results/` | ExamDetailView | :teacher_panel:exam_results | GET | ✓ |
| `/panel/teacher/exams/<int:pk>/results/entry/` | ExamResultEntryView | :teacher_panel:exam_results_entry | GET, POST | ✓ |
| `/panel/teacher/exams/create/` | ExamCreateView | :teacher_panel:exam_create | GET, POST |  |
| `/panel/teacher/my-timetable/` | timetable_teacher | :teacher_panel:my_timetable | GET, POST |  |
| `/panel/teacher/notifications/` | NotificationListView | :teacher_panel:notification_list | GET |  |
| `/panel/teacher/notifications/<int:pk>/` | NotificationDetailView | :teacher_panel:notification_detail | GET | ✓ |
| `/panel/teacher/notifications/mark-read/` | NotificationMarkReadView | :teacher_panel:notification_mark_read | POST |  |
| `/panel/teacher/profile/` | teacher_profile_view | :teacher_panel:profile_view | GET, POST |  |
| `/panel/teacher/profile/edit/` | teacher_profile_edit | :teacher_panel:profile_edit | GET, POST |  |
| `/panel/teacher/sessions/` | my_sessions | :teacher_panel:my_sessions | GET, POST |  |
| `/panel/teacher/sessions/<int:pk>/` | teacher_session_detail | :teacher_panel:session_detail | GET, POST | ✓ |
| `/panel/teacher/sessions/<int:pk>/students/` | teacher_session_students | :teacher_panel:session_students | GET, POST | ✓ |
| `/portal/guardian/child/<int:student_id>/attendance/` | GuardianChildAttendanceView | :guardian_portal:child_attendance | GET | ✓ |
| `/portal/guardian/child/<int:student_id>/exams/` | GuardianChildExamsView | :guardian_portal:child_exams | GET | ✓ |
| `/portal/guardian/child/<int:student_id>/fees/` | GuardianChildFeesView | :guardian_portal:child_payments | GET | ✓ |
| `/portal/guardian/child/<int:student_id>/fees/<int:payment_id>/receipt/` | GuardianChildFeeReceiptPDFView | :guardian_portal:download_receipt | GET | ✓ |
| `/portal/guardian/child/<int:student_id>/profile/` | GuardianChildDetailView | :guardian_portal:child_detail | GET | ✓ |
| `/portal/guardian/child/<int:student_id>/transcript/` | child_transcript | :guardian_portal:child_transcript | GET, POST | ✓ |
| `/portal/guardian/child/<int:student_id>/transcript/pdf/` | StudentTranscriptPDFView | :guardian_portal:child_transcript_pdf | GET | ✓ |
| `/portal/guardian/children/` | GuardianChildrenView | :guardian_portal:my_children | GET |  |
| `/portal/guardian/children/<int:student_id>/` | GuardianChildDetailView | :guardian_portal:child_detail_old | GET | ✓ |
| `/portal/guardian/children/<int:student_id>/attendance/` | GuardianChildAttendanceView | :guardian_portal:child_attendance_old | GET | ✓ |
| `/portal/guardian/children/<int:student_id>/exams/` | GuardianChildExamsView | :guardian_portal:child_exams_old | GET | ✓ |
| `/portal/guardian/children/<int:student_id>/payments/` | GuardianChildFeesView | :guardian_portal:child_payments_old | GET | ✓ |
| `/portal/guardian/dashboard/` | GuardianDashboardView | :guardian_portal:dashboard | GET |  |
| `/portal/guardian/notifications/` | GuardianNotificationListView | :guardian_portal:notification_list | GET |  |
| `/portal/guardian/notifications/<int:pk>/` | GuardianNotificationDetailView | :guardian_portal:notification_detail | GET | ✓ |
| `/portal/guardian/notifications/mark-read/` | GuardianNotificationMarkReadView | :guardian_portal:notification_mark_read | POST |  |
| `/portal/student/attendance/` | StudentAttendanceView | :student_portal:my_attendance | GET |  |
| `/portal/student/dashboard/` | StudentDashboardView | :student_portal:dashboard | GET |  |
| `/portal/student/enrollment/` | my_enrollment | :student_portal:my_enrollment | GET, POST |  |
| `/portal/student/exams/` | StudentExamsView | :student_portal:my_exams | GET |  |
| `/portal/student/exams/<int:pk>/` | exam_result_detail | :student_portal:exam_result_detail | GET, POST | ✓ |
| `/portal/student/fees/` | StudentFeesView | :student_portal:my_fees | GET |  |
| `/portal/student/fees/<int:payment_id>/receipt/` | StudentFeeReceiptPDFView | :student_portal:download_receipt | GET | ✓ |
| `/portal/student/notifications/` | StudentNotificationListView | :student_portal:notification_list | GET |  |
| `/portal/student/notifications/<int:pk>/` | StudentNotificationDetailView | :student_portal:notification_detail | GET | ✓ |
| `/portal/student/notifications/mark-read/` | StudentNotificationMarkReadView | :student_portal:notification_mark_read | POST |  |
| `/portal/student/password/` | StudentPasswordChangeView | :student_portal:password_change | GET, POST, PUT |  |
| `/portal/student/payments/` | StudentFeesView | :student_portal:my_payments | GET |  |
| `/portal/student/profile/` | StudentProfileView | :student_portal:profile_view | GET, POST |  |
| `/portal/student/timetable/` | student_timetable | :student_portal:timetable | GET, POST |  |
| `/portal/student/transcript/` | student_transcript | :student_portal:student_transcript | GET, POST |  |
| `/portal/student/transcript/pdf/` | StudentTranscriptPDFView | :student_portal:student_transcript_pdf | GET |  |

### root

| Path | View | URL Name | Methods | Params |
|------|------|----------|---------|--------|
| `/` | RedirectView | home | GET, POST, PUT |  |
| `/success/` | PublicSuccessStoriesView | public_success | GET |  |
