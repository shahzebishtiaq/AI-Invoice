from django import forms
from django.forms import inlineformset_factory
from django.utils import timezone

from clients.models import Client

from .models import Invoice, InvoiceItem


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice

        fields = [
            "client",
            "invoice_number",
            "issue_date",
            "due_date",
            "status",
            "tax_rate",
            "notes",
        ]

        widgets = {
            "client": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "invoice_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "INV-1001",
                }
            ),
            "issue_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "due_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                }
            ),
            "status": forms.Select(
                attrs={
                    "class": "form-control",
                }
            ),
            "tax_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "max": "100",
                    "step": "0.01",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": "Payment terms or additional notes",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if self.user is not None:
            self.fields["client"].queryset = Client.objects.filter(
                user=self.user,
            )

        if not self.instance.pk:
            self.fields["issue_date"].initial = timezone.localdate()

            if self.user is not None:
                self.fields["tax_rate"].initial = (
                    self.user.default_tax_rate
                )

    def clean_client(self):
        client = self.cleaned_data["client"]

        if self.user and client.user_id != self.user.id:
            raise forms.ValidationError(
                "You cannot use another user's client."
            )

        return client

    def clean_invoice_number(self):
        invoice_number = self.cleaned_data[
            "invoice_number"
        ].strip()

        existing = Invoice.objects.filter(
            invoice_number__iexact=invoice_number,
        )

        if self.user is not None:
            existing = existing.filter(
                user=self.user,
            )

        if self.instance.pk:
            existing = existing.exclude(
                pk=self.instance.pk,
            )

        if existing.exists():
            raise forms.ValidationError(
                "You already have an invoice with this invoice number."
            )

        return invoice_number

    def clean(self):
        cleaned_data = super().clean()

        issue_date = cleaned_data.get(
            "issue_date"
        )

        due_date = cleaned_data.get(
            "due_date"
        )

        if (
            issue_date
            and due_date
            and due_date < issue_date
        ):
            self.add_error(
                "due_date",
                "Due date cannot be before the issue date.",
            )

        return cleaned_data


class InvoiceItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceItem

        fields = [
            "description",
            "quantity",
            "unit_price",
        ]

        widgets = {
            "description": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Service or product description",
                }
            ),
            "quantity": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0.01",
                    "step": "0.01",
                }
            ),
            "unit_price": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "step": "0.01",
                }
            ),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]

        if quantity <= 0:
            raise forms.ValidationError(
                "Quantity must be greater than zero."
            )

        return quantity

    def clean_unit_price(self):
        unit_price = self.cleaned_data["unit_price"]

        if unit_price < 0:
            raise forms.ValidationError(
                "Unit price cannot be negative."
            )

        return unit_price


InvoiceItemFormSet = inlineformset_factory(
    Invoice,
    InvoiceItem,
    form=InvoiceItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
