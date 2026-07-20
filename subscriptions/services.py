from .models import Subscription


def get_user_subscription(user):
    subscription, created = Subscription.objects.get_or_create(
        user=user,
    )

    return subscription


def user_can_create_invoice(user):
    subscription = get_user_subscription(
        user
    )

    return subscription.can_create_invoice()


def get_invoice_limit_message(user):
    subscription = get_user_subscription(
        user
    )

    if subscription.invoice_limit is None:
        return ""

    return (
        f"You have reached the free plan limit of "
        f"{subscription.invoice_limit} invoices. "
        f"Upgrade to Pro to create more invoices."
    )
