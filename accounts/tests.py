from django.core import mail
from django.test import TestCase, override_settings
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


@override_settings(
    EMAIL_BACKEND=(
        "django.core.mail.backends.locmem.EmailBackend"
    )
)
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OldStrongPassword123!",
        )

    def test_password_reset_page_loads(self):
        response = self.client.get(
            reverse("password_reset")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertContains(
            response,
            "Forgot your password?",
        )

    def test_password_reset_email_is_sent(self):
        response = self.client.post(
            reverse("password_reset"),
            {
                "email": self.user.email,
            },
        )

        self.assertRedirects(
            response,
            reverse("password_reset_done"),
        )

        self.assertEqual(
            len(mail.outbox),
            1,
        )

        self.assertIn(
            "Reset your YourAIInvoice password",
            mail.outbox[0].subject,
        )

        self.assertIn(
            "password-reset-confirm",
            mail.outbox[0].body,
        )

    def test_unknown_email_does_not_send_email(self):
        response = self.client.post(
            reverse("password_reset"),
            {
                "email": "unknown@example.com",
            },
        )

        self.assertRedirects(
            response,
            reverse("password_reset_done"),
        )

        self.assertEqual(
            len(mail.outbox),
            0,
        )