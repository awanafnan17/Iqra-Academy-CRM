# Final Admin User Guide

This guide assists system administrators in managing the Iqra Academy CRM.

## 1. Staff and Role Management
The system utilizes group-based permissions to isolate user tasks:
* **Creating Staff Accounts:** Create a user account, then add the user to the correct group (Admin, Principal, Registrar, Teacher, Accountant) in the Django admin interface.
* **Portal Users:** Student and Guardian accounts are created automatically when student files are saved.

## 2. Managing Admissions
* **Reviewing Applications:** Go to the admissions module. You can review submissions, reject invalid files, or approve candidates.
* **Converting to Student:** When an application is approved, click the convert option. The system creates the student profile, sets up their primary enrollment, and generates a portal account.

## 3. Student Profiles and Documents
* **Registering Students:** Use the student create view. You can upload a CNIC photo directly on this form.
* **Managing Uploads:** Access the student details view, then navigate to the Manage Documents panel to view, add, or delete identification records.
* **Financial Ledger:** Check outstanding tuition costs on the ledger subpage.

## 4. Academic Sessions and Attendance
* **Structuring Sessions:** Create sessions, assign fee matrices, and configure classroom schedules.
* **Attendance Logs:** Teachers mark attendance on their portal. Administrators can review logs on the attendance overview panel and use lock actions to prevent historical modifications.

## 5. Audit Log Inspector
* **Accessing Logs:** Navigate to the Audit Logs sidebar link.
* **Searching Events:** View timestamped logs of all actions performed by staff members, including creation, modification, and deletion events.

## 6. AI Engine Administration
* **Inference Logs:** Open the AI predictions view to review historical dropout risk alerts.
* **Model Versions:** View active analytical models to monitor active evaluation versions.
