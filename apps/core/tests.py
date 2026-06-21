"""
Unit tests for the RBAC and URL Routing layer.

Tests decorators, CBV mixins, custom middlewares, and post-login redirection logic.
"""

import os
import datetime
import time
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse
from django.test import TestCase, override_settings
from django.utils import timezone
from django.urls import path
from django.views import View

from apps.accounts.utils import get_role_redirect_url
from apps.core.decorators import role_required, post_required, throttle
from apps.core.mixins import RoleRequiredMixin, PostRequiredMixin
from apps.dashboard.services import (
    get_admin_dashboard_metrics,
    get_principal_dashboard_metrics,
    get_teacher_dashboard_metrics,
    get_accountant_dashboard_metrics,
    get_registrar_dashboard_metrics,
    get_student_dashboard_metrics,
    get_guardian_dashboard_metrics,
)

User = get_user_model()


# -------------------------------------------------------------------
#  Test View definitions
# -------------------------------------------------------------------

@role_required("Admin")
def test_admin_only(request):
    return HttpResponse("admin_ok")


@role_required("Teacher")
@post_required
def test_teacher_post(request):
    return HttpResponse("teacher_post_ok")


@throttle(max_calls=2, period_seconds=10)
def test_throttled(request):
    return HttpResponse("throttled_ok")


class TestCBV(RoleRequiredMixin, View):
    required_roles = ["Accountant"]

    def get(self, request, *args, **kwargs):
        return HttpResponse("cbv_get_ok")


class TestPostCBV(RoleRequiredMixin, PostRequiredMixin, View):
    required_roles = ["Accountant"]

    def post(self, request, *args, **kwargs):
        return HttpResponse("cbv_post_ok")


# Test URL patterns for local routing tests
urlpatterns = [
    path("test/admin-only/", test_admin_only, name="test_admin_only"),
    path("test/teacher-post/", test_teacher_post, name="test_teacher_post"),
    path("test/throttled/", test_throttled, name="test_throttled"),
    path("test/cbv/", TestCBV.as_view(), name="test_cbv"),
    path("test/cbv-post/", TestPostCBV.as_view(), name="test_cbv_post"),
]


