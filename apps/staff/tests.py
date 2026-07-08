from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from apps.staff.models import FacultyProfile
from apps.academics.models import Session

User = get_user_model()


@override_settings(ROOT_URLCONF="config.urls")
class FacultyModuleTests(TestCase):
    def setUp(self):
        super().setUp()
        self.group_admin = Group.objects.create(name="Admin")
        self.group_principal = Group.objects.create(name="Principal")
        self.group_teacher = Group.objects.create(name="Teacher")

        # Admin user
        self.admin_user = User.objects.create_user(
            username="admin@test.com",
            email="admin@test.com",
            password="pass",
        )
        self.admin_user.groups.add(self.group_admin)

        # Principal user
        self.principal_user = User.objects.create_user(
            username="principal@test.com",
            email="principal@test.com",
            password="pass",
        )
        self.principal_user.groups.add(self.group_principal)

        # Teacher user
        self.teacher_user = User.objects.create_user(
            username="teacher@test.com",
            email="teacher@test.com",
            password="pass",
        )
        self.teacher_user.groups.add(self.group_teacher)

        # Create active sessions
        self.session_cs = Session.objects.create(
            name="Computer Programming 101",
            code="CP-101",
            roll_prefix="CP",
            status="Active",
            due_day=10
        )
        self.session_math = Session.objects.create(
            name="Advanced Calculus",
            code="MA-301",
            roll_prefix="MA",
            status="Active",
            due_day=10
        )

        # Create a faculty profile
        self.faculty_profile = FacultyProfile.objects.create(
            user=self.teacher_user,
            designation="Lecturer",
            department="Mathematics"
        )

    def test_faculty_profile_creation(self):
        """Verify faculty profile attributes and string representation."""
        self.assertEqual(self.faculty_profile.designation, "Lecturer")
        self.assertEqual(self.faculty_profile.department, "Mathematics")
        self.assertTrue(self.faculty_profile.is_active)
        self.assertEqual(
            str(self.faculty_profile),
            "teacher@test.com (Lecturer - Mathematics)"
        )

    def test_faculty_list_view_permissions(self):
        """FacultyListView requires Admin or Principal, blocks other roles."""
        url = reverse("admin_panel:staff:faculty_list")

        # Admin gets access
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "staff/faculty_list.html")

        # Principal gets access
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Teacher gets blocked
        self.client.force_login(self.teacher_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_faculty_create_view_permissions_and_processing(self):
        """FacultyCreateView requires Admin, handles transaction mapping on success."""
        url = reverse("admin_panel:staff:faculty_create")

        # Principal is blocked (404)
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Admin can access form
        self.client.force_login(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "staff/faculty_form.html")

        # POST creation processing
        post_data = {
            # UserCreateForm data
            "first_name": "Ahmed",
            "last_name": "Doe",
            "email": "ahmedhassan@test.com",
            "password": "ahmedpassword",
            # FacultyProfileForm data
            "role": "Teacher",
            "designation": "Assistant Professor",
            "department": "Computer Science",
            "is_active": "on",
        }

        response = self.client.post(url, data=post_data)
        # On success, redirects to list
        self.assertEqual(response.status_code, 302)

        # Verify created objects
        new_user = User.objects.get(email="ahmedhassan@test.com")
        self.assertEqual(new_user.first_name, "Ahmed")
        self.assertEqual(new_user.last_name, "Doe")
        self.assertTrue(new_user.groups.filter(name="Teacher").exists())

        new_profile = FacultyProfile.objects.get(user=new_user)
        self.assertEqual(new_profile.designation, "Assistant Professor")
        self.assertEqual(new_profile.department, "Computer Science")

    def test_faculty_create_role_validation(self):
        """FacultyCreateView shows validation error if role is not selected."""
        url = reverse("admin_panel:staff:faculty_create")
        self.client.force_login(self.admin_user)
        
        post_data = {
            "first_name": "Ahmed",
            "last_name": "Doe",
            "email": "ahmedvalidation@test.com",
            "password": "ahmedpassword",
            "role": "",  # Empty role
            "designation": "Assistant Professor",
            "department": "Computer Science",
            "is_active": "on",
        }
        
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 200)  # Form returns 200 on validation failure
        self.assertFormError(response, "form", "role", "This field is required.")

    def test_faculty_create_accountant_role(self):
        """FacultyCreateView creates user with Accountant role successfully."""
        url = reverse("admin_panel:staff:faculty_create")
        self.client.force_login(self.admin_user)
        
        post_data = {
            "first_name": "Accountant",
            "last_name": "User",
            "email": "accountant_faculty@test.com",
            "password": "accountantpass",
            "role": "Accountant",
            "designation": "Senior Accountant",
            "department": "Finance",
            "is_active": "on",
        }
        
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)
        
        new_user = User.objects.get(email="accountant_faculty@test.com")
        self.assertTrue(new_user.groups.filter(name="Accountant").exists())
        self.assertFalse(new_user.groups.filter(name="Teacher").exists())

    def test_faculty_assign_view_permissions_and_processing(self):
        """FacultyAssignSessionView allows Admin/Principal to allocate sessions."""
        url = reverse("admin_panel:staff:faculty_assign", args=[self.faculty_profile.pk])

        # Teacher is blocked
        self.client.force_login(self.teacher_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Principal is allowed
        self.client.force_login(self.principal_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "staff/faculty_assign.html")

        # Assign sessions
        post_data = {
            "assigned_sessions": [self.session_cs.pk, self.session_math.pk]
        }
        response = self.client.post(url, data=post_data)
        self.assertEqual(response.status_code, 302)

        # Verify assignments updated
        self.faculty_profile.refresh_from_db()
        sessions = self.faculty_profile.assigned_sessions.all()
        self.assertEqual(sessions.count(), 2)
        self.assertIn(self.session_cs, sessions)
        self.assertIn(self.session_math, sessions)
