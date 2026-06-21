import csv
import uuid
import os
import re
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache

from apps.core.decorators import role_required
from apps.documents.models import ComparisonJob, ComparisonResult
from apps.documents.services import (
    process_result_pdf,
    parse_pdf_to_preview_records,
    match_students_preview,
)

@role_required("Admin", "Principal", "Registrar")
def pdf_comparison(request):
    # Support clearing the preview
    if request.GET.get("clear") == "1":
        if "pdf_comparison_preview" in request.session:
            del request.session["pdf_comparison_preview"]
        messages.success(request, "Preview cleared successfully.")
        return redirect("/panel/admin/pdf-comparison/")

    selected_job = None
    job_id = request.GET.get("job_id")

    if job_id:
        try:
            selected_job = ComparisonJob.objects.prefetch_related("results__student__enrollments__session").get(pk=job_id)
        except (ComparisonJob.DoesNotExist, ValueError):
            pass

    if request.method == "POST":
        uploaded_file = request.FILES.get("pdf_file")
        exam_type = request.POST.get("exam_type")

        if not uploaded_file:
            messages.error(request, "Please select a PDF file to upload.")
            return redirect("/panel/admin/pdf-comparison/")

        if not exam_type:
            messages.error(request, "Please select an exam type.")
            return redirect("/panel/admin/pdf-comparison/")

        # 1. Validate File Extension
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext != ".pdf":
            messages.error(request, "Invalid file format. Only .pdf files are accepted.")
            return redirect("/panel/admin/pdf-comparison/")

        # 2. Validate MIME type
        if uploaded_file.content_type != "application/pdf":
            messages.error(request, "Invalid file type. File MIME type must be application/pdf.")
            return redirect("/panel/admin/pdf-comparison/")

        # 3. Validate File Size (max 5MB)
        if uploaded_file.size > 5 * 1024 * 1024:
            messages.error(request, "File size exceeds the 5MB limit.")
            return redirect("/panel/admin/pdf-comparison/")

        # 4. Sanitize Filename (no path traversal, keep safe chars)
        base_name = os.path.basename(uploaded_file.name)
        sanitized_name = re.sub(r'[^a-zA-Z0-9_\.\-]', '_', base_name)

        try:
            # Run parser in-memory
            records = parse_pdf_to_preview_records(uploaded_file)
            
            if records == "OCR_REQUIRED":
                messages.error(request, "This PDF appears to be a scanned document with no extractable text. OCR is required.")
                return redirect("/panel/admin/pdf-comparison/")
            elif records == "EXTRACTION_FAILED":
                messages.error(request, "Failed to parse text from the uploaded PDF.")
                return redirect("/panel/admin/pdf-comparison/")
            elif records == "UNKNOWN_FORMAT":
                messages.error(request, "Unknown PDF result format. Layout does not match supported government exam formats.")
                return redirect("/panel/admin/pdf-comparison/")
                
            if isinstance(records, list):
                # 5. Row limit cap
                if len(records) > 1000:
                    messages.error(request, f"The uploaded PDF contains too many candidate records ({len(records)}). The maximum limit is 1000 rows.")
                    return redirect("/panel/admin/pdf-comparison/")
                    
                # Run matching engine
                matched_results = match_students_preview(records)
                
                # Save to cache
                preview_id = str(uuid.uuid4())
                cache.set(f"pdf_preview:{preview_id}", matched_results, timeout=1800)
                
                # Store compact info in session
                request.session['pdf_comparison_preview'] = {
                    'preview_id': preview_id,
                    'summary': {
                        'total': len(matched_results),
                        'confirmed': sum(1 for r in matched_results if r['status'] == 'CONFIRMED_MATCH'),
                        'possible': sum(1 for r in matched_results if r['status'] == 'POSSIBLE_MATCH'),
                        'name_only': sum(1 for r in matched_results if r['status'] == 'NAME_ONLY_PARTIAL'),
                        'father_only': sum(1 for r in matched_results if r['status'] == 'FATHER_ONLY_PARTIAL'),
                        'ambiguous': sum(1 for r in matched_results if r['status'] == 'AMBIGUOUS_MATCH'),
                        'unmatched': sum(1 for r in matched_results if r['status'] == 'UNMATCHED'),
                    },
                    'filename': sanitized_name,
                    'exam_type': exam_type,
                }
                
                messages.success(request, f"PDF comparison completed successfully! Parsed {len(records)} candidates.")
                return redirect("/panel/admin/pdf-comparison/")
        except Exception as e:
            messages.error(request, f"An unexpected error occurred during processing: {str(e)}")
            return redirect("/panel/admin/pdf-comparison/")

    # Fetch recent jobs
    recent_jobs = ComparisonJob.objects.select_related("uploaded_by").order_by("-uploaded_at")[:10]

    preview = request.session.get('pdf_comparison_preview')
    preview_results = []
    
    if preview:
        preview_id = preview['preview_id']
        cached_results = cache.get(f"pdf_preview:{preview_id}")
        if cached_results:
            preview_results = cached_results
            
            # Apply search filters
            q = request.GET.get('q', '').strip()
            status_filter = request.GET.get('status', '').strip()
            
            if status_filter:
                preview_results = [r for r in preview_results if r['status'] == status_filter]
                
            if q:
                q_lower = q.lower()
                filtered = []
                for r in preview_results:
                    cand_name = r['extracted_record']['candidate_name'].lower()
                    father_name = r['extracted_record']['father_name'].lower()
                    roll = (r['extracted_record']['roll_no'] or "").lower()
                    found = (q_lower in cand_name or q_lower in father_name or q_lower in roll)
                    
                    if not found and r['student_info']:
                        s_name = r['student_info']['full_name'].lower()
                        s_father = r['student_info']['father_name'].lower()
                        s_roll = r['student_info']['roll_number'].lower()
                        s_id = str(r['student_info']['id'])
                        found = (q_lower in s_name or q_lower in s_father or q_lower in s_roll or q_lower in s_id)
                        
                    if found:
                        filtered.append(r)
                preview_results = filtered
        else:
            # Cache expired
            if 'pdf_comparison_preview' in request.session:
                del request.session['pdf_comparison_preview']
            preview = None

    # Calculate matched/unmatched lists if a DB job is selected (for backward compatibility)
    matched_results = []
    unmatched_results = []
    if selected_job:
        for res in selected_job.results.all():
            session_name = "No Active Session"
            if res.student:
                active_enrollment = res.student.enrollments.filter(status="Active").first()
                if active_enrollment:
                    session_name = active_enrollment.session.name

            result_item = {
                'student_name': res.student.full_name if res.student else "Not Matched",
                'extracted_name': res.extracted_name,
                'session': session_name,
                'roll': res.extracted_roll or "-",
                'confidence': res.match_confidence * 100,
                'is_exact': res.is_exact_match,
            }
            if res.student:
                matched_results.append(result_item)
            else:
                unmatched_results.append(result_item)

    context = {
        "selected_job": selected_job,
        "recent_jobs": recent_jobs,
        "matched_results": matched_results,
        "unmatched_results": unmatched_results,
        "preview": preview,
        "preview_results": preview_results,
        "q": request.GET.get('q', ''),
        "status_filter": request.GET.get('status', ''),
        "exam_types": [c[0] for c in ComparisonJob.EXAM_TYPE_CHOICES],
    }

    return render(request, "documents/pdf_comparison.html", context)

