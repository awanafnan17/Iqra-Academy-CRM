"""
Finance models - Payment, InstallmentPlan, Installment, Expense,
ExpenseCategory, Refund.

All money fields use DecimalField(max_digits=12, decimal_places=2).
No float. No integer approximation.

Payment is the single source of truth for all money movement.
The financial ledger is computed from Payment + Expense + Refund
records rather than stored in a separate table.
"""

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.core.abstract_models import AuditMixin, TimestampMixin


# ---------------------------------------------------------------
#  FeeStructure
# ---------------------------------------------------------------

class FeeStructure(TimestampMixin, AuditMixin, models.Model):
    session = models.ForeignKey(
        "academics.Session",
        on_delete=models.CASCADE,
        related_name="fee_structures",
    )
    FEE_TYPE_CHOICES = [
        ("one_time", "One Time Payment"),
        ("monthly", "Monthly Installments"),
    ]
    fee_type = models.CharField(
        max_length=20,
        choices=FEE_TYPE_CHOICES,
        default="one_time",
        verbose_name="Fee Type",
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    number_of_installments = models.PositiveIntegerField(
        default=1,
        help_text="Number of monthly installments. Use 1 for one-time payment.",
    )
    monthly_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Amount per monthly installment.",
    )
    due_day = models.PositiveIntegerField(
        default=10,
        help_text="Day of month payment is due (1-28).",
    )

    def __str__(self):
        return f"Fee Structure for {self.session}"

# ---------------------------------------------------------------
#  Payment
# ---------------------------------------------------------------

class Payment(TimestampMixin, AuditMixin, models.Model):
    """Fee payment record - the single source of truth for revenue.

    Payment status:
    - pending: placeholder or unpaid installment slot.
    - confirmed: actual payment received.
    - refunded: payment reversed (linked to Refund record).

    The is_late_fee_payment flag enables clean separation of late
    fee income from tuition revenue in reporting.
    """

    PAYMENT_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("refunded", "Refunded"),
    ]
    PAYMENT_METHOD_CHOICES = [
        ("Cash", "Cash"),
        ("BankTransfer", "Bank Transfer"),
        ("Online", "Online Payment"),
        ("Cheque", "Cheque"),
        ("Other", "Other"),
    ]

    enrollment = models.ForeignKey(
        "students.Enrollment",
        on_delete=models.PROTECT,
        related_name="payments",
        help_text="Which enrollment this payment is for.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Payment amount. Always >= 0.",
    )
    payment_date = models.DateField(
        db_index=True,
        help_text="Date payment was received.",
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="Cash",
        help_text="How the payment was made.",
    )
    payment_status = models.CharField(
        max_length=15,
        choices=PAYMENT_STATUS_CHOICES,
        default="confirmed",
        db_index=True,
        help_text="Current payment status.",
    )
    receipt_number = models.CharField(
        max_length=30,
        null=True,
        blank=True,
        db_index=True,
        help_text="Auto-generated receipt identifier. Uniqueness enforced in clean().",
    )
    reference_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Bank or online transaction reference.",
    )
    month = models.CharField(
        max_length=7,
        null=True,
        blank=True,
        db_index=True,
        help_text="YYYY-MM for monthly sessions and late fee tracking.",
    )
    is_late_fee_payment = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Separates late fee from regular revenue.",
    )
    late_fee_waived = models.BooleanField(
        default=False,
        help_text="Whether this is a waiver record.",
    )
    late_fee_waiver_reason = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Reason for late fee waiver.",
    )
    late_fee_waived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_late_fee_waivers",
        help_text="Who approved the late fee waiver.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Payment notes or remarks.",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_payments",
        help_text="Staff who recorded this payment. Null if user was deleted.",
    )

    class Meta:
        ordering = ["-payment_date", "-pk"]
        indexes = [
            models.Index(
                fields=["enrollment", "payment_status"],
                name="idx_pay_enroll_status",
            ),
            models.Index(
                fields=["payment_status", "is_late_fee_payment"],
                name="idx_pay_status_latefee",
            ),
        ]
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def clean(self):
        super().clean()
        if self.receipt_number:
            qs = Payment.objects.filter(receipt_number=self.receipt_number)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError({
                    "receipt_number": (
                        f"Receipt number '{self.receipt_number}' already exists."
                    )
                })

    def __str__(self):
        return f"Rs.{self.amount} - {self.enrollment} ({self.payment_status})"


# ---------------------------------------------------------------
#  InstallmentPlan
# ---------------------------------------------------------------

class InstallmentPlan(TimestampMixin, AuditMixin, models.Model):
    """Installment plan header for an enrollment.

    ForeignKey to Enrollment allows plan restructuring: deactivate
    the old plan and create a new one. Only one active plan per
    enrollment is enforced via clean() validation.
    """

    enrollment = models.ForeignKey(
        "students.Enrollment",
        on_delete=models.PROTECT,
        related_name="installment_plans",
        help_text="The enrollment this plan belongs to.",
    )
    total_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Total amount being split into installments.",
    )
    number_of_installments = models.PositiveSmallIntegerField(
        help_text="How many installments.",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this plan is currently active.",
    )
    notes = models.TextField(
        null=True,
        blank=True,
        help_text="Plan notes or special terms.",
    )

    class Meta:
        indexes = [
            models.Index(
                fields=["enrollment", "is_active"],
                name="idx_instplan_enroll_active",
            ),
        ]
        verbose_name = "Installment Plan"
        verbose_name_plural = "Installment Plans"

    def clean(self):
        super().clean()
        if self.number_of_installments and self.number_of_installments < 1:
            raise ValidationError({
                "number_of_installments": "Must have at least 1 installment."
            })

        if self.is_active and self.enrollment_id:
            conflict = InstallmentPlan.objects.filter(
                enrollment_id=self.enrollment_id,
                is_active=True,
            )
            if self.pk:
                conflict = conflict.exclude(pk=self.pk)
            if conflict.exists():
                raise ValidationError({
                    "enrollment": (
                        "An active installment plan already exists for "
                        "this enrollment. Deactivate it before creating "
                        "a new one."
                    )
                })

    def __str__(self):
        status = "ACTIVE" if self.is_active else "inactive"
        return f"Plan ({status}): {self.enrollment} - {self.number_of_installments} installments"


