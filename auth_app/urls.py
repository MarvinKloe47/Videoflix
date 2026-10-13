from django.urls import path

from .views import (
    RegistrationView,
    ActivationView,
    LoginView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    CSRFTokenView,
    LogoutView,
    TokenRefreshView,
    UserInfoView,
)


urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
    path(
        "activate/<str:uidb64>/<str:token>/",
        ActivationView.as_view(),
        name="activate",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("password_reset/", PasswordResetRequestView.as_view(), name="password-reset"),
    path(
        "password_confirm/<str:uidb64>/<str:token>/",
        PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),
    path("csrf/", CSRFTokenView.as_view(), name="csrf"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("user/", UserInfoView.as_view(), name="user-info"),
]