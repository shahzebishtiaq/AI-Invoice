from rest_framework import serializers

from clients.models import Client
from invoices.models import (
    Invoice,
    InvoiceItem,
)


class InvoiceItemSerializer(
    serializers.ModelSerializer
):
    line_total = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = InvoiceItem

        fields = [
            "id",
            "description",
            "quantity",
            "unit_price",
            "line_total",
        ]


class InvoiceSerializer(
    serializers.ModelSerializer
):
    items = InvoiceItemSerializer(
        many=True,
        required=False,
    )

    client_name = serializers.CharField(
        source="client.name",
        read_only=True,
    )

    class Meta:
        model = Invoice

        fields = [
            "id",
            "invoice_number",
            "client",
            "client_name",
            "issue_date",
            "due_date",
            "status",
            "notes",
            "subtotal",
            "tax_rate",
            "tax_amount",
            "total",
            "items",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "subtotal",
            "tax_amount",
            "total",
            "created_at",
            "updated_at",
        ]

    def validate_client(self, client):
        request = self.context.get(
            "request"
        )

        if (
            request
            and client.user_id != request.user.id
        ):
            raise serializers.ValidationError(
                "You cannot use another user's client."
            )

        return client

    def create(self, validated_data):
        items_data = validated_data.pop(
            "items",
            [],
        )

        request = self.context["request"]

        invoice = Invoice.objects.create(
            user=request.user,
            **validated_data,
        )

        for item_data in items_data:
            InvoiceItem.objects.create(
                invoice=invoice,
                **item_data,
            )

        invoice.calculate_totals()

        Invoice.objects.filter(
            pk=invoice.pk,
        ).update(
            subtotal=invoice.subtotal,
            tax_amount=invoice.tax_amount,
            total=invoice.total,
        )

        invoice.refresh_from_db()

        return invoice

    def update(self, instance, validated_data):
        items_data = validated_data.pop(
            "items",
            None,
        )

        for field, value in validated_data.items():
            setattr(
                instance,
                field,
                value,
            )

        instance.save()

        if items_data is not None:
            instance.items.all().delete()

            for item_data in items_data:
                InvoiceItem.objects.create(
                    invoice=instance,
                    **item_data,
                )

        instance.calculate_totals()

        Invoice.objects.filter(
            pk=instance.pk,
        ).update(
            subtotal=instance.subtotal,
            tax_amount=instance.tax_amount,
            total=instance.total,
        )

        instance.refresh_from_db()

        return instance
