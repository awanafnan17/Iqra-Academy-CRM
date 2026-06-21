"""
Attendance views for the Academy CRM.
"""

import datetime
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.urls import reverse

from apps.core.decorators import role_required, post_required
from apps.core.services import BusinessRuleViolation
from apps.attendance.models import AttendanceRecord, AttendanceLock
from apps.attendance.services import AttendanceService
from apps.academics.models import Session
from apps.students.models import Enrollment


def _get_attendance_namespace(request):
    """Determine redirect namespace based on request path."""
    if request.path.startswith("/panel/teacher/"):
        return "teacher_panel:"
    return "admin_panel:attendance:"


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
#  Attendance views
# -------------------------------------------------------------------

@login_required
@role_required("Admin", "Principal")
def attendance_overview(request):
    """List active sessions and provide links to mark and view sheets."""
    sessions = Session.objects.filter(status="Active", is_deleted=False).order_by("name")
    
    from django.db.models import Count, Q
    sessions = sessions.annotate(
        student_count=Count(
            "enrollments",
            filter=Q(enrollments__status="Active", enrollments__is_deleted=False)
        )
    )
    
    today_str = datetime.date.today().isoformat()
    
    if request.user.is_superuser or request.user.groups.filter(name="Admin").exists():
        role = "Admin"
    elif request.user.groups.filter(name="Principal").exists():
        role = "Principal"
    else:
        role = "Teacher"

    context = {
        "sessions": sessions,
        "today_str": today_str,
        "role": role,
    }
    return render(request, "attendance/overview.html", context)


@login_required
@role_required("Admin", "Principal", "Teacher")
def attendance_mark(request, session_id):
    """Render sheet or save daily attendance for a session."""
    session = get_object_or_404(Session, pk=session_id)
    
    date_str = request.GET.get("date") or request.POST.get("date")
    if date_str:
        try:
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            date = datetime.date.today()
    else:
        date = datetime.date.today()

    is_locked = AttendanceService.is_date_locked(session.pk, date)

    # Fetch active enrollments
    enrollments = (
        Enrollment.objects
        .select_related("student")
        .filter(session=session, status="Active", is_deleted=False)
        .order_by("student__roll_number", "student__full_name")
    )

    if request.method == "POST":
        if is_locked:
            messages.error(request, f"Attendance for {date} is locked and cannot be modified.")
            ns = _get_attendance_namespace(request)
            return redirect(f"{ns}attendance_mark", session_id=session.pk)

        success_count = 0
        has_error = False
        
        for enrollment in enrollments:
            student_id = enrollment.student.pk
            status = request.POST.get(f"status_{student_id}")
            remarks = request.POST.get(f"remarks_{student_id}")
            
            if status:
                try:
                    AttendanceService.mark_attendance(
                        session_id=session.pk,
                        student_id=student_id,
                        date=date,
                        status=status,
                        user=request.user,
                        remarks=remarks
                    )
                    success_count += 1
                except BusinessRuleViolation as e:
                    messages.error(request, f"Error marking student {enrollment.student.full_name}: {str(e)}")
                    has_error = True
                    break
                except Exception as e:
                    messages.error(request, f"System error marking student {enrollment.student.full_name}: {str(e)}")
                    has_error = True
                    break

        if not has_error:
            if success_count > 0:
                messages.success(request, f"Successfully marked attendance for {success_count} students on {date}.")
            ns = _get_attendance_namespace(request)
            return redirect(f"{ns}attendance_sheet", session_id=session.pk, date=date.isoformat())

    # Get existing records to pre-populate
    records_qs = AttendanceRecord.objects.filter(session=session, date=date)
    records_dict = {r.student_id: r for r in records_qs}

    for enrollment in enrollments:
        record = records_dict.get(enrollment.student.pk)
        if record:
            enrollment.existing_status = record.status
            enrollment.existing_remarks = record.remarks
        else:
            enrollment.existing_status = "Present"
            enrollment.existing_remarks = ""

    if request.path.startswith("/panel/teacher/"):
        back_url = reverse("teacher_panel:session_detail", kwargs={"pk": session.pk})
        sheet_url = reverse("teacher_panel:attendance_sheet", kwargs={"session_id": session.pk, "date": date.isoformat()})
    else:
        back_url = reverse("admin_panel:attendance:attendance_overview")
        sheet_url = reverse("admin_panel:attendance:attendance_sheet", kwargs={"session_id": session.pk, "date": date.isoformat()})

    if request.user.is_superuser or request.user.groups.filter(name="Admin").exists():
        role = "Admin"
    elif request.user.groups.filter(name="Principal").exists():
        role = "Principal"
    else:
        role = "Teacher"

    context = {
        "session": session,
        "date": date,
        "date_str": date.isoformat(),
        "enrollments": enrollments,
        "is_locked": is_locked,
        "status_choices": AttendanceRecord.STATUS_CHOICES,
        "role": role,
        "back_url": back_url,
        "sheet_url": sheet_url,
    }
    return render(request, "attendance/mark.html", context)


