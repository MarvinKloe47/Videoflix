"""Create an optional email-based administrator without changing existing users."""

import os

import django


def create_admin():
    from django.contrib.auth import get_user_model

    email = os.getenv("DJANGO_SUPERUSER_EMAIL")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")
    if not email or not password:
        print("Automatic admin creation disabled; use createsuperuser if needed.")
        return
    User = get_user_model()
    if not User.objects.filter(email__iexact=email).exists():
        User.objects.create_superuser(email=email, password=password)
    print("Academy admin is available; existing credentials were not changed.")


if __name__ == "__main__":
    django.setup()
    create_admin()
