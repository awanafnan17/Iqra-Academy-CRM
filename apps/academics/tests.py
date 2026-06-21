import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session, Subject, ClassSchedule, TeacherAssignment
from apps.academics.forms import SessionForm, TeacherAssignmentForm
from apps.staff.models import FacultyProfile
from apps.analytics.services import get_teacher_workload

User = get_user_model()


class TimetableTests(TestCase):
    def setUp(self):
        super().setUp()

        # Create user accounts
        self.user1 = User.objects.create_user(
            username="teacher1@test.com", email="teacher1@test.com", password="password"
        )
        self.user2 = User.objects.create_user(
            username="teacher2@test.com", email="teacher2@test.com", password="password"
        )

        # Create faculty profiles
        self.faculty1 = FacultyProfile.objects.create(
            user=self.user1,
            designation="Senior Lecturer",
            department="Computer Science",
            is_active=True
        )
        self.faculty2 = FacultyProfile.objects.create(
            user=self.user2,
            designation="Professor",
            department="Mathematics",
            is_active=True
        )

        # Create sessions
        self.session = Session.objects.create(
            name="CSS Morning Batch 2026",
            status="Active",
            roll_prefix="CSS-M",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="Batch 1",
            max_capacity=50,
        )

        # Create subjects
        self.subject1 = Subject.objects.create(
            name="Programming Fundamental",
            session=self.session
        )
        self.subject2 = Subject.objects.create(
            name="Discrete Mathematics",
            session=self.session
        )

    def test_create_class_schedule_success(self):
        """Verify that a non-overlapping ClassSchedule can be created successfully."""
        schedule = ClassSchedule(
            session=self.session,
            subject=self.subject1,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
            classroom="Room 101"
        )
        # Should not raise validation errors
        schedule.full_clean()
        schedule.save()

        self.assertEqual(ClassSchedule.objects.count(), 1)

    def test_clean_validation_start_end_time(self):
        """Verify that start_time >= end_time raises ValidationError."""
        schedule = ClassSchedule(
            session=self.session,
            subject=self.subject1,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(10, 30),
            end_time=datetime.time(9, 0),
            classroom="Room 101"
        )
        with self.assertRaises(ValidationError) as context:
            schedule.full_clean()
        self.assertIn("Start time must be before end time.", str(context.exception))

    def test_faculty_overlap_conflict(self):
        """Verify that scheduling a teacher for overlapping classes on the same day raises ValidationError."""
        # Class 1: 9:00 - 10:30
        schedule1 = ClassSchedule.objects.create(
            session=self.session,
            subject=self.subject1,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
            classroom="Room 101"
        )

        # Class 2: 10:00 - 11:30 (overlaps with Class 1)
        schedule2 = ClassSchedule(
            session=self.session,
            subject=self.subject2,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 30),
            classroom="Room 102"
        )

        with self.assertRaises(ValidationError) as context:
            schedule2.full_clean()
        self.assertIn("is already scheduled on Monday", str(context.exception))

    def test_classroom_overlap_conflict(self):
        """Verify that scheduling two classes in the same classroom at overlapping times raises ValidationError."""
        # Class 1: 9:00 - 10:30 in Room 101
        schedule1 = ClassSchedule.objects.create(
            session=self.session,
            subject=self.subject1,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
            classroom="Room 101"
        )

        # Class 2: 10:00 - 11:30 in Room 101 (overlaps with Class 1)
        schedule2 = ClassSchedule(
            session=self.session,
            subject=self.subject2,
            faculty=self.faculty2,
            day_of_week="Monday",
            start_time=datetime.time(10, 0),
            end_time=datetime.time(11, 30),
            classroom="Room 101"
        )

        with self.assertRaises(ValidationError) as context:
            schedule2.full_clean()
        self.assertIn("is already reserved on Monday", str(context.exception))

    def test_get_teacher_workload(self):
        """Verify that workload calculations return correct hours, sessions, and subjects."""
        # Create schedules for Faculty 1
        # 1. Mon 9:00 - 10:30 (1.5 hrs)
        ClassSchedule.objects.create(
            session=self.session,
            subject=self.subject1,
            faculty=self.faculty1,
            day_of_week="Monday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 30),
            classroom="Room 101"
        )
        # 2. Wed 14:00 - 16:00 (2.0 hrs)
        ClassSchedule.objects.create(
            session=self.session,
            subject=self.subject2,
            faculty=self.faculty1,
            day_of_week="Wednesday",
            start_time=datetime.time(14, 0),
            end_time=datetime.time(16, 0),
            classroom="Room 101"
        )

        # Faculty 2 workload
        # 1. Tue 9:00 - 10:00 (1.0 hr)
        ClassSchedule.objects.create(
            session=self.session,
            subject=self.subject2,
            faculty=self.faculty2,
            day_of_week="Tuesday",
            start_time=datetime.time(9, 0),
            end_time=datetime.time(10, 0),
            classroom="Room 102"
        )

        workloads = get_teacher_workload()

        # We expect 2 workloads returned
        self.assertEqual(len(workloads), 2)

        # Verify Faculty 1 metrics: 3.5 hours, 1 session, 2 subjects
        w1 = next(x for x in workloads if x['faculty_id'] == self.faculty1.id)
        self.assertEqual(w1['hours_per_week'], 3.5)
        self.assertEqual(w1['sessions_count'], 1)
        self.assertEqual(w1['subjects_count'], 2)

        # Verify Faculty 2 metrics: 1.0 hour, 1 session, 1 subject
        w2 = next(x for x in workloads if x['faculty_id'] == self.faculty2.id)
        self.assertEqual(w2['hours_per_week'], 1.0)
        self.assertEqual(w2['sessions_count'], 1)
        self.assertEqual(w2['subjects_count'], 1)


