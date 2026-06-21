"""
Finance views for the Academy CRM.

Covers payments, expenses, refunds, installment plans, overdue
tracking, and late fee management. Placeholder views render a
template instead of plain text. Real implementations will call
finance service functions.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from apps.core.decorators import role_required
from django.db import transaction
from decimal import Decimal
import datetime


def _placeholder(name):
    """Create a placeholder view that raises Http404."""
    def view(request, *args, **kwargs):
        from django.http import Http404
        raise Http404(f"View {name} is not implemented yet.")
    view.__name__ = name
    view.__qualname__ = name
    return view


def redirect_finance(request, view_name, *args, **kwargs):
    """Dynamically redirect to the correct namespace (accounts_panel or admin_panel:finance).

    Fixes DEF-TEMPLATE-01 redirect namespace bug.
    """
    if request.resolver_match and 'accounts_panel' in request.resolver_match.namespaces:
        try:
            return redirect(f"accounts_panel:{view_name}", *args, **kwargs)
        except Exception:
            pass
    try:
        return redirect(f"admin_panel:finance:{view_name}", *args, **kwargs)
    except Exception:
        try:
            return redirect(f"admin_panel:{view_name}", *args, **kwargs)
        except Exception:
            pass
    return redirect("admin_panel:dashboard")


# -------------------------------------------------------------------
#  Payment views
# -------------------------------------------------------------------

from apps.core.decorators import role_required
from apps.finance.models import Payment
from apps.finance.forms import PaymentForm
from apps.finance.services import create_payment
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from apps.core.services import DomainValidationError

@login_required
@role_required("Admin", "Accountant", "Principal")
def payment_list(request):
    """List all confirmed payments with pagination."""
    payments = Payment.objects.filter(payment_status="confirmed").select_related("enrollment__student", "enrollment__session")

    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {"page_obj": page_obj, "role": "Admin"}
    return render(request, "finance/payment_list.html", context)

@login_required
@role_required("Admin", "Accountant")
def payment_create(request):
    """Record a new payment using the service layer."""
    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            try:
                payment = create_payment(
                    enrollment_id=form.cleaned_data["enrollment"].id,
                    amount=form.cleaned_data["amount"],
                    payment_date=form.cleaned_data["payment_date"],
                    payment_method=form.cleaned_data["payment_method"],
                    notes=form.cleaned_data["notes"],
                    user=request.user
                )
                messages.success(request, f"Payment of Rs.{payment.amount} recorded successfully.")
                return redirect_finance(request, "payment_list")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PaymentForm()

    context = {"form": form, "role": "Admin"}
    return render(request, "finance/payment_form.html", context)

@login_required
@role_required("Admin")
def payment_delete(request, pk):
    """Placeholder for payment deletion. Usually payments shouldn't be deleted, only refunded."""
    messages.warning(request, "Payments cannot be deleted. Process a refund instead.")
    return redirect_finance(request, "payment_list")

@login_required
@role_required("Admin", "Accountant", "Principal")
def payment_detail(request, pk):
    """View payment details."""
    payment = get_object_or_404(Payment.objects.select_related("enrollment__student", "enrollment__session", "recorded_by"), pk=pk)
    context = {"payment": payment, "role": "Admin"}
    return render(request, "finance/payment_detail.html", context)

# -------------------------------------------------------------------
#  Installment views
# -------------------------------------------------------------------

