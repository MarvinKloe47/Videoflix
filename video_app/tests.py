import shutil
import subprocess
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from rq.exceptions import DuplicateJobError

from auth_app.models import User

from .hls import process_video_to_hls
from .models import Video
from .signals import enqueue_hls_job
from .tasks import convert_video_to_hls, hls_job_failed


class VideoAPITests(TestCase):
    def setUp(self):
        cache.clear()
        self.media_root = Path(tempfile.mkdtemp())
        self.override = override_settings(
            MEDIA_ROOT=self.media_root,
            MEDIA_URL="/media/",
            VIDEO_ENQUEUE_HLS_JOBS=False,
        )
        self.override.enable()
        self.client = APIClient()
        self.user = self.create_user()
        self.create_library()

    def create_library(self):
        self.old_public = self.create_video(title="Old Public", genre="DRAMA")
        self.new_public = self.create_video(title="New Public", genre="ACTION")
        self.private_video = self.create_video(
            title="Private Video", visibility="PRIVATE"
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
        video.processing_status = "READY"
        video.save(update_fields=["processing_status"])
        output_dir = self.media_root / "hls" / str(video.pk) / resolution
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "index.m3u8").write_text("#EXTM3U\nsegment_000.ts\n")
        (output_dir / "segment_000.ts").write_bytes(b"segment")

    def test_nonready_hls_is_not_served(self):
        self.authenticate()
        self.create_hls_files(self.new_public)
        self.new_public.processing_status = "PENDING"
        self.new_public.save(update_fields=["processing_status"])
        url = f"/api/video/{self.new_public.pk}/480p/index.m3u8"
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_worker_failure_callback_records_unexpected_failure(self):
        job = SimpleNamespace(args=[self.new_public.pk], id=self.new_public.hls_job_id)
        hls_job_failed(job, None, RuntimeError, RuntimeError("worker"), None)
        self.new_public.refresh_from_db()
        self.assertEqual(self.new_public.processing_status, "FAILED")
        Video.objects.filter(pk=self.new_public.pk).update(processing_error="detail")
        hls_job_failed(job, None, RuntimeError, RuntimeError("again"), None)
        self.new_public.refresh_from_db()
        self.assertEqual(self.new_public.processing_error, "detail")

    def test_metadata_cache_is_used_and_invalidated_after_commit(self):
        cache.clear()
        self.authenticate()
        self.get_video_list()
        self.assertIsNotNone(cache.get(f"video:{self.new_public.pk}"))
        with self.captureOnCommitCallbacks(execute=True):
            self.new_public.title = "Changed"
            self.new_public.save()
        self.assertIsNone(cache.get(f"video:{self.new_public.pk}"))

    def test_cached_video_becoming_private_is_not_exposed(self):
        self.authenticate()
        self.get_video_list()
        self.new_public.visibility = "PRIVATE"
        self.new_public.save()
        self.assertEqual(
            self.client.get(f"/api/video/{self.new_public.pk}/").status_code, 404
        )

    @override_settings(VIDEO_ENQUEUE_HLS_JOBS=True)
    @patch("django_rq.enqueue")
    def test_metadata_save_does_not_enqueue(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            self.new_public.title = "Changed"
            self.new_public.save()
        enqueue.assert_not_called()

    @override_settings(VIDEO_ENQUEUE_HLS_JOBS=True)
    @patch("django_rq.enqueue")
    def test_source_change_enqueues_once(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            self.new_public.video_file = "videos/replacement.mp4"
            self.new_public.save(update_fields=["video_file"])
            self.new_public.save()
        self.assertEqual(enqueue.call_count, 1)
        self.new_public.refresh_from_db()
        self.assertEqual(
            enqueue.call_args.kwargs["job_id"], str(self.new_public.hls_job_id)
        )

    @override_settings(VIDEO_ENQUEUE_HLS_JOBS=True)
    @patch("django_rq.enqueue")
    def test_rolled_back_upload_does_not_enqueue(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            with transaction.atomic():
                self.create_video(title="Rollback")
                transaction.set_rollback(True)
        enqueue.assert_not_called()

    @patch("django_rq.enqueue", side_effect=DuplicateJobError("duplicate"))
    def test_duplicate_queue_job_is_ignored(self, enqueue):
        enqueue_hls_job(self.new_public.pk, str(self.new_public.hls_job_id))
        self.new_public.refresh_from_db()
        self.assertNotEqual(self.new_public.processing_status, "FAILED")

    @patch("django_rq.enqueue", side_effect=ConnectionError("offline"))
    def test_queue_failure_is_recorded(self, enqueue):
        with self.assertLogs("video_app.signals", level="ERROR"):
            enqueue_hls_job(self.new_public.pk, str(self.new_public.hls_job_id))
        self.new_public.refresh_from_db()
        self.assertEqual(self.new_public.processing_status, "FAILED")

    @patch("video_app.hls.execute_ffmpeg")
    def test_stale_job_does_not_convert(self, execute):
        self.assertTrue(process_video_to_hls(self.new_public.pk, "stale-job"))
        execute.assert_not_called()

    @patch("video_app.hls.execute_ffmpeg")
    def test_completed_job_is_not_repeated(self, execute):
        self.new_public.processing_status = "READY"
        self.new_public.save(update_fields=["processing_status"])
        self.assertTrue(
            process_video_to_hls(self.new_public.pk, str(self.new_public.hls_job_id))
        )
        execute.assert_not_called()

    def test_upload_extensions_are_validated(self):
        self.new_public.video_file = "videos/malware.exe"
        with self.assertRaises(ValidationError):
            self.new_public.full_clean()

    def test_thumbnail_is_protected_and_available(self):
        path = self.media_root / self.new_public.thumbnail_file.name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")
        url = f"/api/video/{self.new_public.pk}/thumbnail/"
        self.assertEqual(self.client.get(url).status_code, 401)
        self.authenticate()
        response = self.client.get(url)
        self.assertEqual(b"".join(response.streaming_content), b"image")
        self.assertIn("no-store", response["Cache-Control"])

    def test_raw_media_is_not_publicly_served(self):
        self.assertEqual(
            self.client.get("/media/videos/public-video.mp4").status_code, 404
        )

    @override_settings(VIDEO_HLS_OUTPUT_DIR="../outside")
    def test_output_root_cannot_escape_media(self):
        with self.assertLogs("video_app.hls", level="ERROR"):
            self.assertFalse(process_video_to_hls(self.new_public.pk))

    @patch("video_app.tasks.process_video_to_hls", return_value=False)
    def test_failed_conversion_marks_rq_job_failed(self, process):
        with self.assertRaises(RuntimeError):
            convert_video_to_hls(self.new_public.pk)

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
        self.assertEqual(
            categories[self.new_public.title], self.new_public.get_genre_display()
        )
        self.assertEqual(
            categories[self.old_public.title], self.old_public.get_genre_display()
        )

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
        self.assertEqual(response.status_code, 200)
        fields = set("id created_at title description thumbnail_url category".split())
        self.assertEqual(set(response.data), fields)
        self.assertEqual(response.data["category"], self.new_public.get_genre_display())
        thumbnail = f"http://testserver/api/video/{self.new_public.pk}/thumbnail/"
        self.assertEqual(response.data["thumbnail_url"], thumbnail)

    def test_hls_manifest_endpoint_serves_playlist(self):
        self.authenticate()
        self.create_hls_files(self.new_public)

        response = self.client.get(f"/api/video/{self.new_public.pk}/480p/index.m3u8")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.headers["Content-Type"], "application/vnd.apple.mpegurl"
        )

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
        segment = self.client.get(
            f"/api/video/{self.new_public.pk}/480p/segment_000.ts/"
        )

        self.assertEqual(manifest.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(segment.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_hls_endpoints_return_404_for_invalid_inputs(self):
        self.authenticate()
        self.create_hls_files(self.new_public)
        root = f"/api/video/{self.new_public.pk}"
        urls = [
            f"{root}/360p/index.m3u8",
            f"{root}/720p/index.m3u8",
            f"{root}/480p/..bad.ts/",
            f"/api/video/{self.private_video.pk}/480p/index.m3u8",
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 404)

    @override_settings(VIDEO_ENQUEUE_HLS_JOBS=True)
    @patch("django_rq.enqueue")
    def test_video_save_enqueues_hls_job(self, enqueue):
        with self.captureOnCommitCallbacks(execute=True):
            video = self.create_video(title="Queued Video")

        enqueue.assert_called_with(
            convert_video_to_hls,
            video.pk,
            str(video.hls_job_id),
            job_id=str(video.hls_job_id),
            unique=True,
            on_failure=hls_job_failed,
        )

    @patch("video_app.hls.probe_video_height", return_value=720)
    @patch("video_app.hls.execute_ffmpeg")
    def test_hls_processing_creates_allowed_resolutions(self, execute_ffmpeg, probe):
        execute_ffmpeg.side_effect = create_fake_hls_output
        self.assertTrue(process_video_to_hls(self.new_public.pk))
        self.new_public.refresh_from_db()
        self.assertEqual(self.new_public.processing_status, "READY")
        root = self.media_root / "hls" / str(self.new_public.pk)
        for quality in ("480p", "720p"):
            self.assertTrue((root / quality).exists())
        self.assertFalse((root / "1080p").exists())
        self.assertEqual(probe.call_count, 1)
        segment = f"/api/video/{self.new_public.pk}/480p/segment_000.ts/"
        self.assertIn(segment, (root / "480p" / "index.m3u8").read_text())

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
        video = self.create_video(
            title="Real FFmpeg", video_file="videos/real-input.mp4"
        )
        self.assertTrue(process_video_to_hls(video.pk))
        video.refresh_from_db()
        self.assertEqual(video.processing_status, "READY")
        playlist = self.media_root / "hls" / str(video.pk) / "480p" / "index.m3u8"
        self.assertTrue(playlist.is_file())


def create_fake_hls_output(command):
    playlist = Path(command[-1])
    playlist.write_text("#EXTM3U\nsegment_000.ts\n")
    segment_pattern = command[command.index("-hls_segment_filename") + 1]
    Path(segment_pattern.replace("%03d", "000")).write_bytes(b"segment")


def create_tiny_mp4(source_path):
    command = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        "testsrc=size=640x480:rate=1",
        "-t",
        "1",
        str(source_path),
    ]
    subprocess.run(command, check=True, capture_output=True, text=True)
