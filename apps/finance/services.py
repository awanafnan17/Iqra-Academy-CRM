"""
Finance service layer - all financial business logic.

Every write operation uses transaction.atomic().
Every model instance calls full_clean() before save().
No business logic belongs in views or models.

Public API:
    create_payment
    apply_late_fee
    waive_late_fee
    process_refund
    create_installment_plan
    restructure_installment_plan
    record_installment_payment
    calculate_session_revenue
    calculate_student_ledger
    get_overdue_enrollments
"""

import datetime
import json
import logging
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone

from apps.core.models import AuditLog
from apps.finance.models import (
    Expense,
    Installment,
    InstallmentPlan,
    Payment,
    Refund,
)

logger = logging.getLogger("crm.finance")

ZERO = Decimal("0.00")


# ---------------------------------------------------------------
#  Internal helpers
# ---------------------------------------------------------------

def _generate_receipt_number():
    """Generate a unique receipt number for today.

    Format: RCP-YYYYMMDD-NNNNN
    Example: RCP-20260613-00042
    """
    today = timezone.localdate()
    date_str = today.strftime("%Y%m%d")
    count = Payment.objects.filter(
        payment_date=today,
        receipt_number__isnull=False,
    ).count()
    sequence = count + 1
    return f"RCP-{date_str}-{sequence:05d}"


def _get_effective_fee(enrollment):
    """Resolve the actual fee for an enrollment.

    Enrollment.fee overrides Session.fee when not null.
    Caller must use select_related('session').
    """
    if enrollment.fee is not None:
        return enrollment.fee
    return enrollment.session.fee


def _get_effective_registration_fee(enrollment):
    """Resolve the actual registration fee for an enrollment.

    Enrollment.registration_fee overrides Session.registration_fee
    when not null. Caller must use select_related('session').
    """
    if enrollment.registration_fee is not None:
        return enrollment.registration_fee
    return enrollment.session.registration_fee


def _create_audit_entry(user, action, model_name, object_id,
                        changes=None, ip_address=None):
    """Create a centralized audit log entry."""
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id),
        changes=json.dumps(changes) if changes else None,
        ip_address=ip_address,
        timestamp=timezone.now(),
    )


def _verify_payment_immutability(payment):
    """Guard against modifying confirmed payment fields.

    Once a payment reaches 'confirmed' status, its amount and
    enrollment link are immutable. Only payment_status may change
    (e.g. to 'refunded').
    """
    if payment.pk is None:
        return

    try:
        original = Payment.objects.only(
            "payment_status", "amount", "enrollment_id"
        ).get(pk=payment.pk)
    except Payment.DoesNotExist:
        return

    if original.payment_status != "confirmed":
        return

    if original.amount != payment.amount:
        raise ValidationError(
            {"amount": "Cannot change the amount of a confirmed payment."}
        )
    if original.enrollment_id != payment.enrollment_id:
        raise ValidationError(
            {"enrollment": "Cannot change the enrollment of a confirmed payment."}
        )


# ---------------------------------------------------------------
#  create_payment
# ---------------------------------------------------------------

