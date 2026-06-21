# CRM Data Integrity Audit

This report maps the database integrity, checks for orphans or duplicate constraints, and documents transactions behavior in the Iqra Academy CRM.

---

## 1. Database Scan Results (db_demo.sqlite3)

| Check Description | Query Method / Target | Result | Status / Finding |
|---|---|---|---|
| **Orphan Students** | Students without User profiles or enrollments | 5 unenrolled | **PASS (Expected)**: Students registered but not yet enrolled (ID: 2, 3, 4, 5, 6). |
| **Orphan Enrollments** | Enrollments without Student or Session links | 0 occurrences | **PASS**: Enforced by ForeignKey NOT NULL constraint. |
| **Orphan Guardians** | Guardians with null Student links | 0 occurrences | **PASS**: Enforced by ForeignKey NOT NULL constraint. |
| **Orphan Documents** | Student Documents without a linked Student | 0 occurrences | **PASS**: Enforced by ForeignKey CASCADE / NOT NULL constraint. |
| **Payments without Enrollment**| Payment records missing Enrollment reference | 0 occurrences | **PASS**: Enforced by ForeignKey NOT NULL constraint. |
| **Receipts without Payment** | Receipt numbers in database without Payment | 0 occurrences | **PASS**: Receipts are fields on the Payment model. |
| **Attendance without Student** | Attendance records missing Student reference | 0 occurrences | **PASS**: Enforced by ForeignKey NOT NULL constraint. |
| **Duplicate Roll Numbers** | Multi-student matching roll number values | 0 occurrences | **PASS**: Enforced by automatic unique roll prefix backfill generator. |
| **Duplicate Enrollments** | Active student with multiple Active sessions | 0 occurrences | **PASS**: Unique constraints and view validators prevent this. |
| **Duplicate Active Sessions** | Multiple active academic sessions for same code | 0 occurrences | **PASS**: Enforced by unique constraint validation. |

---

## 2. Inconsistencies & Structural Risks

### [RR-013] Active Session Dropdown Mismatch
*   **Description**: In `StudentCreateForm`, session filtering query uses `status="active"` (lowercase), while the database saves `status="Active"`.
*   **Impact**: Creates an operational dead-end where it is impossible to enroll a student in any session during creation.

### SQLite Foreign Key Cascades & Constraints
*   **Description**: SQLite database engine does not enforce foreign key referential integrity constraints by default.
*   **Impact**: Risk of orphans if direct raw database modifications are made outside the Django ORM.
*   **Remedy**: The CRM relies entirely on Django's ORM which does cascade validation and deletion emulation in application space.

---

## 3. Transaction Rollback & File Cleanup Behavior
*   **Transactions**: Database mutations (like student creation and enrollment) are wrapped in `transaction.atomic()`, ensuring partial failures rollback the database state.
*   **Physical Files**: When student creation fails validation after uploading a profile photo or CNIC document, the physical files would normally remain on the disk as orphans.
*   **Cleanup Implementation**: The `student_create` view implements custom exception wrappers that track paths of newly uploaded files and delete them from the file system if the transaction rolls back or fails to commit.
```python
except Exception as exc:
    for filepath in uploaded_files_to_cleanup:
        if os.path.exists(filepath):
            os.remove(filepath)
```
*   **Risk**: `student_edit` does not have the same level of cleanup logic for replaced CNIC images if subsequent edits fail.
