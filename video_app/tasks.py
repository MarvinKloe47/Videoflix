from .hls import process_video_to_hls


def convert_video_to_hls(video_id, job_id=None):
    if not process_video_to_hls(video_id, job_id):
        raise RuntimeError(
            f"HLS conversion failed for video {video_id}; see processing_error"
        )
    return True


def hls_job_failed(job, connection, exception_type, exception, traceback):
    from .models import Video

    Video.objects.filter(pk=job.args[0], hls_job_id=job.id).exclude(
        processing_status__in=["READY", "FAILED"]
    ).update(processing_status="FAILED",
             processing_error="RQ worker failed; inspect worker logs.")
