import datetime
from decimal import Decimal
from django.db import models
from django.db.models import Sum, Count, Q, F, Value, DecimalField, OuterRef, Subquery, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.core.services import NotFoundError
from apps.finance.services import calculate_student_ledger, get_overdue_enrollments
from apps.attendance.services import AttendanceService


def count_weekdays(d1, d2):
    """Calculate the number of weekdays (Mon-Fri) between d1 and d2 inclusive in O(1)."""
    if d1 > d2:
        return 0
    days = (d2 - d1).days + 1
    weeks = days // 7
    weekdays = weeks * 5
    rem = days % 7
    if rem > 0:
        w1 = d1.weekday()
        for i in range(rem):
            if (w1 + i) % 7 < 5:
                weekdays += 1
    return weekdays


def get_admin_dashboard_metrics():
    """Retrieve read-only global admin metrics.

    Calculates confirmed gross revenue, approved expenses, processed refunds,
    net cash flow, active student counts, low attendance counts, and AI alerts.
    """
    from apps.students.models import Student
    from apps.finance.models import Payment, Expense, Refund
    from apps.ai_engine.models import PredictionLog
    from apps.attendance.models import AttendanceRecord
    from apps.admissions.models import AdmissionApplication

    total_revenue = Decimal("0.00")
    try:
        from apps.finance.models import Payment
        from django.db.models import Sum
        # Use the ACTUAL field name from Payment model
        agg = Payment.objects.aggregate(
            total=Sum("amount")
        )
        total_revenue = agg["total"] or Decimal("0.00")
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Revenue metric error: {exc}"
        )

    approved_expenses = Decimal("0.00")
    try:
        from apps.finance.models import Expense
        from django.db.models import Sum
        agg = Expense.objects.filter(status="approved").aggregate(
            total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )
        approved_expenses = agg["total"] or Decimal("0.00")
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Approved expenses metric error: {exc}"
        )

    processed_refunds = Decimal("0.00")
    try:
        from apps.finance.models import Refund
        from django.db.models import Sum
        agg = Refund.objects.filter(status="processed").aggregate(
            total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
        )
        processed_refunds = agg["total"] or Decimal("0.00")
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Processed refunds metric error: {exc}"
        )

    active_students = 0
    try:
        active_students = Student.objects.filter(status="Active").count()
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Active students count error: {exc}"
        )

    dropout_alerts_count = 0
    try:
        dropout_alerts_count = PredictionLog.objects.filter(
            prediction_type="dropout",
            risk_level__in=["high", "critical"],
            is_acknowledged=False
        ).count()
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Dropout alerts count error: {exc}"
        )

    low_attendance_count = 0
    try:
        low_attendance_count = Student.objects.filter(status="Active", has_low_attendance=True).count()
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Low attendance count error: {exc}"
        )

    net_cash_flow = total_revenue - processed_refunds - approved_expenses

    # Fetch all active enrollments and calculate system academic score
    system_academic_score = Decimal("0.00")
    try:
        from apps.students.models import Enrollment
        from apps.students.services import EnrollmentService
        active_enrollments = Enrollment.objects.filter(status="Active").select_related("session")
        _, system_academic_score = EnrollmentService.get_average_academic_score_for_enrollments(active_enrollments)
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"System academic score error: {exc}"
        )

    # Admissions metrics
    pending_admissions_count = 0
    monthly_approvals_count = 0
    try:
        pending_admissions_count = AdmissionApplication.objects.filter(status__in=["pending", "under_review"]).count()
        thirty_days_ago = timezone.now() - datetime.timedelta(days=30)
        monthly_approvals_count = AdmissionApplication.objects.filter(status="approved", reviewed_at__gte=thirty_days_ago).count()
    except Exception as exc:
        import logging
        logging.getLogger("crm").error(
            f"Admissions metrics error: {exc}"
        )

    return {
        "confirmed_revenue": total_revenue,
        "total_revenue": total_revenue,
        "approved_expenses": approved_expenses,
        "processed_refunds": processed_refunds,
        "net_cash_flow": net_cash_flow,
        "active_students": active_students,
        "low_attendance_count": low_attendance_count,
        "dropout_alerts_count": dropout_alerts_count,
        "system_academic_score": system_academic_score,
        "pending_admissions_count": pending_admissions_count,
        "monthly_approvals_count": monthly_approvals_count,
    }



