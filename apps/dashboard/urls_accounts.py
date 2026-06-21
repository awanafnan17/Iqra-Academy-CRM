"""
Accountant panel URL configuration.

Accessible by Accountant role only.
Panel-level access enforced by PanelAccessMiddleware.
"""

from django.urls import path

from apps.dashboard import views as dashboard_views
from apps.dashboard import views_reports
from apps.finance import views as finance_views
from apps.notifications import views as notification_views
from apps.students import views as student_views
from apps.reports import views as reports_views

app_name = "accounts_panel"

urlpatterns = [
    # Dashboard
    path("dashboard/", dashboard_views.accountant_dashboard, name="dashboard"),
    path("pending-dues/", finance_views.PendingDuesView.as_view(), name="pending_dues"),

    # Payments
    path("payments/", finance_views.payment_list, name="payment_list"),
    path("payments/create/", finance_views.payment_create, name="payment_create"),
    path("payments/<int:pk>/", finance_views.payment_detail, name="payment_detail"),

    # Expenses
    path("expenses/", finance_views.expense_list, name="expense_list"),
    path("expenses/create/", finance_views.expense_create, name="expense_create"),
    path("expenses/<int:pk>/", finance_views.expense_detail, name="expense_detail"),

    # Refunds
    path("refunds/", finance_views.refund_list, name="refund_list"),
    path("refunds/create/", finance_views.refund_create, name="refund_create"),

    # Installment plans
    path("installments/", finance_views.installment_plan_list, name="installment_plan_list"),
    path("installments/create/", finance_views.installment_plan_create, name="installment_plan_create"),
    path("installments/<int:pk>/", finance_views.installment_plan_detail, name="installment_plan_detail"),
    path("installments/<int:pk>/restructure/", finance_views.installment_restructure, name="installment_restructure"),
    path(
        "installments/<int:pk>/pay/",
        finance_views.installment_pay,
        name="installment_pay",
    ),

    # Overdue and late fees
    path("overdue/", finance_views.overdue_list, name="overdue_list"),
    path("late-fees/apply/", finance_views.late_fee_apply, name="late_fee_apply"),
    path("late-fees/waive/", finance_views.late_fee_waive, name="late_fee_waive"),

    # Expense categories
    path("categories/", finance_views.expense_category_list, name="expense_category_list"),
    path("categories/create/", finance_views.expense_category_create, name="expense_category_create"),

    # Student ledger
    path("students/<int:pk>/ledger/", student_views.student_ledger, name="student_ledger"),

    # Reports
    path("reports/", reports_views.AccountantReportsDashboardView.as_view(), name="reports_dashboard"),
    path("reports/pending-dues/csv/", reports_views.PendingDuesExportCSVView.as_view(), name="pending_dues_csv"),
    path("reports/pending-dues/pdf/", reports_views.PendingDuesPDFView.as_view(), name="pending_dues_pdf"),
    path("reports/revenue/", views_reports.report_revenue, name="report_revenue"),
    path("reports/overdue/", views_reports.report_overdue, name="report_overdue"),

    # Notifications
    path("notifications/", notification_views.notification_list, name="notification_list"),
    path("notifications/mark-read/", notification_views.notification_mark_read, name="notification_mark_read"),
]
