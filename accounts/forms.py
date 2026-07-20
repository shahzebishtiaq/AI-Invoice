from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    UserCreationForm,
)

from .models import User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                "class": "form-control",
                "placeholder": "Email address",
            }
        ),
    )

    company_name = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Company name",
            }
        ),
    )

    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Phone number",
            }
        ),
    )

    class Meta:
        model = User

        fields = [
            "username",
            "email",
            "company_name",
            "phone_number",
            "password1",
            "password2",
        ]

        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Username",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["password1"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Password",
            }
        )

        self.fields["password2"].widget.attrs.update(
            {
                "class": "form-control",
                "placeholder": "Confirm password",
            }
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "Username",
                "autofocus": True,
            }
        )
    )

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Password",
            }
        )
    )


class AccountSettingsForm(forms.ModelForm):
    class Meta:
        model = User

        fields = [
            "first_name",
            "last_name",
            "email",
            "company_name",
            "phone_number",
            "company_address",
            "company_logo",
            "default_currency",
            "default_tax_rate",
        ]

        widgets = {
            "first_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "First name",
                }
            ),
            "last_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Last name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Business email",
                }
            ),
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company name",
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "company_address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company address",
                    "rows": 4,
                }
            ),
            "company_logo": forms.ClearableFileInput(
                attrs={
                    "class": "form-control",
                    "accept": "image/*",
                }
            ),
            "default_currency": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "default_tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        existing_users = User.objects.filter(
            email__iexact=email
        )

        if self.instance.pk:
            existing_users = existing_users.exclude(
                pk=self.instance.pk
            )

        if existing_users.exists():
            raise forms.ValidationError(
                "Another account already uses this email address."
            )

        return email

    def clean_default_tax_rate(self):
        tax_rate = self.cleaned_data["default_tax_rate"]

        if tax_rate < 0 or tax_rate > 100:
            raise forms.ValidationError(
                "Tax rate must be between 0 and 100."
            )

        return tax_rate

    def clean_company_logo(self):
        logo = self.cleaned_data.get("company_logo")

        if logo and hasattr(logo, "size"):
            maximum_size = 2 * 1024 * 1024

            if logo.size > maximum_size:
                raise forms.ValidationError(
                    "The company logo must be smaller than 2 MB."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            content_type = getattr(
                logo,
                "content_type",
                None,
            )

            if content_type and content_type not in allowed_types:
                raise forms.ValidationError(
                    "Use a JPG, PNG, or WebP image."
                )

        return logo
