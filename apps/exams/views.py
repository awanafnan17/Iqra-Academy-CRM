import json
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import render, redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.core.exceptions import ValidationError, PermissionDenied

from apps.core.decorators import role_required, permission_required
from apps.exams.models import Exam
from apps.exams import services


def _get_namespace_prefix(request):
    """Determine URL namespace prefix dynamically from the request path."""
    if request.path.startswith("/panel/admin/"):
        return "admin_panel:exams:"
    if request.path.startswith("/panel/principal/"):
        return "principal_panel:exams:"
    if request.path.startswith("/panel/teacher/"):
        return "teacher_panel:exams:"
    return "exams:"


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


# Grade Config Views
@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class GradeConfigListView(View):
    """List all grade configurations."""
    template_name = "exams/grade_config_list.html"

    def get(self, request, *args, **kwargs):
        from apps.exams.models import GradeConfig
        grade_configs = GradeConfig.objects.select_related("session").all().order_by("session__name", "sort_order")
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(grade_configs, 20)  # 20 per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        context = {
            "grade_configs": page_obj,
            "can_edit": request.user.is_superuser or request.user.groups.filter(name__in=["Admin", "Principal"]).exists()
        }
        return render(request, self.template_name, context)


@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class GradeConfigCreateView(View):
    """Create a new grade configuration."""
    template_name = "exams/grade_config_form.html"

    def get(self, request, *args, **kwargs):
        from apps.exams.forms import GradeConfigForm
        form = GradeConfigForm()
        return render(request, self.template_name, {"form": form, "action": "Create"})

    def post(self, request, *args, **kwargs):
        from apps.exams.forms import GradeConfigForm
        from django.contrib import messages
        form = GradeConfigForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade configuration created successfully.")
            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}grade_config_list"))
        return render(request, self.template_name, {"form": form, "action": "Create"}, status=400)


@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class GradeConfigEditView(View):
    """Edit an existing grade configuration."""
    template_name = "exams/grade_config_form.html"

    def get(self, request, pk, *args, **kwargs):
        from apps.exams.models import GradeConfig
        from apps.exams.forms import GradeConfigForm
        try:
            config = GradeConfig.objects.get(pk=pk)
        except GradeConfig.DoesNotExist:
            raise Http404("Grade configuration not found.")
        form = GradeConfigForm(instance=config)
        return render(request, self.template_name, {"form": form, "action": "Edit", "config": config})

    def post(self, request, pk, *args, **kwargs):
        from apps.exams.models import GradeConfig
        from apps.exams.forms import GradeConfigForm
        from django.contrib import messages
        try:
            config = GradeConfig.objects.get(pk=pk)
        except GradeConfig.DoesNotExist:
            raise Http404("Grade configuration not found.")
        form = GradeConfigForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, "Grade configuration updated successfully.")
            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}grade_config_list"))
        return render(request, self.template_name, {"form": form, "action": "Edit", "config": config}, status=400)


grade_config_list = GradeConfigListView.as_view()
grade_config_create = GradeConfigCreateView.as_view()
grade_config_edit = GradeConfigEditView.as_view()


@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian"), name="dispatch")
class ExamListView(View):
    """List exams filtered based on roles and scopes."""
    def get(self, request, *args, **kwargs):
        user = request.user

        if user.is_superuser or user.groups.filter(name__in=["Admin", "Principal"]).exists():
            exams = Exam.objects.all()
        elif user.groups.filter(name="Teacher").exists():
            from apps.academics.models import TeacherAssignment
            assigned_sessions = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list("session_id", flat=True)
            assigned_subjects = TeacherAssignment.objects.filter(teacher=user, is_active=True).values_list("subject_id", flat=True)
            exams = Exam.objects.filter(session_id__in=assigned_sessions, subject_id__in=assigned_subjects)
        elif user.groups.filter(name="Student").exists():
            from apps.students.models import Enrollment
            active_sessions = Enrollment.objects.filter(student__portal_user=user, status="Active").values_list("session_id", flat=True)
            exams = Exam.objects.filter(session_id__in=active_sessions, is_published=True)
        elif user.groups.filter(name="Guardian").exists():
            from apps.students.models import Guardian, Enrollment
            student_ids = Guardian.objects.filter(portal_user=user).values_list("student_id", flat=True)
            active_sessions = Enrollment.objects.filter(student_id__in=student_ids, status="Active").values_list("session_id", flat=True)
            exams = Exam.objects.filter(session_id__in=active_sessions, is_published=True)
        else:
            raise Http404("Access denied.")

        # Prefetch session and subject to optimize query performance
        exams = exams.select_related("session", "subject")

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
            data = list(exams.values("id", "name", "exam_type", "total_marks", "passing_marks", "exam_date", "is_published", "session__name", "subject__name"))
            return JsonResponse({"exams": data})

        return render(request, "exams/exam_list.html", {"exams": exams})


