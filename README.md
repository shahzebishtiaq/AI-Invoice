# AI Invoice SaaS

A responsive Django SaaS application for managing clients and invoices, generating invoice items with OpenAI, exporting PDFs, sending invoice emails, and offering Stripe subscriptions.

## Features

- User registration, authentication, and company settings
- Client management with per-user data isolation
- Invoice creation, totals, status tracking, PDF export, and email delivery
- AI-assisted invoice line-item generation
- Free and Pro subscription limits with Stripe Checkout/webhooks
- Responsive navigation, cards, forms, tables, landing page, and pricing page
- Django REST Framework invoice API protected by session authentication

## Local setup

```bash
python -m venv .venv
```

Activate it:

```bash
# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

Then run:

```bash
pip install -r requirements.txt
cp .env.example .env  # Windows: copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`.

## Test before deployment

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test
python manage.py collectstatic --noinput
```

For a production security check, first configure production environment variables and run:

```bash
python manage.py check --deploy
```

## Production checklist

1. Set `DEBUG=False`.
2. Generate a strong, unique `DJANGO_SECRET_KEY`.
3. Set `ALLOWED_HOSTS` to your real domain names.
4. Set `CSRF_TRUSTED_ORIGINS` using full HTTPS origins, for example `https://example.com`.
5. Configure persistent production storage for the database and uploaded media.
6. Add real OpenAI, Stripe, and email credentials.
7. Use HTTPS, then enable secure cookies and redirects.
8. Start HSTS with a small value only after HTTPS is confirmed everywhere; increase it carefully.
9. Run migrations and `collectstatic` during deployment.
10. Never upload `.env`, `db.sqlite3`, virtual environments, or real API keys.

## Mobile QA widths

Test the interface at approximately 1440 px, 1024 px, 768 px, 390 px, and 320 px. Confirm that the menu opens and closes, tables scroll horizontally, forms remain readable, buttons are easy to tap, and no page causes horizontal body scrolling.
