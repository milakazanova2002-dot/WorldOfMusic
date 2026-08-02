from django import forms

from .models import Performance


class PerformanceMaterialForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ["materials"]
        widgets = {
            "materials": forms.CheckboxSelectMultiple
        }

