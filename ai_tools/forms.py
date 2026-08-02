from django import forms

from clients.models import Client


class AIInvoiceForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.none(),
        widget=forms.Select(
            attrs={
                "class": "form-control",
            }
        ),
    )

    prompt = forms.CharField(
        label="Describe the work or products",
        help_text=(
            "Example: Create an invoice for a business website, "
            "five pages, SEO setup, and one year of hosting."
        ),
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 7,
                "placeholder": (
                    "Example: Website design for $900, "
                    "SEO setup for $250, and hosting for $120."
                ),
            }
        ),
    )

    tax_rate = forms.DecimalField(
        required=False,
        initial=0,
        min_value=0,
        max_value=100,
        decimal_places=2,
        max_digits=5,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "max": "100",
                "step": "0.01",
            }
        ),
    )

    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "class": "form-control",
                "type": "date",
            }
        ),
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Optional invoice notes",
            }
        ),
    )

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user is not None:
            self.fields["client"].queryset = Client.objects.filter(
                user=user,
            ).order_by(
                "name"
            )

    def clean_client(self):
        client = self.cleaned_data["client"]

        if self.user and client.user_id != self.user.id:
            raise forms.ValidationError(
                "You cannot select another user's client."
            )

        return client

    def clean_prompt(self):
        prompt = self.cleaned_data["prompt"].strip()

        if len(prompt) < 10:
            raise forms.ValidationError(
                "Please provide a more detailed description."
            )

        if len(prompt) > 5000:
            raise forms.ValidationError(
                "The description is too long."
            )

        return prompt