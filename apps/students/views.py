from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Sum

from apps.students.models import Student, Enrollment
from apps.students.forms import StudentCreateForm
from apps.students.services import StudentService, EnrollmentService
from apps.attendance.services import AttendanceService
from apps.finance.services import calculate_student_ledger
from apps.core.services import DomainValidationError
from apps.core.decorators import role_required

try:
    from apps.attendance.models import attendance
except ImportError:
    attendance = None

try:
    from apps.achievements.models import Achievement
except ImportError:
    Achievement = None


def _placeholder(name):
    """Create a placeholder view that raises Http404."""
    def view(request, *args, **kwargs):
        raise Http404(f"View {name} is not implemented yet.")
    view.__name__ = name
    view.__qualname__ = name
    return view


def redirect_to_student_view(request, view_name, *args, **kwargs):
    """Dynamic redirect helper to avoid hardcoding admin_panel:students: namespace."""
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if 'registrar_panel' in namespaces:
        mapped_name = view_name
        if view_name == "manage_students":
            mapped_name = "student_list"
        elif view_name == "add_student":
            mapped_name = "student_create"
        elif view_name == "student_documents":
            mapped_name = "student_detail"
        try:
            return redirect(f"registrar_panel:{mapped_name}", *args, **kwargs)
        except Exception:
            pass
    try:
        return redirect(f"admin_panel:{view_name}", *args, **kwargs)
    except Exception:
        pass
    try:
        mapped_name = view_name
        if view_name == "manage_students":
            mapped_name = "student_list"
        elif view_name == "add_student":
            mapped_name = "student_create"
        return redirect(f"admin_panel:students:{mapped_name}", *args, **kwargs)
    except Exception:
        pass
    return redirect("admin_panel:dashboard")


# -------------------------------------------------------------------
#  Student views
# -------------------------------------------------------------------

@login_required
@role_required("Admin", "Principal", "Registrar")
def student_list(request):
    """List all students with basic search and pagination."""
    from django.core.paginator import Paginator
    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    students = Student.objects.all()
    if query:
        students = students.filter(full_name__icontains=query) | students.filter(roll_number__icontains=query)
    if status_filter:
        students = students.filter(status=status_filter)

    paginator = Paginator(students, 25)  # Page size 25
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "student_list": page_obj.object_list,
        "query": query,
        "status_filter": status_filter,
        "role": "Admin",
    }
    return render(request, "students/student_list.html", context)


