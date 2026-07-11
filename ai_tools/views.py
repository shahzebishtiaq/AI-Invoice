from django.shortcuts import render
from .utils import parse_invoice_text

def upload_invoice(request):
    result = None

    if request.method == 'POST':
        text = request.POST.get('text')
        result = parse_invoice_text(text)

    return render(request, 'ai_tools/upload.html', {'result': result})