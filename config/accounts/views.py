from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.contrib.auth import login

from .forms import StudentRegistrationForm, TeacherRegistrationForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.get_user()

        # Если пользователь педагог и не одобрен
        if hasattr(user, "teacher_profile") and not user.is_approved:
            return redirect("pending_approval")


        return super().form_valid(form)


class UserLogoutView(LogoutView):
    template_name = "accounts/logout.html"


def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # автоматический вход
            return redirect("/")  # или куда нужно
    else:
        form = StudentRegistrationForm()

    return render(request, "accounts/student_register.html", {"form": form})


def teacher_register(request):
    if request.method == "POST":
        form = TeacherRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(
                request,
                "Ваша заявка отправлена. Администратор рассмотрит её и одобрит ваш аккаунт."
            )

            return redirect("login")
    else:
        form = TeacherRegistrationForm()

    return render(request, "accounts/teacher_register.html", {"form": form})


def pending_approval(request):
    return render(request, "accounts/pending_approval.html")
