from django import forms
from django.contrib.auth import get_user_model
from apps.academics.models import Session, ClassSchedule, Subject, TeacherAssignment

User = get_user_model()

class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = [
            "name",
            "code",
            "roll_prefix",
            "session_type",
            "session_category",
            "academic_year",
            "batch_number",
            "max_capacity",
            "is_admission_open",
            "description",
            "start_date",
            "end_date",
            "fee",
            "registration_fee",
            "status",
            "max_students",
            "late_fee_amount",
            "late_fee_grace_days",
            "late_fee_maximum",
            "due_day",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Computer Science 2026"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS2026"}),
            "roll_prefix": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. CS"}),
            "session_type": forms.Select(attrs={"class": "form-select"}),
            "session_category": forms.Select(attrs={"class": "form-select"}),
            "academic_year": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. 2026"}),
            "batch_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Batch 1"}),
            "max_capacity": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 50"}),
            "is_admission_open": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter session description..."}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "registration_fee": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "status": forms.Select(attrs={"class": "form-select"}),
            "max_students": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g. 50 (empty for unlimited)"}),
            "late_fee_amount": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "late_fee_grace_days": forms.NumberInput(attrs={"class": "form-control"}),
            "late_fee_maximum": forms.NumberInput(attrs={"class": "form-control", "step": "0.01"}),
            "due_day": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 28}),
        }


class ClassScheduleForm(forms.ModelForm):
    class Meta:
        model = ClassSchedule
        fields = [
            "session",
            "subject",
            "faculty",
            "day_of_week",
            "start_time",
            "end_time",
            "classroom",
            "is_active",
        ]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "faculty": forms.Select(attrs={"class": "form-select"}),
            "day_of_week": forms.Select(attrs={"class": "form-select"}),
            "start_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "end_time": forms.TimeInput(attrs={"class": "form-control", "type": "time"}),
            "classroom": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Classroom 3B"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ["name", "code", "session", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. Mathematics"}),
            "code": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. MATH101"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter subject description..."}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class TeacherAssignmentForm(forms.ModelForm):
    class Meta:
        model = TeacherAssignment
        fields = ["teacher", "session", "subject", "assigned_from", "assigned_until", "is_active"]
        widgets = {
            "teacher": forms.Select(attrs={"class": "form-select"}),
            "session": forms.Select(attrs={"class": "form-select"}),
            "subject": forms.Select(attrs={"class": "form-select"}),
            "assigned_from": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "assigned_until": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        teacher_qs = User.objects.filter(groups__name="Teacher")
        session_qs = Session.objects.filter(status="Active")
        subject_qs = Subject.objects.filter(is_active=True)

        if self.instance and self.instance.pk:
            if self.instance.teacher:
                teacher_qs = teacher_qs | User.objects.filter(pk=self.instance.teacher.pk)
            if self.instance.session:
                session_qs = session_qs | Session.objects.filter(pk=self.instance.session.pk)
            if self.instance.subject:
                subject_qs = subject_qs | Subject.objects.filter(pk=self.instance.subject.pk)

        self.fields["teacher"].queryset = teacher_qs.distinct().order_by("first_name", "last_name")
        self.fields["session"].queryset = session_qs.distinct().order_by("name")
        self.fields["subject"].queryset = subject_qs.distinct().order_by("name")

    def clean(self):
        cleaned_data = super().clean()
        assigned_from = cleaned_data.get("assigned_from")
        assigned_until = cleaned_data.get("assigned_until")

        if assigned_from and assigned_until and assigned_until < assigned_from:
            raise forms.ValidationError("End date must be on or after start date.")

        return cleaned_data


