from django.urls import path

from .views import (
    RegistrationView,
    ActivationView,
    LoginView,
    CSRFTokenView,
    LogoutView,
)


urlpatterns = [
    path("register/", RegistrationView.as_view(), name="register"),
     path(
        "activate/<str:uidb64>/<str:token>/",
        ActivationView.as_view(),
        name="activate",
    ),
    path("login/", LoginView.as_view(), name="login"),
    path("csrf/", CSRFTokenView.as_view(), name="csrf"),
    path("logout/", LogoutView.as_view(), name="logout"),
]