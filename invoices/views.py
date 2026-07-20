from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
import logging
logger = logging.getLogger(__name__)
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone

from .forms import (
    InvoiceForm,
    InvoiceItemFormSet,
)
from .models import Invoice
from .services import (
    generate_invoice_pdf,
    send_invoice_email,
)

from subscriptions.services import (
    get_invoice_limit_message,
    user_can_create_invoice,
)
def generate_invoice_number(user):
    prefix = timezone.localdate().strftime(
        "%Y%m"
    )

    latest_invoice = Invoice.objects.filter(
        user=user,
        invoice_number__startswith=f"INV-{prefix}",
    ).order_by(
        "-id"
    ).first()

    if latest_invoice:
        try:
            last_number = int(
                latest_invoice.invoice_number.split(
                    "-"
                )[-1]
            )
        except (ValueError, IndexError):
            last_number = 0
    else:
        last_number = 0

    next_number = last_number + 1

    return f"INV-{prefix}-{next_number:04d}"


@login_required
def invoice_list(request):
    query = request.GET.get(
        "q",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

    invoices = Invoice.objects.filter(
        user=request.user,
    ).select_related(
        "client"
    )

    if query:
        invoices = invoices.filter(
            Q(invoice_number__icontains=query)
            | Q(client__name__icontains=query)
            | Q(client__email__icontains=query)
        )

    if status:
        invoices = invoices.filter(
            status=status,
        )

    return render(
        request,
        "invoices/invoice_list.html",
        {
            "invoices": invoices,
            "query": query,
            "selected_status": status,
            "status_choices": Invoice.STATUS_CHOICES,
        },
    )


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "client",
            "user",
        ).prefetch_related(
            "items"
        ),
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        "invoices/invoice_detail.html",
        {
            "invoice": invoice,
        },
    )


@login_required
@transaction.atomic
def invoice_create(request):
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
    invoice = Invoice(
        user=request.user,
        invoice_number=generate_invoice_number(
            request.user
        ),
    )

    if request.method == "POST":
        form = InvoiceForm(
            request.POST,
            instance=invoice,
            user=request.user,
        )

        formset = InvoiceItemFormSet(
            request.POST,
            instance=invoice,
        )

        if form.is_valid() and formset.is_valid():
            invoice = form.save(
                commit=False
            )

            invoice.user = request.user
            invoice.save()

            formset.instance = invoice
            formset.save()

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
                "Invoice created successfully.",
            )

            return redirect(
                "invoice_detail",
                pk=invoice.pk,
            )
    else:
        form = InvoiceForm(
            instance=invoice,
            user=request.user,
        )

        formset = InvoiceItemFormSet(
            instance=invoice,
        )

    return render(
        request,
        "invoices/invoice_form.html",
        {
            "form": form,
            "formset": formset,
            "page_title": "Create invoice",
            "button_text": "Create invoice",
        },
    )


@login_required
@transaction.atomic
def invoice_update(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = InvoiceForm(
            request.POST,
            instance=invoice,
            user=request.user,
        )

        formset = InvoiceItemFormSet(
            request.POST,
            instance=invoice,
        )

        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.save()

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
                "Invoice updated successfully.",
            )

            return redirect(
                "invoice_detail",
                pk=invoice.pk,
            )
    else:
        form = InvoiceForm(
            instance=invoice,
            user=request.user,
        )

        formset = InvoiceItemFormSet(
            instance=invoice,
        )

    return render(
        request,
        "invoices/invoice_form.html",
        {
            "form": form,
            "formset": formset,
            "invoice": invoice,
            "page_title": "Edit invoice",
            "button_text": "Save changes",
        },
    )


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        invoice_number = invoice.invoice_number
        invoice.delete()

        messages.success(
            request,
            f"Invoice {invoice_number} was deleted.",
        )

        return redirect(
            "invoice_list"
        )

    return render(
        request,
        "invoices/invoice_confirm_delete.html",
        {
            "invoice": invoice,
        },
    )


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "client",
            "user",
        ).prefetch_related(
            "items"
        ),
        pk=pk,
        user=request.user,
    )

    pdf_bytes = generate_invoice_pdf(
        invoice
    )

    if pdf_bytes is None:
        return HttpResponse(
            "PDF generation failed.",
            status=500,
        )

    response = HttpResponse(
        pdf_bytes,
        content_type="application/pdf",
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; filename="{invoice.invoice_number}.pdf"'
    )

    return response


@login_required
def invoice_send_email(request, pk):
    invoice = get_object_or_404(
        Invoice.objects.select_related(
            "client",
            "user",
        ).prefetch_related(
            "items"
        ),
        pk=pk,
        user=request.user,
    )

    if request.method != "POST":
        return redirect(
            "invoice_detail",
            pk=invoice.pk,
        )

    try:
        send_invoice_email(
            invoice
        )

        if invoice.status == Invoice.STATUS_DRAFT:
            invoice.status = Invoice.STATUS_SENT

            Invoice.objects.filter(
                pk=invoice.pk,
            ).update(
                status=Invoice.STATUS_SENT,
            )

        messages.success(
            request,
            f"Invoice sent to {invoice.client.email}.",
        )

    except Exception:
        logger.exception(
            "Invoice email delivery failed for invoice %s.",
            invoice.pk,
        )

        messages.error(
            request,
            "The invoice email could not be sent. "
            "Please check your email settings and try again.",
        )

    return redirect(
        "invoice_detail",
        pk=invoice.pk,
    )


@login_required
def invoice_mark_paid(request, pk):
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        invoice.status = Invoice.STATUS_PAID

        Invoice.objects.filter(
            pk=invoice.pk,
        ).update(
            status=Invoice.STATUS_PAID,
        )

        messages.success(
            request,
            f"Invoice {invoice.invoice_number} marked as paid.",
        )

    return redirect(
        "invoice_detail",
        pk=invoice.pk,
    )
