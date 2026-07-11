from django.template.loader import get_template
from xhtml2pdf import pisa
from io import BytesIO

def render_to_pdf(template_src, context_dict):
    template = get_template(template_src)
    html = template.render(context_dict)

    result = BytesIO()
    pisa.pisaDocument(BytesIO(html.encode("UTF-8")), result)

    return result.getvalue()
from django.core.mail import EmailMessage

def send_invoice_email(invoice, pdf_bytes):
    email = EmailMessage(
        subject=f'Invoice {invoice.invoice_number}',
        body='Please find your invoice attached.',
        to=[invoice.client.email]
    )

    email.attach(f'invoice_{invoice.id}.pdf', pdf_bytes, 'application/pdf')
    email.send()
pdf = render_to_pdf(...)
send_invoice_email(invoice, pdf)