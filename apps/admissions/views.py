from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, CreateView, TemplateView, View
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import Http404, HttpResponse
from django.db.models import Q
import csv

from apps.core.decorators import role_required
from apps.admissions.models import AdmissionApplication, AdmissionDocument
from apps.admissions.forms import AdmissionApplicationForm
from apps.admissions.services import AdmissionService, check_is_admin

def get_client_ip(request):
    """Extract client IP from request headers."""
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "0.0.0.0")


class PublicAdmissionFormView(CreateView):
    """Publicly accessible admission form submission view.
    
    No role restrictions.
    """
    model = AdmissionApplication
    form_class = AdmissionApplicationForm
    template_name = "admissions/public_form.html"
    success_url = reverse_lazy("admissions_public:success")

    def form_valid(self, form):
        # Gather file uploads
        documents = []
        for doc_type in ["cnic", "photo", "academic_certificate", "other"]:
            file_obj = form.cleaned_data.get(f"{doc_type}_file")
            if file_obj:
                documents.append((doc_type, file_obj))

        try:
            AdmissionService.submit_application(
                full_name=form.cleaned_data["full_name"],
                father_name=form.cleaned_data["father_name"],
                email=form.cleaned_data["email"],
                phone=form.cleaned_data["phone"],
                date_of_birth=form.cleaned_data["date_of_birth"],
                desired_session=form.cleaned_data["desired_session"],
                exam_type=form.cleaned_data["exam_type"],
                cnic=form.cleaned_data.get("cnic", ""),
                address=form.cleaned_data.get("address", ""),
                documents=documents,
                user=self.request.user if self.request.user.is_authenticated else None
            )
            messages.success(self.request, "Your admission application has been submitted successfully.")
            return redirect(self.success_url)
        except Exception as e:
            if hasattr(e, "errors") and isinstance(e.errors, dict):
                for field, errs in e.errors.items():
                    # Check if error is list or string
                    if isinstance(errs, list):
                        for err in errs:
                            form.add_error(field, err)
                    else:
                        form.add_error(field, str(errs))
            else:
                form.add_error(None, str(e))
            return self.form_invalid(form)


class PublicSuccessView(TemplateView):
    """Simple public page showing submission success."""
    template_name = "admissions/public_success.html"


@method_decorator(role_required("Admin", "Registrar"), name="dispatch")
class AdmissionListView(ListView):
    """List of all submitted admission applications with basic filters."""
    model = AdmissionApplication
    template_name = "admissions/admission_list.html"
    context_object_name = "applications"
    paginate_by = 25

    def get_queryset(self):
        qs = AdmissionApplication.objects.select_related("desired_session", "reviewed_by", "converted_student").all()
        status_filter = self.request.GET.get("status")
        exam_type_filter = self.request.GET.get("exam_type")
        search_query = self.request.GET.get("q")

        if status_filter:
            qs = qs.filter(status=status_filter)
        if exam_type_filter:
            qs = qs.filter(exam_type=exam_type_filter)
        if search_query:
            qs = qs.filter(
                Q(full_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(cnic__icontains=search_query)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass status choices & exam category choices for filtering dropdowns
        from apps.academics.models import Session
        context["status_choices"] = AdmissionApplication.STATUS_CHOICES
        context["exam_choices"] = Session.SESSION_CATEGORY_CHOICES
        context["status_filter"] = self.request.GET.get("status", "")
        context["exam_filter"] = self.request.GET.get("exam_type", "")
        context["search_query"] = self.request.GET.get("q", "")
        return context


@method_decorator(role_required("Admin", "Registrar"), name="dispatch")
class AdmissionDetailView(DetailView):
    """Detailed view of an admission application including actions & document views."""
    model = AdmissionApplication
    template_name = "admissions/admission_detail.html"
    context_object_name = "application"

    def get_queryset(self):
        return AdmissionApplication.objects.select_related(
            "desired_session", "reviewed_by", "converted_student"
        ).prefetch_related("documents")


@method_decorator(role_required("Admin", "Registrar"), name="dispatch")
class AdmissionReviewView(View):
    """Action to transition admission status to under_review."""
    def get(self, request, *args, **kwargs):
        raise Http404()

    def post(self, request, pk):
        remarks = request.POST.get("remarks", "")
        AdmissionService.review_application(
            application_id=pk,
            user=request.user,
            remarks=remarks,
            ip_address=get_client_ip(request)
        )
        messages.success(request, "Application status set to Under Review.")
        return redirect(f"{request.resolver_match.namespace}:admission_detail", pk=pk)


@method_decorator(role_required("Admin"), name="dispatch")
class AdmissionApproveView(View):
    """Action to approve admission application."""
    def get(self, request, *args, **kwargs):
        raise Http404()

    def post(self, request, pk):
        remarks = request.POST.get("remarks", "")
        AdmissionService.approve_application(
            application_id=pk,
            user=request.user,
            remarks=remarks,
            ip_address=get_client_ip(request)
        )
        messages.success(request, "Application approved successfully.")
        return redirect(f"{request.resolver_match.namespace}:admission_detail", pk=pk)


@method_decorator(role_required("Admin"), name="dispatch")
class AdmissionRejectView(View):
    """Action to reject admission application."""
    def get(self, request, *args, **kwargs):
        raise Http404()

    def post(self, request, pk):
        remarks = request.POST.get("remarks", "")
        AdmissionService.reject_application(
            application_id=pk,
            user=request.user,
            remarks=remarks,
            ip_address=get_client_ip(request)
        )
        messages.success(request, "Application rejected.")
        return redirect(f"{request.resolver_match.namespace}:admission_detail", pk=pk)


@method_decorator(role_required("Admin"), name="dispatch")
class AdmissionConvertView(View):
    """Action to convert approved application into student profile."""
    def get(self, request, *args, **kwargs):
        raise Http404()

    def post(self, request, pk):
        try:
            student = AdmissionService.convert_to_student(
                application_id=pk,
                user=request.user,
                ip_address=get_client_ip(request)
            )
            messages.success(
                request,
                f"Applicant converted successfully! Registered Student: {student.full_name} (Roll: {student.roll_number})."
            )
        except Exception as e:
            messages.error(request, f"Error during student conversion: {str(e)}")
        return redirect(f"{request.resolver_match.namespace}:admission_detail", pk=pk)



@method_decorator(role_required("Admin", "Registrar"), name="dispatch")
class AdmissionSummaryView(TemplateView):
    """Aggregated admission performance metrics dashboard."""
    template_name = "admissions/admission_summary.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["summary"] = AdmissionService.get_application_summary()
        return context


@method_decorator(role_required("Admin"), name="dispatch")
class AdmissionExportCSVView(View):
    """Export all applications to CSV."""
    def get(self, request):
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="admissions_export.csv"'
        
        # BOM for Excel compatibility
        response.write('\ufeff'.encode('utf-8'))
        
        writer = csv.writer(response)
        writer.writerow([
            "Full Name", "Father's Name", "Email", "Phone",
            "Date of Birth", "CNIC", "Exam Type", "Desired Session", "Status", "Remarks", "Applied At"
        ])
        
        applications = AdmissionApplication.objects.select_related("desired_session").all()
        for app in applications:
            writer.writerow([
                app.full_name,
                app.father_name,
                app.email,
                app.phone,
                app.date_of_birth,
                app.cnic,
                app.get_exam_type_display(),
                app.desired_session.name if app.desired_session else "N/A",
                app.get_status_display(),
                app.remarks,
                app.applied_at.strftime("%Y-%m-%d %H:%M")
            ])
        return response
