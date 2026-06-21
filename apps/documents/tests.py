import os
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import Group

from apps.students.models import Student, StudentAchievement
from apps.documents.models import ComparisonJob, ComparisonResult
from apps.documents.services import (
    normalize_name,
    parse_line,
    match_students,
    process_result_pdf,
)
from apps.notifications.models import Notification, EmailLog

User = get_user_model()

class DocumentComparisonTests(TestCase):
    def setUp(self):
        # Create test admin user
        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@test.com",
            password="password",
        )
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin_user.groups.add(self.admin_group)

        # Create test students
        self.student_1 = Student.objects.create(
            full_name="Muhammad Ali Khan",
            roll_number="12345",
            email="ali@test.com",
        )
        self.student_2 = Student.objects.create(
            full_name="Fatima Ayesha",
            roll_number="54321",
            email="fatima@test.com",
        )

    def test_name_normalization(self):
        """Ensure normalize_name strips whitespace, converts to lowercase, and removes punctuation."""
        self.assertEqual(normalize_name("Muhammad Ali Khan!"), "muhammad ali khan")
        self.assertEqual(normalize_name("  Fatima, Ayesha  "), "fatima ayesha")
        self.assertEqual(normalize_name(""), "")

    def test_parse_line(self):
        """Ensure parse_line properly extracts digit sequence as roll number and cleans the name."""
        res1 = parse_line("12345 Muhammad Ali Khan")
        self.assertEqual(res1['roll'], "12345")
        self.assertEqual(res1['raw_name'], "Muhammad Ali Khan")

        res2 = parse_line("Fatima Ayesha 54321")
        self.assertEqual(res2['roll'], "54321")
        self.assertEqual(res2['raw_name'], "Fatima Ayesha")

    def test_exact_matches(self):
        """Ensure match_students works on exact name or roll match."""
        records = [
            {'raw_name': 'Muhammad Ali Khan', 'roll': '12345'},
            {'raw_name': 'Fatima Ayesha', 'roll': None},
        ]
        results = match_students(records)
        self.assertEqual(len(results), 2)

        # Check student 1
        res1 = next(r for r in results if r['student'] == self.student_1)
        self.assertTrue(res1['is_exact_match'])
        self.assertEqual(res1['match_confidence'], 1.0)

        # Check student 2
        res2 = next(r for r in results if r['student'] == self.student_2)
        self.assertTrue(res2['is_exact_match'])

    def test_fuzzy_matches(self):
        """Ensure match_students matches close fuzzy names above threshold."""
        records = [
            {'raw_name': 'Muhammad Aly Khan', 'roll': None}, # Typo in name
        ]
        results = match_students(records)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['student'], self.student_1)
        self.assertFalse(results[0]['is_exact_match'])
        self.assertTrue(results[0]['match_confidence'] >= 0.85)

    @patch("apps.documents.services.extract_text")
    def test_process_pdf_and_trigger_notifications(self, mock_extract_text):
        """Ensure full processing pipeline flags students, creates achievements, and notifies admins/students."""
        # Setup mock PDF content
        mock_extract_text.return_value = "12345 Muhammad Ali Khan\n54321 Fatima Ayesha\n"

        # Create ComparisonJob
        pdf_file = SimpleUploadedFile("results.pdf", b"dummy PDF content", content_type="application/pdf")
        job = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file,
            exam_type="CSS",
            status="Uploaded"
        )

        # Execute process
        success = process_result_pdf(job.id)
        self.assertTrue(success)

        # Verify job is processed
        job.refresh_from_db()
        self.assertEqual(job.status, "Processed")
        self.assertEqual(job.total_entries, 2)
        self.assertEqual(job.matched_entries, 2)

        # Verify students flagged as selected
        self.student_1.refresh_from_db()
        self.student_2.refresh_from_db()
        self.assertTrue(self.student_1.is_selected)
        self.assertTrue(self.student_2.is_selected)

        # Verify achievements are created
        achievements_1 = StudentAchievement.objects.filter(student=self.student_1)
        self.assertEqual(achievements_1.count(), 1)
        self.assertIn("CSS", achievements_1.first().title)

        # Verify comparison result entries are saved
        results = ComparisonResult.objects.filter(job=job)
        self.assertEqual(results.count(), 2)

        # Verify admin notifications are created
        admin_notifications = Notification.objects.filter(recipient=self.admin_user, category="academic")
        self.assertTrue(admin_notifications.exists())

    @patch("apps.documents.services.extract_text")
    def test_duplicate_upload_prevention(self, mock_extract_text):
        """Ensure processing same PDF filename twice is blocked."""
        mock_extract_text.return_value = "12345 Muhammad Ali Khan\n"

        pdf_file1 = SimpleUploadedFile("same_results.pdf", b"dummy 1", content_type="application/pdf")
        job1 = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file1,
            exam_type="CSS",
            status="Uploaded"
        )
        process_result_pdf(job1.id)

        # Attempt to upload second job with same filename
        pdf_file2 = SimpleUploadedFile("same_results.pdf", b"dummy 2", content_type="application/pdf")
        job2 = ComparisonJob.objects.create(
            uploaded_by=self.admin_user,
            file=pdf_file2,
            exam_type="CSS",
            status="Uploaded"
        )

        with self.assertRaises(ValueError):
            process_result_pdf(job2.id)

        job2.refresh_from_db()
        self.assertEqual(job2.status, "Failed")
