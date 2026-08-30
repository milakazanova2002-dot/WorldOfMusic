from django.urls import reverse_lazy
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.http import JsonResponse
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
    View,
)
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Composer, Favorite, Genre, Instrument, MusicalPiece, MusicMaterial
from .forms import GenreForm, InstrumentForm, MusicalPieceForm, MusicMaterialForm


class MusicalPieceListView(ListView):
    """Публичный каталог произведений — доступен без авторизации."""
    model = MusicalPiece
    template_name = "music/piece_list.html"
    context_object_name = "pieces"
    paginate_by = 20

    def get_queryset(self):
        qs = MusicalPiece.objects.select_related("composer").prefetch_related("genre", "instruments")

        query = self.request.GET.get("q")
        if query:
            qs = qs.filter(
                Q(title__icontains=query)
                | Q(composer__first_name__icontains=query)
                | Q(composer__last_name__icontains=query)
            )

        genre_id = self.request.GET.get("genre")
        if genre_id:
            qs = qs.filter(genre__id=genre_id)

        instrument_id = self.request.GET.get("instrument")
        if instrument_id:
            qs = qs.filter(instruments__id=instrument_id)

        return qs.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Справочники меняются редко (раз в несколько дней, когда педагог
        # добавит новый жанр/инструмент), а достаются из базы на каждой
        # загрузке каталога — кешируем на 5 минут.
        genres = cache.get("all_genres")
        if genres is None:
            genres = list(Genre.objects.all())
            cache.set("all_genres", genres, 60 * 5)

        instruments = cache.get("all_instruments")
        if instruments is None:
            instruments = list(Instrument.objects.all())
            cache.set("all_instruments", instruments, 60 * 5)

        context["genres"] = genres
        context["instruments"] = instruments
        return context


class MusicalPieceDetailView(DetailView):
    """Публичная страница произведения — доступна без авторизации."""
    model = MusicalPiece
    template_name = "music/piece_detail.html"
    context_object_name = "piece"

    def get_queryset(self):
        return MusicalPiece.objects.select_related("composer").prefetch_related(
            "genre", "instruments", "materials"
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        piece = self.object
        user = self.request.user

        has_private_access = False

        if user.is_authenticated:
            if user.is_staff or user.is_superuser:
                has_private_access = True
            elif hasattr(user, "teacher_profile") and user.is_approved:
                has_private_access = True
            elif hasattr(user, "student_profile"):
                student = user.student_profile
                from education.models import Lesson, Performance
                has_private_access = (
                    Lesson.objects.filter(student=student, piece=piece).exists()
                    or Performance.objects.filter(
                        assignment__student=student, piece=piece
                    ).exists()
                )

        context["has_private_access"] = has_private_access

        if has_private_access:
            context["materials"] = piece.materials.all()
        else:
            context["materials"] = piece.materials.filter(is_public=True)

        playable_types = [MusicMaterial.MaterialType.VIDEO, MusicMaterial.MaterialType.AUDIO,
                           MusicMaterial.MaterialType.PLUS, MusicMaterial.MaterialType.MINUS]
        context["has_playable_media"] = any(
            m.file and m.type in playable_types for m in context["materials"]
        )

        if user.is_authenticated:
            context["is_favorited"] = Favorite.objects.filter(user=user, piece=piece).exists()

        return context


# ---------- Create / Update / Delete ----------


class MusicalPieceCreateView(LoginRequiredMixin, CreateView):
    """Создание произведения — только для педагогов."""
    model = MusicalPiece
    form_class = MusicalPieceForm
    template_name = "music/piece_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут добавлять произведения.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Произведение успешно создано!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:piece_detail", kwargs={"pk": self.object.pk})


class MusicalPieceUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование произведения — только для педагогов."""
    model = MusicalPiece
    form_class = MusicalPieceForm
    template_name = "music/piece_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут редактировать произведения.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return MusicalPiece.objects.all()

    def form_valid(self, form):
        messages.success(self.request, "Произведение успешно обновлено!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:piece_detail", kwargs={"pk": self.object.pk})


class MusicalPieceDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление произведения."""
    model = MusicalPiece
    template_name = "music/piece_confirm_delete.html"
    success_url = reverse_lazy("music:piece_list")

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут удалять произведения.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Произведение удалено.")
        return super().form_valid(form)


class MusicMaterialCreateView(LoginRequiredMixin, CreateView):
    """Добавление материала (нот, аудио, видео) к уже существующему произведению."""
    model = MusicMaterial
    form_class = MusicMaterialForm
    template_name = "music/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут добавлять материалы.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["piece"] = get_object_or_404(MusicalPiece, pk=self.kwargs["pk"])
        return context

    def form_valid(self, form):
        form.instance.piece = get_object_or_404(MusicalPiece, pk=self.kwargs["pk"])
        messages.success(self.request, "Материал добавлен!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:piece_detail", kwargs={"pk": self.kwargs["pk"]})


class MusicMaterialUpdateView(LoginRequiredMixin, UpdateView):
    """Редактирование материала, привязанного к произведению."""
    model = MusicMaterial
    form_class = MusicMaterialForm
    template_name = "music/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут редактировать материалы.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["piece"] = self.object.piece
        return context

    def form_valid(self, form):
        messages.success(self.request, "Материал обновлён!")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:piece_detail", kwargs={"pk": self.object.piece.pk})


class MusicMaterialDeleteView(LoginRequiredMixin, DeleteView):
    """Удаление материала, привязанного к произведению."""
    model = MusicMaterial
    template_name = "music/material_confirm_delete.html"

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Только педагоги могут удалять материалы.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, "Материал удалён.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("music:piece_detail", kwargs={"pk": self.object.piece.pk})


# ---------- Справочники ----------


class TeacherOnlyMixin:
    """Разрешает доступ только педагогам — используется в CRUD справочников."""

    def dispatch(self, request, *args, **kwargs):
        if not hasattr(request.user, "teacher_profile"):
            messages.error(request, "Эта страница доступна только педагогам.")
            return redirect("home")
        return super().dispatch(request, *args, **kwargs)


class InstrumentDetailView(DetailView):
    """Публичная страница инструмента: какие произведения под него написаны
    и какие ученики их исполняли."""
    model = Instrument
    template_name = "music/instrument_detail.html"
    context_object_name = "instrument"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from education.models import Performance

        context["pieces"] = MusicalPiece.objects.filter(instruments=self.object).select_related("composer")
        context["performances"] = (
            Performance.objects.filter(piece__instruments=self.object)
            .select_related("assignment__student__user", "piece")
            .distinct()
        )
        return context


class GenreDetailView(DetailView):
    """Публичная страница жанра: какие произведения к нему относятся
    и какие ученики их исполняли."""
    model = Genre
    template_name = "music/genre_detail.html"
    context_object_name = "genre"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from education.models import Performance

        context["pieces"] = MusicalPiece.objects.filter(genre=self.object).select_related("composer")
        context["performances"] = (
            Performance.objects.filter(piece__genre=self.object)
            .select_related("assignment__student__user", "piece")
            .distinct()
        )
        return context


class ComposerDetailView(DetailView):
    """Публичная страница композитора: его произведения и кто их исполнял."""
    model = Composer
    template_name = "music/composer_detail.html"
    context_object_name = "composer"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from education.models import Performance

        context["pieces"] = MusicalPiece.objects.filter(composer=self.object)
        context["performances"] = (
            Performance.objects.filter(piece__composer=self.object)
            .select_related("assignment__student__user", "piece")
            .distinct()
        )
        return context


class ComposerListView(TeacherOnlyMixin, LoginRequiredMixin, ListView):
    model = Composer
    template_name = "music/composer_list.html"
    context_object_name = "composers"


class ComposerCreateView(TeacherOnlyMixin, LoginRequiredMixin, CreateView):
    model = Composer
    fields = ["first_name", "last_name", "biography"]
    template_name = "music/composer_form.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор добавлен!")
        return super().form_valid(form)


