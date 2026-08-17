from django.contrib import messages
from django.contrib.auth.views import LogoutView
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

from .forms import (
    GuestRegistrationForm,
    StudentRegistrationForm,
    StyledAuthenticationForm,
    TeacherRegistrationForm,
    UserProfileForm,
    TeacherProfileForm,
    StudentProfileForm,
)
from .models import User
from education.models import TeacherProfile, StudentProfile

@method_decorator(never_cache, name="dispatch")
class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)  #  создает новую сессию
        # Если педагог не одобрен
        if hasattr(user, "teacher_profile") and not user.is_approved:
            return redirect("accounts:pending_approval")

        # Педагог
        if hasattr(user, "teacher_profile"):
            return redirect("education:teacher_dashboard")

        # Ученик
        if hasattr(user, "student_profile"):
            return redirect("education:student_dashboard")

        # Гость (в будущем родитель)
        return redirect("home")

@method_decorator(never_cache, name="dispatch")
class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect("education:student_dashboard")  
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/student_register.html", {"form": form})

def guest_register(request):
    if request.method == "POST":
        form = GuestRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
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
def role_redirect(request):
    user = request.user

    # Не одобренный педагог
    if hasattr(user, "teacher_profile") and not user.is_approved:
        return redirect("accounts:pending_approval")

    # Педагог
    if hasattr(user, "teacher_profile"):
        return redirect("education:teacher_dashboard")

    # Ученик
    if hasattr(user, "student_profile"):
        return redirect("education:student_dashboard")

    # Гость (в будущем родитель)
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
