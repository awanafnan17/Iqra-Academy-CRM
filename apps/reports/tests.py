import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session, Subject, TeacherAssignment
from apps.exams.models import Exam, ExamResult
from apps.students.models import Student, Enrollment, Guardian
from apps.staff.models import FacultyProfile
from apps.finance.models import Payment

User = get_user_model()

class ReportingEngineTests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed Group roles
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_principal, _ = Group.objects.get_or_create(name="Principal")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")
        self.group_accountant, _ = Group.objects.get_or_create(name="Accountant")
        self.group_student, _ = Group.objects.get_or_create(name="Student")
        self.group_guardian, _ = Group.objects.get_or_create(name="Guardian")

        # Seed users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(
            username="principal@test.com", email="principal@test.com", password="password"
        )
        self.principal_user.groups.add(self.group_principal)

        self.accountant_user = User.objects.create_user(
            username="accountant@test.com", email="accountant@test.com", password="password"
        )
        self.accountant_user.groups.add(self.group_accountant)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.student_user = User.objects.create_user(
            username="student_user@test.com", email="student_user@test.com", password="password"
        )
        self.student_user.groups.add(self.group_student)

        self.other_student_user = User.objects.create_user(
            username="other_student_user@test.com", email="other_student_user@test.com", password="password"
        )
        self.other_student_user.groups.add(self.group_student)

        self.guardian_user = User.objects.create_user(
            username="guardian@test.com", email="guardian@test.com", password="password"
        )
        self.guardian_user.groups.add(self.group_guardian)

        # Create models
        self.session = Session.objects.create(
            name="Session Alpha",
            status="Active",
            fee=Decimal("1500.00"),
            registration_fee=Decimal("300.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=60),
            session_category="CSS",
            academic_year="2026",
            batch_number=1,
            max_capacity=50,
            is_admission_open=True
        )

        self.student = Student.objects.create(
            full_name="Ahmed Hassan",
            roll_number="CSS-001",
            portal_user=self.student_user,
            status="Active"
        )

        self.other_student = Student.objects.create(
            full_name="Jane Doe",
            roll_number="CSS-002",
            portal_user=self.other_student_user,
            status="Active"
        )

        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
            registration_date=timezone.localdate()
        )

        self.other_enrollment = Enrollment.objects.create(
            student=self.other_student,
            session=self.session,
            status="Active",
            registration_date=timezone.localdate()
        )

        # Create Guardian link
        self.guardian = Guardian.objects.create(
            student=self.student,
            full_name="Guardian Joe",
            portal_user=self.guardian_user,
            phone="123456"
        )

        # Create Subject & Exams
        self.subject = Subject.objects.create(name="English Essay", code="ENG-101")
        self.exam = Exam.objects.create(
            session=self.session,
            subject=self.subject,
            name="Midterm Exam",
            exam_date=timezone.localdate(),
            total_marks=100,
            passing_marks=40,
            created_by=self.admin_user,
            status="Published"
        )

        self.exam_result = ExamResult.objects.create(
            exam=self.exam,
            student=self.student,
            marks_obtained=Decimal("75.00"),
            percentage=Decimal("75.00"),
            grade="B",
            rank=1,
            is_absent=False
        )

        # Create faculty
        self.faculty_user = User.objects.create_user(
            username="faculty_member@test.com", email="faculty_member@test.com", password="password",
            first_name="Prof", last_name="Teacher"
        )
        self.faculty_user.groups.add(self.group_teacher)
        self.faculty_profile = FacultyProfile.objects.create(
            user=self.faculty_user,
            designation="Lecturer",
            department="English Language",
            is_active=True
        )

        # Create active teaching assignment
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.faculty_user,
            session=self.session,
            subject=self.subject,
            is_active=True
        )

        # Create payment showing outstanding due
        self.payment = Payment.objects.create(
            enrollment=self.enrollment,
            amount=Decimal("1500.00"),
            payment_date=timezone.localdate(),
            payment_status="confirmed"
        )

    def test_admin_and_principal_can_access_reports_dashboard(self):
        url = reverse("reports:dashboard")

        # Admin
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Principal
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Accountant (should be blocked via middleware or mixin)
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_accountant_can_access_accountant_dashboard(self):
        url = reverse("accounts_panel:reports_dashboard")
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Admin cannot access
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_pending_dues_csv_and_pdf_access_rules(self):
        url_csv = reverse("reports:pending_dues_csv")
        url_pdf = reverse("reports:pending_dues_pdf")

        # Admin can access
        self.client.force_login(self.admin_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # Accountant can access accountant endpoints
        self.client.force_login(self.accountant_user)
        url_accounts_csv = reverse("accounts_panel:pending_dues_csv")
        url_accounts_pdf = reverse("accounts_panel:pending_dues_pdf")

        response = self.client.get(url_accounts_csv)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url_accounts_pdf)
        self.assertEqual(response.status_code, 200)

        # Principal can access
        self.client.force_login(self.principal_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)

    def test_session_results_csv_and_pdf_access_rules(self):
        url_csv = reverse("reports:session_results_csv", kwargs={"session_id": self.session.id})
        url_pdf = reverse("reports:session_results_pdf", kwargs={"session_id": self.session.id})

        # Principal can access
        self.client.force_login(self.principal_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)

        # Accountant cannot access
        self.client.force_login(self.accountant_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 404)

    def test_student_directory_csv_access_rules(self):
        url = reverse("reports:student_directory_csv")

        # Principal can access
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Accountant cannot
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_teacher_workload_pdf_and_csv_access_rules(self):
        url_csv = reverse("reports:teacher_workload_csv")
        url_pdf = reverse("reports:teacher_workload_pdf")

        # Admin can access
        self.client.force_login(self.admin_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)

        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)

        # Accountant cannot
        self.client.force_login(self.accountant_user)
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 404)

    def test_student_transcript_pdf_access_rules(self):
        # 1. Admin/Principal can access any student's transcript
        url = reverse("reports:student_transcript_pdf", kwargs={"student_id": self.student.id})
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 2. Student portal PDF transcript mapping (using own profile)
        url_portal = reverse("student_portal:student_transcript_pdf")
        self.client.force_login(self.student_user)
        response = self.client.get(url_portal)
        self.assertEqual(response.status_code, 200)

        # 3. Student cannot access other student's transcript
        url_forbidden = reverse("reports:student_transcript_pdf", kwargs={"student_id": self.other_student.id})
        response = self.client.get(url_forbidden)
        self.assertEqual(response.status_code, 404)

        # 4. Guardian can access linked child transcript
        url_guardian = reverse("guardian_portal:child_transcript_pdf", kwargs={"student_id": self.student.id})
        self.client.force_login(self.guardian_user)
        response = self.client.get(url_guardian)
        self.assertEqual(response.status_code, 200)

        # 5. Guardian cannot access other child's transcript
        url_guardian_forb = reverse("guardian_portal:child_transcript_pdf", kwargs={"student_id": self.other_student.id})
        response = self.client.get(url_guardian_forb)
        self.assertEqual(response.status_code, 404)

    def test_success_report_pdf_performance_and_access(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from apps.achievements.models import Achievement

        # Seed initial achievement
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=2026,
            rank="1st"
        )

        url = reverse("reports:success_pdf")

        # 1. Admin/Principal can access
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # 2. Accountant is blocked
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # 3. Query Count Check (Performance Optimization)
        self.client.force_login(self.admin_user)

        with CaptureQueriesContext(connection) as ctx_base:
            self.client.get(url)
        base_queries = len(ctx_base)

        # Seed more students, enrollments, and achievements
        for i in range(5):
            s = Student.objects.create(
                full_name=f"Success Student {i}",
                roll_number=f"SUC-{i}",
                status="Active"
            )
            Enrollment.objects.create(
                student=s,
                session=self.session,
                status="Active",
                registration_date=timezone.localdate()
            )
            Achievement.objects.create(
                student=s,
                exam_type="CSS",
                year=2026,
                rank=f"{i}th"
            )

        with CaptureQueriesContext(connection) as ctx_expanded:
            self.client.get(url)
        expanded_queries = len(ctx_expanded)

        # The query count must be completely bounded and not grow linearly (N+1 is eliminated)
        self.assertEqual(base_queries, expanded_queries,
                         f"N+1 query detected in SuccessReportPDFView! Base: {base_queries}, Expanded: {expanded_queries}")

    def test_teacher_workload_pdf_performance_and_access(self):
        from django.test.utils import CaptureQueriesContext
        from django.db import connection
        from apps.academics.models import TeacherAssignment

        url = reverse("reports:teacher_workload_pdf")

        # 1. Admin/Principal can access
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")

        # 2. Accountant is blocked
        self.client.force_login(self.accountant_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # 3. Query Count Check (Performance Optimization)
        self.client.force_login(self.admin_user)

        with CaptureQueriesContext(connection) as ctx_base:
            self.client.get(url)
        base_queries = len(ctx_base)

        # Seed more faculty profiles and assignments
        for i in range(5):
            u = User.objects.create_user(
                username=f"teacher_perf_{i}@test.com",
                email=f"teacher_perf_{i}@test.com",
                password="password",
                first_name=f"Teacher{i}",
                last_name="Test"
            )
            u.groups.add(self.group_teacher)
            FacultyProfile.objects.create(
                user=u,
                designation="Lecturer",
                department="English",
                is_active=True
            )
            TeacherAssignment.objects.create(
                teacher=u,
                session=self.session,
                subject=self.subject,
                is_active=True
            )

        with CaptureQueriesContext(connection) as ctx_expanded:
            self.client.get(url)
        expanded_queries = len(ctx_expanded)

        # Bounded query count check (must not grow with N teachers)
        self.assertEqual(base_queries, expanded_queries,
                         f"N+1 query detected in TeacherWorkloadPDFView! Base: {base_queries}, Expanded: {expanded_queries}")
