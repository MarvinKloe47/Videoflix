
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .hls import HLS_RESOLUTIONS, get_hls_file_path
from .models import Video
from .serializers import VideoSerializer


class VideoListView(generics.ListAPIView):
    queryset = Video.objects.filter(
        visibility="PUBLIC"
    ).order_by("-created_at")

    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class VideoDetailView(generics.RetrieveAPIView):
    queryset = Video.objects.filter(visibility="PUBLIC")
    serializer_class = VideoSerializer
    permission_classes = [IsAuthenticated]


class HLSManifestView(APIView):
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


def get_public_video(movie_id):
    return get_object_or_404(Video, pk=movie_id, visibility="PUBLIC")


def get_hls_asset(video, resolution, filename):
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
