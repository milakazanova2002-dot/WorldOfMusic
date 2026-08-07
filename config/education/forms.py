from django import forms

from .models import Performance, PerformanceComment, TeachingAssignment


class PerformanceMaterialForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = ["materials"]
        widgets = {
            "materials": forms.CheckboxSelectMultiple
        }


class AssignmentForm(forms.ModelForm):
    class Meta:
        model = TeachingAssignment
        fields = ["teacher", "student", "subject"]


class PerformanceCommentForm(forms.ModelForm):
    class Meta:
        model = PerformanceComment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3})
        }
