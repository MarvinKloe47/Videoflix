from django.urls import path

from .views import (
    HLSManifestView,
    HLSSegmentView,
    VideoDetailView,
    VideoListView,
    VideoThumbnailView,
)

urlpatterns = [
    path("<int:pk>/thumbnail/", VideoThumbnailView.as_view(), name="video-thumbnail"),
    path("", VideoListView.as_view(), name="video-list"),
    path(
        "<int:movie_id>/<str:resolution>/index.m3u8",
        HLSManifestView.as_view(),
        name="hls-manifest",
    ),
    path(
        "<int:movie_id>/<str:resolution>/<str:segment>/",
        HLSSegmentView.as_view(),
        name="hls-segment",
    ),
    path("<int:pk>/", VideoDetailView.as_view(), name="video-detail"),
]