@login_required
def student_create(request):
    if not request.user.groups.filter(
        name__in=["Admin", "Registrar"]
    ).exists():
        raise Http404

    from apps.students.forms import StudentCreateForm

    if request.method == "POST":
        form = StudentCreateForm(
            request.POST,
            request.FILES,
        )
        if form.is_valid():
            uploaded_files_to_cleanup = []
            try:
                with transaction.atomic():
                    # Create student
                    student = StudentService.create_student(
                        full_name=form.cleaned_data["full_name"],
                        father_name=form.cleaned_data.get(
                            "father_name", ""
                        ),
                        email=form.cleaned_data.get(
                            "email", ""
                        ),
                        phone=form.cleaned_data.get(
                            "phone", ""
                        ),
                        date_of_birth=form.cleaned_data.get(
                            "date_of_birth"
                        ),
                        cnic=form.cleaned_data.get(
                            "cnic", ""
                        ),
                        address=form.cleaned_data.get(
                            "address", ""
                        ),
                        gender=form.cleaned_data.get(
                            "gender", ""
                        ),
                        created_by=request.user,
                    )

                    # Save profile photo if uploaded
                    photo = form.cleaned_data.get(
                        "profile_photo"
                    )
                    if photo:
                        student.profile_photo = photo
                        student.save(
                            update_fields=["profile_photo"]
                        )
                        if student.profile_photo and hasattr(student.profile_photo, 'path'):
                            uploaded_files_to_cleanup.append(student.profile_photo.path)

                    # Save CNIC photo if uploaded
                    cnic_photo = form.cleaned_data.get("cnic_photo")
                    if cnic_photo:
                        from apps.students.models import StudentDocument
                        import mimetypes
                        mime_type, _ = mimetypes.guess_type(cnic_photo.name)
                        doc = StudentDocument(
                            student=student,
                            document_type="cnic_front",
                            title="CNIC Front",
                            file=cnic_photo,
                            file_size=cnic_photo.size,
                            mime_type=mime_type or 'image/jpeg',
                            uploaded_by=request.user,
                        )
                        doc.save()
                        if doc.file and hasattr(doc.file, 'path'):
                            uploaded_files_to_cleanup.append(doc.file.path)

                    # Enroll in session if selected
                    session = form.cleaned_data.get("session")
                    enrollment = None
                    if session:
                        enrollment = (
                            EnrollmentService.create_enrollment(
                                student_id=student.pk,
                                session_id=session.pk,
                                user=request.user,
                            )
                        )

                    # Setup fee structure if fee info provided
                    if (
                        enrollment
                        and form.cleaned_data.get("fee_type")
                        and form.cleaned_data.get(
                            "total_fee_amount"
                        )
                    ):
                        from apps.finance.services import (
                            setup_enrollment_fee,
                        )
                        setup_enrollment_fee(
                            enrollment_id=enrollment.pk,
                            fee_type=form.cleaned_data[
                                "fee_type"
                            ],
                            total_amount=form.cleaned_data[
                                "total_fee_amount"
                            ],
                            number_of_installments=(
                                form.cleaned_data.get(
                                    "number_of_installments"
                                ) or 1
                            ),
                            due_day=(
                                form.cleaned_data.get(
                                    "due_day"
                                ) or 10
                            ),
                            created_by=request.user,
                        )

                success_msg = f"Student {student.full_name} registered successfully."
                if hasattr(student, "_portal_password") and student._portal_password:
                    success_msg += f" Portal account created. Username: {student._portal_username} | Password: {student._portal_password} (Shown only once)"
                messages.success(
                    request,
                    success_msg,
                )
                return redirect_to_student_view(request, "student_detail", pk=student.pk)

            except Exception as exc:
                import os
                for filepath in uploaded_files_to_cleanup:
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception as clean_err:
                        import logging
                        logging.getLogger("crm.students").error(f"Error cleaning up orphan file {filepath}: {clean_err}")
                messages.error(
                    request,
                    f"Error creating student: {exc}",
                )
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = StudentCreateForm()

    return render(
        request,
        "students/student_form.html",
        {
            "form": form,
            "page_title": "Register New Student",
        },
    )


