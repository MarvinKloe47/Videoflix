"""Exercise Django's SMTP transport for both account emails without real secrets."""

from email import policy
from email.parser import BytesParser
from smtplib import SMTPAuthenticationError
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from .models import User
from .services import send_activation_email, send_password_reset_email


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend",
    EMAIL_HOST="smtp.example.com", EMAIL_PORT=587,
    EMAIL_USE_TLS=True, EMAIL_USE_SSL=False,
    EMAIL_HOST_USER="smtp-fixture", EMAIL_HOST_PASSWORD="smtp-fixture-password",
    DEFAULT_FROM_EMAIL="sender@example.com",
)
class SMTPEmailTests(SimpleTestCase):
    def setUp(self):
        self.user = User(pk=7, email="recipient@example.com")
        self.user.set_password("EmailFixtureOnly123!")

    def assert_delivery(self, client, subject):
        sender, recipients, content = client.sendmail.call_args.args
        self.assertEqual(sender, "sender@example.com")
        self.assertEqual(recipients, [self.user.email])
        message = BytesParser(policy=policy.default).parsebytes(content)
        self.assertEqual(message["Subject"], subject)
        plain = message.get_body(preferencelist=("plain",)).get_content()
        self.assertIn("?uid=", plain)
        self.assertIn("cid:videoflix-logo",
                      message.get_body(preferencelist=("html",)).get_content())

    def test_activation_uses_starttls_and_configured_credentials(self):
        with patch("smtplib.SMTP") as smtp:
            send_activation_email(self.user)
        smtp.assert_called_once()
        self.assertEqual(smtp.call_args.args, ("smtp.example.com", 587))
        client = smtp.return_value
        client.starttls.assert_called_once()
        client.login.assert_called_once_with("smtp-fixture", "smtp-fixture-password")
        calls = [call[0] for call in client.method_calls]
        self.assertLess(calls.index("starttls"), calls.index("login"))
        self.assert_delivery(client, "Confirm your email")

    @override_settings(EMAIL_USE_TLS=False, EMAIL_USE_SSL=True, EMAIL_PORT=465)
    def test_reset_uses_implicit_ssl_and_configured_sender(self):
        with patch("smtplib.SMTP_SSL") as smtp:
            send_password_reset_email(self.user)
        self.assertEqual(smtp.call_args.args, ("smtp.example.com", 465))
        self.assertIn("context", smtp.call_args.kwargs)
        client = smtp.return_value
        client.starttls.assert_not_called()
        client.login.assert_called_once_with("smtp-fixture", "smtp-fixture-password")
        self.assert_delivery(client, "Reset your Password")

    @override_settings(EMAIL_USE_TLS=True, EMAIL_USE_SSL=True)
    def test_tls_and_ssl_together_are_rejected(self):
        with self.assertRaises(ValueError):
            send_activation_email(self.user)

    def test_invalid_smtp_credentials_are_not_silently_ignored(self):
        with patch("smtplib.SMTP") as smtp:
            smtp.return_value.login.side_effect = SMTPAuthenticationError(
                535, b"Denied")
            with self.assertRaises(SMTPAuthenticationError):
                send_activation_email(self.user)
