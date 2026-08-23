from django import forms
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm, UserCreationForm
from django.utils.text import slugify

from accounts.models import User
from education.models import StudentProfile, Subject, TeacherProfile


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
        "username": "Логин, email или телефон",
        "password": "Пароль",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Логин, email или телефон"


class StyledPasswordChangeForm(StyledFormMixin, PasswordChangeForm):
    placeholders = {
        "old_password": "Текущий пароль",
        "new_password1": "Новый пароль",
        "new_password2": "Повторите новый пароль",
    }


# ---------- Регистрация ----------


class StudentRegistrationForm(StyledFormMixin, UserCreationForm):
    # Имя и фамилию просим у всех — чтобы на сайте везде было видно человека,
    # а не логин.
    first_name = forms.CharField(label="Имя", max_length=150, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=150, required=True)
    gender = forms.ChoiceField(
        label="Пол",
        choices=[("", "Выберите пол")] + list(User.Gender.choices),
        required=True,
    )

    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "gender")

    def save(self, commit=True):
        user = super().save(commit)
        StudentProfile.objects.create(user=user)
        return user


class TeacherRegistrationForm(StyledFormMixin, UserCreationForm):
    # У педагогов дополнительно обязательно отчество — чтобы ученики
    # могли увидеть его в профиле и правильно обращаться.
    first_name = forms.CharField(label="Имя", max_length=150, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=150, required=True)
    patronymic = forms.CharField(label="Отчество", max_length=150, required=True)
    gender = forms.ChoiceField(
        label="Пол",
        choices=[("", "Выберите пол")] + list(User.Gender.choices),
        required=True,
    )

    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "patronymic": "Отчество",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "patronymic", "gender")

    def save(self, commit=True):
        user = super().save(commit)
        user.is_approved = False
        user.save()
        return user


class GuestRegistrationForm(StyledFormMixin, UserCreationForm):
    # Имя и фамилию просим и у гостя/родителя — иначе ученик не поймёт,
    # кто именно прислал ему запрос на привязку.
    first_name = forms.CharField(label="Имя", max_length=150, required=True)
    last_name = forms.CharField(label="Фамилия", max_length=150, required=True)
    gender = forms.ChoiceField(
        label="Пол",
        choices=[("", "Выберите пол")] + list(User.Gender.choices),
        required=True,
    )

    placeholders = {
        "username": "Придумайте логин",
        "email": "you@example.com",
        "first_name": "Имя",
        "last_name": "Фамилия",
        "password1": "Придумайте пароль",
        "password2": "Повторите пароль",
    }

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "gender")
    # save() не переопределяем — отдельный профиль гостю/родителю не нужен,
    # привязка к ученику делается через ParentLink после регистрации


# ---------- Редактирование профиля ----------


class UserProfileForm(forms.ModelForm):
    """Форма редактирования основных данных пользователя."""

    class Meta:
        model = User
        fields = ("first_name", "last_name", "patronymic", "gender", "email", "phone", "avatar", "email_notifications")
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            "patronymic": forms.TextInput(attrs={"class": "form-control"}),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control", "placeholder": "+7..."}),
            "avatar": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "email_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_phone(self):
        # Пустую строку превращаем в None — иначе у двух пользователей без
        # телефона поле unique=True споткнётся о два одинаковых "" в базе.
        phone = self.cleaned_data.get("phone", "").strip()
        return phone or None


class TeacherProfileForm(forms.ModelForm):
    """Форма редактирования профиля педагога."""

    # Предметы можно выбрать чекбоксами (поле subjects ниже) ИЛИ вписать новые через запятую.
    new_subjects = forms.CharField(
        label="Новые предметы",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: сольфеджио, вокал (через запятую)"}),
        help_text="Если нужного предмета нет в списке выше — впишите его сюда",
    )

    class Meta:
        model = TeacherProfile
        fields = ("bio", "experience_years", "subjects")
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "experience_years": forms.NumberInput(attrs={"class": "form-control"}),
            "subjects": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        }

    def save(self, commit=True):
        teacher = super().save(commit=commit)

        # добавляем предметы, вписанные вручную
        new_subjects = self.cleaned_data.get("new_subjects", "")
        for name in new_subjects.split(","):
            name = name.strip()
            if name:
                subject_obj = Subject.objects.filter(name__iexact=name).first()
                if not subject_obj:
                    subject_obj = Subject.objects.create(
                        name=name.lower(),
                        slug=slugify(name, allow_unicode=True),
                    )
                teacher.subjects.add(subject_obj)

        return teacher


class StudentProfileForm(forms.ModelForm):
    """Форма редактирования профиля ученика."""

    class Meta:
        model = StudentProfile
        fields = ("age", "level")
        widgets = {
            "age": forms.NumberInput(attrs={"class": "form-control"}),
            "level": forms.TextInput(attrs={"class": "form-control", "placeholder": "Начальный, Средний, Продвинутый"}),
        }