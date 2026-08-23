from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Gender(models.TextChoices):
        MALE = "male", "Мужской"
        FEMALE = "female", "Женский"

    email_verified = models.BooleanField(default=False)

    gender = models.CharField(
        max_length=10,
        choices=Gender.choices,
        blank=True,
        verbose_name="Пол",
        help_text="Используется для подбора аватара по умолчанию",
    )

    patronymic = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Отчество",
    )

    email_notifications = models.BooleanField(
        default=True,
        verbose_name="Уведомления на почту",
        help_text="Получать письма о новых уроках, заданиях и комментариях педагога",
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        unique=True,
        verbose_name="Телефон",
        help_text="Можно использовать вместо логина при входе",
    )

    is_approved = models.BooleanField(default=False)

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    def __str__(self):
        return self.username