class SessionAdditionTests(TestCase):
    def setUp(self):
        super().setUp()
        self.admin_group = Group.objects.create(name="Admin")
        self.teacher_group = Group.objects.create(name="Teacher")

        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.admin_group)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.teacher_group)

    def test_session_create_page_loads_for_admin(self):
        """Verify session create page loads for allowed role (Admin)."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_create"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "academics/session_form.html")

    def test_session_create_page_404_for_unauthorized(self):
        """Verify unauthorized role cannot load create page (raises 404)."""
        self.client.login(username="teacher@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_create"))
        self.assertEqual(response.status_code, 404)

    def test_valid_post_creates_session(self):
        """Verify that a valid POST creates a session."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "name": "New Test Session",
            "code": "NTS123",
            "roll_prefix": "NTS",
            "session_type": "time_period",
            "session_category": "CSS",
            "academic_year": "2026",
            "batch_number": "Batch 2",
            "max_capacity": 40,
            "max_students": 40,
            "start_date": "2026-06-01",
            "end_date": "2026-12-01",
            "fee": "12000.00",
            "registration_fee": "2000.00",
            "status": "Active",
            "due_day": 10,
            "late_fee_amount": "500.00",
            "late_fee_grace_days": 5,
            "late_fee_maximum": "2500.00"
        }
        initial_count = Session.objects.count()
        response = self.client.post(reverse("admin_panel:academics:session_create"), post_data)
        self.assertEqual(response.status_code, 302) # Redirect to session_detail
        self.assertEqual(Session.objects.count(), initial_count + 1)
        created_session = Session.objects.get(code="NTS123")
        self.assertEqual(created_session.name, "New Test Session")
        self.assertEqual(created_session.session_category, "CSS")

    def test_invalid_post_fails_and_shows_errors(self):
        """Verify that invalid POST shows errors and does not create a record."""
        self.client.login(username="admin@test.com", password="password")
        # due_day is out of range 1-28
        post_data = {
            "name": "Invalid Session",
            "code": "IS123",
            "roll_prefix": "IS",
            "session_type": "time_period",
            "session_category": "CSS",
            "start_date": "2026-06-01",
            "end_date": "2026-12-01",
            "status": "Active",
            "due_day": 99,
        }
        initial_count = Session.objects.count()
        response = self.client.post(reverse("admin_panel:academics:session_create"), post_data)
        self.assertEqual(response.status_code, 200) # Re-renders form
        self.assertEqual(Session.objects.count(), initial_count)
        self.assertFormError(response, "form", "due_day", "Due day must be between 1 and 28.")

    def test_missing_session_category_field_fails_validation(self):
        """Verify that omitting session_category causes validation error."""
        form_data = {
            "name": "Missing Category",
            "code": "MC123",
            "roll_prefix": "MC",
            "session_type": "time_period",
            "start_date": "2026-06-01",
            "end_date": "2026-12-01",
            "status": "Active",
            "due_day": 10,
        }
        form = SessionForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("session_category", form.errors)
        self.assertEqual(form.errors["session_category"], ["This field is required."])


