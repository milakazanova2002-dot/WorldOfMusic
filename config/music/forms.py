from django import forms
from .models import MusicalPiece, MusicMaterial, Composer, Genre, Instrument


class MusicalPieceForm(forms.ModelForm):
    class Meta:
        model = MusicalPiece
        fields = [
            "title",
            "composer",
            "genre",
            "instruments",
            "year_created",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название произведения"}),
            "composer": forms.Select(attrs={"class": "form-select"}),
            "genre": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "instruments": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "year_created": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Год создания"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Описание произведения"}),
        }


class ComposerForm(forms.ModelForm):
    class Meta:
        model = Composer
        fields = ["first_name", "last_name", "biography"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Фамилия"}),
            "biography": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Биография"}),
        }


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название жанра"}),
        }


class InstrumentForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название инструмента"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Описание"}),
        }
