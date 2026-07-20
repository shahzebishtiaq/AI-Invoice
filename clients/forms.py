from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client

        fields = [
            "name",
            "email",
            "phone",
            "company_name",
            "address",
            "notes",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Client name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "client@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Phone number",
                }
            ),
            "company_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Company name",
                }
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Client address",
                    "rows": 4,
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": "Optional notes",
                    "rows": 4,
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if self.user is None:
            return email

        clients = Client.objects.filter(
            user=self.user,
            email__iexact=email,
        )

        if self.instance.pk:
            clients = clients.exclude(
                pk=self.instance.pk,
            )

        if clients.exists():
            raise forms.ValidationError(
                "You already have a client with this email address."
            )

        return email
