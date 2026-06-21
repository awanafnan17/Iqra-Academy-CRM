# CRM Finance Integrity Audit

This report documents the financial discovery audit of the Iqra Academy CRM, analyzing risks, validation rules, and structural consistency.

---

## 1. Single Source of Truth & Ledger Consistency
The CRM implements a calculated ledger pattern rather than storing static ledger balances in a dedicated database table. Balance sheets and ledger summaries are derived dynamically from:
*   `Payment` (tuition receipts, late fee records, waiver placeholders)
*   `Refund` (reversal entries)
*   `Expense` (outward operational costs)

This ensures perfect ledger consistency because the balances cannot drift from the underlying transactions.

---

## 2. Risk Assessment by Sub-Category

### Payment Creation & Method Validation
*   **Status**: PASS
*   **Assessment**: All payments call `.full_clean()` before saving and utilize database transactions (`transaction.atomic()`). Allowed methods are strictly constrained to standard choices: `Cash`, `BankTransfer`, `Online`, `Cheque`, and `Other`.

### Receipt Uniqueness & Collision Protection
*   **Status**: PASS
*   **Assessment**: Receipt numbers follow the pattern `RCP-YYYYMMDD-NNNNN`. Unique constraint checks are executed in `Payment.clean()` to catch collisions. Furthermore, `create_payment` services implement a 3-attempt collision retry block to avoid sequence collision under concurrent saves.

### Installments & Partial Payments
*   **Status**: PASS
*   **Assessment**: Installment calculations divide total amounts evenly, with any remaining rounding decimals allocated to the final installment. Partial payments are logged cleanly, transitioning the installment status from `pending` to `partial` and updating `paid_amount` atomically.

### Overpayment Behavior
*   **Status**: PASS
*   **Assessment**: The `record_installment_payment` service validates that `amount_paid` cannot exceed the remaining balance of the installment.
```python
if amount_paid > remaining:
    raise ValidationError(f"Amount PKR {amount_paid} exceeds remaining balance of PKR {remaining}.")
```

### Discounts and Waivers
*   **Status**: PASS
*   **Assessment**: Student discounts directly subtract from the active enrollment's ledger total during computation. Late fee waivers are recorded as zero-amount payment entries (`amount=0.00`, `late_fee_waived=True`), which cleanly prevents future late fee applications for the waived month.

### Refund Upper Limit Constraint
*   **Status**: PASS
*   **Assessment**: Cumulative refund checks are enforced in the model's `clean()` method and locked inside `process_refund` services using `select_for_update()`. This prevents double-refund race conditions.

### Dashboard Finance Metrics
*   **Status**: PASS
*   **Assessment**: The service layer calculates total revenue using Django database aggregates (`Sum`, `Coalesce`) to avoid float representation issues or empty database null pointer exceptions.

### Delete & Edit Payment Safety (Immutability)
*   **Status**: PASS
*   **Assessment**: Confirmed payments are guarded against modification. Once a payment has a status of `confirmed`, any attempt to edit its `amount` or `enrollment` links raises a validation error in `_verify_payment_immutability`.

### Decimal Precision & Value Safeguards
*   **Status**: PASS
*   **Assessment**: All money fields use `DecimalField(max_digits=12, decimal_places=2)`. No floats are used. All money models validate that amounts are positive (`MinValueValidator(Decimal("0.00"))`).

---

## 3. Findings & Performance Risks

### [RR-010] N+1 Query in PDF Success Selections Report
*   **Priority**: HIGH
*   **Impact**: Loops over student achievements and executes queries to retrieve the active enrollment of the student.
*   **Location**: `apps/reports/views.py` lines 298-300.
*   **Recommendation**: Prefetch enrollment records or perform SQL joins.

### [RR-011] N+1 Query in Teacher Workload Report
*   **Priority**: HIGH
*   **Impact**: Inside the loop for faculty profiles, it calls `.filter(is_active=True)` on teaching assignments, bypassing prefetch cache.
*   **Location**: `apps/reports/views.py` line 171.
*   **Recommendation**: Filter prefetched records in Python memory using list comprehensions.