@method_decorator(permission_required("exams", "create"), name="dispatch")
class ExamCreateView(View):
    """Create a new exam, verifying scopes."""
    def get(self, request, *args, **kwargs):
        user = request.user
        if user.is_superuser or user.groups.filter(name__in=["Admin", "Principal"]).exists():
            from apps.academics.models import Session, Subject
            sessions = Session.objects.all()
            subjects = Subject.objects.all()
        else:
            from apps.academics.models import TeacherAssignment
            assignments = TeacherAssignment.objects.filter(teacher=user, is_active=True).select_related("session", "subject")
            sessions = list({a.session for a in assignments})
            subjects = list({a.subject for a in assignments if a.subject})

        return render(request, "exams/exam_create.html", {
            "sessions": sessions,
            "subjects": subjects
        })

    def post(self, request, *args, **kwargs):
        session_id = request.POST.get("session_id")
        subject_id = request.POST.get("subject_id")
        name = request.POST.get("name")
        exam_date = request.POST.get("exam_date")
        total_marks = request.POST.get("total_marks")
        passing_marks = request.POST.get("passing_marks") or None
        exam_type = request.POST.get("exam_type", "Test")

        try:
            exam = services.create_exam(
                session_id=session_id,
                subject_id=subject_id,
                name=name,
                exam_date=exam_date,
                total_marks=total_marks,
                passing_marks=passing_marks,
                exam_type=exam_type,
                created_by=request.user
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "success", "exam_id": exam.id})

            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": exam.id}))
        except ValidationError as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)

            # Re-fetch for form context
            user = request.user
            if user.is_superuser or user.groups.filter(name__in=["Admin", "Principal"]).exists():
                from apps.academics.models import Session, Subject
                sessions = Session.objects.all()
                subjects = Subject.objects.all()
            else:
                from apps.academics.models import TeacherAssignment
                assignments = TeacherAssignment.objects.filter(teacher=user, is_active=True).select_related("session", "subject")
                sessions = list({a.session for a in assignments})
                subjects = list({a.subject for a in assignments if a.subject})

            return render(request, "exams/exam_create.html", {
                "sessions": sessions,
                "subjects": subjects,
                "error": str(e)
            }, status=400)


