import shutil
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import User
from .hls import process_video_to_hls
from .models import Video
from .tasks import convert_video_to_hls


class VideoAPITests(TestCase):
    def setUp(self):
        self.media_root = Path(tempfile.mkdtemp())
        self.override = override_settings(
            MEDIA_ROOT=self.media_root,
            MEDIA_URL="/media/",
            VIDEO_ENQUEUE_HLS_JOBS=False,
        )
        self.override.enable()
        self.client = APIClient()
        self.user = self.create_user()
        self.old_public = self.create_video(title="Old Public", genre="DRAMA")
        self.new_public = self.create_video(title="New Public", genre="ACTION")
        self.private_video = self.create_video(
            title="Private Video",
            visibility="PRIVATE",
        )
        self.set_created_at(self.old_public, days_ago=2)
        self.set_created_at(self.new_public, days_ago=1)
        self.set_created_at(self.private_video, days_ago=0)

    def tearDown(self):
        self.override.disable()
        shutil.rmtree(self.media_root, ignore_errors=True)

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

    def create_hls_files(self, video, resolution="480p"):
        output_dir = self.media_root / "hls" / str(video.pk) / resolution
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.m3u8").write_text("#EXTM3U\nsegment_000.ts\n")
        (output_dir / "segment_000.ts").write_bytes(b"segment")

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

        categories = {video["title"]: video["category"] for video in response.data}
        self.assertEqual(categories[self.new_public.title], self.new_public.genre)
        self.assertEqual(categories[self.old_public.title], self.old_public.genre)

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
            "http://testserver/media/thumbnails/public-video.jpg",
        )
        self.assertEqual(
            response.data["video_url"],
            "http://testserver/media/videos/public-video.mp4",
        )

    def test_hls_manifest_endpoint_serves_playlist(self):
        self.authenticate()
        self.create_hls_files(self.new_public)

        response = self.client.get(f"/api/video/{self.new_public.pk}/480p/index.m3u8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Content-Type"], "application/vnd.apple.mpegurl")

    def test_hls_segment_endpoint_serves_segment(self):
        self.authenticate()
        self.create_hls_files(self.new_public)

        response = self.client.get(
            f"/api/video/{self.new_public.pk}/480p/segment_000.ts/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Content-Type"], "video/MP2T")

    def test_hls_endpoints_require_authentication(self):
        self.create_hls_files(self.new_public)

        manifest = self.client.get(f"/api/video/{self.new_public.pk}/480p/index.m3u8")
        segment = self.client.get(f"/api/video/{self.new_public.pk}/480p/segment_000.ts/")

        self.assertEqual(manifest.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(segment.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hls_endpoints_return_404_for_invalid_inputs(self):
        self.authenticate()
        self.create_hls_files(self.new_public)

        invalid_resolution = self.client.get(f"/api/video/{self.new_public.pk}/360p/index.m3u8")
        private_video = self.client.get(f"/api/video/{self.private_video.pk}/480p/index.m3u8")
        missing_file = self.client.get(f"/api/video/{self.new_public.pk}/720p/index.m3u8")
        traversal = self.client.get(f"/api/video/{self.new_public.pk}/480p/..bad.ts/")

        self.assertEqual(invalid_resolution.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(private_video.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(missing_file.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(traversal.status_code, status.HTTP_404_NOT_FOUND)

    @override_settings(VIDEO_ENQUEUE_HLS_JOBS=True)
    @patch("django_rq.enqueue")
    def test_video_save_enqueues_hls_job(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            video = self.create_video(title="Queued Video")

        enqueue.assert_called_with(convert_video_to_hls, video.pk)

    @patch("video_app.hls.probe_video_height", return_value=720)
    @patch("video_app.hls.execute_ffmpeg")
    def test_hls_processing_creates_allowed_resolutions(self, execute_ffmpeg, probe):
        execute_ffmpeg.side_effect = create_fake_hls_output

        result = process_video_to_hls(self.new_public.pk)
        self.new_public.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(self.new_public.processing_status, "READY")
        self.assertTrue((self.media_root / "hls" / str(self.new_public.pk) / "480p").exists())
        self.assertTrue((self.media_root / "hls" / str(self.new_public.pk) / "720p").exists())
        self.assertFalse((self.media_root / "hls" / str(self.new_public.pk) / "1080p").exists())
        self.assertEqual(probe.call_count, 1)
        playlist = self.media_root / "hls" / str(self.new_public.pk) / "480p" / "index.m3u8"
        self.assertIn(
            f"/api/video/{self.new_public.pk}/480p/segment_000.ts/",
            playlist.read_text(),
        )

    @patch("video_app.hls.probe_video_height", side_effect=FileNotFoundError("missing"))
    def test_hls_processing_marks_failures(self, probe):
        with self.assertLogs("video_app.hls", level="ERROR"):
            result = process_video_to_hls(self.new_public.pk)
        self.new_public.refresh_from_db()

        self.assertFalse(result)
        self.assertEqual(self.new_public.processing_status, "FAILED")
        self.assertIn("missing", self.new_public.processing_error)

    def test_real_ffmpeg_integration_if_available(self):
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("ffmpeg/ffprobe not available in PATH")
        source_path = self.media_root / "videos" / "real-input.mp4"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        create_tiny_mp4(source_path)
        video = self.create_video(title="Real FFmpeg", video_file="videos/real-input.mp4")

        result = process_video_to_hls(video.pk)
        video.refresh_from_db()

        self.assertTrue(result)
        self.assertEqual(video.processing_status, "READY")
        self.assertTrue((self.media_root / "hls" / str(video.pk) / "480p" / "index.m3u8").is_file())


def create_fake_hls_output(command):
    playlist = Path(command[-1])
    playlist.write_text("#EXTM3U\nsegment_000.ts\n")
    segment_pattern = command[command.index("-hls_segment_filename") + 1]
    Path(segment_pattern.replace("%03d", "000")).write_bytes(b"segment")


def create_tiny_mp4(source_path):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=640x480:rate=1",
            "-t",
            "1",
            str(source_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )