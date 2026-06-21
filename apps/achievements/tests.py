import os
from unittest.mock import patch
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.students.models import Student, Enrollment
from apps.academics.models import Session
from apps.documents.models import ComparisonJob
from apps.achievements.models import Achievement
from apps.achievements.services import get_success_metrics
from apps.documents.services import process_result_pdf
from apps.notifications.models import Notification

User = get_user_model()

class AchievementSystemTests(TestCase):
    def setUp(self):
        # Create user roles and groups
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="password",
        )
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin_user.groups.add(self.admin_group)

        self.student_user = User.objects.create_user(
            username="student_user",
            email="student@test.com",
            password="password",
        )
        self.student_group, _ = Group.objects.get_or_create(name="Student")
        self.student_user.groups.add(self.student_group)

        # Create active sessions
        self.session = Session.objects.create(
            name="CSS Morning Batch 2026",
            code="CSS2026M",
            status="Active",
            max_capacity=50,
        )

        # Create students
        self.student = Student.objects.create(
            full_name="Muhammad Ali Khan",
            roll_number="12345",
            email="ali@test.com",
            portal_user=self.student_user,
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            session=self.session,
            status="Active",
        )

        # Client setup
        self.client = Client()

    @patch("apps.documents.services.extract_text")
    def test_achievement_created_from_pdf_match(self, mock_extract_text):
        """Ensure high confidence PDF match creates an Achievement and sets selection state."""
        mock_extract_text.return_value = "12345 Muhammad Ali Khan\n"

        pdf_file = SimpleUploadedFile("css_results.pdf", b"pdf bytes", content_type="application/pdf")
        job = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file,
            exam_type="CSS",
            status="Uploaded"
        )

        success = process_result_pdf(job.id)
        self.assertTrue(success)

        # Verify achievement created
        achievement = Achievement.objects.filter(student=self.student, exam_type="CSS", year=job.uploaded_at.year).first()
        self.assertIsNotNone(achievement)
        self.assertTrue(achievement.is_public)

        # Verify student is flagged as selected
        self.student.refresh_from_db()
        self.assertTrue(self.student.is_selected)

        # Verify notification created
        student_notif = Notification.objects.filter(recipient=self.student_user, category="academic")
        self.assertTrue(student_notif.exists())

    def test_duplicate_prevention_validation(self):
        """Ensure model clean/save prevents duplicate achievements per student per exam_type per year."""
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=2026,
            rank="1st",
            is_public=True
        )

        duplicate = Achievement(
            student=self.student,
            exam_type="CSS",
            year=2026,
            rank="2nd",
        )

        with self.assertRaises(ValidationError):
            duplicate.full_clean()

        with self.assertRaises(ValidationError):
            duplicate.save()

    def test_success_dashboard_metrics(self):
        """Ensure get_success_metrics returns correct data structures and metrics."""
        # Create some achievements
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=timezone.now().year,
            rank="3rd",
            is_public=True
        )

        metrics = get_success_metrics()
        self.assertEqual(metrics["total_selections"], 1)
        self.assertEqual(metrics["selections_this_year"], 1)
        self.assertEqual(len(metrics["sessions_metrics"]), 1)
        self.assertEqual(metrics["sessions_metrics"][0]["success_count"], 1)
        self.assertEqual(metrics["sessions_metrics"][0]["success_rate"], 100.0)

    def test_student_profile_shows_badge(self):
        """Ensure student profile page renders achievement badges."""
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=2026,
            rank="Top 10",
        )

        self.client.force_login(self.admin_user)
        url = reverse("admin_panel:students:student_detail", args=[self.student.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Selected in CSS 2026")

    def test_public_page_shows_only_public(self):
        """Ensure public success page displays only public achievements and obeys filters."""
        # Public achievement
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=2026,
            is_public=True,
            testimonial="IICE helped me ace CSS!"
        )

        # Private achievement
        other_student = Student.objects.create(
            full_name="Secret Student",
            roll_number="54321",
        )
        Achievement.objects.create(
            student=other_student,
            exam_type="PMS",
            year=2025,
            is_public=False,
        )

        # Request public page
        url = reverse("public_success")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Should contain public student info
        self.assertContains(response, "Muhammad Ali Khan")
        self.assertContains(response, "IICE helped me ace CSS!")

        # Should not contain private student info
        self.assertNotContains(response, "Secret Student")

        # Test filters
        response_filtered = self.client.get(url + "?exam_type=PMS")
        self.assertNotContains(response_filtered, "Muhammad Ali Khan")

    def test_exports(self):
        """Ensure success report export endpoints output correct formats."""
        Achievement.objects.create(
            student=self.student,
            exam_type="CSS",
            year=2026,
        )

        self.client.force_login(self.admin_user)

        # Test CSV Export
        csv_url = reverse("reports:success_csv")
        csv_response = self.client.get(csv_url)
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("Muhammad Ali Khan", csv_response.content.decode("utf-8"))

        # Test PDF Export
        pdf_url = reverse("reports:success_pdf")
        pdf_response = self.client.get(pdf_url)
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")

    def test_permissions(self):
        """Ensure panel achievements routes are restricted to Admin/Principal groups."""
        dashboard_url = reverse("admin_panel:success_dashboard")

        # Unauthenticated gets login redirect
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 302)

        # Student gets 404 access denied (RBAC design)
        self.client.force_login(self.student_user)
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 404)

        # Admin gets 200
        self.client.force_login(self.admin_user)
        response = self.client.get(dashboard_url)
        self.assertEqual(response.status_code, 200)
