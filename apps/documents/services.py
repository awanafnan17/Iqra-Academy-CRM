import os
import re
import string
import difflib
from django.conf import settings
from django.db import transaction
from django.contrib.auth.models import Group
from pdfminer.high_level import extract_text

from apps.documents.models import ComparisonJob, ComparisonResult
from apps.students.models import Student, StudentAchievement, Enrollment
from apps.academics.models import TeacherAssignment
from apps.notifications.services import create_notification, send_email_notification
from apps.achievements.models import Achievement

def normalize_name(name_str):
    """Normalize names: lowercase, strip spaces, remove punctuation."""
    if not name_str:
        return ""
    # Lowercase
    name_str = name_str.lower()
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    name_str = name_str.translate(translator)
    # Strip spaces and compress inner spaces
    return " ".join(name_str.split())

def parse_line(line):
    """Extract roll number and clean name from a line of text."""
    line = line.strip()
    if not line:
        return None

    # Find sequence of 3 to 10 digits as roll number
    digits = re.findall(r'\b\d{3,10}\b', line)
    roll = digits[0] if digits else None

    cleaned_line = line
    if roll:
        cleaned_line = cleaned_line.replace(roll, "")

    # Remove other digits (like marks)
    cleaned_line = re.sub(r'\d+', '', cleaned_line)

    raw_name = cleaned_line.strip()
    # Ensure raw_name has some letters
    if not re.search(r'[A-Za-z]', raw_name):
        return None

    return {
        'raw_name': raw_name,
        'roll': roll
    }

def match_students(extracted_records):
    """
    Matches extracted records against the Student database.
    Matching logic:
    1. Exact roll number match if available.
    2. Exact full_name match.
    3. Fuzzy match using difflib.get_close_matches() with threshold >= 0.85.
    """
    matched_results = []

    # Pre-fetch all non-deleted students
    all_students = list(Student.objects.filter(is_deleted=False))

    roll_map = {}
    name_map = {}

    for s in all_students:
        if s.roll_number:
            roll_map[s.roll_number.strip().lower()] = s
        norm_s_name = normalize_name(s.full_name)
        if norm_s_name:
            name_map[norm_s_name] = s

    normalized_student_names = list(name_map.keys())

    for record in extracted_records:
        raw_name = record['raw_name']
        roll = record['roll']
        norm_extracted_name = normalize_name(raw_name)
        matched_student = None
        match_confidence = 0.0
        is_exact = False

        # 1. Exact roll number match
        if roll:
            roll_clean = roll.strip().lower()
            if roll_clean in roll_map:
                matched_student = roll_map[roll_clean]
                match_confidence = 1.0
                is_exact = True

        # 2. Exact full_name match
        if not matched_student and norm_extracted_name in name_map:
            matched_student = name_map[norm_extracted_name]
            match_confidence = 1.0
            is_exact = True

        # 3. Fuzzy matching using difflib
        if not matched_student and norm_extracted_name and normalized_student_names:
            close_matches = difflib.get_close_matches(
                norm_extracted_name,
                normalized_student_names,
                n=1,
                cutoff=0.85
            )
            if close_matches:
                best_match_norm = close_matches[0]
                ratio = difflib.SequenceMatcher(None, norm_extracted_name, best_match_norm).ratio()
                if ratio >= 0.85:
                    matched_student = name_map[best_match_norm]
                    match_confidence = ratio
                    is_exact = False

        matched_results.append({
            'student': matched_student,
            'extracted_name': raw_name,
            'extracted_roll': roll,
            'match_confidence': match_confidence,
            'is_exact_match': is_exact
        })

    return matched_results

def get_original_name(filepath):
    """Normalize file name by stripping Django's random or sequential unique suffixes."""
    base = os.path.basename(filepath)
    name, ext = os.path.splitext(base)
    # Remove random 7-character alphanumeric suffix appended by Django (e.g. _abcdef)
    name = re.sub(r'_[a-zA-Z0-9]{7}$', '', name)
    # Remove sequential suffix appended by Django (e.g. _1, _2)
    name = re.sub(r'_\d+$', '', name)
    return name + ext

