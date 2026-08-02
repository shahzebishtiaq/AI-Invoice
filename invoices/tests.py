from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clients.models import Client

from .models import Invoice, InvoiceItem


class InvoiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="invoiceuser",
            email="invoice@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.client_record = Client.objects.create(
            user=self.user,
            name="Test Client",
            email="client@example.com",
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.client_record,
            invoice_number="INV-TEST-0001",
            issue_date=date.today(),
            tax_rate=Decimal("10.00"),
        )

        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Website development",
            quantity=Decimal("2.00"),
            unit_price=Decimal("100.00"),
        )

        self.invoice.calculate_totals()

        Invoice.objects.filter(
            pk=self.invoice.pk,
        ).update(
            subtotal=self.invoice.subtotal,
            tax_amount=self.invoice.tax_amount,
            total=self.invoice.total,
        )

        self.client.login(
            username="invoiceuser",
            password="StrongPassword123!",
        )

    def test_invoice_total_calculation(self):
        self.invoice.refresh_from_db()

        self.assertEqual(
            self.invoice.subtotal,
            Decimal("200.00"),
        )

        self.assertEqual(
            self.invoice.tax_amount,
            Decimal("20.00"),
        )

        self.assertEqual(
            self.invoice.total,
            Decimal("220.00"),
        )

    def test_invoice_list_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("invoice_list")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_cannot_view_other_users_invoice(self):
        other_client = Client.objects.create(
            user=self.other_user,
            name="Other Client",
            email="otherclient@example.com",
        )

        other_invoice = Invoice.objects.create(
            user=self.other_user,
            client=other_client,
            invoice_number="INV-OTHER-0001",
            issue_date=date.today(),
        )

        response = self.client.get(
            reverse(
                "invoice_detail",
                kwargs={
                    "pk": other_invoice.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )