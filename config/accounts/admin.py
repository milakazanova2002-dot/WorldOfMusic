from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
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
        "is_approved",
        "is_staff",
        "date_joined",
    )

    list_filter = ("is_approved", "is_staff", "is_active")
    search_fields = ("username", "first_name", "last_name", "email", "phone")

    @admin.display(description="Имя Фамилия")
    def get_full_name(self, obj):
        return obj.get_full_name() or "—"
