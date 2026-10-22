"""Use the real admin views and keep CSRF enforcement enabled for writes."""

from django.test import Client, TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import User


class UserAdminTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            "admin@example.com", "AdminFixture123!")
        self.member = User.objects.create_user(
            "member@example.com", "MemberFixture123!")
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(self.admin)
        self.change_url = reverse("admin:auth_app_user_change", args=[self.member.pk])

    def post_admin(self, url, data):
        self.client.get(url)
        data["csrfmiddlewaretoken"] = self.client.cookies["csrftoken"].value
        return self.client.post(url, data)

    def test_list_searches_users_by_email(self):
        url = reverse("admin:auth_app_user_changelist")
        response = self.client.get(url, {"q": self.member.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["cl"].queryset), [self.member])

    def test_change_form_uses_email_and_readonly_password(self):
        response = self.client.get(self.change_url)
        self.assertEqual(response.status_code, 200)
        fields = response.context["adminform"].form.fields
        self.assertIn("email", fields)
        self.assertNotIn("username", fields)
        self.assertTrue(fields["password"].disabled)

    def test_edits_member_without_changing_password(self):
        original_hash = self.member.password
        response = self.post_admin(self.change_url, {
            "email": self.member.email, "first_name": "Updated", "is_active": "on",
        })
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertEqual(self.member.first_name, "Updated")
        self.assertEqual(self.member.password, original_hash)

    def test_deactivates_member_and_rejects_api_login(self):
        response = self.post_admin(self.change_url, {"email": self.member.email})
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertFalse(self.member.is_active)
        response = self.client.post("/api/login/", {
            "email": self.member.email, "password": "MemberFixture123!",
        }, content_type="application/json")
        self.assertEqual(response.status_code, 401)

    def test_deletes_member(self):
        url = reverse("admin:auth_app_user_delete", args=[self.member.pk])
        response = self.post_admin(url, {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.filter(pk=self.member.pk).exists())

    def test_deactivation_also_blocks_existing_jwt_cookies(self):
        client = APIClient(enforce_csrf_checks=True)
        data = {"email": self.member.email, "password": "MemberFixture123!"}
        self.assertEqual(client.post("/api/login/", data).status_code, 200)
        self.post_admin(self.change_url, {"email": self.member.email})
        self.assertEqual(client.get("/api/video/").status_code, 401)
        self.assertEqual(client.post("/api/token/refresh/", {}).status_code, 401)

    def test_add_form_hashes_password_without_username(self):
        response = self.post_admin(reverse("admin:auth_app_user_add"), {
            "email": "added@example.com", "usable_password": "true",
            "password1": "AddedFixture123!", "password2": "AddedFixture123!",
        })
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(email="added@example.com")
        self.assertTrue(user.check_password("AddedFixture123!"))
        self.assertFalse(user.is_staff or user.is_superuser)

    def test_admin_password_change_uses_standard_hashed_password_form(self):
        url = reverse("admin:auth_user_password_change", args=[self.member.pk])
        response = self.post_admin(url, {
            "password1": "ChangedFixture123!", "password2": "ChangedFixture123!",
            "usable_password": "true",
        })
        self.assertEqual(response.status_code, 302)
        self.member.refresh_from_db()
        self.assertTrue(self.member.check_password("ChangedFixture123!"))

    def test_admin_write_without_csrf_is_denied(self):
        response = self.client.post(self.change_url, {"email": self.member.email})
        self.assertEqual(response.status_code, 403)

    def test_admin_login_without_csrf_is_denied(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("admin:login"), {
            "username": self.admin.email, "password": "AdminFixture123!",
        })
        self.assertEqual(response.status_code, 403)

    def test_regular_member_cannot_access_user_admin(self):
        self.client.force_login(self.member)
        response = self.client.get(reverse("admin:auth_app_user_changelist"))
        self.assertEqual(response.status_code, 302)