def get_principal_dashboard_metrics():
    """Retrieve academic management metrics.

    Excludes all financial metrics. Returns counts of active students, active
    sessions, active leads, global attendance rates, low attendance alerts,
    pending exams, and active dropout risk alerts.
    """
    from apps.students.models import Student, Lead
    from apps.academics.models import Session
    from apps.exams.models import Exam
    from apps.ai_engine.models import PredictionLog
    from apps.attendance.models import AttendanceRecord

    active_students = Student.objects.filter(status="Active").count()
    active_sessions = Session.objects.filter(status="Active").count()
    active_leads = Lead.objects.exclude(status__in=["Converted", "Lost"]).count()
    pending_exams_count = Exam.objects.filter(is_published=False).count()
    dropout_alerts_count = PredictionLog.objects.filter(
        prediction_type="dropout",
        risk_level__in=["high", "critical"],
        is_acknowledged=False
    ).count()

    # Global attendance percentage across active sessions
    attendance_stats = AttendanceRecord.objects.filter(
        session__status="Active"
    ).aggregate(
        attended=Coalesce(Count("id", filter=Q(status__in=["Present", "Late"])), Value(0)),
        total=Coalesce(Count("id", filter=Q(status__in=["Present", "Absent", "Late"])), Value(0))
    )
    attended = attendance_stats["attended"] or 0
    total = attendance_stats["total"] or 0
    global_attendance_rate = (
        Decimal("100.00")
        if total == 0
        else (Decimal(attended) / Decimal(total) * Decimal("100.00")).quantize(Decimal("0.01"))
    )

    # Students with low attendance (flagged via automated check below 70%)
    low_attendance_count = Student.objects.filter(status="Active", has_low_attendance=True).count()

    return {
        "active_students": active_students,
        "active_sessions": active_sessions,
        "active_leads": active_leads,
        "global_attendance_rate": global_attendance_rate,
        "low_attendance_count": low_attendance_count,
        "pending_exams_count": pending_exams_count,
        "dropout_alerts_count": dropout_alerts_count,
    }


