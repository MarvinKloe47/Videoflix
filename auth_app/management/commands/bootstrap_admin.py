"""Create an optional administrator after migrations without resetting accounts."""

import os

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.validators import validate_email

from auth_app.models import User


class Command(BaseCommand):
    help = "Create an email-based superuser from DJANGO_SUPERUSER_EMAIL/PASSWORD"

    def handle(self, *args, **options):
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "").strip().lower()
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "")
        if not email and not password:
            self.stdout.write(self.style.WARNING(
                "Admin creation skipped: set DJANGO_SUPERUSER_EMAIL and "
                "DJANGO_SUPERUSER_PASSWORD, or run createsuperuser manually."))
            return
        if not email or not password:
            raise CommandError(
                "Set DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD together.")
        _, created = ensure_admin(email, password)
        self.stdout.write("Superuser created." if created else
                          "Existing superuser retained; password unchanged.")


def ensure_admin(email, password):
    """Never promote an existing regular user or overwrite a stored password."""
    existing = User.objects.filter(email__iexact=email).first()
    if existing:
        if not (existing.is_active and existing.is_staff and existing.is_superuser):
            raise CommandError("Existing account is not an active admin; unchanged.")
        return existing, False
    try:
        validate_email(email)
        validate_password(password, user=User(email=email))
    except ValidationError as error:
        raise CommandError("; ".join(error.messages)) from error
    return User.objects.create_superuser(email=email, password=password), True
