from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    CURRENCY_CHOICES = [
        ("USD", "USD — US Dollar"),
        ("EUR", "EUR — Euro"),
        ("GBP", "GBP — British Pound"),
        ("CAD", "CAD — Canadian Dollar"),
        ("AUD", "AUD — Australian Dollar"),
        ("PKR", "PKR — Pakistani Rupee"),
        ("INR", "INR — Indian Rupee"),
        ("AED", "AED — UAE Dirham"),
    ]

    email = models.EmailField(
        unique=True,
    )

    company_name = models.CharField(
        max_length=255,
        blank=True,
    )

    phone_number = models.CharField(
        max_length=30,
        blank=True,
    )

    company_address = models.TextField(
        blank=True,
    )

    company_logo = models.ImageField(
        upload_to="company_logos/",
        blank=True,
        null=True,
    )

    default_currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="USD",
    )

    default_tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def __str__(self):
        return self.username

    @property
    def display_company_name(self):
        return self.company_name or self.get_full_name() or self.username