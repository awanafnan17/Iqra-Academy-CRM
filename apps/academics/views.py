from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import HttpResponse, Http404

from apps.core.decorators import role_required, post_required
from apps.academics.models import Session, Subject, TeacherAssignment, ClassSchedule
from apps.academics.forms import SessionForm, ClassScheduleForm, SubjectForm, TeacherAssignmentForm
from django.core.exceptions import ValidationError as DjangoValidationError
import datetime


def _stub(name):
    """Create a placeholder view function."""
    def view(request, *args, **kwargs):
        return HttpResponse(
            f"{name} - Coming soon",
            content_type="text/plain",
        )
    view.__name__ = name
    view.__qualname__ = name
    return view


# -------------------------------------------------------------------
#  Session views
# -------------------------------------------------------------------




@login_required
@role_required("Admin", "Principal")
def session_create(request):
    """Create a new session."""
    if request.method == "POST":
        form = SessionForm(request.POST, request.FILES)
        if form.is_valid():
            session = form.save()
            from django.contrib import messages
            messages.success(request, "Session created successfully.")
            return redirect("admin_panel:academics:session_detail", pk=session.pk)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = SessionForm()
    return render(request, "academics/session_form.html", {"form": form, "role": "Admin"})


@login_required
@role_required("Admin", "Principal", "Registrar", "Teacher")
def session_detail(request, pk):
    """View detailed parameters and list enrolled students for a session."""
    from apps.academics.models import Session
    session = get_object_or_404(Session, pk=pk)

    enrollments = []
    timetable = []
    exams = []
    success_count = 0
    total_enrolled = 0

    try:
        from apps.students.models import Enrollment
        enrollments = (
            Enrollment.objects
            .select_related("student")
            .filter(session=session, status="Active")
            .order_by("student__roll_number")
        )
        total_enrolled = enrollments.count()
    except Exception:
        enrollments = []

    try:
        from apps.academics.models import ClassSchedule
        timetable = (
            ClassSchedule.objects
            .select_related("subject", "faculty__user")
            .filter(session=session)
            .order_by("day_of_week", "start_time")
        )
    except Exception:
        timetable = []

    try:
        from apps.exams.models import Exam
        exams = (
            Exam.objects
            .filter(session=session)
            .order_by("-exam_date")
        )
    except Exception:
        exams = []

    try:
        from apps.achievements.models import Achievement
        success_count = Achievement.objects.filter(
            student__enrollments__session=session
        ).distinct().count()
    except Exception:
        success_count = 0

    success_rate = 0
    if total_enrolled > 0 and success_count > 0:
        success_rate = round(
            (success_count / total_enrolled) * 100, 1
        )

    context = {
        "session": session,
        "enrollments": enrollments,
        "total_enrolled": total_enrolled,
        "timetable": timetable,
        "exams": exams,
        "success_count": success_count,
        "success_rate": success_rate,
        "page_title": session.name,
        "role": "Admin",
    }
    return render(
        request,
        "academics/session_detail.html",
        context,
    )


@login_required
@role_required("Admin", "Principal")
def session_edit(request, pk):
    """Edit session parameters, including prefix configurations."""
    session = get_object_or_404(Session, pk=pk)
    if request.method == "POST":
        form = SessionForm(request.POST, request.FILES, instance=session)
        if form.is_valid():
            session = form.save()
            from django.contrib import messages
            messages.success(request, "Session updated successfully.")
            return redirect("admin_panel:academics:session_detail", pk=session.pk)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = SessionForm(instance=session)
    return render(request, "academics/session_form.html", {"form": form, "session": session, "role": "Admin"})


@login_required
@role_required("Admin", "Principal")
@post_required
def session_toggle_status(request, pk):
    """Toggle the active/inactive status of a session."""
    session = get_object_or_404(Session, pk=pk)
    session.status = "Inactive" if session.status == "Active" else "Active"
    session.save()
    return redirect("admin_panel:session_overview")


