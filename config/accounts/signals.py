from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from education.models import TeacherProfile


@receiver(post_save, sender=User)
def create_teacher_profile_after_approval(sender, instance, **kwargs):
    # Если пользователь одобрен и профиля нет — создаём
    if instance.is_approved and not hasattr(instance, "teacher_profile"):
        TeacherProfile.objects.create(user=instance)
