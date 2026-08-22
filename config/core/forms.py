from django import forms

from .models import SupportRequest


class SupportRequestForm(forms.ModelForm):
    class Meta:
        model = SupportRequest
        fields = ["subject", "message", "email"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control", "placeholder": "Тема обращения"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 6, "placeholder": "Опишите проблему или вопрос подробно"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "your@email.com"}),
        }
