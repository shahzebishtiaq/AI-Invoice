from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Client


class ClientTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="StrongPassword123!",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="StrongPassword123!",
        )

        self.client.login(
            username="testuser",
            password="StrongPassword123!",
        )

    def test_client_list_requires_login(self):
        self.client.logout()

        response = self.client.get(
            reverse("client_list"),
        )

        self.assertEqual(
            response.status_code,
            302,
        )

    def test_user_can_create_client(self):
        response = self.client.post(
            reverse("client_create"),
            {
                "name": "John Smith",
                "email": "john@example.com",
                "phone": "123456789",
                "company_name": "Smith Company",
                "address": "New York",
                "notes": "Important client",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        self.assertTrue(
            Client.objects.filter(
                user=self.user,
                email="john@example.com",
            ).exists()
        )

    def test_user_cannot_view_another_users_client(self):
        other_client = Client.objects.create(
            user=self.other_user,
            name="Private Client",
            email="private@example.com",
        )

        response = self.client.get(
            reverse(
                "client_detail",
                kwargs={
                    "pk": other_client.pk,
                },
            )
        )

        self.assertEqual(
            response.status_code,
            404,
        )
