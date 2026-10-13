
from rest_framework import serializers
from .models import Video


class VideoSerializer(serializers.ModelSerializer):
    category = serializers.CharField(
        source="genre",
        read_only=True
    )

    thumbnail_url = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            "id",
            "created_at",
            "title",
            "description",
            "thumbnail_url",
            "video_url",
            "category",
        ]

    def get_thumbnail_url(self, obj):
        if obj.thumbnail_file:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(
                    obj.thumbnail_file.url
                )

            return obj.thumbnail_file.url

        return None

    def get_video_url(self, obj):
        if obj.video_file:
            request = self.context.get("request")

            if request:
                return request.build_absolute_uri(
                    obj.video_file.url
                )

            return obj.video_file.url

        return None
