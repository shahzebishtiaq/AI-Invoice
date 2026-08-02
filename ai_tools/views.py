from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from invoices.models import Invoice, InvoiceItem
from invoices.views import generate_invoice_number

from .forms import AIInvoiceForm
from .services import (
    AIInvoiceGenerationError,
    generate_invoice_items,
)

from subscriptions.services import (
    get_invoice_limit_message,
    user_can_create_invoice,
)
@login_required
@transaction.atomic
def generate_invoice_view(request):
    if not user_can_create_invoice(
        request.user
    ):
        messages.warning(
            request,
            get_invoice_limit_message(
                request.user
            ),
        )

        return redirect(
            "invoice_list"
        )
    if request.method == "POST":
        form = AIInvoiceForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            prompt = form.cleaned_data["prompt"]
            client = form.cleaned_data["client"]
            tax_rate = (
                form.cleaned_data["tax_rate"]
                or Decimal("0.00")
            )
            due_date = form.cleaned_data["due_date"]
            notes = form.cleaned_data["notes"]

            try:
                generated_items = generate_invoice_items(
                    prompt
                )

                invoice = Invoice.objects.create(
                    user=request.user,
                    client=client,
                    invoice_number=generate_invoice_number(
                        request.user
                    ),
                    issue_date=timezone.localdate(),
                    due_date=due_date,
                    tax_rate=tax_rate,
                    notes=notes,
                    status=Invoice.STATUS_DRAFT,
                )

                invoice_items = [
                    InvoiceItem(
                        invoice=invoice,
                        description=item["description"],
                        quantity=item["quantity"],
                        unit_price=item["unit_price"],
                    )
                    for item in generated_items
                ]

                InvoiceItem.objects.bulk_create(
                    invoice_items
                )

                invoice.calculate_totals()

                Invoice.objects.filter(
                    pk=invoice.pk,
                ).update(
                    subtotal=invoice.subtotal,
                    tax_amount=invoice.tax_amount,
                    total=invoice.total,
                )

                messages.success(
                    request,
                    "Your AI invoice was created successfully.",
                )

                return redirect(
                    "invoice_detail",
                    pk=invoice.pk,
                )

            except AIInvoiceGenerationError as exc:
                messages.error(
                    request,
                    str(exc),
                )

            except Exception:
                messages.error(
                    request,
                    "An unexpected error occurred while creating the invoice.",
                )
    else:
        form = AIInvoiceForm(
            user=request.user,
        )

    has_clients = request.user.clients.exists()

    return render(
        request,
        "ai_tools/generate_invoice.html",
        {
            "form": form,
            "has_clients": has_clients,
        },
    )
