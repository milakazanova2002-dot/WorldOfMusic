from django.contrib import admin

from .models import TeacherProfile, StudentProfile, Lesson


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "experience_years",
    )

    filter_horizontal = (
        "instruments",
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "teacher",
        "age",
        "level",
    )

    filter_horizontal = (
        "instruments",
    )


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "teacher",
        "date",
        "instrument",
        "piece",
    )

    list_filter = (
        "date",
        "instrument",
    )