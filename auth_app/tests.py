import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import UntypedToken


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    FRONTEND_ACTIVATION_URL="http://frontend/activate.html",
    FRONTEND_PASSWORD_RESET_URL="http://frontend/reset.html",
)
class AuthenticationCookieTests(TestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.email = "user@example.com"
        self.password = "SecurePass123!"
        self.User = get_user_model()
        self.user = self.create_user(self.email, self.password)

    def create_user(self, email, password, is_active=True):
        user = self.User(email=email, is_active=is_active)
        user.set_password(password)
        user.save()
        return user

    def get_csrf_header(self):
        response = self.client.get("/api/csrf/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}

    def login(self, password=None):
        response = self.client.post(
            "/api/login/",
            {"email": self.email, "password": password or self.password},
            format="json",
            **self.get_csrf_header(),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response

    def registration_data(self, **overrides):
        data = {
            "email": "new@example.com",
            "password": "NewSecurePass123!",
            "confirmed_password": "NewSecurePass123!",
        }
        data.update(overrides)
        return data

    def post_register(self, data):
        return self.client.post("/api/register/", data, format="json")

    def activation_params_from_mail(self):
        match = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[-1].body)
        self.assertIsNotNone(match)
        return match.groups()

    def reset_params_from_mail(self):
        match = re.search(r"uid=([^&\s]+)&token=([^\s]+)", mail.outbox[-1].body)
        self.assertIsNotNone(match)
        return match.groups()

    def request_password_reset(self, email=None):
        return self.client.post(
            "/api/password_reset/",
            {"email": email or self.email},
            format="json",
        )

    def expired_token_for(self, user):
        generator = PasswordResetTokenGenerator()
        timeout = settings.PASSWORD_RESET_TIMEOUT + 1
        timestamp = generator._num_seconds(generator._now()) - timeout
        return generator._make_token_with_timestamp(
            user, timestamp, settings.SECRET_KEY
        )

    def csrf_post(self, url, data=None):
        return self.client.post(
            url, data or {}, format="json", **self.get_csrf_header()
        )

    def assert_jwt_cookie(self, response, name, path, age):
        cookie = response.cookies[name]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")
        self.assertEqual(cookie["max-age"], age)
        self.assertEqual(cookie["path"], path)
        self.assertEqual(bool(cookie["secure"]), not settings.DEBUG)
        if age:
            token = UntypedToken(cookie.value)
            self.assertEqual(token["exp"] - token["iat"], age)

    def confirm_reset(
        self, uid, token, password="NewSecurePass123!", confirmation=None
    ):
        data = {"new_password": password, "confirm_password": confirmation or password}
        return self.client.post(
            f"/api/password_confirm/{uid}/{token}/", data, format="json"
        )

    def test_invalid_logout_token_returns_401(self):
        self.client.cookies["refresh_token"] = "invalid"
        response = self.client.post("/api/logout/", {}, **self.get_csrf_header())
        self.assertEqual(response.status_code, 401)

    def test_saved_access_cookie_is_revoked_after_logout(self):
        self.login()
        access = self.client.cookies["access_token"].value
        self.client.post("/api/logout/", {}, **self.get_csrf_header())
        self.client.cookies["access_token"] = access
        self.assertEqual(self.client.get("/api/user/").status_code, 401)

    def test_password_change_revokes_access_and_refresh(self):
        self.login()
        self.user.set_password("ChangedPass123!")
        self.user.save(update_fields=["password"])
        self.assertEqual(self.client.get("/api/user/").status_code, 401)
        response = self.client.post("/api/token/refresh/", {}, **self.get_csrf_header())
        self.assertEqual(response.status_code, 401)

    def test_disabled_user_cannot_refresh(self):
        self.login()
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])
        response = self.client.post("/api/token/refresh/", {}, **self.get_csrf_header())
        self.assertEqual(response.status_code, 401)

    def test_refresh_and_logout_require_csrf(self):
        self.client.cookies["refresh_token"] = "invalid"
        self.assertEqual(self.client.post("/api/token/refresh/", {}).status_code, 403)
        self.assertEqual(self.client.post("/api/logout/", {}).status_code, 403)

    def test_duplicate_registration_error_is_generic(self):
        response = self.post_register(self.registration_data(email=self.email))
        self.assertNotIn("already exists", str(response.data))
        self.assertEqual(response.status_code, 400)

    def test_cors_allows_only_configured_frontend(self):
        allowed = self.client.options(
            "/api/login/", HTTP_ORIGIN="http://localhost:5500"
        )
        denied = self.client.options(
            "/api/login/", HTTP_ORIGIN="https://untrusted.example"
        )
        self.assertEqual(
            allowed["Access-Control-Allow-Origin"], "http://localhost:5500"
        )
        self.assertNotIn("Access-Control-Allow-Origin", denied)

    def test_registration_email_includes_responsive_html_and_plain_text(self):
        self.post_register(self.registration_data())
        email = mail.outbox[-1]
        self.assertIn("uid=", email.body)
        self.assertIn("viewport", email.alternatives[0].content)
        self.assertEqual(email.alternatives[0].mimetype, "text/html")

    def test_registration_creates_inactive_user_and_sends_email(self):
        response = self.post_register(self.registration_data())

        user = self.User.objects.get(email="new@example.com")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(user.is_active)
        self.assertEqual(response.data["user"], {"id": user.id, "email": user.email})
        self.assertIn("token", response.data)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("http://frontend/activate.html?", mail.outbox[0].body)

    def test_registration_rejects_invalid_duplicate_and_password_mismatch(self):
        duplicate = self.post_register(self.registration_data(email=self.email))
        invalid_email = self.post_register(self.registration_data(email="bad"))
        mismatch = self.post_register(
            self.registration_data(confirmed_password="OtherSecurePass123!")
        )

        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(invalid_email.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_accepts_confirm_password_alias(self):
        data = self.registration_data(email="alias@example.com")
        data["confirm_password"] = data.pop("confirmed_password")

        response = self.post_register(data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_activation_with_valid_invalid_and_expired_token(self):
        self.post_register(self.registration_data())
        uid, token = self.activation_params_from_mail()
        expired = self.expired_token_for(self.User.objects.get(email="new@example.com"))
        for invalid in ("invalid-token", expired):
            response = self.client.get(f"/api/activate/{uid}/{invalid}/")
            self.assertEqual(response.status_code, 400)
        response = self.client.get(f"/api/activate/{uid}/{token}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Account successfully activated.")

    def test_login_rejects_inactive_user_wrong_password_and_missing_csrf(self):
        inactive = self.create_user("inactive@example.com", self.password, False)
        self.assertEqual(self.client.post("/api/login/", {}).status_code, 403)
        for email, password in ((inactive.email, self.password), (self.email, "wrong")):
            response = self.csrf_post(
                "/api/login/", {"email": email, "password": password}
            )
            self.assertEqual(response.status_code, 401)

    def test_login_sets_access_and_refresh_cookies(self):
        response = self.login()
        self.assertEqual(response.data["detail"], "Login successful")
        self.assertEqual(response.data["user"]["username"], self.email)
        self.assert_jwt_cookie(response, "access_token", "/", 300)
        self.assert_jwt_cookie(response, "refresh_token", "/api/", 86400)

    def test_logout_requires_csrf_token(self):
        self.login()

        response = self.client.post("/api/logout/", {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_requires_refresh_cookie(self):
        response = self.client.post(
            "/api/logout/",
            {},
            format="json",
            **self.get_csrf_header(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token is missing.")

    def test_logout_expires_access_and_refresh_cookies(self):
        self.login()
        response = self.csrf_post("/api/logout/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Logout successful", response.data["detail"])
        self.assert_jwt_cookie(response, "access_token", "/", 0)
        self.assert_jwt_cookie(response, "refresh_token", "/api/", 0)

    def test_token_refresh_requires_refresh_cookie(self):
        response = self.client.post(
            "/api/token/refresh/",
            {},
            format="json",
            **self.get_csrf_header(),
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Refresh token is missing.")

    def test_token_refresh_sets_new_access_cookie(self):
        self.login()

        response = self.client.post(
            "/api/token/refresh/",
            {},
            format="json",
            **self.get_csrf_header(),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Token refreshed")
        self.assertIn("access", response.data)
        self.assert_jwt_cookie(response, "access_token", "/", 300)

    def test_logout_blacklists_refresh_token(self):
        self.login()
        raw_token = self.client.cookies["refresh_token"].value
        self.csrf_post("/api/logout/")
        self.client.cookies["refresh_token"] = raw_token
        response = self.csrf_post("/api/token/refresh/")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["detail"], "Invalid refresh token.")

    def test_user_endpoint_denies_access_after_logout(self):
        self.login()
        self.assertEqual(self.client.get("/api/user/").status_code, 200)
        self.csrf_post("/api/logout/")
        self.assertEqual(self.client.get("/api/user/").status_code, 401)

    def test_password_reset_request_does_not_expose_unknown_email(self):
        known_response = self.request_password_reset()
        unknown_response = self.request_password_reset("unknown@example.com")

        self.assertEqual(known_response.status_code, status.HTTP_200_OK)
        self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
        self.assertEqual(known_response.data, unknown_response.data)
        self.assertEqual(
            known_response.data["detail"],
            "An email has been sent to reset your password.",
        )
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_valid_invalid_and_expired_tokens(self):
        self.request_password_reset()
        uid, token = self.reset_params_from_mail()
        for invalid in ("invalid-token", self.expired_token_for(self.user)):
            self.assertEqual(self.confirm_reset(uid, invalid).status_code, 400)
        response = self.confirm_reset(uid, token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["detail"], "Your Password has been successfully reset."
        )

    def test_password_reset_changes_password_and_token_cannot_be_reused(self):
        self.request_password_reset()
        uid, token = self.reset_params_from_mail()
        self.assertEqual(self.confirm_reset(uid, token).status_code, 200)
        self.assertEqual(self.confirm_reset(uid, token).status_code, 400)
        self.assertEqual(self.login(password="NewSecurePass123!").status_code, 200)

    def test_password_reset_rejects_mismatch_and_weak_password(self):
        self.request_password_reset()
        uid, token = self.reset_params_from_mail()
        mismatch = self.confirm_reset(uid, token, confirmation="OtherSecurePass123!")
        weak = self.confirm_reset(uid, token, "123", "123")
        self.assertEqual(mismatch.status_code, 400)
        self.assertEqual(weak.status_code, 400)
