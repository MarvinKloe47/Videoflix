from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RegistrationSerializer,
)
from .services import (
    get_user_by_uid,
    send_activation_email,
    send_password_reset_email,
)
from .utils import (
    activate_user,
    blacklist_refresh_token,
    expire_jwt_cookie,
    get_login_credentials,
    get_reset_user,
    get_valid_reset_user,
    set_access_cookie,
    set_refresh_cookie,
    validate_refresh_user,
)


def registration_response(user):
    return {
        "user": {"id": user.id, "email": user.email},
        "token": default_token_generator.make_token(user),
    }


def activation_error(message):
    return Response({"message": message}, status=status.HTTP_400_BAD_REQUEST)


def activation_success_message():
    return {"message": "Account successfully activated."}


def missing_login_data_response():
    return Response(
        {"message": "E-Mail und Passwort sind erforderlich."},
        status=status.HTTP_400_BAD_REQUEST,
    )


def invalid_login_response():
    return Response(
        {"message": "Ungültige Zugangsdaten oder Konto nicht aktiviert."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def refresh_cookie_missing_response():
    return Response(
        {"detail": "Refresh token is missing."},
        status=status.HTTP_400_BAD_REQUEST,
    )


def invalid_refresh_token_response():
    return Response(
        {"detail": "Invalid refresh token."},
        status=status.HTTP_401_UNAUTHORIZED,
    )


def create_login_response(user):
    refresh = RefreshToken.for_user(user)
    refresh["session_id"] = refresh["jti"]
    response = Response(login_response_data(user))
    set_access_cookie(response, refresh)
    set_refresh_cookie(response, refresh)
    return response


def login_response_data(user):
    return {
        "detail": "Login successful",
        "user": {"id": user.id, "username": user.email},
    }


def create_token_refresh_response(refresh):
    response = Response(
        {"detail": "Token refreshed", "access": str(refresh.access_token)}
    )
    set_access_cookie(response, refresh)
    return response


# --------------------------------------------------
# REGISTRIERUNG
# --------------------------------------------------


class RegistrationView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        send_activation_email(user)
        return Response(registration_response(user), status=status.HTTP_201_CREATED)


# --------------------------------------------------
# E-MAIL-AKTIVIERUNG
# --------------------------------------------------


class ActivationView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, uidb64, token):
        user = get_user_by_uid(uidb64)
        if user is None:
            return activation_error("Ungültiger Aktivierungslink.")
        if user.is_active:
            return Response({"message": "Dieses Konto ist bereits aktiviert."})
        if not default_token_generator.check_token(user, token):
            return activation_error(
                "Der Aktivierungslink ist ungültig oder abgelaufen."
            )
        activate_user(user)
        return Response(activation_success_message())


# --------------------------------------------------
# PASSWORT ZURUECKSETZEN
# --------------------------------------------------


class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_reset_user(serializer.validated_data["email"])
        if user is not None:
            send_password_reset_email(user)
        return Response(get_password_reset_response(), status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, uidb64, token):
        user = get_valid_reset_user(uidb64, token)
        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Your Password has been successfully reset."})


def get_password_reset_response():
    return {"detail": "An email has been sent to reset your password."}


@method_decorator(csrf_protect, name="dispatch")
class TokenRefreshView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_token = request.COOKIES.get("refresh_token")
        if raw_token is None:
            return refresh_cookie_missing_response()
        try:
            refresh = RefreshToken(raw_token)
            validate_refresh_user(refresh)
            return create_token_refresh_response(refresh)
        except TokenError:
            return invalid_refresh_token_response()


# --------------------------------------------------
# LOGIN MIT JWT-COOKIES UND CSRF-SCHUTZ
# --------------------------------------------------


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email, password = get_login_credentials(request)
        if not email or not password:
            return missing_login_data_response()
        user = authenticate(request, username=email, password=password)
        if user is None:
            return invalid_login_response()
        return create_login_response(user)


# --------------------------------------------------
# CSRF-TOKEN ABRUFEN
# --------------------------------------------------


@method_decorator(ensure_csrf_cookie, name="dispatch")
class CSRFTokenView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        token = get_token(request)

        return Response(
            {"csrfToken": token},
            status=status.HTTP_200_OK,
        )


# --------------------------------------------------
# ANGEMELDETEN BENUTZER ABRUFEN
# --------------------------------------------------


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "id": user.id,
                "email": user.email,
            },
            status=status.HTTP_200_OK,
        )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        raw_token = request.COOKIES.get("refresh_token")
        if raw_token is None:
            return refresh_cookie_missing_response()
        try:
            blacklist_refresh_token(raw_token)
        except TokenError:
            return invalid_refresh_token_response()
        return logout_response()


def logout_response():
    response = Response({"detail": (
        "Logout successful! All tokens will be deleted. Refresh token is now invalid."
    )})
    expire_jwt_cookie(response, "access_token", "/")
    expire_jwt_cookie(response, "refresh_token", "/api/")
    return response
