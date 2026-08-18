from django.urls import path
from .views import (
    AboutView,
    ComposerCreateView,
    ComposerDeleteView,
    ComposerListView,
    ComposerUpdateView,
    FavoriteListView,
    FavoriteToggleView,
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

    # Избранное
    path("favorites/", FavoriteListView.as_view(), name="favorite_list"),
    path("piece/<int:pk>/favorite/", FavoriteToggleView.as_view(), name="favorite_toggle"),

    # Композиторы
    path("composers/", ComposerListView.as_view(), name="composer_list"),
    path("composers/create/", ComposerCreateView.as_view(), name="composer_create"),
    path("composers/<int:pk>/edit/", ComposerUpdateView.as_view(), name="composer_edit"),
    path("composers/<int:pk>/delete/", ComposerDeleteView.as_view(), name="composer_delete"),

    # Жанры
    path("genres/", GenreListView.as_view(), name="genre_list"),
    path("genres/create/", GenreCreateView.as_view(), name="genre_create"),
    path("genres/<int:pk>/edit/", GenreUpdateView.as_view(), name="genre_edit"),
    path("genres/<int:pk>/delete/", GenreDeleteView.as_view(), name="genre_delete"),

    # Инструменты
    path("instruments/", InstrumentListView.as_view(), name="instrument_list"),
    path("instruments/create/", InstrumentCreateView.as_view(), name="instrument_create"),
    path("instruments/<int:pk>/edit/", InstrumentUpdateView.as_view(), name="instrument_edit"),
    path("instruments/<int:pk>/delete/", InstrumentDeleteView.as_view(), name="instrument_delete"),

    # О сайте
    path("about/", AboutView.as_view(), name="about"),
]
