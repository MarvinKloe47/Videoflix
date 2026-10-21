from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers


class FrontendCORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.headers.get("Origin")
        response = (
            HttpResponse()
            if request.method == "OPTIONS"
            else self.get_response(request)
        )
        patch_vary_headers(response, ("Origin", "Cookie"))
        set_cors_headers(response, origin)
        if request.path.startswith(("/api/", "/media/")):
            response["Cache-Control"] = "private, no-store"
        return response


def set_cors_headers(response, origin):
    if origin in settings.CSRF_TRUSTED_ORIGINS:
        response["Access-Control-Allow-Origin"] = origin
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Allow-Headers"] = "Content-Type, X-CSRFToken"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
