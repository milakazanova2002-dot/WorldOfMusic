from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from .forms import StudentRegistrationForm, TeacherRegistrationForm


class UserLoginView(LoginView):
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.get_user()

        # Если педагог не одобрен
        if hasattr(user, "teacher_profile") and not user.is_approved:
            return redirect("pending_approval")

        # Педагог
        if hasattr(user, "teacher_profile"):
            return redirect("teacher_dashboard")

        # Ученик
        if hasattr(user, "student_profile"):
            return redirect("student_dashboard")

        # Гость (в будущем родитель)
        return redirect("/")


class UserLogoutView(LogoutView):
    # template_name = "accounts/logout.html"
    next_page = "login"

def student_register(request):
    if request.method == "POST":
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  
            return redirect("student_dashboard")  
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


@login_required
def role_redirect(request):
    user = request.user

    # Не одобренный педагог
    if hasattr(user, "teacher_profile") and not user.is_approved:
        return redirect("pending_approval")

    # Педагог
    if hasattr(user, "teacher_profile"):
        return redirect("teacher_dashboard")

    # Ученик
    if hasattr(user, "student_profile"):
        return redirect("student_dashboard")

    # Гость (в будущем родитель)
    return redirect("/")
