from django import forms
from django.contrib.auth.forms import UserCreationForm

from accounts.models import User
from education.models import StudentProfile, TeacherProfile


# ---------- Регистрация ----------


class StudentRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)
        StudentProfile.objects.create(user=user)
        return user


class TeacherRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)
        user.is_approved = False
        user.save()
        return user


class GuestRegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username", "email")
    # save() не переопределяем — профиль ему не нужен


# ---------- Редактирование профиля ----------


class UserProfileForm(forms.ModelForm):
    """Форма редактирования основных данных пользователя."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "email", "avatar")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }


class TeacherProfileForm(forms.ModelForm):
    """Форма редактирования профиля педагога."""

    class Meta:
        model = TeacherProfile
        fields = ("bio", "experience_years")
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control"}),
        }


class StudentProfileForm(forms.ModelForm):
    """Форма редактирования профиля ученика."""

    class Meta:
        model = StudentProfile
        fields = ("age", "level")
        widgets = {
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "level": forms.TextInput(attrs={"class": "form-control", "placeholder": "Начальный, Средний, Продвинутый"}),
        }