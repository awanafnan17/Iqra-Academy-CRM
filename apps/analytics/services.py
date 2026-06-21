import datetime
from decimal import Decimal
from django.db import models
from django.db.models import Sum, Count, Q
from django.db.models.functions import ExtractMonth, Coalesce
from django.utils.timezone import now

from apps.finance.models import Payment, Expense, Refund, Installment
from apps.attendance.models import AttendanceRecord
from apps.students.models import Student, Lead, Enrollment
from apps.academics.models import Session

def get_revenue_trend(year=None):
    """Calculate monthly confirmed revenue, expenses, refunds, and net cash flow.

    Returns a list of 12 dicts (one for each month).
    """
    if year is None:
        year = now().year

    # confirmed payments (non-late fee) and late fee payments
    payments_by_month = Payment.objects.filter(
        payment_date__year=year
    ).annotate(
        month_val=ExtractMonth('payment_date')
    ).values('month_val').annotate(
        tuition=Coalesce(Sum('amount', filter=Q(is_late_fee_payment=False)), Decimal('0.00')),
        late_fees=Coalesce(Sum('amount', filter=Q(is_late_fee_payment=True)), Decimal('0.00'))
    )

    # approved expenses
    expenses_by_month = Expense.objects.filter(
        expense_date__year=year,
        status='approved'
    ).annotate(
        month_val=ExtractMonth('expense_date')
    ).values('month_val').annotate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )

    # processed refunds
    refunds_by_month = Refund.objects.filter(
        refund_date__year=year,
        status='processed'
    ).annotate(
        month_val=ExtractMonth('refund_date')
    ).values('month_val').annotate(
        total=Coalesce(Sum('amount'), Decimal('0.00'))
    )

    trend = []
    for m in range(1, 13):
        p = next((x for x in payments_by_month if x['month_val'] == m), None)
        e = next((x for x in expenses_by_month if x['month_val'] == m), None)
        r = next((x for x in refunds_by_month if x['month_val'] == m), None)

        tuition = p['tuition'] if p else Decimal('0.00')
        late_fees = p['late_fees'] if p else Decimal('0.00')
        expenses = e['total'] if e else Decimal('0.00')
        refunds = r['total'] if r else Decimal('0.00')

        trend.append({
            'month': m,
            'tuition': float(tuition),
            'late_fees': float(late_fees),
            'expenses': float(expenses),
            'refunds': float(refunds),
            'net': float(tuition + late_fees - expenses - refunds)
        })

    return trend

def get_attendance_trend(session_id=None):
    """Get historical daily attendance stats for a session (or all sessions if None)."""
    qs = AttendanceRecord.objects.all()
    if session_id:
        qs = qs.filter(session_id=session_id)

    attendance_data = qs.values('date').annotate(
        present=Count('pk', filter=Q(status='Present')),
        absent=Count('pk', filter=Q(status='Absent')),
        late=Count('pk', filter=Q(status='Late')),
        excused=Count('pk', filter=Q(status='Excused')),
        total=Count('pk')
    ).order_by('date')

    trend = []
    for record in attendance_data:
        total = record['total']
        present_rate = (record['present'] + record['late']) / total * 100 if total > 0 else 0
        trend.append({
            'date': record['date'].strftime('%Y-%m-%d'),
            'present': record['present'],
            'absent': record['absent'],
            'late': record['late'],
            'excused': record['excused'],
            'total': total,
            'present_rate': float(round(present_rate, 1))
        })

    # If no records exist, return an empty template
    return trend

def get_enrollment_growth():
    """Calculate new monthly and cumulative enrollments for the current year."""
    current_year = now().year

    enrollments_by_month = Enrollment.objects.filter(
        registration_date__year=current_year
    ).annotate(
        month_val=ExtractMonth('registration_date')
    ).values('month_val').annotate(
        count=Count('pk')
    ).order_by('month_val')

    growth = []
    cumulative = 0
    for m in range(1, 13):
        e = next((x for x in enrollments_by_month if x['month_val'] == m), None)
        count = e['count'] if e else 0
        cumulative += count
        growth.append({
            'month': m,
            'new_enrollments': count,
            'cumulative_enrollments': cumulative
        })

    return growth