class ComposerUpdateView(TeacherOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Composer
    fields = ["first_name", "last_name", "biography"]
    template_name = "music/composer_form.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор обновлён!")
        return super().form_valid(form)


class ComposerDeleteView(TeacherOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Composer
    template_name = "music/composer_confirm_delete.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор удалён.")
        return super().form_valid(form)


class GenreListView(TeacherOnlyMixin, LoginRequiredMixin, ListView):
    model = Genre
    template_name = "music/genre_list.html"
    context_object_name = "genres"


class GenreCreateView(TeacherOnlyMixin, LoginRequiredMixin, CreateView):
    model = Genre
    form_class = GenreForm
    template_name = "music/genre_form.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр добавлен!")
        return super().form_valid(form)


class GenreUpdateView(TeacherOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Genre
    form_class = GenreForm
    template_name = "music/genre_form.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр обновлён!")
        return super().form_valid(form)


class GenreDeleteView(TeacherOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Genre
    template_name = "music/genre_confirm_delete.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр удалён.")
        return super().form_valid(form)


class InstrumentListView(TeacherOnlyMixin, LoginRequiredMixin, ListView):
    model = Instrument
    template_name = "music/instrument_list.html"
    context_object_name = "instruments"


class InstrumentCreateView(TeacherOnlyMixin, LoginRequiredMixin, CreateView):
    model = Instrument
    form_class = InstrumentForm
    template_name = "music/instrument_form.html"
    success_url = reverse_lazy("music:instrument_list")

    def form_valid(self, form):
        messages.success(self.request, "Инструмент добавлен!")
        return super().form_valid(form)