@method_decorator(role_required("Admin", "Principal", "Teacher", "Student", "Guardian"), name="dispatch")
class ExamDetailView(View):
    """View detailed information and results of an exam."""
    def get(self, request, pk, *args, **kwargs):
        user = request.user

        try:
            exam = Exam.objects.select_related("session", "subject").get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        if user.is_superuser or user.groups.filter(name__in=["Admin", "Principal"]).exists():
            pass
        elif user.groups.filter(name="Teacher").exists():
            services._validate_teacher_scope(user, exam=exam)
        elif user.groups.filter(name="Student").exists():
            if not exam.is_published:
                raise Http404("Exam not published.")
            from apps.students.models import Enrollment
            if not Enrollment.objects.filter(student__portal_user=user, session=exam.session, status="Active").exists():
                raise Http404("Access denied.")
        elif user.groups.filter(name="Guardian").exists():
            if not exam.is_published:
                raise Http404("Exam not published.")
            from apps.students.models import Guardian, Enrollment
            student_ids = Guardian.objects.filter(portal_user=user).values_list("student_id", flat=True)
            if not Enrollment.objects.filter(student_id__in=student_ids, session=exam.session, status="Active").exists():
                raise Http404("Access denied.")
        else:
            raise Http404("Access denied.")

        # Determine results scope visibility
        if not (user.groups.filter(name="Student").exists() or user.groups.filter(name="Guardian").exists()):
            results = exam.results.all().select_related("student")
        else:
            if user.groups.filter(name="Student").exists():
                results = exam.results.filter(student__portal_user=user)
            else:
                from apps.students.models import Guardian
                student_ids = Guardian.objects.filter(portal_user=user).values_list("student_id", flat=True)
                results = exam.results.filter(student_id__in=student_ids)

        if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
            results_data = list(results.values("id", "student__full_name", "marks_obtained", "percentage", "grade", "rank", "is_absent", "remarks"))
            return JsonResponse({
                "exam": {
                    "id": exam.id,
                    "name": exam.name,
                    "exam_type": exam.exam_type,
                    "total_marks": exam.total_marks,
                    "passing_marks": exam.passing_marks,
                    "exam_date": exam.exam_date,
                    "is_published": exam.is_published,
                    "session_name": exam.session.name,
                    "subject_name": exam.subject.name if exam.subject else None
                },
                "results": results_data
            })

        return render(request, "exams/exam_detail.html", {"exam": exam, "results": results})


@method_decorator(permission_required("exams", "edit"), name="dispatch")
class ExamEditView(View):
    """Edit an existing exam."""
    def get(self, request, pk, *args, **kwargs):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        services._validate_teacher_scope(request.user, exam=exam)
        return render(request, "exams/exam_create.html", {"exam": exam})

    def post(self, request, pk, *args, **kwargs):
        name = request.POST.get("name")
        exam_date = request.POST.get("exam_date")
        total_marks = request.POST.get("total_marks")
        passing_marks = request.POST.get("passing_marks") or None
        exam_type = request.POST.get("exam_type", "Test")

        try:
            exam = services.update_exam(
                exam_id=pk,
                name=name,
                exam_date=exam_date,
                total_marks=total_marks,
                passing_marks=passing_marks,
                exam_type=exam_type,
                user=request.user
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "success", "exam_id": exam.id})
            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": exam.id}))
        except ValidationError as e:
            try:
                exam = Exam.objects.get(pk=pk)
            except Exam.DoesNotExist:
                raise Http404("Exam not found.")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            return render(request, "exams/exam_create.html", {"exam": exam, "error": str(e)}, status=400)


@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class ExamReviewView(View):
    """Review the results of an exam, setting status to Under Review."""
    def dispatch(self, request, *args, **kwargs):
        if request.method != "POST":
            raise Http404("POST required.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        try:
            exam = services.review_exam(pk, request.user)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "success", "message": "Exam results reviewed and set to Under Review."})

            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": exam.id}))
        except (ValidationError, PermissionDenied) as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            raise Http404(str(e))


@method_decorator(role_required("Admin"), name="dispatch")
class ExamPublishView(View):
    """Publish the results of an exam."""
    def dispatch(self, request, *args, **kwargs):
        if request.method != "POST":
            raise Http404("POST required.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        try:
            exam = services.publish_exam(pk, request.user)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "success", "message": "Exam published successfully."})

            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": exam.id}))
        except (ValidationError, PermissionDenied) as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)
            raise Http404(str(e))


@method_decorator(role_required("Admin", "Principal", "Teacher"), name="dispatch")
class ExamResultEntryView(View):
    """Record an exam result for a single student."""
    def get(self, request, pk, *args, **kwargs):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        services._validate_teacher_scope(request.user, exam=exam)
        return render(request, "exams/result_entry.html", {"exam": exam})

    def post(self, request, pk, *args, **kwargs):
        student_id = request.POST.get("student_id")
        obtained_marks = request.POST.get("obtained_marks")
        status = request.POST.get("status", "Present")
        remarks = request.POST.get("remarks", "")

        try:
            result = services.record_exam_result(
                exam_id=pk,
                student_id=student_id,
                obtained_marks=obtained_marks,
                status=status,
                remarks=remarks,
                user=request.user
            )
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({
                    "status": "success",
                    "result_id": result.id,
                    "percentage": result.percentage,
                    "grade": result.grade,
                    "rank": result.rank
                })

            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": pk}))
        except ValidationError as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)

            try:
                exam = Exam.objects.get(pk=pk)
            except Exam.DoesNotExist:
                raise Http404("Exam not found.")
            return render(request, "exams/result_entry.html", {"exam": exam, "error": str(e)}, status=400)


