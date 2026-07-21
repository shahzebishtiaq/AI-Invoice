import logging
from datetime import datetime
from datetime import timezone as datetime_timezone

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User

from .models import Subscription
from .services import get_user_subscription


logger = logging.getLogger(__name__)


def stripe_to_dict(value):
    """
    Convert real Stripe objects to normal Python dictionaries.

    MagicMock objects used by Django tests are not converted.
    """
    if isinstance(value, dict):
        return value

    value_type = type(value)
    module_name = getattr(
        value_type,
        "__module__",
        "",
    )

    if module_name.startswith("stripe"):
        converter = getattr(
            value,
            "to_dict_recursive",
            None,
        )

        if callable(converter):
            return converter()

    return value


def configure_stripe():
    secret_key = getattr(
        settings,
        "STRIPE_SECRET_KEY",
        "",
    ).strip()

    if not secret_key:
        raise ValueError(
            "STRIPE_SECRET_KEY is not configured."
        )

    if not secret_key.startswith(
        (
            "sk_test_",
            "sk_live_",
        )
    ):
        raise ValueError(
            "STRIPE_SECRET_KEY has an invalid format."
        )

    stripe.api_key = secret_key


def timestamp_to_datetime(timestamp):
    if not timestamp:
        return None

    try:
        return datetime.fromtimestamp(
            int(timestamp),
            tz=datetime_timezone.utc,
        )
    except (
        TypeError,
        ValueError,
        OverflowError,
    ):
        logger.warning(
            "Invalid Stripe timestamp received: %r",
            timestamp,
        )
        return None


def get_subscription_period_end(
    stripe_subscription,
):
    stripe_subscription = stripe_to_dict(
        stripe_subscription
    )

    period_end = stripe_subscription.get(
        "current_period_end"
    )

    if period_end:
        return period_end

    items = stripe_subscription.get(
        "items",
        {},
    )

    items = stripe_to_dict(items)

    if isinstance(items, dict):
        item_data = items.get(
            "data",
            [],
        )
    else:
        item_data = []

    if item_data:
        first_item = stripe_to_dict(
            item_data[0]
        )

        if isinstance(first_item, dict):
            return first_item.get(
                "current_period_end"
            )

    return None


@login_required
@require_POST



