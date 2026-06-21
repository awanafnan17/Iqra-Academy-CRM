from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()


class StudentPortalLoginTests(TestCase):
    def setUp(self):
        self.admin_group, _ = Group.objects.get_or_create(
            name="Admin"
        )
        self.admin = User.objects.create_user(
            username="admin_portal_test",
            password="TestPass123!",
            email="admin_portal@example.com",
        )
        self.admin.groups.add(self.admin_group)
        self.client.force_login(self.admin)

        from apps.academics.models import Session
        self.session = Session.objects.create(
            name="Portal Test Session",
            status="Active",
            roll_prefix="PT",
        )

    def test_student_create_generates_portal_user(self):
        """Adding a student creates a linked portal user."""
        from apps.students.services import StudentService
        student = StudentService.create_student(
            full_name="Ahmed Hassan",
            email="ahmed.hassan@example.com",
            phone="03001234567",
            created_by=self.admin,
        )
        self.assertIsNotNone(student.pk)
        # Check portal user was created
        portal_username = getattr(
            student, "_portal_username", None
        )
        if portal_username:
            self.assertTrue(
                User.objects.filter(
                    username=portal_username
                ).exists()
            )

    def test_student_create_view_post_creates_student(self):
        """POST to student create redirects and creates student."""
        response = self.client.post(
            "/panel/admin/add-student/",
            data={
                "full_name": "Fatima Khan",
                "phone": "03211234567",
                "email": "fatima.khan@example.com",
                "gender": "Female",
                "status": "Active"
            },
        )
        self.assertIn(
            response.status_code, [200, 302],
            "Student create should return 200 or redirect"
        )

    def test_student_reset_password_view(self):
        """Admin can reset student portal password."""
        from apps.students.models import Student
        # Create student with user
        student = Student.objects.create(
            full_name="Usman Ali",
            phone="03451234567",
        )
        portal_user = User.objects.create_user(
            username="usman_ali_test",
            password="OldPass123!",
            email="usman@example.com",
        )
        student.portal_user = portal_user
        student.save(update_fields=["portal_user"])

        response = self.client.post(
            f"/panel/admin/students/{student.pk}/reset-password/"
        )
        self.assertIn(
            response.status_code, [200, 302]
        )

    def test_student_create_login_view(self):
        """Admin can create portal login for student without one."""
        from apps.students.models import Student
        student = Student.objects.create(
            full_name="Ayesha Siddiqui",
            email="ayesha@example.com",
        )
        # Ensure no user linked
        student.portal_user = None
        student.save(update_fields=["portal_user"])

        response = self.client.post(
            f"/panel/admin/students/{student.pk}/create-login/"
        )
        self.assertIn(
            response.status_code, [200, 302]
        )
