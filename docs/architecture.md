# Implemented architecture

The API and PDF in this directory define the contract; requirements.md is a derived
index. Current evidence and limitations are in ABGABE_CHECK.md.

A separately maintained Vanilla JavaScript frontend calls Django REST Framework.
Django stores users and video metadata in PostgreSQL. Redis database 0 runs RQ;
database 1 caches public video metadata for 60 seconds. Authentication and current
visibility are checked before metadata/file delivery; cache entries are not HTTP
responses and contain no JWTs. Cache failures fall back to the database.

`auth_app` owns the email-based User and API serializers/views. Dictionary helpers
live in utils.py; views construct Responses. CookieJWTAuthentication checks token
validity, password revocation, refresh-session blacklist and CSRF for writes.
Refresh separately checks active user/password state. Logout blacklists the session
and expires both cookies. Login/refresh/logout also require CSRF when unauthenticated.

services.py builds activation/reset links and multipart messages from escaped HTML
and plain-text templates. Logo bytes are attached inline by CID. Message design
comes from the supplied frontend references. Reset validity text reflects Django's
actual timeout rather than changing working token behavior to match sample text.

`video_app` returns a flat PUBLIC list in descending creation order. Thumbnails and
HLS files require authenticated access and current public visibility. Original MP4s
are not served. Genre grouping and manual quality selection belong to the frontend.

pre_save identifies actual source changes and assigns a new UUID. post_save queues
RQ and cache invalidation only after transaction commit. RQ uniqueness plus a row
lock serializes conversion and skips stale/finished jobs. The long conversion
transaction keeps PROCESSING invisible until completion and can block concurrent
editing of the same video. This behavior is documented, not silently refactored.

FFprobe checks source height. FFmpeg emits supported 480p/720p/1080p versions without
upscaling; under-480p files fail. Paths stay within MEDIA_ROOT. Playlists reference
only protected segment URLs. Only READY assets are served. Queue/conversion failures
are visible in processing_status/processing_error and RQ logs.

core/settings.py supports the existing local profile. The isolated Academy settings
module maps official environment names and static volume paths. The original
Academy Dockerfile/Compose/entrypoint remain byte-identical; the separate override
selects an email-aware bootstrap and foreground web/worker processes behind a
one-shot migration gate. Sources are staged by allowlist; runtime secrets stay
outside that image context. Existing database/media volumes are not reused across
profiles. No schema migration was needed for cleanup.

Tests use PostgreSQL. Unit/API tests isolate outbound email and metadata cache;
the container smoke test deliberately uses real Redis, RQ and FFmpeg. Browser tests
use real cookie-authenticated API/HLS and explicitly marked mocked error states.
The Git repository excludes the course frontend, virtual environments and local
runtime/media/cache files. Public deployment remains a separate configuration step.
