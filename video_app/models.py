import uuid

from django.core.validators import FileExtensionValidator
from django.db import models


class Video(models.Model):
    PROCESSING_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PROCESSING", "Processing"),
        ("READY", "Ready"),
        ("FAILED", "Failed"),
    ]

    VISIBILITY_CHOICES = [
        ("PUBLIC", "Public"),
        ("PRIVATE", "Private"),
    ]

    GENRE_CHOICES = [
        ("ACTION", "Action"),
        ("COMEDY", "Comedy"),
        ("DRAMA", "Drama"),
        ("HORROR", "Horror"),
        ("ROMANCE", "Romance"),
        ("SCI-FI", "Sci-Fi"),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255)
    description = models.TextField(max_length=500)
    video_file = models.FileField(
        upload_to="videos/", validators=[FileExtensionValidator(["mp4"])]
    )
    thumbnail_file = models.FileField(
        upload_to="thumbnails/",
        validators=[FileExtensionValidator(["jpg", "jpeg", "png", "webp"])],
    )

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default="PUBLIC",
    )

    genre = models.CharField(
        max_length=10,
        choices=GENRE_CHOICES,
        default="ACTION",
    )

    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default="PENDING",
    )
    processing_error = models.TextField(blank=True)
    hls_output_path = models.CharField(max_length=255, blank=True)

    hls_job_id = models.UUIDField(default=uuid.uuid4, editable=False)

    def save(self, *args, **kwargs):
        fields = kwargs.get("update_fields")
        if fields and "video_file" in fields:
            kwargs["update_fields"] = set(fields) | {
                "hls_job_id",
                "processing_status",
                "processing_error",
                "hls_output_path",
            }
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.title
