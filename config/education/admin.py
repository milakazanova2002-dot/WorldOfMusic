from django.contrib import admin

from .models import TeacherProfile, StudentProfile, Lesson, Subject, TeachingAssignment, Performance, PerformanceComment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")

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
        "assignment",
        "date",
        "instrument",
        "piece",
    )

    list_filter = (
        "date",
        "instrument",
    )


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "student", "subject", "is_active", "created_at")
    list_filter = ("subject", "is_active")


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("assignment", "piece", "score", "created_at")
    list_filter = ("score", "piece")


@admin.register(PerformanceComment)
class PerformanceCommentAdmin(admin.ModelAdmin):
    list_display = ("performance", "teacher", "created_at")
    list_filter = ("teacher",)
