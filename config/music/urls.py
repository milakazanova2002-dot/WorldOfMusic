from django.urls import path
from .views import (
    MusicMaterialListView,
    MusicMaterialCreateView,
    MusicMaterialDeleteView,
)

urlpatterns = [
    path("piece/<int:piece_id>/materials/", MusicMaterialListView.as_view(), name="material_list"),
    path("piece/<int:piece_id>/materials/add/", MusicMaterialCreateView.as_view(), name="material_add"),
    path("material/<int:pk>/delete/", MusicMaterialDeleteView.as_view(), name="material_delete"),
]
