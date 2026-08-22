from django.db import models
from accounts.models import User
from music.models import Instrument



class TeacherProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="teacher_profile",
        verbose_name="Пользователь"
    )

    bio = models.TextField(
        blank=True,
        verbose_name="О себе"
    )

    experience_years = models.PositiveIntegerField(
        default=0,
        verbose_name="Опыт работы (лет)"
    )

    instruments = models.ManyToManyField(
        Instrument,
        blank=True,
        verbose_name="Инструменты"
    )

    subjects = models.ManyToManyField(
        "Subject",
        blank=True,
        related_name="teachers",
        verbose_name="Предметы"
    )

    class Meta:
            verbose_name = "Профиль педагога"
            verbose_name_plural = "Профили педагогов"

            
    def __str__(self):
        return f"Педагог: {self.user.get_full_name() or self.user.username}"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name="Пользователь"
    )

    age = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Возраст"
    )

    instruments = models.ManyToManyField(
        Instrument,
        blank=True,
        verbose_name="Инструменты"
    )

    level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Уровень подготовки"
    )

    class Meta:
        verbose_name = "Профиль ученика"
        verbose_name_plural = "Профили учеников"

    def __str__(self):
        return f"Ученик: {self.user.get_full_name() or self.user.username}"


class Lesson(models.Model):

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Ученик"
    )

    date = models.DateTimeField(
        verbose_name="Дата и время"
    )

    instrument = models.ForeignKey(
        Instrument,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Инструмент"
    )

    piece = models.ForeignKey(
        "music.MusicalPiece",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Произведение"
    )

    homework = models.TextField(
        blank=True,
        verbose_name="Домашнее задание"
    )

    comment = models.TextField(
        blank=True,
        verbose_name="Комментарий педагога"
    )

    assignment = models.ForeignKey(
        "education.TeachingAssignment",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="lessons",
        verbose_name="Курс"
    )

    class Meta:
            verbose_name = "Урок"
            verbose_name_plural = "Занятия"


    def __str__(self):
        return f"{self.student} — {self.date.strftime('%d.%m.%Y')}"


class Subject(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Предмет"
    )

    slug = models.SlugField(
        max_length=100,
        unique=True,
        verbose_name="URL-имя"
    )

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return self.name


class TeachingAssignment(models.Model):
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Педагог"
    )

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Ученик"
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name="assignments",
        verbose_name="Предмет"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Обновлено"
    )

    class Meta:
        verbose_name = "Курс (педагог-ученик)"
        verbose_name_plural = "Курсы (педагог-ученик)"

    def __str__(self):
        return f"{self.teacher} → {self.student} ({self.subject})"


class Performance(models.Model):
    assignment = models.ForeignKey(
        TeachingAssignment,
        on_delete=models.CASCADE,
        related_name="performances",
        verbose_name="Курс"
    )

    piece = models.ForeignKey(
        "music.MusicalPiece",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="performances",
        verbose_name="Произведение"
    )

    video = models.FileField(
        upload_to="performances/videos/",
        null=True,
        blank=True,
        verbose_name="Видео исполнения"
    )

    materials = models.ManyToManyField(
        "music.MusicMaterial",
        blank=True,
        related_name="performances",
        verbose_name="Материалы исполнения"
    )
    
    score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Оценка"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    class Meta:
        verbose_name = "Исполнение"
        verbose_name_plural = "Исполнения"

    def __str__(self):
        return f"Исполнение: {self.assignment.student} — {self.piece}"


class PerformanceComment(models.Model):
    performance = models.ForeignKey(
        Performance,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Исполнение"
    )

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        verbose_name="Педагог"
    )

    text = models.TextField(
        verbose_name="Комментарий"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    class Meta:
        verbose_name = "Комментарий к исполнению"
        verbose_name_plural = "Комментарии к исполнениям"

    def __str__(self):
        return f"Комментарий от {self.teacher}"


class LessonMaterial(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="materials")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="lesson_materials/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.lesson})"