def get_teacher_dashboard_metrics(user):
    """Retrieve teacher specific dashboard metrics based on assigned sessions.

    Counts assigned active sessions, unique students enrolled, class attendance rates,
    missing attendance logs (not unlocked logs), and pending exams.
    """
    from apps.academics.models import Session, TeacherAssignment
    from apps.students.models import Enrollment
    from apps.attendance.models import AttendanceRecord
    from apps.exams.models import Exam

    # Retrieve active session and subject assignments
    assignments = list(TeacherAssignment.objects.filter(teacher=user, is_active=True).select_related("session"))
    assigned_session_ids = list(set(a.session_id for a in assignments if a.session.status == "Active"))

    if not assigned_session_ids:
        return {
            "assigned_sessions_count": 0,
            "assigned_students_count": 0,
            "teacher_attendance_rate": Decimal("100.00"),
            "pending_attendance_count": 0,
            "pending_exams_count": 0,
        }

    # Count of assigned active sessions
    assigned_sessions_count = len(assigned_session_ids)

    # Count of active enrolled students in those sessions
    assigned_students_count = Enrollment.objects.filter(
        session_id__in=assigned_session_ids,
        status="Active"
    ).values("student_id").distinct().count()

    # Class attendance rate across assigned sessions
    attendance_stats = AttendanceRecord.objects.filter(
        session_id__in=assigned_session_ids
    ).aggregate(
        attended=Coalesce(Count("id", filter=Q(status__in=["Present", "Late"])), Value(0)),
        total=Coalesce(Count("id", filter=Q(status__in=["Present", "Absent", "Late"])), Value(0))
    )
    attended = attendance_stats["attended"] or 0
    total = attendance_stats["total"] or 0
    teacher_attendance_rate = (
        Decimal("100.00")
        if total == 0
        else (Decimal(attended) / Decimal(total) * Decimal("100.00")).quantize(Decimal("0.01"))
    )

    # Teacher pending attendance sheets: counts missing attendance logs using database-level annotations
    today = timezone.localdate()
    thirty_days_ago = today - datetime.timedelta(days=30)

    # Respect locks: exclude dates where an AttendanceLock exists
    from apps.attendance.models import AttendanceLock

    recorded_subquery = AttendanceRecord.objects.filter(
        session=OuterRef("pk"),
        date__gte=thirty_days_ago,
        date__lte=today,
        date__week_day__in=[2, 3, 4, 5, 6]
    ).filter(
        Q(session__start_date__isnull=True) | Q(date__gte=F("session__start_date"))
    ).values("session").annotate(
        recorded_days=Coalesce(Count("date", distinct=True), Value(0))
    ).values("recorded_days")

    locked_subquery = AttendanceLock.objects.filter(
        session=OuterRef("pk"),
        date__gte=thirty_days_ago,
        date__lte=today,
        date__week_day__in=[2, 3, 4, 5, 6]
    ).filter(
        Q(session__start_date__isnull=True) | Q(date__gte=F("session__start_date"))
    ).exclude(
        date__in=Subquery(
            AttendanceRecord.objects.filter(
                session=OuterRef("session")
            ).values("date")
        )
    ).values("session").annotate(
        locked_days=Coalesce(Count("date", distinct=True), Value(0))
    ).values("locked_days")

    sessions = Session.objects.filter(
        id__in=assigned_session_ids
    ).annotate(
        recorded_count=Coalesce(Subquery(recorded_subquery), Value(0), output_field=IntegerField()),
        locked_count=Coalesce(Subquery(locked_subquery), Value(0), output_field=IntegerField())
    )

    pending_attendance_count = 0
    for s in sessions:
        limit_date = max(s.start_date or thirty_days_ago, thirty_days_ago)
        expected = count_weekdays(limit_date, today)
        # We subtract both recorded and locked days to respect locks and prevent double-counting
        pending_attendance_count += max(0, expected - s.recorded_count - s.locked_count)

    # Pending exams
    pending_exams_count = Exam.objects.filter(
        session_id__in=assigned_session_ids,
        is_published=False
    ).count()

    return {
        "assigned_sessions_count": assigned_sessions_count,
        "assigned_students_count": assigned_students_count,
        "teacher_attendance_rate": teacher_attendance_rate,
        "pending_attendance_count": pending_attendance_count,
        "pending_exams_count": pending_exams_count,
    }


def get_accountant_dashboard_metrics():
    """Retrieve financial metrics for the accountant dashboard.

    Reuses existing financial service functions. Calculates gross confirmed revenue,
    unpaid installments, overdue fees count, pending expenses, and processed refunds.
    """
    from apps.finance.models import Payment, Expense, Refund, Installment

    confirmed_revenue = Payment.objects.aggregate(
        total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
    )["total"] or Decimal("0.00")

    unpaid_installments = Installment.objects.filter(status="unpaid", plan__is_active=True).aggregate(
        total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
    )["total"] or Decimal("0.00")

    pending_expenses = Expense.objects.filter(status="pending").aggregate(
        total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
    )["total"] or Decimal("0.00")

    processed_refunds = Refund.objects.filter(status="processed").aggregate(
        total=Coalesce(Sum("amount"), Value(Decimal("0.00")))
    )["total"] or Decimal("0.00")

    # Overdue fee count: directly count from get_overdue_enrollments QuerySet
    overdue_count = get_overdue_enrollments().count()

    return {
        "confirmed_revenue": confirmed_revenue,
        "unpaid_installments": unpaid_installments,
        "overdue_count": overdue_count,
        "pending_expenses": pending_expenses,
        "processed_refunds": processed_refunds,
    }


def get_registrar_dashboard_metrics():
    """Retrieve metrics for the registrar registry dashboard.

    Excludes all financial and grade metrics. Returns active leads, today's
    registrations, converted leads, suspended students, and active student counts.
    """
    from apps.students.models import Student, Lead, Enrollment
    from apps.admissions.models import AdmissionApplication

    active_leads = Lead.objects.exclude(status__in=["Converted", "Lost"]).count()
    todays_registrations = Enrollment.objects.filter(created_at__date=timezone.localdate(), status="Active").count()
    converted_leads = Lead.objects.filter(status="Converted").count()
    suspended_students = Student.objects.filter(status="Suspended").count()
    active_students = Student.objects.filter(status="Active").count()
    pending_admissions_count = AdmissionApplication.objects.filter(status__in=["pending", "under_review"]).count()

    return {
        "active_leads": active_leads,
        "todays_registrations": todays_registrations,
        "converted_leads": converted_leads,
        "suspended_students": suspended_students,
        "active_students": active_students,
        "pending_admissions_count": pending_admissions_count,
    }


