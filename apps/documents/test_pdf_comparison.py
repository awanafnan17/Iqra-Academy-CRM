import os
import io
import re
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages

from apps.students.models import Student, StudentAchievement
from apps.documents.services import (
    parse_pdf_to_preview_records,
    match_students_preview,
    classify_match,
    normalize_and_clean_name,
)
from apps.achievements.models import Achievement

User = get_user_model()

class PDFComparisonPreviewTests(TestCase):
    def setUp(self):
        # Create groups and users for permission tests
        self.admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.principal_group, _ = Group.objects.get_or_create(name="Principal")
        self.registrar_group, _ = Group.objects.get_or_create(name="Registrar")
        self.teacher_group, _ = Group.objects.get_or_create(name="Teacher")

        self.admin_user = User.objects.create_user(username="admin_u", email="admin@test.com", password="pwd")
        self.admin_user.groups.add(self.admin_group)

        self.principal_user = User.objects.create_user(username="principal_u", email="principal@test.com", password="pwd")
        self.principal_user.groups.add(self.principal_group)

        self.registrar_user = User.objects.create_user(username="registrar_u", email="registrar@test.com", password="pwd")
        self.registrar_user.groups.add(self.registrar_group)

        self.teacher_user = User.objects.create_user(username="teacher_u", email="teacher@test.com", password="pwd")
        self.teacher_user.groups.add(self.teacher_group)

        self.downloads_dir = r"C:\Users\Afnan Awan\Downloads"

        # Create test students for match cases
        self.st_confirmed = Student.objects.create(
            full_name="Muhammad Nafees",
            father_name="Muhammad Siddique",
            roll_number="12345",
            status="Active"
        )
        self.st_fuzzy = Student.objects.create(
            full_name="Maaria Raheel",
            father_name="Raheel Akhtar",
            roll_number="54321",
            status="Active"
        )
        self.st_missing_father = Student.objects.create(
            full_name="Usaid Rafique",
            father_name="",
            roll_number="012633",
            status="Active"
        )
        self.st_wrong_father = Student.objects.create(
            full_name="Muhammad Asghar",
            father_name="Wrong Father Name",
            status="Active"
        )
        self.st_father_only = Student.objects.create(
            full_name="Wrong Student Name",
            father_name="Muhammad Aslam",
            status="Active"
        )
        # Multiple candidates for ambiguity
        self.st_ambig1 = Student.objects.create(
            full_name="Ambiguous Student",
            father_name="Same Father",
            status="Active"
        )
        self.st_ambig2 = Student.objects.create(
            full_name="Ambiguous Student",
            father_name="Same Father",
            status="Active"
        )

    def test_ppsc_boilers_parser(self):
        """1. PPSC Boilers/two-line parser extracts candidate + father name."""
        path = os.path.join(self.downloads_dir, "7J2026_260620153843.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                records = parse_pdf_to_preview_records(f)
            self.assertIsInstance(records, list)
            self.assertTrue(len(records) > 0)
            rec = records[0]
            self.assertEqual(rec['candidate_name'].upper(), "MUHAMMAD NAFEES")
            self.assertEqual(rec['father_name'].upper(), "MUHAMMAD SIDDIQUE")
            self.assertEqual(rec['merit_no'], "1")
            self.assertEqual(rec['application_no'], "27400006")
            self.assertEqual(rec['source_format'], "PPSC_BOILERS")

    def test_ppsc_tehsildar_parser(self):
        """2. PPSC Tehsildar/separate-column parser extracts roll + candidate + father."""
        path = os.path.join(self.downloads_dir, "8J2023_260407152859.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                records = parse_pdf_to_preview_records(f)
            self.assertIsInstance(records, list)
            self.assertTrue(len(records) > 0)
            rec = records[0]
            self.assertEqual(rec['roll_no'], "13519")
            self.assertEqual(rec['candidate_name'].upper(), "SHUMAIL JAMSHAID")
            self.assertEqual(rec['father_name'].upper(), "JAMSHAID HUSSAIN")
            self.assertEqual(rec['source_format'], "PPSC_TEHSILDAR")
            # Assert 61 records extracted
            self.assertEqual(len(records), 61)
            # Assert last quota rows are included
            last_rec = records[-1]
            self.assertEqual(last_rec['roll_no'], "80719")
            self.assertEqual(last_rec['candidate_name'].upper(), "MUHAMMAD YASIR KHAN")
            self.assertEqual(last_rec['father_name'].upper(), "MUHAMMAD NASIR KHAN")

    def test_ppsc_revised_merit_list_parser(self):
        """3. PPSC Revised Merit List parser works dynamically without hardcoded page values."""
        path = os.path.join(self.downloads_dir, "23J2023 (Rev 1)_26062015423.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                records = parse_pdf_to_preview_records(f)
            self.assertIsInstance(records, list)
            self.assertTrue(len(records) > 0)
            rec = records[0]
            self.assertEqual(rec['candidate_name'].upper(), "HUMA IJAZ")
            self.assertEqual(rec['father_name'].upper(), "IJAZ AHMED")
            self.assertEqual(rec['application_no'], "18100356")
            self.assertEqual(rec['merit_no'], "1")
            self.assertEqual(rec['source_format'], "PPSC_REVISED_MERIT_LIST")

    def test_ppsc_sergeant_parser(self):
        """4. PPSC Sergeant/roll-diary parser extracts candidate + father."""
        path = os.path.join(self.downloads_dir, "93C2026_260620145838.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                records = parse_pdf_to_preview_records(f)
            self.assertIsInstance(records, list)
            self.assertTrue(len(records) > 0)
            rec = records[0]
            self.assertEqual(rec['roll_no'], "10888")
            self.assertEqual(rec['application_no'], "54000029")
            self.assertEqual(rec['candidate_name'].upper(), "SAMINA RABNAWAZ")
            self.assertEqual(rec['father_name'].upper(), "RABNAWAZ")
            self.assertEqual(rec['source_format'], "PPSC_SERGEANT")

    def test_css_fpsc_parser(self):
        """5. CSS/FPSC parser extracts candidate data but leaves father empty."""
        path = os.path.join(self.downloads_dir, "1777540845484_Annexure_A_--_CSS-2025.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                records = parse_pdf_to_preview_records(f)
            self.assertIsInstance(records, list)
            self.assertTrue(len(records) > 0)
            rec = records[0]
            self.assertEqual(rec['roll_no'], "012633")
            self.assertEqual(rec['candidate_name'].upper(), "USAID RAFIQUE")
            self.assertEqual(rec['father_name'], "")
            self.assertEqual(rec['source_format'], "CSS_FPSC")

            # Assert CSS/FPSC name-only records still do not become confirmed matches
            students = list(Student.objects.all())
            status, matched, conf = classify_match(rec['candidate_name'], rec['father_name'], rec['roll_no'], students)
            self.assertNotEqual(status, "CONFIRMED_MATCH")
            self.assertNotEqual(status, "POSSIBLE_MATCH")
            self.assertEqual(status, "NAME_ONLY_PARTIAL")

    def test_scanned_pdf(self):
        """6. No-text/scanned PDF returns OCR_REQUIRED or EXTRACTION_FAILED."""
        path = os.path.join(self.downloads_dir, "SDEO Pera Result.pdf")
        if os.path.exists(path):
            with open(path, "rb") as f:
                res = parse_pdf_to_preview_records(f)
            self.assertIn(res, ["OCR_REQUIRED", "EXTRACTION_FAILED"])

    def test_confirmed_match(self):
        """7. Exact candidate + father returns CONFIRMED_MATCH."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("Muhammad Nafees", "Muhammad Siddique", None, students)
        self.assertEqual(status, "CONFIRMED_MATCH")
        self.assertEqual(matched[0], self.st_confirmed)

    def test_missing_father_match(self):
        """8. Candidate match with missing father returns NAME_ONLY_PARTIAL, not confirmed."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("Usaid Rafique", "", None, students)
        self.assertEqual(status, "NAME_ONLY_PARTIAL")
        self.assertEqual(matched[0], self.st_missing_father)

    def test_wrong_father_match(self):
        """9. Candidate match with wrong father returns NAME_ONLY_PARTIAL."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("Muhammad Asghar", "Completely Wrong Father", None, students)
        self.assertEqual(status, "NAME_ONLY_PARTIAL")
        self.assertEqual(matched[0], self.st_wrong_father)

    def test_father_only_match(self):
        """10. Father-only match returns FATHER_ONLY_PARTIAL."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("No Candidate Name Match", "Muhammad Aslam", None, students)
        self.assertEqual(status, "FATHER_ONLY_PARTIAL")
        self.assertEqual(matched[0], self.st_father_only)

    def test_ambiguous_match(self):
        """11. Multiple CRM candidates return AMBIGUOUS_MATCH."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("Ambiguous Student", "Same Father", None, students)
        self.assertEqual(status, "AMBIGUOUS_MATCH")
        self.assertEqual(len(matched), 2)

    def test_unmatched(self):
        """12. No CRM match returns UNMATCHED."""
        students = list(Student.objects.all())
        status, matched, conf = classify_match("Unknown Name", "Unknown Father", None, students)
        self.assertEqual(status, "UNMATCHED")
        self.assertEqual(len(matched), 0)

    def test_unauthorized_roles_blocked(self):
        """13. Unauthorized roles are blocked."""
        c = Client()
        
        # Blocked: Teacher
        c.force_login(self.teacher_user)
        response = c.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 404)

        # Blocked: Anonymous user (redirects to login)
        c.logout()
        response = c.get("/panel/admin/pdf-comparison/")
        self.assertRedirects(response, "/accounts/login/?next=/panel/admin/pdf-comparison/")

        # Allowed: Registrar
        c.force_login(self.registrar_user)
        response = c.get("/panel/admin/pdf-comparison/")
        self.assertEqual(response.status_code, 200)

    def test_non_pdf_upload_rejected(self):
        """14. Non-PDF upload is rejected."""
        c = Client()
        c.force_login(self.admin_user)
        
        txt_file = SimpleUploadedFile("results.txt", b"some text", content_type="text/plain")
        response = c.post("/panel/admin/pdf-comparison/", {"pdf_file": txt_file, "exam_type": "CSS"})
        self.assertRedirects(response, "/panel/admin/pdf-comparison/")
        
        # Check that error message is set
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertTrue(any("Only .pdf files are accepted" in str(msg) for msg in messages_list))

    def test_preview_upload_no_mutation(self):
        """15. Preview upload does not mutate student records, is_selected, achievements, or student achievements."""
        c = Client()
        c.force_login(self.admin_user)

        path = os.path.join(self.downloads_dir, "7J2026_260620153843.pdf")
        if os.path.exists(path):
            # Check baseline values
            self.assertFalse(self.st_confirmed.is_selected)
            self.assertEqual(Achievement.objects.count(), 0)
            self.assertEqual(StudentAchievement.objects.count(), 0)

            with open(path, "rb") as f:
                pdf_file = SimpleUploadedFile("7J2026_260620153843.pdf", f.read(), content_type="application/pdf")
            
            response = c.post("/panel/admin/pdf-comparison/", {"pdf_file": pdf_file, "exam_type": "PPSC"})
            self.assertRedirects(response, "/panel/admin/pdf-comparison/")

            # Refresh and check values remain unchanged
            self.st_confirmed.refresh_from_db()
            self.assertFalse(self.st_confirmed.is_selected)
            self.assertEqual(Achievement.objects.count(), 0)
            self.assertEqual(StudentAchievement.objects.count(), 0)
