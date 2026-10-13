import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core import mail
from django.test import override_settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


@override_settings(
	EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
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
		match = re.search(r"activate/([^/]+)/([^/]+)/", mail.outbox[-1].body)
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
		return generator._make_token_with_timestamp(user, timestamp, settings.SECRET_KEY)

	def test_registration_creates_inactive_user_and_sends_email(self):
		response = self.post_register(self.registration_data())

		user = self.User.objects.get(email="new@example.com")
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertFalse(user.is_active)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn("activate/", mail.outbox[0].body)

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

		invalid_response = self.client.get(f"/api/activate/{uid}/invalid-token/")
		expired_response = self.client.get(f"/api/activate/{uid}/{expired}/")
		valid_response = self.client.get(f"/api/activate/{uid}/{token}/")

		self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(expired_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(valid_response.status_code, status.HTTP_200_OK)

	def test_login_rejects_inactive_user_wrong_password_and_missing_csrf(self):
		inactive = self.create_user("inactive@example.com", self.password, False)

		no_csrf = self.client.post("/api/login/", {}, format="json")
		inactive_response = self.client.post(
			"/api/login/",
			{"email": inactive.email, "password": self.password},
			format="json",
			**self.get_csrf_header(),
		)
		wrong_response = self.client.post(
			"/api/login/",
			{"email": self.email, "password": "wrong"},
			format="json",
			**self.get_csrf_header(),
		)

		self.assertEqual(no_csrf.status_code, status.HTTP_403_FORBIDDEN)
		self.assertEqual(inactive_response.status_code, status.HTTP_401_UNAUTHORIZED)
		self.assertEqual(wrong_response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_login_sets_access_and_refresh_cookies(self):
		response = self.login()

		access_cookie = response.cookies["access_token"]
		refresh_cookie = response.cookies["refresh_token"]

		self.assertTrue(access_cookie["httponly"])
		self.assertEqual(access_cookie["samesite"], "Lax")
		self.assertEqual(access_cookie["max-age"], 300)
		self.assertEqual(access_cookie["path"], "/")

		self.assertTrue(refresh_cookie["httponly"])
		self.assertEqual(refresh_cookie["samesite"], "Lax")
		self.assertEqual(refresh_cookie["max-age"], 86400)
		self.assertEqual(refresh_cookie["path"], "/api/")

	def test_logout_requires_csrf_token(self):
		self.login()

		response = self.client.post("/api/logout/", {}, format="json")

		self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

	def test_logout_expires_access_and_refresh_cookies(self):
		self.login()

		response = self.client.post(
			"/api/logout/",
			{},
			format="json",
			**self.get_csrf_header(),
		)

		self.assertEqual(response.status_code, status.HTTP_200_OK)

		access_cookie = response.cookies["access_token"]
		refresh_cookie = response.cookies["refresh_token"]

		self.assertTrue(access_cookie["httponly"])
		self.assertEqual(access_cookie["max-age"], 0)
		self.assertEqual(access_cookie["path"], "/")
		self.assertEqual(access_cookie["samesite"], "Lax")

		self.assertTrue(refresh_cookie["httponly"])
		self.assertEqual(refresh_cookie["max-age"], 0)
		self.assertEqual(refresh_cookie["path"], "/api/")
		self.assertEqual(refresh_cookie["samesite"], "Lax")

	def test_user_endpoint_denies_access_after_logout(self):
		self.login()

		authenticated_response = self.client.get("/api/user/")
		self.assertEqual(authenticated_response.status_code, status.HTTP_200_OK)

		self.client.post(
			"/api/logout/",
			{},
			format="json",
			**self.get_csrf_header(),
		)

		logged_out_response = self.client.get("/api/user/")

		self.assertEqual(logged_out_response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_password_reset_request_does_not_expose_unknown_email(self):
		known_response = self.request_password_reset()
		unknown_response = self.request_password_reset("unknown@example.com")

		self.assertEqual(known_response.status_code, status.HTTP_200_OK)
		self.assertEqual(unknown_response.status_code, status.HTTP_200_OK)
		self.assertEqual(known_response.data, unknown_response.data)
		self.assertEqual(len(mail.outbox), 1)

	def test_password_reset_valid_invalid_and_expired_tokens(self):
		self.request_password_reset()
		uid, token = self.reset_params_from_mail()
		expired = self.expired_token_for(self.user)

		invalid_response = self.client.post(
			f"/api/password_confirm/{uid}/invalid-token/",
			{"new_password": "NewSecurePass123!", "confirm_password": "NewSecurePass123!"},
			format="json",
		)
		expired_response = self.client.post(
			f"/api/password_confirm/{uid}/{expired}/",
			{"new_password": "NewSecurePass123!", "confirm_password": "NewSecurePass123!"},
			format="json",
		)
		valid_response = self.client.post(
			f"/api/password_confirm/{uid}/{token}/",
			{"new_password": "NewSecurePass123!", "confirm_password": "NewSecurePass123!"},
			format="json",
		)

		self.assertEqual(invalid_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(expired_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(valid_response.status_code, status.HTTP_200_OK)

	def test_password_reset_changes_password_and_token_cannot_be_reused(self):
		self.request_password_reset()
		uid, token = self.reset_params_from_mail()
		data = {"new_password": "NewSecurePass123!", "confirm_password": "NewSecurePass123!"}

		reset_response = self.client.post(
			f"/api/password_confirm/{uid}/{token}/",
			data,
			format="json",
		)
		reuse_response = self.client.post(
			f"/api/password_confirm/{uid}/{token}/",
			data,
			format="json",
		)
		self.password = "NewSecurePass123!"
		login_response = self.login(password=self.password)

		self.assertEqual(reset_response.status_code, status.HTTP_200_OK)
		self.assertEqual(reuse_response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(login_response.status_code, status.HTTP_200_OK)

	def test_password_reset_rejects_mismatch_and_weak_password(self):
		self.request_password_reset()
		uid, token = self.reset_params_from_mail()

		mismatch = self.client.post(
			f"/api/password_confirm/{uid}/{token}/",
			{"new_password": "NewSecurePass123!", "confirm_password": "OtherSecurePass123!"},
			format="json",
		)
		weak = self.client.post(
			f"/api/password_confirm/{uid}/{token}/",
			{"new_password": "123", "confirm_password": "123"},
			format="json",
		)

		self.assertEqual(mismatch.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(weak.status_code, status.HTTP_400_BAD_REQUEST)
