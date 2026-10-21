from .settings import *  # noqa: F403

CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
VIDEO_ENQUEUE_HLS_JOBS = False
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
