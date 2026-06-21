# Release Navigation & Route Discoverability Audit Report

This report outlines the navigation, sidebar discoverability, and routing audit performed after implementing Batch 2E. The audit covers all 11 system modules and assesses visibility, security, and links for all 8 user roles (Admin, Principal, Registrar, Teacher, Accountant, Student, Guardian, and Anonymous).

---

## 1. Sidebar/Menu Inventory by Role

### Admin
* **Dashboard Section**: Dashboard (`admin_panel:dashboard`), Analytics (`admin_panel:analytics`), Session Overview (`admin_panel:session_overview`), Reports & Exports (`reports:dashboard`).
* **Academic Management Section**: Add Student (`admin_panel:add_student`), Manage Students (`admin_panel:manage_students`), Add Session (`admin_panel:add_session`), Manage Sessions (`admin_panel:session_overview`), Manage Faculty (`admin_panel:faculty_overview`), Exams (`admin_panel:exam_overview`), Class Timetable (`admin_panel:timetable_overview`), PDF Comparison (`admin_panel:pdf_comparison`).
* **Admissions Section**: Applications (`admin_panel:admissions:admission_list`), Summary & Metrics (`admin_panel:admissions:admission_summary`).
* **Finance Section**: Payments (`admin_panel:finance:payment_list`), Expenses (`admin_panel:finance:expense_list`), Refund Request (`admin_panel:finance:refund_list`), Installment Plans (`admin_panel:finance:installment_plan_list`), Overdue Payments (`admin_panel:finance:overdue_list`), Pending Dues (`admin_panel:pending_dues`).
* **Notifications Section**: Send Alert (`admin_panel:notifications:notification_bulk_send`), Email Logs (`admin_panel:notifications:email_log_list`).
* **Automation Section**: System Alerts (`admin_panel:automation_alerts`), Background Jobs (`admin_panel:automation_jobs`).
* **Administration Section**: Permission Matrix (`admin_panel:permissions`), User Management (`admin_panel:users:user_list`).

### Principal
* **Dashboard Section**: Dashboard (`admin_panel:dashboard`), Analytics (`admin_panel:analytics`), Session Overview (`admin_panel:session_overview`), Reports & Exports (`reports:dashboard`).
* **Academic Management Section**: Manage Students (`admin_panel:manage_students`), Manage Sessions (`admin_panel:session_overview`), Manage Faculty (`admin_panel:faculty_overview`), Exams (`admin_panel:exam_overview`), Class Timetable (`admin_panel:timetable_overview`), PDF Comparison (`admin_panel:pdf_comparison`).
* **Finance Section**: Payments (`admin_panel:finance:payment_list`), Overdue Payments (`admin_panel:finance:overdue_list`), Pending Dues (`admin_panel:pending_dues`).

### Registrar
* **Dashboard Section**: Dashboard (`registrar_panel:dashboard`).
* **Academic Management Section**: Manage Students (`registrar_panel:student_list`), Leads (`registrar_panel:lead_list`).
* **Admissions Section**: Applications (`registrar_panel:admissions:admission_list`), Summary & Metrics (`registrar_panel:admissions:admission_summary`).

### Teacher
* **Dashboard Section**: Dashboard (`teacher_panel:dashboard`).
* **Academic Management Section**: My Sessions (`teacher_panel:my_sessions`), Exams (`teacher_panel:my_exams`), My Timetable (`teacher_panel:my_timetable`).
* **Notifications Section**: Notifications (`teacher_panel:notification_list`).

### Accountant
* **Dashboard Section**: Dashboard (`accounts_panel:dashboard`), Reports & Exports (`accounts_panel:reports_dashboard`).
* **Finance Section**: Payments (`accounts_panel:payment_list`), Expenses (`accounts_panel:expense_list`), Refund Request (`accounts_panel:refund_list`), Installment Plans (`accounts_panel:installment_plan_list`), Overdue Payments (`accounts_panel:overdue_list`), Pending Dues (`accounts_panel:pending_dues`).

### Student
* **Dashboard Section**: Dashboard (`student_portal:dashboard`).
* **Academic Management Section**: Enrollment (`student_portal:my_enrollment`), Attendance (`student_portal:my_attendance`), Exams & Grades (`student_portal:my_exams`), Academic Transcript (`student_portal:student_transcript`), Class Timetable (`student_portal:timetable`).
* **Finance Section**: Payments (`student_portal:my_payments`).
* **Notifications Section**: Notifications (`student_portal:notification_list`).

### Guardian
* **Dashboard Section**: Dashboard (`guardian_portal:dashboard`).
* **Academic Management Section**: Children (`guardian_portal:my_children`).
* **Notifications Section**: Notifications (`guardian_portal:notification_list`).

