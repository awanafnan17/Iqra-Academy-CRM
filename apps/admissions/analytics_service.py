import datetime
from django.db.models import Avg, F, Q, Count
from django.db.models.functions import TruncMonth
from django.utils import timezone
from apps.admissions.models import AdmissionApplication

def get_admission_funnel_metrics():
    """Calculates granular admission funnel metrics using database aggregations."""
    now = timezone.now()
    # Beginning of the current calendar month (timezone-aware)
    start_of_month = timezone.make_aware(datetime.datetime(now.year, now.month, 1))

    metrics = AdmissionApplication.objects.aggregate(
        total=Count("id"),
        pending_cnt=Count("id", filter=Q(status="pending")),
        under_review_cnt=Count("id", filter=Q(status="under_review")),
        approved_cnt=Count("id", filter=Q(status="approved")),
        rejected_cnt=Count("id", filter=Q(status="rejected")),
        converted_cnt=Count("id", filter=Q(converted_student__isnull=False)),
        this_month_app=Count("id", filter=Q(applied_at__gte=start_of_month)),
        this_month_conv=Count("id", filter=Q(applied_at__gte=start_of_month, converted_student__isnull=False)),
        avg_time=Avg(F("reviewed_at") - F("applied_at"), filter=Q(reviewed_at__isnull=False, applied_at__isnull=False))
    )

    total = metrics["total"] or 0
    pending = metrics["pending_cnt"] or 0
    under_review = metrics["under_review_cnt"] or 0
    approved = metrics["approved_cnt"] or 0
    rejected = metrics["rejected_cnt"] or 0
    converted = metrics["converted_cnt"] or 0

    conversion_rate = (converted / total * 100) if total > 0 else 0.0
    rejection_rate = (rejected / total * 100) if total > 0 else 0.0

    avg_duration = metrics["avg_time"]
    if avg_duration is not None:
        if isinstance(avg_duration, datetime.timedelta):
            average_review_time_days = round(avg_duration.total_seconds() / 86400.0, 2)
        else:
            try:
                average_review_time_days = round(float(avg_duration) / 86400.0, 2)
            except Exception:
                average_review_time_days = 0.0
    else:
        average_review_time_days = 0.0

    return {
        "total_applications": total,
        "pending": pending,
        "under_review": under_review,
        "approved": approved,
        "rejected": rejected,
        "converted": converted,
        "conversion_rate_percent": round(conversion_rate, 2),
        "rejection_rate_percent": round(rejection_rate, 2),
        "average_review_time_days": average_review_time_days,
        "this_month_applications": metrics["this_month_app"] or 0,
        "this_month_conversions": metrics["this_month_conv"] or 0,
    }


def get_admission_monthly_trend(year):
    """Retrieves monthly application counts and conversion counts for a specific year."""
    trend = (
        AdmissionApplication.objects.filter(applied_at__year=year)
        .annotate(month_date=TruncMonth("applied_at"))
        .values("month_date")
        .annotate(
            applications=Count("id"),
            conversions=Count("id", filter=Q(converted_student__isnull=False))
        )
        .order_by("month_date")
    )

    res = []
    for item in trend:
        dt = item["month_date"]
        if isinstance(dt, str):
            try:
                from django.utils.dateparse import parse_datetime
                dt = parse_datetime(dt) or datetime.datetime.strptime(dt[:10], "%Y-%m-%d")
            except Exception:
                pass
        month_str = dt.strftime("%B") if hasattr(dt, "strftime") else str(dt)
        res.append({
            "month": month_str,
            "applications": item["applications"],
            "conversions": item["conversions"]
        })
    return res


def get_session_demand():
    """Analyzes application demand across sessions."""
    demand = (
        AdmissionApplication.objects.filter(desired_session__isnull=False)
        .values("desired_session__name")
        .annotate(applications_count=Count("id"))
        .order_by("-applications_count")
    )

    return [
        {
            "session_name": item["desired_session__name"],
            "applications_count": item["applications_count"]
        }
        for item in demand
    ]


def get_admissions_period_metrics():
    """Calculates daily, weekly, and monthly counts for applications and enrollments.

    - Daily: applications received today, successful enrollments today.
    - Weekly: applications received this week, successful enrollments this week.
    - Monthly: applications received this month, successful enrollments this month.

    All datetime comparisons use the project's local timezone (Asia/Karachi).
    """
    from django.utils import timezone
    import datetime
    from apps.admissions.models import AdmissionApplication
    from apps.students.models import Enrollment

    # Get local current date/time
    local_now = timezone.localtime(timezone.now())
    local_today = local_now.date()

    # 1. Today boundaries (timezone-aware)
    today_start = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.min))
    today_end = timezone.make_aware(datetime.datetime.combine(local_today, datetime.time.max))

    # 2. Week boundaries (Monday-Sunday, timezone-aware)
    week_start_date = local_today - datetime.timedelta(days=local_today.weekday())
    week_end_date = week_start_date + datetime.timedelta(days=6)
    week_start = timezone.make_aware(datetime.datetime.combine(week_start_date, datetime.time.min))
    week_end = timezone.make_aware(datetime.datetime.combine(week_end_date, datetime.time.max))

    # 3. Month boundaries (timezone-aware)
    month_start_date = local_today.replace(day=1)
    if local_today.month == 12:
        month_end_date = datetime.date(local_today.year, 12, 31)
    else:
        month_end_date = datetime.date(local_today.year, local_today.month + 1, 1) - datetime.timedelta(days=1)
    month_start = timezone.make_aware(datetime.datetime.combine(month_start_date, datetime.time.min))
    month_end = timezone.make_aware(datetime.datetime.combine(month_end_date, datetime.time.max))

    # Applications: count via applied_at (DateTimeField)
    apps_today = AdmissionApplication.objects.filter(applied_at__range=(today_start, today_end)).count()
    apps_week = AdmissionApplication.objects.filter(applied_at__range=(week_start, week_end)).count()
    apps_month = AdmissionApplication.objects.filter(applied_at__range=(month_start, month_end)).count()

    # Enrollments: count via registration_date (DateField)
    # Filter directly using Date ranges because registration_date is DateField
    enrolls_today = Enrollment.objects.filter(registration_date=local_today).count()
    enrolls_week = Enrollment.objects.filter(registration_date__range=(week_start_date, week_end_date)).count()
    enrolls_month = Enrollment.objects.filter(registration_date__range=(month_start_date, month_end_date)).count()

    return {
        "today": {
            "applications_received": apps_today,
            "successful_enrollments": enrolls_today,
        },
        "this_week": {
            "applications_received": apps_week,
            "successful_enrollments": enrolls_week,
        },
        "this_month": {
            "applications_received": apps_month,
            "successful_enrollments": enrolls_month,
        }
    }


def get_admission_daily_metrics():
    """Wrapper function returning daily metrics."""
    return get_admissions_period_metrics()["today"]


def get_admission_weekly_metrics():
    """Wrapper function returning weekly metrics."""
    return get_admissions_period_metrics()["this_week"]


def get_admission_monthly_metrics():
    """Wrapper function returning monthly metrics."""
    return get_admissions_period_metrics()["this_month"]


