import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.core.exceptions import ValidationError

from apps.academics.models import Session
from apps.admissions.models import AdmissionApplication, AdmissionDocument
from apps.admissions.services import AdmissionService
from apps.core.models import AuditLog, RolePermission
from apps.core.services import DomainValidationError
from apps.notifications.models import EmailLog
from apps.students.models import Student, Enrollment

User = get_user_model()

class AdmissionWorkflowTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        
        # Create user groups
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_registrar, _ = Group.objects.get_or_create(name="Registrar")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.group_admin)

        self.registrar_user = User.objects.create_user(
            username="registrar@test.com", email="registrar@test.com", password="password"
        )
        self.registrar_user.groups.add(self.group_registrar)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Create active session
        self.session = Session.objects.create(
            name="CSS Evening Batch",
            code="CSSE",
            roll_prefix="CSS-E",
            status="Active",
            is_admission_open=True,
            max_capacity=50,
            session_category="CSS",
            academic_year="2026",
            batch_number="1",
            fee=Decimal("5000.00"),
            registration_fee=Decimal("1000.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
        )

    def test_duplicate_application_prevented(self):
        """Submitting duplicate application with same email + desired session in 30 days should fail."""
        # First submission
        app = AdmissionService.submit_application(
            full_name="John Doe",
            father_name="Senior Doe",
            email="john@example.com",
            phone="+923001234567",
            date_of_birth=datetime.date(2000, 1, 1),
            desired_session=self.session,
            exam_type="CSS",
            cnic="35201-1234567-1",
            address="Lahore, Pakistan"
        )
        self.assertIsNotNone(app.id)

        # Second submission should raise DomainValidationError
        with self.assertRaises(DomainValidationError):
            AdmissionService.submit_application(
                full_name="John Doe Duplicate",
                father_name="Senior Doe",
                email="john@example.com",
                phone="+923001234567",
                date_of_birth=datetime.date(2000, 1, 1),
                desired_session=self.session,
                exam_type="CSS",
                cnic="35201-1234567-1",
                address="Lahore, Pakistan"
            )

    def test_registrar_cannot_approve(self):
        """Registrar role is restricted from approving applications."""
        app = AdmissionService.submit_application(
            full_name="Jane Doe",
            father_name="Senior Doe",
            email="jane@example.com",
            phone="+923001234567",
            date_of_birth=datetime.date(2000, 1, 1),
            desired_session=self.session,
            exam_type="CSS"
        )
        
        self.client.force_login(self.registrar_user)
        # Try to approve via POST view
        url = reverse("registrar_panel:admissions:admission_approve", kwargs={"pk": app.id})
        response = self.client.post(url, {"remarks": "Looks good"})
        self.assertEqual(response.status_code, 404) # Check that they get a 404

    def test_non_admin_cannot_access_admin_panel(self):
        """Users without Admin/Registrar roles cannot view admissions panel."""
        self.client.force_login(self.teacher_user)
        url = reverse("admin_panel:admissions:admission_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_conversion_creates_student_enrollment_roll(self):
        """Approve and convert to student creates Student, Enrollment and auto roll prefix number."""
        app = AdmissionService.submit_application(
            full_name="Conversion Test Student Name That is Very Long and Needs Truncation to Max Length of Hundred Characters",
            father_name="Father Name That is Also Long and Needs Truncation to Max Length of Hundred Characters",
            email="convert@example.com",
            phone="+9230012345678901234", # Phone with max 20, student allows max 15
            date_of_birth=datetime.date(2002, 2, 2),
            desired_session=self.session,
            exam_type="CSS",
            cnic="35201-9876543-1"
        )
        
        # Approve
        AdmissionService.approve_application(app.id, self.admin_user, "Approved by admin")
        
        # Convert to student
        student = AdmissionService.convert_to_student(app.id, self.admin_user)
        
        # Assert student profile is created and truncated properly
        self.assertEqual(student.full_name, app.full_name[:100])
        self.assertEqual(student.father_name, app.father_name[:100])
        self.assertEqual(student.phone, app.phone[:15])
        self.assertEqual(student.email, app.email)
        
        # Assert roll number is generated based on prefix CSS-E
        self.assertTrue(student.roll_number.startswith("CSS-E-"))
        
        # Assert enrollment is created
        enrollments = Enrollment.objects.filter(student=student, session=self.session)
        self.assertEqual(enrollments.count(), 1)
        self.assertEqual(enrollments.first().status, "Active")
        
        # Assert application status is now withdrawn
        app.refresh_from_db()
        self.assertEqual(app.status, "withdrawn")
        self.assertEqual(app.converted_student, student)

    def test_email_sent_on_approval(self):
        """Approved application triggers email and saves EmailLog."""
        app = AdmissionService.submit_application(
            full_name="Email Test",
            father_name="Father",
            email="emailtest@example.com",
            phone="+923001234567",
            date_of_birth=datetime.date(2001, 1, 1),
            desired_session=self.session,
            exam_type="CSS"
        )
        
        # Reset outbox and logs
        mail.outbox = []
        EmailLog.objects.all().delete()
        
        # Approve
        AdmissionService.approve_application(app.id, self.admin_user, "Looks clean")
        
        # Check outbox
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["emailtest@example.com"])
        self.assertIn("Approved", mail.outbox[0].subject)
        
        # Check EmailLog
        logs = EmailLog.objects.filter(recipient_email="emailtest@example.com")
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().status, "sent")

    def test_audit_log_on_conversion(self):
        """Conversion generates proper AuditLog entries."""
        app = AdmissionService.submit_application(
            full_name="Audit Test",
            father_name="Father",
            email="audit@example.com",
            phone="+923001234567",
            date_of_birth=datetime.date(2001, 1, 1),
            desired_session=self.session,
            exam_type="CSS"
        )
        
        # Approve
        AdmissionService.approve_application(app.id, self.admin_user, "Approved")
        
        # Convert
        AuditLog.objects.all().delete()
        student = AdmissionService.convert_to_student(app.id, self.admin_user)
        
        # Assert student creation audit log
        logs = AuditLog.objects.filter(model_name="students.Student", action="create")
        self.assertEqual(logs.count(), 1)
        
        # Assert application status change audit log
        logs_app = AuditLog.objects.filter(model_name="admissions.AdmissionApplication", action="update")
        self.assertEqual(logs_app.count(), 1)

    def test_public_form_accessible_without_login(self):
        """Public admission submission form is accessible without login."""
        url = reverse("admissions_public:apply")
        
        # GET request should succeed
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        # POST request should redirect to success page
        post_data = {
            "full_name": "Public Applicant",
            "father_name": "Father Name",
            "email": "public@example.com",
            "phone": "+923001234567",
            "date_of_birth": "2000-01-01",
            "desired_session": self.session.id,
            "exam_type": "CSS",
            "cnic": "12345-1234567-1",
            "address": "Lahore"
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302) # redirects to public_success
        self.assertRedirects(response, reverse("admissions_public:success"))

    def test_summary_metrics_correct(self):
        """Test aggregate admission summary metrics calculation."""
        AdmissionApplication.objects.all().delete()
        
        # Create applications
        app1 = AdmissionService.submit_application(
            full_name="App 1", father_name="F", email="app1@test.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        app2 = AdmissionService.submit_application(
            full_name="App 2", father_name="F", email="app2@test.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        app3 = AdmissionService.submit_application(
            full_name="App 3", father_name="F", email="app3@test.com", phone="123",
            date_of_birth=datetime.date(2000, 1, 1), desired_session=self.session, exam_type="CSS"
        )
        
        # Review app2
        AdmissionService.review_application(app2.id, self.admin_user)
        # Approve and convert app3
        AdmissionService.approve_application(app3.id, self.admin_user)
        AdmissionService.convert_to_student(app3.id, self.admin_user)
        
        summary = AdmissionService.get_application_summary()
        self.assertEqual(summary["total_applications"], 3)
        self.assertEqual(summary["pending_applications"], 2) # app1 is pending, app2 is under_review
        self.assertEqual(summary["converted_applications"], 1)
        self.assertEqual(summary["conversion_rate"], 33.33)

    def test_export_csv_admin_only(self):
        """Only users with Admin role can export admissions as CSV."""
        url = reverse("admin_panel:admissions:admission_export")
        
        # Registrar access should get 404
        self.client.force_login(self.registrar_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        
        # Admin access should get 200 and CSV content
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Full Name", response.content.decode("utf-8"))