class InstrumentUpdateView(TeacherOnlyMixin, LoginRequiredMixin, UpdateView):
    model = Instrument
    form_class = InstrumentForm
    template_name = "music/instrument_form.html"
    success_url = reverse_lazy("music:instrument_list")

    def form_valid(self, form):
        messages.success(self.request, "Инструмент обновлён!")
        return super().form_valid(form)


class InstrumentDeleteView(TeacherOnlyMixin, LoginRequiredMixin, DeleteView):
    model = Instrument
    template_name = "music/instrument_confirm_delete.html"
    success_url = reverse_lazy("music:instrument_list")

    def form_valid(self, form):
        messages.success(self.request, "Инструмент удалён.")
        return super().form_valid(form)


# ---------- О сайте ----------


class AboutView(ListView):
    """Публичная страница «О сайте»."""
    model = MusicalPiece
    template_name = "core/about.html"
    paginate_by = 10

    def get_queryset(self):
        return MusicalPiece.objects.order_by("-id")[:6]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # COUNT() по целым таблицам — не бесплатная операция, а меняется
        # редко (на 1-2 в течение дня), поэтому кешируем на 10 минут.
        stats = cache.get("about_stats")
        if stats is None:
            stats = {
                "total_pieces": MusicalPiece.objects.count(),
                "total_composers": Composer.objects.count(),
                "total_genres": Genre.objects.count(),
            }
            cache.set("about_stats", stats, 60 * 10)

        context.update(stats)
        return context


# ---------- Избранное ----------


class FavoriteListView(LoginRequiredMixin, ListView):
    """Список избранных произведений текущего пользователя (педагога или ученика).
    В плеере показываются только публичные материалы — полная проверка прав
    (как на странице произведения) для целого списка была бы слишком тяжёлой."""
    template_name = "music/favorite_list.html"
    context_object_name = "pieces"

    def get_queryset(self):
        piece_ids = Favorite.objects.filter(user=self.request.user).values_list("piece_id", flat=True)
        public_materials = MusicMaterial.objects.filter(is_public=True)
        return (
            MusicalPiece.objects.filter(id__in=piece_ids)
            .select_related("composer")
            .prefetch_related("genre", Prefetch("materials", queryset=public_materials))
        )


class FavoriteToggleView(LoginRequiredMixin, View):
    """Добавляет/убирает произведение из избранного и возвращает туда, откуда пришли."""

    def post(self, request, pk):
        piece = get_object_or_404(MusicalPiece, pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, piece=piece)

        if not created:
            favorite.delete()
            messages.info(request, "Убрано из избранного.")
        else:
            messages.success(request, "Добавлено в избранное!")

        next_url = request.POST.get("next") or reverse_lazy("music:piece_detail", kwargs={"pk": pk})
        return redirect(next_url)


@login_required
def composer_autocomplete(request):
    """Подсказки при вводе имени композитора — как в поисковике: печатаешь,
    снизу подтягиваются похожие уже существующие композиторы, можно кликнуть
    и подставить вместо того, чтобы печатать заново (и случайно создать дубль)."""
    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        return JsonResponse({"results": []})

    composers = Composer.objects.filter(
        Q(first_name__icontains=query) | Q(last_name__icontains=query)
    )[:8]

    results = [
        {"id": c.pk, "name": f"{c.first_name} {c.last_name}".strip()}
        for c in composers
    ]
    return JsonResponse({"results": results})