def get_student_dashboard_metrics(user):
    """Retrieve student portal dashboard metrics.

    Ensures we stay strictly within the max 4 query budget for Student.
    """
    from apps.students.models import Student, Enrollment
    from apps.exams.models import ExamResult
    from apps.notifications.models import Notification
    from apps.finance.models import Payment, Refund

    # Query 1: Fetch enrollment with student, session and annotated ledger aggregates in 1 single database roundtrip
    enrollment = Enrollment.objects.filter(
        student__portal_user=user, status="Active"
    ).select_related("student", "session").annotate(
        total_paid=Coalesce(Subquery(
            Payment.objects.filter(
                enrollment=OuterRef("pk"), payment_status="confirmed"
            ).values("enrollment").annotate(total=Sum("amount")).values("total")
        ), Value(Decimal("0.00")), output_field=DecimalField()),
        total_refunded=Coalesce(Subquery(
            Refund.objects.filter(
                payment__enrollment=OuterRef("pk"), status="processed"
            ).values("payment__enrollment").annotate(total=Sum("amount")).values("total")
        ), Value(Decimal("0.00")), output_field=DecimalField())
    ).first()

    if not enrollment:
        student = Student.objects.filter(portal_user=user).first()
        if not student:
            raise NotFoundError("Student profile not found.")

        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        return {
            "student_name": student.full_name,
            "session_name": None,
            "attendance_percentage": Decimal("100.00"),
            "outstanding_balance": Decimal("0.00"),
            "unread_notifications": unread_notifications,
            "exam_results": [],
            "has_low_attendance": student.has_low_attendance,
        }

    student = enrollment.student
    session_name = enrollment.session.name

    # Ledger calculations (direct, avoiding expensive services.py calls to preserve query budget)
    fee = enrollment.fee if enrollment.fee is not None else enrollment.session.fee
    reg_fee = enrollment.registration_fee if enrollment.registration_fee is not None else enrollment.session.registration_fee
    discount = enrollment.discount or Decimal("0.00")
    total_payable = fee + reg_fee - discount
    outstanding_balance = Decimal("0.00") if enrollment.is_fee_waived else (total_payable - enrollment.total_paid + enrollment.total_refunded)

    # Query 2: Fetch student attendance rate in 1 query
    from apps.attendance.models import AttendanceRecord
    attendance_stats = AttendanceRecord.objects.filter(
        student=student,
        session=enrollment.session
    ).aggregate(
        attended=Coalesce(Count("id", filter=Q(status__in=["Present", "Late"])), Value(0)),
        total=Coalesce(Count("id", filter=Q(status__in=["Present", "Absent", "Late"])), Value(0))
    )
    attended = attendance_stats["attended"] or 0
    total_att = attendance_stats["total"] or 0
    attendance_percentage = (
        Decimal("100.00")
        if total_att == 0
        else (Decimal(attended) / Decimal(total_att) * Decimal("100.00")).quantize(Decimal("0.01"))
    )

    # Query 3: Count of unread notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

    # Query 4: List of published exam results
    exam_results = list(
        ExamResult.objects.filter(
            student=student,
            exam__is_published=True
        )
        .select_related("exam", "exam__subject")
        .annotate(score=F("marks_obtained"))
        .values("exam__name", "exam__subject__name", "score", "grade", "remarks")
    )

    return {
        "student_name": student.full_name,
        "session_name": session_name,
        "attendance_percentage": attendance_percentage,
        "outstanding_balance": outstanding_balance,
        "unread_notifications": unread_notifications,
        "exam_results": exam_results,
        "has_low_attendance": student.has_low_attendance,
    }


