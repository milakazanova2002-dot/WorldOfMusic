from django.contrib import admin

from .models import TeacherProfile, StudentProfile, Lesson, Subject, TeachingAssignment, Performance, PerformanceComment


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "experience_years")
    search_fields = ("user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("instruments", "subjects")
    autocomplete_fields = ("user",)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "age", "level")
    list_filter = ("level",)
    search_fields = ("user__username", "user__first_name", "user__last_name")
    filter_horizontal = ("instruments",)
    autocomplete_fields = ("user",)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("student", "assignment", "date", "instrument", "piece")
    list_filter = ("date", "instrument")
    search_fields = ("student__user__username", "student__user__last_name")
    date_hierarchy = "date"  # удобная навигация по датам сверху списка


@admin.register(TeachingAssignment)
class TeachingAssignmentAdmin(admin.ModelAdmin):
    list_display = ("teacher", "student", "subject", "is_active", "created_at")
    list_filter = ("subject", "is_active")
    search_fields = ("teacher__user__last_name", "student__user__last_name")


@admin.register(Performance)
class PerformanceAdmin(admin.ModelAdmin):
    list_display = ("assignment", "piece", "score", "created_at")
    list_filter = ("score", "piece")
    search_fields = ("assignment__student__user__last_name", "piece__title")
    date_hierarchy = "created_at"


@admin.register(PerformanceComment)
class PerformanceCommentAdmin(admin.ModelAdmin):
    list_display = ("performance", "teacher", "created_at")
    list_filter = ("teacher",)
    search_fields = ("text",)
