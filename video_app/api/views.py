from django.http import FileResponse, Http404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from ..models import Video
from ..utils import get_hls_asset, get_public_video, validate_segment_name
from .serializers import VideoSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.filter(visibility="PUBLIC").order_by("-created_at")

    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class VideoDetailView(generics.RetrieveAPIView):
    queryset = Video.objects.filter(visibility="PUBLIC")
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class HLSManifestView(APIView):
    # Both playlists and segments require authentication and current visibility.
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution):
        video = get_public_video(movie_id)
        file_path = get_hls_asset(video, resolution, "index.m3u8")
        return FileResponse(
            open(file_path, "rb"),
            content_type="application/vnd.apple.mpegurl",
        )


class HLSSegmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, movie_id, resolution, segment):
        video = get_public_video(movie_id)
        validate_segment_name(segment)
        file_path = get_hls_asset(video, resolution, segment)
        return FileResponse(open(file_path, "rb"), content_type="video/MP2T")


class VideoThumbnailView(APIView):
    # Serve thumbnails through the same access checks as their videos.
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        video = get_public_video(pk)
        if not video.thumbnail_file:
            raise Http404("Thumbnail not found.")
        try:
            return FileResponse(video.thumbnail_file.open("rb"))
        except FileNotFoundError:
            raise Http404("Thumbnail not found.")
