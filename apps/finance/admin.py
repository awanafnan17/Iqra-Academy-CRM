"""
Finance admin - Payment, InstallmentPlan, Installment, Expense,
ExpenseCategory, Refund.
"""

from django.contrib import admin

from apps.finance.models import (
    Expense,
    ExpenseCategory,
    Installment,
    InstallmentPlan,
    Payment,
    Refund,
)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment admin with immutability on confirmed status.

    Confirmed payments block edits on amount, enrollment,
    and payment_method via get_readonly_fields().
    """

    list_display = (
        "enrollment",
        "amount",
        "payment_date",
        "payment_method",
        "payment_status",
        "receipt_number",
        "is_late_fee_payment",
        "recorded_by",
    )
    list_filter = ("payment_status", "payment_method", "is_late_fee_payment")
    search_fields = (
        "enrollment__student__full_name",
        "receipt_number",
        "reference_number",
    )
    ordering = ("-payment_date", "-pk")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "payment_date"
    autocomplete_fields = ("enrollment",)

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and obj.payment_status == "confirmed":
            base.extend(["amount", "enrollment", "payment_method"])
        return base


class InstallmentInline(admin.TabularInline):
    """Inline for installments within an installment plan."""

    model = Installment
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(InstallmentPlan)
class InstallmentPlanAdmin(admin.ModelAdmin):
    """Installment plan admin with installment inline."""

    list_display = (
        "enrollment",
        "total_amount",
        "number_of_installments",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active",)
    search_fields = (
        "enrollment__student__full_name",
        "enrollment__session__name",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    inlines = [InstallmentInline]


@admin.register(Installment)
class InstallmentAdmin(admin.ModelAdmin):
    """Standalone installment admin."""

    list_display = (
        "plan",
        "installment_number",
        "amount",
        "due_date",
        "paid_amount",
        "status",
    )
    list_filter = ("status",)
    search_fields = ("plan__enrollment__student__full_name",)
    ordering = ("plan", "installment_number")
    readonly_fields = ("created_at", "updated_at")


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Expense category admin."""

    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """Expense admin with read-only recorded_by and created_by."""

    list_display = (
        "category",
        "amount",
        "expense_date",
        "status",
        "recorded_by",
        "approved_by",
    )
    list_filter = ("status", "category")
    search_fields = ("description", "category__name")
    ordering = ("-expense_date",)
    readonly_fields = ("created_at", "updated_at", "recorded_by", "created_by")
    date_hierarchy = "expense_date"


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Refund admin with full immutability on processed status.

    Processed refunds block all field edits via get_readonly_fields().
    """

    list_display = (
        "payment",
        "amount",
        "refund_date",
        "status",
        "processed_by",
        "approved_by",
    )
    list_filter = ("status",)
    search_fields = (
        "payment__enrollment__student__full_name",
        "payment__receipt_number",
        "reason",
    )
    ordering = ("-refund_date",)
    readonly_fields = ("created_at", "updated_at")

    def get_readonly_fields(self, request, obj=None):
        base = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == "processed":
            base = [f.name for f in self.model._meta.fields]
        return base
