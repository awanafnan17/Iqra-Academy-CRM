
<!--
  Run ID: e7586812-3531-4961-b8a7-9963cf879463
  Timestamp: 2026-06-21T04:38:08.943592
  Settings Module: config.settings.test
  Database: django.db.backends.sqlite3 / file:memorydb_default?mode=memory&cache=shared
  Git Tree Identifier: working_tree
  Source Evidence: field_ledger.json
-->
# Field Persistence Matrix

| Module | Model | Field | Outcome |
|--------|-------|-------|---------|
| academics | Session | academic_year | **PASS** |
| academics | Session | batch_number | **PASS** |
| academics | Session | code | **PASS** |
| academics | Session | description | **PASS** |
| academics | Session | end_date | **PASS** |
| academics | Session | fee | **PASS** |
| academics | Session | is_admission_open | **PASS** |
| academics | Session | late_fee_amount | **PASS** |
| academics | Session | late_fee_grace_days | **PASS** |
| academics | Session | late_fee_maximum | **PASS** |
| academics | Session | max_capacity | **PASS** |
| academics | Session | max_students | **PASS** |
| academics | Session | name | **PASS** |
| academics | Session | registration_fee | **PASS** |
| academics | Session | roll_prefix | **PASS** |
| academics | Session | session_category | **PASS** |
| academics | Session | session_type | **PASS** |
| academics | Session | start_date | **PASS** |
| academics | Session | status | **PASS** |
| accounts | CustomUser | first_name | **PASS** |
| accounts | CustomUser | last_name | **PASS** |
| accounts | CustomUser | phone | **PASS** |
| exams | Exam | exam_date | **PASS** |
| exams | Exam | name | **PASS** |
| exams | Exam | total_marks | **PASS** |
| exams | ExamResult | remarks | **PASS** |
| finance | Payment | payment_date | **PASS** |
| finance | Refund | refund_date | **PASS** |
| students | Lead | area_of_residence | **PASS** |
| students | Lead | follow_up_date | **PASS** |
| students | Lead | follow_up_notes | **PASS** |
| students | Lead | inquiry_date | **PASS** |
| students | Lead | inquiry_source | **PASS** |
| students | Lead | interested_session | **PASS** |
| students | Lead | loss_reason | **PASS** |
| students | Lead | name | **PASS** |
| students | Lead | phone | **PASS** |
| students | Lead | status | **PASS** |
| students | Student | address_permanent | **PASS** |
| students | Student | address_temporary | **PASS** |
| students | Student | date_of_birth | **PASS** |
| students | Student | father_name | **PASS** |
| students | Student | full_name | **PASS** |
| students | Student | gender | **PASS** |
| students | Student | inactive_reason | **PASS** |
| students | Student | phone | **PASS** |
| students | Student | status | **PASS** |
| admissions | AdmissionApplication | address | **FAIL** |
| admissions | AdmissionApplication | cnic | **FAIL** |
| admissions | AdmissionApplication | date_of_birth | **FAIL** |
| admissions | AdmissionApplication | desired_session | **FAIL** |
| admissions | AdmissionApplication | email | **FAIL** |
| admissions | AdmissionApplication | exam_type | **FAIL** |
| admissions | AdmissionApplication | father_name | **FAIL** |
| admissions | AdmissionApplication | full_name | **FAIL** |
| admissions | AdmissionApplication | phone | **FAIL** |
| exams | Exam | exam_type | **FAIL** |
| exams | Exam | passing_marks | **FAIL** |
| finance | Expense | amount | **FAIL** |
| finance | Expense | category | **FAIL** |
| finance | Expense | description | **FAIL** |
| finance | Expense | expense_date | **FAIL** |
| finance | ExpenseCategory | description | **FAIL** |
| finance | ExpenseCategory | name | **FAIL** |
| finance | InstallmentPlan | notes | **FAIL** |
| finance | InstallmentPlan | number_of_installments | **FAIL** |
| finance | InstallmentPlan | total_amount | **FAIL** |
| finance | Payment | amount | **FAIL** |
| finance | Payment | enrollment | **FAIL** |
| finance | Payment | notes | **FAIL** |
| finance | Payment | payment_method | **FAIL** |
| finance | Payment | reference_number | **FAIL** |
| finance | Refund | amount | **FAIL** |
| finance | Refund | reason | **FAIL** |
| students | Enrollment | discount | **FAIL** |
| students | Enrollment | fee | **FAIL** |
| students | Enrollment | registration_date | **FAIL** |
| students | Enrollment | registration_fee | **FAIL** |
| students | Enrollment | session | **FAIL** |
| students | Enrollment | status | **FAIL** |
| students | Enrollment | student | **FAIL** |
