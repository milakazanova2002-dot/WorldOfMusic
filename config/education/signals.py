from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User
from .models import TeacherProfile, StudentProfile


@receiver(post_save, sender=User)
def create_profiles_if_missing(sender, instance, created, **kwargs):
    """
    WOM-логика:
    - Профили создаются автоматически, если их нет.
    - Не зависит от role.
    - Пользователь может иметь оба профиля.
    """

    if created:
        # Создаём пустые профили
        TeacherProfile.objects.create(user=instance)
        StudentProfile.objects.create(user=instance)

    else:
        # Если профиля нет — создаём
        if not hasattr(instance, "teacher_profile"):
            TeacherProfile.objects.create(user=instance)

        if not hasattr(instance, "student_profile"):
            StudentProfile.objects.create(user=instance)