def process_result_pdf(job_id):
    """Extract and process PDF results for a given job."""
    try:
        job = ComparisonJob.objects.get(pk=job_id)
    except ComparisonJob.DoesNotExist:
        return False

    # Prevent same PDF processed twice
    orig_filename = get_original_name(job.file.name)
    all_processed_jobs = ComparisonJob.objects.filter(status="Processed").exclude(pk=job.id)

    for pj in all_processed_jobs:
        if get_original_name(pj.file.name) == orig_filename:
            job.status = "Failed"
            job.save()
            raise ValueError("This PDF file has already been processed.")

    # 1. Extract text from PDF
    try:
        pdf_path = job.file.path
        text = extract_text(pdf_path)
    except Exception as e:
        job.status = "Failed"
        job.save()
        return False

    # 2. Parse lines
    lines = text.splitlines()
    extracted_records = []

    for line in lines:
        parsed = parse_line(line)
        if parsed:
            extracted_records.append(parsed)

    # 3. Match students
    matched_results = match_students(extracted_records)

    # 4. Record matches
    total_entries = len(extracted_records)
    matched_entries = 0

    with transaction.atomic():
        for res in matched_results:
            student = res['student']
            extracted_name = res['extracted_name']
            extracted_roll = res['extracted_roll']
            match_confidence = res['match_confidence']
            is_exact_match = res['is_exact_match']

            # Create ComparisonResult entry
            ComparisonResult.objects.create(
                job=job,
                student=student,
                extracted_name=extracted_name,
                extracted_roll=extracted_roll,
                match_confidence=match_confidence,
                is_exact_match=is_exact_match
            )

            if student and match_confidence >= 0.85:
                year = job.uploaded_at.year

                # Check for duplicate Achievement (per student per exam_type per year)
                achievement_exists = Achievement.objects.filter(
                    student=student,
                    exam_type=job.exam_type,
                    year=year
                ).exists()

                if not achievement_exists:
                    Achievement.objects.create(
                        student=student,
                        exam_type=job.exam_type,
                        year=year,
                        rank="",
                        source_job=job,
                        created_by=job.uploaded_by,
                        is_public=True
                    )

                    matched_entries += 1

                    # Flag student as selected
                    student.is_selected = True
                    student.save(update_fields=["is_selected"])

                    # Add old StudentAchievement record for compatibility with existing tests
                    achievement_title = f"Selected in {job.exam_type} {year}"
                    if not StudentAchievement.objects.filter(student=student, title=achievement_title).exists():
                        StudentAchievement.objects.create(
                            student=student,
                            title=achievement_title
                        )

                    # Trigger notifications
                    # A. Student notification
                    if student.portal_user:
                        notif = create_notification(
                            recipient=student.portal_user,
                            title=f"New Achievement: {achievement_title}",
                            message=f"Congratulations! You have been successfully matched in the official {job.exam_type} results PDF.",
                            category="academic",
                            created_by=None
                        )
                        if notif:
                            send_email_notification(notif.id)

                    # B. Notify Admin group
                    admin_group = Group.objects.filter(name="Admin").first()
                    if admin_group:
                        for admin in admin_group.user_set.all():
                            admin_notif = create_notification(
                                recipient=admin,
                                title=f"Student Selection Alert: {student.full_name}",
                                message=f"Student {student.full_name} ({student.roll_number}) was matched in the official {job.exam_type} results PDF with confidence {match_confidence*100:.1f}%.",
                                category="academic",
                                created_by=None
                            )
                            if admin_notif:
                                send_email_notification(admin_notif.id)

                    # C. Notify relevant faculty
                    active_enrollments = Enrollment.objects.filter(student=student, status="Active").select_related("session")
                    sessions = [e.session for e in active_enrollments]
                    if sessions:
                        teachers = TeacherAssignment.objects.filter(
                            session__in=sessions,
                            is_active=True
                        ).select_related("teacher")
                        notified_teachers = set()
                        for ta in teachers:
                            teacher_user = ta.teacher
                            if teacher_user and teacher_user.id not in notified_teachers:
                                notified_teachers.add(teacher_user.id)
                                teacher_notif = create_notification(
                                    recipient=teacher_user,
                                    title=f"Student Selection Alert: {student.full_name}",
                                    message=f"Student {student.full_name} enrolled in session '{ta.session.name}' has been selected in {job.exam_type}.",
                                    category="academic",
                                    created_by=None
                                )
                                if teacher_notif:
                                    send_email_notification(teacher_notif.id)

        # Update job stats
        job.total_entries = total_entries
        job.matched_entries = matched_entries
        job.status = "Processed"
        job.save()

    return True


