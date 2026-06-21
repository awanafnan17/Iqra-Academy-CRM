import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session
from apps.students.models import Student, Enrollment, Guardian
from apps.admissions.models import AdmissionApplication
from apps.core.permission_service import seed_default_permissions
from apps.core.validators import format_cnic, validate_cnic
from apps.students.forms import StudentCreateForm, StudentForm, GuardianForm
from apps.admissions.forms import AdmissionApplicationForm
from apps.accounts.forms import UserProfileForm

User = get_user_model()

class RepairBatch1RegressionTests(TestCase):
    def setUp(self):
        super().setUp()

        # Seed roles & permissions
        seed_default_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.registrar_group, _ = Group.objects.get_or_create(name="Registrar")

        # Create test users
        self.admin_user = User.objects.create_user(
            username="admin_repair@test.com",
            email="admin_repair@test.com",
            password="password",
            first_name="Admin",
            last_name="User",
            status="Active"
        )
        self.admin_user.groups.add(self.admin_group)

        # Create test session
        self.session = Session.objects.create(
            name="CP Science 101",
            status="Active",
            roll_prefix="CP-S",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS"
        )

        # Create a test student without enrollment
        self.student = Student.objects.create(
            full_name="Ali Raza",
            phone="03001112222",
            cnic="35202-1111111-1"
        )

        # Log in test client as admin
        self.client.login(username="admin_repair@test.com", password="password")

    def test_missing_templates_render_successfully(self):
        """Verify that accessing views that render previously missing templates returns 200 OK."""
        # 1. student_documents
        url = reverse("admin_panel:students:student_documents", kwargs={"pk": self.student.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_documents.html")

        # 2. student_guardians
        url = reverse("admin_panel:students:student_guardians", kwargs={"pk": self.student.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_guardians.html")

        # 3. student_ledger
        url = reverse("admin_panel:students:student_ledger", kwargs={"pk": self.student.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/student_ledger.html")

        # 4. enrollment_list
        url = reverse("admin_panel:students:enrollment_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/enrollment_list.html")

        # 5. enrollment_create (renders enrollment_form.html)
        url = reverse("admin_panel:students:enrollment_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/enrollment_form.html")

        # 6. enrollment_detail (need to create an enrollment first)
        enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active"
        )
        url = reverse("admin_panel:students:enrollment_detail", kwargs={"pk": enrollment.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "students/enrollment_detail.html")

    def test_student_edit_flow(self):
        """Verify student edit views are linked in details/list and save mutations correctly."""
        # Check details page for edit details link
        url_detail = reverse("admin_panel:students:student_detail", kwargs={"pk": self.student.pk})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit Details")

        # Check list page for edit link
        url_list = reverse("admin_panel:students:student_list")
        response = self.client.get(url_list)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Edit")

        # Load edit page
        url_edit = reverse("admin_panel:students:student_edit", kwargs={"pk": self.student.pk})
        response = self.client.get(url_edit)
        self.assertEqual(response.status_code, 200)

        # POST edit mutation
        post_data = {
            "full_name": "Ali Raza Edited",
            "phone": "03009998888",
            "cnic": "35202-2222222-2",
            "gender": "Male",
            "status": "Active"
        }
        response = self.client.post(url_edit, data=post_data)
        self.assertRedirects(response, url_detail)

        # Verify DB and UI updated
        self.student.refresh_from_db()
        self.assertEqual(self.student.full_name, "Ali Raza Edited")
        self.assertEqual(self.student.phone, "03009998888")
        self.assertEqual(self.student.cnic, "35202-2222222-2")

        # Check detail page shows updated name
        response = self.client.get(url_detail)
        self.assertContains(response, "Ali Raza Edited")

    def test_student_enrollment_dead_end_resolution(self):
        """Verify unenrolled students have an Enroll Student action and can be successfully enrolled."""
        # Unenrolled student starts with "Not Enrolled"
        self.assertIsNone(self.student.roll_number)

        url_detail = reverse("admin_panel:students:student_detail", kwargs={"pk": self.student.pk})
        response = self.client.get(url_detail)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Not Enrolled")
        self.assertContains(response, "Enroll Student")
        self.assertContains(response, "Enroll Now")

        # Load enrollment form
        url_enroll_create = reverse("admin_panel:students:enrollment_create")
        response = self.client.get(f"{url_enroll_create}?student={self.student.pk}")
        self.assertEqual(response.status_code, 200)

        # Submit enrollment
        post_data = {
            "student": self.student.pk,
            "session": self.session.pk,
            "registration_date": timezone.localdate().isoformat(),
            "status": "Active",
            "registration_fee": "200.00",
            "fee": "1000.00",
            "discount": "0.00"
        }
        response = self.client.post(url_enroll_create, data=post_data)

        # Verify enrollment created in database
        self.assertTrue(Enrollment.objects.filter(student=self.student, session=self.session).exists())

        # Verify student roll number is generated
        self.student.refresh_from_db()
        self.assertIsNotNone(self.student.roll_number)
        self.assertTrue(self.student.roll_number.startswith("CP-S"))

        # Verify details page no longer displays "Not Enrolled" or "Enroll Student"
        response = self.client.get(url_detail)
        self.assertNotContains(response, "Not Enrolled")
        self.assertNotContains(response, "Enroll Student")
        self.assertContains(response, self.student.roll_number)

    def test_cnic_validation_logic(self):
        """Verify the CNIC validation utility and form sanitization behavior."""
        # Test validator function directly
        # Correctly formatted
        validate_cnic("35202-1234567-1")
        validate_cnic(format_cnic("3520212345671"))

        # Letters rejected
        with self.assertRaises(ValidationError):
            validate_cnic("35202-abc4567-1")

        # Wrong digits rejected
        with self.assertRaises(ValidationError):
            validate_cnic("35202-123456-1") # 6 digits instead of 7
        with self.assertRaises(ValidationError):
            validate_cnic("352021234561") # 12 digits

        # Test CNIC fields across forms
        # 1. StudentCreateForm
        # Valid raw 13 digits
        form = StudentCreateForm(data={
            "full_name": "Test Name",
            "cnic": "3520212345671"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnic"], "35202-1234567-1")

        # Optional blank CNIC accepted
        form = StudentCreateForm(data={
            "full_name": "Test Name",
            "cnic": ""
        })
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["cnic"], "")

        # Invalid CNIC letters rejected
        form = StudentCreateForm(data={
            "full_name": "Test Name",
            "cnic": "35202-ABC-1"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("cnic", form.errors)

        # 2. StudentForm
        form = StudentForm(data={
            "full_name": "Test Name",
            "cnic": "3520212345671",
            "status": "Active"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnic"], "35202-1234567-1")

        # 3. GuardianForm
        form = GuardianForm(data={
            "full_name": "Test Parent",
            "relationship": "Father",
            "cnic": "3520212345671"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnic"], "35202-1234567-1")

        # 4. AdmissionApplicationForm
        form = AdmissionApplicationForm(data={
            "full_name": "Applicant",
            "father_name": "Parent",
            "email": "applicant@test.com",
            "phone": "03001234567",
            "date_of_birth": "2010-01-01",
            "cnic": "3520212345671",
            "desired_session": self.session.pk,
            "exam_type": "CSS"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnic"], "35202-1234567-1")

        # 5. UserProfileForm
        form = UserProfileForm(data={
            "first_name": "User",
            "last_name": "Profile",
            "cnic": "3520212345671"
        })
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["cnic"], "35202-1234567-1")

        # Duplicate CNIC behavior matches current database rule (allowed)
        student_dup = Student(
            full_name="Duplicate Student",
            cnic="35202-1111111-1" # matches setUp student's CNIC
        )
        student_dup.full_clean() # Should not raise uniqueness error since cnic is not unique

    def test_student_create_session_dropdown(self):
        """Verify session dropdown in StudentCreateForm filters correctly."""
        # Active session is already created in setUp (self.session)
        # Create an inactive session
        inactive_session = Session.objects.create(
            name="Inactive Session 101",
            status="Inactive",
            roll_prefix="IN-S",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS"
        )
        
        # Instantiate StudentCreateForm and check the session field choices
        form = StudentCreateForm()
        session_queryset = form.fields["session"].queryset
        
        # Active session should be in queryset, Inactive session should not
        self.assertIn(self.session, session_queryset)
        self.assertNotIn(inactive_session, session_queryset)
        
        # Verify student create page renders and has the active session in select element
        url = reverse("admin_panel:students:student_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.session.name)
        self.assertNotContains(response, inactive_session.name)
        
        # Verify student can be created with the active session
        post_data = {
            "full_name": "New Student With Session",
            "phone": "03001112222",
            "cnic": "35202-3333333-3",
            "gender": "Male",
            "session": self.session.pk,
            "fee_type": "one_time",
            "total_fee_amount": "1000.00",
        }
        response = self.client.post(url, data=post_data)
        # Check if student and enrollment are created
        self.assertTrue(Student.objects.filter(full_name="New Student With Session").exists())
        student = Student.objects.get(full_name="New Student With Session")
        self.assertTrue(Enrollment.objects.filter(student=student, session=self.session).exists())

    def test_student_list_pagination(self):
        """Verify student list is paginated and search/filters are preserved."""
        # Create enough students to have multiple pages (e.g. 30 more students, making 31 total)
        students_to_create = []
        for i in range(1, 31):
            students_to_create.append(
                Student(
                    full_name=f"Paginated Student {i:02d}",
                    phone=f"0300{i:07d}",
                    cnic=f"35202-{i:07d}-1",
                    status="Active" if i % 2 == 0 else "Inactive"
                )
            )
        Student.objects.bulk_create(students_to_create)
        
        # We now have 31 students total (30 bulk created + 1 from setUp)
        url = reverse("admin_panel:students:student_list")
        
        # 1. Fetch first page
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # Check that context has page_obj and it is paginated to 25 items
        self.assertIn("page_obj", response.context)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj.object_list), 25)
        self.assertEqual(page_obj.paginator.count, 31)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())
        
        # 2. Fetch second page
        response = self.client.get(f"{url}?page=2")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(len(page_obj.object_list), 6) # 31 - 25 = 6
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())
        
        # 3. Invalid page should fallback gracefully and not crash (e.g. page=999)
        response = self.client.get(f"{url}?page=999")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, 2)
        
        # 4. Non-integer page should fallback to page 1
        response = self.client.get(f"{url}?page=invalid")
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, 1)

        # 5. Verify search parameter is preserved in context
        response = self.client.get(f"{url}?q=Paginated&status=Active")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "Paginated")
        self.assertEqual(response.context["status_filter"], "Active")


