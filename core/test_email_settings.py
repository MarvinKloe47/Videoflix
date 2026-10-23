"""Check environment mapping independently of the developer's private .env file."""

import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase


def email_settings(**values):
    environment = {"SECRET_KEY": "settings-test-only", **values}
    with patch.dict(os.environ, environment, clear=True):
        with patch("dotenv.load_dotenv"):
            return runpy.run_path(str(Path(__file__).with_name("settings.py")))


class EmailSettingsTests(SimpleTestCase):
    def test_smtp_is_default_and_starttls_is_enabled(self):
        config = email_settings()
        self.assertEqual(config["EMAIL_BACKEND"],
                         "django.core.mail.backends.smtp.EmailBackend")
        self.assertTrue(config["EMAIL_USE_TLS"])
        self.assertFalse(config["EMAIL_USE_SSL"])
        self.assertEqual(config["EMAIL_PORT"], 587)

    def test_provider_values_and_implicit_ssl_are_read_from_environment(self):
        config = email_settings(EMAIL_HOST="mail.example.com", EMAIL_PORT="465",
                              EMAIL_USE_TLS="false", EMAIL_USE_SSL="true",
                              EMAIL_HOST_USER="fixture", EMAIL_HOST_PASSWORD="fixture",
                              DEFAULT_FROM_EMAIL="verified@example.com")
        self.assertEqual(config["EMAIL_HOST"], "mail.example.com")
        self.assertEqual(config["EMAIL_PORT"], 465)
        self.assertFalse(config["EMAIL_USE_TLS"])
        self.assertTrue(config["EMAIL_USE_SSL"])
        self.assertEqual(config["EMAIL_HOST_USER"], "fixture")
        self.assertEqual(config["EMAIL_HOST_PASSWORD"], "fixture")
        self.assertEqual(config["DEFAULT_FROM_EMAIL"], "verified@example.com")

    def test_console_requires_an_explicit_local_override(self):
        backend = "django.core.mail.backends.console.EmailBackend"
        config = email_settings(EMAIL_BACKEND=backend)
        self.assertEqual(config["EMAIL_BACKEND"], backend)