@method_decorator(role_required("Admin", "Principal", "Teacher"), name="dispatch")
class ExamBulkResultEntryView(View):
    """Record exam results for multiple students at once."""
    def get(self, request, pk, *args, **kwargs):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        services._validate_teacher_scope(request.user, exam=exam)

        from apps.students.models import Enrollment
        enrollments = Enrollment.objects.filter(session=exam.session, status="Active").select_related("student")

        return render(request, "exams/bulk_result_entry.html", {
            "exam": exam,
            "enrollments": enrollments
        })

    def post(self, request, pk, *args, **kwargs):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        services._validate_teacher_scope(request.user, exam=exam)

        if request.content_type == "application/json" or request.GET.get("format") == "json":
            try:
                body = json.loads(request.body)
                results_list = body.get("results", [])
            except ValueError:
                return JsonResponse({"status": "error", "message": "Invalid JSON."}, status=400)
        else:
            results_list = []
            student_ids = request.POST.getlist("student_ids")
            obtained_marks = request.POST.getlist("obtained_marks")
            statuses = request.POST.getlist("statuses")
            remarks_list = request.POST.getlist("remarks")
            for i in range(len(student_ids)):
                results_list.append({
                    "student_id": student_ids[i],
                    "obtained_marks": obtained_marks[i] if i < len(obtained_marks) else 0,
                    "status": statuses[i] if i < len(statuses) else "Present",
                    "remarks": remarks_list[i] if i < len(remarks_list) else ""
                })

        try:
            results = services.bulk_result_entry(exam_id=pk, results_list=results_list, user=request.user)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "success", "count": len(results)})

            ns = _get_namespace_prefix(request)
            return redirect(reverse(f"{ns}exam_detail", kwargs={"pk": pk}))
        except ValidationError as e:
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse({"status": "error", "message": str(e)}, status=400)

            from apps.students.models import Enrollment
            enrollments = Enrollment.objects.filter(session=exam.session, status="Active").select_related("student")
            return render(request, "exams/bulk_result_entry.html", {
                "exam": exam,
                "enrollments": enrollments,
                "error": str(e)
            }, status=400)


@method_decorator(role_required("Admin", "Principal", "Teacher"), name="dispatch")
class ExamStatisticsView(View):
    """View calculated statistics of an exam."""
    def get(self, request, pk, *args, **kwargs):
        try:
            exam = Exam.objects.get(pk=pk)
        except Exam.DoesNotExist:
            raise Http404("Exam not found.")

        # Teacher scope check
        if request.user.groups.filter(name="Teacher").exists() and not request.user.is_superuser:
            services._validate_teacher_scope(request.user, exam=exam)

        try:
            stats = services.calculate_exam_statistics(pk)
            if request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.GET.get("format") == "json":
                return JsonResponse(stats)
            return render(request, "exams/exam_statistics.html", {"stats": stats, "exam": exam})
        except ValidationError as e:
            raise Http404(str(e))


# Expose CBVs as function views to preserve namespace backward compatibility
exam_list = ExamListView.as_view()
exam_create = ExamCreateView.as_view()
exam_detail = ExamDetailView.as_view()
exam_edit = ExamEditView.as_view()
exam_results = ExamDetailView.as_view()
exam_results_entry = ExamResultEntryView.as_view()
exam_results_bulk_entry = ExamBulkResultEntryView.as_view()
exam_publish = ExamPublishView.as_view()
exam_review = ExamReviewView.as_view()
exam_statistics = ExamStatisticsView.as_view()
