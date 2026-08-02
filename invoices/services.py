from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from .utils import render_to_pdf


def generate_invoice_pdf(invoice):
    return render_to_pdf(
        "invoices/invoice_pdf.html",
        {
            "invoice": invoice,
        },
    )


def send_invoice_email(invoice):
    pdf_bytes = generate_invoice_pdf(
        invoice
    )

    if pdf_bytes is None:
        raise ValueError(
            "The invoice PDF could not be generated."
        )

    subject = (
        f"Invoice {invoice.invoice_number} "
        f"from {invoice.user.company_name or invoice.user.username}"
    )

    body = render_to_string(
        "invoices/invoice_email.html",
        {
            "invoice": invoice,
        },
    )

    email = EmailMessage(
        subject=subject,
        body=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[
            invoice.client.email,
        ],
    )

    email.attach(
        f"{invoice.invoice_number}.pdf",
        pdf_bytes,
        "application/pdf",
    )

    return email.send(
        fail_silently=False,
    )