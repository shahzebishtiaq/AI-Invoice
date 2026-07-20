from datetime import date
from unittest.mock import patch

from django.test import (
    TestCase,
    override_settings,
)
from django.urls import reverse

from accounts.models import User
from clients.models import Client
from invoices.models import Invoice

from .models import Subscription


class SubscriptionTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="freeuser",
            email="freeuser@example.com",
            password="StrongPassword123!",
        )

        self.client_record = Client.objects.create(
            user=self.user,
            name="Subscription Client",
            email="client@example.com",
        )

        self.client.login(
            username="freeuser",
            password="StrongPassword123!",
        )

    def test_subscription_created_for_new_user(self):
        self.assertTrue(
            Subscription.objects.filter(
                user=self.user,
            ).exists()
        )

    def test_free_user_can_create_fewer_than_five_invoices(self):
        subscription = self.user.subscription

        self.assertTrue(
            subscription.can_create_invoice()
        )

    def test_free_user_cannot_create_more_than_five_invoices(self):
        for number in range(5):
            Invoice.objects.create(
                user=self.user,
                client=self.client_record,
                invoice_number=f"INV-LIMIT-{number}",
                issue_date=date.today(),
            )

        self.assertFalse(
            self.user.subscription.can_create_invoice()
        )

    def test_invoice_create_redirects_when_limit_reached(self):
        for number in range(5):
            Invoice.objects.create(
                user=self.user,
                client=self.client_record,
                invoice_number=f"INV-LIMIT-{number}",
                issue_date=date.today(),
            )

        response = self.client.get(
            reverse("invoice_create")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("invoice_list"),
        )

    def test_pro_user_has_unlimited_invoices(self):
        subscription = self.user.subscription

        subscription.plan = Subscription.PLAN_PRO
        subscription.status = Subscription.STATUS_ACTIVE

        subscription.save(
            update_fields=[
                "plan",
                "status",
            ]
        )

        for number in range(10):
            Invoice.objects.create(
                user=self.user,
                client=self.client_record,
                invoice_number=f"INV-PRO-{number}",
                issue_date=date.today(),
            )

        self.assertTrue(
            subscription.can_create_invoice()
        )

    @override_settings(
        STRIPE_SECRET_KEY="sk_test_example",
        STRIPE_PRO_PRICE_ID="price_example",
    )
    @patch(
        "subscriptions.views.stripe.checkout.Session.create"
    )
    def test_checkout_session_created(
        self,
        mock_checkout_create,
    ):
        mock_checkout_create.return_value.id = (
            "cs_test_example"
        )

        mock_checkout_create.return_value.url = (
            "https://checkout.stripe.com/test"
        )

        response = self.client.post(
            reverse("subscription_checkout")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            "https://checkout.stripe.com/test",
        )

        subscription = self.user.subscription
        subscription.refresh_from_db()

        self.assertEqual(
            subscription.stripe_checkout_session_id,
            "cs_test_example",
        )

    def test_checkout_requires_login(self):
        self.client.logout()

        response = self.client.post(
            reverse("subscription_checkout")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        expected_login_url = (
            reverse("login")
            + "?next="
            + reverse("subscription_checkout")
        )

        self.assertEqual(
            response.url,
            expected_login_url,
        )

    def test_existing_pro_user_is_not_sent_to_checkout(self):
        subscription = self.user.subscription

        subscription.plan = Subscription.PLAN_PRO
        subscription.status = Subscription.STATUS_ACTIVE

        subscription.save(
            update_fields=[
                "plan",
                "status",
            ]
        )

        response = self.client.post(
            reverse("subscription_checkout")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            response.url,
            reverse("pricing"),
        )
