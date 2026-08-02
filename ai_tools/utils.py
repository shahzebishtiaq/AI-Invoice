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