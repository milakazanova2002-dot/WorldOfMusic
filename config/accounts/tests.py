from django.test import TestCase, Client
from django.urls import reverse

from accounts.backends import EmailOrPhoneBackend
from accounts.forms import GuestRegistrationForm, StudentRegistrationForm, TeacherRegistrationForm
from accounts.models import User
from education.models import ParentLink, StudentProfile, TeacherProfile


class UserModelTests(TestCase):
    """Базовые проверки кастомной модели пользователя."""

    def test_str_returns_username(self):
        user = User.objects.create_user(username="ivanov", password="pass12345")
        self.assertEqual(str(user), "ivanov")

    def test_gender_field_accepts_declared_choices(self):
        user = User.objects.create_user(username="petrova", password="pass12345", gender=User.Gender.FEMALE)
        self.assertEqual(user.gender, "female")

    def test_new_user_is_not_approved_by_default(self):
        user = User.objects.create_user(username="new_teacher", password="pass12345")
        self.assertFalse(user.is_approved)


class StudentRegistrationFormTests(TestCase):
    """Регистрация ученика: обязательные поля и создание профиля."""

    def valid_data(self, **overrides):
        data = {
            "username": "student1",
            "email": "student1@example.com",
            "first_name": "Аня",
            "last_name": "Петрова",
            "gender": User.Gender.FEMALE,
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_user_and_student_profile(self):
        form = StudentRegistrationForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())

    def test_gender_is_required(self):
        form = StudentRegistrationForm(data=self.valid_data(gender=""))
        self.assertFalse(form.is_valid())
        self.assertIn("gender", form.errors)

    def test_first_and_last_name_are_required(self):
        form = StudentRegistrationForm(data=self.valid_data(first_name="", last_name=""))
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)
        self.assertIn("last_name", form.errors)


class TeacherRegistrationFormTests(TestCase):
    """Регистрация педагога: отчество обязательно, аккаунт не одобрен сразу."""

    def valid_data(self, **overrides):
        data = {
            "username": "teacher1",
            "email": "teacher1@example.com",
            "first_name": "Мария",
            "last_name": "Иванова",
            "patronymic": "Петровна",
            "gender": User.Gender.FEMALE,
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        }
        data.update(overrides)
        return data

    def test_valid_form_creates_unapproved_teacher_profile(self):
        form = TeacherRegistrationForm(data=self.valid_data())
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertFalse(user.is_approved)
        self.assertTrue(TeacherProfile.objects.filter(user=user).exists())

    def test_patronymic_is_required(self):
        form = TeacherRegistrationForm(data=self.valid_data(patronymic=""))
        self.assertFalse(form.is_valid())
        self.assertIn("patronymic", form.errors)


class GuestRegistrationFormTests(TestCase):
    """Регистрация гостя/родителя: без отдельного профиля."""

    def test_valid_form_creates_user_without_any_profile(self):
        data = {
            "username": "parent1",
            "email": "parent1@example.com",
            "first_name": "Ольга",
            "last_name": "Орлова",
            "gender": User.Gender.FEMALE,
            "password1": "SuperSecret123",
            "password2": "SuperSecret123",
        }
        form = GuestRegistrationForm(data=data)
        self.assertTrue(form.is_valid(), form.errors)

        user = form.save()

        self.assertFalse(hasattr(user, "teacher_profile"))
        self.assertFalse(hasattr(user, "student_profile"))