# =====================================================================
#  Phase 1 Preview comparison & dynamic matching parser
# =====================================================================

import string
import uuid
import re
import difflib
from pypdf import PdfReader
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LAParams, LTTextLine

def normalize_and_clean_name(name_str):
    """Normalize names: lowercase, strip spaces, remove punctuation, align common abbreviations."""
    if not name_str:
        return ""
    name_str = name_str.lower()
    # Remove punctuation
    translator = str.maketrans('', '', string.punctuation)
    name_str = name_str.translate(translator)
    
    # Align common abbreviations
    words = name_str.split()
    cleaned = []
    for w in words:
        if w in ["m", "mohammad", "mohamad", "mhammed"]:
            cleaned.append("muhammad")
        elif w in ["ch", "chaudhary", "chaudhri", "ch"]:
            cleaned.append("chaudhry")
        elif w in ["syd"]:
            cleaned.append("syed")
        else:
            cleaned.append(w)
    return " ".join(cleaned)

def get_name_match_ratio(name1, name2):
    n1 = normalize_and_clean_name(name1)
    n2 = normalize_and_clean_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return difflib.SequenceMatcher(None, n1, n2).ratio()

def split_row_cells(row_texts):
    full_str = " | ".join(row_texts)
    cells = [c.strip() for c in full_str.split("|") if c.strip()]
    return cells