@login_required
@role_required("Admin")
@post_required
def session_delete(request, pk):
    """Soft delete a session if safe to do so."""
    session = get_object_or_404(Session, pk=pk)
    from apps.students.models import Enrollment
    enrollments_count = Enrollment.objects.filter(session=session).count()
    if enrollments_count > 0:
        from django.contrib import messages
        messages.error(
            request,
            f"Cannot delete session '{session.name}' because it contains {enrollments_count} enrollment record(s)."
        )
        return redirect("admin_panel:session_detail", pk=session.pk)

    session.soft_delete(user=request.user)
    from django.contrib import messages
    messages.success(request, f"Session '{session.name}' deleted successfully.")
    return redirect("admin_panel:session_overview")


@login_required
@role_required("Admin", "Principal", "Registrar", "Teacher")
def session_enrollments(request, pk):
    """List all enrollments for a selected session (read-only)."""
    from apps.academics.models import Session
    session = get_object_or_404(Session, pk=pk)
    
    user = request.user
    if user.groups.filter(name="Teacher").exists() and not user.is_superuser:
        from apps.academics.models import TeacherAssignment
        if not TeacherAssignment.objects.filter(
            teacher=user, session=session, is_active=True
        ).exists():
            raise Http404("You are not assigned to this session.")

    # Show all enrollments for selected session
    from apps.students.models import Enrollment
    enrollments_qs = Enrollment.objects.filter(session=session).select_related("student")

    # Add search by student name or roll number
    search_query = request.GET.get("search", "").strip()
    if search_query:
        from django.db.models import Q
        enrollments_qs = enrollments_qs.filter(
            Q(student__full_name__icontains=search_query) |
            Q(student__roll_number__icontains=search_query)
        )

    # Add status filter
    status_filter = request.GET.get("status", "").strip()
    if status_filter:
        enrollments_qs = enrollments_qs.filter(status=status_filter)

    enrollments_qs = enrollments_qs.order_by("student__roll_number", "student__full_name")

    # Pagination: 25 per page
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(enrollments_qs, 25)
    page = request.GET.get("page")
    try:
        enrollments = paginator.page(page)
    except PageNotAnInteger:
        enrollments = paginator.page(1)
    except EmptyPage:
        enrollments = paginator.page(paginator.num_pages)

    # Get status choices from Enrollment
    status_choices = Enrollment.STATUS_CHOICES

    if request.path.startswith("/panel/teacher/"):
        back_url = reverse("teacher_panel:session_detail", kwargs={"pk": session.pk})
    else:
        back_url = reverse("admin_panel:academics:session_detail", kwargs={"pk": session.pk})

    context = {
        "session": session,
        "enrollments": enrollments,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": status_choices,
        "page_title": f"Enrollments: {session.name}",
        "back_url": back_url,
    }
    return render(request, "academics/session_enrollments.html", context)


