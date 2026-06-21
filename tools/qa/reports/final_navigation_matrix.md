# Final Navigation Matrix

This document summarizes the sidebar discoverability and layout of the Iqra Academy CRM following the integration fixes in Batch 2F.

---

## 1. Sidebar Links Inventory by Role

### Admin Sidebar Links
- **Dashboard Section:**
  - Dashboard (`admin_panel:dashboard`)
  - Analytics (`admin_panel:analytics`)
  - Session Overview (`admin_panel:session_overview`)
  - Reports & Exports (`reports:dashboard`)
- **Academic Management Section:**
  - Add Student (`admin_panel:add_student`)
  - Manage Students (`admin_panel:manage_students`)
  - Add Session (`admin_panel:add_session`)
  - Manage Sessions (`admin_panel:session_overview`)
  - Manage Faculty (`admin_panel:faculty_overview`)
  - Exams (`admin_panel:exam_overview`)
  - Grade Configurations (`admin_panel:exams:grade_config_list`)
  - Class Timetable (`admin_panel:timetable_overview`)
  - PDF Comparison (`admin_panel:pdf_comparison`)
- **Attendance Section:**
  - Attendance Overview (`admin_panel:attendance:attendance_overview`)
  - Low Attendance Report (`admin_panel:attendance:low_attendance_report`)
- **Admissions Section:**
  - Applications (`admin_panel:admissions:admission_list`)
  - Summary & Metrics (`admin_panel:admissions:admission_summary`)
- **AI Engine Section:**
  - Dropout Dashboard (`admin_panel:ai_engine:dropout_risk_dashboard`)
  - Predictions List (`admin_panel:ai_engine:prediction_list`)
  - Model Versions (`admin_panel:ai_engine:model_version_list`)
- **Finance Section:**
  - Payments (`admin_panel:finance:payment_list`)
  - Expenses (`admin_panel:finance:expense_list`)
  - Refund Request (`admin_panel:finance:refund_list`)
  - Installment Plans (`admin_panel:finance:installment_plan_list`)
  - Overdue Payments (`admin_panel:finance:overdue_list`)
  - Pending Dues (`admin_panel:pending_dues`)
- **Notifications Section:**
  - Send Alert (`admin_panel:notifications:notification_bulk_send`)
  - Email Logs (`admin_panel:notifications:email_log_list`)
- **Automation Section:**
  - System Alerts (`admin_panel:automation_alerts`)
  - Background Jobs (`admin_panel:automation_jobs`)
- **Administration Section:**
  - Permission Matrix (`admin_panel:permissions`)
  - User Management (`admin_panel:users:user_list`)
  - Audit Logs (`admin_panel:audit:audit_log_list`)

### Principal Sidebar Links
- **Dashboard Section:** Dashboard, Analytics, Session Overview, Reports & Exports
- **Academic Management Section:** Manage Students, Manage Sessions, Manage Faculty, Exams, Grade Configurations, Class Timetable, PDF Comparison
- **Attendance Section:** Low Attendance Report
- **AI Engine Section:** Dropout Dashboard
- **Finance Section:** Payments, Overdue Payments, Pending Dues

*Note: Principal is blocked from seeing predictions, model versions, audit logs, and admin-only attendance overview.*

### Other Portal Sidebars (Registrar, Teacher, Accountant, Student, Guardian)
- **Registrar:** Dashboard, Manage Students, Leads, Applications, Summary & Metrics.
- **Teacher:** Dashboard, My Sessions, Exams, My Timetable, Notifications.
- **Accountant:** Dashboard, Reports & Exports, Payments, Expenses, Refund Request, Installment Plans, Overdue Payments, Pending Dues.
- **Student:** Dashboard, Enrollment, Attendance, Exams & Grades, Academic Transcript, Class Timetable, Payments, Notifications.
- **Guardian:** Dashboard, Children, Notifications.

---

## 2. Dashboard Card Shortcuts

- **Admin Dashboard:** Card for "Active Dropout Alerts" is wrapped in a dynamic link pointing to `/panel/admin/ai/dropout-risk/` (`admin_panel:ai_engine:dropout_risk_dashboard`).
- **Principal Dashboard:** Card for "Dropout Risk Alerts" is wrapped in a dynamic link pointing to `/panel/admin/ai/dropout-risk/` (`admin_panel:ai_engine:dropout_risk_dashboard`).
- Safe active highlights ensure clicking these shortcuts or sidebar links renders the navigation correctly.
