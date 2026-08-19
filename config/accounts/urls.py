from django.urls import path
from .views import (
    ProfileEditView,
    StudentProfileEditView,
    TeacherProfileEditView,
    UserLoginView,
    UserLogoutView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
    account_menu,
    google_callback,
    google_login,
    guest_register,
    pending_approval,
    role_redirect,
    student_register,
    teacher_register,
)

app_name = "accounts"

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path("logout/", UserLogoutView.as_view(), name="logout"),
    path("register/student/", student_register, name="student_register"),
    path("register/teacher/", teacher_register, name="teacher_register"),
    path("register/guest/", guest_register, name="guest_register"),
    path("pending/", pending_approval, name="pending_approval"),
    path("redirect/", role_redirect, name="role_redirect"),
    path("account/", account_menu, name="account_menu"),
    path("password/change/", UserPasswordChangeView.as_view(), name="password_change"),
    path("password/change/done/", UserPasswordChangeDoneView.as_view(), name="password_change_done"),
    path("google/login/", google_login, name="google_login"),
    path("google/callback/", google_callback, name="google_callback"),

    # Редактирование профиля
    path("profile/edit/", ProfileEditView.as_view(), name="profile_edit"),
    path("profile/teacher/edit/", TeacherProfileEditView.as_view(), name="teacher_profile_edit"),
    path("profile/student/edit/", StudentProfileEditView.as_view(), name="student_profile_edit"),
]
