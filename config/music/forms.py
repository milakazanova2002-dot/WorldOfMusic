from django import forms
from .models import MusicalPiece, MusicMaterial, Composer, Genre, Instrument


class MusicalPieceForm(forms.ModelForm):
    # Композитора вводим текстом вместо выбора из готового списка —
    # если такого ещё нет в базе, он создастся автоматически при сохранении.
    composer_name = forms.CharField(
        label="Композитор",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя и фамилия композитора"}),
        help_text="Если такого композитора ещё нет в базе — он будет создан автоматически",
    )

    # Жанры можно выбрать чекбоксами (поле genre ниже) ИЛИ вписать новые через запятую.
    new_genres = forms.CharField(
        label="Новые жанры",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: вальс, этюд (через запятую)"}),
        help_text="Если нужного жанра нет в списке выше — впишите его сюда",
    )

    # Инструменты можно выбрать чекбоксами (поле instruments ниже) ИЛИ вписать новые через запятую.
    new_instruments = forms.CharField(
        label="Новые инструменты",
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: домра, баян (через запятую)"}),
        help_text="Если нужного инструмента нет в списке выше — впишите его сюда",
    )

    # Материалы к произведению — добавляются сразу при создании.
    sheet_file = forms.FileField(
        label="Ноты (PDF или изображение)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    minus_file = forms.FileField(
        label="Минусовка (аудио без мелодии)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    plus_file = forms.FileField(
        label="Плюсовка (аудио с мелодией)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    video_file = forms.FileField(
        label="Видео профессионального исполнения (файл)",
        required=False,
        widget=forms.ClearableFileInput(attrs={"class": "form-control"}),
    )
    video_url = forms.URLField(
        label="Или ссылка на видео (YouTube и т.п.)",
        required=False,
        widget=forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
    )

    class Meta:
        model = MusicalPiece
        fields = [
            "title",
            "cover",
            "genre",
            "instruments",
            "year_created",
            "description",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название произведения"}),
            "cover": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "genre": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "instruments": forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
            "year_created": forms.NumberInput(attrs={"class": "form-control", "placeholder": "Год создания"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Описание произведения"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # при редактировании — показываем текущего композитора в текстовом поле
        if self.instance and self.instance.pk and self.instance.composer_id:
            self.fields["composer_name"].initial = str(self.instance.composer)

    def save(self, commit=True):
        # находим композитора по имени или создаём нового
        full_name = self.cleaned_data["composer_name"].strip()
        first_name, _, last_name = full_name.partition(" ")
        composer, _ = Composer.objects.get_or_create(
            first_name=first_name.strip(),
            last_name=last_name.strip(),
        )

        piece = super().save(commit=False)
        piece.composer = composer

        if commit:
            piece.save()
            self.save_m2m()  # сохраняет выбранные чекбоксами жанры и инструменты

            # добавляем жанры, вписанные вручную
            new_genres = self.cleaned_data.get("new_genres", "")
            for name in new_genres.split(","):
                name = name.strip()
                if name:
                    genre_obj = self._get_or_create_ci(Genre, name)
                    piece.genre.add(genre_obj)

            # добавляем инструменты, вписанные вручную
            new_instruments = self.cleaned_data.get("new_instruments", "")
            for name in new_instruments.split(","):
                name = name.strip()
                if name:
                    instrument_obj = self._get_or_create_ci(Instrument, name)
                    piece.instruments.add(instrument_obj)

            # создаём материалы из загруженных файлов (если есть)
            self._add_material(piece, "sheet_file", MusicMaterial.MaterialType.SHEET, "Ноты")
            self._add_material(piece, "minus_file", MusicMaterial.MaterialType.MINUS, "Минусовка")
            self._add_material(piece, "plus_file", MusicMaterial.MaterialType.PLUS, "Плюсовка")
            self._add_material(piece, "video_file", MusicMaterial.MaterialType.VIDEO, "Видео исполнения")

            video_url = self.cleaned_data.get("video_url")
            if video_url:
                MusicMaterial.objects.create(
                    piece=piece,
                    type=MusicMaterial.MaterialType.VIDEO,
                    url=video_url,
                    description="Видео исполнения",
                )

        return piece

    def _add_material(self, piece, field_name, material_type, description):
        """Создаёт MusicMaterial из загруженного файла, если он был передан."""
        uploaded_file = self.cleaned_data.get(field_name)
        if uploaded_file:
            MusicMaterial.objects.create(
                piece=piece,
                type=material_type,
                file=uploaded_file,
                description=description,
            )

    @staticmethod
    def _get_or_create_ci(model, name):
        """Ищет объект по имени без учёта регистра (чтобы 'Вальс' и 'вальс'
        не создавались как два разных жанра), а при создании нового —
        сохраняет его в нижнем регистре для единообразия."""
        existing = model.objects.filter(name__iexact=name).first()
        if existing:
            return existing
        return model.objects.create(name=name.lower())


class ComposerForm(forms.ModelForm):
    class Meta:
        model = Composer
        fields = ["first_name", "last_name", "biography"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Имя"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Фамилия"}),
            "biography": forms.Textarea(attrs={"class": "form-control", "rows": 4, "placeholder": "Биография"}),
        }


class GenreForm(forms.ModelForm):
    class Meta:
        model = Genre
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название жанра"}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip().lower()


class InstrumentForm(forms.ModelForm):
    class Meta:
        model = Instrument
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Название инструмента"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Описание"}),
        }

    def clean_name(self):
        return self.cleaned_data["name"].strip().lower()


class MusicMaterialForm(forms.ModelForm):
    class Meta:
        model = MusicMaterial
        fields = ["type", "file", "url", "description", "is_public"]
        widgets = {
            "type": forms.Select(attrs={"class": "form-select"}),
            "file": forms.ClearableFileInput(attrs={"class": "form-control"}),
            "url": forms.URLInput(attrs={"class": "form-control", "placeholder": "https://..."}),
            "description": forms.TextInput(attrs={"class": "form-control", "placeholder": "Например: запись концерта 2024"}),
        }
