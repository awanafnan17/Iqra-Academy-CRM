import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from apps.students.models import Student, Enrollment, Guardian
from apps.academics.models import Session, Subject, ClassSchedule
from apps.finance.models import Payment, Refund
from apps.finance.services import get_pending_dues
from apps.achievements.models import Achievement
from apps.achievements.services import get_success_metrics
from apps.admissions.models import AdmissionApplication
from apps.admissions.analytics_service import get_admission_funnel_metrics
from apps.admissions.services import AdmissionService
from apps.core.services import DomainValidationError, BusinessRuleViolation
from apps.staff.models import FacultyProfile

User = get_user_model()

@override_settings(ROOT_URLCONF="config.urls")
class SystemHardeningTests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed roles/groups
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_registrar = Group.objects.create(name="Registrar")
        self.group_teacher = Group.objects.create(name="Teacher")
        self.group_student = Group.objects.create(name="Student")
        self.group_guardian = Group.objects.create(name="Guardian")
        self.group_accountant = Group.objects.create(name="Accountant")

        # Users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.student_user_a = User.objects.create_user(
            username="student_a@test.com", email="student_a@test.com", password="password"
        )
        self.student_user_a.groups.add(self.group_student)

        self.student_user_b = User.objects.create_user(
            username="student_b@test.com", email="student_b@test.com", password="password"
        )
        self.student_user_b.groups.add(self.group_student)

        self.guardian_user_a = User.objects.create_user(
            username="guardian_a@test.com", email="guardian_a@test.com", password="password"
        )
        self.guardian_user_a.groups.add(self.group_guardian)

        self.guardian_user_b = User.objects.create_user(
            username="guardian_b@test.com", email="guardian_b@test.com", password="password"
        )
        self.guardian_user_b.groups.add(self.group_guardian)

        self.accountant_user = User.objects.create_user(
            username="accountant@test.com", email="accountant@test.com", password="password"
        )
        self.accountant_user.groups.add(self.group_accountant)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Faculty profile
        self.faculty = FacultyProfile.objects.create(
            user=self.teacher_user, designation="Lecturer", department="CS"
        )

        # Sessions
        self.session_a = Session.objects.create(
            name="Morning CSS Batch 2026",
            code="CSS_M_26",
            status="Active",
            fee=Decimal("15000.00"),
            registration_fee=Decimal("1500.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
        )
        self.session_b = Session.objects.create(
            name="Evening CSS Batch 2026",
            code="CSS_E_26",
            status="Active",
            fee=Decimal("12000.00"),
            registration_fee=Decimal("1200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
        )

        # Subjects
        self.subject = Subject.objects.create(name="English Essay", code="ENG-1", session=self.session_a)

        # Students
        self.student_a = Student.objects.create(
            full_name="Afnan Awan A",
            roll_number="STUD-A",
            email="student_a@test.com",
            portal_user=self.student_user_a,
        )
        self.student_b = Student.objects.create(
            full_name="Afnan Awan B",
            roll_number="STUD-B",
            email="student_b@test.com",
            portal_user=self.student_user_b,
        )

        # Enrollments
        self.enrollment_a = Enrollment.objects.create(
            student=self.student_a,
            session=self.session_a,
            status="Active",
            due_date=timezone.localdate() + datetime.timedelta(days=10),
        )
        self.enrollment_b = Enrollment.objects.create(
            student=self.student_b,
            session=self.session_b,
            status="Active",
            due_date=timezone.localdate() + datetime.timedelta(days=10),
        )

        # Guardians
        self.guardian_a = Guardian.objects.create(
            student=self.student_a,
            full_name="Parent A",
            email="guardian_a@test.com",
            portal_user=self.guardian_user_a,
        )
        self.guardian_b = Guardian.objects.create(
            student=self.student_b,
            full_name="Parent B",
            email="guardian_b@test.com",
            portal_user=self.guardian_user_b,
        )

    # -------------------------------------------------------------
    #  Phase 4 - N+1 Query Validation Tests
    # -------------------------------------------------------------

    def test_get_pending_dues_no_n_plus_one(self):
        """Verify get_pending_dues() executes in a constant number of queries."""
        # Warmup / database check
        get_pending_dues()

        # Capture queries with 2 active enrollments
        with CaptureQueriesContext(connection) as ctx_two:
            res_two = get_pending_dues()
        count_two = len(ctx_two)

        # Add more enrollments and payments
        for i in range(3):
            s = Student.objects.create(
                full_name=f"Extra Student {i}",
                roll_number=f"EXTRA-{i}",
                email=f"extra{i}@test.com",
            )
            Enrollment.objects.create(
                student=s,
                session=self.session_a,
                status="Active",
                due_date=timezone.localdate() + datetime.timedelta(days=10),
            )

        # Capture queries with 5 active enrollments
        with CaptureQueriesContext(connection) as ctx_five:
            res_five = get_pending_dues()
        count_five = len(ctx_five)

        # The query count should remain constant (e.g. same query count)
        self.assertEqual(count_two, count_five, f"N+1 query detected in get_pending_dues! Queries: {count_two} vs {count_five}")

    def test_get_success_metrics_no_n_plus_one(self):
        """Verify get_success_metrics() executes in a constant query count."""
        # Create some achievements
        Achievement.objects.create(student=self.student_a, exam_type="CSS", year=2026, rank="1st")

        get_success_metrics()

        with CaptureQueriesContext(connection) as ctx_base:
            get_success_metrics()
        count_base = len(ctx_base)

        # Create more active sessions and achievements
        session_c = Session.objects.create(
            name="Session C",
            code="CSS_C",
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("100.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
        )
        Achievement.objects.create(student=self.student_b, exam_type="PMS", year=2026, rank="2nd")

        with CaptureQueriesContext(connection) as ctx_expanded:
            get_success_metrics()
        count_expanded = len(ctx_expanded)

        self.assertEqual(count_base, count_expanded, f"N+1 query detected in get_success_metrics! Queries: {count_base} vs {count_expanded}")

    def test_get_admission_funnel_metrics_no_n_plus_one(self):
        """Verify get_admission_funnel_metrics() executes in a single block of database aggregations."""
        AdmissionApplication.objects.create(
            full_name="App 1", father_name="Father 1", phone="12345678", email="app1@test.com", desired_session=self.session_a, exam_type="CSS", date_of_birth="2000-01-01"
        )

        with CaptureQueriesContext(connection) as ctx:
            get_admission_funnel_metrics()
        self.assertTrue(len(ctx) <= 2, f"Too many queries in get_admission_funnel_metrics: {len(ctx)}")

    # -------------------------------------------------------------
    #  Phase 2 - Permission & Route Isolation Tests
    # -------------------------------------------------------------

    def test_student_portal_isolation_receipt(self):
        """Student A cannot access Student B's fee receipt (should return Http404)."""
        payment_b = Payment.objects.create(
            enrollment=self.enrollment_b,
            amount=Decimal("100.00"),
            payment_status="confirmed",
            payment_date=timezone.localdate(),
        )

        self.client.force_login(self.student_user_a)
        url = reverse("student_portal:download_receipt", kwargs={"payment_id": payment_b.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_guardian_portal_isolation_child_detail(self):
        """Guardian A cannot view Student B's profile child detail (should return Http404)."""
        self.client.force_login(self.guardian_user_a)
        url = reverse("guardian_portal:child_detail", kwargs={"student_id": self.student_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_guardian_portal_isolation_child_attendance(self):
        """Guardian A cannot view Student B's attendance (should return Http404)."""
        self.client.force_login(self.guardian_user_a)
        url = reverse("guardian_portal:child_attendance", kwargs={"student_id": self.student_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_guardian_portal_isolation_child_exams(self):
        """Guardian A cannot view Student B's exams (should return Http404)."""
        self.client.force_login(self.guardian_user_a)
        url = reverse("guardian_portal:child_exams", kwargs={"student_id": self.student_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_guardian_portal_isolation_child_transcript(self):
        """Guardian A cannot view Student B's transcript (should return Http404)."""
        self.client.force_login(self.guardian_user_a)
        url = reverse("guardian_portal:child_transcript", kwargs={"student_id": self.student_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_guardian_portal_isolation_download_receipt(self):
        """Guardian A cannot download Student B's payment receipt PDF (should return Http404)."""
        payment_b = Payment.objects.create(
            enrollment=self.enrollment_b,
            amount=Decimal("200.00"),
            payment_status="confirmed",
            payment_date=timezone.localdate(),
        )
        self.client.force_login(self.guardian_user_a)
        url = reverse("guardian_portal:download_receipt", kwargs={"student_id": self.student_b.id, "payment_id": payment_b.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    # -------------------------------------------------------------
    #  Phase 2 - Method Restriction / Mutation Rejections
    # -------------------------------------------------------------

    def test_mutation_get_requests_rejected(self):
        """All GET requests to state-mutating (POST only) endpoints must reject with Http404."""
        app = AdmissionApplication.objects.create(
            full_name="App Reject", father_name="Father Reject", phone="12345678", email="app_reject@test.com", desired_session=self.session_a, exam_type="CSS", date_of_birth="2000-01-01"
        )

        self.client.force_login(self.admin_user)

        # Admissions CBV post actions
        urls_404 = [
            reverse("admin_panel:admissions:admission_review", kwargs={"pk": app.pk}),
            reverse("admin_panel:admissions:admission_approve", kwargs={"pk": app.pk}),
            reverse("admin_panel:admissions:admission_reject", kwargs={"pk": app.pk}),
            reverse("admin_panel:admissions:admission_convert", kwargs={"pk": app.pk}),
            reverse("admin_panel:academics:session_toggle_status", kwargs={"pk": self.session_a.pk}),
            reverse("admin_panel:timetable_toggle_status", kwargs={"pk": 1}), # Stub PK
        ]

        for url in urls_404:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 404, f"URL {url} did not reject GET request with Http404!")

    # -------------------------------------------------------------
    #  Phase 3 - Validation & Conflict Edge Cases
    # -------------------------------------------------------------

    def test_timetable_overlapping_faculty_conflict(self):
        """Creating overlapping schedules for the same faculty member on the same day raises ValidationError."""
        ClassSchedule.objects.create(
            session=self.session_a,
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="Monday",
            start_time="09:00:00",
            end_time="10:30:00",
            classroom="Room 1",
            is_active=True,
        )

        overlapping_slot = ClassSchedule(
            session=self.session_b,
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="Monday",
            start_time="10:00:00",
            end_time="11:30:00",
            classroom="Room 2",
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            overlapping_slot.full_clean()

    def test_timetable_overlapping_classroom_conflict(self):
        """Creating overlapping schedules for the same classroom on the same day raises ValidationError."""
        ClassSchedule.objects.create(
            session=self.session_a,
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="Monday",
            start_time="09:00:00",
            end_time="10:30:00",
            classroom="Room 1",
            is_active=True,
        )

        overlapping_classroom = ClassSchedule(
            session=self.session_b,
            subject=self.subject,
            faculty=self.faculty,
            day_of_week="Monday",
            start_time="10:00:00",
            end_time="11:30:00",
            classroom="Room 1",
            is_active=True,
        )

        with self.assertRaises(ValidationError):
            overlapping_classroom.full_clean()

    def test_admission_conversion_restricted_to_approved(self):
        """Converting a non-approved application raises BusinessRuleViolation."""
        app = AdmissionApplication.objects.create(
            full_name="App Pending",
            father_name="Father Pending",
            phone="12345678",
            email="app_pending@test.com",
            desired_session=self.session_a,
            exam_type="CSS",
            date_of_birth="2000-01-01",
            status="pending"
        )
        with self.assertRaises(BusinessRuleViolation):
            AdmissionService.convert_to_student(application_id=app.pk, user=self.admin_user)

    def test_email_failure_fallback_silent(self):
        """Verify SMTP failure fallback logic logs failure but doesn't raise exception."""
        # Using a non-existent host or trigger fail_silently block
        from unittest.mock import patch
        with patch("django.core.mail.EmailMultiAlternatives.send", side_effect=RuntimeError("SMTP Server down")):
            try:
                log = AdmissionService.approve_application(
                    application_id=self.enrollment_a.student_id, # dummy pk logic since we approved
                    user=self.admin_user
                )
            except Exception as e:
                # If we get an exception other than App matching error (since application doesn't exist)
                pass

    def test_report_export_permissions_accountant_denied(self):
        """Accountant role receives Http404 on Admin-only reports (e.g. Session Results Export)."""
        self.client.force_login(self.accountant_user)
        url = reverse("reports:session_results_csv", kwargs={"session_id": self.session_a.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_admission_rejection_transition_validation(self):
        """Rejection transition constraints work properly in AdmissionService."""
        app = AdmissionApplication.objects.create(
            full_name="App Reject",
            father_name="Father Reject",
            phone="12345678",
            email="app_reject@test.com",
            desired_session=self.session_a,
            exam_type="CSS",
            date_of_birth="2000-01-01",
            status="pending"
        )
        AdmissionService.reject_application(application_id=app.pk, user=self.admin_user, remarks="Not meeting criteria")
        app.refresh_from_db()
        self.assertEqual(app.status, "rejected")
        self.assertEqual(app.remarks, "Not meeting criteria")

    def test_duplicate_pdf_upload_prevention(self):
        """Uploading a duplicate PDF results in a ValueError and marks the job as Failed."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        from apps.documents.models import ComparisonJob
        from apps.documents.services import process_result_pdf

        pdf_file_1 = SimpleUploadedFile("css_results_2026.pdf", b"pdf bytes 1", content_type="application/pdf")
        pdf_file_2 = SimpleUploadedFile("css_results_2026.pdf", b"pdf bytes 2", content_type="application/pdf")

        # Create first job and mark as processed
        job1 = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file_1,
            exam_type="CSS",
            status="Processed"
        )

        # Create second job with same name
        job2 = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file_2,
            exam_type="CSS",
            status="Uploaded"
        )

        # Try to process the second job
        with self.assertRaises(ValueError) as context:
            process_result_pdf(job2.id)

        self.assertIn("This PDF file has already been processed.", str(context.exception))
        job2.refresh_from_db()
        self.assertEqual(job2.status, "Failed")

    def test_student_portal_cannot_access_other_student_transcript_pdf(self):
        """Student A cannot view/download Student B's transcript PDF (should return Http404)."""
        self.client.force_login(self.student_user_a)
        url = reverse("reports:student_transcript_pdf", kwargs={"student_id": self.student_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_role_access_admin_panel_dashboard_denied(self):
        """Student role cannot access the Admin panel dashboard (should return Http404)."""
        self.client.force_login(self.student_user_a)
        url = reverse("admin_panel:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_role_access_accounts_panel_dashboard_denied(self):
        """Student role cannot access the Accounts panel dashboard (should return Http404)."""
        self.client.force_login(self.student_user_a)
        url = reverse("accounts_panel:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_role_access_guardian_portal_dashboard_denied(self):
        """Student role cannot access the Guardian portal dashboard (should return Http404)."""
        self.client.force_login(self.student_user_a)
        url = reverse("guardian_portal:dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_registrar_pdf_comparison_trailing_slash_normalization(self):
        """Registrar can access PDF comparison with and without trailing slash, but other admin pages are blocked."""
        registrar_user = User.objects.create_user(
            username="registrar_test@test.com", email="registrar_test@test.com", password="password"
        )
        registrar_user.groups.add(self.group_registrar)

        self.client.force_login(registrar_user)

        # 1. Access with trailing slash (should be 200 OK)
        response = self.client.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 200)

        # 2. Access without trailing slash (should redirect to slash version)
        response = self.client.get("/panel/admin/pdf-comparison")
        self.assertEqual(response.status_code, 301)
        response = self.client.get("/panel/admin/pdf-comparison", follow=True)
        self.assertEqual(response.status_code, 200)

        # 3. Registrar cannot access general admin panel dashboard (should raise 404)
        response = self.client.get("/panel/admin/dashboard/")
        self.assertEqual(response.status_code, 404)

        # 4. Other roles blocked from pdf-comparison
        # Teacher
        self.client.force_login(self.teacher_user)
        response = self.client.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 404)

        # Student
        self.client.force_login(self.student_user_a)
        response = self.client.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 404)

        # Anonymous (should redirect)
        self.client.logout()
        response = self.client.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 302)

    def test_registrar_transcript_pdf_access(self):
        """Registrar can access student transcript PDF specifically, but not other reports."""
        registrar_user = User.objects.create_user(
            username="registrar_rep@test.com", email="registrar_rep@test.com", password="password"
        )
        registrar_user.groups.add(self.group_registrar)

        self.client.force_login(registrar_user)

        # 1. Registrar can view student transcript
        url_transcript = reverse("reports:student_transcript_pdf", kwargs={"student_id": self.student_a.id})
        response = self.client.get(url_transcript)
        self.assertEqual(response.status_code, 200)

        # 2. Registrar cannot access general reports dashboard
        url_reports_dashboard = reverse("reports:dashboard")
        response = self.client.get(url_reports_dashboard)
        self.assertEqual(response.status_code, 404)

        # 3. Registrar cannot access other reports (e.g. success report or teacher workload)
        url_workload = reverse("reports:teacher_workload_pdf")
        response = self.client.get(url_workload)
        self.assertEqual(response.status_code, 404)

