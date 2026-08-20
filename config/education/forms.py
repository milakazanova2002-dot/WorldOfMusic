from django import forms

from .models import Lesson, LessonMaterial, Performance, PerformanceComment, TeachingAssignment


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
        fields = ["student", "subject"]


class PerformanceCommentForm(forms.ModelForm):
    class Meta:
        model = PerformanceComment
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3})
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ["date", "instrument", "piece", "homework", "comment"]
        widgets = {
            "date": forms.DateTimeInput(attrs={"class": "form-control", "type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "instrument": forms.Select(attrs={"class": "form-select"}),
            "piece": forms.Select(attrs={"class": "form-select"}),
            "homework": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Что нужно выучить/повторить к следующему уроку"}),
            "comment": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Заметки педагога об уроке"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["date"].input_formats = ["%Y-%m-%dT%H:%M"]


class LessonMaterialForm(forms.ModelForm):
    class Meta:
        model = LessonMaterial
        fields = ["title", "file"]