---

## 2. Missing Sidebar Links (Discoverability Gaps)

The following completed release-ready features are functional but have no entry points in the sidebar navigation:

1. **Audit Logs (Batch 2D)**:
   * *Status*: Functional list/detail pages exist.
   * *Missing Link*: Under the "Administration" section for `Admin` role.
   * *Path/URL*: `/panel/admin/audit/` (`admin_panel:audit:audit_log_list`).
2. **AI Engine Predictions (Batch 2E)**:
   * *Status*: Functional predictions list/detail pages exist.
   * *Missing Link*: Under a new "AI Engine" section for `Admin` role.
   * *Path/URL*: `/panel/admin/ai/predictions/` (`admin_panel:ai_engine:prediction_list`).
3. **AI Engine Models (Batch 2E)**:
   * *Status*: Functional models list exists.
   * *Missing Link*: Under a new "AI Engine" section for `Admin` role.
   * *Path/URL*: `/panel/admin/ai/models/` (`admin_panel:ai_engine:model_version_list`).
4. **AI Engine Dropout Risk Dashboard (Batch 2E)**:
   * *Status*: Functional risk dashboards exist.
   * *Missing Link*: For `Admin` and `Principal` roles.
   * *Path/URL*: `/panel/admin/ai/dropout-risk/` (`admin_panel:ai_engine:dropout_risk_dashboard`).
5. **Attendance Management (Batch 1B-3A)**:
   * *Status*: Functional attendance overview and low attendance report exist.
   * *Missing Link*: "Attendance Overview" and "Low Attendance Report" for `Admin`, and "Low Attendance Report" for `Principal`.
   * *Path/URL*: `/panel/admin/attendance/` (`admin_panel:attendance:attendance_overview`) & `/panel/admin/attendance/low-report/` (`admin_panel:attendance:low_attendance_report`).
6. **Exams Grade Configurations (Batch 2C)**:
   * *Status*: Functional grade configurations list/create/edit exist.
   * *Missing Link*: For `Admin` and `Principal` roles.
   * *Path/URL*: `/panel/admin/exams/grade-config/` (`admin_panel:exams:grade_config_list`).

---

## 3. Broken, Stale, or Unauthorized-Visible Links

* **Broken Links**: None. All sidebar links render and resolve to valid view targets.
* **Stale Links**: The Admin sidebar has a duplicate link: `Session Overview` (under Dashboard section) and `Manage Sessions` (under Academic Management) both resolve to the same page (`admin_panel:session_overview`).
* **Unauthorized-Visible Links**: None. Sidebar sections are cleanly isolated by primary role group in `templates/components/sidebar.html` using an `if-elif` chain. Unprivileged roles do not see links for Admin/Principal sections.

---

## 4. Hidden-but-Working / Intentionally Hidden Routes

Certain views are intentionally hidden from direct sidebar navigation as they represent contextual detail views or sub-flows:
1. **Student Detail & Reset Password**: Contextual to a selected student.
2. **Session Enrollments**: Contextual sub-list accessible from the Session Detail page for a given session.
3. **Session Revenue**: Financial summary accessible from the Session Detail page for a given session.
4. **Exam Detail & Statistics**: Contextual detail pages accessible from the Exam Overview list.
5. **Admissions Application Review/Actions**: Accessed from the Admissions Application detail page.

---

## 5. UI Dashboard Discoverability Improvements

Two metrics cards on the dashboards represent critical starting points for core workflows but lack direct hyperlinking:
* **Admin Dashboard**: Card for "Active Dropout Alerts" should link to the AI Dropout Dashboard (`admin_panel:ai_engine:dropout_risk_dashboard`).
* **Principal Dashboard**: Card for "Dropout Risk Alerts" should link to the AI Dropout Dashboard (`admin_panel:ai_engine:dropout_risk_dashboard`).

---

## 6. Audit Verdict & Final Status

* **Is navigation release-ready?**: **No.** While the backend views are secure and fully functional, critical features like **Audit Logs**, **AI Engine**, **Attendance Management**, and **Exams Grade Configs** cannot be reached by clicking any menu items. They are hidden from administrators and principals.
* **Can Batch 2E be accepted as-is?**: Yes. The AI cleanup views are correctly implemented, robustly tested, and fully secured at the route level.
* **Are navigation fixes needed before final re-audit?**: Yes. Resolving the sidebar and dashboard card discoverability gaps is required to make the CRM fully usable and release-ready.

### Recommended Fix Batch (Batch 2F):
Modify `templates/components/sidebar.html` and `templates/dashboard/admin.html`/`principal.html` to add the missing entry points for the completed modules.

**Final Status**: `NAV_AUDIT_FIXES_NEEDED`
