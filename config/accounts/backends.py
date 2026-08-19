from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

User = get_user_model()


class EmailOrPhoneBackend(ModelBackend):
    """Позволяет входить не только по логину, но и по email или телефону —
    пользователь вводит любой из трёх в то же самое поле "логин" на форме входа."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = (
            User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username) | Q(phone=username)
            )
            .order_by("id")
            .first()
        )

        if user is None:
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
