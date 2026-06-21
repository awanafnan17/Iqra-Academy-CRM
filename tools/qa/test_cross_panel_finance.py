import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.test import TestCase, override_settings
from django.contrib.auth.models import Group
from django.urls import reverse
from apps.accounts.models import CustomUser
from apps.students.models import Student, Enrollment
from apps.finance.models import Payment, Expense, ExpenseCategory, Refund, InstallmentPlan, Installment
from apps.academics.models import Session

TEST_PASSWORD = "FinanceTest!2026"

@override_settings(
    SECURE_SSL_REDIRECT=False,
    SECURE_HSTS_SECONDS=0,
    SESSION_COOKIE_SECURE=False,
    CSRF_COOKIE_SECURE=False,
)
class CrossPanelFinanceTests(TestCase):
    """Regression tests for shared finance templates namespace resolution (DEF-TEMPLATE-01)."""

    @classmethod
    def setUpTestData(cls):
        # Create Admin
        cls.admin_group, _ = Group.objects.get_or_create(name="Admin")
        cls.admin_user = CustomUser.objects.create_user(
            email="admin@iqra.test",
            username="admin_finance",
            password=TEST_PASSWORD,
            status="Active",
            is_staff=True,
            is_superuser=True,
        )
        cls.admin_user.groups.add(cls.admin_group)

        # Create Accountant
        cls.accountant_group, _ = Group.objects.get_or_create(name="Accountant")
        cls.accountant_user = CustomUser.objects.create_user(
            email="accountant@iqra.test",
            username="accountant_finance",
            password=TEST_PASSWORD,
            status="Active",
        )
        cls.accountant_user.groups.add(cls.accountant_group)

        # Base Academic Session
        cls.session = Session.objects.create(
            name="Finance Session 2026",
            code="FIN2026",
            roll_prefix="FN",
            session_type="monthly",
            session_category="Academic",
            academic_year="2026",
            start_date="2026-01-01",
            end_date="2026-12-31",
            fee="5000.00",
            status="Active",
        )

        # Student + Enrollment
        cls.student = Student.objects.create(
            full_name="Finance Student QA",
            email="finance_std@iqra.test",
            status="Active",
        )
        cls.enrollment = Enrollment.objects.create(
            student=cls.student,
            session=cls.session,
            registration_date="2026-01-05",
            fee="5000.00",
            status="Active",
        )

        # Core finance objects
        cls.payment = Payment.objects.create(
            enrollment=cls.enrollment,
            amount="5000.00",
            payment_date="2026-01-10",
            payment_method="Cash",
            payment_status="confirmed",
            receipt_number="REC-FIN-2026-01",
        )

        cls.category = ExpenseCategory.objects.create(
            name="Supplies",
            description="Office and class supplies",
        )
        cls.expense = Expense.objects.create(
            category=cls.category,
            amount="2500.00",
            expense_date="2026-01-15",
            description="Paper and pens",
            recorded_by=cls.admin_user,
            status="pending",
        )

        cls.refund = Refund.objects.create(
            payment=cls.payment,
            amount="1000.00",
            reason="Overpayment correction",
            refund_date="2026-01-12",
            status="pending",
        )

        cls.plan = InstallmentPlan.objects.create(
            enrollment=cls.enrollment,
            total_amount="15000.00",
            number_of_installments=3,
            is_active=True,
        )
        cls.installment = Installment.objects.create(
            plan=cls.plan,
            installment_number=1,
            amount="5000.00",
            due_date="2026-02-10",
            status="pending",
        )

    def test_payment_templates_resolution(self):
        """Payments pages resolve namespaces correctly for both Admin and Accountant."""
        for role, user, prefix in [("Admin", self.admin_user, "/panel/admin/finance/payments/"),
                                    ("Accountant", self.accountant_user, "/panel/accounts/payments/")]:
            self.client.login(username=user.email, password=TEST_PASSWORD)

            # List
            response = self.client.get(prefix)
            self.assertEqual(response.status_code, 200, msg=f"{role} payments list failed")
            # Verify create link matches prefix
            self.assertContains(response, f'{prefix}create/', msg_prefix=f"{role} create link wrong")
            # Verify detail link matches prefix
            self.assertContains(response, f'{prefix}{self.payment.pk}/', msg_prefix=f"{role} detail link wrong")

            # Detail
            response = self.client.get(f"{prefix}{self.payment.pk}/")
            self.assertEqual(response.status_code, 200, msg=f"{role} payments detail failed")
            # Verify back link
            self.assertContains(response, prefix, msg_prefix=f"{role} back link wrong")

    def test_expense_templates_resolution(self):
        """Expenses pages resolve namespaces correctly for both Admin and Accountant."""
        for role, user, prefix in [("Admin", self.admin_user, "/panel/admin/finance/expenses/"),
                                    ("Accountant", self.accountant_user, "/panel/accounts/expenses/")]:
            self.client.login(username=user.email, password=TEST_PASSWORD)

            # List
            response = self.client.get(prefix)
            self.assertEqual(response.status_code, 200, msg=f"{role} expenses list failed")
            self.assertContains(response, f'{prefix}create/', msg_prefix=f"{role} create link wrong")
            self.assertContains(response, f'{prefix}{self.expense.pk}/', msg_prefix=f"{role} detail link wrong")

            # Detail
            response = self.client.get(f"{prefix}{self.expense.pk}/")
            self.assertEqual(response.status_code, 200, msg=f"{role} expenses detail failed")
            self.assertContains(response, prefix, msg_prefix=f"{role} back link wrong")

    def test_refund_templates_resolution(self):
        """Refund pages resolve namespaces correctly for both Admin and Accountant."""
        for role, user, prefix in [("Admin", self.admin_user, "/panel/admin/finance/refunds/"),
                                    ("Accountant", self.accountant_user, "/panel/accounts/refunds/")]:
            self.client.login(username=user.email, password=TEST_PASSWORD)

            # List
            response = self.client.get(prefix)
            self.assertEqual(response.status_code, 200, msg=f"{role} refunds list failed")
            self.assertContains(response, f'{prefix}create/', msg_prefix=f"{role} create link wrong")

    def test_installment_templates_resolution(self):
        """Installment plan pages resolve namespaces correctly for both Admin and Accountant."""
        for role, user, prefix in [("Admin", self.admin_user, "/panel/admin/finance/installments/"),
                                    ("Accountant", self.accountant_user, "/panel/accounts/installments/")]:
            self.client.login(username=user.email, password=TEST_PASSWORD)

            # List
            response = self.client.get(prefix)
            self.assertEqual(response.status_code, 200, msg=f"{role} installment plan list failed")
            self.assertContains(response, f'{prefix}create/', msg_prefix=f"{role} create link wrong")
            self.assertContains(response, f'{prefix}{self.plan.pk}/', msg_prefix=f"{role} detail link wrong")

            # Detail
            response = self.client.get(f"{prefix}{self.plan.pk}/")
            self.assertEqual(response.status_code, 200, msg=f"{role} installment plan detail failed")
            self.assertContains(response, prefix, msg_prefix=f"{role} back link wrong")
            self.assertContains(response, f'{prefix}{self.plan.pk}/restructure/', msg_prefix=f"{role} restructure link wrong")
            if role == "Admin":
                self.assertContains(response, f'/panel/admin/finance/installments/pay/{self.installment.id}/', msg_prefix="Admin pay link wrong")
            else:
                self.assertContains(response, f'/panel/accounts/installments/{self.installment.id}/pay/', msg_prefix="Accountant pay link wrong")
