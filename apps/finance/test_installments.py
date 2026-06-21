import os
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    "config.settings.base",
)

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from decimal import Decimal

User = get_user_model()


class InstallmentSystemTests(TestCase):

    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(
            name="Admin"
        )
        self.admin = User.objects.create_user(
            username="admin_install_test",
            password="testpass123",
            email="admin_install@test.com",
        )
        self.admin.groups.add(self.admin_group)
        self.client.force_login(self.admin)

        from apps.academics.models import Session
        self.session = Session.objects.create(
            name="Install Test Session",
            session_category="css",
            status="active",
            roll_prefix="IT",
        )

        from apps.students.models import Student, Enrollment
        self.student = Student.objects.create(
            full_name="Install Test Student",
            phone="03009876543",
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="active",
        )

    def test_one_time_fee_creates_single_installment(self):
        from apps.finance.services import (
            setup_enrollment_fee,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="one_time",
            total_amount=Decimal("50000.00"),
            number_of_installments=1,
            created_by=self.admin,
        )
        result = plan.installments.all()
        self.assertEqual(len(result), 1)
        self.assertEqual(
            result[0].amount,
            Decimal("50000.00"),
        )
        self.assertEqual(result[0].status, "pending")
        self.assertEqual(result[0].installment_number, 1)

    def test_monthly_creates_correct_count(self):
        from apps.finance.services import (
            setup_enrollment_fee,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="monthly",
            total_amount=Decimal("60000.00"),
            number_of_installments=6,
            due_day=10,
            created_by=self.admin,
        )
        result = plan.installments.all()
        self.assertEqual(len(result), 6)
        for inst in result:
            self.assertEqual(
                inst.amount,
                Decimal("10000.00"),
            )

    def test_full_payment_marks_installment_paid(self):
        from apps.finance.services import (
            setup_enrollment_fee,
            record_installment_payment,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="one_time",
            total_amount=Decimal("25000.00"),
            created_by=self.admin,
        )
        insts = plan.installments.all()
        payment, updated = record_installment_payment(
            installment_id=insts[0].pk,
            amount_paid=Decimal("25000.00"),
            payment_method="Cash",
            created_by=self.admin,
        )
        self.assertEqual(updated.status, "paid")
        self.assertEqual(
            updated.paid_amount,
            Decimal("25000.00"),
        )

    def test_partial_payment_stays_pending(self):
        from apps.finance.services import (
            setup_enrollment_fee,
            record_installment_payment,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="one_time",
            total_amount=Decimal("20000.00"),
            created_by=self.admin,
        )
        insts = plan.installments.all()
        payment, updated = record_installment_payment(
            installment_id=insts[0].pk,
            amount_paid=Decimal("10000.00"),
            created_by=self.admin,
        )
        self.assertEqual(updated.status, "partial")
        self.assertEqual(
            updated.paid_amount,
            Decimal("10000.00"),
        )

    def test_overpayment_raises_error(self):
        from apps.finance.services import (
            setup_enrollment_fee,
            record_installment_payment,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="one_time",
            total_amount=Decimal("5000.00"),
            created_by=self.admin,
        )
        insts = plan.installments.all()
        with self.assertRaises(Exception):
            record_installment_payment(
                installment_id=insts[0].pk,
                amount_paid=Decimal("99999.00"),
                created_by=self.admin,
            )

    def test_fee_summary_totals_correct(self):
        from apps.finance.services import (
            setup_enrollment_fee,
            record_installment_payment,
            get_enrollment_fee_summary,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="monthly",
            total_amount=Decimal("30000.00"),
            number_of_installments=3,
            created_by=self.admin,
        )
        insts = plan.installments.all()
        record_installment_payment(
            installment_id=insts[0].pk,
            amount_paid=Decimal("10000.00"),
            created_by=self.admin,
        )
        summary = get_enrollment_fee_summary(
            self.enrollment.pk
        )
        self.assertEqual(
            summary["total_installments"], 3
        )
        self.assertEqual(
            summary["total_paid"],
            Decimal("10000.00"),
        )
        self.assertEqual(
            summary["total_outstanding"],
            Decimal("20000.00"),
        )
        self.assertEqual(
            summary["completion_percentage"], 33
        )

    def test_installment_pay_view_post(self):
        from apps.finance.services import (
            setup_enrollment_fee,
        )
        plan = setup_enrollment_fee(
            enrollment_id=self.enrollment.pk,
            fee_type="one_time",
            total_amount=Decimal("15000.00"),
            created_by=self.admin,
        )
        insts = plan.installments.all()
        accountant_group, _ = Group.objects.get_or_create(
            name="Accountant"
        )
        self.admin.groups.add(accountant_group)

        url = f"/panel/admin/finance/installments/{insts[0].pk}/pay/"
        response = self.client.post(
            url,
            data={
                "amount": "15000",
                "payment_method": "Cash",
                "payment_date": "2026-06-15",
                "reference_number": "TEST123",
            },
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("success"), True)
