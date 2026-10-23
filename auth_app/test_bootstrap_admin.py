"""Exercise optional, repeatable admin creation without changing existing users."""

import os
from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from .models import User


@override_settings(ACADEMY_DEFAULT_ADMIN=False)
class BootstrapAdminTests(TestCase):
    def run_bootstrap(self, email="", password=""):
        values = {"DJANGO_SUPERUSER_EMAIL": email,
                  "DJANGO_SUPERUSER_PASSWORD": password}
        output = StringIO()
        with patch.dict(os.environ, values):
            call_command("bootstrap_admin", stdout=output, stderr=output)
        return output.getvalue()

    def test_creates_active_email_admin_with_hashed_password(self):
        output = self.run_bootstrap("ADMIN@example.com", "AdminFixture123!")
        user = User.objects.get(email="admin@example.com")
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password("AdminFixture123!"))
        self.assertNotEqual(user.password, "AdminFixture123!")
        self.assertNotIn("AdminFixture123!", output)

    def test_second_run_keeps_account_and_password(self):
        self.run_bootstrap("admin@example.com", "AdminFixture123!")
        user = User.objects.get()
        original_hash = user.password
        output = self.run_bootstrap("ADMIN@example.com", "DifferentFixture456!")
        user.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.password, original_hash)
        self.assertIn("password unchanged", output)

    def test_missing_credentials_skip_with_explanation(self):
        output = self.run_bootstrap()
        self.assertIn("Admin creation skipped", output)
        self.assertIn("DJANGO_SUPERUSER_EMAIL", output)
        self.assertFalse(User.objects.exists())

    def test_partial_credentials_fail_without_creating_account(self):
        for values in (("admin@example.com", ""), ("", "AdminFixture123!")):
            with self.subTest(values=values):
                with self.assertRaises(CommandError):
                    self.run_bootstrap(*values)
        self.assertFalse(User.objects.exists())

    def test_invalid_email_or_weak_password_fail(self):
        for values in (("invalid", "AdminFixture123!"), ("admin@example.com", "123")):
            with self.subTest(values=values):
                with self.assertRaises(CommandError):
                    self.run_bootstrap(*values)
        self.assertFalse(User.objects.exists())

    def test_existing_regular_account_is_not_promoted(self):
        user = User.objects.create_user("admin@example.com", "MemberFixture123!")
        with self.assertRaises(CommandError):
            self.run_bootstrap(user.email, "AdminFixture123!")
        user.refresh_from_db()
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertTrue(user.check_password("MemberFixture123!"))
        self.assertEqual(User.objects.count(), 1)

    def test_disabled_admin_is_not_reactivated(self):
        user = User.objects.create_superuser(
            "admin@example.com", "AdminFixture123!", is_active=False)
        with self.assertRaises(CommandError):
            self.run_bootstrap(user.email, "DifferentFixture456!")
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    @override_settings(DEBUG=True, ACADEMY_DEFAULT_ADMIN=True)
    def test_local_academy_defaults_create_known_admin(self):
        self.run_bootstrap()
        user = User.objects.get(email="admin@example.com")
        self.assertTrue(user.is_active and user.is_staff and user.is_superuser)
        self.assertTrue(user.check_password("adminpassword"))
        self.run_bootstrap()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(User.objects.get().password, user.password)

    @override_settings(DEBUG=False, ACADEMY_DEFAULT_ADMIN=True)
    def test_production_never_uses_academy_defaults(self):
        self.run_bootstrap()
        self.assertFalse(User.objects.exists())

    @override_settings(DEBUG=True, ACADEMY_DEFAULT_ADMIN=True)
    def test_default_does_not_overwrite_existing_admin_password(self):
        self.run_bootstrap("admin@example.com", "CustomFixture123!")
        self.run_bootstrap()
        self.assertTrue(User.objects.get().check_password("CustomFixture123!"))