@login_required
@role_required("Admin", "Principal", "Teacher")
def attendance_sheet(request, session_id, date):
    """View sheet of attendance for a session and date."""
    session = get_object_or_404(Session, pk=session_id)
    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise Http404("Invalid date format.")

    is_locked = AttendanceService.is_date_locked(session.pk, date_obj)

    records = (
        AttendanceRecord.objects
        .select_related("student")
        .filter(session=session, date=date_obj)
        .order_by("student__roll_number", "student__full_name")
    )

    if request.path.startswith("/panel/teacher/"):
        back_url = reverse("teacher_panel:session_detail", kwargs={"pk": session.pk})
        edit_url = reverse("teacher_panel:attendance_mark", kwargs={"session_id": session.pk}) + f"?date={date}"
    else:
        back_url = reverse("admin_panel:attendance:attendance_overview")
        edit_url = reverse("admin_panel:attendance:attendance_mark", kwargs={"session_id": session.pk}) + f"?date={date}"

    if request.user.is_superuser or request.user.groups.filter(name="Admin").exists():
        role = "Admin"
    elif request.user.groups.filter(name="Principal").exists():
        role = "Principal"
    else:
        role = "Teacher"

    context = {
        "session": session,
        "date": date_obj,
        "date_str": date,
        "records": records,
        "is_locked": is_locked,
        "role": role,
        "back_url": back_url,
        "edit_url": edit_url,
    }
    return render(request, "attendance/sheet.html", context)


@login_required
@role_required("Admin", "Principal")
@post_required
def attendance_lock(request, session_id):
    """Lock attendance modifications for a date."""
    session = get_object_or_404(Session, pk=session_id)
    date_str = request.POST.get("date")
    reason = request.POST.get("reason")
    
    if not date_str:
        messages.error(request, "Date is required to lock attendance.")
        return redirect("admin_panel:attendance:attendance_overview")

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect("admin_panel:attendance:attendance_overview")

    try:
        AttendanceService.lock_attendance_for_date(
            session_id=session.pk,
            date=date_obj,
            user=request.user,
            reason=reason
        )
        messages.success(request, f"Attendance locked successfully for {date_str}.")
    except BusinessRuleViolation as e:
        messages.error(request, f"Could not lock attendance: {str(e)}")
    except Exception as e:
        messages.error(request, f"System error locking attendance: {str(e)}")

    ns = _get_attendance_namespace(request)
    return redirect(f"{ns}attendance_sheet", session_id=session.pk, date=date_str)


@login_required
@role_required("Admin")
@post_required
def attendance_unlock(request, session_id):
    """Unlock attendance modifications for a date."""
    session = get_object_or_404(Session, pk=session_id)
    date_str = request.POST.get("date")
    
    if not date_str:
        messages.error(request, "Date is required to unlock attendance.")
        return redirect("admin_panel:attendance:attendance_overview")

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        messages.error(request, "Invalid date format.")
        return redirect("admin_panel:attendance:attendance_overview")

    try:
        AttendanceService.unlock_attendance_for_date(
            session_id=session.pk,
            date=date_obj,
            user=request.user
        )
        messages.success(request, f"Attendance unlocked successfully for {date_str}.")
    except BusinessRuleViolation as e:
        messages.error(request, f"Could not unlock attendance: {str(e)}")
    except Exception as e:
        messages.error(request, f"System error unlocking attendance: {str(e)}")

    ns = _get_attendance_namespace(request)
    return redirect(f"{ns}attendance_sheet", session_id=session.pk, date=date_str)


