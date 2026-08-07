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
                    "email_verified",
                    "is_approved",
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
                    "email_verified",
                    "is_approved",
                    "avatar",
                )
            }
        ),
    )

    list_display = (
        "username",
        "email",
        "is_approved",
        "is_staff",
    )

    list_filter = ("is_approved",)