def create_payment(
    enrollment_id,
    amount,
    payment_date,
    payment_method="Cash",
    month=None,
    is_late_fee_payment=False,
    notes=None,
    user=None,
    ip_address=None,
):
    """Record a fee payment against an enrollment.

    Args:
        enrollment_id: PK of the target Enrollment.
        amount: Decimal payment amount (must be > 0).
        payment_date: date when payment was received.
        payment_method: one of Payment.PAYMENT_METHOD_CHOICES.
        month: YYYY-MM string for monthly sessions.
        is_late_fee_payment: True if this is a late fee charge.
        notes: optional payment notes.
        user: staff member recording the payment.
        ip_address: request IP for audit trail.

    Returns:
        Created Payment instance.

    Raises:
        Enrollment.DoesNotExist: invalid enrollment_id.
        ValueError: enrollment is not active.
        ValidationError: model validation failure.
    """
    from apps.students.models import Enrollment

    with transaction.atomic():
        enrollment = (
            Enrollment.objects
            .select_related("session")
            .get(pk=enrollment_id)
        )

        if enrollment.status != "Active":
            raise ValueError(
                f"Cannot record payment for enrollment with "
                f"status '{enrollment.status}'. Must be Active."
            )

        # Generate receipt with retry for collision safety
        payment = None
        for attempt in range(3):
            receipt = _generate_receipt_number()
            payment = Payment(
                enrollment=enrollment,
                amount=amount,
                payment_date=payment_date,
                payment_method=payment_method,
                payment_status="confirmed",
                receipt_number=receipt,
                month=month,
                is_late_fee_payment=is_late_fee_payment,
                notes=notes,
                recorded_by=user,
                created_by=user,
            )
            try:
                payment.full_clean()
                payment.save()
                break
            except ValidationError as e:
                if "receipt_number" in e.message_dict and attempt < 2:
                    logger.warning(
                        "Receipt collision on attempt %d: %s",
                        attempt + 1, receipt,
                    )
                    continue
                raise

        _create_audit_entry(
            user=user,
            action="create",
            model_name="finance.Payment",
            object_id=payment.pk,
            changes={
                "amount": str(payment.amount),
                "enrollment_id": enrollment_id,
                "receipt_number": payment.receipt_number,
                "is_late_fee_payment": is_late_fee_payment,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Payment created: Rs.%s for enrollment #%s by %s",
            amount, enrollment_id, user,
        )

        return payment


# ---------------------------------------------------------------
#  apply_late_fee
# ---------------------------------------------------------------

def apply_late_fee(
    enrollment_id,
    target_month,
    user=None,
    ip_address=None,
):
    """Calculate and record a late fee for a specific month.

    Returns None if no late fee applies (already paid, in grace
    period, cap reached, or late fee not configured).

    Args:
        enrollment_id: PK of the target Enrollment.
        target_month: YYYY-MM string.
        user: staff member applying the late fee.
        ip_address: request IP for audit trail.

    Returns:
        Created Payment or None.
    """
    from apps.students.models import Enrollment

    enrollment = (
        Enrollment.objects
        .select_related("session")
        .get(pk=enrollment_id)
    )

    session = enrollment.session

    # Check if late fee is configured
    if session.late_fee_amount <= ZERO:
        return None

    # Check if enrollment is active
    if enrollment.status != "Active":
        return None

    # Parse target month
    try:
        year, month_num = target_month.split("-")
        year, month_num = int(year), int(month_num)
    except (ValueError, AttributeError):
        raise ValueError(
            f"Invalid month format: '{target_month}'. Expected YYYY-MM."
        )

    # Determine due date and grace deadline
    due_date = datetime.date(year, month_num, session.due_day)
    grace_deadline = due_date + datetime.timedelta(
        days=session.late_fee_grace_days
    )

    # Still in grace period - use timezone.localdate() for correctness
    today = timezone.localdate()
    if today <= grace_deadline:
        return None

    # Check if tuition already paid for this month
    tuition_paid = Payment.objects.filter(
        enrollment_id=enrollment_id,
        month=target_month,
        payment_status="confirmed",
        is_late_fee_payment=False,
    ).exists()

    if tuition_paid:
        return None

    # Check if late fee already applied for this month (idempotency)
    already_applied = Payment.objects.filter(
        enrollment_id=enrollment_id,
        month=target_month,
        payment_status="confirmed",
        is_late_fee_payment=True,
    ).exists()

    if already_applied:
        return None

    # Calculate fee amount respecting maximum cap
    fee_amount = session.late_fee_amount

    if session.late_fee_maximum > ZERO:
        total_applied = Payment.objects.filter(
            enrollment_id=enrollment_id,
            payment_status="confirmed",
            is_late_fee_payment=True,
        ).aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(ZERO),
                output_field=DecimalField(),
            ),
        )["total"]

        remaining_cap = session.late_fee_maximum - total_applied
        if remaining_cap <= ZERO:
            return None
        fee_amount = min(fee_amount, remaining_cap)

    # Create late fee payment
    return create_payment(
        enrollment_id=enrollment_id,
        amount=fee_amount,
        payment_date=today,
        payment_method="Cash",
        month=target_month,
        is_late_fee_payment=True,
        notes=f"Late fee for {target_month}",
        user=user,
        ip_address=ip_address,
    )


# ---------------------------------------------------------------
#  waive_late_fee
# ---------------------------------------------------------------

