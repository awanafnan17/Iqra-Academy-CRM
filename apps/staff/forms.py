from django import forms
from django.contrib.auth import get_user_model
from apps.staff.models import FacultyProfile
from apps.academics.models import Session
from apps.core.models import RolePermission

User = get_user_model()


class UserCreateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"class": "form-control"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control"}), required=True)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class FacultyProfileForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[("", "Select Role")] + [(role[0], f"{role[1]} Role") for role in RolePermission.ROLE_CHOICES],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    designation = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    department = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    class Meta:
        model = FacultyProfile
        fields = ["designation", "department", "is_active"]


class FacultyAssignSessionForm(forms.ModelForm):
    assigned_sessions = forms.ModelMultipleChoiceField(
        queryset=Session.objects.filter(status="Active"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False
    )

    class Meta:
        model = FacultyProfile
        fields = ["assigned_sessions"]
