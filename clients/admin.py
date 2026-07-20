from django.contrib import admin

from .models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "company_name",
        "user",
        "created_at",
    )

    list_filter = (
        "created_at",
        "updated_at",
    )

    search_fields = (
        "name",
        "email",
        "company_name",
        "phone",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
