from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import User
from .models import Video


@override_settings(MEDIA_URL="/media/")
class VideoAPITests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = self.create_user()
		self.old_public = self.create_video(
			title="Old Public",
			genre="DRAMA",
			video_file="videos/old-public.mp4",
			thumbnail_file="thumbnails/old-public.jpg",
		)
		self.new_public = self.create_video(
			title="New Public",
			genre="ACTION",
			video_file="videos/new-public.mp4",
			thumbnail_file="thumbnails/new-public.jpg",
		)
		self.private_video = self.create_video(
			title="Private Video",
			visibility="PRIVATE",
		)
		self.set_created_at(self.old_public, days_ago=2)
		self.set_created_at(self.new_public, days_ago=1)
		self.set_created_at(self.private_video, days_ago=0)

	def create_user(self):
		user = User(email="viewer@example.com", is_active=True)
		user.set_password("SecurePass123!")
		user.save()
		return user

	def authenticate(self):
		refresh = RefreshToken.for_user(self.user)
		self.client.cookies["access_token"] = str(refresh.access_token)

	def create_video(self, **overrides):
		data = {
			"title": "Public Video",
			"description": "A public video.",
			"visibility": "PUBLIC",
			"genre": "COMEDY",
			"video_file": "videos/public-video.mp4",
			"thumbnail_file": "thumbnails/public-video.jpg",
		}
		data.update(overrides)
		return Video.objects.create(**data)

	def set_created_at(self, video, days_ago):
		created_at = timezone.now() - timezone.timedelta(days=days_ago)
		Video.objects.filter(pk=video.pk).update(created_at=created_at)
		video.refresh_from_db()

	def get_video_list(self):
		return self.client.get("/api/video/")

	def test_public_video_list_returns_only_public_videos(self):
		self.authenticate()

		response = self.get_video_list()

		titles = [video["title"] for video in response.data]
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertIn(self.old_public.title, titles)
		self.assertIn(self.new_public.title, titles)
		self.assertNotIn(self.private_video.title, titles)

	def test_public_video_list_is_ordered_by_created_at_desc(self):
		self.authenticate()

		response = self.get_video_list()

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data[0]["id"], self.new_public.id)
		self.assertEqual(response.data[1]["id"], self.old_public.id)

	def test_public_video_list_exposes_categories_for_genre_grouping(self):
		self.authenticate()

		response = self.get_video_list()

		categories_by_title = {
			video["title"]: video["category"] for video in response.data
		}
		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(categories_by_title[self.new_public.title], self.new_public.genre)
		self.assertEqual(categories_by_title[self.old_public.title], self.old_public.genre)

	def test_public_video_detail_returns_single_public_video(self):
		self.authenticate()

		response = self.client.get(f"/api/video/{self.new_public.id}/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(response.data["id"], self.new_public.id)
		self.assertEqual(response.data["title"], self.new_public.title)

	def test_missing_video_detail_returns_404(self):
		self.authenticate()

		response = self.client.get("/api/video/999999/")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_private_video_detail_returns_404(self):
		self.authenticate()

		response = self.client.get(f"/api/video/{self.private_video.id}/")

		self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

	def test_video_endpoints_require_authentication(self):
		list_response = self.client.get("/api/video/")
		detail_response = self.client.get(f"/api/video/{self.old_public.id}/")

		self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)
		self.assertEqual(detail_response.status_code, status.HTTP_401_UNAUTHORIZED)

	def test_serializer_fields_and_file_urls(self):
		self.authenticate()

		response = self.client.get(f"/api/video/{self.new_public.id}/")

		self.assertEqual(response.status_code, status.HTTP_200_OK)
		self.assertEqual(
			set(response.data.keys()),
			{
				"id",
				"created_at",
				"title",
				"description",
				"thumbnail_url",
				"video_url",
				"category",
			},
		)
		self.assertEqual(response.data["category"], self.new_public.genre)
		self.assertEqual(
			response.data["thumbnail_url"],
			"http://testserver/media/thumbnails/new-public.jpg",
		)
		self.assertEqual(
			response.data["video_url"],
			"http://testserver/media/videos/new-public.mp4",
		)