def parse_pdf_to_preview_records(file_obj):
    """
    Extracts candidate records from official result PDFs dynamically.
    Reconstructs rows page-by-page using vertical middle coordinates.
    Detects formats dynamically based on keyword patterns.
    """
    # 1. Verify text presence / scanned PDF
    try:
        file_obj.seek(0)
        reader = PdfReader(file_obj)
        total_text = ""
        for page in reader.pages:
            total_text += page.extract_text() or ""
        total_text_clean = total_text.strip()
        letters = re.findall(r'[a-zA-Z0-9]', total_text_clean)
        if len(letters) < 10:
            return "OCR_REQUIRED"
    except Exception:
        return "EXTRACTION_FAILED"

    # 2. Extract layout lines across all pages
    try:
        rsrcmgr = PDFResourceManager()
        laparams = LAParams(line_margin=0.5, word_margin=0.1)
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        
        file_obj.seek(0)
        pages = PDFPage.get_pages(file_obj)
        
        records = []
        format_detected = None
        
        # Detect format from the first page text
        first_page_text = total_text_clean.upper()
        if "INSPECTOR OF BOILERS" in first_page_text or "AGAINST OPEN MERIT" in first_page_text:
            format_detected = "PPSC_BOILERS"
        elif "TEHSILDAR" in first_page_text or ("WRITTEN EXAMINATION" in first_page_text and "BOARD OF REVENUE" in first_page_text):
            format_detected = "PPSC_TEHSILDAR"
        elif "REVISED MERIT LIST" in first_page_text or "Orbit of Selection" in first_page_text:
            format_detected = "PPSC_REVISED_MERIT_LIST"
        elif "SERGEANT DRIVER" in first_page_text:
            format_detected = "PPSC_SERGEANT"
        elif "FEDERAL PUBLIC SERVICE COMMISSION" in first_page_text and "CSS" in first_page_text:
            format_detected = "CSS_FPSC"
        else:
            return "UNKNOWN_FORMAT"
            
        for page_idx, page in enumerate(pages):
            interpreter.process_page(page)
            layout = device.get_result()
            
            text_lines = []
            def recurse_layout(obj):
                if isinstance(obj, LTTextLine):
                    text_lines.append(obj)
                elif hasattr(obj, '_objs'):
                    for child in obj._objs:
                        recurse_layout(child)
            recurse_layout(layout)
            
            if not text_lines:
                continue
                
            # Reconstruct rows by grouping elements by y coordinate
            rows_dict = {}
            y_tolerance = 14 if format_detected == "PPSC_TEHSILDAR" else 4
            for line in text_lines:
                text = line.get_text().strip()
                if not text:
                    continue
                y_mid = (line.y0 + line.y1) / 2
                
                found_row = None
                for row_y in rows_dict.keys():
                    if abs(row_y - y_mid) <= y_tolerance:
                        found_row = row_y
                        break
                if found_row is not None:
                    rows_dict[found_row].append(line)
                else:
                    rows_dict[y_mid] = [line]
                    
            sorted_y_coords = sorted(rows_dict.keys(), reverse=True)
            rows = []
            for y in sorted_y_coords:
                row_items = rows_dict[y]
                row_items.sort(key=lambda item: item.x0)
                rows.append({
                    'y': y,
                    'texts': [item.get_text().strip() for item in row_items]
                })
                
            # Parse rows based on format
            page_number = page_idx + 1
            
            if format_detected == "PPSC_BOILERS":
                i = 0
                while i < len(rows):
                    row_texts = rows[i]['texts']
                    if not row_texts:
                        i += 1
                        continue
                    first_token = row_texts[0]
                    match = re.match(r'^(\d+)/(\d+)', first_token)
                    if match:
                        merit_no = match.group(1)
                        app_no = match.group(2)
                        
                        candidate_name = ""
                        domicile = ""
                        
                        if len(row_texts) > 1:
                            row_str = " | ".join(row_texts[1:])
                            parts = [p.strip() for p in row_str.split("|") if p.strip()]
                            if len(parts) > 1:
                                candidate_name = parts[0]
                                domicile = parts[1]
                            else:
                                words = parts[0].split()
                                if len(words) > 1:
                                    domicile = words[-1]
                                    candidate_name = " ".join(words[:-1])
                                else:
                                    candidate_name = parts[0]
                                    
                        # Father name is on the next line
                        father_name = ""
                        if i + 1 < len(rows):
                            next_row = rows[i+1]
                            next_texts = next_row['texts']
                            if next_texts and not re.match(r'^(\d+)/(\d+)', next_texts[0]) and not next_texts[0].startswith("Note:"):
                                father_name = " ".join(next_texts)
                                i += 1
                                
                        records.append({
                            'candidate_name': candidate_name.strip(),
                            'father_name': father_name.strip(),
                            'roll_no': None,
                            'merit_no': merit_no,
                            'application_no': app_no,
                            'domicile': domicile.strip(),
                            'status': 'RECOMMENDED',
                            'page_number': page_number,
                            'raw_text_row': " | ".join(row_texts),
                            'extraction_confidence': 1.0,
                            'source_format': 'PPSC_BOILERS'
                        })
                    i += 1
                    
            elif format_detected == "PPSC_TEHSILDAR":
                for row in rows:
                    row_texts = row['texts']
                    full_str = " | ".join(row_texts)
                    cells = [c.strip() for c in full_str.split("|") if c.strip()]
                    if len(cells) >= 3:
                        roll_match = None
                        roll_idx = -1
                        for idx, cell in enumerate(cells[:3]):
                            if re.match(r'^\d{5}$', cell):
                                roll_match = cell
                                roll_idx = idx
                                break
                        if roll_match:
                            candidate_name = cells[roll_idx + 1]
                            father_name = " ".join(cells[roll_idx + 2:]) if roll_idx + 2 < len(cells) else ""
                            if "NAME" not in candidate_name.upper():
                                records.append({
                                    'candidate_name': candidate_name.strip(),
                                    'father_name': father_name.strip(),
                                    'roll_no': roll_match,
                                    'merit_no': None,
                                    'application_no': None,
                                    'domicile': None,
                                    'status': 'PASSED_WRITTEN',
                                    'page_number': page_number,
                                    'raw_text_row': full_str,
                                    'extraction_confidence': 1.0,
                                    'source_format': 'PPSC_TEHSILDAR'
                                })
                                
            elif format_detected == "PPSC_REVISED_MERIT_LIST":
                i = 0
                while i < len(rows):
                    row_texts = rows[i]['texts']
                    full_str = " | ".join(row_texts)
                    cells = [c.strip() for c in full_str.split("|") if c.strip()]
                    if len(cells) >= 2 and re.match(r'^\d{8}$', cells[1]):
                        app_no = cells[1]
                        merit_no = None
                        cand_idx = 2
                        if cells[2].isdigit():
                            merit_no = cells[2]
                            cand_idx = 3
                            
                        candidate_name = cells[cand_idx] if cand_idx < len(cells) else ""
                        candidate_name = re.sub(r'\s*\(.*\)', '', candidate_name).strip()
                        domicile = cells[cand_idx + 1] if cand_idx + 1 < len(cells) else ""
                        status = cells[cand_idx + 2] if cand_idx + 2 < len(cells) else "RECOMMENDED"
                        
                        father_name = ""
                        if i + 1 < len(rows):
                            next_row = rows[i+1]
                            next_full_str = " | ".join(next_row['texts'])
                            next_cells = [c.strip() for c in next_full_str.split("|") if c.strip()]
                            if next_cells and not re.match(r'^\d+$', next_cells[0]) and len(next_cells[0]) != 8:
                                if not any(kw in next_cells[0] for kw in ["Commission", "Post :", "Department:", "Note:"]):
                                    father_name = " ".join(next_cells)
                                    i += 1
                                    
                        records.append({
                            'candidate_name': candidate_name.strip(),
                            'father_name': father_name.strip(),
                            'roll_no': None,
                            'merit_no': merit_no,
                            'application_no': app_no,
                            'domicile': domicile.strip(),
                            'status': status.strip(),
                            'page_number': page_number,
                            'raw_text_row': full_str,
                            'extraction_confidence': 1.0,
                            'source_format': 'PPSC_REVISED_MERIT_LIST'
                        })
                    i += 1
                    
            elif format_detected == "PPSC_SERGEANT":
                for row in rows:
                    row_texts = row['texts']
                    full_str = " | ".join(row_texts)
                    cells = [c.strip() for c in full_str.split("|") if c.strip()]
                    if len(cells) >= 3:
                        m = re.match(r'^(\d{5})\s+(\d{8})\s+(.+)', cells[1])
                        if m:
                            roll_no = m.group(1)
                            diary_no = m.group(2)
                            candidate_name = m.group(3).strip()
                            father_name = cells[2]
                            
                            records.append({
                                'candidate_name': candidate_name,
                                'father_name': father_name,
                                'roll_no': roll_no,
                                'merit_no': None,
                                'application_no': diary_no,
                                'domicile': None,
                                'status': 'PASSED_TEST',
                                'page_number': page_number,
                                'raw_text_row': full_str,
                                'extraction_confidence': 1.0,
                                'source_format': 'PPSC_SERGEANT'
                            })
                            
            elif format_detected == "CSS_FPSC":
                for row in rows:
                    row_texts = row['texts']
                    full_str = " | ".join(row_texts)
                    cells = [c.strip() for c in full_str.split("|") if c.strip()]
                    if len(cells) >= 2 and cells[0].isdigit():
                        merit_no = cells[0]
                        m = re.match(r'^(\d{6})\s+(.+)', cells[1])
                        if m:
                            roll_no = m.group(1)
                            candidate_name = m.group(2).strip()
                            domicile = cells[2] if len(cells) > 2 else ""
                            status = cells[3] if len(cells) > 3 else "ALLOCATED"
                            
                            records.append({
                                'candidate_name': candidate_name,
                                'father_name': "",
                                'roll_no': roll_no,
                                'merit_no': merit_no,
                                'application_no': None,
                                'domicile': domicile,
                                'status': status,
                                'page_number': page_number,
                                'raw_text_row': full_str,
                                'extraction_confidence': 0.9,
                                'source_format': 'CSS_FPSC'
                            })
                            
        return records
    except Exception:
        return "EXTRACTION_FAILED"

