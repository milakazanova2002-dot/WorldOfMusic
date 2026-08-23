import os

from django.core.files import File

# Файлы лежат прямо в static-папке приложения — их кладёт Милана вручную.
# Имя файла = "{роль}_{пол}.png", например "student_female.png".
DEFAULT_AVATARS_DIR = os.path.join(
    os.path.dirname(__file__), "static", "accounts", "default_avatars"
)


def assign_default_avatar(user, role):
    """Подставляет дефолтную аватарку по роли и полу, если пользователь
    ещё не загрузил свою и указал пол. role: 'student' | 'teacher' | 'parent'.
    Не переопределяет уже загруженный аватар — вызывать безопасно в любой момент."""
    if user.avatar or not user.gender:
        return

    filename = f"{role}_{user.gender}.png"
    path = os.path.join(DEFAULT_AVATARS_DIR, filename)
    if not os.path.exists(path):
        return  # картинку ещё не положили — просто остаёмся без аватара

    with open(path, "rb") as f:
        user.avatar.save(filename, File(f), save=True)
