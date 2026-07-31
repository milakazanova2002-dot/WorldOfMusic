from django.contrib import admin

from .models import (
    Instrument,
    Genre,
    Composer,
    MusicalPiece,
)


@admin.register(Instrument)
class InstrumentAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = (
        "name",
    )


@admin.register(Composer)
class ComposerAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
    )


@admin.register(MusicalPiece)
class MusicalPieceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "composer",
    )

    filter_horizontal = (
        "genre",
        "instruments",
    )