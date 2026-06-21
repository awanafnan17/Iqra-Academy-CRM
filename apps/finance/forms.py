from django import forms
from apps.finance.models import Payment, Expense, Refund, InstallmentPlan
from apps.finance.models import ExpenseCategory

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ["enrollment", "amount", "payment_date", "payment_method", "reference_number", "notes"]
        widgets = {
            "enrollment": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "payment_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference_number": forms.TextInput(attrs={"class": "form-control", "placeholder": "Reference No."}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ["category", "amount", "expense_date", "description"]
        widgets = {
            "category": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "expense_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class RefundForm(forms.ModelForm):
    class Meta:
        model = Refund
        fields = ["amount", "refund_date", "reason"]
        widgets = {
            "amount": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
            "refund_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class InstallmentPlanForm(forms.ModelForm):
    class Meta:
        model = InstallmentPlan
        fields = ["total_amount", "number_of_installments", "notes"]
        widgets = {
            "total_amount": forms.NumberInput(attrs={"class": "form-control", "min": "0.01", "step": "0.01"}),
            "number_of_installments": forms.NumberInput(attrs={"class": "form-control", "min": "1"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
