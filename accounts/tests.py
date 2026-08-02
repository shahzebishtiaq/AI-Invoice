from django.test import TestCase
from django.urls import reverse

from .models import User


class AccountsTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(
            reverse("register")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_user_registration(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "testuser",
                "email": "test@example.com",
                "company_name": "Test Company",
                "phone_number": "123456789",
                "password1": "StrongPassword123!",
                "password2": "StrongPassword123!",
            },
        )

        self.assertTrue(
            User.objects.filter(
                username="testuser"
            ).exists()
        )

        self.assertEqual(
            response.status_code,
            302,
        )