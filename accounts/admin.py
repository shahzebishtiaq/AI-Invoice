from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "company_name",
        "is_staff",
        "is_active",
    )

    search_fields = (
        "username",
        "email",
        "company_name",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "Business information",
            {
                "fields": (
                    "company_name",
                    "phone_number",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Business information",
            {
                "fields": (
                    "email",
                    "company_name",
                    "phone_number",
                )
            },
        ),
    )