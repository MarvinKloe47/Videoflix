import logging

import django_rq
from django.conf import settings
from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Video
from .tasks import convert_video_to_hls

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Video)
def enqueue_hls_processing(sender, instance, created, update_fields=None, **kwargs):
    if not should_enqueue_hls_job(instance, update_fields):
        return

    transaction.on_commit(lambda: enqueue_hls_job(instance.pk))


def enqueue_hls_job(video_id):
    try:
        django_rq.enqueue(convert_video_to_hls, video_id)
    except Exception:
        logger.exception("Could not enqueue HLS job for video %s", video_id)


def should_enqueue_hls_job(instance, update_fields):
    if not settings.VIDEO_ENQUEUE_HLS_JOBS:
        return False
    if not instance.video_file:
        return False
    return update_fields is None or "video_file" in update_fields