from functools import wraps

from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.contrib import messages

class TeacherRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user

        # Не авторизован
        if not user.is_authenticated:
            return redirect("login")

        # Нет профиля педагога
        if not hasattr(user, "teacher_profile"):
            messages.error(request, "Доступ только для педагогов.")
            return redirect("login")

        # Педагог не одобрен
        if not user.is_approved:
            return redirect("pending_approval")

        return super().dispatch(request, *args, **kwargs)


class StudentRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        user = request.user

        if not user.is_authenticated:
            return redirect("login")

        if not hasattr(user, "student_profile"):
            messages.error(request, "Доступ только для учеников.")
            return redirect("login")

        return super().dispatch(request, *args, **kwargs)


def teacher_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Не авторизован
        if not request.user.is_authenticated:
            return HttpResponseForbidden("Вы должны войти в систему.")

        # Не педагог
        if not hasattr(request.user, "teacher_profile"):
            return HttpResponseForbidden("Только педагог может оставлять комментарии.")

        # Педагог не одобрен
        if not request.user.is_approved:
            return HttpResponseForbidden("Ваш аккаунт ещё не одобрен администратором.")

        return view_func(request, *args, **kwargs)

    return _wrapped_view