@login_required
def stripe_checkout_success(request):
    session_id = request.GET.get(
        "session_id",
        "",
    ).strip()

    if not session_id:
        messages.warning(
            request,
            "Payment succeeded, but the Checkout Session "
            "ID was not returned. The webhook will update "
            "your subscription.",
        )
        return redirect("dashboard")

    try:
        configure_stripe()

        checkout_session = (
            stripe.checkout.Session.retrieve(
                session_id,
                expand=[
                    "subscription",
                ],
            )
        )

        checkout_session = stripe_to_dict(
            checkout_session
        )

        metadata = stripe_to_dict(
            checkout_session.get(
                "metadata",
                {},
            )
        )

        if not isinstance(metadata, dict):
            metadata = {}

        session_user_id = str(
            metadata.get(
                "user_id",
                "",
            )
        )

        if session_user_id != str(
            request.user.pk
        ):
            logger.warning(
                "Checkout Session %s does not belong "
                "to user %s.",
                session_id,
                request.user.pk,
            )

            messages.error(
                request,
                "This payment session does not belong "
                "to your account.",
            )
            return redirect("pricing")

        payment_status = checkout_session.get(
            "payment_status",
            "",
        )

        stripe_subscription = (
            checkout_session.get(
                "subscription"
            )
        )

        if (
            payment_status
            in {
                "paid",
                "no_payment_required",
            }
            and stripe_subscription
        ):
            if isinstance(
                stripe_subscription,
                str,
            ):
                stripe_subscription = (
                    stripe.Subscription.retrieve(
                        stripe_subscription
                    )
                )

            stripe_subscription = stripe_to_dict(
                stripe_subscription
            )

            activate_pro_subscription(
                stripe_subscription
            )

            subscription = get_user_subscription(
                request.user
            )

            subscription.stripe_checkout_session_id = (
                checkout_session.get(
                    "id",
                    "",
                )
            )

            subscription.stripe_customer_id = (
                checkout_session.get(
                    "customer",
                    "",
                )
                or subscription.stripe_customer_id
            )

            subscription.save(
                update_fields=[
                    "stripe_checkout_session_id",
                    "stripe_customer_id",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Payment completed. Your Pro "
                "subscription is active.",
            )

        else:
            messages.info(
                request,
                "Stripe is still processing your "
                "subscription. The webhook will update it.",
            )

    except stripe.StripeError:
        logger.exception(
            "Could not verify the successful "
            "Stripe Checkout Session."
        )

        messages.warning(
            request,
            "Payment completed, but Stripe verification "
            "failed temporarily.",
        )

    except Exception:
        logger.exception(
            "Unexpected Checkout success verification error."
        )

        messages.warning(
            request,
            "Payment was completed, but subscription "
            "verification is still pending.",
        )

    return redirect("dashboard")


@login_required
def stripe_checkout_cancel(request):
    messages.info(
        request,
        "Payment was cancelled. "
        "Your plan has not changed.",
    )

    return redirect("pricing")


@login_required
@require_POST
def subscription_portal(request):
    subscription = get_user_subscription(
        request.user
    )

    if not subscription.stripe_customer_id:
        messages.warning(
            request,
            "No Stripe billing account was found.",
        )
        return redirect("pricing")

    try:
        configure_stripe()

        return_url = request.build_absolute_uri(
            reverse("pricing")
        )

        portal_session = (
            stripe.billing_portal.Session.create(
                customer=(
                    subscription.stripe_customer_id
                ),
                return_url=return_url,
            )
        )

        portal_session = stripe_to_dict(
            portal_session
        )

        portal_url = portal_session.get(
            "url"
        )

        if not portal_url:
            raise ValueError(
                "Stripe did not return a billing portal URL."
            )

        return redirect(portal_url)

    except stripe.StripeError as exc:
        logger.exception(
            "Stripe billing portal creation failed."
        )

        messages.error(
            request,
            f"Stripe billing portal error: {exc}",
        )

    except Exception as exc:
        logger.exception(
            "Billing portal creation failed."
        )

        messages.error(
            request,
            f"Billing portal error: {exc}",
        )

    return redirect("pricing")


def activate_pro_subscription(
    stripe_subscription,
):
    stripe_subscription = stripe_to_dict(
        stripe_subscription
    )

    metadata = stripe_to_dict(
        stripe_subscription.get(
            "metadata",
            {},
        )
    )

    if not isinstance(metadata, dict):
        metadata = {}

    user_id = metadata.get(
        "user_id"
    )

    customer_id = stripe_subscription.get(
        "customer",
        "",
    )

    stripe_subscription_id = (
        stripe_subscription.get(
            "id",
            "",
        )
    )

    user = None

    if user_id:
        try:
            user = User.objects.get(
                pk=user_id
            )
        except User.DoesNotExist:
            logger.warning(
                "Stripe subscription user does "
                "not exist: %s",
                user_id,
            )
            return

    elif customer_id:
        existing_subscription = (
            Subscription.objects.filter(
                stripe_customer_id=customer_id,
            )
            .select_related("user")
            .first()
        )

        if existing_subscription:
            user = existing_subscription.user

    if user is None:
        logger.warning(
            "Could not match Stripe subscription %s "
            "to a local user.",
            stripe_subscription_id,
        )
        return

    subscription = get_user_subscription(
        user
    )

    stripe_status = stripe_subscription.get(
        "status",
        "",
    )

    active_statuses = {
        "active",
        "trialing",
    }

    if stripe_status in active_statuses:
        subscription.status = (
            Subscription.STATUS_ACTIVE
        )
        subscription.plan = (
            Subscription.PLAN_PRO
        )
    else:
        subscription.status = (
            Subscription.STATUS_EXPIRED
        )
        subscription.plan = (
            Subscription.PLAN_FREE
        )

    period_end = get_subscription_period_end(
        stripe_subscription
    )

    subscription.stripe_customer_id = (
        customer_id
        or subscription.stripe_customer_id
    )

    subscription.stripe_subscription_id = (
        stripe_subscription_id
        or subscription.stripe_subscription_id
    )

    subscription.started_at = timezone.now()

    subscription.expires_at = (
        timestamp_to_datetime(
            period_end
        )
    )

    subscription.save(
        update_fields=[
            "plan",
            "status",
            "stripe_customer_id",
            "stripe_subscription_id",
            "started_at",
            "expires_at",
            "updated_at",
        ]
    )


def deactivate_pro_subscription(
    stripe_subscription,
):
    stripe_subscription = stripe_to_dict(
        stripe_subscription
    )

    stripe_subscription_id = (
        stripe_subscription.get(
            "id",
            "",
        )
    )

    customer_id = stripe_subscription.get(
        "customer",
        "",
    )

    subscription = (
        Subscription.objects.filter(
            stripe_subscription_id=(
                stripe_subscription_id
            )
        ).first()
    )

    if subscription is None and customer_id:
        subscription = (
            Subscription.objects.filter(
                stripe_customer_id=customer_id,
            ).first()
        )

    if subscription is None:
        logger.warning(
            "Local subscription was not found for "
            "Stripe subscription %s.",
            stripe_subscription_id,
        )
        return

    subscription.plan = (
        Subscription.PLAN_FREE
    )

    subscription.status = (
        Subscription.STATUS_CANCELLED
    )

    subscription.expires_at = timezone.now()

    subscription.save(
        update_fields=[
            "plan",
            "status",
            "expires_at",
            "updated_at",
        ]
    )


@csrf_exempt
@require_POST
def stripe_webhook(request):
    webhook_secret = getattr(
        settings,
        "STRIPE_WEBHOOK_SECRET",
        "",
    ).strip()

    if not webhook_secret:
        logger.error(
            "STRIPE_WEBHOOK_SECRET is not configured."
        )

        return HttpResponse(
            "Webhook secret is not configured.",
            status=500,
        )

    if not webhook_secret.startswith("whsec_"):
        logger.error(
            "STRIPE_WEBHOOK_SECRET has an invalid format."
        )

        return HttpResponse(
            "Webhook secret must start with whsec_.",
            status=500,
        )

    payload = request.body

    signature = request.META.get(
        "HTTP_STRIPE_SIGNATURE",
        "",
    )

    if not signature:
        return HttpResponseBadRequest(
            "Missing Stripe signature."
        )

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=webhook_secret,
        )

        event = stripe_to_dict(
            event
        )

    except ValueError:
        logger.warning(
            "Stripe webhook contained an invalid payload."
        )

        return HttpResponseBadRequest(
            "Invalid Stripe payload."
        )

    except stripe.SignatureVerificationError:
        logger.warning(
            "Stripe webhook signature verification failed."
        )

        return HttpResponseBadRequest(
            "Invalid Stripe signature."
        )

    event_id = event.get(
        "id",
        "",
    )

    event_type = event.get(
        "type",
        "",
    )

    event_data = stripe_to_dict(
        event.get(
            "data",
            {},
        )
    )

    if not isinstance(event_data, dict):
        event_data = {}

    event_object = stripe_to_dict(
        event_data.get(
            "object",
            {},
        )
    )

    logger.info(
        "Processing Stripe webhook %s of type %s.",
        event_id,
        event_type,
    )

    try:
        configure_stripe()

        if event_type == (
            "checkout.session.completed"
        ):
            process_checkout_completed(
                event_object
            )

        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
        }:
            activate_pro_subscription(
                event_object
            )

        elif event_type == (
            "customer.subscription.deleted"
        ):
            deactivate_pro_subscription(
                event_object
            )

        elif event_type in {
            "invoice.paid",
            "invoice.payment_succeeded",
        }:
            process_paid_invoice(
                event_object
            )

        elif event_type == (
            "invoice.payment_failed"
        ):
            process_failed_invoice(
                event_object
            )

        else:
            logger.info(
                "Ignoring unsupported Stripe event: %s",
                event_type,
            )

    except stripe.StripeError:
        logger.exception(
            "Stripe API error while processing "
            "webhook %s.",
            event_id,
        )

        return HttpResponse(
            "Stripe API processing failed.",
            status=500,
        )

    except Exception:
        logger.exception(
            "Stripe webhook processing failed for "
            "event %s of type %s.",
            event_id,
            event_type,
        )

        return HttpResponse(
            "Webhook processing failed.",
            status=500,
        )

    return HttpResponse(status=200)


