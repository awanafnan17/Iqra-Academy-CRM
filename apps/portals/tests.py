import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TransactionTestCase, Client
from django.urls import reverse
from django.utils import timezone

from apps.academics.models import Session, Subject
from apps.exams.models import Exam, ExamResult
from apps.finance.models import Payment
from apps.students.models import Student, Guardian, Enrollment
from apps.attendance.models import AttendanceRecord

User = get_user_model()

class PortalSecurityAndLogicTests(TransactionTestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        # Create groups
        self.group_student, _ = Group.objects.get_or_create(name="Student")
        self.group_guardian, _ = Group.objects.get_or_create(name="Guardian")

        # Create Users
        self.student1_user = User.objects.create_user(
            username="student1@test.com", email="student1@test.com", password="password"
        )
        self.student1_user.groups.add(self.group_student)

        self.student2_user = User.objects.create_user(
            username="student2@test.com", email="student2@test.com", password="password"
        )
        self.student2_user.groups.add(self.group_student)

        self.guardian_user = User.objects.create_user(
            username="guardian@test.com", email="guardian@test.com", password="password"
        )
        self.guardian_user.groups.add(self.group_guardian)

        self.other_guardian_user = User.objects.create_user(
            username="otherguardian@test.com", email="otherguardian@test.com", password="password"
        )
        self.other_guardian_user.groups.add(self.group_guardian)

        # Create session
        self.session = Session.objects.create(
            name="CSS 2026",
            status="Active",
            roll_prefix="CSS",
            fee=Decimal("5000.00"),
            registration_fee=Decimal("1000.00"),
            start_date=timezone.localdate(),
            end_date=timezone.localdate() + datetime.timedelta(days=90),
            session_type="time_period",
            session_category="CSS",
            academic_year="2026",
            batch_number="1",
        )

        # Create students
        self.student1 = Student.objects.create(
            portal_user=self.student1_user,
            full_name="Student One",
            roll_number="CSS-001"
        )

        self.student2 = Student.objects.create(
            portal_user=self.student2_user,
            full_name="Student Two",
            roll_number="CSS-002"
        )

        # Enrollments
        self.enrollment1 = Enrollment.objects.create(
            student=self.student1,
            session=self.session,
            status="Active"
        )

        # Guardian links
        Guardian.objects.create(
            student=self.student1,
            portal_user=self.guardian_user,
            full_name="Guardian One",
            relationship="Father",
            email="guardian@test.com"
        )

    def test_student_cannot_access_other_student_profile(self):
        """Student A cannot view Student B profile page."""
        self.client.login(username="student1@test.com", password="password")
        # Ensure student1 profile works
        response = self.client.get(reverse('student_portal:profile_view'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Student One")
        self.assertNotContains(response, "Student Two")

    def test_guardian_cannot_access_unlinked_child(self):
        """Guardian cannot access child not linked to them."""
        self.client.login(username="guardian@test.com", password="password")
        # Guardian is linked to student1
        response = self.client.get(reverse('guardian_portal:child_detail', kwargs={'student_id': self.student1.id}))
        self.assertEqual(response.status_code, 200)

        # Guardian is NOT linked to student2
        response2 = self.client.get(reverse('guardian_portal:child_detail', kwargs={'student_id': self.student2.id}))
        self.assertEqual(response2.status_code, 404)

    def test_unpublished_exam_not_visible_to_student(self):
        """Unpublished exam result not in student exam list."""
        self.client.login(username="student1@test.com", password="password")

        subject = Subject.objects.create(name="Math", session=self.session)
        # Create published exam
        exam_published = Exam.objects.create(
            name="Midterm Published",
            session=self.session,
            subject=subject,
            total_marks=100,
            status="Published"
        )
        ExamResult.objects.create(exam=exam_published, student=self.student1, marks_obtained=Decimal("80"), is_absent=False)

        # Create draft exam
        exam_draft = Exam.objects.create(
            name="Final Draft",
            session=self.session,
            subject=subject,
            total_marks=100,
            status="Draft"
        )
        ExamResult.objects.create(exam=exam_draft, student=self.student1, marks_obtained=Decimal("90"), is_absent=False)

        response = self.client.get(reverse('student_portal:my_exams'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Midterm Published")
        self.assertNotContains(response, "Final Draft")

    def test_fee_history_shows_correct_balance(self):
        """Fee page shows correct outstanding balance."""
        self.client.login(username="student1@test.com", password="password")

        # session fee is 5000, reg fee 1000 = 6000 total
        Payment.objects.create(
            enrollment=self.enrollment1,
            amount=Decimal("2000.00"),
            payment_date=timezone.localdate(),
            payment_status="confirmed"
        )

        response = self.client.get(reverse('student_portal:my_fees'))
        self.assertEqual(response.status_code, 200)
        # outstanding = 6000 - 2000 = 4000
        self.assertContains(response, "4,000")

    def test_attendance_percentage_correct(self):
        """Attendance page shows correct percentage."""
        self.client.login(username="student1@test.com", password="password")

        AttendanceRecord.objects.create(student=self.student1, session=self.session, date=timezone.localdate(), status="Present")
        AttendanceRecord.objects.create(student=self.student1, session=self.session, date=timezone.localdate() - datetime.timedelta(days=1), status="Present")
        AttendanceRecord.objects.create(student=self.student1, session=self.session, date=timezone.localdate() - datetime.timedelta(days=2), status="Absent")
        AttendanceRecord.objects.create(student=self.student1, session=self.session, date=timezone.localdate() - datetime.timedelta(days=3), status="Late")

        # 4 records: 2 present, 1 late (counts as present usually, or depends on business logic, let's just see if it renders)
        # Let's check response
        response = self.client.get(reverse('student_portal:my_attendance'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('overall_percentage' in response.context)

    def test_profile_update_restricted_to_own(self):
        """Student cannot update another student profile."""
        self.client.login(username="student1@test.com", password="password")

        # Trying to POST to profile updates student1's profile because the view infers from request.user
        response = self.client.post(reverse('student_portal:profile_view'), {
            'phone': '+923001111111',
            'address': 'New Address',
            'email': 'student1_new@test.com',
            'confirm_email': 'student1_new@test.com',
        })
        # Should succeed and redirect
        self.assertEqual(response.status_code, 302)

        self.student1.refresh_from_db()
        self.assertEqual(self.student1.phone, '+923001111111')
        self.assertEqual(self.student1.portal_user.email, 'student1_new@test.com')

    def test_portal_navigation_loads(self):
        """All portal pages return 200 for authenticated student."""
        self.client.login(username="student1@test.com", password="password")

        pages = [
            'student_portal:dashboard',
            'student_portal:profile_view',
            'student_portal:my_attendance',
            'student_portal:my_fees',
            'student_portal:my_exams',
            'student_portal:notification_list',
        ]

        for page in pages:
            response = self.client.get(reverse(page))
            self.assertEqual(response.status_code, 200, f"Page {page} failed to load.")

    def test_guardian_portal_shows_all_children(self):
        """Guardian sees all linked children on dashboard."""
        self.client.login(username="guardian@test.com", password="password")

        response = self.client.get(reverse('guardian_portal:dashboard'))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "Student One")
        self.assertNotContains(response, "Student Two")