@login_required
def student_detail(request, pk):
    from decimal import Decimal
    from django.db.models import Count as DCount, Sum as DSum

    student = get_object_or_404(Student, pk=pk)

    if not request.user.groups.filter(
        name__in=["Admin", "Principal", "Registrar",
                  "Teacher", "Accountant"]
    ).exists():
        from django.http import Http404
        raise Http404

    # --- Safe defaults (ALWAYS set before any DB call) ---
    enrollment = None
    attendance_counts = {}
    attendance_percentage = 0
    present_count = 0
    absent_count = 0
    late_count = 0
    total_classes = 0
    ledger = {}
    total_fee = Decimal("0.00")
    amount_paid = Decimal("0.00")
    outstanding = Decimal("0.00")
    discount = Decimal("0.00")
    exam_results = []
    achievements_list = []
    timetable = []
    payments = []
    all_enrollments = []

    # --- Enrollment ---
    try:
        all_enrollments = (
            Enrollment.objects
            .select_related("session")
            .filter(student=student)
            .order_by("-created_at")
        )
        enrollment = all_enrollments.first()
    except Exception:
        all_enrollments = []
        enrollment = None

    # --- Attendance ---
    try:
        if attendance:
            att_rows = (
                attendance.objects
                .filter(enrollment__student=student)
                .values("status")
                .annotate(count=DCount("id"))
            )
            for row in att_rows:
                attendance_counts[row["status"]] = row["count"]
            present_count = attendance_counts.get("present", 0)
            late_count = attendance_counts.get("late", 0)
            absent_count = attendance_counts.get("absent", 0)
            total_classes = (
                present_count + late_count + absent_count
            )
            if total_classes > 0:
                attendance_percentage = round(
                    ((present_count + late_count) / total_classes)
                    * 100,
                    1,
                )
    except Exception:
        pass

    # --- Finance Ledger & Installments ---
    fee_summary = {
        "total_installments": 0,
        "total_amount": Decimal("0.00"),
        "total_paid": Decimal("0.00"),
        "total_outstanding": Decimal("0.00"),
        "pending_installments": 0,
        "paid_installments": 0,
        "overdue_installments": 0,
        "installments": [],
        "completion_percentage": 0,
    }

    try:
        if enrollment:
            from apps.finance.services import (
                calculate_student_ledger,
                get_enrollment_fee_summary,
            )
            ledger = calculate_student_ledger(enrollment.pk)
            if ledger:
                total_fee = ledger.get(
                    "total_fee", Decimal("0.00")
                )
                amount_paid = ledger.get(
                    "amount_paid", Decimal("0.00")
                )
                outstanding = ledger.get(
                    "outstanding", Decimal("0.00")
                )
                discount = ledger.get(
                    "discount", Decimal("0.00")
                )

            # Fetch Installments fee summary
            fee_summary = get_enrollment_fee_summary(enrollment.pk)
    except Exception:
        pass

    # --- Payments ---
    try:
        if enrollment:
            from apps.finance.models import Payment
            payments = (
                Payment.objects
                .filter(enrollment=enrollment)
                .order_by("-payment_date")
            )
    except Exception:
        payments = []

    # --- Exam Results ---
    try:
        from apps.exams.models import StudentMark
        exam_results = (
            StudentMark.objects
            .select_related("exam", "exam__subject")
            .filter(
                student=student,
                exam__status="published",
            )
            .order_by("-exam__exam_date")
        )
    except Exception:
        exam_results = []

    # --- Achievements ---
    try:
        if Achievement:
            achievements_list = (
                Achievement.objects
                .filter(student=student)
                .order_by("-year")
            )
    except Exception:
        achievements_list = []

    # --- Timetable ---
    try:
        if enrollment and enrollment.session:
            from apps.academics.models import ClassSchedule
            timetable = (
                ClassSchedule.objects
                .select_related("subject", "teacher")
                .filter(session=enrollment.session)
                .order_by("day_of_week", "start_time")
            )
    except Exception:
        timetable = []

    cnic_doc = student.documents.filter(document_type="cnic_front").first()
    context = {
        "student": student,
        "enrollment": enrollment,
        "all_enrollments": all_enrollments,
        "attendance_counts": attendance_counts,
        "attendance_percentage": attendance_percentage,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "total_classes": total_classes,
        "ledger": ledger,
        "total_fee": total_fee,
        "amount_paid": amount_paid,
        "outstanding": outstanding,
        "discount": discount,
        "fee_summary": fee_summary,
        "exam_results": exam_results,
        "achievements": achievements_list,
        "timetable": timetable,
        "payments": payments,
        "cnic_doc": cnic_doc,
        "page_title": f"Student: {student.full_name}",
    }
    return render(
        request, "students/student_detail.html", context
    )