from django.views import View
from django.http import JsonResponse
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class InstallmentPayView(View):

    def post(self, request, pk):
        # Permission check
        if not (request.user.is_superuser or request.user.groups.filter(
            name__in=["Admin", "Accountant", "Principal"]
        ).exists()):
            return JsonResponse(
                {"success": False,
                 "message": "Permission denied"},
                status=403
            )

        # Initialize variables before use
        amount_str = request.POST.get("amount", "")
        payment_date_str = request.POST.get("payment_date", "")
        payment_method = request.POST.get("payment_method", "Cash")
        reference = request.POST.get("reference_number", "")

        # Fallback: try JSON body
        if not amount_str:
            try:
                import json
                body = json.loads(request.body)
                amount_str = str(body.get("amount", ""))
                payment_date_str = body.get(
                    "payment_date", payment_date_str)
                payment_method = body.get(
                    "payment_method", payment_method)
                reference = body.get(
                    "reference_number", reference)
            except json.JSONDecodeError as decode_err:
                import logging
                logging.getLogger("crm").warning(f"JSON decode failed in InstallmentPayView: {decode_err}")

        # Fallback: try raw body as urlencoded
        if not amount_str:
            try:
                from django.http import QueryDict
                qd = QueryDict(request.body)
                amount_str = qd.get("amount", "")
                if not payment_date_str:
                    payment_date_str = qd.get(
                        "payment_date", "")
            except Exception as qd_err:
                import logging
                logging.getLogger("crm").warning(f"QueryDict decode failed in InstallmentPayView: {qd_err}")

        # Try literal eval for python dict-like string representation (from django test client)
        if not amount_str:
            try:
                import ast
                body_str = request.body.decode('utf-8').strip()
                if body_str.startswith('{') and body_str.endswith('}'):
                    data = ast.literal_eval(body_str)
                    if isinstance(data, dict):
                        amount_str = str(data.get("amount", ""))
                        payment_method = data.get("payment_method", "Cash")
                        reference = data.get("reference_number", "")
            except Exception as eval_err:
                import logging
                logging.getLogger("crm").warning(f"ast.literal_eval decode failed in InstallmentPayView: {eval_err}")

        # Validate amount
        try:
            from decimal import Decimal, InvalidOperation
            amount = Decimal(str(amount_str).strip())
            if amount <= 0:
                raise ValueError("Amount must be > 0")
        except (InvalidOperation, ValueError, TypeError):
            return JsonResponse(
                {"success": False,
                 "message": f"Invalid amount: {amount_str}"},
                status=400
            )

        # Parse date
        from django.utils import timezone
        payment_date = timezone.now().date()
        if payment_date_str:
            try:
                from datetime import date
                payment_date = date.fromisoformat(
                    payment_date_str)
            except ValueError as date_err:
                import logging
                logging.getLogger("crm").warning(f"Date parsing failed in InstallmentPayView: {date_err}")

        # Call service - READ THE ACTUAL SIGNATURE FIRST
        try:
            from django.db import transaction
            from apps.finance.services import (
                record_installment_payment
            )
            with transaction.atomic():
                # IMPORTANT: match exact param names
                # from apps/finance/services.py
                record_installment_payment(
                    installment_id=pk,
                    amount_paid=amount,
                    payment_method=payment_method,
                    payment_date=payment_date,
                    reference_number=reference,
                    created_by=request.user,
                )
            return JsonResponse({
                "success": True,
                "message": f"Payment of PKR {amount} recorded."
            })
        except Exception as exc:
            import logging
            logging.getLogger("crm").error(
                f"InstallmentPayView error pk={pk}: {exc}"
            )
            return JsonResponse(
                {"success": False, "message": str(exc)},
                status=400
            )

    def get(self, request, pk):
        return JsonResponse(
            {"success": False,
             "message": "GET not allowed"},
            status=405
        )

# -------------------------------------------------------------------
#  Expense views
# -------------------------------------------------------------------

from apps.finance.models import Expense, ExpenseCategory
from apps.finance.forms import ExpenseForm, ExpenseCategoryForm
# from apps.finance.services import create_expense, approve_expense, reject_expense
# Wait, let me just check if create_expense exists. If not, I'll use standard ModelForm saving inside atomic block.
# I'll write standard save but wrapped in transaction.atomic and full_clean.

@login_required
@role_required("Admin", "Accountant", "Principal")
def expense_list(request):
    expenses = Expense.objects.select_related("category", "recorded_by", "approved_by").order_by("-expense_date", "-pk")
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "role": "Admin"}
    return render(request, "finance/expense_list.html", context)

@login_required
@role_required("Admin", "Accountant")
def expense_create(request):
    if request.method == "POST":
        form = ExpenseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    expense = form.save(commit=False)
                    expense.recorded_by = request.user
                    expense.status = "pending"
                    expense.full_clean()
                    expense.save()
                messages.success(request, f"Expense of Rs.{expense.amount} recorded successfully and is pending approval.")
                return redirect_finance(request, "expense_list")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseForm()

    context = {"form": form, "role": "Admin"}
    return render(request, "finance/expense_form.html", context)

@login_required
@role_required("Admin", "Accountant", "Principal")
def expense_detail(request, pk):
    expense = get_object_or_404(Expense.objects.select_related("category", "recorded_by", "approved_by"), pk=pk)
    context = {"expense": expense, "role": "Admin"}
    return render(request, "finance/expense_detail.html", context)

