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
)

app_name = "music"

urlpatterns = [
    # Каталог произведений
    path("", MusicalPieceListView.as_view(), name="piece_list"),
    path("piece/<int:pk>/", MusicalPieceDetailView.as_view(), name="piece_detail"),
    path("piece/create/", MusicalPieceCreateView.as_view(), name="piece_create"),
    path("piece/<int:pk>/edit/", MusicalPieceUpdateView.as_view(), name="piece_edit"),
    path("piece/<int:pk>/delete/", MusicalPieceDeleteView.as_view(), name="piece_delete"),

    # О сайте
    path("about/", AboutView.as_view(), name="about"),
]
