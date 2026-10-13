
from django.conf import settings
from django.db import models


class Video(models.Model):
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
    video_file = models.FileField(upload_to="videos/")
    thumbnail_file = models.FileField(upload_to="thumbnails/")

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

    def __str__(self):
        return self.title