@role_required("Admin", "Principal", "Registrar")
def export_comparison_csv(request, job_id):
    job = get_object_or_404(ComparisonJob, pk=job_id)
    results = ComparisonResult.objects.filter(job=job).select_related("student__enrollments__session")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="comparison_results_{job.exam_type}_{job.id}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Extracted Name", "Student Name", "Session", "Roll Number", "Confidence (%)", "Is Exact Match"])

    for res in results:
        session_name = "No Active Session"
        student_name = "Not Matched"
        if res.student:
            student_name = res.student.full_name
            active_enrollment = res.student.enrollments.filter(status="Active").first()
            if active_enrollment:
                session_name = active_enrollment.session.name

        writer.writerow([
            res.extracted_name,
            student_name,
            session_name,
            res.extracted_roll or "-",
            f"{res.match_confidence * 100:.1f}" if res.match_confidence <= 1.0 else f"{res.match_confidence:.1f}",
            "Yes" if res.is_exact_match else "No"
        ])

    return response

@role_required("Admin", "Principal", "Registrar")
def export_preview_csv(request):
    preview = request.session.get('pdf_comparison_preview')
    if not preview:
        raise Http404("No active preview session.")
        
    preview_id = preview['preview_id']
    results = cache.get(f"pdf_preview:{preview_id}")
    if not results:
        raise Http404("Preview data has expired.")

    response = HttpResponse(content_type="text/csv")
    exam_type_val = preview['exam_type']
    response["Content-Disposition"] = f'attachment; filename="preview_results_{exam_type_val}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Candidate Name (PDF)", "Father Name (PDF)", "Roll No", "Merit No", 
        "Domicile", "Match Status", "Confidence (%)", "Matched Student ID", "Matched Student Name"
    ])

    for res in results:
        rec = res['extracted_record']
        student_id = res['student_info']['id'] if res['student_info'] else "-"
        student_name = res['student_info']['full_name'] if res['student_info'] else "-"
        
        writer.writerow([
            rec['candidate_name'],
            rec['father_name'] or "-",
            rec['roll_no'] or "-",
            rec['merit_no'] or "-",
            rec['domicile'] or "-",
            res['status'],
            f"{res['confidence']:.1f}",
            student_id,
            student_name
        ])

    return response

