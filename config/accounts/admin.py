from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Case, IntegerField, Value, When
from django.utils.safestring import mark_safe
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Дополнительно",
            {
                "fields": (
                    "patronymic",
                    "phone",
                    "email_verified",
                    "is_approved",
                    "email_notifications",
                    "avatar",
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Дополнительно",
            {
                "fields": (
                    "patronymic",
                    "phone",
                    "email_verified",
                    "is_approved",
                    "avatar",
                )
            }
        ),
    )

    list_display = (
        "username",
        "get_full_name",
        "email",
        "status_badge",
        "is_staff",
        "date_joined",
    )

    list_filter = ("is_approved", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "phone")

    @admin.display(description="Имя Фамилия")
    def get_full_name(self, obj):
        return obj.get_full_name() or "—"

    @admin.display(description="Статус")
    def status_badge(self, obj):
        # Явно выделяем самое важное: педагог, ожидающий одобрения —
        # это единственный статус, требующий немедленного внимания администратора.
        if hasattr(obj, "teacher_profile"):
            if not obj.is_approved:
                return mark_safe(
                    '<span style="background:#dc3545;color:#fff;padding:4px 12px;'
                    'border-radius:10px;font-size:11px;font-weight:700;">🔴 Ждёт одобрения</span>'
                )
            return mark_safe(
                '<span style="background:#198754;color:#fff;padding:4px 12px;'
                'border-radius:10px;font-size:11px;">Педагог</span>'
            )
        if hasattr(obj, "student_profile"):
            return mark_safe(
                '<span style="background:#6c757d;color:#fff;padding:4px 12px;'
                'border-radius:10px;font-size:11px;">Ученик</span>'
            )
        return mark_safe(
            '<span style="background:#adb5bd;color:#fff;padding:4px 12px;'
            'border-radius:10px;font-size:11px;">Гость</span>'
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("teacher_profile", "student_profile")
        # Неодобренные педагоги — всегда первыми в списке, чтобы их
        # не приходилось выискивать среди остальных пользователей.
        return qs.annotate(
            _pending_priority=Case(
                When(teacher_profile__isnull=False, is_approved=False, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            )
        ).order_by("_pending_priority", "-date_joined")
