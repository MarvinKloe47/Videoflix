from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode


def encode_user_pk(user):
    return urlsafe_base64_encode(force_bytes(user.pk))


def get_user_by_uid(uidb64):
    User = get_user_model()
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        return User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return None


def make_activation_link(user):
    uid = encode_user_pk(user)
    token = default_token_generator.make_token(user)
    return f"{settings.BACKEND_API_URL}/activate/{uid}/{token}/"


def make_password_reset_link(user):
    params = urlencode({"uid": encode_user_pk(user), "token": make_token(user)})
    return f"{settings.FRONTEND_PASSWORD_RESET_URL}?{params}"


def make_token(user):
    return default_token_generator.make_token(user)


def send_activation_email(user):
    send_mail(
        subject="Videoflix - Konto aktivieren",
        message=get_activation_message(user),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def send_password_reset_email(user):
    send_mail(
        subject="Videoflix - Passwort zuruecksetzen",
        message=get_password_reset_message(user),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )


def get_activation_message(user):
    return (
        "Willkommen bei Videoflix!\n\n"
        "Klicke auf diesen Link, um dein Konto zu aktivieren:\n"
        f"{make_activation_link(user)}"
    )


def get_password_reset_message(user):
    return (
        "Du hast ein neues Videoflix-Passwort angefordert.\n\n"
        "Klicke auf diesen Link, um ein neues Passwort zu setzen:\n"
        f"{make_password_reset_link(user)}"
    )