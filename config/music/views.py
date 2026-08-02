from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView
from django.shortcuts import get_object_or_404

from .models import MusicalPiece, MusicMaterial


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
    fields = ["type", "file", "url", "description"]
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