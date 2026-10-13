
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegistrationSerializer


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


# --------------------------------------------------
# REGISTRIERUNG
# --------------------------------------------------

class RegistrationView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            activation_link = (
                f"http://127.0.0.1:8000/api/activate/{uid}/{token}/"
            )

            send_mail(
                subject="Videoflix – Konto aktivieren",
                message=(
                    "Willkommen bei Videoflix!\n\n"
                    "Klicke auf diesen Link, um dein Konto zu aktivieren:\n"
                    f"{activation_link}"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
            )

            return Response(
                {
                    "message": (
                        "Registrierung erfolgreich. "
                        "Bitte aktiviere dein Konto."
                    )
                },
                status=status.HTTP_201_CREATED,
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST,
        )


# --------------------------------------------------
# E-MAIL-AKTIVIERUNG
# --------------------------------------------------

class ActivationView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, uidb64, token):
        User = get_user_model()

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"message": "Ungültiger Aktivierungslink."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user.is_active:
            return Response(
                {"message": "Dieses Konto ist bereits aktiviert."},
                status=status.HTTP_200_OK,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {
                    "message": (
                        "Der Aktivierungslink ist ungültig "
                        "oder abgelaufen."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.is_active = True
        user.save(update_fields=["is_active"])

        return Response(
            {
                "message": (
                    "Dein Videoflix-Konto wurde "
                    "erfolgreich aktiviert."
                )
            },
            status=status.HTTP_200_OK,
        )


# --------------------------------------------------
# LOGIN MIT JWT-COOKIES UND CSRF-SCHUTZ
# --------------------------------------------------

@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {
                    "message": (
                        "E-Mail und Passwort sind erforderlich."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(
            request,
            username=email,
            password=password,
        )

        if user is None:
            return Response(
                {
                    "message": (
                        "Ungültige Zugangsdaten "
                        "oder Konto nicht aktiviert."
                    )
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)

        response = Response(
            {"message": "Login erfolgreich."},
            status=status.HTTP_200_OK,
        )

        # Kurzlebiges Access-Token
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=300,
            path="/",
        )

        # Refresh-Token für die spätere Token-Erneuerung
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=86400,
            path="/api/",
        )

        return response


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
        response = Response(
            {"message": "Logout erfolgreich."},
            status=status.HTTP_200_OK,
        )

        expire_jwt_cookie(response, "access_token", "/")
        expire_jwt_cookie(response, "refresh_token", "/api/")

        return response


