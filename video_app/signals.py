"""Commit hooks prevent rolled-back uploads from spawning jobs or evicting cache."""

import logging
import uuid

import django_rq
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from rq.exceptions import DuplicateJobError

from .models import Video
from .tasks import convert_video_to_hls, hls_job_failed
from .utils import invalidate_video_cache

logger = logging.getLogger(__name__)


# A new upload may keep the same filename; _committed detects unsaved file data.
@receiver(pre_save, sender=Video)
def track_source_change(sender, instance, update_fields=None, **kwargs):
    if update_fields is not None and "video_file" not in update_fields:
        instance._source_changed = False
        return
    old = (
        Video.objects.filter(pk=instance.pk)
        .values_list("video_file", flat=True)
        .first()
    )
    instance._source_changed = bool(instance.video_file) and (
        old != instance.video_file.name or not instance.video_file._committed
    )
    if instance._source_changed:
        reset_processing(instance)


def reset_processing(instance):
    # A new ID lets workers ignore queued jobs for an older source file.
    instance.hls_job_id = uuid.uuid4()
    instance.processing_status = "PENDING"
    instance.processing_error = ""
    instance.hls_output_path = ""


@receiver(post_save, sender=Video)
def enqueue_hls_processing(sender, instance, **kwargs):
    # Workers and cache readers must only see changes that were committed.
    transaction.on_commit(lambda: invalidate_video_cache(instance.pk))
    if settings.VIDEO_ENQUEUE_HLS_JOBS and getattr(instance, "_source_changed", False):
        job_id = str(instance.hls_job_id)
        transaction.on_commit(lambda: enqueue_hls_job(instance.pk, job_id))


@receiver(post_delete, sender=Video)
def clear_deleted_video_cache(sender, instance, **kwargs):
    transaction.on_commit(lambda: invalidate_video_cache(instance.pk))


# RQ uniqueness prevents repeated saves from queuing the same upload twice.
def enqueue_hls_job(video_id, job_id):
    try:
        django_rq.enqueue(
            convert_video_to_hls, video_id, job_id, job_id=job_id, unique=True,
            on_failure=hls_job_failed
        )
    except DuplicateJobError:
        return
    except Exception:
        logger.exception("Could not enqueue HLS job for video %s", video_id)
        Video.objects.filter(pk=video_id, hls_job_id=job_id).update(
            processing_status="FAILED",
            processing_error="Queue unavailable; upload again to retry.",
        )
