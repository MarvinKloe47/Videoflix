from email.mime.image import MIMEImage
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def encode_user_pk(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def get_user_by_uid(uidb64):
    """Treat malformed IDs and deleted users as invalid account links."""
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def make_activation_link(user):
    # The frontend reads these parameters and calls the activation API.
    params = urlencode({
        "uid": encode_user_pk(user), "token": default_token_generator.make_token(user)
    })
    return f"{settings.FRONTEND_ACTIVATION_URL}?{params}"


def make_password_reset_link(user):
    # The frontend collects the new password before posting it with this token.
    params = urlencode({
        "uid": encode_user_pk(user), "token": default_token_generator.make_token(user)
    })
    return f"{settings.FRONTEND_PASSWORD_RESET_URL}?{params}"


def send_activation_email(user):
    send_account_email(user, "activation", make_activation_link(user))


def send_password_reset_email(user):
    send_account_email(user, "password_reset", make_password_reset_link(user))


def send_account_email(user, kind, link):
    """Send plain text and HTML alternatives with an embedded logo."""
    context = email_context(user, kind, link)
    message = EmailMultiAlternatives(
        subject=context["subject"],
        body=render_to_string(f"auth_app/{kind}.txt", context),
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(render_to_string("auth_app/email.html", context),
                               "text/html")
    attach_email_logo(message)
    message.send()


def email_context(user, kind, link):
    activation = kind == "activation"
    return {
        "activation": activation,
        "recipient": user.first_name or user.email,
        "link": link,
        "validity_hours": settings.PASSWORD_RESET_TIMEOUT // 3600,
        "subject": "Confirm your email" if activation else "Reset your Password",
        "button_label": "Activate account" if activation else "Reset password",
    }


def attach_email_logo(message):
    # CID embedding keeps the supplied brand asset available without remote tracking.
    path = Path(__file__).parent / "static" / "auth_app" / "email-logo.png"
    logo = MIMEImage(path.read_bytes(), _subtype="png")
    logo.add_header("Content-ID", "<videoflix-logo>")
    logo.add_header("Content-Disposition", "inline", filename="videoflix-logo.png")
    message.mixed_subtype = "related"
    message.attach(logo)