# Placeholder views for editing, delete, etc.
@login_required
@role_required("Admin", "Registrar")
def student_edit(request, pk):
    from apps.students.models import Student, StudentDocument
    from apps.students.forms import StudentForm
    student = get_object_or_404(Student, pk=pk)

    cnic_doc = student.documents.filter(document_type="cnic_front").first()

    if request.method == "POST":
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            with transaction.atomic():
                form.save()
                cnic_photo = form.cleaned_data.get("cnic_photo")
                if cnic_photo:
                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(cnic_photo.name)
                    
                    if cnic_doc:
                        # delete old physical file safely
                        try:
                            import os
                            if cnic_doc.file and os.path.exists(cnic_doc.file.path):
                                os.remove(cnic_doc.file.path)
                        except Exception as e:
                            import logging
                            logging.getLogger("crm.students").error(f"Error removing old CNIC file: {e}")
                        
                        cnic_doc.file = cnic_photo
                        cnic_doc.file_size = cnic_photo.size
                        cnic_doc.mime_type = mime_type or 'image/jpeg'
                        cnic_doc.uploaded_by = request.user
                        cnic_doc.save()
                    else:
                        StudentDocument.objects.create(
                            student=student,
                            document_type="cnic_front",
                            title="CNIC Front",
                            file=cnic_photo,
                            file_size=cnic_photo.size,
                            mime_type=mime_type or 'image/jpeg',
                            uploaded_by=request.user,
                        )
            messages.success(request, f"Student {student.full_name} updated successfully.")
            return redirect_to_student_view(request, "student_detail", pk=student.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = StudentForm(instance=student)

    return render(request, "students/student_form.html", {
        "form": form,
        "student": student,
        "student_cnic_doc": cnic_doc,
        "page_title": f"Edit Student: {student.full_name}"
    })

@login_required
@role_required("Admin", "Registrar")
def student_delete(request, pk):
    from apps.students.models import Student
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.status = "Inactive"
        student.save()
        messages.success(request, f"Student {student.full_name} successfully marked as Inactive (Deleted).")
    else:
        messages.error(request, "Invalid request method.")
    return redirect_to_student_view(request, "manage_students")

@login_required
@role_required("Admin", "Registrar")
def student_restore(request, pk):
    from apps.students.models import Student
    student = get_object_or_404(Student, pk=pk)
    if request.method == "POST":
        student.status = "Active"
        student.save()
        messages.success(request, f"Student {student.full_name} successfully restored to Active.")
    else:
        messages.error(request, "Invalid request method.")
    return redirect_to_student_view(request, "student_detail", pk=pk)
@login_required
@role_required("Admin", "Registrar", "Principal")
def student_documents(request, pk):
    from apps.students.models import Student, StudentDocument
    from apps.students.forms import StudentDocumentForm
    student = get_object_or_404(Student, pk=pk)
    documents = StudentDocument.objects.filter(student=student).order_by('-created_at')
    form = StudentDocumentForm()

    return render(request, "students/student_documents.html", {
        "student": student,
        "documents": documents,
        "form": form,
        "page_title": f"Manage Documents: {student.full_name}"
    })

@login_required
@role_required("Admin", "Registrar", "Principal")
def student_document_upload(request, pk):
    from apps.students.models import Student
    from apps.students.forms import StudentDocumentForm
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        form = StudentDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.student = student
            document.uploaded_by = request.user
            if document.file:
                document.file_size = document.file.size
                import mimetypes
                mime_type, _ = mimetypes.guess_type(document.file.name)
                document.mime_type = mime_type or 'application/octet-stream'
            document.save()
            messages.success(request, "Document uploaded successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        messages.error(request, "Invalid request method.")

    return redirect_to_student_view(request, "student_documents", pk=pk)
@login_required
@role_required("Admin", "Registrar")
def student_guardians(request, pk):
    from apps.students.models import Student, Guardian
    from apps.students.forms import GuardianForm
    student = get_object_or_404(Student, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_new":
            form = GuardianForm(request.POST)
            if form.is_valid():
                guardian = form.save(commit=False)
                guardian.student = student
                guardian.save()
                messages.success(request, f"New guardian {guardian.full_name} added successfully.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        elif action == "link_existing":
            guardian_id = request.POST.get("guardian_id")
            if guardian_id:
                try:
                    existing_guardian = Guardian.objects.get(pk=guardian_id)
                    # Duplicate the record and link to current student
                    existing_guardian.pk = None
                    existing_guardian.student = student
                    existing_guardian.save()
                    messages.success(request, f"Guardian {existing_guardian.full_name} successfully linked.")
                except Guardian.DoesNotExist:
                    messages.error(request, "Selected guardian does not exist.")
            else:
                messages.error(request, "Please select a guardian to link.")

        return redirect_to_student_view(request, "student_detail", pk=pk)

    form = GuardianForm()
    available_guardians = Guardian.objects.exclude(student=student).order_by("full_name")

    return render(request, "students/student_guardians.html", {
        "student": student,
        "form": form,
        "available_guardians": available_guardians,
        "page_title": f"Manage Guardians: {student.full_name}"
    })
@login_required
@role_required("Admin", "Registrar", "Accountant")
def student_ledger(request, pk):
    from apps.students.models import Student, Enrollment
    from apps.finance.models import Payment, InstallmentPlan
    from django.db.models import Sum
    student = get_object_or_404(Student, pk=pk)

    enrollments = Enrollment.objects.filter(student=student)
    payments = Payment.objects.filter(enrollment__student=student).order_by('-payment_date')
    installment_plans = InstallmentPlan.objects.filter(enrollment__student=student)

    total_paid = payments.filter(payment_status='confirmed').aggregate(Sum('amount'))['amount__sum'] or 0
    total_due = installment_plans.aggregate(Sum('total_amount'))['total_amount__sum'] or 0


    return render(request, "students/student_ledger.html", {
        "student": student,
        "enrollments": enrollments,
        "payments": payments,
        "installment_plans": installment_plans,
        "total_paid": total_paid,
        "total_due": total_due,
        "page_title": f"Financial Ledger: {student.full_name}"
    })

# -------------------------------------------------------------------
#  Lead views (Placeholders)
# -------------------------------------------------------------------
@login_required
@role_required("Admin", "Registrar", "Receptionist")
def lead_list(request):
    from apps.students.models import Lead
    from django.core.paginator import Paginator
    from django.db.models import Q

    query = request.GET.get("q", "")
    status_filter = request.GET.get("status", "")

    leads = Lead.objects.all().order_by('-inquiry_date')
    if query:
        leads = leads.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(area_of_residence__icontains=query)
        )
    if status_filter:
        leads = leads.filter(status=status_filter)

    paginator = Paginator(leads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "students/lead_list.html", {
        "page_obj": page_obj,
        "leads": page_obj.object_list,
        "query": query,
        "status_filter": status_filter,
        "page_title": "Lead Management"
    })

@login_required
@role_required("Admin", "Registrar", "Receptionist")
def lead_create(request):
    from apps.students.forms import LeadForm
    if request.method == "POST":
        form = LeadForm(request.POST)
        if form.is_valid():
            lead = form.save(commit=False)
            lead.handled_by = request.user
            lead.save()
            messages.success(request, f"Lead {lead.name} created successfully.")
            namespaces = request.resolver_match.namespaces if request.resolver_match else []
            if 'registrar_panel' in namespaces:
                return redirect("registrar_panel:lead_list")
            return redirect("admin_panel:students:lead_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LeadForm()

    return render(request, "students/lead_form.html", {
        "form": form,
        "page_title": "Create Lead"
    })

@login_required
@role_required("Admin", "Registrar", "Receptionist")
def lead_detail(request, pk):
    from apps.students.models import Lead
    lead = get_object_or_404(Lead, pk=pk)
    return render(request, "students/lead_detail.html", {
        "lead": lead,
        "page_title": f"Lead: {lead.name}"
    })

@login_required
@role_required("Admin", "Registrar", "Receptionist")
def lead_edit(request, pk):
    from apps.students.models import Lead
    from apps.students.forms import LeadForm
    lead = get_object_or_404(Lead, pk=pk)

    if request.method == "POST":
        form = LeadForm(request.POST, instance=lead)
        if form.is_valid():
            form.save()
            messages.success(request, f"Lead {lead.name} updated successfully.")
            namespaces = request.resolver_match.namespaces if request.resolver_match else []
            if 'registrar_panel' in namespaces:
                return redirect("registrar_panel:lead_detail", pk=lead.pk)
            return redirect("admin_panel:students:lead_detail", pk=lead.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = LeadForm(instance=lead)

    return render(request, "students/lead_form.html", {
        "form": form,
        "lead": lead,
        "page_title": f"Edit Lead: {lead.name}"
    })

@login_required
@role_required("Admin", "Registrar", "Receptionist")
def lead_convert(request, pk):
    from apps.students.models import Lead, Student
    lead = get_object_or_404(Lead, pk=pk)
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if request.method == "POST":
        if lead.status == "Converted":
            messages.error(request, "This lead is already converted.")
            if 'registrar_panel' in namespaces:
                return redirect("registrar_panel:lead_detail", pk=pk)
            return redirect("admin_panel:students:lead_detail", pk=pk)

        student = Student.objects.create(
            full_name=lead.name,
            email=lead.email,
            phone=lead.phone,
            address_temporary=lead.area_of_residence,
            status="Active",
        )

        lead.status = "Converted"
        lead.converted_student = student
        lead.save()

        messages.success(request, f"Lead {lead.name} successfully converted to Student.")
        if 'registrar_panel' in namespaces:
            return redirect("registrar_panel:student_detail", pk=student.pk)
        return redirect("admin_panel:students:student_detail", pk=student.pk)
    else:
        messages.error(request, "Invalid request method.")
    if 'registrar_panel' in namespaces:
        return redirect("registrar_panel:lead_detail", pk=pk)
    return redirect("admin_panel:students:lead_detail", pk=pk)

# -------------------------------------------------------------------
#  Enrollment views (Placeholders)
# -------------------------------------------------------------------
@login_required
@role_required("Admin", "Registrar")
def enrollment_list(request):
    from apps.students.models import Enrollment
    enrollments = Enrollment.objects.select_related('student', 'session').order_by('-created_at')
    return render(request, "students/enrollment_list.html", {
        "enrollments": enrollments,
        "page_title": "All Enrollments"
    })

@login_required
@role_required("Admin", "Registrar")
def enrollment_create(request):
    from apps.students.forms import EnrollmentForm
    if request.method == "POST":
        form = EnrollmentForm(request.POST)
        if form.is_valid():
            from apps.students.services import EnrollmentService
            try:
                enrollment = EnrollmentService.create_enrollment(
                    student_id=form.cleaned_data["student"].pk,
                    session_id=form.cleaned_data["session"].pk,
                    user=request.user,
                    registration_fee=form.cleaned_data.get("registration_fee"),
                    fee=form.cleaned_data.get("fee"),
                    discount=form.cleaned_data.get("discount")
                )
                messages.success(request, f"Enrollment for {enrollment.student.full_name} created successfully.")
                namespaces = request.resolver_match.namespaces if request.resolver_match else []
                if 'registrar_panel' in namespaces:
                    return redirect("registrar_panel:enrollment_detail", pk=enrollment.pk)
                return redirect("admin_panel:students:enrollment_detail", pk=enrollment.pk)
            except Exception as e:
                messages.error(request, f"Enrollment failed: {e}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        initial = {}
        student_id = request.GET.get("student")
        if student_id:
            initial["student"] = student_id
        form = EnrollmentForm(initial=initial)

    return render(request, "students/enrollment_form.html", {
        "form": form,
        "page_title": "Create Enrollment"
    })

@login_required
@role_required("Admin", "Registrar")
def enrollment_detail(request, pk):
    from apps.students.models import Enrollment
    enrollment = get_object_or_404(Enrollment, pk=pk)
    return render(request, "students/enrollment_detail.html", {
        "enrollment": enrollment,
        "page_title": f"Enrollment Details: {enrollment.student.full_name}"
    })

@login_required
@role_required("Admin", "Registrar")
def enrollment_withdraw(request, pk):
    from apps.students.models import Enrollment
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == "POST":
        enrollment.status = "Withdrawn"
        enrollment.save()
        messages.success(request, f"Enrollment for {enrollment.student.full_name} successfully withdrawn.")
    else:
        messages.error(request, "Invalid request method.")
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if 'registrar_panel' in namespaces:
        return redirect("registrar_panel:enrollment_detail", pk=pk)
    return redirect("admin_panel:students:enrollment_detail", pk=pk)

@login_required
@role_required("Admin", "Registrar")
def enrollment_restore(request, pk):
    from apps.students.models import Enrollment
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == "POST":
        enrollment.status = "Active"
        enrollment.save()
        messages.success(request, f"Enrollment for {enrollment.student.full_name} successfully restored to Active.")
    else:
        messages.error(request, "Invalid request method.")
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if 'registrar_panel' in namespaces:
        return redirect("registrar_panel:enrollment_detail", pk=pk)
    return redirect("admin_panel:students:enrollment_detail", pk=pk)

@login_required
@role_required("Admin", "Registrar")
def enrollment_freeze(request, pk):
    from apps.students.models import Enrollment
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == "POST":
        enrollment.status = "Frozen"
        enrollment.save()
        messages.success(request, f"Enrollment for {enrollment.student.full_name} successfully frozen.")
    else:
        messages.error(request, "Invalid request method.")
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if 'registrar_panel' in namespaces:
        return redirect("registrar_panel:enrollment_detail", pk=pk)
    return redirect("admin_panel:students:enrollment_detail", pk=pk)

@login_required
@role_required("Admin", "Registrar")
def enrollment_unfreeze(request, pk):
    from apps.students.models import Enrollment
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == "POST":
        enrollment.status = "Active"
        enrollment.save()
        messages.success(request, f"Enrollment for {enrollment.student.full_name} successfully unfrozen.")
    else:
        messages.error(request, "Invalid request method.")
    namespaces = request.resolver_match.namespaces if request.resolver_match else []
    if 'registrar_panel' in namespaces:
        return redirect("registrar_panel:enrollment_detail", pk=pk)
    return redirect("admin_panel:students:enrollment_detail", pk=pk)

@login_required
@role_required("Admin", "Principal")
def enrollment_transfer(request, pk):
    """POST view to transfer student to a new session."""
    enrollment = get_object_or_404(Enrollment, pk=pk)
    if request.method == "POST":
        new_session_id = request.POST.get("new_session_id")
        if new_session_id:
            try:
                from apps.students.services import EnrollmentService
                EnrollmentService.transfer_student_to_session(
                    student_id=enrollment.student_id,
                    new_session_id=new_session_id,
                    user=request.user,
                )
                messages.success(request, "Student successfully transferred to new session.")
            except Exception as e:
                messages.error(request, f"Transfer failed: {str(e)}")
        else:
            messages.error(request, "No target session selected.")
    return redirect(reverse("admin_panel:students:student_detail", args=[enrollment.student_id]))

@login_required
def student_reset_password(request, pk):
    from apps.students.models import Student
    if not request.user.groups.filter(
        name__in=["Admin"]
    ).exists():
        raise Http404
    student = get_object_or_404(Student, pk=pk)

    if not hasattr(student, "portal_user") or not student.portal_user:
        messages.error(
            request,
            "No portal account found for this student."
        )
        return redirect(
            "admin_panel:students:student_detail", pk=pk
        )

    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    new_password = "".join(
        secrets.choice(alphabet) for _ in range(12)
    )
    student.portal_user.set_password(new_password)
    student.portal_user.save()
    messages.success(
        request,
        f"Password reset for {student.full_name}. "
        f"New password: {new_password} "
        f"(Shown only once - please save it)"
    )
    return redirect(
        "admin_panel:students:student_detail", pk=pk
    )

@login_required
def student_create_login(request, pk):
    from apps.students.models import Student
    from django.contrib.auth import get_user_model
    if not request.user.groups.filter(
        name__in=["Admin"]
    ).exists():
        raise Http404
    student = get_object_or_404(Student, pk=pk)

    if hasattr(student, "portal_user") and student.portal_user:
        messages.info(
            request,
            f"{student.full_name} already has a "
            f"portal account: {student.portal_user.username}"
        )
        return redirect(
            "admin_panel:students:student_detail", pk=pk
        )

    User = get_user_model()
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    raw_password = "".join(
        secrets.choice(alphabet) for _ in range(12)
    )

    try:
        with transaction.atomic():
            if student.email:
                base_username = (
                    student.email.split("@")[0]
                    .lower()
                    .replace(" ", "")
                )
            else:
                base_username = f"student{student.pk}"

            username = base_username
            counter = 1
            while User.objects.filter(
                username=username
            ).exists():
                username = f"{base_username}{counter}"
                counter += 1

            portal_user = User(
                username=username,
                email=(
                    student.email
                    or f"{username}@iice.edu.pk"
                ),
                first_name=student.full_name.split()[0],
                last_name=" ".join(
                    student.full_name.split()[1:]
                ) if len(
                    student.full_name.split()
                ) > 1 else "",
            )
            if hasattr(portal_user, "role"):
                portal_user.role = "student"
            portal_user.set_password(raw_password)
            portal_user.full_clean()
            portal_user.save()

            from django.contrib.auth.models import Group
            student_group, _ = Group.objects.get_or_create(
                name="Student"
            )
            portal_user.groups.add(student_group)

            student.portal_user = portal_user
            student.save(update_fields=["portal_user"])

        messages.success(
            request,
            f"Portal account created for "
            f"{student.full_name}. "
            f"Username: {username} | "
            f"Password: {raw_password} "
            f"(Shown only once)"
        )
    except Exception as exc:
        messages.error(
            request,
            f"Failed to create portal account: {exc}"
        )

    return redirect(
        "admin_panel:students:student_detail", pk=pk
    )
