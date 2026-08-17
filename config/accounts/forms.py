from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from accounts.models import User
from education.models import StudentProfile, TeacherProfile


# ---------- Оформление форм ----------


class StyledFormMixin:
    """Убирает длинные стандартные подсказки Django (про условия пароля и т.п.)
    и добавляет bootstrap-класс form-control всем полям."""

    placeholders = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.help_text = ""
            field.widget.attrs["class"] = "form-control"
            if name in self.placeholders:
                field.widget.attrs["placeholder"] = self.placeholders[name]


class StyledAuthenticationForm(StyledFormMixin, AuthenticationForm):
    placeholders = {
        "username": "Ваш логин",
        "password": "Пароль",
    }


# ---------- Регистрация ----------


class StudentRegistrationForm(StyledFormMixin, UserCreationForm):
    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)
        StudentProfile.objects.create(user=user)
        return user


class TeacherRegistrationForm(StyledFormMixin, UserCreationForm):
    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit)
        user.is_approved = False
        user.save()
        return user


class GuestRegistrationForm(StyledFormMixin, UserCreationForm):
    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

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