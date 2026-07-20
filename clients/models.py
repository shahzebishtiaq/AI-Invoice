from django.conf import settings
from django.db import models


class Client(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
    )

    name = models.CharField(
        max_length=255,
    )

    email = models.EmailField()

    phone = models.CharField(
        max_length=30,
        blank=True,
    )

    address = models.TextField(
        blank=True,
    )

    company_name = models.CharField(
        max_length=255,
        blank=True,
    )

    notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = [
            "-created_at",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "user",
                    "email",
                ],
                name="unique_client_email_per_user",
            ),
        ]

    def __str__(self):
        return self.name
