from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from .models import Invoice
from .utils import render_to_pdf


def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoices/invoice_list.html', {'invoices': invoices})


def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoices/invoice_detail.html', {'invoice': invoice})

def invoice_pdf(request, pk):
    invoice = Invoice.objects.get(pk=pk)
    pdf = render_to_pdf('invoices/pdf.html', {'invoice': invoice})

    return HttpResponse(pdf, content_type='application/pdf')