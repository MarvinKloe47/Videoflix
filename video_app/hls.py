"""Hold the source row lock through conversion to serialize competing RQ jobs.

PROCESSING remains uncommitted until READY/FAILED; readers only serve READY assets.
"""

import json
import logging
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.db import transaction

from .models import Video

logger = logging.getLogger(__name__)

HLS_RESOLUTIONS = {
    "480p": 480,
    "720p": 720,
    "1080p": 1080,
}


@transaction.atomic
def process_video_to_hls(video_id, job_id=None):
    video = Video.objects.select_for_update().filter(pk=video_id).first()
    if video is None:
        return True
    if job_id and (
        str(video.hls_job_id) != job_id or video.processing_status == "READY"
    ):
        return True
    mark_processing(video)
    return run_conversion(video)


def run_conversion(video):
    try:
        output_root = prepare_output_root(video)
        resolutions = get_target_resolutions(video)
        if not resolutions:
            raise ValueError("No matching HLS resolution for source video.")
        for resolution, height in resolutions.items():
            convert_resolution(video, output_root, resolution, height)
    except Exception as error:
        logger.exception("HLS processing failed for video %s", video.pk)
        mark_failed(video, error)
        return False
    mark_ready(video, output_root)
    return True


def mark_processing(video):
    video.processing_status = "PROCESSING"
    video.processing_error = ""
    video.save(update_fields=["processing_status", "processing_error"])


def mark_failed(video, error):
    video.processing_status = "FAILED"
    video.processing_error = (getattr(error, "stderr", None) or str(error))[-2000:]
    video.save(update_fields=["processing_status", "processing_error"])


def mark_ready(video, output_root):
    video.processing_status = "READY"
    video.processing_error = ""
    video.hls_output_path = str(output_root.relative_to(settings.MEDIA_ROOT))
    video.save(
        update_fields=["processing_status", "processing_error", "hls_output_path"]
    )


def prepare_output_root(video):
    output_root = get_hls_output_root(video)
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    return output_root


def get_hls_output_root(video):
    media = Path(settings.MEDIA_ROOT).resolve()
    root = (media / settings.VIDEO_HLS_OUTPUT_DIR / str(video.pk)).resolve()
    if not root.is_relative_to(media) or root == media:
        raise ValueError("HLS output must stay inside MEDIA_ROOT")
    return root


def get_target_resolutions(video):
    source_height = probe_video_height(video.video_file.path)
    return {
        name: height
        for name, height in HLS_RESOLUTIONS.items()
        if height <= source_height
    }


def probe_video_height(source_path):
    command = build_ffprobe_command(source_path)
    result = subprocess.run(
        command, capture_output=True, text=True, check=True, timeout=30
    )
    data = json.loads(result.stdout)
    stream = get_video_stream(data)
    return int(stream["height"])


def build_ffprobe_command(source_path):
    return [
        settings.FFPROBE_BINARY,
        "-v",
        "error",
        "-protocol_whitelist", "file,pipe",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=height",
        "-of",
        "json",
        source_path,
    ]


def get_video_stream(data):
    streams = data.get("streams", [])
    if not streams:
        raise ValueError("Source file has no video stream.")
    return streams[0]


def convert_resolution(video, output_root, resolution, height):
    output_dir = output_root / resolution
    output_dir.mkdir(parents=True, exist_ok=True)
    command = build_ffmpeg_command(video.video_file.path, output_dir, height)
    execute_ffmpeg(command)
    rewrite_manifest_segments(video, output_dir / "index.m3u8", resolution)


def build_ffmpeg_command(source_path, output_dir, height):
    return [settings.FFMPEG_BINARY, "-y", "-protocol_whitelist", "file,pipe",
            "-i", source_path,
            "-vf", f"scale=-2:{height}", "-c:v", "libx264", "-c:a", "aac",
            "-hls_time", "4", "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(output_dir / "segment_%03d.ts"),
            str(output_dir / "index.m3u8")]


def execute_ffmpeg(command):
    subprocess.run(command, capture_output=True, text=True, check=True, timeout=900)


def rewrite_manifest_segments(video, manifest_path, resolution):
    lines = manifest_path.read_text().splitlines()
    rewritten = [rewrite_manifest_line(video, resolution, line) for line in lines]
    manifest_path.write_text("\n".join(rewritten) + "\n")


def rewrite_manifest_line(video, resolution, line):
    if not line or line.startswith("#"):
        return line
    segment = Path(line).name
    return f"/api/video/{video.pk}/{resolution}/{segment}/"


def get_hls_file_path(video, resolution, filename):
    root = get_hls_output_root(video).resolve()
    target = (root / resolution / filename).resolve()
    if not is_safe_hls_path(root, target):
        return None
    return target


def is_safe_hls_path(root, target):
    try:
        target.relative_to(root)
    except ValueError:
        return False
    return target.is_file()
