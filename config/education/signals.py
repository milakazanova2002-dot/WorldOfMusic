from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import User

from .models import StudentProfile, TeacherProfile


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == User.Role.TEACHER:
            TeacherProfile.objects.create(user=instance)

        elif instance.role == User.Role.STUDENT:
            StudentProfile.objects.create(user=instance)