from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import User
from education.models import TeacherProfile


@receiver(post_save, sender=User)
def create_teacher_profile_after_approval(sender, instance, created, raw=False, **kwargs):
    # raw=True — сохранение идёт из loaddata (восстановление фикстуры).
    # В этом случае TeacherProfile придёт своей строкой в самой фикстуре,
    # сигналу вмешиваться не нужно — иначе будет дубликат по user_id.
    if raw:
        return
    if instance.is_approved and not hasattr(instance, "teacher_profile"):
        TeacherProfile.objects.create(user=instance)
