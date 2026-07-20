from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "plan",
        "status",
        "started_at",
        "expires_at",
    )

    list_filter = (
        "plan",
        "status",
    )

    search_fields = (
        "user__username",
        "user__email",
    )
