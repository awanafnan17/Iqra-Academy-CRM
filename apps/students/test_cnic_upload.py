import os
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from apps.students.models import Student, StudentDocument
from apps.students.forms import StudentCreateForm, StudentForm
from apps.core.permission_service import seed_default_permissions

User = get_user_model()

class CnicUploadTests(TestCase):
    def setUp(self):
        super().setUp()
        seed_default_permissions()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        self.principal_group, _ = Group.objects.get_or_create(name="Principal")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")

        self.admin_user = User.objects.create_user(
            username="admin_cnic@test.com",
            email="admin_cnic@test.com",
            password="password",
            status="Active"
        )
        self.admin_user.groups.add(self.admin_group)

        self.registrar_user = User.objects.create_user(
            username="registrar_cnic@test.com",
            email="registrar_cnic@test.com",
            password="password",
            status="Active"
        )
        self.registrar_user.groups.add(self.registrar_group)

        self.principal_user = User.objects.create_user(
            username="principal_cnic@test.com",
            email="principal_cnic@test.com",
            password="password",
            status="Active"
        )
        self.principal_user.groups.add(self.principal_group)

        self.teacher_user = User.objects.create_user(
            username="teacher_cnic@test.com",
            email="teacher_cnic@test.com",
            password="password",
            status="Active"
        )
        self.teacher_user.groups.add(self.teacher_group)

    def test_form_fields_present(self):
        """Assert both forms contain cnic_photo field."""
        create_form = StudentCreateForm()
        self.assertIn("cnic_photo", create_form.fields)
        
        edit_form = StudentForm()
        self.assertIn("cnic_photo", edit_form.fields)

    def test_valid_image_upload_creation(self):
        """Valid JPG upload during student creation saves and links to student."""
        self.client.login(username="admin_cnic@test.com", password="password")
        url = reverse("admin_panel:students:student_create")
        
        # Valid 100 bytes jpeg image file content
        image_content = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00" + b"\x00" * 80
        cnic_photo = SimpleUploadedFile("cnic.jpg", image_content, content_type="image/jpeg")

        post_data = {
            "full_name": "Test Student Cnic",
            "phone": "03001234567",
            "cnic": "35202-1234567-1",
            "cnic_photo": cnic_photo
        }
        
        response = self.client.post(url, data=post_data)
        student = Student.objects.filter(full_name="Test Student Cnic").first()
        self.assertIsNotNone(student)
        self.assertRedirects(response, reverse("admin_panel:students:student_detail", kwargs={"pk": student.pk}))

        # Check linked StudentDocument
        doc = StudentDocument.objects.filter(student=student, document_type="cnic_front").first()
        self.assertIsNotNone(doc)
        self.assertEqual(doc.title, "CNIC Front")
        self.assertTrue(os.path.exists(doc.file.path))
        
        # Clean up physical file
        if os.path.exists(doc.file.path):
            os.remove(doc.file.path)

    def test_invalid_file_type_rejected(self):
        """Invalid file type (e.g. .txt) is rejected."""
        # 1. StudentCreateForm validation
        invalid_file = SimpleUploadedFile("cnic.txt", b"plain text content", content_type="text/plain")
        form = StudentCreateForm(
            data={"full_name": "Test", "cnic": "35202-1234567-1"},
            files={"cnic_photo": invalid_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cnic_photo", form.errors)
        self.assertIn("Only JPG, JPEG, PNG, and WEBP", form.errors["cnic_photo"][0])

    def test_pdf_rejected(self):
        """PDF file is rejected by policy."""
        invalid_file = SimpleUploadedFile("cnic.pdf", b"%PDF-1.4 dummy pdf content", content_type="application/pdf")
        form = StudentCreateForm(
            data={"full_name": "Test", "cnic": "35202-1234567-1"},
            files={"cnic_photo": invalid_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cnic_photo", form.errors)
        self.assertIn("Only JPG, JPEG, PNG, and WEBP", form.errors["cnic_photo"][0])

    def test_oversized_file_rejected(self):
        """Oversized file (> 2MB) is rejected."""
        large_content = b"\x00" * (2 * 1024 * 1024 + 100)  # > 2MB
        large_file = SimpleUploadedFile("cnic.jpg", large_content, content_type="image/jpeg")
        form = StudentCreateForm(
            data={"full_name": "Test", "cnic": "35202-1234567-1"},
            files={"cnic_photo": large_file}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("cnic_photo", form.errors)
        self.assertIn("File size must be under 2MB.", form.errors["cnic_photo"][0])

    def test_no_orphan_on_student_validation_failure(self):
        """If student creation fails validation, no orphan CNIC document or physical file remains."""
        self.client.login(username="admin_cnic@test.com", password="password")
        url = reverse("admin_panel:students:student_create")
        
        # Missing full_name to trigger form/service validation failure
        image_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"
        cnic_photo = SimpleUploadedFile("cnic.jpg", image_content, content_type="image/jpeg")

        post_data = {
            "full_name": "",  # invalid
            "phone": "03001234567",
            "cnic_photo": cnic_photo
        }
        
        doc_count_before = StudentDocument.objects.count()
        response = self.client.post(url, data=post_data)
        
        # Form should have errors and render form with errors
        self.assertEqual(response.status_code, 200)
        self.assertEqual(StudentDocument.objects.count(), doc_count_before)

    def test_student_edit_replace_cnic_photo(self):
        """Student edit can upload/replace CNIC photo and deletes the old file."""
        self.client.login(username="admin_cnic@test.com", password="password")
        
        student = Student.objects.create(
            full_name="Edit Student Test",
            phone="03001234567"
        )
        
        # Upload initial CNIC photo
        url_edit = reverse("admin_panel:students:student_edit", kwargs={"pk": student.pk})
        
        image_content_1 = b"\xff\xd8\xff\xe0\x00\x10JFIF_1"
        photo_1 = SimpleUploadedFile("cnic1.jpg", image_content_1, content_type="image/jpeg")
        
        post_data_1 = {
            "full_name": "Edit Student Test",
            "phone": "03001234567",
            "status": "Active",
            "cnic_photo": photo_1
        }
        self.client.post(url_edit, data=post_data_1)
        
        doc_1 = StudentDocument.objects.filter(student=student, document_type="cnic_front").first()
        self.assertIsNotNone(doc_1)
        path_1 = doc_1.file.path
        self.assertTrue(os.path.exists(path_1))

        # Replace with photo 2 (use .png to ensure path extension changes and path_1 deletion can be asserted)
        image_content_2 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        photo_2 = SimpleUploadedFile("cnic2.png", image_content_2, content_type="image/png")
        
        post_data_2 = {
            "full_name": "Edit Student Test",
            "phone": "03001234567",
            "status": "Active",
            "cnic_photo": photo_2
        }
        self.client.post(url_edit, data=post_data_2)
        
        # Verify old file was deleted
        self.assertFalse(os.path.exists(path_1))
        
        # Verify new file exists
        doc_2 = StudentDocument.objects.filter(student=student, document_type="cnic_front").first()
        self.assertIsNotNone(doc_2)
        self.assertTrue(os.path.exists(doc_2.file.path))
        self.assertTrue(doc_2.file.name.endswith(".png"))
        
        # Clean up
        if os.path.exists(doc_2.file.path):
            os.remove(doc_2.file.path)

    def test_permissions_student_documents(self):
        """Verify view/upload access to student documents is role-restricted."""
        student = Student.objects.create(
            full_name="Doc Perm Test",
            phone="03001234567"
        )
        url_docs = reverse("admin_panel:students:student_documents", kwargs={"pk": student.pk})

        # 1. Admin can access Admin Panel documents page
        self.client.login(username="admin_cnic@test.com", password="password")
        response = self.client.get(url_docs)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
 
        # 2. Principal can access Admin Panel documents page
        self.client.login(username="principal_cnic@test.com", password="password")
        response = self.client.get(url_docs)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # 3. Registrar cannot access Admin Panel prefix routes (blocked by middleware with 404)
        self.client.login(username="registrar_cnic@test.com", password="password")
        response = self.client.get(url_docs)
        self.assertEqual(response.status_code, 404)
        
        # Registrar CAN access their own Registrar Panel upload route
        url_registrar_upload = reverse("registrar_panel:student_document_upload", kwargs={"pk": student.pk})
        response = self.client.get(url_registrar_upload)
        # GET is allowed through middleware/decorators, view returns a 302 redirect for invalid method
        self.assertEqual(response.status_code, 302)
        self.client.logout()

        # 4. Teacher is blocked (returns 404 as per role_required decorator policy)
        self.client.login(username="teacher_cnic@test.com", password="password")
        response = self.client.get(url_docs)
        self.assertEqual(response.status_code, 404)
        self.client.logout()

        # 5. Anonymous user redirected to login
        response = self.client.get(url_docs)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
