# Form Persistence Report — Iqra Academy CRM

*Generated: 2026-06-19 22:53:16*

**Total forms audited: 51**
**Forms with issues: 27**
**Clean forms: 24**

## Forms With Issues

| File | Line | Method | Issue |
|------|------|--------|-------|
| `templates\academics\session_form.html` | 25 | POST | POST form with empty action (relies on current URL) |
| `templates\academics\timetable_form.html` | 38 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\login.html` | 134 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\password_change.html` | 17 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\profile.html` | 59 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\user_list.html` | 268 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\user_list.html` | 294 | POST | POST form with empty action (relies on current URL) |
| `templates\accounts\user_list.html` | 324 | POST | POST form with empty action (relies on current URL) |
| `templates\admissions\admission_detail.html` | 179 | POST | POST form with empty action (relies on current URL) |
| `templates\admissions\public_form.html` | 53 | POST | POST form with empty action (relies on current URL) |
| `templates\components\form.html` | 5 | POST | POST form with empty action (relies on current URL) |
| `templates\dashboard\permissions.html` | 25 | POST | POST form with empty action (relies on current URL) |
| `templates\exams\bulk_result_entry.html` | 34 | POST | POST form with empty action (relies on current URL) |
| `templates\exams\exam_create.html` | 38 | POST | POST form with empty action (relies on current URL) |
| `templates\exams\result_entry.html` | 33 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\expense_category_form.html` | 12 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\expense_form.html` | 12 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\installment_plan_form.html` | 12 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\installment_plan_restructure.html` | 15 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\payment_form.html` | 12 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\pending_dues.html` | 80 | POST | POST form with empty action (relies on current URL) |
| `templates\finance\refund_form.html` | 12 | POST | POST form with empty action (relies on current URL) |
| `templates\notifications\bulk_send_form.html` | 14 | POST | POST form with empty action (relies on current URL) |
| `templates\notifications\template_form.html` | 25 | POST | POST form with empty action (relies on current URL) |
| `templates\staff\faculty_assign.html` | 46 | POST | POST form with empty action (relies on current URL) |
| `templates\staff\faculty_form.html` | 33 | POST | POST form with empty action (relies on current URL) |
| `templates\students\student_form.html` | 101 | POST | POST form with empty action (relies on current URL) |

## All Forms Summary

| File | Line | Method | Action | CSRF | Fields | Issues |
|------|------|--------|--------|------|--------|--------|
| `templates\academics\session_form.html` | 25 | POST |  | ✓ | 0 | 1 |
| `templates\academics\session_list.html` | 27 | GET |  | ✗ | 2 | 0 |
| `templates\academics\session_list.html` | 104 | POST | {% url  | ✓ | 0 | 0 |
| `templates\academics\timetable_form.html` | 38 | POST |  | ✓ | 0 | 1 |
| `templates\academics\timetable_list.html` | 25 | GET |  | ✗ | 1 | 0 |
| `templates\accounts\login.html` | 134 | POST |  | ✓ | 0 | 1 |
| `templates\accounts\password_change.html` | 17 | POST |  | ✓ | 0 | 1 |
| `templates\accounts\profile.html` | 59 | POST |  | ✓ | 0 | 1 |
| `templates\accounts\user_list.html` | 44 | GET |  | ✗ | 2 | 0 |
| `templates\accounts\user_list.html` | 208 | POST | {% url  | ✓ | 1 | 0 |
| `templates\accounts\user_list.html` | 222 | POST | {% url  | ✓ | 1 | 0 |
| `templates\accounts\user_list.html` | 268 | POST |  | ✓ | 1 | 1 |
| `templates\accounts\user_list.html` | 294 | POST |  | ✓ | 1 | 1 |
| `templates\accounts\user_list.html` | 324 | POST |  | ✓ | 2 | 1 |
| `templates\admissions\admission_detail.html` | 150 | POST | {% url  | ✓ | 1 | 0 |
| `templates\admissions\admission_detail.html` | 169 | POST | {% url  | ✓ | 0 | 0 |
| `templates\admissions\admission_detail.html` | 179 | POST |  | ✓ | 1 | 1 |
| `templates\admissions\admission_detail.html` | 200 | POST | {% url  | ✓ | 0 | 0 |
| `templates\admissions\admission_list.html` | 32 | GET |  | ✗ | 3 | 0 |
| `templates\admissions\public_form.html` | 53 | POST |  | ✓ | 0 | 1 |
| `templates\components\form.html` | 5 | POST |  | ✓ | 0 | 1 |
| `templates\dashboard\permissions.html` | 25 | POST |  | ✓ | 6 | 1 |
| `templates\documents\pdf_comparison.html` | 36 | POST | /panel/admin/pdf-comparison/ | ✓ | 2 | 0 |
| `templates\exams\bulk_result_entry.html` | 34 | POST |  | ✓ | 4 | 1 |
| `templates\exams\exam_create.html` | 38 | POST |  | ✓ | 9 | 1 |
| `templates\exams\exam_list.html` | 32 | GET |  | ✗ | 2 | 0 |
| `templates\exams\result_entry.html` | 33 | POST |  | ✓ | 4 | 1 |
| `templates\finance\expense_category_form.html` | 12 | POST |  | ✓ | 0 | 1 |
| `templates\finance\expense_form.html` | 12 | POST |  | ✓ | 0 | 1 |
| `templates\finance\installment_plan_detail.html` | 107 | POST | {% url  | ✓ | 3 | 0 |
| `templates\finance\installment_plan_form.html` | 12 | POST |  | ✓ | 2 | 1 |
| `templates\finance\installment_plan_restructure.html` | 15 | POST |  | ✓ | 1 | 1 |
| `templates\finance\overdue_list.html` | 55 | POST | {% url  | ✓ | 4 | 0 |
| `templates\finance\payment_form.html` | 12 | POST |  | ✓ | 0 | 1 |
| `templates\finance\pending_dues.html` | 35 | GET |  | ✗ | 4 | 0 |
| `templates\finance\pending_dues.html` | 80 | POST |  | ✓ | 2 | 1 |
| `templates\finance\refund_form.html` | 12 | POST |  | ✓ | 1 | 1 |
| `templates\notifications\bulk_send_form.html` | 14 | POST |  | ✓ | 4 | 1 |
| `templates\notifications\notification_detail.html` | 28 | POST | {% if  | ✓ | 1 | 0 |
| `templates\notifications\notification_list.html` | 14 | POST | {% if  | ✓ | 0 | 0 |
| `templates\notifications\notification_list.html` | 25 | GET |  | ✗ | 2 | 0 |
| `templates\notifications\template_form.html` | 25 | POST |  | ✓ | 0 | 1 |
| `templates\portal\notification_list.html` | 15 | POST | {% if role ==  | ✓ | 0 | 0 |
| `templates\portal\password_change.html` | 19 | POST | {% if request.resolver_match.n | ✓ | 1 | 0 |
| `templates\portal\student_profile.html` | 94 | POST | {% url  | ✓ | 0 | 0 |
| `templates\public\success_stories.html` | 78 | GET |  | ✗ | 2 | 0 |
| `templates\staff\faculty_assign.html` | 46 | POST |  | ✓ | 0 | 1 |
| `templates\staff\faculty_form.html` | 33 | POST |  | ✓ | 0 | 1 |
| `templates\students\student_detail.html` | 708 | POST | {% url  | ✓ | 1 | 0 |
| `templates\students\student_form.html` | 101 | POST |  | ✓ | 0 | 1 |
| `templates\students\student_list.html` | 25 | GET |  | ✗ | 2 | 0 |