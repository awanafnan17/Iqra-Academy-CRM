import datetime
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from django.test import TestCase, override_settings
from django.urls import path, reverse, include
from django.utils import timezone

from apps.academics.models import Session, Subject, TeacherAssignment
from apps.students.models import Student, Enrollment, Guardian
from apps.exams.models import Exam, ExamResult, GradeConfig
from apps.exams import views
from apps.portals import views_student, views_parent
from apps.dashboard import views as dashboard_views
from apps.exams.services import (
    create_exam,
    publish_exam,
    record_exam_result,
    update_exam_result,
    bulk_result_entry,
    calculate_exam_statistics,
    _get_grade_for_percentage,
    _recalculate_exam_ranking,
    _validate_teacher_scope,
)

User = get_user_model()

# Custom URLConf for tests to resolve routing prefixes that bypass PanelAccessMiddleware role checks properly
urlpatterns = [
    # Specific paths first
    path("panel/admin/exams/", views.exam_list, name="exam_list"),
    path("panel/admin/exams/<int:pk>/", views.exam_detail, name="exam_detail"),
    path("panel/admin/exams/<int:pk>/publish/", views.exam_publish, name="exam_publish"),
    path("panel/admin/exams/<int:pk>/review/", views.exam_review, name="exam_review"),
    path("portal/student/exams/", views.exam_list, name="student_exam_list"),
    path("portal/student/exams/<int:pk>/", views.exam_detail, name="student_exam_detail"),
    path("portal/guardian/exams/", views.exam_list, name="guardian_exam_list"),
    path("portal/guardian/exams/<int:pk>/", views.exam_detail, name="guardian_exam_detail"),
    path("portal/student/transcript/", views_student.student_transcript, name="student_transcript"),
    path("portal/guardian/child/<int:student_id>/transcript/", views_parent.child_transcript, name="child_transcript"),
    path("panel/admin/session/<int:pk>/results/", dashboard_views.session_result_summary, name="session_result_summary"),

    # Include namespaces to prevent NoReverseMatch in templates
    path("accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("portal/student/", include("apps.portals.urls_student", namespace="student_portal")),
    path("portal/guardian/", include("apps.portals.urls_parent", namespace="guardian_portal")),
    path("panel/admin/", include("apps.dashboard.urls_admin", namespace="admin_panel")),
    path("panel/admin/reports/", include("apps.reports.urls", namespace="reports")),
]


@override_settings(ROOT_URLCONF="apps.exams.tests")
class ExamsModuleTests(TestCase):
    """Test suite covering the complete Exams module services and view authorization workflows."""

    def setUp(self):
        super().setUp()

        # Create user roles
        self.group_admin, _ = Group.objects.get_or_create(name="Admin")
        self.group_principal, _ = Group.objects.get_or_create(name="Principal")
        self.group_teacher, _ = Group.objects.get_or_create(name="Teacher")
        self.group_student, _ = Group.objects.get_or_create(name="Student")
        self.group_guardian, _ = Group.objects.get_or_create(name="Guardian")

        # Create users
        self.admin_user = User.objects.create_user(
            username="admin@test.com", email="admin@test.com", password="pass"
        )
        self.admin_user.groups.add(self.group_admin)

        self.principal_user = User.objects.create_user(
            username="principal@test.com", email="principal@test.com", password="pass"
        )
        self.principal_user.groups.add(self.group_principal)

        self.teacher_user = User.objects.create_user(
            username="teacher@test.com", email="teacher@test.com", password="pass"
        )
        self.teacher_user.groups.add(self.group_teacher)

        self.unassigned_teacher = User.objects.create_user(
            username="unassigned_teacher@test.com", email="unassigned_teacher@test.com", password="pass"
        )
        self.unassigned_teacher.groups.add(self.group_teacher)

        self.student_user = User.objects.create_user(
            username="student@test.com", email="student@test.com", password="pass"
        )
        self.student_user.groups.add(self.group_student)

        self.guardian_user = User.objects.create_user(
            username="guardian@test.com", email="guardian@test.com", password="pass"
        )
        self.guardian_user.groups.add(self.group_guardian)

        # Create session
        self.session = Session.objects.create(
            name="Session A",
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate() - datetime.timedelta(days=10),
            end_date=timezone.localdate() + datetime.timedelta(days=10),
        )

        # Create subjects
        self.subject = Subject.objects.create(name="Math", code="M101", session=self.session)
        self.other_subject = Subject.objects.create(name="Physics", code="P101", session=self.session)

        # Teacher assignments
        self.assignment = TeacherAssignment.objects.create(
            teacher=self.teacher_user,
            session=self.session,
            subject=self.subject,
            is_active=True,
        )

        # Create students
        self.student = Student.objects.create(
            full_name="Ahmed Hassan",
            email="student@test.com",
            portal_user=self.student_user,
            status="Active",
        )

        self.other_student = Student.objects.create(
            full_name="Other Student",
            email="otherstudent@test.com",
            status="Active",
        )

        # Enrollments
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
        )
        self.other_enrollment = Enrollment.objects.create(
            student=self.other_student,
            session=self.session,
            status="Active",
        )

        # Guardian link
        self.guardian = Guardian.objects.create(
            student=self.student,
            full_name="Jane Parent",
            email="guardian@test.com",
            portal_user=self.guardian_user,
        )

        # Create global grade configurations
        GradeConfig.objects.create(
            grade_name="A",
            min_percentage=Decimal("80.00"),
            max_percentage=Decimal("100.00"),
            sort_order=1
        )
        GradeConfig.objects.create(
            grade_name="B",
            min_percentage=Decimal("60.00"),
            max_percentage=Decimal("79.99"),
            sort_order=2
        )

    def test_teacher_scope_enforcement(self):
        """Verify that teachers can only access subjects and sessions they are explicitly assigned to."""
        # Unassigned teacher must raise Http404 when validating scope
        with self.assertRaises(Http404):
            _validate_teacher_scope(
                self.unassigned_teacher, session_id=self.session.id, subject_id=self.subject.id
            )

        # Assigned teacher must pass validation
        _validate_teacher_scope(
            self.teacher_user, session_id=self.session.id, subject_id=self.subject.id
        )

        # Try to access a subject they are not assigned to
        with self.assertRaises(Http404):
            _validate_teacher_scope(
                self.teacher_user, session_id=self.session.id, subject_id=self.other_subject.id
            )

    def test_teacher_view_scoping(self):
        """Verify that a teacher cannot access exam detail or results for an unassigned exam/subject."""
        # Create an exam in a subject they are not assigned to
        other_exam = create_exam(
            session_id=self.session.id,
            subject_id=self.other_subject.id,
            name="Physics Quiz",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )
        self.client.force_login(self.teacher_user)
        # Accessing exam detail of unassigned subject should raise 404
        response = self.client.get(reverse("exam_detail", kwargs={"pk": other_exam.id}))
        self.assertEqual(response.status_code, 404)

    def test_grade_config_lookups(self):
        """Verify grade lookup priority: session specific -> global -> fallback to F."""
        # Create session specific config
        GradeConfig.objects.create(
            session=self.session,
            grade_name="A+",
            min_percentage=Decimal("90.00"),
            max_percentage=Decimal("100.00"),
            sort_order=1
        )

        # Test session specific lookup (A+ for 95%)
        grade = _get_grade_for_percentage(self.session, Decimal("95.00"))
        self.assertEqual(grade, "A+")

        # Test fallback to global config (B for 70%)
        grade = _get_grade_for_percentage(self.session, Decimal("70.00"))
        self.assertEqual(grade, "B")

        # Test no matching configuration fallback to F
        grade = _get_grade_for_percentage(self.session, Decimal("30.00"))
        self.assertEqual(grade, "F")

    def test_overlapping_grade_configs(self):
        """Verify that overlapping grade configs raise ValidationError."""
        # Create an overlapping global config (B is 60-79.99, let's create a C from 50-65)
        GradeConfig.objects.create(
            grade_name="C",
            min_percentage=Decimal("50.00"),
            max_percentage=Decimal("65.00"),
            sort_order=3
        )

        with self.assertRaises(ValidationError):
            _get_grade_for_percentage(self.session, Decimal("70.00"))

    def test_competition_ranking_calculation(self):
        """Verify standard competition ranking rules (1,1,3) and absent students exclusion."""
        # Create an exam
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Math Quiz",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        # Record results
        res1 = record_exam_result(exam.id, self.student.id, Decimal("90.00"), "Present", "", self.admin_user)
        res2 = record_exam_result(exam.id, self.other_student.id, Decimal("90.00"), "Present", "", self.admin_user)

        # Create a third student
        third_student = Student.objects.create(
            full_name="Third Student", email="third@test.com", status="Active"
        )
        Enrollment.objects.create(student=third_student, session=self.session, status="Active")
        res3 = record_exam_result(exam.id, third_student.id, Decimal("80.00"), "Present", "", self.admin_user)

        # Create a fourth student (Absent)
        fourth_student = Student.objects.create(
            full_name="Fourth Student", email="fourth@test.com", status="Active"
        )
        Enrollment.objects.create(student=fourth_student, session=self.session, status="Active")
        res4 = record_exam_result(exam.id, fourth_student.id, Decimal("0.00"), "Absent", "", self.admin_user)

        # Refetch
        res1.refresh_from_db()
        res2.refresh_from_db()
        res3.refresh_from_db()
        res4.refresh_from_db()

        # Competition ranks check:
        # Both 90s get rank 1.
        self.assertEqual(res1.rank, 1)
        self.assertEqual(res2.rank, 1)
        # 80 gets rank 3
        self.assertEqual(res3.rank, 3)
        # Absent get rank None
        self.assertIsNone(res4.rank)
        self.assertEqual(res4.percentage, Decimal("0.00"))
        self.assertEqual(res4.grade, "F")

    def test_bulk_result_entry_atomic(self):
        """Verify that bulk result entry recalculates ranking atomically once at the end."""
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Math Exam",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        results_list = [
            {"student_id": self.student.id, "obtained_marks": Decimal("95.00"), "status": "Present", "remarks": ""},
            {"student_id": self.other_student.id, "obtained_marks": Decimal("85.00"), "status": "Present", "remarks": ""},
        ]

        saved = bulk_result_entry(exam.id, results_list, self.admin_user)
        self.assertEqual(len(saved), 2)

        # Rankings check
        r1 = ExamResult.objects.get(exam=exam, student=self.student)
        r2 = ExamResult.objects.get(exam=exam, student=self.other_student)
        self.assertEqual(r1.rank, 1)
        self.assertEqual(r2.rank, 2)

    def test_publish_restrictions(self):
        """Verify that only Admin can publish exams, and Principal/Admin can review."""
        from apps.exams.services import review_exam
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Publish Test",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        # Teacher cannot publish
        with self.assertRaises(PermissionDenied):
            publish_exam(exam.id, self.teacher_user)

        # Principal cannot publish
        with self.assertRaises(PermissionDenied):
            publish_exam(exam.id, self.principal_user)

        # Principal can review
        review_exam(exam.id, self.principal_user)
        exam.refresh_from_db()
        self.assertEqual(exam.status, "Under Review")

        # Admin can publish
        publish_exam(exam.id, self.admin_user)
        exam.refresh_from_db()
        self.assertTrue(exam.is_published)
        self.assertEqual(exam.status, "Published")

    def test_view_published_exams_scoping(self):
        """Verify that students and guardians can only view published exams within their scoping."""
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Student View Test",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        # Record result
        record_exam_result(exam.id, self.student.id, Decimal("85.00"), "Present", "", self.admin_user)

        # Students and Guardians see 404 for unpublished exams (when accessed via portal routes)
        self.client.force_login(self.student_user)
        response = self.client.get(f"/portal/student/exams/{exam.id}/")
        self.assertEqual(response.status_code, 404)

        self.client.force_login(self.guardian_user)
        response = self.client.get(f"/portal/guardian/exams/{exam.id}/")
        self.assertEqual(response.status_code, 404)

        # Publish the exam
        publish_exam(exam.id, self.admin_user)

        # Student accesses detail page (now published)
        self.client.force_login(self.student_user)
        response = self.client.get("/portal/student/exams/?format=json", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["exams"]), 1)

        # Check guardian list view
        self.client.force_login(self.guardian_user)
        response = self.client.get("/portal/guardian/exams/?format=json", HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["exams"]), 1)

    def test_guardian_access_unlinked_student_exam(self):
        """Verify that a guardian cannot access exams of unlinked students."""
        # Create another student and session
        unlinked_session = Session.objects.create(
            name="Session B",
            status="Active",
            fee=Decimal("1000.00"),
            registration_fee=Decimal("200.00"),
            start_date=timezone.localdate() - datetime.timedelta(days=10),
            end_date=timezone.localdate() + datetime.timedelta(days=10),
        )
        unlinked_subject = Subject.objects.create(name="Chemistry", code="C101", session=unlinked_session)
        unlinked_student = Student.objects.create(
            full_name="Unlinked Student",
            email="unlinked@test.com",
            status="Active",
        )
        Enrollment.objects.create(
            student=unlinked_student,
            session=unlinked_session,
            status="Active",
        )

        unlinked_exam = create_exam(
            session_id=unlinked_session.id,
            subject_id=unlinked_subject.id,
            name="Chem Exam",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )
        publish_exam(unlinked_exam.id, self.admin_user)

        self.client.force_login(self.guardian_user)
        # The guardian is only linked to self.student (Session A), not unlinked_student (Session B)
        # Attempting to access unlinked_exam should return 404
        response = self.client.get(reverse("guardian_exam_detail", kwargs={"pk": unlinked_exam.id}))
        self.assertEqual(response.status_code, 404)

    def test_exam_statistics(self):
        """Verify that exam statistics returns correct calculations."""
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Stats Test",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("55.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        # Record marks
        record_exam_result(exam.id, self.student.id, Decimal("80.00"), "Present", "", self.admin_user)
        record_exam_result(exam.id, self.other_student.id, Decimal("40.00"), "Present", "", self.admin_user)

        # Create a third student who is absent
        third_student = Student.objects.create(
            full_name="Absent Student", email="absent@test.com", status="Active"
        )
        Enrollment.objects.create(student=third_student, session=self.session, status="Active")
        record_exam_result(exam.id, third_student.id, Decimal("0.00"), "Absent", "", self.admin_user)

        stats = calculate_exam_statistics(exam.id)
        self.assertEqual(stats["total_students"], 3)
        self.assertEqual(stats["present_count"], 2)
        self.assertEqual(stats["absent_count"], 1)
        self.assertEqual(stats["average_marks"], Decimal("60.00"))  # (80 + 40) / 2 = 60
        self.assertEqual(stats["highest_marks"], Decimal("80.00"))
        self.assertEqual(stats["lowest_marks"], Decimal("40.00"))
        self.assertEqual(stats["pass_count"], 1)  # only Student 1 (80 >= 55)
        self.assertEqual(stats["fail_count"], 2)  # Student 2 (40 < 55) + Absent

    def test_result_locking_when_published(self):
        """Verify that ExamResult entries are read-only once exam.status == Published."""
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Lock Test",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Quiz",
            created_by=self.admin_user,
        )

        # Record initial result (allowed in Draft status)
        result = record_exam_result(exam.id, self.student.id, Decimal("85.00"), "Present", "", self.admin_user)

        # Publish the exam
        publish_exam(exam.id, self.admin_user)

        # Attempt to record/update result should raise ValidationError
        with self.assertRaises(ValidationError):
            record_exam_result(exam.id, self.student.id, Decimal("90.00"), "Present", "", self.admin_user)

        with self.assertRaises(ValidationError):
            update_exam_result(result.id, Decimal("90.00"), "Present", "Updated remarks", self.admin_user)

        with self.assertRaises(ValidationError):
            bulk_result_entry(exam.id, [{"student_id": self.student.id, "obtained_marks": Decimal("90.00"), "status": "Present", "remarks": ""}], self.admin_user)

    def test_transcript_generation_and_view(self):
        """Verify that generate_student_transcript calculates correct GPA/scores, and views return 200."""
        from apps.exams.transcript_service import generate_student_transcript

        # Setup exam with results
        exam = create_exam(
            session_id=self.session.id,
            subject_id=self.subject.id,
            name="Math Final",
            exam_date=timezone.localdate(),
            total_marks=Decimal("100.00"),
            passing_marks=Decimal("50.00"),
            exam_type="Final",
            created_by=self.admin_user,
        )
        record_exam_result(exam.id, self.student.id, Decimal("85.00"), "Present", "Great job", self.admin_user)
        publish_exam(exam.id, self.admin_user)

        GradeConfig.objects.filter(grade_name="A").update(grade_point=Decimal("4.00"))

        transcript = generate_student_transcript(self.student.id)
        self.assertEqual(transcript["student_name"], self.student.full_name)
        self.assertEqual(transcript["gpa"], Decimal("4.00"))
        self.assertEqual(transcript["overall_result"], "Pass")

        # Test Student view
        self.client.force_login(self.student_user)
        response = self.client.get("/portal/student/transcript/")
        self.assertEqual(response.status_code, 200)

        # Test Guardian view (authorized)
        self.client.force_login(self.guardian_user)
        response = self.client.get(f"/portal/guardian/child/{self.student.id}/transcript/")
        self.assertEqual(response.status_code, 200)

        # Test Guardian view (unauthorized - other_student is not linked to guardian_user)
        response = self.client.get(f"/portal/guardian/child/{self.other_student.id}/transcript/")
        self.assertEqual(response.status_code, 404)

    def test_session_result_summary_view(self):
        """Verify that session result summary view loads and computes class stats."""
        # Test Admin view
        self.client.force_login(self.admin_user)
        response = self.client.get(f"/panel/admin/session/{self.session.id}/results/")
        self.assertEqual(response.status_code, 200)

    def test_grade_config_list_loads_for_admin_and_principal(self):
        # Admin can access
        self.client.force_login(self.admin_user)
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 200)

        # Principal can access
        self.client.force_login(self.principal_user)
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 200)

    def test_grade_config_unauthorized_and_anonymous(self):
        # Teacher is blocked
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 404)

        # Student is blocked
        self.client.force_login(self.student_user)
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 404)

        # Anonymous redirects to login
        self.client.logout()
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 302)

    def test_grade_config_create_and_validation(self):
        self.client.force_login(self.admin_user)
        url = reverse("admin_panel:exams:grade_config_create")

        # 1. GET page loads
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 2. Valid POST creates config
        data = {
            "session": self.session.id,
            "grade_name": "C+",
            "min_percentage": "50.00",
            "max_percentage": "59.99",
            "grade_point": "2.50",
            "sort_order": "3"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302) # Redirect to list
        self.assertTrue(GradeConfig.objects.filter(grade_name="C+", session=self.session).exists())

        # 3. Invalid score range is rejected (min > max)
        data["grade_name"] = "C-"
        data["min_percentage"] = "60.00"
        data["max_percentage"] = "50.00"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(GradeConfig.objects.filter(grade_name="C-").exists())

        # 4. Overlapping range is rejected (overlapping with B: 60-79.99 global config context doesn't apply to session, so let's test overlapping with another session config)
        GradeConfig.objects.create(
            session=self.session,
            grade_name="B-",
            min_percentage=Decimal("60.00"),
            max_percentage=Decimal("70.00"),
            sort_order=2
        )
        data["grade_name"] = "C-"
        data["min_percentage"] = "65.00"
        data["max_percentage"] = "75.00"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(GradeConfig.objects.filter(grade_name="C-").exists())

        # 5. Non-overlapping range is accepted
        data["grade_name"] = "C-"
        data["min_percentage"] = "30.00"
        data["max_percentage"] = "40.00"
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(GradeConfig.objects.filter(grade_name="C-", session=self.session).exists())

    def test_grade_config_edit_and_validation(self):
        self.client.force_login(self.admin_user)
        
        # Create a grade config to edit
        config = GradeConfig.objects.create(
            session=self.session,
            grade_name="D",
            min_percentage=Decimal("40.00"),
            max_percentage=Decimal("49.99"),
            sort_order=4
        )

        url = reverse("admin_panel:exams:grade_config_edit", kwargs={"pk": config.pk})

        # 1. GET page loads
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # 2. Valid edit updates config
        data = {
            "session": self.session.id,
            "grade_name": "D",
            "min_percentage": "41.00",
            "max_percentage": "49.00",
            "grade_point": "1.00",
            "sort_order": "4"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        config.refresh_from_db()
        self.assertEqual(config.min_percentage, Decimal("41.00"))
        self.assertEqual(config.grade_point, Decimal("1.00"))

        # 3. Invalid edit does not mutate record
        GradeConfig.objects.create(
            session=self.session,
            grade_name="A-",
            min_percentage=Decimal("80.00"),
            max_percentage=Decimal("90.00"),
            sort_order=1
        )
        data["min_percentage"] = "85.00" # Overlaps with A- (80-90)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
        config.refresh_from_db()
        self.assertEqual(config.min_percentage, Decimal("41.00")) # Unchanged

    def test_grade_config_list_empty_state(self):
        self.client.force_login(self.admin_user)
        # Delete all grade configs
        GradeConfig.objects.all().delete()
        response = self.client.get(reverse("admin_panel:exams:grade_config_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No Grade Configurations Found")
