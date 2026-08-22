import io
import math
import struct
import wave
from datetime import timedelta

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from accounts.models import User
from core.models import Notification
from education.models import (
    Lesson,
    Performance,
    PerformanceComment,
    StudentProfile,
    Subject,
    TeacherProfile,
    TeachingAssignment,
)
from music.models import Composer, Favorite, Genre, Instrument, MusicalPiece, MusicMaterial

DEMO_PASSWORD = "demo12345"


def make_tone_wav(freq=440, duration=2.5):
    """Генерирует короткий синус-тон в WAV на лету — чтобы в демо-данных
    были РЕАЛЬНО проигрываемые аудио-файлы (плеер не будет пустым),
    без скачивания сторонних файлов из интернета."""
    rate = 22050
    n_samples = int(rate * duration)
    buf = io.BytesIO()
    with wave.open(buf, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        frames = bytearray()
        for i in range(n_samples):
            value = int(3000 * math.sin(2 * math.pi * freq * (i / rate)))
            frames += struct.pack("<h", value)
        wav.writeframes(bytes(frames))
    return buf.getvalue()


def get_or_create_subject(name):
    """Безопасно находит или создаёт предмет: сначала ищет без учёта регистра
    по имени, потом — по slug (на случай, если предмет уже был создан вручную
    через форму профиля педагога и совпадает по сути, но не байт-в-байт)."""
    name = name.strip().lower()

    existing = Subject.objects.filter(name__iexact=name).first()
    if existing:
        return existing

    slug = slugify(name, allow_unicode=True)
    existing_by_slug = Subject.objects.filter(slug=slug).first()
    if existing_by_slug:
        return existing_by_slug

    return Subject.objects.create(name=name, slug=slug)


class Command(BaseCommand):
    help = "Заполняет базу демо-данными: педагоги, ученики, уроки, исполнения, избранное, уведомления."

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("Заполнение базы данных..."))

        # ---------- Справочники ----------

        composers_data = [
            ("Иоганн Себастьян", "Бах", "Великий немецкий композитор и органист"),
            ("Вольфганг Амадей", "Моцарт", "Австрийский композитор и музыкант"),
            ("Пётр Ильич", "Чайковский", "Русский композитор, дирижёр и педагог"),
            ("Людвиг ван", "Бетховен", "Немецкий композитор и пианист"),
            ("Фридерик", "Шопен", "Французско-польский композитор и пианист"),
        ]
        composers = []
        for first_name, last_name, biography in composers_data:
            composer, _ = Composer.objects.get_or_create(
                first_name=first_name, last_name=last_name, defaults={"biography": biography}
            )
            composers.append(composer)
        self.stdout.write(f"  ✅ Композиторов: {len(composers)}")

        # Жанры/инструменты/предметы — в нижнем регистре, по общему правилу проекта
        genres = [Genre.objects.get_or_create(name=n)[0] for n in ["классика", "романс", "народная", "оперная", "хоровая"]]
        instruments = [
            Instrument.objects.get_or_create(name=n, defaults={"description": d})[0]
            for n, d in [
                ("фортепиано", "Клавишный музыкальный инструмент"),
                ("скрипка", "Смычковый струнный инструмент"),
                ("вокал", "Исполнение голосом"),
                ("гитара", "Щипковый струнный инструмент"),
                ("флейта", "Духовой музыкальный инструмент"),
            ]
        ]
        subjects = [get_or_create_subject(n) for n in ["вокал", "фортепиано", "гитара", "скрипка"]]
        self.stdout.write(f"  ✅ Жанров: {len(genres)}, инструментов: {len(instruments)}, предметов: {len(subjects)}")

        # ---------- Педагоги ----------

        teacher_user, created = User.objects.get_or_create(
            username="teacher_ivanova",
            defaults={
                "first_name": "Мария",
                "last_name": "Иванова",
                "patronymic": "Петровна",
                "email": "teacher@wom.ru",
                "is_approved": True,
                "is_active": True,
            },
        )
        if created:
            teacher_user.set_password(DEMO_PASSWORD)
            teacher_user.save()

        teacher_profile, _ = TeacherProfile.objects.get_or_create(
            user=teacher_user,
            defaults={"bio": "Педагог высшей категории, стаж 15 лет", "experience_years": 15},
        )
        teacher_profile.instruments.set(instruments[:3])
        teacher_profile.subjects.set(subjects[:3])

        # Второй педагог — специально НЕ одобрен, чтобы было видно бейдж
        # "на рассмотрении" в хедере и страницу pending_approval.
        teacher2_user, created = User.objects.get_or_create(
            username="teacher_smirnov",
            defaults={
                "first_name": "Алексей",
                "last_name": "Смирнов",
                "patronymic": "Дмитриевич",
                "email": "teacher2@wom.ru",
                "is_approved": False,
                "is_active": True,
            },
        )
        if created:
            teacher2_user.set_password(DEMO_PASSWORD)
            teacher2_user.save()

        teacher2_profile, _ = TeacherProfile.objects.get_or_create(
            user=teacher2_user,
            defaults={"bio": "Молодой педагог, специализация — гитара", "experience_years": 3},
        )
        teacher2_profile.instruments.set(instruments[3:4])
        teacher2_profile.subjects.set(subjects[2:3])

        self.stdout.write("  ✅ Педагоги: teacher_ivanova (одобрена), teacher_smirnov (на рассмотрении)")

        # ---------- Ученики ----------

        student_user, created = User.objects.get_or_create(
            username="student_petrova",
            defaults={
                "first_name": "Анна",
                "last_name": "Петрова",
                "email": "student@wom.ru",
                "is_active": True,
            },
        )
        if created:
            student_user.set_password(DEMO_PASSWORD)
            student_user.save()

        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student_user, defaults={"age": 14, "level": "Средний"}
        )
        student_profile.instruments.set(instruments[:2])

        student2_user, created = User.objects.get_or_create(
            username="student_orlov",
            defaults={
                "first_name": "Дмитрий",
                "last_name": "Орлов",
                "email": "student2@wom.ru",
                "is_active": True,
            },
        )
        if created:
            student2_user.set_password(DEMO_PASSWORD)
            student2_user.save()

        student2_profile, _ = StudentProfile.objects.get_or_create(
            user=student2_user, defaults={"age": 11, "level": "Начальный"}
        )
        student2_profile.instruments.set(instruments[3:4])

        self.stdout.write("  ✅ Ученики: student_petrova, student_orlov")

        # ---------- Гость (родитель) ----------

        guest_user, created = User.objects.get_or_create(
            username="guest_orlova",
            defaults={
                "first_name": "Ольга",
                "last_name": "Орлова",
                "email": "guest@wom.ru",
                "is_active": True,
            },
        )
        if created:
            guest_user.set_password(DEMO_PASSWORD)
            guest_user.save()
        self.stdout.write("  ✅ Гость: guest_orlova")

        # ---------- Связи педагог-ученик ----------

        assignment1, _ = TeachingAssignment.objects.get_or_create(
            teacher=teacher_profile, student=student_profile, subject=subjects[0]  # вокал
        )
        assignment2, _ = TeachingAssignment.objects.get_or_create(
            teacher=teacher_profile, student=student2_profile, subject=subjects[1]  # фортепиано
        )
        self.stdout.write("  ✅ Курсы: Иванова—Петрова (вокал), Иванова—Орлов (фортепиано)")

        # ---------- Произведения ----------

        pieces_data = [
            {"title": "Аве Мария", "composer": composers[0], "genres": [genres[0]], "instruments": [instruments[2]], "description": "Один из самых известных духовных романсов"},
            {"title": "Реквием (фрагмент)", "composer": composers[1], "genres": [genres[0], genres[4]], "instruments": [instruments[2]], "description": "Знаменитое хоровое произведение"},
            {"title": "Лунная соната", "composer": composers[3], "genres": [genres[0]], "instruments": [instruments[0]], "description": "Классическое фортепианное произведение"},
            {"title": "Вальс цветов", "composer": composers[2], "genres": [genres[0]], "instruments": [instruments[0]], "description": "Вальс из балета «Щелкунчик»"},
            {"title": "Прелюдия ми минор", "composer": composers[4], "genres": [genres[0]], "instruments": [instruments[0]], "description": "Лирическая фортепианная прелюдия"},
        ]

        pieces = []
        for data in pieces_data:
            piece, _ = MusicalPiece.objects.get_or_create(
                title=data["title"], composer=data["composer"], defaults={"description": data["description"]}
            )
            piece.genre.set(data["genres"])
            piece.instruments.set(data["instruments"])
            pieces.append(piece)
        self.stdout.write(f"  ✅ Произведений: {len(pieces)}")

        # ---------- Материалы (с реально проигрываемым аудио) ----------

        if not pieces[0].materials.exists():
            wav_bytes = make_tone_wav(440, 3)
            MusicMaterial.objects.create(
                piece=pieces[0],
                type=MusicMaterial.MaterialType.PLUS,
                file=ContentFile(wav_bytes, name="ave_maria_plus.wav"),
                description="Плюсовка (демо-запись)",
                is_public=True,
            )
            MusicMaterial.objects.create(
                piece=pieces[0],
                type=MusicMaterial.MaterialType.MINUS,
                file=ContentFile(make_tone_wav(330, 3), name="ave_maria_minus.wav"),
                description="Минусовка (демо-запись)",
                is_public=True,
            )
        if not pieces[2].materials.exists():
            MusicMaterial.objects.create(
                piece=pieces[2],
                type=MusicMaterial.MaterialType.AUDIO,
                file=ContentFile(make_tone_wav(523, 4), name="lunnaya_sonata.wav"),
                description="Пример исполнения (демо-запись)",
                is_public=True,
            )
        self.stdout.write("  ✅ Материалы: демо-аудио прикреплено к 2 произведениям (плеер будет играть)")

        # ---------- Уроки ----------

        now = timezone.now()
        lessons_data = [
            (assignment1, student_profile, now - timedelta(days=7), pieces[0], "Выучить первый куплет наизусть", "Хорошо держит дыхание"),
            (assignment1, student_profile, now + timedelta(days=2), pieces[1], "Повторить партию сопрано", ""),
            (assignment2, student2_profile, now - timedelta(days=3), pieces[2], "Отработать левую руку в медленном темпе", "Есть прогресс с ритмом"),
        ]
        lessons = list(Lesson.objects.filter(assignment__in=[assignment1, assignment2]))
        if not lessons:
            for assignment, student, date, piece, homework, comment in lessons_data:
                lesson = Lesson.objects.create(
                    assignment=assignment, student=student, date=date,
                    instrument=instruments[2], piece=piece, homework=homework, comment=comment,
                )
                lessons.append(lesson)
                if homework:
                    Notification.notify(
                        student.user,
                        f"Новый урок: {date:%d.%m.%Y} (есть задание)",
                        link=reverse("education:lesson_detail", kwargs={"pk": lesson.pk}),
                    )
        self.stdout.write(f"  ✅ Уроков: {len(lessons)}")

        # ---------- Исполнения + комментарии педагога ----------

        perf1, created = Performance.objects.get_or_create(
            assignment=assignment1, piece=pieces[0], defaults={"score": 8}
        )
        if created:
            comment = PerformanceComment.objects.create(
                performance=perf1, teacher=teacher_profile, text="Отлично! Поработай над динамикой во второй части."
            )
            Notification.notify(
                student_profile.user, "Педагог оставил комментарий к вашему исполнению",
                link=reverse("education:performance_detail", kwargs={"pk": perf1.pk}),
            )

        perf2, _ = Performance.objects.get_or_create(
            assignment=assignment2, piece=pieces[2], defaults={"score": 6}
        )
        self.stdout.write("  ✅ Исполнений: 2 (одно с комментарием педагога)")

        # ---------- Избранное ----------

        Favorite.objects.get_or_create(user=student_user, piece=pieces[0])
        Favorite.objects.get_or_create(user=student_user, piece=pieces[3])
        Favorite.objects.get_or_create(user=teacher_user, piece=pieces[2])
        self.stdout.write("  ✅ Избранное заполнено")

        self.stdout.write(self.style.SUCCESS("\n✅ База данных заполнена демо-данными!\n"))
        self.stdout.write(f"Пароль у всех демо-аккаунтов один: {DEMO_PASSWORD}\n")
        self.stdout.write("Логины для входа:")
        self.stdout.write("  Педагог (одобрена):      teacher_ivanova")
        self.stdout.write("  Педагог (на рассмотрении): teacher_smirnov")
        self.stdout.write("  Ученик:                   student_petrova")
        self.stdout.write("  Ученик:                   student_orlov")
        self.stdout.write("  Гость/родитель:            guest_orlova")
