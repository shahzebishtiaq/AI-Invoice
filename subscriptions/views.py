import logging
from datetime import (
    datetime,
    timezone as datetime_timezone,
)

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
)
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from accounts.models import User

from .models import Subscription
from .services import get_user_subscription


logger = logging.getLogger(__name__)


def configure_stripe():
    secret_key = settings.STRIPE_SECRET_KEY.strip()

    if not secret_key:
        raise ValueError(
            "STRIPE_SECRET_KEY is not configured in the .env file."
        )

    if not secret_key.startswith("sk_test_"):
        raise ValueError(
            "STRIPE_SECRET_KEY must be a real Stripe test secret key "
            "starting with sk_test_."
        )

    stripe.api_key = secret_key


def timestamp_to_datetime(timestamp):
    if not timestamp:
        return None

    return datetime.fromtimestamp(
        timestamp,
        tz=datetime_timezone.utc,
    )


@login_required
@require_POST
def create_checkout_session(request):
    subscription = get_user_subscription(
        request.user
    )

    if (
        subscription.plan == Subscription.PLAN_PRO
        and subscription.is_active
    ):
        messages.info(
            request,
            "You already have an active Pro subscription.",
        )

        return redirect(
            "pricing"
        )

    price_id = settings.STRIPE_PRO_PRICE_ID.strip()

    if not price_id:
        messages.error(
            request,
            "STRIPE_PRO_PRICE_ID is not configured.",
        )

        return redirect(
            "pricing"
        )

    if not price_id.startswith("price_"):
        messages.error(
            request,
            "STRIPE_PRO_PRICE_ID must start with price_.",
        )

        return redirect(
            "pricing"
        )

    try:
        configure_stripe()

        success_url = request.build_absolute_uri(
            reverse(
                "subscription_success"
            )
        )

        cancel_url = request.build_absolute_uri(
            reverse(
                "subscription_cancel"
            )
        )

        checkout_data = {
            "mode": "subscription",
            "line_items": [
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            "success_url": (
                success_url
                + "?session_id={CHECKOUT_SESSION_ID}"
            ),
            "cancel_url": cancel_url,
            "client_reference_id": str(
                request.user.pk
            ),
            "metadata": {
                "user_id": str(
                    request.user.pk
                ),
            },
            "subscription_data": {
                "metadata": {
                    "user_id": str(
                        request.user.pk
                    ),
                },
            },
            "allow_promotion_codes": True,
        }

        if subscription.stripe_customer_id:
            checkout_data["customer"] = (
                subscription.stripe_customer_id
            )
        else:
            checkout_data["customer_email"] = (
                request.user.email
            )

        checkout_session = stripe.checkout.Session.create(
            **checkout_data
        )

        if not checkout_session.url:
            raise ValueError(
                "Stripe created a Checkout Session "
                "but did not return a checkout URL."
            )

        subscription.stripe_checkout_session_id = (
            checkout_session.id
        )

        subscription.save(
            update_fields=[
                "stripe_checkout_session_id",
                "updated_at",
            ]
        )

        return redirect(
            checkout_session.url
        )

    except stripe.error.AuthenticationError as exc:
        logger.exception(
            "Stripe authentication failed."
        )

        messages.error(
            request,
            f"Stripe authentication failed: {exc}",
        )

    except stripe.error.InvalidRequestError as exc:
        logger.exception(
            "Stripe rejected the checkout request."
        )

        messages.error(
            request,
            f"Stripe request error: {exc}",
        )

    except stripe.error.StripeError as exc:
        logger.exception(
            "Stripe checkout failed."
        )

        messages.error(
            request,
            f"Stripe error: {exc}",
        )

    except Exception as exc:
        logger.exception(
            "Stripe checkout session creation failed."
        )

        messages.error(
            request,
            f"Checkout error: {exc}",
        )

    return redirect(
        "pricing"
    )


@login_required
@login_required
def stripe_checkout_success(request):
    session_id = request.GET.get(
        "session_id",
        "",
    ).strip()

    if not session_id:
        messages.warning(
            request,
            "Payment succeeded, but the Checkout Session ID "
            "was not returned. Your subscription will be updated "
            "when the Stripe webhook arrives.",
        )

        return redirect(
            "dashboard"
        )

    try:
        configure_stripe()

        checkout_session = stripe.checkout.Session.retrieve(
            session_id,
            expand=[
                "subscription",
            ],
        )

        session_user_id = str(
            checkout_session.get(
                "metadata",
                {},
            ).get(
                "user_id",
                "",
            )
        )

        if session_user_id != str(request.user.pk):
            logger.warning(
                "Stripe Checkout Session %s does not belong to user %s.",
                session_id,
                request.user.pk,
            )

            messages.error(
                request,
                "This payment session does not belong to your account.",
            )

            return redirect(
                "pricing"
            )

        payment_status = checkout_session.get(
            "payment_status",
            "",
        )

        stripe_subscription = checkout_session.get(
            "subscription"
        )

        if (
            payment_status in {
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
                "Payment completed. Your Pro subscription is active.",
            )

        else:
            messages.info(
                request,
                "Stripe is still processing your subscription. "
                "The account will be updated by the webhook.",
            )

    except stripe.error.StripeError:
        logger.exception(
            "Could not verify the successful Stripe Checkout Session."
        )

        messages.warning(
            request,
            "Payment was completed, but the subscription could not "
            "be verified immediately. The Stripe webhook will retry it.",
        )

    except Exception:
        logger.exception(
            "Unexpected Checkout success verification error."
        )

        messages.warning(
            request,
            "Payment was completed, but subscription verification "
            "is still pending.",
        )

    return redirect(
        "dashboard"
    )


@login_required
def stripe_checkout_cancel(request):
    messages.info(
        request,
        "Payment was cancelled. "
        "Your plan has not changed.",
    )

    return redirect(
        "pricing"
    )


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

        return redirect(
            "pricing"
        )

    try:
        configure_stripe()

        return_url = request.build_absolute_uri(
            reverse(
                "pricing"
            )
        )

        portal_session = (
            stripe.billing_portal.Session.create(
                customer=(
                    subscription.stripe_customer_id
                ),
                return_url=return_url,
            )
        )

        return redirect(
            portal_session.url
        )

    except stripe.error.StripeError as exc:
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

    return redirect(
        "pricing"
    )


def activate_pro_subscription(
    stripe_subscription,
):
    metadata = stripe_subscription.get(
        "metadata",
        {},
    )

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

    if user_id:
        try:
            user = User.objects.get(
                pk=user_id
            )
        except User.DoesNotExist:
            logger.warning(
                "Stripe subscription user does not exist: %s",
                user_id,
            )

            return

    elif customer_id:
        subscription = (
            Subscription.objects.filter(
                stripe_customer_id=customer_id,
            )
            .select_related(
                "user"
            )
            .first()
        )

        if subscription is None:
            logger.warning(
                "No user found for Stripe customer %s.",
                customer_id,
            )

            return

        user = subscription.user

    else:
        logger.warning(
            "Stripe subscription has no user metadata "
            "or customer ID."
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
        local_status = Subscription.STATUS_ACTIVE
        local_plan = Subscription.PLAN_PRO
    else:
        local_status = Subscription.STATUS_EXPIRED
        local_plan = Subscription.PLAN_FREE

    subscription.plan = local_plan
    subscription.status = local_status
    subscription.stripe_customer_id = customer_id
    subscription.stripe_subscription_id = (
        stripe_subscription_id
    )
    subscription.started_at = timezone.now()
    subscription.expires_at = timestamp_to_datetime(
        stripe_subscription.get(
            "current_period_end"
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

    subscription.plan = Subscription.PLAN_FREE
    subscription.status = Subscription.STATUS_CANCELLED
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
    webhook_secret = (
        settings.STRIPE_WEBHOOK_SECRET.strip()
    )

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
        logger.warning(
            "Stripe webhook request has no signature header."
        )

        return HttpResponseBadRequest(
            "Missing Stripe signature."
        )

    try:
        configure_stripe()

        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=webhook_secret,
        )

    except ValueError:
        logger.warning(
            "Stripe webhook contained an invalid payload."
        )

        return HttpResponseBadRequest(
            "Invalid Stripe payload."
        )

    except stripe.error.SignatureVerificationError:
        logger.warning(
            "Stripe webhook signature verification failed."
        )

        return HttpResponseBadRequest(
            "Invalid Stripe signature."
        )

    except ValueError as exc:
        logger.exception(
            "Stripe configuration error: %s",
            exc,
        )

        return HttpResponse(
            "Stripe is not configured correctly.",
            status=500,
        )

    event_id = event.get(
        "id",
        "",
    )

    event_type = event.get(
        "type",
        "",
    )

    event_object = (
        event.get(
            "data",
            {},
        ).get(
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
        if event_type == "checkout.session.completed":
            payment_status = event_object.get(
                "payment_status",
                "",
            )

            session_mode = event_object.get(
                "mode",
                "",
            )

            user_id = (
                event_object.get(
                    "metadata",
                    {},
                ).get(
                    "user_id"
                )
            )

            if not user_id:
                logger.warning(
                    "Checkout Session %s has no user_id metadata.",
                    event_object.get(
                        "id",
                        "",
                    ),
                )

                return HttpResponse(
                    status=200
                )

            subscription = (
                Subscription.objects.filter(
                    user_id=user_id,
                ).first()
            )

            if not subscription:
                logger.warning(
                    "No local subscription was found for user %s.",
                    user_id,
                )

                return HttpResponse(
                    status=200
                )

            subscription.stripe_customer_id = (
                event_object.get(
                    "customer",
                    "",
                )
                or subscription.stripe_customer_id
            )

            stripe_subscription_id = (
                event_object.get(
                    "subscription",
                    "",
                )
            )

            if stripe_subscription_id:
                subscription.stripe_subscription_id = (
                    stripe_subscription_id
                )

            subscription.stripe_checkout_session_id = (
                event_object.get(
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

            if (
                session_mode == "subscription"
                and stripe_subscription_id
                and payment_status in {
                    "paid",
                    "no_payment_required",
                }
            ):
                stripe_subscription = (
                    stripe.Subscription.retrieve(
                        stripe_subscription_id
                    )
                )

                activate_pro_subscription(
                    stripe_subscription
                )

        elif event_type in {
            "customer.subscription.created",
            "customer.subscription.updated",
        }:
            activate_pro_subscription(
                event_object
            )

        elif event_type == "customer.subscription.deleted":
            deactivate_pro_subscription(
                event_object
            )

        elif event_type == "invoice.payment_succeeded":
            stripe_subscription_id = (
                event_object.get(
                    "subscription",
                    "",
                )
            )

            if stripe_subscription_id:
                stripe_subscription = (
                    stripe.Subscription.retrieve(
                        stripe_subscription_id
                    )
                )

                activate_pro_subscription(
                    stripe_subscription
                )

        elif event_type == "invoice.payment_failed":
            stripe_subscription_id = (
                event_object.get(
                    "subscription",
                    "",
                )
            )

            if stripe_subscription_id:
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

        else:
            logger.info(
                "Ignoring unsupported Stripe event type %s.",
                event_type,
            )

    except stripe.error.StripeError:
        logger.exception(
            "Stripe API error while processing webhook %s.",
            event_id,
        )

        return HttpResponse(
            "Stripe API processing failed.",
            status=500,
        )

    except Exception:
        logger.exception(
            "Stripe webhook processing failed for event %s "
            "of type %s.",
            event_id,
            event_type,
        )

        return HttpResponse(
            "Webhook processing failed.",
            status=500,
        )

    return HttpResponse(
        status=200
    )
