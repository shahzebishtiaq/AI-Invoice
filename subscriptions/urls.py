from django.urls import path

from .views import (
    create_checkout_session,
    stripe_checkout_cancel,
    stripe_checkout_success,
    stripe_webhook,
    subscription_portal,
)


urlpatterns = [
    path(
        "checkout/",
        create_checkout_session,
        name="subscription_checkout",
    ),
    path(
        "success/",
        stripe_checkout_success,
        name="subscription_success",
    ),
    path(
        "cancel/",
        stripe_checkout_cancel,
        name="subscription_cancel",
    ),
    path(
        "portal/",
        subscription_portal,
        name="subscription_portal",
    ),
    path(
        "webhook/",
        stripe_webhook,
        name="stripe_webhook",
    ),
]