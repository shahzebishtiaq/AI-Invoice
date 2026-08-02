from django.urls import path
from . import views

urlpatterns = [
    path(
        "generate-invoice/",
        views.generate_invoice_view,
        name="ai_generate_invoice",
    ),
]