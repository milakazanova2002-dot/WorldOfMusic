from django.db import models


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

    cover = models.ImageField(
        upload_to="pieces_covers/",
        blank=True,
        null=True,
        verbose_name="Обложка"
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


    def get_gradient_class(self):
        """Возвращает CSS-строку для градиента на основе жанра."""
        genres = list(self.genre.all())
        if not genres:
            return 'background: linear-gradient(135deg, #667eea, #764ba2);'

        # Разные цвета для разных жанров
        gradient_map = {
            'Классика': 'linear-gradient(135deg, #667eea, #764ba2)',
            'Романс': 'linear-gradient(135deg, #f093fb, #f5576c)',
            'Народная': 'linear-gradient(135deg, #4facfe, #00f2fe)',
            'Оперная': 'linear-gradient(135deg, #fa709a, #fee140)',
            'Хоровая': 'linear-gradient(135deg, #a18cd1, #fbc2eb)',
        }

        genre_name = genres[0].name
        gradient = gradient_map.get(genre_name, 'linear-gradient(135deg, #667eea, #764ba2)')
        return f'background: {gradient};'

    def get_badge_class(self):
        """Возвращает класс Bootstrap для бейджа."""
        badge_map = {
            'Классика': 'primary',
            'Романс': 'danger',
            'Народная': 'success',
            'Оперная': 'warning',
            'Хоровая': 'info',
        }
        genres = list(self.genre.all())
        if not genres:
            return 'secondary'
        return badge_map.get(genres[0].name, 'secondary')
        
    def __str__(self):
        return self.title
    


class MusicMaterial(models.Model):
    class MaterialType(models.TextChoices):
        VIDEO = "video", "Видео"
        AUDIO = "audio", "Аудио"
        SHEET = "sheet", "Ноты (PDF)"
        IMAGE = "image", "Изображение нот"
        LINK = "link", "Ссылка"

    piece = models.ForeignKey(
        "music.MusicalPiece",
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name="Произведение"
    )

    type = models.CharField(
        max_length=20,
        choices=MaterialType.choices,
        verbose_name="Тип материала"
    )

    file = models.FileField(
        upload_to="materials/",
        null=True,
        blank=True,
        verbose_name="Файл"
    )

    url = models.URLField(
        null=True,
        blank=True,
        verbose_name="Ссылка"
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Описание"
    )

    is_public = models.BooleanField(
        default=True,
        verbose_name="Общедоступно",
        help_text="Если выключено — материал видят только педагоги и прикреплённые ученики"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Создано"
    )

    class Meta:
        verbose_name = "Материал к произведению"
        verbose_name_plural = "Материалы к произведениям"

    def __str__(self):
        return f"{self.piece.title} — {self.get_type_display()}"