
from django.conf import settings
from django.middleware.csrf import CsrfViewMiddleware
from rest_framework.exceptions import PermissionDenied
from rest_framework_simplejwt.authentication import JWTAuthentication


class CSRFCheck(CsrfViewMiddleware):
    def _reject(self, request, reason):
        return reason


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        raw_token = request.COOKIES.get("access_token")

        if raw_token is None:
            return None

        validated_token = self.get_validated_token(raw_token)
        user = self.get_user(validated_token)

        self.enforce_csrf(request)

        return user, validated_token

    def enforce_csrf(self, request):
        check = CSRFCheck(lambda request: None)

        check.process_request(request)
        reason = check.process_view(request, lambda request: None, (), {})

        if reason:
            raise PermissionDenied(f"CSRF-Prüfung fehlgeschlagen: {reason}")

