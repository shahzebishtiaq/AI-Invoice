#!/usr/bin/env python

import os
import sys


def main():
    """Run Django administrative tasks."""

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "ai_saas_invoices.settings",
    )

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Django could not be imported. Make sure Django is installed "
            "and your virtual environment is activated."
        ) from exc

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()