def get_lead_conversion_funnel():
    """Calculate conversion rates across Lead statuses."""
    lead_stats = Lead.objects.values('status').annotate(
        count=Count('pk')
    )

    statuses = ["New", "Contacted", "Interested", "Converted", "Lost"]
    funnel = {s: 0 for s in statuses}
    for stat in lead_stats:
        if stat['status'] in funnel:
            funnel[stat['status']] = stat['count']

    total_leads = sum(funnel.values())
    conversion_rate = (funnel['Converted'] / total_leads * 100) if total_leads > 0 else 0

    return {
        'funnel': [{'status': k, 'count': v} for k, v in funnel.items()],
        'total_leads': total_leads,
        'conversion_rate': float(round(conversion_rate, 1))
    }

def get_payment_aging_report():
    """Calculate outstanding aging buckets for pending/partial/overdue installments."""
    today = now().date()

    unpaid_installments = Installment.objects.filter(
        status__in=["pending", "partial", "overdue"]
    ).values('due_date', 'amount', 'paid_amount')

    aging = {
        'current': Decimal('0.00'),
        '1_30': Decimal('0.00'),
        '31_60': Decimal('0.00'),
        '61_90': Decimal('0.00'),
        '90_plus': Decimal('0.00'),
    }

    for inst in unpaid_installments:
        due_date = inst['due_date']
        unpaid_amount = inst['amount'] - inst['paid_amount']
        if unpaid_amount <= 0:
            continue

        if due_date >= today:
            aging['current'] += unpaid_amount
        else:
            days_overdue = (today - due_date).days
            if days_overdue <= 30:
                aging['1_30'] += unpaid_amount
            elif days_overdue <= 60:
                aging['31_60'] += unpaid_amount
            elif days_overdue <= 90:
                aging['61_90'] += unpaid_amount
            else:
                aging['90_plus'] += unpaid_amount

    report = {k: float(v) for k, v in aging.items()}
    report['total_outstanding'] = float(sum(aging.values()))

    return report


def get_teacher_workload():
    """Calculate weekly teaching hours, sessions, and subjects for all active teachers.

    Avoids N+1 queries.
    """
    from apps.staff.models import FacultyProfile
    from apps.academics.models import ClassSchedule

    faculties = FacultyProfile.objects.filter(is_active=True).select_related('user')

    workload = {}
    for f in faculties:
        workload[f.id] = {
            'faculty_id': f.id,
            'name': f.user.full_name or f.user.username,
            'designation': f.designation,
            'department': f.department,
            'hours_per_week': 0.0,
            'sessions': set(),
            'subjects': set(),
        }

    schedules = ClassSchedule.objects.filter(is_active=True)
    for s in schedules:
        if s.faculty_id in workload:
            if s.start_time and s.end_time:
                # Calculate duration in hours
                dummy_date = datetime.date.min
                dt1 = datetime.datetime.combine(dummy_date, s.start_time)
                dt2 = datetime.datetime.combine(dummy_date, s.end_time)
                duration_hours = (dt2 - dt1).total_seconds() / 3600.0
                workload[s.faculty_id]['hours_per_week'] += duration_hours

            workload[s.faculty_id]['sessions'].add(s.session_id)
            workload[s.faculty_id]['subjects'].add(s.subject_id)

    report = []
    for fid, data in workload.items():
        data['sessions_count'] = len(data['sessions'])
        data['subjects_count'] = len(data['subjects'])
        del data['sessions']
        del data['subjects']
        data['hours_per_week'] = round(data['hours_per_week'], 2)
        report.append(data)

    return report

