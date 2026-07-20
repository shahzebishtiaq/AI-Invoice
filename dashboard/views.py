from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from django.utils import timezone

from clients.models import Client
from invoices.models import Invoice
from subscriptions.services import get_user_subscription

def pricing_page(request):
    subscription = None

    if request.user.is_authenticated:
        subscription = get_user_subscription(
            request.user
        )

    return render(
        request,
        "dashboard/pricing.html",
        {
            "subscription": subscription,
        },
    )
def landing_page(request):
    if request.user.is_authenticated:
        return redirect(
            "dashboard"
        )

    return render(
        request,
        "dashboard/landing_page.html",
    )

@login_required
def dashboard_view(request):
    today = timezone.localdate()
    subscription = get_user_subscription(
        request.user
    )

    invoice_limit = subscription.invoice_limit

    if invoice_limit is None:
        remaining_invoices = None
    else:
        remaining_invoices = max(
            invoice_limit
            - request.user.invoices.count(),
            0,
        )

    user_invoices = Invoice.objects.filter(
        user=request.user,
    ).select_related(
        "client"
    )

    # Mark sent invoices as overdue when their due date has passed.
    user_invoices.filter(
        status=Invoice.STATUS_SENT,
        due_date__lt=today,
    ).update(
        status=Invoice.STATUS_OVERDUE,
    )

    total_clients = Client.objects.filter(
        user=request.user,
    ).count()

    total_invoices = user_invoices.count()

    draft_invoices = user_invoices.filter(
        status=Invoice.STATUS_DRAFT,
    ).count()

    sent_invoices = user_invoices.filter(
        status=Invoice.STATUS_SENT,
    ).count()

    paid_invoices = user_invoices.filter(
        status=Invoice.STATUS_PAID,
    ).count()

    overdue_invoices = user_invoices.filter(
        status=Invoice.STATUS_OVERDUE,
    ).count()

    cancelled_invoices = user_invoices.filter(
        status=Invoice.STATUS_CANCELLED,
    ).count()

    paid_revenue = (
        user_invoices.filter(
            status=Invoice.STATUS_PAID,
        ).aggregate(
            amount=Sum("total")
        )["amount"]
        or Decimal("0.00")
    )

    unpaid_amount = (
        user_invoices.filter(
            status__in=[
                Invoice.STATUS_SENT,
                Invoice.STATUS_OVERDUE,
            ]
        ).aggregate(
            amount=Sum("total")
        )["amount"]
        or Decimal("0.00")
    )

    draft_amount = (
        user_invoices.filter(
            status=Invoice.STATUS_DRAFT,
        ).aggregate(
            amount=Sum("total")
        )["amount"]
        or Decimal("0.00")
    )

    recent_invoices = user_invoices.order_by(
        "-created_at"
    )[:5]

    context = {
        "total_clients": total_clients,
        "total_invoices": total_invoices,
        "draft_invoices": draft_invoices,
        "sent_invoices": sent_invoices,
        "paid_invoices": paid_invoices,
        "overdue_invoices": overdue_invoices,
        "cancelled_invoices": cancelled_invoices,
        "paid_revenue": paid_revenue,
        "unpaid_amount": unpaid_amount,
        "draft_amount": draft_amount,
        "recent_invoices": recent_invoices,
        "subscription": subscription,
        "invoice_limit": invoice_limit,
        "remaining_invoices": remaining_invoices,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )
