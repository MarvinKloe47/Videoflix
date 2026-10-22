"""Account emails follow supplied designs without changing activation/reset tokens."""

import re
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import SimpleTestCase, override_settings

from .services import send_activation_email, send_password_reset_email


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class AccountEmailTests(SimpleTestCase):
    def setUp(self):
        self.user = get_user_model()(pk=7, email="recipient@example.com")
        self.user.set_password("EmailFixtureOnly123!")

    def assert_valid_link(self, message):
        link = re.search(r"https?://\S+\?uid=\S+", message.body).group()
        query = parse_qs(urlsplit(link).query)
        self.assertIn("uid", query)
        self.assertTrue(default_token_generator.check_token(
            self.user, query["token"][0]))
        self.assertIn(link.replace("&", "&amp;"), message.alternatives[0].content)

    def test_activation_design_contains_valid_link_and_inline_logo(self):
        send_activation_email(self.user)
        message = mail.outbox[-1]
        self.assertEqual(message.subject, "Confirm your email")
        self.assertIn("Activate account", message.alternatives[0].content)
        self.assertIn('src="cid:videoflix-logo"', message.alternatives[0].content)
        self.assertEqual(message.message().get_content_subtype(), "related")
        self.assertEqual(message.attachments[0]["Content-ID"], "<videoflix-logo>")
        self.assert_valid_link(message)

    @override_settings(PASSWORD_RESET_TIMEOUT=86400)
    def test_reset_design_uses_actual_configured_expiry(self):
        send_password_reset_email(self.user)
        message = mail.outbox[-1]
        self.assertEqual(message.subject, "Reset your Password")
        self.assertIn("Reset password", message.alternatives[0].content)
        self.assertIn("24 hours", message.body)
        self.assertIn("24 hours", message.alternatives[0].content)
        self.assert_valid_link(message)

    def test_personalized_html_escapes_untrusted_names(self):
        self.user.first_name = '<script>alert("unsafe")</script>'
        send_activation_email(self.user)
        html = mail.outbox[-1].alternatives[0].content
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn(self.user.first_name, mail.outbox[-1].body)
