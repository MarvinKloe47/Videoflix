"""Keep public URL paths and route names stable when moving code into api/."""

from django.test import SimpleTestCase
from django.urls import resolve, reverse

AUTH = "auth_app.api.views"
VIDEO = "video_app.api.views"
ROUTES = [
    ("/api/register/", "register", AUTH, {}),
    ("/api/login/", "login", AUTH, {}),
    ("/api/logout/", "logout", AUTH, {}),
    ("/api/token/refresh/", "token-refresh", AUTH, {}),
    ("/api/password_reset/", "password-reset", AUTH, {}),
    ("/api/csrf/", "csrf", AUTH, {}),
    ("/api/user/", "user-info", AUTH, {}),
    ("/api/activate/MQ/token/", "activate", AUTH, {"uidb64": "MQ", "token": "token"}),
    ("/api/password_confirm/MQ/token/", "password-reset-confirm", AUTH,
     {"uidb64": "MQ", "token": "token"}),
    ("/api/video/", "video-list", VIDEO, {}),
    ("/api/video/1/", "video-detail", VIDEO, {"pk": 1}),
    ("/api/video/1/thumbnail/", "video-thumbnail", VIDEO, {"pk": 1}),
    ("/api/video/1/480p/index.m3u8", "hls-manifest", VIDEO,
     {"movie_id": 1, "resolution": "480p"}),
    ("/api/video/1/480p/segment_000.ts/", "hls-segment", VIDEO,
     {"movie_id": 1, "resolution": "480p", "segment": "segment_000.ts"}),
]


class ApiRouteTests(SimpleTestCase):
    def test_paths_and_names_are_unchanged(self):
        for path, name, module, kwargs in ROUTES:
            with self.subTest(path=path):
                match = resolve(path)
                self.assertEqual(match.url_name, name)
                self.assertEqual(match.func.view_class.__module__, module)
                self.assertEqual(reverse(name, kwargs=kwargs), path)
