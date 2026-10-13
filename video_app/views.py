
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

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