def process_checkout_completed(
    checkout_session,
):
    checkout_session = stripe_to_dict(
        checkout_session
    )

    metadata = stripe_to_dict(
        checkout_session.get(
            "metadata",
            {},
        )
    )

    if not isinstance(metadata, dict):
        metadata = {}

    user_id = (
        metadata.get(
            "user_id"
        )
        or checkout_session.get(
            "client_reference_id"
        )
    )

    if not user_id:
        logger.warning(
            "Checkout Session %s has no user ID.",
            checkout_session.get(
                "id",
                "",
            ),
        )
        return

    subscription = (
        Subscription.objects.filter(
            user_id=user_id,
        ).first()
    )

    if subscription is None:
        logger.warning(
            "No local subscription was found "
            "for user %s.",
            user_id,
        )
        return

    customer_id = checkout_session.get(
        "customer",
        "",
    )

    stripe_subscription_id = (
        checkout_session.get(
            "subscription",
            "",
        )
    )

    subscription.stripe_customer_id = (
        customer_id
        or subscription.stripe_customer_id
    )

    subscription.stripe_subscription_id = (
        stripe_subscription_id
        or subscription.stripe_subscription_id
    )

    subscription.stripe_checkout_session_id = (
        checkout_session.get(
            "id",
            "",
        )
    )

    subscription.save(
        update_fields=[
            "stripe_customer_id",
            "stripe_subscription_id",
            "stripe_checkout_session_id",
            "updated_at",
        ]
    )

    payment_status = checkout_session.get(
        "payment_status",
        "",
    )

    if (
        checkout_session.get("mode")
        == "subscription"
        and stripe_subscription_id
        and payment_status
        in {
            "paid",
            "no_payment_required",
        }
    ):
        stripe_subscription = (
            stripe.Subscription.retrieve(
                stripe_subscription_id
            )
        )

        stripe_subscription = stripe_to_dict(
            stripe_subscription
        )

        activate_pro_subscription(
            stripe_subscription
        )