@login_required
@role_required("Admin", "Principal", "Teacher")
def attendance_analytics(request, session_id):
    """View read-only attendance statistics for a session."""
    session = get_object_or_404(Session, pk=session_id)
    
    user = request.user
    if user.groups.filter(name="Teacher").exists() and not user.is_superuser:
        from apps.academics.models import TeacherAssignment
        if not TeacherAssignment.objects.filter(
            teacher=user, session=session, is_active=True
        ).exists():
            raise Http404("You are not assigned to this session.")

    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    
    start_date = None
    end_date = None
    
    if start_date_str:
        try:
            start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass
    if end_date_str:
        try:
            end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    analytics_data = AttendanceService.get_attendance_analytics(
        session_id=session.pk,
        start_date=start_date,
        end_date=end_date
    )

    from django.db.models import Count, Q
    records = AttendanceRecord.objects.filter(session=session)
    if start_date:
        records = records.filter(date__gte=start_date)
    if end_date:
        records = records.filter(date__lte=end_date)
        
    counts = records.aggregate(
        present=Count("id", filter=Q(status="Present")),
        absent=Count("id", filter=Q(status="Absent")),
        late=Count("id", filter=Q(status="Late")),
        excused=Count("id", filter=Q(status="Excused")),
        total=Count("id"),
    )
    
    total_marked_days = records.values("date").distinct().count()

    context = {
        "session": session,
        "analytics": analytics_data,
        "counts": counts,
        "total_marked_days": total_marked_days,
        "start_date_str": start_date_str or "",
        "end_date_str": end_date_str or "",
        "back_url": reverse("teacher_panel:session_detail", kwargs={"pk": session.pk}) if request.path.startswith("/panel/teacher/") else reverse("admin_panel:attendance:attendance_overview")
    }
    return render(request, "attendance/analytics.html", context)


@login_required
@role_required("Admin", "Principal")
def low_attendance_report(request):
    """Generate report of students with attendance below threshold."""
    threshold_str = request.GET.get("threshold", "75")
    try:
        threshold = Decimal(threshold_str)
    except Exception:
        threshold = Decimal("75.00")

    session_id_str = request.GET.get("session_id")
    
    from apps.academics.models import Session
    active_sessions = Session.objects.filter(status="Active", is_deleted=False).order_by("name")
    
    selected_session = None
    if session_id_str:
        try:
            selected_session = Session.objects.get(pk=int(session_id_str), is_deleted=False)
        except (ValueError, Session.DoesNotExist):
            pass

    low_attendance_students = []
    
    if selected_session:
        sessions_to_check = [selected_session]
    else:
        sessions_to_check = list(active_sessions)

    from apps.students.models import Student
    
    for session in sessions_to_check:
        student_list = AttendanceService.get_low_attendance_students(session.pk, threshold=threshold)
        for item in student_list:
            try:
                student = Student.objects.get(pk=item["student_id"], is_deleted=False)
                total_days = AttendanceRecord.objects.filter(session=session, student=student).values("date").distinct().count()
                low_attendance_students.append({
                    "student": student,
                    "session": session,
                    "attendance_percentage": item["attendance_percentage"],
                    "total_days": total_days,
                })
            except Student.DoesNotExist:
                pass

    # Sort by percentage ascending
    low_attendance_students.sort(key=lambda x: x["attendance_percentage"])

    # Pagination: 25 per page
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    paginator = Paginator(low_attendance_students, 25)
    page = request.GET.get("page")
    try:
        report_page = paginator.page(page)
    except PageNotAnInteger:
        report_page = paginator.page(1)
    except EmptyPage:
        report_page = paginator.page(paginator.num_pages)

    context = {
        "report_page": report_page,
        "active_sessions": active_sessions,
        "selected_session": selected_session,
        "threshold": threshold,
        "page_title": "Low Attendance Report",
    }
    return render(request, "attendance/low_attendance_report.html", context)
