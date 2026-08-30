import json
import logging
import secrets
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.http import HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)

from .forms import (
    CompleteProfileForm,
    GuestRegistrationForm,
    StudentRegistrationForm,
    StyledAuthenticationForm,
    StyledPasswordChangeForm,
    TeacherRegistrationForm,
    UserProfileForm,
    TeacherProfileForm,
    StudentProfileForm,
)
from .models import User
from education.models import TeacherProfile, StudentProfile
from .avatars import assign_default_avatar


def needs_profile_setup(user):
    """True, если у пользователя нет ни роли, ни пола — то есть аккаунт
    создан через Google и обычную регистрацию (где пол обязателен) не проходил."""
    has_role = (
        hasattr(user, "teacher_profile")
        or hasattr(user, "student_profile")
        or user.parent_links.exists()
    )
    return not has_role and not user.gender


@method_decorator(never_cache, name="dispatch")
class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)  #  создает новую сессию

        # Аккаунт без роли и без пола — пришёл через Google, роль не выбрана
        if needs_profile_setup(user):
            return redirect("accounts:complete_profile")

        # Если педагог не одобрен
        if hasattr(user, "teacher_profile") and not user.is_approved:
            return redirect("accounts:pending_approval")

        # Педагог
        if hasattr(user, "teacher_profile"):
            return redirect("education:teacher_dashboard")

        # Ученик
        if hasattr(user, "student_profile"):
            return redirect("education:student_dashboard")

        # Родитель с хотя бы одной привязкой (подтверждённой или ожидающей)
        if user.parent_links.exists():
            return redirect("education:parent_request_link")

        # Обычный гость
        return redirect("home")

@method_decorator(never_cache, name="dispatch")
class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("education:student_dashboard")  
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/student_register.html", {"form": form})

def guest_register(request):
    if request.method == "POST":
        form = GuestRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("home")
    else:
        form = GuestRegistrationForm()

    return render(request, "accounts/guest_register.html", {"form": form})

def teacher_register(request):
    if request.method == "POST":
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "Ваша заявка отправлена. Администратор рассмотрит её и одобрит ваш аккаунт."
            )

            return redirect("accounts:login")
    else:
        form = TeacherRegistrationForm()

    return render(request, "accounts/teacher_register.html", {"form": form})


def pending_approval(request):
    return render(request, "accounts/pending_approval.html")


@login_required
def complete_profile(request):
    """Просим пользователя без роли и пола (обычно — вошедшего через Google)
    выбрать, кто он: ученик, педагог или родитель, и указать пол.
    Без этого шага такие аккаунты навсегда оставались бы гостями."""
    user = request.user

    # Роль уже выбрана раньше — второй раз сюда заходить незачем
    if not needs_profile_setup(user):
        return redirect("accounts:role_redirect")

    if request.method == "POST":
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            role = form.cleaned_data["role"]
            user.gender = form.cleaned_data["gender"]

            if role == "teacher":
                user.patronymic = form.cleaned_data["patronymic"]
                user.is_approved = False
                user.save()
                TeacherProfile.objects.create(user=user)  # без этого hasattr(user, "teacher_profile") всегда False
                assign_default_avatar(user, "teacher")
                messages.success(
                    request,
                    "Заявка отправлена. Администратор рассмотрит её и одобрит ваш аккаунт.",
                )
                return redirect("accounts:pending_approval")

            if role == "student":
                StudentProfile.objects.create(user=user)
                assign_default_avatar(user, "student")
                return redirect("education:student_dashboard")

            # role == "parent" — отдельный профиль не нужен, привязка
            # к ученику делается позже через ParentLink
            assign_default_avatar(user, "parent")
            return redirect("education:parent_request_link")
    else:
        form = CompleteProfileForm()

    return render(request, "accounts/complete_profile.html", {"form": form})


class UserPasswordChangeView(PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")


class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


def google_login(request):
    """Отправляет пользователя на экран согласия Google."""
    if not settings.GOOGLE_OAUTH_CLIENT_ID:
        messages.error(request, "Вход через Google пока не настроен администратором сайта.")
        return redirect("accounts:login")

    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state

    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)
    return redirect(url)


