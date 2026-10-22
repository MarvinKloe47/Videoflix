from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

urlpatterns = [
    path("admin/", admin.site.urls),
    path("django-rq/", include("django_rq.urls")),
    path("api/", include("auth_app.api.urls")),
    path("api/video/", include("video_app.api.urls")),
]

# Local container setup: production should serve STATIC_ROOT with a reverse proxy.

urlpatterns += [
    re_path(r"^static/(?P<path>.*)$", serve, {"document_root": settings.STATIC_ROOT})
]
