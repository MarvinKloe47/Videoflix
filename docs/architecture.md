# Implemented architecture

The API and PDF in this directory define the contract; requirements.md is a derived
index. Current evidence and limitations are in ABGABE_CHECK.md.

A separately maintained Vanilla JavaScript frontend calls Django REST Framework.
Django stores users and video metadata in PostgreSQL. Redis database 0 runs RQ;
database 1 caches public video metadata for 60 seconds. Authentication and current
visibility are checked before metadata/file delivery; cache entries are not HTTP
responses and contain no JWTs. Cache failures fall back to the database.

`auth_app` owns the email-based User; API serializers/views/URLs are in `auth_app/api/`.
Video API modules are in `video_app/api/`. Services, models, tasks, signals and
shared helpers stay outside api/. Dictionary helpers live in utils.py; views
construct Responses. CookieJWTAuthentication checks token
validity, password revocation, refresh-session blacklist and CSRF for writes.
Refresh separately checks active user/password state. Logout blacklists the session
and expires both cookies. Login/refresh/logout are explicit CSRF exceptions for
the supplied frontend; other protected writes retain authentication-level CSRF.

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

The root Academy Dockerfile, Compose file and original entrypoint are unchanged
copies of the upstream snapshot. Compose automatically loads our separate override,
which builds directly from the checkout. One init container generates project
migrations, migrates PostgreSQL and collects static files before web/worker start.
The own entrypoint bypasses the upstream username-based admin bootstrap and calls
the email-aware bootstrap_admin management command after migrate. Explicit env
credentials create an active superuser once; existing passwords/roles are retained.
In the local Academy DEBUG profile only, absent credentials use the documented
upstream test admin; production requires explicit credentials. Partial/conflicting
credentials are handled explicitly. Django's built-in
createsuperuser remains available. Email-specific admin forms inherit Django's
password handling and permissions; the User admin exposes account management.

The mentor requires empty project migration packages in the submitted repository.
Only their __init__.py files are versioned. Initial migrations are generated inside
the init container in the shared source mount, before dependencies on the custom
User are applied. Generated migrations must be retained with their database.
This is a fresh-install submission profile, not a migration path for existing data.
New project-scoped volumes keep both previous stacks' data separate and untouched.

core.academy_settings maps official environment names and static paths without
changing the application's auth/video logic. Runtime secrets are in ignored .env;
no host Python or PowerShell preparation is needed. Setup and known limitations
are described in docker/academy/README.md.

Tests use PostgreSQL. Unit/API tests isolate outbound email and metadata cache;
the container smoke test deliberately uses real Redis, RQ and FFmpeg. Browser tests
use real cookie-authenticated API/HLS and explicitly marked mocked error states.
The Git repository excludes the course frontend, virtual environments and local
runtime/media/cache files. Public deployment remains a separate configuration step.

## Frontend connection and API extensions

Frontend requests must use `credentials: 'include'`, including playlist and segment
requests. Login, refresh and logout do not require a CSRF header or a prior admin
session. `/api/csrf/` remains available for protected writes and existing clients.
Tokens remain in HttpOnly cookies;
the frontend must not copy JWTs into Local Storage. SameSite=Lax requires the same
site: do not mix localhost with 127.0.0.1. Allowed origins are configured through
FRONTEND_ORIGINS in the root settings or CSRF_TRUSTED_ORIGINS in the Academy adapter.

The contract in `APIDoku_Videoflix (1).txt` remains authoritative. Existing additions:

| Method | Route | Purpose |
|---|---|---|
| GET | /api/csrf/ | CSRF cookie and masked token |
| GET | /api/user/ | Authenticated user information |
| GET | /api/video/id/ | Authenticated public-video details |
| GET | /api/video/id/thumbnail/ | Protected thumbnail |

The default backend host port is 8000, configurable through HTTP_PORT. The
separate frontend must use that port and the same hostname. The default Compose
project is videoflix-submission. Previous profiles and host preparation scripts
have been retired; do not attach their old volumes to this fresh-schema setup.

Staff video uploads use `/admin/video_app/video/add/` with an MP4 and a JPG/PNG/WebP
thumbnail. Frontend activation/reset URLs are set with FRONTEND_ACTIVATION_URL and
FRONTEND_PASSWORD_RESET_URL. SMTP is the default and requires provider EMAIL_*
settings and a verified sender.
The console backend is an explicit local-only override; never version credentials.

## CSRF and frontend compatibility

The supplied Academy frontend does not send X-CSRFToken. Only the explicit
csrf_protect decorators on login, token refresh and logout were removed.
Those APIViews already disable authentication classes, so an expired access
cookie does not block refresh and no session login is required. Django's global
CsrfViewMiddleware, admin form protection and CookieJWTAuthentication.enforce_csrf
for other authenticated writes remain enabled. Read-only protected video/HLS
requests still require a valid, active, non-revoked JWT and public visibility.

This compatibility exception weakens CSRF protection at those three endpoints.
HttpOnly prevents JavaScript from reading a cookie; it does not prevent a browser
from sending it with a forged request. SameSite=Lax limits cross-site cookie
sending but does not cover every same-site attack or login CSRF. CORS restricts
browser access to responses, not every forged request. Session blacklist checks,
password-change revocation, Secure outside DEBUG, cookie paths and lifetimes are
unchanged. No claim of equivalent CSRF protection is made. Production hardening
should coordinate frontend CSRF headers and re-enable these endpoint checks.
