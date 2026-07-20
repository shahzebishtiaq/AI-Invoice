from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clients.models import Client
from invoices.models import Invoice

from .services import normalize_invoice_items


class AIInvoiceServiceTests(TestCase):
    def test_normalize_invoice_items(self):
        items = normalize_invoice_items(
            [
                {
                    "description": "Website development",
                    "quantity": 1,
                    "unit_price": 1000,
                }
            ]
        )

        self.assertEqual(
            len(items),
            1,
        )

        self.assertEqual(
            items[0]["description"],
            "Website development",
        )

        self.assertEqual(
            str(items[0]["quantity"]),
            "1.00",
        )

        self.assertEqual(
            str(items[0]["unit_price"]),
            "1000.00",
        )


class AIInvoiceViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="aiuser",
            email="aiuser@example.com",
            password="StrongPassword123!",
        )

        self.client_record = Client.objects.create(
            user=self.user,
            name="AI Test Client",
            email="client@example.com",
        )

        self.client.login(
            username="aiuser",
            password="StrongPassword123!",
        )

    @patch(
        "ai_tools.views.generate_invoice_items"
    )
    def test_ai_invoice_creation(
        self,
        mock_generate_invoice_items,
    ):
        mock_generate_invoice_items.return_value = [
            {
                "description": "Django development",
                "quantity": 2,
                "unit_price": 250,
            }
        ]

        response = self.client.post(
            reverse("ai_generate_invoice"),
            {
                "client": self.client_record.pk,
                "prompt": (
                    "Create an invoice for two days "
                    "of Django development."
                ),
                "tax_rate": "10.00",
                "notes": "Thank you.",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertEqual(
            Invoice.objects.filter(
                user=self.user
            ).count(),
            1,
        )