def get_guardian_dashboard_metrics(user):
    """Retrieve parent portal dashboard metrics.

    Ensures we stay strictly within the max 5 query budget for Guardian.
    """
    from apps.students.models import Guardian, Enrollment
    from apps.finance.models import Payment, Refund
    from apps.attendance.models import AttendanceRecord
    from apps.exams.models import ExamResult
    from apps.notifications.models import Notification

    # Determine guardian email to select all linked children
    guardian_email = user.email
    if not guardian_email:
        guardian = Guardian.objects.filter(portal_user=user).first()
        if guardian:
            guardian_email = guardian.email

    if not guardian_email:
        return {
            "children_count": 0,
            "total_outstanding_balance": Decimal("0.00"),
            "children": [],
            "unread_notifications": 0,
        }

    # Query 1: Fetch all active enrollments for linked children with annotated payment/refund sums in 1 query
    enrollments = list(
        Enrollment.objects.filter(
            student__guardians__email=guardian_email,
            status="Active"
        )
        .select_related("student", "session")
        .annotate(
            total_paid=Coalesce(Subquery(
                Payment.objects.filter(
                    enrollment=OuterRef("pk"), payment_status="confirmed", is_late_fee_payment=False
                ).values("enrollment").annotate(total=Sum("amount")).values("total")
            ), Value(Decimal("0.00")), output_field=DecimalField()),
            total_refunded=Coalesce(Subquery(
                Refund.objects.filter(
                    payment__enrollment=OuterRef("pk"), status="processed"
                ).values("payment__enrollment").annotate(total=Sum("amount")).values("total")
            ), Value(Decimal("0.00")), output_field=DecimalField())
        )
    )

    if not enrollments:
        # Query 2: Fallback unread notification count
        unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()
        return {
            "children_count": 0,
            "total_outstanding_balance": Decimal("0.00"),
            "children": [],
            "unread_notifications": unread_notifications,
        }

    student_ids = [e.student_id for e in enrollments]

    # Query 2: Batch attendance statistics in 1 query
    attendance_stats = (
        AttendanceRecord.objects.filter(
            student_id__in=student_ids,
            session__status="Active"
        )
        .values("student_id", "session_id")
        .annotate(
            attended=Coalesce(Count("id", filter=Q(status__in=["Present", "Late"])), Value(0)),
            total=Coalesce(Count("id", filter=Q(status__in=["Present", "Absent", "Late"])), Value(0)),
        )
    )
    attendance_map = {
        (a["student_id"], a["session_id"]): (a["attended"], a["total"])
        for a in attendance_stats
    }

    # Query 3: Batch exam results in 1 query
    results_qs = (
        ExamResult.objects.filter(
            student_id__in=student_ids,
            exam__is_published=True
        )
        .select_related("exam", "exam__subject")
        .annotate(score=F("marks_obtained"))
        .values("student_id", "exam__name", "exam__subject__name", "score", "grade")
    )
    results_by_student = {}
    for r in results_qs:
        results_by_student.setdefault(r["student_id"], []).append(r)

    # Query 4: Count of unread notifications
    unread_notifications = Notification.objects.filter(recipient=user, is_read=False).count()

    # Process metrics per child
    children_details = []
    total_outstanding_balance = Decimal("0.00")

    for enrollment in enrollments:
        # 1. Net outstanding balance calculation using the correct Net Paid formula
        fee = enrollment.fee if enrollment.fee is not None else enrollment.session.fee
        reg_fee = enrollment.registration_fee if enrollment.registration_fee is not None else enrollment.session.registration_fee
        discount = enrollment.discount or Decimal("0.00")
        total_payable = fee + reg_fee - discount

        net_paid = enrollment.total_paid - enrollment.total_refunded
        balance = Decimal("0.00") if enrollment.is_fee_waived else (total_payable - net_paid)
        total_outstanding_balance += balance

        # 2. Attendance percentage calculation
        att_data = attendance_map.get((enrollment.student_id, enrollment.session_id), (0, 0))
        attended, total_att = att_data
        if total_att == 0:
            attendance_pct = Decimal("100.00")
        else:
            attendance_pct = (
                Decimal(attended) / Decimal(total_att) * Decimal("100.00")
            ).quantize(Decimal("0.01"))

        children_details.append({
            "student_id": enrollment.student_id,
            "student_name": enrollment.student.full_name,
            "session_name": enrollment.session.name,
            "outstanding_balance": balance,
            "attendance_percentage": attendance_pct,
            "grades": results_by_student.get(enrollment.student_id, []),
        })

    return {
        "children_count": len(children_details),
        "total_outstanding_balance": total_outstanding_balance,
        "children": children_details,
        "unread_notifications": unread_notifications,
    }
