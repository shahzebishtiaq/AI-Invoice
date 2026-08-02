from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from clients.models import Client
from invoices.models import Invoice, InvoiceItem


class DashboardTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="dashboarduser",
            email="dashboard@example.com",
            password="StrongPassword123!",
        )

        self.client_record = Client.objects.create(
            user=self.user,
            name="Dashboard Client",
            email="client@example.com",
        )

        self.invoice = Invoice.objects.create(
            user=self.user,
            client=self.client_record,
            invoice_number="INV-DASH-0001",
            issue_date=date.today(),
            status=Invoice.STATUS_PAID,
        )

        InvoiceItem.objects.create(
            invoice=self.invoice,
            description="Django development",
            quantity=Decimal("1.00"),
            unit_price=Decimal("500.00"),
        )

        self.invoice.calculate_totals()

        Invoice.objects.filter(
            pk=self.invoice.pk,
        ).update(
            subtotal=self.invoice.subtotal,
            tax_amount=self.invoice.tax_amount,
            total=self.invoice.total,
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_dashboard_loads_for_logged_in_user(self):
        self.client.login(
            username="dashboarduser",
            password="StrongPassword123!",
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Dashboard",
        )

    def test_dashboard_displays_invoice_total(self):
        self.client.login(
            username="dashboarduser",
            password="StrongPassword123!",
        )

        response = self.client.get(
            reverse("dashboard")
        )

        self.assertEqual(
            response.context["total_invoices"],
            1,
        )

        self.assertEqual(
            response.context["paid_revenue"],
            Decimal("500.00"),
        )