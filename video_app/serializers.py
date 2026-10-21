from rest_framework import serializers
from rest_framework.reverse import reverse

from .models import Video
from .utils import video_metadata


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = [
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "category",
        ]

    def to_representation(self, instance):
        data = dict(video_metadata(instance))
        data["created_at"] = serializers.DateTimeField().to_representation(
            data["created_at"]
        )
        data["thumbnail_url"] = self.thumbnail_url(instance)
        return data

    def thumbnail_url(self, instance):
        if instance.thumbnail_file:
            return reverse("video-thumbnail", args=[instance.pk],
                           request=self.context.get("request"))
        return None
