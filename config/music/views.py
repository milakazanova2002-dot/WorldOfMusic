from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView
from django.shortcuts import get_object_or_404

from .models import Composer, Genre, Instrument, MusicalPiece, MusicMaterial


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
                # Одобренный педагог — доверенный участник общей библиотеки
                has_private_access = True
            elif hasattr(user, "student_profile"):
                # Ученик видит приватные материалы, только если реально
                # привязан к этому произведению (через урок или исполнение)
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


class MusicMaterialListView(ListView):
    model = MusicMaterial
    template_name = "music/material_list.html"
    context_object_name = "materials"

    def dispatch(self, request, *args, **kwargs):
        self.piece = get_object_or_404(MusicalPiece, id=kwargs["piece_id"])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return MusicMaterial.objects.filter(piece=self.piece)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["piece"] = self.piece
        return context


class MusicMaterialCreateView(CreateView):
    model = MusicMaterial
    fields = ["type", "file", "url", "description", "is_public"]
    template_name = "music/material_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.piece = get_object_or_404(MusicalPiece, id=kwargs["piece_id"])
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.piece = self.piece
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("material_list", kwargs={"piece_id": self.piece.id})


class MusicMaterialDeleteView(DeleteView):
    model = MusicMaterial
    template_name = "music/material_confirm_delete.html"

    def get_success_url(self):
        piece_id = self.object.piece.id
        return reverse_lazy("material_list", kwargs={"piece_id": piece_id})