from django.contrib import admin

from .models import Notification, SupportRequest

# Делаем панель администратора понятной с первого взгляда: понятные заголовки
# вместо стандартного "Django administration".
admin.site.site_header = "World Of Music — администрирование"
admin.site.site_title = "World Of Music"
admin.site.index_title = "Панель управления сайтом"


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    list_display = ("subject", "email", "user", "is_resolved", "created_at")
    list_filter = ("is_resolved", "created_at")
    search_fields = ("subject", "message", "email")
    list_editable = ("is_resolved",)  # можно отметить решённой прямо из списка, не открывая заявку
    readonly_fields = ("user", "created_at")
    ordering = ("is_resolved", "-created_at")  # нерешённые заявки — всегда сверху


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("text", "user", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("text", "user__username", "user__email")
    readonly_fields = ("created_at",)
