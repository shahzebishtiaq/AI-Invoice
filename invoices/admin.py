from django.contrib import admin

from .models import Invoice, InvoiceItem


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 1


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "client",
        "user",
        "status",
        "total",
        "issue_date",
        "due_date",
    )

    list_filter = (
        "status",
        "issue_date",
        "due_date",
    )

    search_fields = (
        "invoice_number",
        "client__name",
        "client__email",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "subtotal",
        "tax_amount",
        "total",
        "created_at",
        "updated_at",
    )

    inlines = [
        InvoiceItemInline,
    ]


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = (
        "description",
        "invoice",
        "quantity",
        "unit_price",
        "line_total",
    )

    search_fields = (
        "description",
        "invoice__invoice_number",
    )
