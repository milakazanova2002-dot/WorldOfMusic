from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Пользователь сайта WOM.
    """

    class Role(models.TextChoices):
        TEACHER = "teacher", "Педагог"
        STUDENT = "student", "Ученик"
        PARENT = "parent", "Родитель"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        verbose_name="Роль"
    )

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар"
    )

    def __str__(self):
        return self.username