from django.urls import reverse_lazy
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from .models import Composer, Genre, Instrument, MusicalPiece, MusicMaterial
from .forms import MusicalPieceForm, MusicMaterialForm


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
            qs = qs.filter(title__icontains=query)

        genre_id = self.request.GET.get("genre")
        if genre_id:
            qs = qs.filter(genre__id=genre_id)

        instrument_id = self.request.GET.get("instrument")
        if instrument_id:
            qs = qs.filter(instruments__id=instrument_id)

        return qs.order_by("title")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["genres"] = Genre.objects.all()
        context["instruments"] = Instrument.objects.all()
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


class ComposerListView(LoginRequiredMixin, ListView):
    model = Composer
    template_name = "music/composer_list.html"
    context_object_name = "composers"


class ComposerCreateView(LoginRequiredMixin, CreateView):
    model = Composer
    fields = ["first_name", "last_name", "biography"]
    template_name = "music/composer_form.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор добавлен!")
        return super().form_valid(form)


class ComposerUpdateView(LoginRequiredMixin, UpdateView):
    model = Composer
    fields = ["first_name", "last_name", "biography"]
    template_name = "music/composer_form.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор обновлён!")
        return super().form_valid(form)


class ComposerDeleteView(LoginRequiredMixin, DeleteView):
    model = Composer
    template_name = "music/composer_confirm_delete.html"
    success_url = reverse_lazy("music:composer_list")

    def form_valid(self, form):
        messages.success(self.request, "Композитор удалён.")
        return super().form_valid(form)


class GenreListView(LoginRequiredMixin, ListView):
    model = Genre
    template_name = "music/genre_list.html"
    context_object_name = "genres"


class GenreCreateView(LoginRequiredMixin, CreateView):
    model = Genre
    fields = ["name"]
    template_name = "music/genre_form.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр добавлен!")
        return super().form_valid(form)


class GenreUpdateView(LoginRequiredMixin, UpdateView):
    model = Genre
    fields = ["name"]
    template_name = "music/genre_form.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр обновлён!")
        return super().form_valid(form)


class GenreDeleteView(LoginRequiredMixin, DeleteView):
    model = Genre
    template_name = "music/genre_confirm_delete.html"
    success_url = reverse_lazy("music:genre_list")

    def form_valid(self, form):
        messages.success(self.request, "Жанр удалён.")
        return super().form_valid(form)


class InstrumentListView(LoginRequiredMixin, ListView):
    model = Instrument
    template_name = "music/instrument_list.html"
    context_object_name = "instruments"


class InstrumentCreateView(LoginRequiredMixin, CreateView):
    model = Instrument
    fields = ["name", "description"]
    template_name = "music/instrument_form.html"
    success_url = reverse_lazy("music:instrument_list")

    def form_valid(self, form):
        messages.success(self.request, "Инструмент добавлен!")
        return super().form_valid(form)


class InstrumentUpdateView(LoginRequiredMixin, UpdateView):
    model = Instrument
    fields = ["name", "description"]
    template_name = "music/instrument_form.html"
    success_url = reverse_lazy("music:instrument_list")

    def form_valid(self, form):
        messages.success(self.request, "Инструмент обновлён!")
        return super().form_valid(form)


class InstrumentDeleteView(LoginRequiredMixin, DeleteView):
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
        context["total_pieces"] = MusicalPiece.objects.count()
        context["total_composers"] = Composer.objects.count()
        context["total_genres"] = Genre.objects.count()
        return context