@override_settings(ROOT_URLCONF="apps.core.tests")
class RBACRoutingTests(TestCase):
    """Integrative and unit tests for the RBAC layer."""

    def setUp(self):
        super().setUp()
        cache.clear()

        # Create basic Groups
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_accountant = Group.objects.create(name="Accountant")
        self.group_registrar = Group.objects.create(name="Registrar")
        self.group_student = Group.objects.create(name="Student")
        self.group_guardian = Group.objects.create(name="Guardian")

        # Create standard test users
        self.admin_user = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="password123",
        )
        self.admin_user.groups.add(self.group_admin)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            password="password123",
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.superuser = User.objects.create_superuser(
            username="superuser@test.com",
            email="superuser@test.com",
            password="password123",
        )

        self.regular_user = User.objects.create_user(
            username="user@test.com",
            email="user@test.com",
            password="password123",
        )

    # 1. Test role_required decorator
    def test_role_required_unauthenticated(self):
        """Unauthenticated request is redirected to the login page."""
        response = self.client.get("/test/admin-only/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_role_required_authorized(self):
        """Authenticated user belonging to required group gets 200."""
        self.client.force_login(self.admin_user)
        response = self.client.get("/test/admin-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"admin_ok")

    def test_role_required_unauthorized(self):
        """Authenticated user NOT in the group gets a 404 to hide route existence."""
        self.client.force_login(self.teacher_user)
        response = self.client.get("/test/admin-only/")
        self.assertEqual(response.status_code, 404)

    def test_role_required_superuser_bypass(self):
        """Superuser automatically bypasses all group checks."""
        self.client.force_login(self.superuser)
        response = self.client.get("/test/admin-only/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"admin_ok")

    # 2. Test post_required decorator
    def test_post_required_fails_on_get(self):
        """GET requests to post_required endpoints fail with 404."""
        self.client.force_login(self.teacher_user)
        response = self.client.get("/test/teacher-post/")
        self.assertEqual(response.status_code, 404)

    def test_post_required_succeeds_on_post(self):
        """POST requests to post_required endpoints succeed."""
        self.client.force_login(self.teacher_user)
        response = self.client.post("/test/teacher-post/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"teacher_post_ok")

    # 3. Test CBV Mixins
    def test_cbv_mixin_authorized(self):
        """Authenticated Accountant user succeeds on Accountant-restricted CBV."""
        accountant_user = User.objects.create_user(
            username="accountant@test.com",
            email="accountant@test.com",
            password="password123",
        )
        accountant_user.groups.add(self.group_accountant)
        self.client.force_login(accountant_user)
        response = self.client.get("/test/cbv/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"cbv_get_ok")

    def test_cbv_mixin_unauthorized(self):
        """Teacher user visiting Accountant-restricted CBV gets 404."""
        self.client.force_login(self.teacher_user)
        response = self.client.get("/test/cbv/")
        self.assertEqual(response.status_code, 404)

    def test_cbv_post_mixin_fails_on_get(self):
        """GET request to CBV with PostRequiredMixin raises 404."""
        accountant_user = User.objects.create_user(
            username="accountant2@test.com",
            email="accountant2@test.com",
            password="password123",
        )
        accountant_user.groups.add(self.group_accountant)
        self.client.force_login(accountant_user)
        response = self.client.get("/test/cbv-post/")
        self.assertEqual(response.status_code, 404)

    def test_cbv_post_mixin_succeeds_on_post(self):
        """POST request to CBV with PostRequiredMixin succeeds."""
        accountant_user = User.objects.create_user(
            username="accountant3@test.com",
            email="accountant3@test.com",
            password="password123",
        )
        accountant_user.groups.add(self.group_accountant)
        self.client.force_login(accountant_user)
        response = self.client.post("/test/cbv-post/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"cbv_post_ok")

    # 4. Test rate limiting throttle
    def test_throttle_rate_limiting(self):
        """Accessing throttled view within limits is allowed, exceeding throws 429."""
        response = self.client.get("/test/throttled/")
        self.assertEqual(response.status_code, 200)

        response = self.client.get("/test/throttled/")
        self.assertEqual(response.status_code, 200)

        # Third attempt in rapid succession exceeds max_calls=2
        response = self.client.get("/test/throttled/")
        self.assertEqual(response.status_code, 429)
        self.assertIn("Retry-After", response)

    # 5. Test redirection priority
    def test_get_role_redirect_url_priority(self):
        """Role redirection priority is Admin > Principal > Accountant > Registrar > Teacher > Student > Guardian."""
        # 5.1 Admin priority
        admin_multi = User.objects.create_user(
            username="admin_multi@test.com",
            email="admin_multi@test.com",
        )
        admin_multi.groups.add(self.group_admin)
        admin_multi.groups.add(self.group_principal)
        admin_multi.groups.add(self.group_teacher)
        self.assertEqual(get_role_redirect_url(admin_multi), "/panel/admin/dashboard/")

        # 5.2 Principal priority over others (except Admin)
        principal_multi = User.objects.create_user(
            username="principal_multi@test.com",
            email="principal_multi@test.com",
        )
        principal_multi.groups.add(self.group_principal)
        principal_multi.groups.add(self.group_teacher)
        self.assertEqual(get_role_redirect_url(principal_multi), "/panel/principal/dashboard/")

        # 5.3 Accountant priority
        acc_multi = User.objects.create_user(
            username="acc_multi@test.com",
            email="acc_multi@test.com",
        )
        acc_multi.groups.add(self.group_accountant)
        acc_multi.groups.add(self.group_registrar)
        acc_multi.groups.add(self.group_teacher)
        self.assertEqual(get_role_redirect_url(acc_multi), "/panel/accounts/dashboard/")

        # 5.4 Registrar priority
        reg_multi = User.objects.create_user(
            username="reg_multi@test.com",
            email="reg_multi@test.com",
        )
        reg_multi.groups.add(self.group_registrar)
        reg_multi.groups.add(self.group_teacher)
        self.assertEqual(get_role_redirect_url(reg_multi), "/panel/registrar/dashboard/")

        # 5.5 Teacher priority
        teach_multi = User.objects.create_user(
            username="teach_multi@test.com",
            email="teach_multi@test.com",
        )
        teach_multi.groups.add(self.group_teacher)
        teach_multi.groups.add(self.group_student)
        self.assertEqual(get_role_redirect_url(teach_multi), "/panel/teacher/dashboard/")

        # 5.6 Student priority
        stud_multi = User.objects.create_user(
            username="stud_multi@test.com",
            email="stud_multi@test.com",
        )
        stud_multi.groups.add(self.group_student)
        stud_multi.groups.add(self.group_guardian)
        self.assertEqual(get_role_redirect_url(stud_multi), "/portal/student/dashboard/")

        # 5.7 Guardian fallback
        guard_only = User.objects.create_user(
            username="guard_only@test.com",
            email="guard_only@test.com",
        )
        guard_only.groups.add(self.group_guardian)
        self.assertEqual(get_role_redirect_url(guard_only), "/portal/guardian/dashboard/")

        # 5.8 No groups -> login
        self.assertEqual(get_role_redirect_url(self.regular_user), "/accounts/login/")

    # 6. Test PanelAccessMiddleware on real URL paths
    @override_settings(ROOT_URLCONF="config.urls")
    def test_panel_access_middleware_enforcement(self):
        """PanelAccessMiddleware restricts panel prefixes to authorized roles only."""
        # Unauthenticated: redirects to login
        response = self.client.get("/panel/admin/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

        # Teacher visiting admin panel gets 404
        self.client.force_login(self.teacher_user)
        response = self.client.get("/panel/admin/dashboard/")
        self.assertEqual(response.status_code, 404)

        # Teacher visiting teacher panel gets 200 (ok)
        response = self.client.get("/panel/teacher/dashboard/")
        self.assertEqual(response.status_code, 200)

        # Admin visiting teacher panel gets 404 (segregation of panels)
        self.client.force_login(self.admin_user)
        response = self.client.get("/panel/teacher/dashboard/")
        self.assertEqual(response.status_code, 404)

        # Admin visiting admin panel gets 200
        response = self.client.get("/panel/admin/dashboard/")
        self.assertEqual(response.status_code, 200)


@override_settings(ROOT_URLCONF="config.urls", SESSION_ENGINE="django.contrib.sessions.backends.db")
class SessionTimeoutTests(TestCase):
    """Tests for SessionTimeoutMiddleware activity tracking and timeout triggers."""

    def setUp(self):
        super().setUp()
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_student = Group.objects.create(name="Student")

        self.teacher_user = User.objects.create_user(
            username="t@test.com",
            email="t@test.com",
            password="pass",
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.student_user = User.objects.create_user(
            username="s@test.com",
            email="s@test.com",
            password="pass",
        )
        self.student_user.groups.add(self.group_student)

    def test_session_activity_tracked(self):
        """Active session updates _last_activity timestamp."""
        self.client.force_login(self.teacher_user)
        response = self.client.get("/panel/teacher/dashboard/")
        self.assertEqual(response.status_code, 200)

        session = self.client.session
        self.assertIn("_last_activity", session)
        first_time = session["_last_activity"]

        # Make another request, should update timestamp
        time.sleep(0.1)
        response = self.client.get("/panel/teacher/dashboard/")
        second_time = self.client.session["_last_activity"]
        self.assertGreater(second_time, first_time)

    def test_session_timeout_trigger(self):
        """Session is logged out when idle threshold is exceeded."""
        self.client.force_login(self.teacher_user)
        # Force a request to initialize _last_activity
        self.client.get("/panel/teacher/dashboard/")

        # Manually alter session's last activity to 31 minutes ago
        session = self.client.session
        session["_last_activity"] = time.time() - (31 * 60)
        session.save()

        # Next request should trigger timeout redirect and clear login
        response = self.client.get("/panel/teacher/dashboard/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/?timeout=1", response.url)

        # Verify user is logged out in the session
        self.assertNotIn("_auth_user_id", self.client.session)


class DashboardServicesTests(TestCase):
    """Tests for the dashboard service layer functions."""

    def setUp(self):
        super().setUp()
        # Create user roles
        self.group_admin = Group.objects.create(name="Admin")
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_student = Group.objects.create(name="Student")
        self.group_guardian = Group.objects.create(name="Guardian")

        # Create session
        from apps.academics.models import Session, Subject, TeacherAssignment
        self.session = Session.objects.create(
            name="Session A",
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate() - datetime.timedelta(days=10),
            end_date=timezone.localdate() + datetime.timedelta(days=10),
        )

        self.subject = Subject.objects.create(
            name="Math",
            code="M101",
        )

        # Create users
        self.teacher_user = User.objects.create_user(
            username="t_serv@test.com",
            email="t_serv@test.com",
            password="pass",
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Teacher assignment
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            subject=self.subject,
            is_active=True,
        )

        # Student user
        self.student_user = User.objects.create_user(
            username="s_serv@test.com",
            email="s_serv@test.com",
            password="pass",
        )
        self.student_user.groups.add(self.group_student)

        from apps.students.models import Student, Enrollment
        self.student = Student.objects.create(
            full_name="Ahmed Hassan",
            email="s_serv@test.com",
            portal_user=self.student_user,
            status="Active",
        )

        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            discount=Decimal("50.00"),
        )

        # Guardian user
        self.guardian_user = User.objects.create_user(
            username="g_serv@test.com",
            email="g_serv@test.com",
            password="pass",
        )
        self.guardian_user.groups.add(self.group_guardian)

        from apps.students.models import Guardian
        self.guardian = Guardian.objects.create(
            student=self.student,
            full_name="Jane Doe",
            email="g_serv@test.com",
            portal_user=self.guardian_user,
        )

    def test_get_admin_dashboard_metrics(self):
        """Admin metrics should return correct financial and active counters."""
        from apps.finance.models import Payment, Expense, Refund
        # Create a confirmed payment
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("1200.00"),
            payment_status="confirmed",
            payment_date=timezone.localdate(),
        )
        # Create a refund
        Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("200.00"),
            payment_status="refunded",
            payment_date=timezone.localdate(),
        )
        # Create processed refund record
        Refund.objects.create(
            payment=Payment.objects.filter(payment_status="refunded").first(),
            amount=Decimal("200.00"),
            status="processed",
            refund_date=timezone.localdate(),
        )
        # Create approved expense
        from apps.finance.models import ExpenseCategory
        cat = ExpenseCategory.objects.create(name="Rent")
        Expense.objects.create(
            category=cat,
            amount=Decimal("300.00"),
            status="approved",
            expense_date=timezone.localdate(),
        )

        metrics = get_admin_dashboard_metrics()
        self.assertEqual(metrics["confirmed_revenue"], Decimal("1400.00"))  # Includes refunded payment
        self.assertEqual(metrics["approved_expenses"], Decimal("300.00"))
        self.assertEqual(metrics["processed_refunds"], Decimal("200.00"))
        self.assertEqual(metrics["net_cash_flow"], Decimal("900.00"))  # 1400 - 200 - 300
        self.assertEqual(metrics["active_students"], 1)

    def test_get_principal_dashboard_metrics(self):
        """Principal metrics should return enrollment and alert counters."""
        metrics = get_principal_dashboard_metrics()
        self.assertEqual(metrics["active_students"], 1)
        self.assertEqual(metrics["active_sessions"], 1)
        self.assertEqual(metrics["pending_exams_count"], 0)

    def test_get_teacher_dashboard_metrics(self):
        """Teacher metrics should return correct assignment counters."""
        metrics = get_teacher_dashboard_metrics(self.teacher_user)
        self.assertEqual(metrics["assigned_sessions_count"], 1)
        self.assertEqual(metrics["assigned_students_count"], 1)

    def test_get_accountant_dashboard_metrics(self):
        """Accountant metrics should fetch outstanding balance and financial aggregates."""
        metrics = get_accountant_dashboard_metrics()
        self.assertIn("confirmed_revenue", metrics)
        self.assertIn("unpaid_installments", metrics)

    def test_get_registrar_dashboard_metrics(self):
        """Registrar metrics should return active students and registration status counts."""
        metrics = get_registrar_dashboard_metrics()
        self.assertEqual(metrics["active_students"], 1)

    def test_get_student_dashboard_metrics(self):
        """Student dashboard returns current session, outstanding balance, and unread count."""
        metrics = get_student_dashboard_metrics(self.student_user)
        self.assertEqual(metrics["student_name"], "Ahmed Hassan")
        self.assertEqual(metrics["session_name"], "Session A")
        self.assertEqual(metrics["outstanding_balance"], Decimal("1150.00"))  # 1000 + 200 - 50

    def test_get_guardian_dashboard_metrics(self):
        """Guardian dashboard returns batched outstanding balance for linked children."""
        metrics = get_guardian_dashboard_metrics(self.guardian_user)
        self.assertEqual(metrics["children_count"], 1)
        self.assertEqual(metrics["total_outstanding_balance"], Decimal("1150.00"))


class SecurityHardeningMiddlewareTests(TestCase):
    """Tests for SecurityHardeningMiddleware header injection."""

    def test_security_headers_injected(self):
        """Ensure security headers are attached to all response objects."""
        response = self.client.get("/accounts/login/")
        self.assertIn("Content-Security-Policy", response)
        self.assertIn("Referrer-Policy", response)
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")


class BackupDbCommandTests(TestCase):
    """Tests for backup_db management command."""

    import unittest
    from django.conf import settings
    @unittest.skipIf(
        settings.DATABASES['default'].get('TEST', {}).get('ENGINE', '') == 'django.db.backends.sqlite3',
        "Skipped: MySQL-specific test, running SQLite for tests"
    )
    def test_backup_db_execution(self):
        """Ensure database backup command runs and generates backup file."""
        import os
        import glob
        from unittest.mock import patch
        from django.conf import settings
        from django.core.management import call_command

        backup_dir = os.path.join(settings.BASE_DIR, "backups")

        # Keep track of existing files to avoid deleting real backups
        existing_backups = set(glob.glob(os.path.join(backup_dir, "*")))

        # Define a mock run function to write to target stdout file object to simulate database dump output
        def mock_run(*args, **kwargs):
            if "stdout" in kwargs and hasattr(kwargs["stdout"], "write"):
                kwargs["stdout"].write("MOCK DATABASE BACKUP CONTENT\n")
            return None

        original_exists = os.path.exists
        def mock_exists(path):
            if "memory" in str(path) or path == settings.DATABASES["default"]["NAME"]:
                return True
            return original_exists(path)

        def mock_copy2(src, dst):
            with open(dst, "w", encoding="utf-8") as f:
                f.write("MOCK DATABASE BACKUP CONTENT\n")

        # Call the command while mocking subprocess.run, shutil.copy2, and os.path.exists
        with patch("subprocess.run", side_effect=mock_run), \
             patch("shutil.copy2", side_effect=mock_copy2), \
             patch("os.path.exists", side_effect=mock_exists):
            call_command("backup_db")

        # Verify a new file is created
        current_backups = set(glob.glob(os.path.join(backup_dir, "*")))
        new_backups = current_backups - existing_backups

        self.assertTrue(len(new_backups) >= 1, "No backup file created by backup_db command.")

        # Clean up created files
        for filepath in new_backups:
            if os.path.exists(filepath):
                os.remove(filepath)