def classify_match(candidate_name, father_name, roll_no, students):
    both_matches = []
    candidate_matches = []
    father_matches = []
    
    for student in students:
        name_ratio = get_name_match_ratio(student.full_name, candidate_name)
        father_ratio = get_name_match_ratio(student.father_name, father_name) if (father_name and student.father_name) else 0.0
        
        name_matched = (name_ratio >= 0.85)
        father_matched = (father_ratio >= 0.85) if father_name else False
        
        roll_matched = False
        if roll_no and student.roll_number:
            roll_matched = (student.roll_number.strip().lower() == roll_no.strip().lower())
            if roll_matched:
                name_matched = True
                
        if name_matched and father_matched:
            both_matches.append((student, name_ratio, father_ratio))
        elif name_matched:
            candidate_matches.append((student, name_ratio))
        elif father_matched:
            father_matches.append((student, father_ratio))
            
    if both_matches:
        if len(both_matches) > 1:
            return "AMBIGUOUS_MATCH", [m[0] for m in both_matches], max(m[1] for m in both_matches)
        else:
            student, nr, fr = both_matches[0]
            if nr == 1.0 and fr == 1.0:
                return "CONFIRMED_MATCH", [student], 1.0
            else:
                return "POSSIBLE_MATCH", [student], (nr + fr) / 2
                
    if candidate_matches:
        if len(candidate_matches) > 1:
            return "AMBIGUOUS_MATCH", [m[0] for m in candidate_matches], max(m[1] for m in candidate_matches)
        else:
            student, nr = candidate_matches[0]
            return "NAME_ONLY_PARTIAL", [student], nr
            
    if father_matches:
        if len(father_matches) > 1:
            return "AMBIGUOUS_MATCH", [m[0] for m in father_matches], max(m[1] for m in father_matches)
        else:
            student, fr = father_matches[0]
            return "FATHER_ONLY_PARTIAL", [student], fr
            
    return "UNMATCHED", [], 0.0

