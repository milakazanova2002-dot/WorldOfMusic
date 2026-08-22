from django.contrib import admin

from .models import (
    Composer,
    Favorite,
    Genre,
    Instrument,
    MusicalPiece,
    MusicMaterial,
)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Composer)
class ComposerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name")
    search_fields = ("first_name", "last_name")


@admin.register(MusicalPiece)
class MusicalPieceAdmin(admin.ModelAdmin):
    list_display = ("title", "composer", "year_created")
    list_filter = ("genre", "instruments")
    search_fields = ("title", "composer__first_name", "composer__last_name")
    filter_horizontal = ("genre", "instruments")
    autocomplete_fields = ("composer",)


@admin.register(MusicMaterial)
class MusicMaterialAdmin(admin.ModelAdmin):
    list_display = ("piece", "type", "description", "is_public", "created_at")
    list_filter = ("type", "is_public")
    search_fields = ("piece__title", "description")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "piece", "created_at")
    search_fields = ("user__username", "piece__title")
