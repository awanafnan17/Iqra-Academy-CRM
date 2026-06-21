from django import forms
from apps.notifications.models import NotificationTemplate

class NotificationTemplateForm(forms.ModelForm):
    class Meta:
        model = NotificationTemplate
        fields = [
            'name', 'code', 'channel', 'subject_template', 'body_template',
            'is_active', 'description'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'channel': forms.Select(attrs={'class': 'form-select'}),
            'subject_template': forms.TextInput(attrs={'class': 'form-control'}),
            'body_template': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
        }
