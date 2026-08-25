from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from education.models import TeacherProfile


@receiver(post_save, sender=User)
def create_teacher_profile_after_approval(sender, instance, **kwargs):
    # С момента исправления в TeacherRegistrationForm.save() профиль педагога
    # создаётся сразу при регистрации, поэтому в норме этот сигнал больше не
    # должен ничего делать. Оставлен как подстраховка для аккаунтов,
    # зарегистрированных ДО этого исправления (у них профиля могло не быть).
    if instance.is_approved and not hasattr(instance, "teacher_profile"):
        TeacherProfile.objects.create(user=instance)
