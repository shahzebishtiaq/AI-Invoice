from django.conf import settings
from django.db import models
from django.utils import timezone


class Subscription(models.Model):
    PLAN_FREE = "free"
    PLAN_PRO = "pro"

    PLAN_CHOICES = [
        (PLAN_FREE, "Free"),
        (PLAN_PRO, "Pro"),
    ]

    STATUS_ACTIVE = "active"
    STATUS_PAST_DUE = "past_due"
    STATUS_CANCELLED = "cancelled"
    STATUS_EXPIRED = "expired"

    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAST_DUE, "Past due"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_EXPIRED, "Expired"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="subscription",
    )

    plan = models.CharField(
        max_length=20,
        choices=PLAN_CHOICES,
        default=PLAN_FREE,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
    )

    started_at = models.DateTimeField(
        default=timezone.now,
    )

    expires_at = models.DateTimeField(
        null=True,
        blank=True,
    )
    stripe_customer_id = models.CharField(
        max_length=255,
        blank=True,
    )

    stripe_subscription_id = models.CharField(
        max_length=255,
        blank=True,
    )

    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.get_plan_display()}"

    @property
    def is_active(self):
        if self.status != self.STATUS_ACTIVE:
            return False

        if self.expires_at and self.expires_at < timezone.now():
            return False

        return True

    @property
    def invoice_limit(self):
        if self.plan == self.PLAN_PRO and self.is_active:
            return None

        return 5

    def can_create_invoice(self):
        limit = self.invoice_limit

        if limit is None:
            return True

        return self.user.invoices.count() < limit