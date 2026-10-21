import logging

from django.core.cache import cache
from django.http import Http404
from django.shortcuts import get_object_or_404

from .hls import HLS_RESOLUTIONS, get_hls_file_path
from .models import Video

logger = logging.getLogger(__name__)


def invalidate_video_cache(video_id):
    try:
        cache.delete(f"video:{video_id}")
    except Exception:
        logger.warning("Metadata cache unavailable", exc_info=True)


def cached_video_metadata(video):
    try:
        return cache.get_or_set(f"video:{video.pk}", lambda: video_metadata(video), 60)
    except Exception:
        logger.warning("Metadata cache unavailable", exc_info=True)
        return video_metadata(video)


def video_metadata(video):
    return {
        "id": video.pk,
        "created_at": video.created_at,
        "title": video.title,
        "description": video.description,
        "category": video.get_genre_display(),
    }


def get_public_video(movie_id):
    return get_object_or_404(Video, pk=movie_id, visibility="PUBLIC")


def get_hls_asset(video, resolution, filename):
    if video.processing_status != "READY":
        raise Http404("Video is not ready.")
    validate_resolution(resolution)
    file_path = get_hls_file_path(video, resolution, filename)
    if file_path is None:
        raise Http404("HLS asset not found.")
    return file_path


def validate_resolution(resolution):
    if resolution not in HLS_RESOLUTIONS:
        raise Http404("Resolution not found.")


def validate_segment_name(segment):
    if "/" in segment or "\\" in segment or ".." in segment:
        raise Http404("Segment not found.")
    if not segment.endswith(".ts"):
        raise Http404("Segment not found.")
