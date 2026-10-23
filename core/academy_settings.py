"""Own settings adapter for the unchanged Academy Docker reference files."""

import os

from .settings import *  # noqa: F403
from .settings import BASE_DIR, CACHES, CSRF_TRUSTED_ORIGINS, DEBUG

STATIC_ROOT = BASE_DIR / "static"
CACHES = {
    "default": {
        **CACHES["default"],
        "LOCATION": os.getenv(
            "REDIS_LOCATION", os.getenv("CACHE_URL", "redis://redis:6379/1")
        ),
    }
}
CSRF_TRUSTED_ORIGINS = list(filter(
    None,
    os.getenv("CSRF_TRUSTED_ORIGINS", ",".join(CSRF_TRUSTED_ORIGINS)).split(","),
))
# Public Academy credentials are permitted only for local submission/development.
ACADEMY_DEFAULT_ADMIN = DEBUG
