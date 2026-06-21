import datetime
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session
from apps.attendance.models import AttendanceRecord, AttendanceLock
from apps.attendance.services import AttendanceService
from apps.students.models import Student, Enrollment

User = get_user_model()


class AttendanceWorkflowTests(TestCase):
    def setUp(self):
        super().setUp()
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")
        self.student_group, _ = Group.objects.get_or_create(name="StudentPortal")

        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="password"
        )
        self.admin_user.groups.add(self.admin_group)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="password"
        )
        self.teacher_user.groups.add(self.teacher_group)

        self.student_user = User.objects.create_user(
            username="student@test.com", email="student@test.com", password="password"
        )
        self.student_user.groups.add(self.student_group)

        self.session = Session.objects.create(
            name="CSS Morning 2026",
            status="Active",
            roll_prefix="CSS-M",
            fee=1000,
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=30),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            due_day=10
        )

        self.student = Student.objects.create(
            full_name="Fatima Khan",
            roll_number="CSS-01"
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active"
        )

    def test_attendance_overview_loads_for_allowed_roles(self):
        """Attendance overview page loads for Admin, blocks Teacher and Student (due to admin panel prefix constraints)."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_overview"))
        self.assertEqual(response.status_code, 200)

        self.client.login(username="teacher@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_overview"))
        self.assertEqual(response.status_code, 404)

        self.client.login(username="student@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_overview"))
        self.assertEqual(response.status_code, 404)

    def test_teacher_can_access_allowed_attendance_views(self):
        """Teacher can access attendance mark and sheet views via the teacher panel prefix."""
        self.client.login(username="teacher@test.com", password="password")
        
        # Test mark page loads via teacher panel
        response = self.client.get(
            reverse("teacher_panel:attendance_mark", kwargs={"session_id": self.session.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

        # Test sheet page loads via teacher panel
        today_str = timezone.localdate().isoformat()
        response = self.client.get(
            reverse("teacher_panel:attendance_sheet", kwargs={"session_id": self.session.pk, "date": today_str})
        )
        self.assertEqual(response.status_code, 200)

    def test_attendance_mark_page_loads_with_students(self):
        """Mark attendance page loads and contains the enrolled student."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": self.session.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

    def test_valid_post_creates_attendance_records(self):
        """POST request successfully marks student attendance."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "date": timezone.localdate().isoformat(),
            f"status_{self.student.pk}": "Present",
            f"remarks_{self.student.pk}": "Early arrival"
        }
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302) # redirects to sheet
        
        record = AttendanceRecord.objects.get(student=self.student, session=self.session)
        self.assertEqual(record.status, "Present")
        self.assertEqual(record.remarks, "Early arrival")

    def test_invalid_status_does_not_save_and_shows_error(self):
        """Invalid status values cause the view to return errors and block saving."""
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "date": timezone.localdate().isoformat(),
            f"status_{self.student.pk}": "SuperPresent",  # invalid choice
        }
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 200) # Form re-renders with errors
        self.assertFalse(AttendanceRecord.objects.filter(student=self.student, session=self.session).exists())

    def test_future_date_is_blocked_by_service_rules(self):
        """Future date is rejected by view constraints / service constraints."""
        self.client.login(username="admin@test.com", password="password")
        future_date = (timezone.localdate() + datetime.timedelta(days=1)).isoformat()
        post_data = {
            "date": future_date,
            f"status_{self.student.pk}": "Present",
        }
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AttendanceRecord.objects.filter(student=self.student, session=self.session).exists())

    def test_locked_date_blocks_edits(self):
        """Editing attendance on locked date redirects and throws error."""
        today = timezone.localdate()
        AttendanceLock.objects.create(
            session=self.session,
            date=today,
            locked_by=self.admin_user,
            reason="Locked test"
        )
        
        self.client.login(username="admin@test.com", password="password")
        post_data = {
            "date": today.isoformat(),
            f"status_{self.student.pk}": "Present"
        }
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302) # redirects immediately
        
        # Verify no record created
        self.assertFalse(AttendanceRecord.objects.filter(student=self.student, session=self.session).exists())

    def test_lock_action_requires_post(self):
        """GET request to lock attendance view is blocked."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_lock", kwargs={"session_id": self.session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_lock_action_creates_attendance_lock(self):
        """POST request to lock attendance creates AttendanceLock record."""
        self.client.login(username="admin@test.com", password="password")
        today_str = timezone.localdate().isoformat()
        post_data = {
            "date": today_str,
            "reason": "End of day finalize"
        }
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_lock", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        
        lock_exists = AttendanceLock.objects.filter(session=self.session, date=timezone.localdate()).exists()
        self.assertTrue(lock_exists)

    def test_unlock_action_requires_post(self):
        """GET request to unlock attendance view is blocked."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:attendance_unlock", kwargs={"session_id": self.session.pk}))
        self.assertEqual(response.status_code, 404)

    def test_unlock_action_removes_lock(self):
        """POST request to unlock attendance removes the AttendanceLock record."""
        today = timezone.localdate()
        lock = AttendanceLock.objects.create(
            session=self.session,
            date=today,
            locked_by=self.admin_user,
            reason="Locked test"
        )
        
        self.client.login(username="admin@test.com", password="password")
        post_data = {"date": today.isoformat()}
        response = self.client.post(
            reverse("admin_panel:attendance:attendance_unlock", kwargs={"session_id": self.session.pk}),
            post_data
        )
        self.assertEqual(response.status_code, 302)
        
        lock_exists = AttendanceLock.objects.filter(session=self.session, date=today).exists()
        self.assertFalse(lock_exists)

    def test_sheet_page_shows_records(self):
        """Sheet page loads and displays logs for marked records."""
        today = timezone.localdate()
        rec = AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            date=today,
            status="Present",
            marked_by=self.admin_user
        )
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(
            reverse("admin_panel:attendance:attendance_sheet", kwargs={"session_id": self.session.pk, "date": today.isoformat()})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")
        self.assertContains(response, "Present")

    def test_empty_sheet_renders_empty_state(self):
        """Sheet page renders fallback empty warning if no records are found."""
        self.client.login(username="admin@test.com", password="password")
        today_str = timezone.localdate().isoformat()
        response = self.client.get(
            reverse("admin_panel:attendance:attendance_sheet", kwargs={"session_id": self.session.pk, "date": today_str})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No attendance records found for this date.")

    def test_attendance_analytics_loads_for_admin_and_principal(self):
        """Attendance analytics page loads successfully for Admin."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(
            reverse("admin_panel:attendance:attendance_analytics", kwargs={"session_id": self.session.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_teacher_attendance_analytics_restrictions(self):
        """Teacher can only view analytics for assigned session."""
        from apps.academics.models import TeacherAssignment
        self.client.login(username="teacher@test.com", password="password")
        
        # Unassigned session gets 404
        response = self.client.get(
            reverse("teacher_panel:attendance_analytics", kwargs={"session_id": self.session.pk})
        )
        self.assertEqual(response.status_code, 404)

        # Assigned session loads successfully
        TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            is_active=True,
            assigned_from="2026-06-01"
        )
        response = self.client.get(
            reverse("teacher_panel:attendance_analytics", kwargs={"session_id": self.session.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_empty_analytics_state_renders_cleanly(self):
        """Analytics page renders empty state correctly when there are no records."""
        self.client.login(username="admin@test.com", password="password")
        response = self.client.get(
            reverse("admin_panel:attendance:attendance_analytics", kwargs={"session_id": self.session.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Attendance Logs Found")

    def test_low_attendance_report_loads_and_filters_work(self):
        """Low attendance report page loads and supports threshold and session filters."""
        # Create a record of Present and Absent to get exactly 50.00% attendance
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            date=timezone.localdate() - datetime.timedelta(days=1),
            status="Present",
            marked_by=self.admin_user
        )
        AttendanceRecord.objects.create(
            session=self.session,
            student=self.student,
            date=timezone.localdate(),
            status="Absent",
            marked_by=self.admin_user
        )

        self.client.login(username="admin@test.com", password="password")
        
        # Loads with default threshold (75%) which includes 50%
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

        # High threshold (90%) includes them
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"), {"threshold": "90"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

        # Low threshold (40%) excludes them
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"), {"threshold": "40"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Fatima Khan")

        # Session filter matches
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"), {"session_id": self.session.pk})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Fatima Khan")

    def test_low_attendance_report_blocks_unauthorized_roles(self):
        """Student and Teacher are blocked from low attendance report."""
        self.client.login(username="student@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"))
        self.assertEqual(response.status_code, 404)

        self.client.login(username="teacher@test.com", password="password")
        response = self.client.get(reverse("admin_panel:attendance:low_attendance_report"))
        self.assertEqual(response.status_code, 404)
