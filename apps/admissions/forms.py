from django import forms
from apps.admissions.models import AdmissionApplication, AdmissionDocument
from apps.academics.models import Session

class AdmissionApplicationForm(forms.ModelForm):
    # Optional file fields to support document uploads on application submission
    cnic_file = forms.FileField(
        required=False,
        label="CNIC / B-Form Document",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    photo_file = forms.FileField(
        required=False,
        label="Profile Photograph",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    academic_certificate_file = forms.FileField(
        required=False,
        label="Academic Certificate / Transcript",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )
    other_file = forms.FileField(
        required=False,
        label="Other Supporting Document",
        widget=forms.ClearableFileInput(attrs={"class": "form-control"})
    )

    class Meta:
        model = AdmissionApplication
        fields = [
            "full_name",
            "father_name",
            "email",
            "phone",
            "date_of_birth",
            "cnic",
            "address",
            "desired_session",
            "exam_type",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Your Full Name"}),
            "father_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Father's Full Name"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "email@example.com"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., +923001234567"}),
            "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "cnic": forms.TextInput(attrs={"class": "form-control", "placeholder": "xxxxx-xxxxxxx-x"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Postal Address"}),
            "desired_session": forms.Select(attrs={"class": "form-select"}),
            "exam_type": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit desired_session to active sessions and where admissions are open
        self.fields["desired_session"].queryset = Session.objects.filter(
            status="Active",
            is_admission_open=True
        )

    def clean_cnic(self):
        cnic = self.cleaned_data.get("cnic")
        if not cnic:
            return cnic
        from apps.core.validators import format_cnic, validate_cnic
        normalized = format_cnic(cnic)
        validate_cnic(normalized)
        return normalized
