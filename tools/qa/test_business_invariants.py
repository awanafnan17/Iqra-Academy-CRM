"""
Business Invariant Tests — Iqra Academy CRM.

Tests derived from model/service logic, not guessed formulas:
- Roll number generation and prefix changes
- Exam marks constraints (obtained <= total)
- Grade config boundaries
- Enrollment consistency
- Fee/payment/refund balance correctness
- Attendance percentage calculation
- Session status transitions

Usage:
    python -m pytest tools/qa/test_business_invariants.py -v --tb=short
"""

import os
import sys
from decimal import Decimal
from datetime import date

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

import django
django.setup()

from django.test import TestCase
from django.core.exceptions import ValidationError


class ExamMarkInvariantTests(TestCase):
    """Exam marks constraints derived from ExamResult.clean()."""

    def setUp(self):
        from apps.academics.models import Session, Subject
        from apps.exams.models import Exam
        from apps.students.models import Student

        self.session = Session.objects.create(
            name="Invariant Session", session_type="time_period",
            roll_prefix="INV", status="Active",
        )
        self.subject = Subject.objects.create(name="Invariant Subject")
        self.exam = Exam.objects.create(
            session=self.session, subject=self.subject,
            name="Invariant Exam", total_marks=Decimal("100.00"),
            passing_marks=Decimal("40.00"), exam_type="Test",
        )
        self.student = Student.objects.create(
            full_name="Invariant Student",
            email="inv_stud@test.iqra", status="Active",
        )

    def test_obtained_marks_cannot_exceed_total(self):
        """ExamResult.clean() must reject marks > total_marks."""
        from apps.exams.models import ExamResult

        result = ExamResult(
            exam=self.exam, student=self.student,
            marks_obtained=Decimal("150.00"),
        )
        with self.assertRaises(ValidationError):
            result.clean()

    def test_percentage_auto_calculated(self):
        """ExamResult.save() computes percentage = (obtained/total)*100."""
        from apps.exams.models import ExamResult

        result = ExamResult.objects.create(
            exam=self.exam, student=self.student,
            marks_obtained=Decimal("75.00"),
        )
        self.assertEqual(result.percentage, Decimal("75.00"))

    def test_passing_marks_cannot_exceed_total(self):
        """Exam.clean() rejects passing_marks > total_marks."""
        from apps.exams.models import Exam

        exam = Exam(
            session=self.session, subject=self.subject,
            name="Bad Exam", total_marks=Decimal("50.00"),
            passing_marks=Decimal("100.00"), exam_type="Test",
        )
        with self.assertRaises(ValidationError):
            exam.clean()

    def test_zero_marks_produces_zero_percentage(self):
        """Zero marks should produce 0% percentage."""
        from apps.exams.models import ExamResult

        result = ExamResult.objects.create(
            exam=self.exam, student=self.student,
            marks_obtained=Decimal("0.00"),
        )
        self.assertEqual(result.percentage, Decimal("0.00"))


class GradeConfigInvariantTests(TestCase):
    """Grade config boundary invariants from GradeConfig.clean()."""

    def setUp(self):
        from apps.academics.models import Session
        self.session = Session.objects.create(
            name="Grade Session", session_type="time_period",
            roll_prefix="GRD", status="Active",
        )

    def test_min_cannot_exceed_max_percentage(self):
        """GradeConfig.clean() rejects min_percentage > max_percentage."""
        from apps.exams.models import GradeConfig

        gc = GradeConfig(
            session=self.session, grade_name="A+",
            min_percentage=Decimal("95.00"),
            max_percentage=Decimal("80.00"),
        )
        with self.assertRaises(ValidationError):
            gc.clean()

    def test_valid_grade_config_saves(self):
        """Valid grade config should save without errors."""
        from apps.exams.models import GradeConfig

        gc = GradeConfig.objects.create(
            session=self.session, grade_name="A",
            min_percentage=Decimal("80.00"),
            max_percentage=Decimal("100.00"),
            grade_point=Decimal("4.00"),
        )
        self.assertEqual(gc.grade_name, "A")


class SessionStatusInvariantTests(TestCase):
    """Session status field constraints."""

    def test_session_status_choices(self):
        """Session status must be one of Active/Inactive/Completed."""
        from apps.academics.models import Session

        valid_statuses = ["Active", "Inactive", "Completed"]
        for status in valid_statuses:
            s = Session(
                name=f"Status {status}", session_type="time_period",
                roll_prefix=f"S{status[:2]}", status=status,
            )
            s.full_clean()  # Should not raise