def get_invoice_subscription_id(invoice):
    invoice = stripe_to_dict(
        invoice
    )

    subscription_id = invoice.get(
        "subscription"
    )

    if subscription_id:
        return subscription_id

    parent = stripe_to_dict(
        invoice.get(
            "parent",
            {},
        )
    )

    if isinstance(parent, dict):
        subscription_details = stripe_to_dict(
            parent.get(
                "subscription_details",
                {},
            )
        )

        if isinstance(
            subscription_details,
            dict,
        ):
            return subscription_details.get(
                "subscription"
            )

    return None


def process_paid_invoice(invoice):
    invoice = stripe_to_dict(
        invoice
    )

    stripe_subscription_id = (
        get_invoice_subscription_id(
            invoice
        )
    )

    if not stripe_subscription_id:
        logger.info(
            "Paid invoice %s has no subscription ID.",
            invoice.get(
                "id",
                "",
            ),
        )
        return

    stripe_subscription = (
        stripe.Subscription.retrieve(
            stripe_subscription_id
        )
    )

    stripe_subscription = stripe_to_dict(
        stripe_subscription
    )

    activate_pro_subscription(
        stripe_subscription
    )


def process_failed_invoice(invoice):
    invoice = stripe_to_dict(
        invoice
    )

    stripe_subscription_id = (
        get_invoice_subscription_id(
            invoice
        )
    )

    if not stripe_subscription_id:
        return

    subscription = (
        Subscription.objects.filter(
            stripe_subscription_id=(
                stripe_subscription_id
            ),
        ).first()
    )

    if subscription:
        subscription.status = (
            Subscription.STATUS_PAST_DUE
        )

        subscription.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )