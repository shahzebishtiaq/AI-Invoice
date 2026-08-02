import json
import logging
from decimal import Decimal, InvalidOperation

from django.conf import settings
from openai import OpenAI


logger = logging.getLogger(__name__)


class AIInvoiceGenerationError(Exception):
    """Raised when invoice items cannot be generated."""


def get_openai_client():
    api_key = settings.OPENAI_API_KEY

    if not api_key:
        return None

    return OpenAI(
        api_key=api_key,
    )


def get_fallback_items():
    """
    Return test data when no OpenAI API key is configured.

    This allows the rest of the project to be tested without
    spending API credits.
    """

    return [
        {
            "description": "Professional service",
            "quantity": Decimal("1.00"),
            "unit_price": Decimal("100.00"),
        }
    ]


def extract_json_from_text(content):
    """
    Remove accidental Markdown code fences before parsing JSON.
    """

    content = content.strip()

    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]

    if content.endswith("```"):
        content = content[:-3]

    return content.strip()


def normalize_invoice_items(raw_items):
    """
    Validate and convert AI values into Decimal values that can
    safely be stored in Django DecimalField columns.
    """

    if not isinstance(raw_items, list):
        raise AIInvoiceGenerationError(
            "The AI response was not a list of invoice items."
        )

    if not raw_items:
        raise AIInvoiceGenerationError(
            "The AI did not create any invoice items."
        )

    if len(raw_items) > 20:
        raise AIInvoiceGenerationError(
            "The AI generated too many invoice items."
        )

    normalized_items = []

    for position, item in enumerate(
        raw_items,
        start=1,
    ):
        if not isinstance(item, dict):
            raise AIInvoiceGenerationError(
                f"Invoice item {position} has an invalid format."
            )

        description = str(
            item.get(
                "description",
                "",
            )
        ).strip()

        quantity_value = item.get(
            "quantity",
            1,
        )

        price_value = item.get(
            "unit_price",
            item.get("price"),
        )

        if not description:
            raise AIInvoiceGenerationError(
                f"Invoice item {position} has no description."
            )

        if len(description) > 500:
            description = description[:500]

        try:
            quantity = Decimal(
                str(quantity_value)
            ).quantize(
                Decimal("0.01")
            )

            unit_price = Decimal(
                str(price_value)
            ).quantize(
                Decimal("0.01")
            )
        except (
            InvalidOperation,
            TypeError,
            ValueError,
        ) as exc:
            raise AIInvoiceGenerationError(
                f"Invoice item {position} contains an invalid number."
            ) from exc

        if quantity <= 0:
            raise AIInvoiceGenerationError(
                f"Invoice item {position} must have a positive quantity."
            )

        if unit_price < 0:
            raise AIInvoiceGenerationError(
                f"Invoice item {position} cannot have a negative price."
            )

        normalized_items.append(
            {
                "description": description,
                "quantity": quantity,
                "unit_price": unit_price,
            }
        )

    return normalized_items


def generate_invoice_items(prompt):
    client = get_openai_client()

    if client is None:
        return get_fallback_items()

    instructions = """
You generate professional invoice line items.

Convert the user's description into a JSON array.

Each array item must have exactly these fields:

- description: a clear string
- quantity: a positive number
- unit_price: a non-negative number

Rules:

- Return only valid JSON.
- Do not return Markdown.
- Do not include explanations.
- Do not include currency symbols in numbers.
- Do not calculate tax.
- Create no more than 20 items.
- If a price is not provided, make a reasonable estimate.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            instructions=instructions,
            input=prompt,
        )

        content = response.output_text

        if not content:
            raise AIInvoiceGenerationError(
                "The AI returned an empty response."
            )

        cleaned_content = extract_json_from_text(
            content
        )

        raw_items = json.loads(
            cleaned_content
        )

        return normalize_invoice_items(
            raw_items
        )

    except json.JSONDecodeError as exc:
        logger.exception(
            "OpenAI returned invalid JSON."
        )

        raise AIInvoiceGenerationError(
            "The AI response was not valid JSON. Please try again."
        ) from exc

    except AIInvoiceGenerationError:
        raise

    except Exception as exc:
        logger.exception(
            "OpenAI invoice generation failed."
        )

        raise AIInvoiceGenerationError(
            "Invoice generation failed. Check your API key and try again."
        ) from exc