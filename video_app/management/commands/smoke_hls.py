"""Exercise an actual admin upload, Redis, RQ worker and protected HLS delivery."""

import shutil
import subprocess
import tempfile
import time
import uuid
from pathlib import Path

import django_rq
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.models import User
from video_app.hls import get_hls_output_root
from video_app.models import Video


class Command(BaseCommand):
    help = "Real 1080p admin upload -> RQ -> FFmpeg -> authenticated HLS smoke test"

    def handle(self, *args, **options):
        marker = f"smoke-{uuid.uuid4().hex}"
        user = User.objects.create_superuser(f"{marker}@example.com", uuid.uuid4().hex)
        try:
            run_smoke(user, marker)
            self.stdout.write(self.style.SUCCESS(
                "PASS: upload, cache, RQ, 3 qualities, auth"))
        finally:
            clean_fixture(marker)
            user.delete()


def run_smoke(user, marker):
    verify_redis(marker)
    with tempfile.TemporaryDirectory() as directory:
        upload_fixture(user, marker, Path(directory))
    video = Video.objects.get(title=marker)
    wait_for_conversion(video)
    verify_delivery(user, video)


def verify_redis(marker):
    if not django_rq.get_connection().ping():
        raise CommandError("Redis queue unavailable")
    cache.set(marker, "ok", 60)
    if cache.get(marker) != "ok":
        raise CommandError("Redis cache unavailable")
    cache.delete(marker)


def upload_fixture(user, marker, directory):
    source = directory / "source.mp4"
    create_source(source)
    client = Client()
    client.force_login(user)
    response = client.post(
        "/admin/video_app/video/add/",
        upload_data(marker, source),
        HTTP_HOST="localhost",
    )
    if response.status_code != 302:
        raise CommandError(f"Admin upload failed: HTTP {response.status_code}")


def create_source(source):
    subprocess.run([settings.FFMPEG_BINARY, "-y", "-f", "lavfi", "-i",
                    "color=c=blue:s=1920x1080:r=1", "-t", "1", str(source)],
                   check=True, capture_output=True, timeout=30)


def upload_data(marker, source):
    return {
        "title": marker,
        "description": "Temporary integration fixture",
        "genre": "ACTION",
        "visibility": "PUBLIC",
        "processing_status": "PENDING",
        "video_file": SimpleUploadedFile("smoke.mp4", source.read_bytes(), "video/mp4"),
        "thumbnail_file": SimpleUploadedFile("smoke.png", b"thumbnail", "image/png"),
    }


def wait_for_conversion(video):
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        video.refresh_from_db()
        if video.processing_status == "READY":
            return
        if video.processing_status == "FAILED":
            raise CommandError(f"Worker failed: {video.processing_error}")
        time.sleep(1)
    raise CommandError("Worker did not finish within 60 seconds")


def verify_delivery(user, video):
    client = APIClient()
    root = f"/api/video/{video.pk}"
    if client.get(f"{root}/480p/index.m3u8", HTTP_HOST="localhost").status_code != 401:
        raise CommandError("Anonymous HLS access was not denied")
    client.cookies["access_token"] = str(RefreshToken.for_user(user).access_token)
    for quality in ("480p", "720p", "1080p"):
        verify_quality(client, f"{root}/{quality}")


def verify_quality(client, root):
    response = client.get(f"{root}/index.m3u8", HTTP_HOST="localhost")
    if response.status_code != 200:
        raise CommandError(f"Missing playlist: {root}")
    playlist = b"".join(response.streaming_content).decode()
    segment = next(
        line for line in playlist.splitlines() if line and not line.startswith("#")
    )
    response = client.get(segment, HTTP_HOST="localhost")
    if response.status_code != 200 or not b"".join(response.streaming_content):
        raise CommandError("Missing or empty HLS segment")


def clean_fixture(marker):
    for video in Video.objects.filter(title=marker):
        root = get_hls_output_root(video)
        video.video_file.delete(save=False)
        video.thumbnail_file.delete(save=False)
        if root.is_relative_to(Path(settings.MEDIA_ROOT).resolve()):
            shutil.rmtree(root, ignore_errors=True)
        video.delete()
