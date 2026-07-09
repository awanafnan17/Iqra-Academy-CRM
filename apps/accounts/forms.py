from django import forms
from apps.accounts.models import CustomUser
from apps.core.models import RolePermission

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone', 'cnic']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXXX-XXXXXXX-X'}),
        }

    def clean_cnic(self):
        cnic = self.cleaned_data.get("cnic")
        if not cnic:
            return cnic
        from apps.core.validators import format_cnic, validate_cnic
        normalized = format_cnic(cnic)
        validate_cnic(normalized)
        return normalized


class AdminUserCreateForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[("", "Select Role")] + [(role[0], f"{role[1]} Role") for role in RolePermission.ROLE_CHOICES],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
        required=True
    )
    designation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "email", "phone", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        self.fields["username"].required = False
        self.fields["is_active"].initial = True

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            if CustomUser.objects.filter(username=username).exists():
                raise forms.ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if CustomUser.objects.filter(email=email).exists():
                raise forms.ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")
        role = cleaned_data.get("role")
        designation = cleaned_data.get("designation")
        department = cleaned_data.get("department")

        if password and confirm_password and password != confirm_password:
            self.add_error("confirm_password", "Passwords do not match.")

        if role == "Teacher":
            if not designation:
                self.add_error("designation", "Designation is required for Teacher role.")
            if not department:
                self.add_error("department", "Department is required for Teacher role.")
        return cleaned_data


class AdminUserEditForm(forms.ModelForm):
    role = forms.ChoiceField(
        choices=[("", "Select Role")] + [(role[0], f"{role[1]} Role") for role in RolePermission.ROLE_CHOICES],
        required=True,
        widget=forms.Select(attrs={"class": "form-select"})
    )
    designation = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    department = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "username", "email", "phone", "is_active"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["email"].required = True
        self.fields["username"].required = True

        if self.instance and self.instance.pk:
            current_roles = list(self.instance.groups.values_list("name", flat=True))
            canonical_role_names = [role[0] for role in RolePermission.ROLE_CHOICES]
            assigned_canonical_role = next((r for r in current_roles if r in canonical_role_names), "")
            self.fields["role"].initial = assigned_canonical_role

            if hasattr(self.instance, "faculty_profile") and self.instance.faculty_profile:
                self.fields["designation"].initial = self.instance.faculty_profile.designation
                self.fields["department"].initial = self.instance.faculty_profile.department

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            if CustomUser.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email:
            if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Email is already registered.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        designation = cleaned_data.get("designation")
        department = cleaned_data.get("department")

        if role == "Teacher":
            if not designation:
                self.add_error("designation", "Designation is required for Teacher role.")
            if not department:
                self.add_error("department", "Department is required for Teacher role.")
        return cleaned_data