@login_required
@role_required("Admin")
def session_revenue(request, pk):
    """View read-only revenue dashboard for a session."""
    from apps.academics.models import Session
    from apps.students.models import Enrollment
    from apps.finance.services import calculate_session_revenue, calculate_student_ledger

    session = get_object_or_404(Session, pk=pk)

    # Get month and year from request, default to current month/year
    today = datetime.date.today()
    try:
        year = int(request.GET.get("year", today.year))
    except ValueError:
        year = today.year

    try:
        month = int(request.GET.get("month", today.month))
        if not (1 <= month <= 12):
            month = today.month
    except ValueError:
        month = today.month

    # Get monthly session revenue using existing service
    try:
        monthly_revenue = calculate_session_revenue(session.pk, year, month)
    except Exception:
        monthly_revenue = {
            "tuition_revenue": Decimal("0.00"),
            "late_fee_revenue": Decimal("0.00"),
            "total_revenue": Decimal("0.00"),
            "refunds": Decimal("0.00"),
            "net_revenue": Decimal("0.00"),
            "payment_count": 0,
            "refund_count": 0,
        }

    # Fetch all enrollments for the student ledger table
    enrollments_qs = Enrollment.objects.filter(session=session).select_related("student").order_by("student__roll_number", "student__full_name")
    total_enrolled = enrollments_qs.count()

    # Pagination: 25 per page
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(enrollments_qs, 25)
    page = request.GET.get("page")
    try:
        paginated_enrollments = paginator.page(page)
    except PageNotAnInteger:
        paginated_enrollments = paginator.page(1)
    except EmptyPage:
        paginated_enrollments = paginator.page(paginator.num_pages)

    # Calculate ledger for each student in the paginated set
    student_ledgers = []
    from decimal import Decimal
    for enr in paginated_enrollments:
        try:
            ledger = calculate_student_ledger(enr.pk)
            student_ledgers.append({
                "student": enr.student,
                "status": enr.status,
                "total_payable": ledger["total_payable"],
                "total_paid": ledger["total_paid"],
                "total_refunded": ledger["total_refunded"],
                "outstanding_balance": ledger["outstanding_balance"],
            })
        except Exception:
            student_ledgers.append({
                "student": enr.student,
                "status": enr.status,
                "total_payable": None,
                "total_paid": None,
                "total_refunded": None,
                "outstanding_balance": None,
            })

    # Generate lists for the selectors
    years_range = list(range(today.year - 5, today.year + 2))
    months_range = [
        (1, "January"), (2, "February"), (3, "March"), (4, "April"),
        (5, "May"), (6, "June"), (7, "July"), (8, "August"),
        (9, "September"), (10, "October"), (11, "November"), (12, "December")
    ]

    context = {
        "session": session,
        "total_enrolled": total_enrolled,
        "year": year,
        "month": month,
        "monthly_revenue": monthly_revenue,
        "paginated_enrollments": paginated_enrollments,
        "student_ledgers": student_ledgers,
        "years_range": years_range,
        "months_range": months_range,
        "page_title": f"Session Revenue: {session.name}",
    }
    return render(request, "academics/session_revenue.html", context)


# -------------------------------------------------------------------
#  Subject views
# -------------------------------------------------------------------


@login_required
@role_required("Admin", "Principal")
def subject_create(request):
    """Create a new subject."""
    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            from django.contrib import messages
            messages.success(request, "Subject created successfully.")
            if subject.session:
                return redirect("admin_panel:session_detail", pk=subject.session.pk)
            return redirect("admin_panel:session_overview")
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = SubjectForm()
    return render(request, "academics/subject_form.html", {"form": form, "role": "Admin"})


