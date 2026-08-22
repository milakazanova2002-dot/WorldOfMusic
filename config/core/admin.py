from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import Notification, SupportRequest

# Делаем панель администратора понятной с первого взгляда: понятные заголовки
# вместо стандартного "Django administration".
admin.site.site_header = "World Of Music — администрирование"
admin.site.site_title = "World Of Music"
admin.site.index_title = "Панель управления сайтом"


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "user", "status_badge", "is_resolved", "created_at")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("subject", "message", "email")
    list_editable = ("is_resolved",)  # можно отметить решённой прямо из списка, не открывая заявку
    readonly_fields = ("user", "created_at")
    ordering = ("is_resolved", "-created_at")  # нерешённые заявки — всегда сверху

    @admin.display(description="Статус")
    def status_badge(self, obj):
        if not obj.is_resolved:
            return mark_safe(
                '<span style="background:#dc3545;color:#fff;padding:4px 12px;'
                'border-radius:10px;font-size:11px;font-weight:700;">🔴 Новая</span>'
            )
        return mark_safe(
            '<span style="background:#198754;color:#fff;padding:4px 12px;'
            'border-radius:10px;font-size:11px;">✓ Решено</span>'
        )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("text", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("text", "user__username", "user__email")
    readonly_fields = ("created_at",)