def google_callback(request):
    """Сюда Google возвращает пользователя после согласия — обмениваем код на токен и логиним."""
    if request.GET.get("error"):
        messages.error(request, "Вход через Google отменён.")
        return redirect("accounts:login")

    state = request.GET.get("state")
    if not state or state != request.session.get("google_oauth_state"):
        return HttpResponseBadRequest("Неверный state — попробуйте войти снова.")

    code = request.GET.get("code")
    if not code:
        return HttpResponseBadRequest("Google не передал код авторизации.")

    # 1. Обмениваем code на access_token
    token_data = urllib.parse.urlencode({
        "code": code,
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()

    try:
        token_request = urllib.request.Request(
            "https://oauth2.googleapis.com/token", data=token_data, method="POST"
        )
        with urllib.request.urlopen(token_request, timeout=10) as response:
            token_response = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        # Google вернул код ошибки (не 2xx) — тело ответа обычно содержит
        # понятное описание причины (например redirect_uri_mismatch,
        # invalid_client, invalid_grant). Печатаем в лог сервера, но
        # пользователю показываем общее сообщение.
        body = e.read().decode(errors="replace")
        logger.error("Google OAuth: обмен code на token не удался (HTTP %s): %s", e.code, body)
        messages.error(request, "Не удалось связаться с Google. Попробуйте позже.")
        return redirect("accounts:login")
    except Exception:
        logger.exception("Google OAuth: обмен code на token не удался (сетевая ошибка)")
        messages.error(request, "Не удалось связаться с Google. Попробуйте позже.")
        return redirect("accounts:login")

    access_token = token_response.get("access_token")
    if not access_token:
        messages.error(request, "Google не вернул токен доступа.")
        return redirect("accounts:login")

    # 2. Получаем данные профиля (имя, email)
    try:
        info_request = urllib.request.Request(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        with urllib.request.urlopen(info_request, timeout=10) as response:
            profile = json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        logger.error("Google OAuth: не удалось получить профиль (HTTP %s): %s", e.code, body)
        messages.error(request, "Не удалось получить данные профиля Google.")
        return redirect("accounts:login")
    except Exception:
        logger.exception("Google OAuth: не удалось получить профиль (сетевая ошибка)")
        messages.error(request, "Не удалось получить данные профиля Google.")
        return redirect("accounts:login")

    email = profile.get("email")
    if not email:
        messages.error(request, "Google не предоставил email.")
        return redirect("accounts:login")

    user = User.objects.filter(email__iexact=email).first()

    if user is None:
        # Новый пользователь через Google — создаём как гостя (без роли педагога/ученика).
        # Пароль не задаём: у такого аккаунта вход возможен только через Google.
        base_username = email.split("@")[0]
        username = base_username
        suffix = 1
        while User.objects.filter(username=username).exists():
            suffix += 1
            username = f"{base_username}{suffix}"

        user = User.objects.create(
            username=username,
            email=email,
            first_name=profile.get("given_name", ""),
            last_name=profile.get("family_name", ""),
        )
        user.set_unusable_password()
        user.save()
        messages.success(request, "Аккаунт создан через Google!")

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    return redirect("accounts:role_redirect")


@login_required
def account_delete(request):
    """Удаление аккаунта — требует подтверждения паролем, чтобы не удалить
    случайно (например, если кто-то подошёл к незалоченному компьютеру)."""
    if request.user.is_superuser:
        messages.error(request, "Аккаунт администратора нельзя удалить через сайт — только через панель Django.")
        return redirect("accounts:account_menu")

    if request.method == "POST":
        if request.user.has_usable_password():
            password = request.POST.get("password", "")
            ok = request.user.check_password(password)
            error = "Неверный пароль. Аккаунт не удалён."
        else:
            confirm_email = request.POST.get("confirm_email", "").strip()
            ok = confirm_email.lower() == request.user.email.lower()
            error = "Email не совпадает. Аккаунт не удалён."

        if ok:
            user = request.user
            logout(request)
            user.delete()
            messages.success(request, "Аккаунт удалён.")
            return redirect("home")
        else:
            messages.error(request, error)
            return redirect("accounts:account_delete")

    return render(request, "accounts/account_delete.html")


@login_required
def account_menu(request):
    """Маленькая страница-меню: сюда ведёт кружок с инициалами в хедере.
    Здесь только «Настройки» и «Выйти» — сам личный кабинет (дашборд)
    открывается отдельным пунктом навигации «Кабинет»."""
    return render(request, "accounts/account_menu.html")


@login_required
def role_redirect(request):
    user = request.user

    # Аккаунт без роли и без пола — пришёл через Google, роль не выбрана
    if needs_profile_setup(user):
        return redirect("accounts:complete_profile")

    # Не одобренный педагог
    if hasattr(user, "teacher_profile") and not user.is_approved:
        return redirect("accounts:pending_approval")

    # Педагог
    if hasattr(user, "teacher_profile"):
        return redirect("education:teacher_dashboard")

    # Ученик
    if hasattr(user, "student_profile"):
        return redirect("education:student_dashboard")

    # Родитель с хотя бы одной привязкой (подтверждённой или ожидающей)
    if user.parent_links.exists():
        return redirect("education:parent_request_link")

    # Обычный гость
    return redirect("home")


# ---------- Редактирование профиля ----------


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование данных пользователя (имя, email, аватар)."""
    model = User
    form_class = UserProfileForm
    template_name = "accounts/edit_profile.html"

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Профиль успешно обновлён!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:profile_edit")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, "teacher_profile"):
            context["teacher_form"] = TeacherProfileForm(
                instance=self.request.user.teacher_profile
            )
        if hasattr(self.request.user, "student_profile"):
            context["student_form"] = StudentProfileForm(
                instance=self.request.user.student_profile
            )
        return context


class TeacherProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля педагога."""
    model = TeacherProfile
    form_class = TeacherProfileForm
    template_name = "accounts/edit_teacher_profile.html"

    def get_object(self):
        return self.request.user.teacher_profile

    def form_valid(self, form):
        messages.success(self.request, "Профиль педагога обновлён!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:teacher_profile_edit")


class StudentProfileEditView(LoginRequiredMixin, UpdateView):
    """Редактирование профиля ученика."""
    model = StudentProfile
    form_class = StudentProfileForm
    template_name = "accounts/edit_student_profile.html"

    def get_object(self):
        return self.request.user.student_profile

    def form_valid(self, form):
        messages.success(self.request, "Профиль ученика обновлён!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("accounts:student_profile_edit")