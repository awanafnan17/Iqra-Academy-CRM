import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from apps.finance.models import Payment, Expense, Refund, Installment, InstallmentPlan, ExpenseCategory
from apps.attendance.models import AttendanceRecord
from apps.students.models import Student, Lead, Enrollment
from apps.academics.models import Session

User = get_user_model()

class AnalyticsTests(TestCase):
    def setUp(self):
        super().setUp()

        # Setup Roles / Groups
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_accountant = Group.objects.create(name="Accountant")
        self.group_teacher = Group.objects.create(name="Teacher")

        # Setup Users
        self.admin_user = User.objects.create_user(
            username="admin_analytics@test.com",
            email="admin_analytics@test.com",
            password="password123",
        )
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(
            username="principal_analytics@test.com",
            email="principal_analytics@test.com",
            password="password123",
        )
        self.principal_user.groups.add(self.group_principal)

        self.accountant_user = User.objects.create_user(
            username="accountant_analytics@test.com",
            email="accountant_analytics@test.com",
            password="password123",
        )
        self.accountant_user.groups.add(self.group_accountant)

        self.teacher_user = User.objects.create_user(
            username="teacher_analytics@test.com",
            email="teacher_analytics@test.com",
            password="password123",
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Setup Session & Student & Enrollment
        self.session = Session.objects.create(
            name="Test Session",
            status="Active",
            fee=Decimal("1500.00"),
            registration_fee=Decimal("250.00"),
            start_date=timezone.localdate() - datetime.timedelta(days=30),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
        )

        self.student = Student.objects.create(
            full_name="Jane Doe",
            email="jane@test.com",
            status="Active",
        )

        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
            fee=Decimal("1500.00"),
            registration_fee=Decimal("250.00"),
            discount=Decimal("100.00"),
            registration_date=timezone.localdate(),
        )

    def test_get_revenue_trend(self):
        # Create payments
        p1 = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("1000.00"),
            payment_status="confirmed",
            payment_date=timezone.localdate(),
            is_late_fee_payment=False,
        )
        # Create a payment with late fee
        p2 = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("50.00"),
            payment_status="confirmed",
            payment_date=timezone.localdate(),
            is_late_fee_payment=True,
        )
        # Create approved expense
        cat = ExpenseCategory.objects.create(name="Utilities")
        Expense.objects.create(
            category=cat,
            amount=Decimal("200.00"),
            status="approved",
            expense_date=timezone.localdate(),
        )
        # Create refund
        p_ref = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("150.00"),
            payment_status="refunded",
            payment_date=timezone.localdate(),
        )
        Refund.objects.create(
            payment=p_ref,
            amount=Decimal("150.00"),
            status="processed",
            refund_date=timezone.localdate(),
        )

        from apps.analytics.services import get_revenue_trend
        trend = get_revenue_trend(timezone.localdate().year)

        current_month = timezone.localdate().month
        month_data = next(x for x in trend if x['month'] == current_month)

        self.assertEqual(month_data['tuition'], 1150.00)
        self.assertEqual(month_data['late_fees'], 50.00)
        self.assertEqual(month_data['expenses'], 200.00)
        self.assertEqual(month_data['refunds'], 150.00)
        self.assertEqual(month_data['net'], 850.00) # 1150 + 50 - 200 - 150

    def test_get_attendance_trend(self):
        # Create attendance records
        # Create attendance record
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate(),
            status="Present",
        )
        AttendanceRecord.objects.create(
            student=self.student,
            session=self.session,
            date=timezone.localdate() - datetime.timedelta(days=1),
            status="Absent",
        )

        from apps.analytics.services import get_attendance_trend
        trend = get_attendance_trend(self.session.id)

        self.assertEqual(len(trend), 2)
        # Ordered by date, so yesterday (Absent) comes first, today (Present) comes second
        self.assertEqual(trend[0]['absent'], 1)
        self.assertEqual(trend[1]['present'], 1)

    def test_get_enrollment_growth(self):
        from apps.analytics.services import get_enrollment_growth
        growth = get_enrollment_growth()

        current_month = timezone.localdate().month
        month_data = next(x for x in growth if x['month'] == current_month)
        self.assertEqual(month_data['new_enrollments'], 1)
        self.assertEqual(month_data['cumulative_enrollments'], 1)

    def test_get_lead_conversion_funnel(self):
        Lead.objects.create(
            name="Lead One",
            email="lead1@test.com",
            status="New",
        )
        Lead.objects.create(
            name="Lead Two",
            email="lead2@test.com",
            status="Converted",
        )

        from apps.analytics.services import get_lead_conversion_funnel
        funnel = get_lead_conversion_funnel()
        self.assertEqual(funnel['total_leads'], 2)
        self.assertEqual(funnel['conversion_rate'], 50.0)

    def test_get_payment_aging_report(self):
        plan = InstallmentPlan.objects.create(
            enrollment=self.enrollment,
            total_amount=Decimal("1200.00"),
            number_of_installments=2,
            is_active=True,
        )

        # Installment 1: Overdue by 15 days
        Installment.objects.create(
            plan=plan,
            installment_number=1,
            amount=Decimal("600.00"),
            due_date=timezone.localdate() - datetime.timedelta(days=15),
            paid_amount=Decimal("100.00"),
            status="overdue",
        )

        # Installment 2: Current (due in 15 days)
        Installment.objects.create(
            plan=plan,
            installment_number=2,
            amount=Decimal("600.00"),
            due_date=timezone.localdate() + datetime.timedelta(days=15),
            paid_amount=Decimal("0.00"),
            status="pending",
        )

        from apps.analytics.services import get_payment_aging_report
        report = get_payment_aging_report()

        self.assertEqual(report['1_30'], 500.00) # 600 - 100
        self.assertEqual(report['current'], 600.00)
        self.assertEqual(report['total_outstanding'], 1100.00)

    def test_view_role_restrictions(self):
        # Test api_revenue_trend: restricted to Admin, Accountant
        url = reverse("analytics:api_revenue_trend")

        # Unauthenticated redirects to login
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Admin can access
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'success')

        # Accountant can access
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Teacher gets 404 (denied)
        self.client.force_login(self.teacher_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Principal gets 404 (denied)
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
