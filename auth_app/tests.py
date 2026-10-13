from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient


class AuthenticationCookieTests(TestCase):
	def setUp(self):
		self.client = APIClient(enforce_csrf_checks=True)
		self.email = "user@example.com"
		self.password = "SecurePass123!"

		User = get_user_model()
		self.user = User(email=self.email, is_active=True)
		self.user.set_password(self.password)
		self.user.save()

	def get_csrf_header(self):
		response = self.client.get("/api/csrf/")
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		return {"HTTP_X_CSRFTOKEN": self.client.cookies["csrftoken"].value}

	def login(self):
		response = self.client.post(
			"/api/login/",
			{"email": self.email, "password": self.password},
			format="json",
			**self.get_csrf_header(),
		)
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		return response

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
