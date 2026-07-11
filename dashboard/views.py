from django.shortcuts import render
from invoices.models import Invoice

def dashboard_view(request):
    total = Invoice.objects.count()
    paid = Invoice.objects.filter(status='paid').count()
    pending = Invoice.objects.filter(status='sent').count()

    return render(request, 'dashboard/dashboard.html', {
        'total': total,
        'paid': paid,
        'pending': pending
    })