class AcademicsCRUDTests(TestCase):
    def setUp(self):
        super().setUp()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")
        self.principal_group, _ = Group.objects.get_or_create(name="Principal")
        self.student_group, _ = Group.objects.get_or_create(name="StudentPortal")

        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.admin_group)

        self.principal_user = User.objects.create_user(
            username="principal@test.com", email="principal@test.com", password="password"
        )
        self.principal_user.groups.add(self.principal_group)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.teacher_group)

        self.student_user = User.objects.create_user(
            username="student@test.com", email="student@test.com", password="password"
        )
        self.student_user.groups.add(self.student_group)

        self.session = Session.objects.create(
            name="CSS Morning Batch 2026",
            status="Active",
            roll_prefix="CSS-M",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="Batch 1",
            max_capacity=50,
        )

        self.subject = Subject.objects.create(
            name="Programming Fundamental",
            session=self.session
        )

    def test_subject_create_page_loads_for_allowed_role(self):
        """Subject create page loads for Admin and Principal, blocks Student."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:subject_create"))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="principal@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:subject_create"))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="student@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:subject_create"))
        self.assertEqual(response.status_code, 404)

    def test_valid_subject_post_creates_subject(self):
        """Valid subject POST creates a subject and redirects to session detail."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "name": "Database Systems",
            "code": "CS301",
            "session": self.session.pk,
            "is_active": True,
            "description": "Intro to DB"
        }
        response = self.client.post(reverse("admin_panel:academics:subject_create"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Subject.objects.filter(name="Database Systems").exists())

    def test_invalid_subject_post_fails(self):
        """Invalid subject POST shows form errors and does not create subject."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "name": "Programming Fundamental",
            "code": "CS101",
            "session": self.session.pk,
            "is_active": True
        }
        initial_count = Subject.objects.count()
        response = self.client.post(reverse("admin_panel:academics:subject_create"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Subject.objects.count(), initial_count)
        self.assertFormError(response, "form", None, "Subject with this Name and Session already exists.")

    def test_subject_edit_updates_subject(self):
        """Subject edit updates an existing subject's details."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "name": "Advanced Programming",
            "code": "CS102",
            "session": self.session.pk,
            "is_active": True,
            "description": "Updated description"
        }
        response = self.client.post(
            reverse("admin_panel:academics:subject_edit", kwargs={"pk": self.subject.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        self.subject.refresh_from_db()
        self.assertEqual(self.subject.name, "Advanced Programming")
        self.assertEqual(self.subject.description, "Updated description")

    def test_teacher_assignment_create_page_loads_for_allowed_role(self):
        """Teacher assignment create page loads for allowed role (Admin, Principal)."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:assignment_create"))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="student@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:assignment_create"))
        self.assertEqual(response.status_code, 404)

    def test_teacher_dropdown_only_includes_teachers(self):
        """TeacherAssignmentForm teacher dropdown only lists users in Teacher group."""
        form = TeacherAssignmentForm()
        teacher_choices = list(form.fields["teacher"].queryset)
        self.assertIn(self.teacher_user, teacher_choices)
        self.assertNotIn(self.admin_user, teacher_choices)
        self.assertNotIn(self.student_user, teacher_choices)

    def test_valid_teacher_assignment_post(self):
        """Valid teacher assignment POST creates assignment and redirects."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "teacher": self.teacher_user.pk,
            "session": self.session.pk,
            "subject": self.subject.pk,
            "assigned_from": "2026-06-01",
            "assigned_until": "2026-12-01",
            "is_active": True
        }
        response = self.client.post(reverse("admin_panel:academics:assignment_create"), post_data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(TeacherAssignment.objects.filter(teacher=self.teacher_user, session=self.session).exists())

    def test_invalid_teacher_assignment_post(self):
        """Invalid teacher assignment POST shows errors."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "teacher": self.teacher_user.pk,
            "session": self.session.pk,
            "subject": self.subject.pk,
            "assigned_from": "2026-06-01",
            "assigned_until": "2026-05-01",
            "is_active": True
        }
        initial_count = TeacherAssignment.objects.count()
        response = self.client.post(reverse("admin_panel:academics:assignment_create"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(TeacherAssignment.objects.count(), initial_count)
        self.assertFormError(response, "form", None, "End date must be on or after start date.")

    def test_teacher_assignment_edit_updates_assignment(self):
        """Teacher assignment edit updates the assignment."""
        assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            subject=self.subject,
            assigned_from="2026-06-01",
            is_active=True
        )
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "teacher": self.teacher_user.pk,
            "session": self.session.pk,
            "subject": self.subject.pk,
            "assigned_from": "2026-06-02",
            "assigned_until": "2026-11-30",
            "is_active": False
        }
        response = self.client.post(
            reverse("admin_panel:academics:assignment_edit", kwargs={"pk": assignment.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        assignment.refresh_from_db()
        self.assertEqual(str(assignment.assigned_from), "2026-06-02")
        self.assertFalse(assignment.is_active)

    def test_teacher_assignment_delete_requires_post(self):
        """Teacher assignment delete blocks GET request."""
        assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            subject=self.subject,
            assigned_from="2026-06-01",
            is_active=True
        )
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:assignment_delete", kwargs={"pk": assignment.pk}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_assignment_delete_removes_assignment(self):
        """Teacher assignment delete removes the assignment record."""
        assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            subject=self.subject,
            assigned_from="2026-06-01",
            is_active=True
        )
        self.client.login(username="admin@test.com", password="password")
        response = self.client.post(reverse("admin_panel:academics:assignment_delete", kwargs={"pk": assignment.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(TeacherAssignment.objects.filter(pk=assignment.pk).exists())

    def test_session_delete_requires_post(self):
        """Session delete blocks GET request."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_delete", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_session_delete_uses_soft_delete(self):
        """Session delete marks is_deleted=True and excludes from default manager."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.post(reverse("admin_panel:academics:session_delete", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 302)
        
        self.session.refresh_from_db()
        self.assertTrue(self.session.is_deleted)
        self.assertNotIn(self.session, Session.objects.all())
        self.assertIn(self.session, Session.all_objects.all())

    def test_session_delete_blocks_if_has_enrollments(self):
        """Session delete fails and redirects if session has active/past enrollments."""
        from apps.students.models import Student, Enrollment
        student = Student.objects.create(full_name="Test Student", roll_number="TEST1")
        Enrollment.objects.create(student=student, session=self.session, status="Active")

        self.client.login(username="admin@test.com", password="password")
        response = self.client.post(reverse("admin_panel:academics:session_delete", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 302)
        
        self.session.refresh_from_db()
        self.assertFalse(self.session.is_deleted)

    def test_session_enrollments_loads_for_allowed_roles(self):
        """session_enrollments loads for Admin, Principal, and Registrar."""
        # Admin
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)

        # Principal
        self.client.login(username="principal@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)

        # Registrar
        registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        registrar_user = User.objects.create_user(
            username="registrar_unique@test.com", email="registrar_unique@test.com", password="password"
        )
        registrar_user.groups.add(registrar_group)
        self.client.login(username="registrar_unique@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)

    def test_session_enrollments_blocks_unauthorized_roles(self):
        """session_enrollments blocks unauthorized roles (Student)."""
        self.client.login(username="student@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_view_only_assigned_session_enrollments(self):
        """Teacher can view enrollments for assigned session, gets 404 for unassigned session."""
        TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            is_active=True,
            assigned_from="2026-06-01"
        )
        self.client.login(username="teacher@test.com", password="password")
        # Allowed since assigned
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)

        # Unassigned session
        other_session = Session.objects.create(
            name="CSS Evening 2026",
            status="Active",
            roll_prefix="CSS-E",
            fee=1200,
            session_type="time_period",
            session_category="CSS"
        )
        response = self.client.get(reverse("admin_panel:academics:session_enrollments", kwargs={"pk": other_session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_enrollment_search_and_filters_work(self):
        """Enrollment search and status filtering returns correct subsets."""
        from apps.students.models import Student, Enrollment
        student1 = Student.objects.create(full_name="Ahmad Ali", roll_number="AA-01")
        student2 = Student.objects.create(full_name="Fatima Bibi", roll_number="FB-02")
        Enrollment.objects.create(student=student1, session=self.session, status="Active")
        Enrollment.objects.create(student=student2, session=self.session, status="Frozen")

        self.client.login(username="admin@test.com", password="password")
        
        # Test Search
        response = self.client.get(
            reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}),
            {"search": "Ahmad"}
        )
        self.assertContains(response, "Ahmad Ali")
        self.assertNotContains(response, "Fatima Bibi")

        # Test Status filter
        response = self.client.get(
            reverse("admin_panel:academics:session_enrollments", kwargs={"pk": self.session.pk}),
            {"status": "Frozen"}
        )
        self.assertContains(response, "Fatima Bibi")
        self.assertNotContains(response, "Ahmad Ali")


class SessionRevenueTests(TestCase):
    def setUp(self):
        super().setUp()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.principal_group, _ = Group.objects.get_or_create(name="Principal")
        self.registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")
        self.student_group, _ = Group.objects.get_or_create(name="StudentPortal")

        self.admin_user = User.objects.create_user(
            username="admin_rev@test.com", email="admin_rev@test.com", password="password"
        )
        self.admin_user.groups.add(self.admin_group)

        self.principal_user = User.objects.create_user(
            username="principal_rev@test.com", email="principal_rev@test.com", password="password"
        )
        self.principal_user.groups.add(self.principal_group)

        self.registrar_user = User.objects.create_user(
            username="registrar_rev@test.com", email="registrar_rev@test.com", password="password"
        )
        self.registrar_user.groups.add(self.registrar_group)

        self.teacher_user = User.objects.create_user(
            username="teacher_rev@test.com", email="teacher_rev@test.com", password="password"
        )
        self.teacher_user.groups.add(self.teacher_group)

        self.student_user = User.objects.create_user(
            username="student_rev@test.com", email="student_rev@test.com", password="password"
        )
        self.student_user.groups.add(self.student_group)

        self.session = Session.objects.create(
            name="CSS Morning Batch 2026 Revenue",
            status="Active",
            roll_prefix="CSS-M-REV",
            fee=Decimal("5000.00"),
            registration_fee=Decimal("500.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="Batch 1",
            max_capacity=50,
        )

    def test_session_revenue_loads_for_admin(self):
        """Verify session revenue page loads for Admin role."""
        self.client.login(username="admin_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "academics/session_revenue.html")

    def test_session_revenue_blocks_unauthorized_roles(self):
        """Verify that roles other than Admin (Principal, Registrar, Teacher, Student) are blocked."""
        # Principal
        self.client.login(username="principal_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

        # Registrar
        self.client.login(username="registrar_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

        # Teacher
        self.client.login(username="teacher_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

        # Student
        self.client.login(username="student_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_session_revenue_no_mutation_allowed(self):
        """Verify that GET requests do not modify any financial database objects."""
        self.client.login(username="admin_rev@test.com", password="password")
        from apps.finance.models import Payment, Refund
        initial_payments = Payment.objects.count()
        initial_refunds = Refund.objects.count()

        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Payment.objects.count(), initial_payments)
        self.assertEqual(Refund.objects.count(), initial_refunds)

    def test_session_revenue_selector_and_data(self):
        """Verify that monthly calculations and ledger rows are loaded correctly."""
        from apps.students.models import Student, Enrollment
        from apps.finance.models import Payment, Refund

        # Create student and enrollment
        student = Student.objects.create(full_name="Zeeshan Ali", roll_number="CSS-REV-01")
        enrollment = Enrollment.objects.create(
            student=student,
            session=self.session,
            status="Active",
            fee=Decimal("4500.00"),
            registration_fee=Decimal("400.00"),
            discount=Decimal("200.00")
        )

        today = timezone.localdate()

        # Create confirmed payment
        payment = Payment.objects.create(
            enrollment=enrollment,
            amount=Decimal("3000.00"),
            payment_date=today,
            payment_status="confirmed",
            is_late_fee_payment=False,
            receipt_number="RCP-REV-001"
        )

        # Create processed refund
        refund = Refund.objects.create(
            payment=payment,
            amount=Decimal("500.00"),
            reason="Overpayment",
            refund_date=today,
            status="processed"
        )

        self.client.login(username="admin_rev@test.com", password="password")
        response = self.client.get(
            reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}),
            {"year": str(today.year), "month": str(today.month)}
        )
        self.assertEqual(response.status_code, 200)

        # Confirm monthly cards rendered with correct values
        self.assertContains(response, "PKR 3000.00")  # Tuition
        self.assertContains(response, "PKR 500.00")   # Refund
        self.assertContains(response, "PKR 2500.00")  # Net

        # Confirm ledger row for student
        self.assertContains(response, "Zeeshan Ali")
        # Expected payable: 4500 + 400 - 200 = 4700.00
        self.assertContains(response, "PKR 4700.00")
        # Paid: 3000
        self.assertContains(response, "PKR 3000.00")
        # Outstanding balance: 4700 - 3000 + 500 = 2200.00
        self.assertContains(response, "PKR 2200.00")

    def test_session_revenue_empty_state(self):
        """Verify empty warning is displayed when no enrollments exist."""
        self.client.login(username="admin_rev@test.com", password="password")
        response = self.client.get(reverse("admin_panel:academics:session_revenue", kwargs={"pk": self.session.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No enrollments or financial transactions exist for this session.")