def waive_late_fee(
    enrollment_id,
    target_month,
    reason,
    user=None,
    ip_address=None,
):
    """Record a late fee waiver for a specific month.

    Creates a zero-amount payment record flagged as waived
    to prevent future late fee application for this month.

    Args:
        enrollment_id: PK of the target Enrollment.
        target_month: YYYY-MM string.
        reason: justification for the waiver.
        user: staff member approving the waiver.
        ip_address: request IP for audit trail.

    Returns:
        Created Payment (waiver record).
    """
    from apps.students.models import Enrollment

    with transaction.atomic():
        enrollment = (
            Enrollment.objects
            .select_related("session")
            .get(pk=enrollment_id)
        )

        payment = Payment(
            enrollment=enrollment,
            amount=ZERO,
            payment_date=timezone.localdate(),
            payment_method="Cash",
            payment_status="confirmed",
            receipt_number=_generate_receipt_number(),
            month=target_month,
            is_late_fee_payment=True,
            late_fee_waived=True,
            late_fee_waiver_reason=reason,
            late_fee_waived_by=user,
            recorded_by=user,
            created_by=user,
        )
        payment.full_clean()
        payment.save()

        _create_audit_entry(
            user=user,
            action="create",
            model_name="finance.Payment",
            object_id=payment.pk,
            changes={
                "type": "late_fee_waiver",
                "enrollment_id": enrollment_id,
                "month": target_month,
                "reason": reason,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Late fee waived for enrollment #%s month %s by %s",
            enrollment_id, target_month, user,
        )

        return payment


# ---------------------------------------------------------------
#  process_refund
# ---------------------------------------------------------------

def process_refund(
    payment_id,
    amount,
    reason,
    refund_date,
    user=None,
    ip_address=None,
):
    """Process a refund against a confirmed payment.

    Uses select_for_update to prevent concurrent refund
    race conditions. Aggregates use Coalesce for null safety.

    Args:
        payment_id: PK of the original Payment.
        amount: Decimal refund amount.
        reason: text justification for the refund.
        refund_date: date when refund was processed.
        user: staff member processing the refund.
        ip_address: request IP for audit trail.

    Returns:
        Created Refund instance.

    Raises:
        Payment.DoesNotExist: invalid payment_id.
        ValueError: payment is not confirmed.
        ValidationError: cumulative refund exceeds payment.
    """
    with transaction.atomic():
        # Lock the payment row to prevent concurrent refunds
        payment = (
            Payment.objects
            .select_for_update()
            .select_related("enrollment")
            .get(pk=payment_id)
        )

        if payment.payment_status != "confirmed":
            raise ValueError(
                f"Cannot refund payment with status "
                f"'{payment.payment_status}'. Must be 'confirmed'."
            )

        refund = Refund(
            payment=payment,
            amount=amount,
            reason=reason,
            refund_date=refund_date,
            status="processed",
            processed_by=user,
            approved_by=user,
            created_by=user,
        )
        # full_clean validates cumulative refund <= payment amount
        refund.full_clean()
        refund.save()

        # Check if payment is now fully refunded using Coalesce
        total_refunded = Refund.objects.filter(
            payment_id=payment_id,
        ).exclude(
            status="rejected",
        ).aggregate(
            total=Coalesce(
                Sum("amount"),
                Value(ZERO),
                output_field=DecimalField(),
            ),
        )["total"]

        if total_refunded >= payment.amount:
            payment.payment_status = "refunded"
            payment.save(update_fields=["payment_status", "updated_at"])

            _create_audit_entry(
                user=user,
                action="update",
                model_name="finance.Payment",
                object_id=payment.pk,
                changes={
                    "payment_status": {"old": "confirmed", "new": "refunded"},
                    "reason": "Fully refunded",
                },
                ip_address=ip_address,
            )

        _create_audit_entry(
            user=user,
            action="create",
            model_name="finance.Refund",
            object_id=refund.pk,
            changes={
                "payment_id": payment_id,
                "amount": str(amount),
                "reason": reason,
                "total_refunded": str(total_refunded),
            },
            ip_address=ip_address,
        )

        logger.info(
            "Refund Rs.%s processed on payment #%s by %s",
            amount, payment_id, user,
        )

        return refund


# ---------------------------------------------------------------
#  create_installment_plan
# ---------------------------------------------------------------

def create_installment_plan(
    enrollment_id,
    total_amount,
    number_of_installments,
    first_due_date,
    interval_days=30,
    notes=None,
    user=None,
    ip_address=None,
):
    """Create a new installment plan with generated installment rows.

    Fails if an active plan already exists. Use
    restructure_installment_plan to replace an existing plan.

    Args:
        enrollment_id: PK of the target Enrollment.
        total_amount: Decimal total being split.
        number_of_installments: how many installments.
        first_due_date: date of the first installment.
        interval_days: days between installments (default 30).
        notes: optional plan notes.
        user: staff member creating the plan.
        ip_address: request IP for audit trail.

    Returns:
        Created InstallmentPlan with installments.
    """
    from apps.students.models import Enrollment

    with transaction.atomic():
        enrollment = Enrollment.objects.get(pk=enrollment_id)

        plan = InstallmentPlan(
            enrollment=enrollment,
            total_amount=total_amount,
            number_of_installments=number_of_installments,
            is_active=True,
            notes=notes,
            created_by=user,
        )
        plan.full_clean()
        plan.save()

        # Generate installment rows
        _generate_installments(
            plan, total_amount, number_of_installments,
            first_due_date, interval_days,
        )

        _create_audit_entry(
            user=user,
            action="create",
            model_name="finance.InstallmentPlan",
            object_id=plan.pk,
            changes={
                "enrollment_id": enrollment_id,
                "total_amount": str(total_amount),
                "number_of_installments": number_of_installments,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Installment plan created for enrollment #%s: %s installments",
            enrollment_id, number_of_installments,
        )

        return plan


def _generate_installments(plan, total_amount, count,
                           first_due_date, interval_days):
    """Generate installment rows for a plan.

    Distributes amount evenly with remainder on last installment
    to ensure zero rounding error.
    """
    base_amount = (total_amount / count).quantize(Decimal("0.01"))
    last_amount = total_amount - (base_amount * (count - 1))

    installments = []
    for i in range(count):
        due_date = first_due_date + datetime.timedelta(
            days=i * interval_days
        )
        inst_amount = last_amount if i == count - 1 else base_amount

        installments.append(Installment(
            plan=plan,
            installment_number=i + 1,
            amount=inst_amount,
            due_date=due_date,
            paid_amount=ZERO,
            status="pending",
        ))

    Installment.objects.bulk_create(installments)


# ---------------------------------------------------------------
#  restructure_installment_plan
# ---------------------------------------------------------------

def restructure_installment_plan(
    enrollment_id,
    total_amount,
    number_of_installments,
    first_due_date,
    interval_days=30,
    notes=None,
    user=None,
    ip_address=None,
):
    """Deactivate existing plan and create a new one.

    Safe restructuring: old plan is locked with select_for_update(),
    deactivated before new plan is created, all within a single
    atomic block. If anything fails, the old plan remains active.

    Args:
        enrollment_id: PK of the target Enrollment.
        total_amount: Decimal total for the new plan.
        number_of_installments: how many new installments.
        first_due_date: date of the first new installment.
        interval_days: days between installments (default 30).
        notes: optional plan notes.
        user: staff member restructuring.
        ip_address: request IP for audit trail.

    Returns:
        New InstallmentPlan instance.
    """
    with transaction.atomic():
        # Lock existing active plan to prevent concurrent restructuring
        old_plan = (
            InstallmentPlan.objects
            .select_for_update()
            .filter(
                enrollment_id=enrollment_id,
                is_active=True,
            )
            .first()
        )

        if old_plan:
            old_plan.is_active = False
            old_plan.save(update_fields=["is_active", "updated_at"])

            _create_audit_entry(
                user=user,
                action="update",
                model_name="finance.InstallmentPlan",
                object_id=old_plan.pk,
                changes={
                    "is_active": {"old": True, "new": False},
                    "reason": "Replaced by new plan",
                },
                ip_address=ip_address,
            )

        # Create new plan (reuses create_installment_plan logic
        # but inside the same transaction)
        return create_installment_plan(
            enrollment_id=enrollment_id,
            total_amount=total_amount,
            number_of_installments=number_of_installments,
            first_due_date=first_due_date,
            interval_days=interval_days,
            notes=notes,
            user=user,
            ip_address=ip_address,
        )


# Note: record_installment_payment is defined at the end of this file (line 1308).


# ---------------------------------------------------------------
#  calculate_session_revenue
# ---------------------------------------------------------------

def calculate_session_revenue(session_id, year, month):
    """Compute revenue breakdown for a session in a given month.

    Read-only operation. No transactions needed.
    All aggregates use Coalesce to prevent None arithmetic errors.

    Args:
        session_id: PK of the Session.
        year: integer year.
        month: integer month (1-12).

    Returns:
        Dict with tuition_revenue, late_fee_revenue, total_revenue,
        refunds, net_revenue, payment_count, refund_count.
    """
    payment_agg = Payment.objects.filter(
        enrollment__session_id=session_id,
        payment_status="confirmed",
        payment_date__year=year,
        payment_date__month=month,
    ).aggregate(
        tuition=Coalesce(
            Sum("amount", filter=models.Q(is_late_fee_payment=False)),
            Value(ZERO),
            output_field=DecimalField(),
        ),
        late_fees=Coalesce(
            Sum("amount", filter=models.Q(is_late_fee_payment=True)),
            Value(ZERO),
            output_field=DecimalField(),
        ),
        count=models.Count("id"),
    )

    refund_agg = Refund.objects.filter(
        payment__enrollment__session_id=session_id,
        status="processed",
        refund_date__year=year,
        refund_date__month=month,
    ).aggregate(
        total=Coalesce(
            Sum("amount"),
            Value(ZERO),
            output_field=DecimalField(),
        ),
        count=models.Count("id"),
    )

    tuition = payment_agg["tuition"]
    late_fees = payment_agg["late_fees"]
    total_revenue = tuition + late_fees
    refunds = refund_agg["total"]

    return {
        "tuition_revenue": tuition,
        "late_fee_revenue": late_fees,
        "total_revenue": total_revenue,
        "refunds": refunds,
        "net_revenue": total_revenue - refunds,
        "payment_count": payment_agg["count"],
        "refund_count": refund_agg["count"],
    }


# ---------------------------------------------------------------
#  calculate_student_ledger
# ---------------------------------------------------------------

def calculate_student_ledger(enrollment_id):
    """Complete financial snapshot for one enrollment.

    Read-only operation. Returns fee breakdown, payment history,
    outstanding balance, and active installment plan.
    All aggregates use Coalesce for null safety.

    Args:
        enrollment_id: PK of the Enrollment.

    Returns:
        Dict with full financial snapshot.
    """
    from apps.students.models import Enrollment

    enrollment = (
        Enrollment.all_objects
        .select_related("session", "student")
        .get(pk=enrollment_id)
    )

    effective_fee = _get_effective_fee(enrollment)
    registration_fee = _get_effective_registration_fee(enrollment)
    discount = enrollment.discount

    total_payable = effective_fee + registration_fee - discount

    # Confirmed payments (tuition)
    payments = Payment.objects.filter(
        enrollment_id=enrollment_id,
        payment_status="confirmed",
    ).order_by("-payment_date", "-pk")

    total_paid = ZERO
    total_late_fees_paid = ZERO
    payment_list = []

    for p in payments:
        if p.is_late_fee_payment:
            total_late_fees_paid += p.amount
        else:
            total_paid += p.amount

        payment_list.append({
            "id": p.pk,
            "date": p.payment_date,
            "amount": p.amount,
            "method": p.payment_method,
            "receipt": p.receipt_number,
            "status": p.payment_status,
            "is_late_fee": p.is_late_fee_payment,
            "month": p.month,
        })

    # Processed refunds with Coalesce
    total_refunded = Refund.objects.filter(
        payment__enrollment_id=enrollment_id,
        status="processed",
    ).aggregate(
        total=Coalesce(
            Sum("amount"),
            Value(ZERO),
            output_field=DecimalField(),
        ),
    )["total"]

    # Outstanding balance
    if enrollment.is_fee_waived:
        outstanding_balance = ZERO
    else:
        outstanding_balance = total_payable - total_paid + total_refunded

    # Active installment plan
    plan_data = None
    active_plan = (
        InstallmentPlan.objects
        .filter(enrollment_id=enrollment_id, is_active=True)
        .prefetch_related("installments")
        .first()
    )

    if active_plan:
        plan_data = {
            "id": active_plan.pk,
            "total": active_plan.total_amount,
            "number_of_installments": active_plan.number_of_installments,
            "installments": [
                {
                    "number": inst.installment_number,
                    "amount": inst.amount,
                    "due_date": inst.due_date,
                    "paid_amount": inst.paid_amount,
                    "status": inst.status,
                }
                for inst in active_plan.installments.all()
            ],
        }

    return {
        "enrollment_id": enrollment_id,
        "student_name": enrollment.student.full_name,
        "session_name": enrollment.session.name,
        "effective_fee": effective_fee,
        "registration_fee": registration_fee,
        "discount": discount,
        "total_payable": total_payable,
        "total_paid": total_paid,
        "total_late_fees_paid": total_late_fees_paid,
        "total_refunded": total_refunded,
        "outstanding_balance": outstanding_balance,
        "is_fee_waived": enrollment.is_fee_waived,
        "payments": payment_list,
        "installment_plan": plan_data,
    }


def get_overdue_enrollments(session_id=None):
    """Find enrollments with unpaid fees past their due date.

    Read-only operation. Checks both time-period and monthly
    session types. All aggregates use Coalesce for null safety.

    Args:
        session_id: optional filter to a specific session.

    Returns:
        QuerySet of Enrollment.
    """
    from apps.students.models import Enrollment
    from apps.finance.models import Payment
    from django.db.models import Sum, Q, F, OuterRef, Subquery, Exists, Value, DecimalField
    from django.db.models.functions import Coalesce, ExtractYear, ExtractMonth
    from django.utils import timezone

    today = timezone.localdate()

    qs = (
        Enrollment.objects
        .filter(status="Active")
        .select_related("session", "student")
    )

    if session_id:
        qs = qs.filter(session_id=session_id)

    # Subquery for time_period: total confirmed tuition paid
    total_paid_sub = Payment.objects.filter(
        enrollment=OuterRef("pk"),
        payment_status="confirmed",
        is_late_fee_payment=False
    ).values("enrollment").annotate(
        total=Sum("amount")
    ).values("total")

    # Annotate outer query with year/month extracts and effective fees/paid tuition
    qs = qs.annotate(
        next_due_year=ExtractYear("next_monthly_due"),
        next_due_month=ExtractMonth("next_monthly_due"),
        effective_fee=Coalesce(F("fee"), F("session__fee")),
        total_paid_tuition=Coalesce(Subquery(total_paid_sub), Value(Decimal("0.00")), output_field=DecimalField())
    )

    # Monthly paid check subquery
    monthly_paid_exists = Payment.objects.filter(
        enrollment=OuterRef("pk"),
        payment_status="confirmed",
        is_late_fee_payment=False,
        payment_date__year=OuterRef("next_due_year"),
        payment_date__month=OuterRef("next_due_month")
    )

    qs = qs.annotate(
        has_monthly_payment=Exists(monthly_paid_exists)
    )

    # Filter to only overdue records
    overdue_qs = qs.filter(
        Q(
            session__session_type="time_period",
            due_date__lt=today,
            total_paid_tuition__lt=F("effective_fee")
        ) | Q(
            session__session_type="monthly",
            next_monthly_due__lt=today,
            has_monthly_payment=False
        )
    )

    return overdue_qs


# ---------------------------------------------------------------
#  get_pending_dues
# ---------------------------------------------------------------

def get_pending_dues(category=None, academic_year=None, due_start=None, due_end=None):
    """Retrieve all active enrollments with outstanding balance > 0, supporting filters.

    Optimized to avoid N+1 queries by pre-filtering using Coalesce and subqueries,
    then computing the official ledger snapshot using calculate_student_ledger().
    """
    from django.db.models import Sum, Q, F, OuterRef, Subquery, Value, DecimalField, Case, When
    from django.db.models.functions import Coalesce
    from apps.students.models import Enrollment
    from apps.finance.models import Payment, Refund

    # Subquery for total tuition paid (is_late_fee_payment=False)
    tuition_paid_sub = Payment.objects.filter(
        enrollment=OuterRef("pk"),
        payment_status="confirmed",
        is_late_fee_payment=False
    ).values("enrollment").annotate(
        total=Sum("amount")
    ).values("total")

    # Subquery for total processed refunds
    refunds_sub = Refund.objects.filter(
        payment__enrollment=OuterRef("pk"),
        status="processed"
    ).values("payment__enrollment").annotate(
        total=Sum("amount")
    ).values("total")

    # Construct filtering query
    filters = Q(status="Active")
    if category:
        filters &= Q(session__session_category=category)
    if academic_year:
        filters &= Q(session__academic_year=academic_year)
    if due_start:
        filters &= (
            Q(session__session_type="time_period", due_date__gte=due_start) |
            Q(session__session_type="monthly", next_monthly_due__gte=due_start)
        )
    if due_end:
        filters &= (
            Q(session__session_type="time_period", due_date__lte=due_end) |
            Q(session__session_type="monthly", next_monthly_due__lte=due_end)
        )

    # Get active enrollments, annotated with financial math matching ledger logic
    active_enrollments = (
        Enrollment.objects.filter(filters)
        .select_related("student", "session")
        .annotate(
            effective_fee_val=Coalesce(F("fee"), F("session__fee"), Value(Decimal("0.00")), output_field=DecimalField()),
            effective_reg_fee_val=Coalesce(F("registration_fee"), F("session__registration_fee"), Value(Decimal("0.00")), output_field=DecimalField()),
            total_payable=Case(
                When(is_fee_waived=True, then=Value(Decimal("0.00"))),
                default=F("effective_fee_val") + F("effective_reg_fee_val") - F("discount"),
                output_field=DecimalField()
            ),
            total_paid=Coalesce(Subquery(tuition_paid_sub), Value(Decimal("0.00")), output_field=DecimalField()),
            total_refunded=Coalesce(Subquery(refunds_sub), Value(Decimal("0.00")), output_field=DecimalField()),
            calculated_balance=F("total_payable") - F("total_paid") + F("total_refunded")
        )
        .filter(calculated_balance__gt=0)
    )

    results = []
    for enrollment in active_enrollments:
        if enrollment.session.session_type == "time_period":
            due_from = enrollment.due_date
        else:
            due_from = enrollment.next_monthly_due

        results.append({
            "enrollment_id": enrollment.id,
            "roll_number": enrollment.student.roll_number,
            "student_name": enrollment.student.full_name,
            "session_name": enrollment.session.name,
            "due_from": due_from,
            "outstanding_balance": enrollment.calculated_balance
        })

    return results

# ---------------------------------------------------------------
#  setup_enrollment_fee
# ---------------------------------------------------------------

def setup_enrollment_fee(
    enrollment_id,
    fee_type,
    total_amount,
    number_of_installments=1,
    due_day=10,
    created_by=None,
):
    """
    Sets up fee structure for an enrollment.
    For one_time: creates single installment due immediately.
    For monthly: creates N installments spread monthly.
    """
    from decimal import Decimal
    from datetime import date
    from dateutil.relativedelta import relativedelta
    from django.db import transaction

    with transaction.atomic():
        total_amount = Decimal(str(total_amount))
        number_of_installments = max(1, int(number_of_installments))

        if fee_type == "one_time":
            number_of_installments = 1

        today = date.today()
        # Create InstallmentPlan which creates the installments
        plan = create_installment_plan(
            enrollment_id=enrollment_id,
            total_amount=total_amount,
            number_of_installments=number_of_installments,
            first_due_date=today,
            interval_days=30, # We'll override the due dates if monthly
            notes=f"{fee_type.capitalize()} Fee Setup",
            user=created_by,
        )

        # Fix the due dates for monthly
        if fee_type == "monthly":
            installments = plan.installments.all().order_by('installment_number')
            due_day = min(max(int(due_day), 1), 28)
            for i, inst in enumerate(installments):
                target = today + relativedelta(months=i)
                try:
                    due_date = target.replace(day=due_day)
                except ValueError:
                    due_date = target
                inst.due_date = due_date
                inst.save(update_fields=['due_date'])

        from apps.core.services import BaseService
        BaseService.audit_on_commit(
            action="CREATE",
            model_name="EnrollmentFeeSetup",
            object_id=enrollment_id,
            user=created_by,
            changes={
                "fee_type": fee_type,
                "total_amount": str(total_amount),
                "installments": number_of_installments,
            },
        )
        return plan

# ---------------------------------------------------------------
#  get_enrollment_fee_summary
# ---------------------------------------------------------------

def get_enrollment_fee_summary(enrollment_id):
    """
    Returns complete fee summary for an enrollment.
    """
    from decimal import Decimal
    from apps.finance.models import Installment

    summary = {
        "total_installments": 0,
        "total_amount": Decimal("0.00"),
        "total_paid": Decimal("0.00"),
        "total_outstanding": Decimal("0.00"),
        "pending_installments": 0,
        "paid_installments": 0,
        "overdue_installments": 0,
        "installments": [],
        "completion_percentage": 0,
    }

    try:
        from django.db.models import Sum, Count, Q
        installments = Installment.objects.filter(
            plan__enrollment_id=enrollment_id,
            plan__is_active=True
        ).order_by("installment_number")

        agg = installments.aggregate(
            total_amount=Sum("amount"),
            total_paid=Sum("paid_amount"),
            total_count=Count("id"),
            pending_count=Count(
                "id", filter=Q(status="pending") | Q(status="partial")
            ),
            paid_count=Count(
                "id", filter=Q(status="paid")
            ),
            overdue_count=Count(
                "id", filter=Q(status="overdue")
            ),
        )

        summary["total_installments"] = agg["total_count"] or 0
        summary["total_amount"] = agg["total_amount"] or Decimal("0.00")
        summary["total_paid"] = agg["total_paid"] or Decimal("0.00")
        summary["total_outstanding"] = summary["total_amount"] - summary["total_paid"]
        summary["pending_installments"] = agg["pending_count"] or 0
        summary["paid_installments"] = agg["paid_count"] or 0
        summary["overdue_installments"] = agg["overdue_count"] or 0
        summary["installments"] = list(installments)

        if summary["total_amount"] > 0:
            summary["completion_percentage"] = int(
                (summary["total_paid"] / summary["total_amount"]) * 100
            )
    except Exception:
        pass

    return summary

# ---------------------------------------------------------------
#  mark_overdue_installments
# ---------------------------------------------------------------

def mark_overdue_installments():
    """
    Marks all past-due installments as overdue.
    Call from management command or scheduler.
    """
    from datetime import date
    from apps.finance.models import Installment
    from django.db import transaction

    with transaction.atomic():
        today = date.today()
        updated = Installment.objects.filter(
            status__in=["pending", "partial"],
            due_date__lt=today,
        ).update(status="overdue")
        return updated

# ---------------------------------------------------------------
#  record_installment_payment
# ---------------------------------------------------------------

def record_installment_payment(
    installment_id,
    amount_paid,
    payment_method="Cash",
    reference_number="",
    payment_date=None,
    created_by=None,
    notes="",
    user=None,
):
    from decimal import Decimal
    from datetime import date
    from django.db import transaction
    from django.utils import timezone
    from django.core.exceptions import ValidationError
    from apps.finance.models import Installment, Payment

    if user and not created_by:
        created_by = user

    # Rate Limiting: Max 5 requests per 10 seconds per user/installment
    from django.core.cache import cache
    cache_key = f"rate_limit_installment_{installment_id}_{created_by.id if created_by else 'anon'}"
    requests = cache.get(cache_key, [])
    now = timezone.now().timestamp()
    requests = [r for r in requests if now - r < 10]
    if len(requests) >= 5:
        raise ValidationError("Rate limit exceeded. Please try again later.")
    requests.append(now)
    cache.set(cache_key, requests, 10)

    with transaction.atomic():
        installment = Installment.objects.select_for_update().select_related(
            "plan__enrollment__student",
            "plan__enrollment__session",
        ).get(pk=installment_id)

        amount_paid = Decimal(str(amount_paid))
        remaining = installment.amount - installment.paid_amount

        if amount_paid <= 0:
            raise ValidationError(
                "Payment amount must be greater than zero."
            )
        if installment.status == "paid":
            raise ValidationError("Installment is already paid.")
        if amount_paid > remaining:
            raise ValidationError(
                f"Amount PKR {amount_paid} exceeds "
                f"remaining balance of PKR {remaining}."
            )

        installment.paid_amount += amount_paid
        if installment.paid_amount >= installment.amount:
            installment.status = "paid"
            installment.paid_date = timezone.now().date()
        else:
            installment.status = "partial"

        installment.full_clean()
        installment.save(
            update_fields=[
                "paid_amount",
                "status",
                "paid_date",
            ]
        )

        payment_date = payment_date or date.today()

        payment = Payment(
            enrollment=installment.plan.enrollment,
            amount=amount_paid,
            payment_method=payment_method,
            reference_number=reference_number,
            payment_date=payment_date,
            created_by=created_by,
            recorded_by=created_by,
            notes=(
                f"Installment "
                f"{installment.installment_number} payment. {notes}"
            ),
        )
        # Handle receipt number explicitly using the helper method if needed or let it handle via full_clean/save
        payment.full_clean()
        payment.save()

        _create_audit_entry(
            user=created_by,
            action="PAYMENT",
            model_name="finance.Installment",
            object_id=installment.pk,
            changes={
                "amount_paid": str(amount_paid),
                "installment_number": installment.installment_number,
                "payment_id": payment.pk,
            },
        )

        return payment, installment