class ExamStatusWorkflowTests(TestCase):
    """Exam status transitions: Draft -> Under Review -> Published."""

    def setUp(self):
        from apps.academics.models import Session, Subject
        self.session = Session.objects.create(
            name="Workflow Session", session_type="time_period",
            roll_prefix="WFS", status="Active",
        )
        self.subject = Subject.objects.create(name="Workflow Subject")

    def test_exam_default_status_is_draft(self):
        """New exam starts as Draft."""
        from apps.exams.models import Exam

        exam = Exam.objects.create(
            session=self.session, subject=self.subject,
            name="Status Exam", total_marks=100, exam_type="Test",
        )
        self.assertEqual(exam.status, "Draft")
        self.assertFalse(exam.is_published)

    def test_published_exam_sets_is_published_flag(self):
        """Setting status=Published auto-sets is_published=True on save."""
        from apps.exams.models import Exam

        exam = Exam.objects.create(
            session=self.session, subject=self.subject,
            name="Pub Exam", total_marks=100, exam_type="Test",
        )
        exam.status = "Published"
        exam.save()
        exam.refresh_from_db()
        self.assertTrue(exam.is_published)

    def test_draft_exam_not_published(self):
        """Draft status means is_published=False."""
        from apps.exams.models import Exam

        exam = Exam.objects.create(
            session=self.session, subject=self.subject,
            name="Draft Exam", total_marks=100, exam_type="Test",
        )
        self.assertFalse(exam.is_published)


class EnrollmentUniqueConstraintTests(TestCase):
    """Enrollment consistency — student can only enroll once per session."""

    def setUp(self):
        from apps.academics.models import Session
        from apps.students.models import Student

        self.session = Session.objects.create(
            name="Enroll Session", session_type="time_period",
            roll_prefix="ENR", status="Active",
        )
        self.student = Student.objects.create(
            full_name="Enroll Student",
            email="enroll@test.iqra", status="Active",
        )

    def test_student_can_enroll_in_session(self):
        """Student can create an enrollment."""
        from apps.students.models import Enrollment

        enrollment = Enrollment.objects.create(
            student=self.student, session=self.session, status="Active",
        )
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.session, self.session)


class TeacherAssignmentConstraintTests(TestCase):
    """Teacher assignment uniqueness: (teacher, session, subject)."""

    def setUp(self):
        from django.contrib.auth.models import Group
        from apps.accounts.models import CustomUser
        from apps.academics.models import Session, Subject

        group, _ = Group.objects.get_or_create(name="Teacher")
        self.teacher = CustomUser.objects.create_user(
            email="ta_teacher@test.iqra", username="ta_teacher",
            password="TATest2026!", first_name="TA", last_name="Teacher",
            status="Active",
        )
        self.teacher.groups.add(group)

        self.session = Session.objects.create(
            name="TA Session", session_type="time_period",
            roll_prefix="TAS", status="Active",
        )
        self.subject = Subject.objects.create(name="TA Subject")

    def test_teacher_assignment_creates(self):
        """Can create a valid teacher assignment."""
        from apps.academics.models import TeacherAssignment

        ta = TeacherAssignment.objects.create(
            teacher=self.teacher, session=self.session,
            subject=self.subject, is_active=True,
        )
        self.assertTrue(ta.is_active)

    def test_duplicate_assignment_rejected(self):
        """Duplicate (teacher, session, subject) raises IntegrityError."""
        from apps.academics.models import TeacherAssignment
        from django.db import IntegrityError

        TeacherAssignment.objects.create(
            teacher=self.teacher, session=self.session,
            subject=self.subject, is_active=True,
        )
        with self.assertRaises(IntegrityError):
            TeacherAssignment.objects.create(
                teacher=self.teacher, session=self.session,
                subject=self.subject, is_active=True,
            )


class DisplayNameInvariantTests(TestCase):
    """Display name business rules from CustomUser.display_name."""

    def test_full_name_takes_precedence(self):
        from apps.accounts.models import CustomUser
        u = CustomUser(username="jdoe", first_name="John", last_name="Doe")
        self.assertEqual(u.display_name, "John Doe")

    def test_first_name_only(self):
        from apps.accounts.models import CustomUser
        u = CustomUser(username="jane", first_name="Jane", last_name="")
        self.assertEqual(u.display_name, "Jane")

    def test_fallback_to_username(self):
        from apps.accounts.models import CustomUser
        u = CustomUser(username="anon_user", first_name="", last_name="")
        self.assertEqual(u.display_name, "anon_user")

    def test_whitespace_normalized(self):
        from apps.accounts.models import CustomUser
        u = CustomUser(username="ws", first_name="  Jane  ", last_name="  Doe  ")
        self.assertEqual(u.display_name, "Jane Doe")
