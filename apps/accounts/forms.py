from django import forms
from apps.accounts.models import CustomUser

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
