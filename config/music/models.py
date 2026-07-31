from django.db import models

# Create your models here.from django.db import models


class Instrument(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Инструмент"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )
    class Meta:
        verbose_name = "Инструмент"
        verbose_name_plural = "Инструменты"

    def __str__(self):
        return self.name


class Genre(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name="Жанр"
    )

    class Meta:
        verbose_name = "Жанр"
        verbose_name_plural = "Жанры"

    def __str__(self):
        return self.name


class Composer(models.Model):
    first_name = models.CharField(
        max_length=100,
        verbose_name="Имя"
    )

    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия"
    )

    biography = models.TextField(
        blank=True,
        verbose_name="Биография"
    )

    class Meta:
        verbose_name = "Композитор"
        verbose_name_plural = "Композиторы"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class MusicalPiece(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название"
    )

    composer = models.ForeignKey(
        Composer,
        on_delete=models.CASCADE,
        related_name="pieces",
        verbose_name="Композитор"
    )

    genre = models.ManyToManyField(
        Genre,
        blank=True,
        related_name="pieces",
        verbose_name="Жанры"
    )

    instruments = models.ManyToManyField(
        Instrument,
        blank=True,
        related_name="pieces",
        verbose_name="Инструменты"
    )

    year_created = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Год создания"
    )

    description = models.TextField(
        blank=True,
        verbose_name="Описание"
    )

    class Meta:
        verbose_name = "Музыкальное произведение"
        verbose_name_plural = "Музыкальные произведения"
        
    def __str__(self):
        return self.title
