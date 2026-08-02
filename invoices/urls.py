from django.urls import path

from . import views


urlpatterns = [
    path(
        "",
        views.invoice_list,
        name="invoice_list",
    ),
    path(
        "create/",
        views.invoice_create,
        name="invoice_create",
    ),
    path(
        "<int:pk>/",
        views.invoice_detail,
        name="invoice_detail",
    ),
    path(
        "<int:pk>/edit/",
        views.invoice_update,
        name="invoice_update",
    ),
    path(
        "<int:pk>/delete/",
        views.invoice_delete,
        name="invoice_delete",
    ),
    path(
        "<int:pk>/pdf/",
        views.invoice_pdf,
        name="invoice_pdf",
    ),
    path(
        "<int:pk>/send/",
        views.invoice_send_email,
        name="invoice_send_email",
    ),
    path(
        "<int:pk>/mark-paid/",
        views.invoice_mark_paid,
        name="invoice_mark_paid",
    ),
]