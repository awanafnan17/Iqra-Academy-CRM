"""
Finance app URL patterns.

Included by admin_panel under prefix 'finance/'.
"""

from django.urls import path

from apps.core.decorators import role_required
from apps.finance import views

app_name = "finance"

urlpatterns = [
    # Payments
    path("payments/", views.payment_list, name="payment_list"),
    path("payments/create/", views.payment_create, name="payment_create"),
    path("payments/<int:pk>/", views.payment_detail, name="payment_detail"),
    path("payments/<int:pk>/delete/", views.payment_delete, name="payment_delete"),

    # Installments
    path("installments/<int:pk>/pay/", views.installment_pay, name="installment_pay"),

    # Expenses
    path("expenses/", views.expense_list, name="expense_list"),
    path("expenses/create/", views.expense_create, name="expense_create"),
    path("expenses/categories/", views.expense_category_list, name="expense_category_list"),
    path("expenses/categories/create/", views.expense_category_create, name="expense_category_create"),
    path("expenses/<int:pk>/", views.expense_detail, name="expense_detail"),
    path(
        "expenses/<int:pk>/approve/",
        role_required("Admin")(views.expense_approve),
        name="expense_approve",
    ),
    path(
        "expenses/<int:pk>/reject/",
        role_required("Admin")(views.expense_reject),
        name="expense_reject",
    ),

    # Refunds
    path("refunds/", views.refund_list, name="refund_list"),
    path("refunds/create/", views.refund_create, name="refund_create"),

    # Installment plans
    path("installments/", views.installment_plan_list, name="installment_plan_list"),
    path("installments/create/", views.installment_plan_create, name="installment_plan_create"),
    path("installments/<int:pk>/", views.installment_plan_detail, name="installment_plan_detail"),
    path("installments/<int:pk>/restructure/", views.installment_restructure, name="installment_restructure"),
    path(
        "installments/pay/<int:pk>/",
        views.installment_pay,
        name="installment_pay",
    ),

    # Overdue and late fees
    path("overdue/", views.overdue_list, name="overdue_list"),
    path("late-fees/apply/", views.late_fee_apply, name="late_fee_apply"),
    path("late-fees/waive/<int:pk>/", views.late_fee_waive, name="late_fee_waive"),
    path("send-fee-reminder/", views.send_fee_reminder, name="send_fee_reminder"),
]