class EmailOrPhoneBackendTests(TestCase):
    """Логин по логину, email или телефону."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="multiuser",
            email="multi@example.com",
            phone="+70000000001",
            password="correct-pass",
        )
        self.backend = EmailOrPhoneBackend()

    def test_authenticate_by_username(self):
        user = self.backend.authenticate(None, username="multiuser", password="correct-pass")
        self.assertEqual(user, self.user)

    def test_authenticate_by_email(self):
        user = self.backend.authenticate(None, username="multi@example.com", password="correct-pass")
        self.assertEqual(user, self.user)

    def test_authenticate_by_phone(self):
        user = self.backend.authenticate(None, username="+70000000001", password="correct-pass")
        self.assertEqual(user, self.user)

    def test_wrong_password_returns_none(self):
        user = self.backend.authenticate(None, username="multiuser", password="wrong")
        self.assertIsNone(user)

    def test_unknown_login_returns_none(self):
        user = self.backend.authenticate(None, username="nobody", password="correct-pass")
        self.assertIsNone(user)


class RoleRedirectViewTests(TestCase):
    """Проверка, что 'accounts:role_redirect' ведёт разных пользователей
    в правильный личный кабинет."""

    def setUp(self):
        self.client = Client()

    def _login(self, user):
        user.set_password("pass12345")
        user.save()
        self.client.login(username=user.username, password="pass12345")

    def test_unapproved_teacher_goes_to_pending_approval(self):
        user = User.objects.create_user(username="t_pending", gender=User.Gender.MALE)
        TeacherProfile.objects.create(user=user)
        self._login(user)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("accounts:pending_approval"))

    def test_approved_teacher_goes_to_teacher_dashboard(self):
        # is_approved=True при создании может автоматически создать TeacherProfile
        # через сигнал (accounts/signals.py) — get_or_create() не даст дубля
        # независимо от того, сработал сигнал или нет.
        user = User.objects.create_user(username="t_approved", gender=User.Gender.MALE, is_approved=True)
        TeacherProfile.objects.get_or_create(user=user)
        self._login(user)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("education:teacher_dashboard"))

    def test_student_goes_to_student_dashboard(self):
        user = User.objects.create_user(username="s_one", gender=User.Gender.FEMALE)
        StudentProfile.objects.create(user=user)
        self._login(user)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("education:student_dashboard"))

    def test_parent_with_pending_link_goes_to_parent_request_page(self):
        parent = User.objects.create_user(username="parent_pending", gender=User.Gender.FEMALE)
        student_user = User.objects.create_user(username="s_two", gender=User.Gender.MALE)
        student = StudentProfile.objects.create(user=student_user)
        ParentLink.objects.create(parent=parent, student=student)
        self._login(parent)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("education:parent_request_link"))

    def test_guest_without_role_or_gender_goes_to_complete_profile(self):
        # Имитация аккаунта, созданного через Google: пола нет, роли нет.
        user = User.objects.create_user(username="google_guest")
        user.set_unusable_password()
        user.save()
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("accounts:complete_profile"))

    def test_guest_with_gender_and_no_role_goes_home(self):
        user = User.objects.create_user(username="plain_guest", gender=User.Gender.MALE)
        self._login(user)

        response = self.client.get(reverse("accounts:role_redirect"))

        self.assertRedirects(response, reverse("home"))


class AccountDeleteViewTests(TestCase):
    """Удаление аккаунта требует подтверждения паролем."""

    def setUp(self):
        self.user = User.objects.create_user(username="to_delete", password="correct-pass", gender=User.Gender.MALE)
        self.client = Client()
        self.client.login(username="to_delete", password="correct-pass")

    def test_correct_password_deletes_account(self):
        response = self.client.post(reverse("accounts:account_delete"), {"password": "correct-pass"})

        self.assertRedirects(response, reverse("home"))
        self.assertFalse(User.objects.filter(pk=self.user.pk).exists())

    def test_wrong_password_keeps_account(self):
        response = self.client.post(reverse("accounts:account_delete"), {"password": "wrong-pass"})

        self.assertRedirects(response, reverse("accounts:account_delete"))
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_superuser_cannot_delete_via_this_view(self):
        admin = User.objects.create_superuser(username="admin1", email="admin1@example.com", password="adminpass")
        self.client.login(username="admin1", password="adminpass")

        response = self.client.post(reverse("accounts:account_delete"), {"password": "adminpass"})

        self.assertRedirects(response, reverse("accounts:account_menu"))
        self.assertTrue(User.objects.filter(pk=admin.pk).exists())
