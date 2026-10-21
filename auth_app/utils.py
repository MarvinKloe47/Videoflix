from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from .services import get_user_by_uid


def validate_refresh_user(refresh):
    user = get_user_model().objects.filter(pk=refresh["user_id"]).first()
    if user is None or not user.is_active:
        raise TokenError("Invalid user")
    if refresh.get("hash_password") != get_md5_hash_password(user.password):
        raise TokenError("Password changed")


def expire_jwt_cookie(response, key, path):
    response.set_cookie(
        key=key,
        value="",
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=0,
        expires="Thu, 01 Jan 1970 00:00:00 GMT",
        path=path,
    )


def activate_user(user):
    user.is_active = True
    user.save(update_fields=["is_active"])


def get_login_credentials(request):
    return request.data.get("email"), request.data.get("password")


def blacklist_refresh_token(raw_token):
    try:
        RefreshToken(raw_token).blacklist()
    except AttributeError:
        raise TokenError("Token blacklist unavailable")


def set_access_cookie(response, refresh):
    response.set_cookie(
        key="access_token",
        value=str(refresh.access_token),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=300,
        path="/",
    )


def set_refresh_cookie(response, refresh):
    response.set_cookie(
        key="refresh_token",
        value=str(refresh),
        httponly=True,
        secure=not settings.DEBUG,
        samesite="Lax",
        max_age=86400,
        path="/api/",
    )


def get_reset_user(email):
    User = get_user_model()
    return User.objects.filter(email__iexact=email, is_active=True).first()


def get_valid_reset_user(uidb64, token):
    user = get_user_by_uid(uidb64)
    if user is None or not user.is_active:
        raise_invalid_reset_token()
    if not default_token_generator.check_token(user, token):
        raise_invalid_reset_token()
    return user


def raise_invalid_reset_token():
    from rest_framework.exceptions import ValidationError

    raise ValidationError({"message": "Ungueltiger oder abgelaufener Link."})
