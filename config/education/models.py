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

    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="students",
        verbose_name="Педагог"
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
    teacher = models.ForeignKey(
        TeacherProfile,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Педагог"
    )

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

    class Meta:
            verbose_name = "Урок"
            verbose_name_plural = "Занятия"


    def __str__(self):
        return f"{self.student} — {self.date.strftime('%d.%m.%Y')}"