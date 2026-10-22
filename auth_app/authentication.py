"""Protect authenticated writes with CSRF and reject revoked JWT sessions."""

from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken


class CSRFCheck(CsrfViewMiddleware):
    # Return the reason so DRF can build its usual permission error response.
    def _reject(self, request, reason):
        return reason


class CookieJWTAuthentication(JWTAuthentication):
    """Read the access JWT from its cookie instead of an Authorization header."""
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        reject_revoked_session(validated_token)
        user = self.get_user(validated_token)

        self.enforce_csrf(request)

        return user, validated_token

    def enforce_csrf(self, request):
        # Browsers send cookies automatically, so writes also need a CSRF token.
        check = CSRFCheck(lambda request: None)

        check.process_request(request)
        reason = check.process_view(request, lambda request: None, (), {})

        if reason:
            raise PermissionDenied(f"CSRF-Prüfung fehlgeschlagen: {reason}")


def reject_revoked_session(token):
    # Access tokens carry the refresh token's ID to detect logout immediately.
    if BlacklistedToken.objects.filter(token__jti=token.get("session_id", "")).exists():
        raise AuthenticationFailed("Session expired")
