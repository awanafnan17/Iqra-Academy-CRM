from django import forms
from apps.academics.models import Session
from apps.students.models import Student


class StudentCreateForm(forms.Form):

    # Personal Information
    full_name = forms.CharField(
        max_length=200,
        label="Full Name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter full name",
        }),
    )
    father_name = forms.CharField(
        max_length=200,
        required=False,
        label="Father Name",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Enter father name",
        }),
    )
    email = forms.EmailField(
        required=False,
        label="Email Address",
        widget=forms.EmailInput(attrs={
            "class": "form-control",
            "placeholder": "student@email.com",
        }),
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        label="Phone Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "03001234567",
        }),
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date of Birth",
        widget=forms.DateInput(attrs={
            "class": "form-control",
            "type": "date",
        }),
    )
    gender = forms.ChoiceField(
        choices=[
            ("", "Select Gender"),
            ("Male", "Male"),
            ("Female", "Female"),
            ("Other", "Other"),
        ],
        required=False,
        label="Gender",
        widget=forms.Select(
            attrs={"class": "form-select"}
        ),
    )
    cnic = forms.CharField(
        max_length=15,
        required=False,
        label="CNIC Number",
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "XXXXX-XXXXXXX-X",
        }),
    )
    address = forms.CharField(
        required=False,
        label="Address",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": "2",
            "placeholder": "Full address",
        }),
    )

    # Profile Photo (optional)
    profile_photo = forms.ImageField(
        required=False,
        label="Profile Photo (optional)",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": "image/*",
        }),
    )

    # CNIC Photo (optional)
    cnic_photo = forms.FileField(
        required=False,
        label="CNIC Photo/Image (optional)",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": "image/jpeg,image/png,image/webp",
        }),
    )

    # Enrollment Section
    session = forms.ModelChoiceField(
        queryset=Session.objects.filter(
            status="Active"
        ).order_by("name"),
        required=False,
        empty_label="-- Select Session (optional) --",
        label="Enroll in Session",
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "id": "id_session",
                "onchange": "loadSessionFeeInfo(this.value)",
            }
        ),
    )

    # Fee Configuration
    FEE_TYPE_CHOICES = [
        ("", "-- Select Fee Type --"),
        ("one_time", "One-Time Payment"),
        ("monthly", "Monthly Installments"),
    ]

    fee_type = forms.ChoiceField(
        choices=FEE_TYPE_CHOICES,
        required=False,
        label="Fee Payment Type",
        widget=forms.Select(attrs={
            "class": "form-select",
            "id": "id_fee_type",
            "onchange": "toggleInstallmentFields(this.value)",
        }),
    )
    total_fee_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label="Total Fee Amount (PKR)",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. 50000",
            "min": "0",
            "step": "100",
        }),
    )
    number_of_installments = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=24,
        initial=1,
        label="Number of Installments",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. 6",
            "min": "1",
            "max": "24",
            "id": "id_number_of_installments",
        }),
    )
    due_day = forms.IntegerField(
        required=False,
        min_value=1,
        max_value=28,
        initial=10,
        label="Monthly Due Day",
        help_text="Day of month when payment is due (1-28).",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "e.g. 10",
            "min": "1",
            "max": "28",
            "id": "id_due_day",
        }),
    )
    discount_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        initial=0,
        label="Discount Amount (PKR)",
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": "0",
            "min": "0",
        }),
    )

    def clean(self):
        cleaned = super().clean()
        session = cleaned.get("session")
        fee_type = cleaned.get("fee_type")
        total_fee = cleaned.get("total_fee_amount")
        num_inst = cleaned.get("number_of_installments")

        if session and fee_type:
            if not total_fee or total_fee <= 0:
                self.add_error(
                    "total_fee_amount",
                    "Enter a valid fee amount when "
                    "assigning a session.",
                )
            if fee_type == "monthly":
                if not num_inst or num_inst < 1:
                    self.add_error(
                        "number_of_installments",
                        "Enter number of installments "
                        "for monthly payment.",
                    )
        return cleaned

    def clean_cnic(self):
        cnic = self.cleaned_data.get("cnic")
        if not cnic:
            return cnic
        from apps.core.validators import format_cnic, validate_cnic
        normalized = format_cnic(cnic)
        validate_cnic(normalized)
        return normalized

    def clean_cnic_photo(self):
        file = self.cleaned_data.get("cnic_photo")
        if file:
            # Enforce file size limit (2MB)
            if file.size > 2 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 2MB.")
            # Enforce file type (image only: jpeg, png, webp)
            ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
            allowed_exts = {'jpg', 'jpeg', 'png', 'webp'}
            if ext not in allowed_exts:
                raise forms.ValidationError("Only JPG, JPEG, PNG, and WEBP image files are allowed.")
            # Enforce content type
            content_type = getattr(file, 'content_type', '')
            allowed_mimes = {'image/jpeg', 'image/png', 'image/webp'}
            if content_type and content_type not in allowed_mimes:
                raise forms.ValidationError("Invalid image content type.")
        return file


from apps.students.models import Guardian

class GuardianForm(forms.ModelForm):
    class Meta:
        model = Guardian
        fields = ['full_name', 'relationship', 'phone', 'email', 'cnic', 'is_primary', 'is_emergency_contact', 'occupation', 'address']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control', 'required': 'required'}),
            'relationship': forms.Select(attrs={'class': 'form-select'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXXX-XXXXXXX-X'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_emergency_contact': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_cnic(self):
        cnic = self.cleaned_data.get("cnic")
        if not cnic:
            return cnic
        from apps.core.validators import format_cnic, validate_cnic
        normalized = format_cnic(cnic)
        validate_cnic(normalized)
        return normalized


from apps.students.models import StudentDocument

class StudentDocumentForm(forms.ModelForm):
    class Meta:
        model = StudentDocument
        fields = ['document_type', 'title', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title (optional)'}),
            'file': forms.ClearableFileInput(attrs={'class': 'form-control', 'required': 'required'}),
        }

from apps.students.models import Enrollment

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ['student', 'session', 'registration_date', 'status', 'registration_fee', 'fee', 'discount']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'session': forms.Select(attrs={'class': 'form-select', 'required': 'required'}),
            'registration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'registration_fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty for session default'}),
            'fee': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Leave empty for session default'}),
            'discount': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount if any'}),
        }

from apps.students.models import Student

class StudentForm(forms.ModelForm):
    cnic_photo = forms.FileField(
        required=False,
        label="CNIC Photo/Image (optional)",
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control",
            "accept": "image/jpeg,image/png,image/webp",
        }),
    )

    class Meta:
        model = Student
        fields = [
            'full_name', 'father_name', 'email', 'phone', 'date_of_birth',
            'gender', 'cnic', 'address_temporary', 'address_permanent', 'profile_photo', 'status', 'inactive_reason'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'cnic': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XXXXX-XXXXXXX-X'}),
            'address_temporary': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'address_permanent': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'profile_photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'inactive_reason': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean_cnic(self):
        cnic = self.cleaned_data.get("cnic")
        if not cnic:
            return cnic
        from apps.core.validators import format_cnic, validate_cnic
        normalized = format_cnic(cnic)
        validate_cnic(normalized)
        return normalized

    def clean_cnic_photo(self):
        file = self.cleaned_data.get("cnic_photo")
        if file:
            # Enforce file size limit (2MB)
            if file.size > 2 * 1024 * 1024:
                raise forms.ValidationError("File size must be under 2MB.")
            # Enforce file type (image only: jpeg, png, webp)
            ext = file.name.split('.')[-1].lower() if '.' in file.name else ''
            allowed_exts = {'jpg', 'jpeg', 'png', 'webp'}
            if ext not in allowed_exts:
                raise forms.ValidationError("Only JPG, JPEG, PNG, and WEBP image files are allowed.")
            # Enforce content type
            content_type = getattr(file, 'content_type', '')
            allowed_mimes = {'image/jpeg', 'image/png', 'image/webp'}
            if content_type and content_type not in allowed_mimes:
                raise forms.ValidationError("Invalid image content type.")
        return file


from apps.students.models import Lead

class LeadForm(forms.ModelForm):
    class Meta:
        model = Lead
        fields = [
            'name', 'email', 'phone', 'area_of_residence', 'interested_session',
            'inquiry_date', 'inquiry_source', 'follow_up_date', 'follow_up_notes',
            'status', 'loss_reason'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'area_of_residence': forms.TextInput(attrs={'class': 'form-control'}),
            'interested_session': forms.Select(attrs={'class': 'form-select'}),
            'inquiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'inquiry_source': forms.Select(attrs={'class': 'form-select'}),
            'follow_up_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'follow_up_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': '3'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'loss_reason': forms.TextInput(attrs={'class': 'form-control'}),
        }
