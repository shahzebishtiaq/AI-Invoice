import re

def parse_invoice_text(text):
    data = {}

    total = re.search(r'Total[: ]+(\d+\.?\d*)', text)
    date = re.search(r'Date[: ]+([\d\-\/]+)', text)

    if total:
        data['total'] = total.group(1)

    if date:
        data['date'] = date.group(1)

    return data
from openai import OpenAI

client = OpenAI(api_key="YOUR_API_KEY")

def extract_invoice_data(text):
    prompt = f"""
    Extract invoice data:
    {text}

    Return JSON with:
    - invoice_number
    - total
    - date
    - company
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content