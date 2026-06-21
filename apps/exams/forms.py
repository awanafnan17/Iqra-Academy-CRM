from django import forms
from apps.exams.models import GradeConfig

class GradeConfigForm(forms.ModelForm):
    class Meta:
        model = GradeConfig
        fields = ["session", "grade_name", "min_percentage", "max_percentage", "grade_point", "sort_order"]
        widgets = {
            "session": forms.Select(attrs={"class": "form-select"}),
            "grade_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. A+"}),
            "min_percentage": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}),
            "max_percentage": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "100", "step": "0.01"}),
            "grade_point": forms.NumberInput(attrs={"class": "form-control", "min": "0", "max": "5.00", "step": "0.01"}),
            "sort_order": forms.NumberInput(attrs={"class": "form-control", "min": "0"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        min_pct = cleaned_data.get("min_percentage")
        max_pct = cleaned_data.get("max_percentage")
        session = cleaned_data.get("session")
        grade_name = cleaned_data.get("grade_name")

        if min_pct is not None and max_pct is not None:
            if min_pct > max_pct:
                self.add_error("min_percentage", "Minimum percentage must be less than or equal to maximum.")

            # Overlap check
            qs = GradeConfig.objects.filter(session=session)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            # Check for range overlap: min_percentage <= existing.max_percentage AND max_percentage >= existing.min_percentage
            overlapping = qs.filter(
                min_percentage__lte=max_pct,
                max_percentage__gte=min_pct
            )
            if overlapping.exists():
                overlap_grades = ", ".join([obj.grade_name for obj in overlapping])
                self.add_error("min_percentage", f"This range overlaps with existing grade configurations: {overlap_grades}.")

            # unique_together check
            if grade_name:
                duplicate_name = qs.filter(grade_name__iexact=grade_name)
                if duplicate_name.exists():
                    self.add_error("grade_name", f"A grade configuration with label '{grade_name}' already exists for this scope.")

        return cleaned_data
