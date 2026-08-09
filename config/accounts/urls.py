from django.urls import path
from .views import (
    UserLoginView,
    UserLogoutView,
    guest_register,
    pending_approval,
    role_redirect,
    student_register,
    teacher_register,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/student/", student_register, name="student_register"),
    path("register/teacher/", teacher_register, name="teacher_register"),
    path("register/guest/", guest_register, name="guest_register"),
    path("pending/", pending_approval, name="pending_approval"),
    path("redirect/", role_redirect, name="role_redirect"),
]