def match_students_preview(extracted_records):
    """
    Fuzzy match extracted records against Student database.
    Does NOT modify database. Returns a list of dicts with match results and full student info.
    """
    matched_results = []
    students = list(Student.objects.filter(is_deleted=False).prefetch_related('enrollments__session'))
    
    for record in extracted_records:
        candidate_name = record['candidate_name']
        father_name = record['father_name']
        roll_no = record['roll_no']
        
        status, matched_students, confidence = classify_match(candidate_name, father_name, roll_no, students)
        
        student_info = None
        if matched_students:
            student = matched_students[0]
            active_enrollment = student.enrollments.filter(status="Active").first()
            enrollment_status = student.status
            session_name = "No Active Session"
            batch_number = ""
            class_name = ""
            
            if active_enrollment:
                session_name = active_enrollment.session.name
                batch_number = active_enrollment.session.batch_number
                class_name = active_enrollment.session.session_category
                enrollment_status = active_enrollment.status
                
            student_info = {
                'id': student.id,
                'full_name': student.full_name,
                'father_name': student.father_name or "",
                'cnic': student.cnic or "",
                'roll_number': student.roll_number or "",
                'admission_number': student.id,
                'session_name': session_name,
                'batch_number': batch_number,
                'class_name': class_name,
                'phone': student.phone or "",
                'status': enrollment_status,
                'profile_url': f"/panel/admin/students/{student.id}/"
            }
            
        matched_results.append({
            'extracted_record': record,
            'status': status,
            'confidence': confidence * 100,
            'student_info': student_info,
            'all_matched_student_ids': [s.id for s in matched_students]
        })
        
    return matched_results