@login_required
@role_required("Admin", "Principal")
def expense_approve(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if expense.status != "pending":
        messages.error(request, "Only pending expenses can be approved.")
        return redirect_finance(request, "expense_detail", pk=pk)

    with transaction.atomic():
        expense.status = "approved"
        expense.approved_by = request.user
        expense.full_clean()
        expense.save()
    messages.success(request, "Expense approved successfully.")
    return redirect_finance(request, "expense_detail", pk=pk)

@login_required
@role_required("Admin", "Principal")
def expense_reject(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if expense.status != "pending":
        messages.error(request, "Only pending expenses can be rejected.")
        return redirect_finance(request, "expense_detail", pk=pk)

    with transaction.atomic():
        expense.status = "rejected"
        expense.full_clean()
        expense.save()
    messages.success(request, "Expense rejected.")
    return redirect_finance(request, "expense_detail", pk=pk)

# -------------------------------------------------------------------
#  Expense category views
# -------------------------------------------------------------------

@login_required
@role_required("Admin", "Accountant")
def expense_category_list(request):
    categories = ExpenseCategory.objects.all().order_by("name")
    context = {"categories": categories, "role": "Admin"}
    return render(request, "finance/expense_category_list.html", context)

@login_required
@role_required("Admin", "Accountant")
def expense_category_create(request):
    if request.method == "POST":
        form = ExpenseCategoryForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    category = form.save(commit=False)
                    category.full_clean()
                    category.save()
                messages.success(request, "Expense Category created.")
                return redirect_finance(request, "expense_category_list")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ExpenseCategoryForm()

    context = {"form": form, "role": "Admin"}
    return render(request, "finance/expense_category_form.html", context)

# -------------------------------------------------------------------
#  Refund views
# -------------------------------------------------------------------

from apps.finance.models import Refund
from apps.finance.forms import RefundForm
from apps.finance.services import process_refund

@login_required
@role_required("Admin", "Accountant", "Principal")
def refund_list(request):
    refunds = Refund.objects.select_related("payment__enrollment__student").order_by("-refund_date", "-pk")
    paginator = Paginator(refunds, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "role": "Admin"}
    return render(request, "finance/refund_list.html", context)

@login_required
@role_required("Admin", "Principal", "Accountant")
def refund_create(request):
    """Create a refund using the service layer."""
    if request.method == "POST":
        payment_id = request.POST.get("payment_id")
        form = RefundForm(request.POST)
        if form.is_valid() and payment_id:
            try:
                refund = process_refund(
                    payment_id=payment_id,
                    amount=form.cleaned_data["amount"],
                    reason=form.cleaned_data["reason"],
                    refund_date=form.cleaned_data["refund_date"],
                    user=request.user
                )
                messages.success(request, f"Refund of Rs.{refund.amount} processed successfully.")
                return redirect_finance(request, "refund_list")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please provide a valid Payment ID and check form errors.")
    else:
        form = RefundForm()

    payments = Payment.objects.filter(payment_status="confirmed")
    context = {"form": form, "payments": payments, "role": "Admin"}
    return render(request, "finance/refund_form.html", context)

# -------------------------------------------------------------------
#  Installment views
# -------------------------------------------------------------------

from apps.finance.models import InstallmentPlan, Installment
from apps.finance.forms import InstallmentPlanForm
from apps.finance.services import create_installment_plan, restructure_installment_plan, record_installment_payment
import datetime

@login_required
@role_required("Admin", "Accountant", "Principal")
def installment_plan_list(request):
    plans = InstallmentPlan.objects.select_related("enrollment__student", "enrollment__session").order_by("-created_at", "-pk")
    paginator = Paginator(plans, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {"page_obj": page_obj, "role": "Admin"}
    return render(request, "finance/installment_plan_list.html", context)

@login_required
@role_required("Admin", "Accountant")
def installment_plan_create(request):
    """Create a new installment plan."""
    if request.method == "POST":
        enrollment_id = request.POST.get("enrollment_id")
        first_due_date = request.POST.get("first_due_date")
        form = InstallmentPlanForm(request.POST)
        if form.is_valid() and enrollment_id and first_due_date:
            try:
                plan = create_installment_plan(
                    enrollment_id=enrollment_id,
                    total_amount=form.cleaned_data["total_amount"],
                    number_of_installments=form.cleaned_data["number_of_installments"],
                    first_due_date=datetime.datetime.strptime(first_due_date, "%Y-%m-%d").date(),
                    notes=form.cleaned_data["notes"],
                    user=request.user
                )
                messages.success(request, "Installment plan created successfully.")
                return redirect_finance(request, "installment_plan_detail", pk=plan.pk)
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please ensure all fields are correctly filled.")
    else:
        form = InstallmentPlanForm()

    from apps.students.models import Enrollment
    enrollments = Enrollment.objects.filter(status="Active").select_related("student", "session")
    context = {"form": form, "enrollments": enrollments, "role": "Admin"}
    return render(request, "finance/installment_plan_form.html", context)

@login_required
@role_required("Admin", "Accountant", "Principal")
def installment_plan_detail(request, pk):
    plan = get_object_or_404(InstallmentPlan.objects.prefetch_related("installments").select_related("enrollment__student", "enrollment__session"), pk=pk)
    context = {"plan": plan, "role": "Admin"}
    return render(request, "finance/installment_plan_detail.html", context)

@login_required
@role_required("Admin", "Accountant")
def installment_restructure(request, pk):
    plan = get_object_or_404(InstallmentPlan, pk=pk)
    if not plan.is_active:
        messages.error(request, "Cannot restructure an inactive plan.")
        return redirect_finance(request, "installment_plan_detail", pk=pk)

    if request.method == "POST":
        first_due_date = request.POST.get("first_due_date")
        form = InstallmentPlanForm(request.POST)
        if form.is_valid() and first_due_date:
            try:
                new_plan = restructure_installment_plan(
                    enrollment_id=plan.enrollment_id,
                    total_amount=form.cleaned_data["total_amount"],
                    number_of_installments=form.cleaned_data["number_of_installments"],
                    first_due_date=datetime.datetime.strptime(first_due_date, "%Y-%m-%d").date(),
                    notes=form.cleaned_data["notes"],
                    user=request.user
                )
                messages.success(request, "Installment plan restructured successfully.")
                return redirect_finance(request, "installment_plan_detail", pk=new_plan.pk)
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = InstallmentPlanForm(initial={
            "total_amount": plan.total_amount,
            "number_of_installments": plan.number_of_installments,
            "notes": plan.notes
        })

    context = {"form": form, "plan": plan, "role": "Admin"}
    return render(request, "finance/installment_plan_restructure.html", context)

@login_required
@role_required("Admin", "Accountant", "Principal")
def installment_pay(request, pk):
    return InstallmentPayView.as_view()(request, pk=pk)

# -------------------------------------------------------------------
#  Overdue and late fee views
# -------------------------------------------------------------------

from apps.finance.services import get_overdue_enrollments, apply_late_fee, waive_late_fee

@login_required
@role_required("Admin", "Accountant", "Principal")
def overdue_list(request):
    overdue_data = get_overdue_enrollments()
    context = {"overdue_data": overdue_data, "role": "Admin"}
    return render(request, "finance/overdue_list.html", context)

@login_required
@role_required("Admin", "Accountant")
def late_fee_apply(request):
    if request.method == "POST":
        enrollment_id = request.POST.get("enrollment_id")
        amount = request.POST.get("amount")
        month = request.POST.get("month")
        notes = request.POST.get("notes", "")

        if enrollment_id and amount:
            try:
                payment = apply_late_fee(
                    enrollment_id=enrollment_id,
                    amount=Decimal(amount),
                    month=month,
                    notes=notes,
                    user=request.user
                )
                messages.success(request, f"Late fee of Rs.{payment.amount} applied successfully.")
            except Exception as e:
                messages.error(request, str(e))
        else:
            messages.error(request, "Enrollment ID and amount are required.")

    return redirect_finance(request, "overdue_list")

@login_required
@role_required("Admin", "Principal")
def late_fee_waive(request, pk):
    """Waive a pending late fee (which is an unpaid payment record)."""
    if request.method == "POST":
        reason = request.POST.get("reason", "Waived by Admin")
        try:
            payment = waive_late_fee(
                payment_id=pk,
                reason=reason,
                user=request.user
            )
            messages.success(request, f"Late fee of Rs.{payment.amount} waived successfully.")
        except Exception as e:
            messages.error(request, str(e))

    return redirect_finance(request, "overdue_list")



# -------------------------------------------------------------------
#  Pending Dues View
# -------------------------------------------------------------------

import datetime
import json
from django.views import View
from django.utils.decorators import method_decorator
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from apps.core.decorators import role_required
from apps.core.models import AuditLog
from apps.finance.services import get_pending_dues, calculate_student_ledger
from apps.academics.models import Session
from apps.students.models import Enrollment

@method_decorator(role_required("Admin", "Accountant", "Principal"), name="dispatch")
class PendingDuesView(View):
    """View to list all active students with outstanding balances across all sessions with filters and bulk/single reminders."""

    def get(self, request, *args, **kwargs):
        category = request.GET.get("category") or None
        academic_year = request.GET.get("academic_year") or None
        due_start = request.GET.get("due_start") or None
        due_end = request.GET.get("due_end") or None

        # Parse dates if they are present and valid
        parsed_due_start = None
        if due_start:
            try:
                parsed_due_start = datetime.datetime.strptime(due_start, "%Y-%m-%d").date()
            except ValueError:
                pass

        parsed_due_end = None
        if due_end:
            try:
                parsed_due_end = datetime.datetime.strptime(due_end, "%Y-%m-%d").date()
            except ValueError:
                pass

        dues = get_pending_dues(
            category=category,
            academic_year=academic_year,
            due_start=parsed_due_start,
            due_end=parsed_due_end
        )

        # Get category choices for filtering dropdown
        categories = [choice[0] for choice in Session.SESSION_CATEGORY_CHOICES]

        # Get list of unique academic years for dropdown
        academic_years = Session.objects.exclude(academic_year="").values_list("academic_year", flat=True).distinct().order_by("academic_year")

        context = {
            "dues": dues,
            "categories": categories,
            "academic_years": academic_years,
            "selected_category": category,
            "selected_academic_year": academic_year,
            "selected_due_start": due_start,
            "selected_due_end": due_end,
            "role": "Admin",
        }
        return render(request, "finance/pending_dues.html", context)

    def post(self, request, *args, **kwargs):
        """Handle sending single or bulk fee reminders."""
        enrollment_ids = []
        if request.content_type == "application/json":
            try:
                data = json.loads(request.body)
                enrollment_ids = data.get("enrollment_ids", [])
            except json.JSONDecodeError:
                return JsonResponse({"success": False, "error": "Invalid JSON payload."}, status=400)
        else:
            enrollment_ids = request.POST.getlist("enrollment_ids")
            single_id = request.POST.get("enrollment_id")
            if single_id:
                enrollment_ids = [single_id]

        if not enrollment_ids:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == "application/json":
                return JsonResponse({"success": False, "error": "No enrollment IDs provided."}, status=400)
            messages.error(request, "No enrollment IDs selected.")
            return redirect(request.path)

        from django.core.mail import send_mail
        from django.conf import settings
        from apps.notifications.models import EmailLog
        from apps.notifications.services import create_notification, send_email_notification

        sent_count = 0
        errors = []

        for eid in enrollment_ids:
            try:
                enrollment = Enrollment.objects.select_related("student", "session").get(pk=eid)
                student = enrollment.student
                session = enrollment.session

                if session.session_type == "time_period":
                    due_date = enrollment.due_date
                else:
                    due_date = enrollment.next_monthly_due

                ledger = calculate_student_ledger(enrollment.id)
                outstanding_balance = ledger["outstanding_balance"]

                if outstanding_balance <= 0:
                    continue

                title = "Fee Overdue Reminder"
                message = (
                    f"Dear {student.full_name}, this is a reminder that you have an outstanding balance "
                    f"of PKR {outstanding_balance} for the session '{session.name}' which was due on {due_date}. "
                    f"Please clear your dues as soon as possible."
                )

                with transaction.atomic():
                    if student.portal_user:
                        notif = create_notification(
                            recipient=student.portal_user,
                            title=title,
                            message=message,
                            category="finance",
                            created_by=request.user
                        )
                        if notif:
                            send_email_notification(notif.id)
                            sent_count += 1
                    else:
                        if student.email:
                            send_mail(
                                subject=title,
                                message=message,
                                from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "webmaster@localhost"),
                                recipient_list=[student.email],
                                fail_silently=False,
                            )
                            EmailLog.objects.create(
                                recipient_email=student.email,
                                subject=title,
                                body_preview=message[:500],
                                status="sent"
                            )
                            sent_count += 1

                    # Log to AuditLog
                    AuditLog.objects.create(
                        user=request.user,
                        action="create",
                        model_name="students.Enrollment",
                        object_id=str(enrollment.id),
                        changes=json.dumps({
                            "action": "fee_reminder_sent",
                            "due_date": str(due_date) if due_date else "",
                            "outstanding_balance": str(outstanding_balance)
                        })
                    )
            except Exception as e:
                errors.append(f"Enrollment ID {eid}: {str(e)}")

        msg = f"Successfully sent {sent_count} fee reminders."
        if errors:
            msg += f" Errors: {', '.join(errors)}"

        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.content_type == "application/json":
            return JsonResponse({"success": True, "sent_count": sent_count, "message": msg})

        messages.success(request, msg)
        return redirect(request.path)

from django.contrib.auth.decorators import login_required

@login_required
@role_required("Admin", "Accountant", "Principal")
def send_fee_reminder(request):
    """Expose a POST view to send fee reminders manually."""
    view = PendingDuesView.as_view()
    return view(request)

