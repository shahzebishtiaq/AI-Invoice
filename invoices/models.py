from decimal import Decimal

from django.conf import settings
from django.db import models


class Invoice(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    STATUS_PAID = "paid"
    STATUS_OVERDUE = "overdue"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SENT, "Sent"),
        (STATUS_PAID, "Paid"),
        (STATUS_OVERDUE, "Overdue"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="invoices",
    )

    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="invoices",
    )

    invoice_number = models.CharField(
        max_length=100,

    )

    issue_date = models.DateField()

    due_date = models.DateField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    notes = models.TextField(
        blank=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Enter a percentage, for example 10 for 10%.",
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
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
                    "invoice_number",
                ],
                name="unique_invoice_number_per_user",
            ),
        ]

    def __str__(self):
        return self.invoice_number

    def calculate_totals(self):
        subtotal = sum(
            (
                item.get_total()
                for item in self.items.all()
            ),
            Decimal("0.00"),
        )

        tax_amount = (
            subtotal
            * self.tax_rate
            / Decimal("100")
        )

        total = subtotal + tax_amount

        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total = total

        return total

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.pk:
            calculated_total = self.calculate_totals()

            Invoice.objects.filter(
                pk=self.pk,
            ).update(
                subtotal=self.subtotal,
                tax_amount=self.tax_amount,
                total=calculated_total,
            )


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="items",
    )

    description = models.CharField(
        max_length=500,
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("1.00"),
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = [
            "id",
        ]

    def __str__(self):
        return self.description

    def get_total(self):
        return self.quantity * self.unit_price

    @property
    def line_total(self):
        return self.get_total()