@login_required
@role_required("Admin", "Principal")
def subject_edit(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == "POST":
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            subject = form.save()
            from django.contrib import messages
            messages.success(request, "Subject updated successfully.")
            if subject.session:
                return redirect("admin_panel:session_detail", pk=subject.session.pk)
            return redirect("admin_panel:session_overview")
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = SubjectForm(instance=subject)
    return render(request, "academics/subject_form.html", {"form": form, "subject": subject, "role": "Admin"})

# -------------------------------------------------------------------
#  Teacher Assignment views
# -------------------------------------------------------------------


@login_required
@role_required("Admin", "Principal")
def assignment_create(request):
    """Create a new teacher assignment."""
    if request.method == "POST":
        form = TeacherAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save()
            from django.contrib import messages
            messages.success(request, "Teacher assignment created successfully.")
            return redirect("admin_panel:session_detail", pk=assignment.session.pk)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        session_id = request.GET.get("session")
        initial = {}
        if session_id:
            initial["session"] = session_id
        form = TeacherAssignmentForm(initial=initial)
    return render(request, "academics/assignment_form.html", {"form": form, "role": "Admin"})


@login_required
@role_required("Admin", "Principal")
def assignment_edit(request, pk):
    """Edit an existing teacher assignment."""
    assignment = get_object_or_404(TeacherAssignment, pk=pk)
    if request.method == "POST":
        form = TeacherAssignmentForm(request.POST, instance=assignment)
        if form.is_valid():
            assignment = form.save()
            from django.contrib import messages
            messages.success(request, "Teacher assignment updated successfully.")
            return redirect("admin_panel:session_detail", pk=assignment.session.pk)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = TeacherAssignmentForm(instance=assignment)
    return render(request, "academics/assignment_form.html", {"form": form, "assignment": assignment, "role": "Admin"})


@login_required
@role_required("Admin")
@post_required
def assignment_delete(request, pk):
    """Delete a teacher assignment."""
    assignment = get_object_or_404(TeacherAssignment, pk=pk)
    session_pk = assignment.session.pk
    assignment.delete()
    from django.contrib import messages
    messages.success(request, "Teacher assignment deleted successfully.")
    return redirect("admin_panel:session_detail", pk=session_pk)


# -------------------------------------------------------------------
#  Timetable views
# -------------------------------------------------------------------

@login_required
@role_required("Admin", "Principal")
def timetable_list(request):
    session_id = request.GET.get("session", "")
    schedules = ClassSchedule.objects.select_related("session", "subject", "faculty__user").all()
    if session_id:
        schedules = schedules.filter(session_id=session_id)

    sessions = Session.objects.filter(is_deleted=False)
    context = {
        "schedules": schedules,
        "sessions": sessions,
        "selected_session_id": int(session_id) if session_id.isdigit() else "",
        "role": "Admin",
    }
    return render(request, "academics/timetable_list.html", context)


@login_required
@role_required("Admin", "Principal")
def timetable_create(request):
    if request.method == "POST":
        form = ClassScheduleForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                from django.contrib import messages
                messages.success(request, "Timetable created successfully.")
                return redirect("admin_panel:timetable_list")
            except DjangoValidationError as e:
                form.add_error(None, e)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClassScheduleForm()
    return render(request, "academics/timetable_form.html", {"form": form, "role": "Admin"})


@login_required
@role_required("Admin", "Principal")
def timetable_edit(request, pk):
    schedule = get_object_or_404(ClassSchedule, pk=pk)
    if request.method == "POST":
        form = ClassScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            try:
                form.save()
                from django.contrib import messages
                messages.success(request, "Timetable updated successfully.")
                return redirect("admin_panel:timetable_list")
            except DjangoValidationError as e:
                form.add_error(None, e)
        else:
            from django.contrib import messages
            messages.error(request, "Please correct the errors below.")
    else:
        form = ClassScheduleForm(instance=schedule)
    return render(request, "academics/timetable_form.html", {"form": form, "schedule": schedule, "role": "Admin"})


@login_required
@role_required("Admin", "Principal")
@post_required
def timetable_toggle_status(request, pk):
    schedule = get_object_or_404(ClassSchedule, pk=pk)
    schedule.is_active = not schedule.is_active
    schedule.save(update_fields=["is_active"])
    return redirect("admin_panel:timetable_list")


@login_required
@role_required("Teacher")
def timetable_teacher(request):
    faculty = getattr(request.user, "faculty_profile", None)
    schedules = []
    if faculty:
        schedules = ClassSchedule.objects.filter(
            faculty=faculty,
            is_active=True
        ).select_related("session", "subject").order_by("start_time")

    days_map = {
        "Monday": [],
        "Tuesday": [],
        "Wednesday": [],
        "Thursday": [],
        "Friday": [],
        "Saturday": [],
        "Sunday": [],
    }
    for s in schedules:
        if s.day_of_week in days_map:
            days_map[s.day_of_week].append(s)

    today_name = datetime.date.today().strftime("%A")
    context = {
        "days_map": days_map,
        "today_name": today_name,
        "role": "Teacher",
    }
    return render(request, "academics/timetable_teacher.html", context)


