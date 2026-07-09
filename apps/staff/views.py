from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator

from apps.core.decorators import role_required
from apps.staff.models import FacultyProfile
from apps.staff.forms import UserCreateForm, FacultyProfileForm, FacultyProfileUpdateForm, FacultyAssignSessionForm

User = get_user_model()


@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class FacultyListView(LoginRequiredMixin, ListView):
    model = FacultyProfile
    template_name = "staff/faculty_list.html"
    context_object_name = "faculty_list"


@method_decorator(role_required("Admin"), name="dispatch")
class FacultyCreateView(LoginRequiredMixin, CreateView):
    model = FacultyProfile
    template_name = "staff/faculty_form.html"
    form_class = FacultyProfileForm
    success_url = reverse_lazy("admin_panel:staff:faculty_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["user_form"] = UserCreateForm(self.request.POST)
        else:
            context["user_form"] = UserCreateForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context["user_form"]
        if user_form.is_valid():
            with transaction.atomic():
                user = user_form.save(commit=False)
                # Auto-assign standard username prefix logic
                user.save()

                # Assign selected role group
                selected_role = form.cleaned_data.get("role")
                role_group, _ = Group.objects.get_or_create(name=selected_role)
                user.groups.add(role_group)

                # Create profile
                profile = form.save(commit=False)
                profile.user = user
                profile.save()
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))


@method_decorator(role_required("Admin", "Principal"), name="dispatch")
class FacultyAssignSessionView(LoginRequiredMixin, UpdateView):
    model = FacultyProfile
    template_name = "staff/faculty_assign.html"
    form_class = FacultyAssignSessionForm
    success_url = reverse_lazy("admin_panel:staff:faculty_list")


@method_decorator(role_required("Admin"), name="dispatch")
class FacultyUpdateView(LoginRequiredMixin, UpdateView):
    model = FacultyProfile
    template_name = "staff/faculty_form.html"
    form_class = FacultyProfileUpdateForm
    success_url = reverse_lazy("admin_panel:staff:faculty_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_edit"] = True
        return context