# ---------------------------------------------------------------
#  Installment
# ---------------------------------------------------------------

class Installment(TimestampMixin, models.Model):
    """Individual installment within an installment plan.

    Status is denormalized for query performance. The service
    layer must keep it in sync with paid_amount vs amount.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("partial", "Partially Paid"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
    ]

    plan = models.ForeignKey(
        InstallmentPlan,
        on_delete=models.CASCADE,
        related_name="installments",
        help_text="Parent installment plan.",
    )
    installment_number = models.PositiveSmallIntegerField(
        help_text="Sequence number within the plan (1, 2, 3...).",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Amount due for this installment.",
    )
    due_date = models.DateField(
        db_index=True,
        help_text="When this installment is due.",
    )
    paid_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Amount actually paid against this installment.",
    )
    paid_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this installment was paid.",
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Current installment payment status.",
    )
    payment = models.ForeignKey(
        Payment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="installment_links",
        help_text="Linked payment record when paid.",
    )

    class Meta:
        unique_together = [("plan", "installment_number")]
        ordering = ["installment_number"]
        indexes = [
            models.Index(
                fields=["plan", "installment_number"],
                name="idx_inst_plan_number",
            ),
        ]
        verbose_name = "Installment"
        verbose_name_plural = "Installments"

    def __str__(self):
        return f"#{self.installment_number} - Rs.{self.amount} ({self.status})"


# ---------------------------------------------------------------
#  ExpenseCategory
# ---------------------------------------------------------------

class ExpenseCategory(TimestampMixin, models.Model):
    """Predefined expense categories for consistent reporting.

    Examples: Rent, Utilities, Salaries, Supplies, Marketing.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Category name (e.g., Rent, Utilities).",
    )
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Category description.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this category is currently in use.",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Expense Category"
        verbose_name_plural = "Expense Categories"

    def __str__(self):
        return self.name


# ---------------------------------------------------------------
#  Expense
# ---------------------------------------------------------------

class Expense(TimestampMixin, AuditMixin, models.Model):
    """Academy expense record with approval workflow."""

    STATUS_CHOICES = [
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    category = models.ForeignKey(
        ExpenseCategory,
        on_delete=models.PROTECT,
        related_name="expenses",
        help_text="Expense category.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Expense amount.",
    )
    expense_date = models.DateField(
        db_index=True,
        help_text="When the expense occurred.",
    )
    description = models.TextField(
        help_text="What the expense was for.",
    )
    receipt_file = models.FileField(
        upload_to="expense_receipts/",
        null=True,
        blank=True,
        help_text="Scan of expense receipt.",
    )
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_expenses",
        help_text="Staff who recorded this expense. Null if user was deleted.",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_expenses",
        help_text="Staff who approved this expense.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Approval workflow status.",
    )
    rejection_reason = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Reason if the expense was rejected.",
    )

    class Meta:
        ordering = ["-expense_date"]
        indexes = [
            models.Index(
                fields=["expense_date", "status"],
                name="idx_expense_date_status",
            ),
        ]
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"

    def __str__(self):
        return f"Rs.{self.amount} - {self.category.name} ({self.expense_date})"


# ---------------------------------------------------------------
#  Refund
# ---------------------------------------------------------------

class Refund(TimestampMixin, AuditMixin, models.Model):
    """Refund record linked to an original payment.

    Separate from Payment to provide explicit audit trail,
    approval workflow, and prevent confusion in revenue
    calculations.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("processed", "Processed"),
        ("rejected", "Rejected"),
    ]

    payment = models.ForeignKey(
        Payment,
        on_delete=models.PROTECT,
        related_name="refunds",
        help_text="The original payment being refunded.",
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        help_text="Refund amount. Can be partial.",
    )
    reason = models.TextField(
        help_text="Reason for the refund.",
    )
    refund_date = models.DateField(
        db_index=True,
        help_text="When the refund was processed.",
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default="pending",
        db_index=True,
        help_text="Refund approval status.",
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_refunds",
        help_text="Staff who processed the refund.",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_refunds",
        help_text="Staff who approved the refund.",
    )

    class Meta:
        ordering = ["-refund_date"]
        verbose_name = "Refund"
        verbose_name_plural = "Refunds"

    def clean(self):
        """Ensure cumulative refunds do not exceed original payment."""
        super().clean()
        if not self.payment_id or not self.amount:
            return

        existing_refunds_qs = Refund.objects.filter(
            payment_id=self.payment_id,
        ).exclude(
            status="rejected",
        )

        if self.pk:
            existing_refunds_qs = existing_refunds_qs.exclude(pk=self.pk)

        already_refunded = existing_refunds_qs.aggregate(
            total=models.Sum("amount"),
        )["total"] or Decimal("0.00")

        available = self.payment.amount - already_refunded

        if self.amount > available:
            raise ValidationError({
                "amount": (
                    f"Refund amount Rs.{self.amount} exceeds available "
                    f"refundable balance Rs.{available} "
                    f"(original payment Rs.{self.payment.amount}, "
                    f"already refunded Rs.{already_refunded})."
                )
            })

    def __str__(self):
        return f"Refund Rs.{self.amount} on Payment #{self.payment_id}"
