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


def validate_profile_picture(picture):
    if picture:
        # 1. Validate file size (max 2 MB = 2 * 1024 * 1024 bytes)
        if picture.size > 2 * 1024 * 1024:
            raise forms.ValidationError("File size must not exceed 2 MB.")
        
        # 2. Validate file extension
        import os
        ext = os.path.splitext(picture.name)[1].lower()
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if ext not in valid_extensions:
            raise forms.ValidationError("Invalid file type. Allowed types: JPG, PNG, WEBP.")
        
        # 3. Validate actual image content using Pillow
        from PIL import Image
        try:
            img = Image.open(picture)
            img.verify()
            if img.format not in ['JPEG', 'PNG', 'WEBP']:
                raise forms.ValidationError("Invalid image format. Allowed formats: JPEG, PNG, WEBP.")
            # Seek back to 0 so django can save the file
            if hasattr(picture, 'seek'):
                picture.seek(0)
        except Exception:
            raise forms.ValidationError("Uploaded file is not a valid image.")
    return picture


class FacultyProfileForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[("", "Select Role")] + [(role[0], f"{role[1]} Role") for role in RolePermission.ROLE_CHOICES],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    profile_picture = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        help_text="JPG, PNG, or WEBP. Max 2 MB."
    )
    designation = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    department = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    class Meta:
        model = FacultyProfile
        fields = ["profile_picture", "designation", "department", "is_active"]

    def clean_profile_picture(self):
        return validate_profile_picture(self.cleaned_data.get("profile_picture"))


class FacultyProfileUpdateForm(forms.ModelForm):
    profile_picture = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
        help_text="JPG, PNG, or WEBP. Max 2 MB."
    )
    designation = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    department = forms.CharField(max_length=100, widget=forms.TextInput(attrs={"class": "form-control"}))
    is_active = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"}))

    class Meta:
        model = FacultyProfile
        fields = ["profile_picture", "designation", "department", "is_active"]

    def clean_profile_picture(self):
        return validate_profile_picture(self.cleaned_data.get("profile_picture"))


class FacultyAssignSessionForm(forms.ModelForm):
    assigned_sessions = forms.ModelMultipleChoiceField(
        queryset=Session.objects.filter(status="Active"),
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        required=False
    )

    class Meta:
        model = FacultyProfile
        fields = ["assigned_sessions"]
