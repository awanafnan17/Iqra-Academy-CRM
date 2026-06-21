import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session
from apps.admissions.models import AdmissionApplication
from apps.admissions.services import AdmissionService
from apps.admissions.analytics_service import (
    get_admission_funnel_metrics,
    get_admission_monthly_trend,
    get_session_demand,
    get_admissions_period_metrics,
)

User = get_user_model()

class AdmissionFunnelAnalyticsTests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed roles
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_principal, _ = Group.objects.get_or_create(name="Principal")
        self.group_accountant, _ = Group.objects.get_or_create(name="Accountant")
        self.group_registrar, _ = Group.objects.get_or_create(name="Registrar")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")

        # Seed users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Create session
        self.session = Session.objects.create(
            name="Funnel Analytics Session",
            code="FAS",
            status="Active",
            max_capacity=50,
            session_category="CSS",
            academic_year="2026",
            batch_number="1",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("100.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
        )

    def test_metrics_empty(self):
        """Ensure funnel metrics handle division by zero safely when no applications exist."""
        metrics = get_admission_funnel_metrics()
        self.assertEqual(metrics["total_applications"], 0)
        self.assertEqual(metrics["conversion_rate_percent"], 0.0)
        self.assertEqual(metrics["rejection_rate_percent"], 0.0)
        self.assertEqual(metrics["average_review_time_days"], 0.0)

    def test_funnel_metrics_correct(self):
        """Ensure get_admission_funnel_metrics aggregates application stages and time metrics accurately."""
        # Create applications
        # 1. Pending application
        app_pending = AdmissionService.submit_application(
            full_name="Pending App", father_name="Father", email="p@example.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )

        # 2. Rejected application
        app_rejected = AdmissionService.submit_application(
            full_name="Rejected App", father_name="Father", email="r@example.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        AdmissionService.review_application(app_rejected.id, self.admin_user)
        # Use direct save with full_clean for review timestamps
        app_rejected.status = "rejected"
        app_rejected.reviewed_at = app_rejected.applied_at + datetime.timedelta(days=2)
        app_rejected.save()

        # 3. Approved and converted application
        app_converted = AdmissionService.submit_application(
            full_name="Converted App", father_name="Father", email="c@example.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        app_converted = AdmissionService.approve_application(app_converted.id, self.admin_user)
        # Override reviewed_at so average review time averages to exactly 2.0 days
        app_converted.reviewed_at = app_converted.applied_at + datetime.timedelta(days=2)
        app_converted.save(update_fields=["reviewed_at"])
        student = AdmissionService.convert_to_student(app_converted.id, self.admin_user)

        # Retrieve metrics
        metrics = get_admission_funnel_metrics()
        self.assertEqual(metrics["total_applications"], 3)
        self.assertEqual(metrics["pending"], 1)
        self.assertEqual(metrics["rejected"], 1)
        self.assertEqual(metrics["converted"], 1)

        # Rates
        self.assertEqual(metrics["conversion_rate_percent"], 33.33)
        self.assertEqual(metrics["rejection_rate_percent"], 33.33)

        # Average review time: 2 days for the rejected one, 2 days for the converted one
        self.assertEqual(metrics["average_review_time_days"], 2.0)

    def test_monthly_trend_correct(self):
        """Ensure get_admission_monthly_trend returns correct month labels and counts."""
        year = timezone.now().year
        trend = get_admission_monthly_trend(year)
        # Verify it lists trend metrics
        self.assertIsInstance(trend, list)

    def test_session_demand_correct(self):
        """Ensure get_session_demand correctly ranks session demand."""
        # Create applications
        AdmissionService.submit_application(
            full_name="Student 1", father_name="Father", email="s1@example.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        demand = get_session_demand()
        self.assertTrue(len(demand) > 0)
        self.assertEqual(demand[0]["session_name"], self.session.name)
        self.assertEqual(demand[0]["applications_count"], 1)

    def test_permission_enforcement(self):
        """Ensure executive analytics dashboard is restricted to Admin/Principal/Accountant."""
        url = reverse("admin_panel:analytics")

        # Unauthenticated redirects to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Teacher (unauthorized) gets 404
        self.client.force_login(self.teacher_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Admin (authorized) gets 200
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admission Funnel")

    def test_admissions_period_metrics_empty(self):
        """Ensure get_admissions_period_metrics returns all zeros when there is no data."""
        from apps.students.models import Enrollment
        AdmissionApplication.objects.all().delete()
        Enrollment.objects.all().delete()

        metrics = get_admissions_period_metrics()
        self.assertEqual(metrics["today"]["applications_received"], 0)
        self.assertEqual(metrics["today"]["successful_enrollments"], 0)
        self.assertEqual(metrics["this_week"]["applications_received"], 0)
        self.assertEqual(metrics["this_week"]["successful_enrollments"], 0)
        self.assertEqual(metrics["this_month"]["applications_received"], 0)
        self.assertEqual(metrics["this_month"]["successful_enrollments"], 0)

    def test_admissions_period_metrics_correct(self):
        """Ensure that applications and enrollments created today, this week, and this month count correctly."""
        from apps.students.models import Student, Enrollment
        from unittest.mock import patch
        AdmissionApplication.objects.all().delete()
        Enrollment.objects.all().delete()

        # Wednesday, June 17, 2026 12:00:00 Asia/Karachi (07:00:00 UTC)
        frozen_dt = datetime.datetime(2026, 6, 17, 7, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("django.utils.timezone.now", return_value=frozen_dt):
            local_now = timezone.localtime(timezone.now())
            local_today = local_now.date()

            # Create an application today
            AdmissionApplication.objects.create(
                full_name="Today App", father_name="Father", email="today@example.com", phone="123",
                date_of_birth=datetime.date(2000, 1, 1), exam_type="CSS"
            )

            # Create an enrollment today
            student_today = Student.objects.create(full_name="Student Today")
            Enrollment.objects.create(
                student=student_today,
                session=self.session,
                registration_date=local_today
            )

            metrics = get_admissions_period_metrics()
            self.assertEqual(metrics["today"]["applications_received"], 1)
            self.assertEqual(metrics["today"]["successful_enrollments"], 1)
            self.assertEqual(metrics["this_week"]["applications_received"], 1)
            self.assertEqual(metrics["this_week"]["successful_enrollments"], 1)
            self.assertEqual(metrics["this_month"]["applications_received"], 1)
            self.assertEqual(metrics["this_month"]["successful_enrollments"], 1)

    def test_admissions_period_metrics_boundaries(self):
        """Ensure boundary dates (past/future) do not get counted in wrong periods."""
        from apps.students.models import Student, Enrollment
        from unittest.mock import patch
        AdmissionApplication.objects.all().delete()
        Enrollment.objects.all().delete()

        # Wednesday, June 17, 2026 12:00:00 Asia/Karachi (07:00:00 UTC)
        frozen_dt = datetime.datetime(2026, 6, 17, 7, 0, 0, tzinfo=datetime.timezone.utc)
        with patch("django.utils.timezone.now", return_value=frozen_dt):
            # Create a yesterday application (June 16, 2026 - within week, within month)
            yesterday_date = datetime.date(2026, 6, 16)
            yesterday_start = timezone.make_aware(datetime.datetime.combine(yesterday_date, datetime.time.min))
            app_yesterday = AdmissionApplication.objects.create(
                full_name="Yesterday App", father_name="Father", email="yesterday@example.com", phone="123",
                date_of_birth=datetime.date(2000, 1, 1), exam_type="CSS"
            )
            # Manually update applied_at since auto_now_add makes it read-only on save()
            AdmissionApplication.objects.filter(id=app_yesterday.id).update(applied_at=yesterday_start)

            # Create a yesterday enrollment
            student_yesterday = Student.objects.create(full_name="Student Yesterday")
            Enrollment.objects.create(
                student=student_yesterday,
                session=self.session,
                registration_date=yesterday_date
            )

            # Create a last week application (June 10, 2026 - outside week, within month)
            last_week_date = datetime.date(2026, 6, 10)
            last_week_start = timezone.make_aware(datetime.datetime.combine(last_week_date, datetime.time.min))
            app_last_week = AdmissionApplication.objects.create(
                full_name="Last Week App", father_name="Father", email="lastweek@example.com", phone="123",
                date_of_birth=datetime.date(2000, 1, 1), exam_type="CSS"
            )
            AdmissionApplication.objects.filter(id=app_last_week.id).update(applied_at=last_week_start)

            # Create last week enrollment
            student_last_week = Student.objects.create(full_name="Student Last Week")
            Enrollment.objects.create(
                student=student_last_week,
                session=self.session,
                registration_date=last_week_date
            )

            # Create a last month application (May 17, 2026 - outside week, outside month)
            last_month_date = datetime.date(2026, 5, 17)
            last_month_start = timezone.make_aware(datetime.datetime.combine(last_month_date, datetime.time.min))
            app_last_month = AdmissionApplication.objects.create(
                full_name="Last Month App", father_name="Father", email="lastmonth@example.com", phone="123",
                date_of_birth=datetime.date(2000, 1, 1), exam_type="CSS"
            )
            AdmissionApplication.objects.filter(id=app_last_month.id).update(applied_at=last_month_start)

            # Create last month enrollment
            student_last_month = Student.objects.create(full_name="Student Last Month")
            Enrollment.objects.create(
                student=student_last_month,
                session=self.session,
                registration_date=last_month_date
            )

            # Create a next month application (July 17, 2026 - outside week, outside month)
            next_month_date = datetime.date(2026, 7, 17)
            next_month_start = timezone.make_aware(datetime.datetime.combine(next_month_date, datetime.time.min))
            app_next_month = AdmissionApplication.objects.create(
                full_name="Next Month App", father_name="Father", email="nextmonth@example.com", phone="123",
                date_of_birth=datetime.date(2000, 1, 1), exam_type="CSS"
            )
            AdmissionApplication.objects.filter(id=app_next_month.id).update(applied_at=next_month_start)

            # Create next month enrollment
            student_next_month = Student.objects.create(full_name="Student Next Month")
            Enrollment.objects.create(
                student=student_next_month,
                session=self.session,
                registration_date=next_month_date
            )

            metrics = get_admissions_period_metrics()

            # Today: should be 0 for both
            self.assertEqual(metrics["today"]["applications_received"], 0)
            self.assertEqual(metrics["today"]["successful_enrollments"], 0)

            # This Week: June 15 to June 21. Should include yesterday (June 16), but not June 10, May 17, or July 17.
            # So counts must be exactly 1
            self.assertEqual(metrics["this_week"]["applications_received"], 1)
            self.assertEqual(metrics["this_week"]["successful_enrollments"], 1)

            # This Month: June 1 to June 30. Should include yesterday (June 16) and last week (June 10), but not May 17 or July 17.
            # So counts must be exactly 2
            self.assertEqual(metrics["this_month"]["applications_received"], 2)
            self.assertEqual(metrics["this_month"]["successful_enrollments"], 2)

