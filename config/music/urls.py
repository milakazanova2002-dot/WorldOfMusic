from django.urls import path
from .views import (
    AboutView,
    ComposerCreateView,
    ComposerDeleteView,
    ComposerListView,
    ComposerUpdateView,
    GenreCreateView,
    GenreDeleteView,
    GenreListView,
    GenreUpdateView,
    InstrumentCreateView,
    InstrumentDeleteView,
    InstrumentListView,
    InstrumentUpdateView,
    MusicalPieceCreateView,
    MusicalPieceDeleteView,
    MusicalPieceDetailView,
    MusicalPieceListView,
    MusicalPieceUpdateView,
    MusicMaterialCreateView,
    MusicMaterialUpdateView,
    MusicMaterialDeleteView,
)

app_name = "music"

urlpatterns = [
    # Каталог произведений
    path("", MusicalPieceListView.as_view(), name="piece_list"),
    path("piece/<int:pk>/", MusicalPieceDetailView.as_view(), name="piece_detail"),
    path("piece/create/", MusicalPieceCreateView.as_view(), name="piece_create"),
    path("piece/<int:pk>/edit/", MusicalPieceUpdateView.as_view(), name="piece_edit"),
    path("piece/<int:pk>/delete/", MusicalPieceDeleteView.as_view(), name="piece_delete"),
    path("piece/<int:pk>/material/add/", MusicMaterialCreateView.as_view(), name="material_add"),
    path("material/<int:pk>/edit/", MusicMaterialUpdateView.as_view(), name="material_edit"),
    path("material/<int:pk>/delete/", MusicMaterialDeleteView.as_view(), name="material_delete"),

    # О сайте
    path("about/", AboutView.as_view(), name="about"),
]
