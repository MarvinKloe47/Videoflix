# Videoflix submission check

## Second mentor feedback: current working changes

The mentor reports that Docker startup, video management, required fields and
email delivery already work. This update addresses automatic admin creation,
User admin registration, the supplied frontend's no-CSRF-header contract and
API subpackages. Earlier evidence below describes the previous submission and
is historical where it refers to mandatory login/refresh/logout CSRF headers.
No commit or push has been made for this update.

### Implemented changes

- API urls/views/serializers now live in auth_app/api and video_app/api. Models,
  services, authentication, tasks and signals remain outside these packages.
  All 14 existing URL names/paths, response bodies and video processing are kept.
- The init service runs bootstrap_admin after migrate and before collectstatic.
  DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD are explicit optional
  credentials. Both empty means a clear skip message; partial credentials fail.
  New credentials use Django validation and password hashing. Existing active
  superusers keep their ID/password; regular or inactive accounts are never
  promoted or reactivated and cause an explanatory configuration error.
- The custom User is registered with email-based Django UserAdmin/forms. Search,
  editing, adding, password changes, deactivation and deletion are supported.
- Only explicit csrf_protect decorators on login, refresh and logout are removed.
  Admin/session CSRF and CookieJWTAuthentication for other protected writes remain.
  HttpOnly is NOT a CSRF defense. SameSite and CORS are not equivalent substitutes.
  Login CSRF and same-site forgery risks remain at the exempt endpoints; see
  architecture.md for the explicit compatibility/security tradeoff.
- JWT lifetimes, HttpOnly/Secure/SameSite/path attributes, refresh validation,
  blacklist/session revocation and password-change checks are unchanged.
- API movement is checked against the previous AST (excluding imports/docstrings
  and the three intended decorators). This also verifies exact response strings.

### Executed verification

Tested in a new local clone of c239d69 plus the uncommitted working changes, with
new isolated Docker volumes and configured test-only admin credentials. Project:
videoflix-mentor2-4fbb0ae0, host port 8013. No existing volumes were reused/deleted.
The first build/up used the unchanged Academy Dockerfile and automatic override.
Initialization generated the custom-User migration before dependent migrations,
created the administrator and completed before web/worker startup.
The test stack was stopped after verification; all its volumes were retained.

The existing 63 tests remain, with three CSRF expectations updated to the mentor's
new contract. New tests cover bootstrap behavior, admin permissions/CRUD/passwords,
no-header authentication, other-write CSRF, deactivated JWT access and API routes.

| Check | Result |
|---|---|
| Default full backend suite | 85 passed, 17.086s, no skips (final response-text rerun) |
| Final bootstrap configuration-message verification | All 7 bootstrap tests passed again |
| Django check and migration checks | Passed; no model changes |
| Real Redis/RQ/FFmpeg/HLS smoke | PASS: upload, cache, worker, all 3 qualities, auth |
| pip dependency check | Passed |
| Bootstrap repeat and full stack restart | One admin; identical ID/password hash |
| Existing admin credentials after restart | Real HTTP login without CSRF/session passed |
| Migration files after restart | Hashes unchanged |
| Browser frontend-style protocol | Chromium cross-origin registration/activation/login/videos/refresh/logout passed |
| Browser cookie/storage checks | HttpOnly cookies; no prior admin/CSRF session; no Local Storage JWTs |
| Real Django admin in Chromium | Login, search, edit, deactivate, rejected member login, delete passed |
| Browser JavaScript errors | None in completed run |
| Ruff and DA function-size check | Passed; 49 Python files, 224 functions <=14 lines |
| Official Docker references and three root copies | Exact hashes preserved |

The browser protocol test sends real API requests from a real loopback origin,
with credentials included and no CSRF header. It is a protocol harness, not a full
run of the unchanged Academy frontend UI. Initial harness-origin/cookie-filter/
selector issues were corrected; no API responses were mocked. A final source
comparison caught and corrected a Windows encoding error in moved German response
strings; an explicit exact-text assertion was added before the final suite rerun.

Not executed here: external SMTP/provider rendering, native macOS/Linux hosts,
or the complete unchanged Academy frontend UI. The mentor's successful email
check is user-reported evidence, not a new SMTP test by this run. No frontend
files or application models/migrations were changed. No Academy approval claimed.

## Previous direct-Compose test record

## Previous direct-Compose submission profile

Reviewed on 2026-10-22. Mentor feedback supersedes the previous host-script setup.
Use the root Academy files plus the automatically loaded project override.
The supported installation is: clone, copy .env.example to .env, replace SECRET_KEY
and DB_PASSWORD, then run docker compose up --build. No host Python or PowerShell
initialization is needed. Optional admin creation uses Django createsuperuser.

The six official references and the three root copies are byte-identical to the
recorded upstream snapshot. The own override selects an email-aware entrypoint,
a single init service and a separate foreground worker. Application auth/video
Python code, JWT/CSRF settings, models and existing tests were not changed.

## Migration policy and data safety

The mentor requires project migration packages without existing migrations.
Only auth_app/migrations/__init__.py and video_app/migrations/__init__.py remain.
The init container generates both initial migrations before migrate so Django
admin and JWT blacklist dependencies on auth_app.User resolve correctly.
Generated migration files are ignored by Git and excluded from the image build;
they persist in the shared source mount and must be retained with the database.

This is a fresh-database profile, not an upgrade of the old migration history.
The default project name is videoflix-submission. Existing videoflix and
videoflix-academy volumes were neither reused nor deleted. The original five
project migrations were removed only after successful generation and application
in the isolated fresh-clone test. Django/dependency migrations remain unchanged.

## Test method

A new local Git clone of c1e930a was created outside the working repository, then
the uncommitted changes and new setup files were applied. This is a fresh clone
plus working patch, not a test of an already published commit. No commit/push was
made. The test checkout started without project migrations or its own .env.
A new .env was copied from the template and only secrets plus test isolation
values were supplied. Four new project-scoped Docker volumes were verified
absent before startup and distinct from every pre-existing volume.

Test project: videoflix-clean-33db5a61.
Host port: 8012 (8000 and 8001 were occupied by the existing stacks).
Host: Windows with Docker Desktop Linux containers, Compose 5.1.4.
The first start used exactly docker compose up --build, without host setup scripts.
The test harness uses local tooling to inspect results; it is not an installation
prerequisite for an examiner.

## Executed checks

| Check | Result |
|---|---|
| Official original-file and root-copy hashes | Passed |
| Empty-database build and direct Compose startup | Passed |
| One-shot init and dependent web/worker startup | Passed; init exited 0 |
| Initial User/Video generation and all Django/JWT migrations | Passed |
| Django system check | No issues |
| makemigrations --check --dry-run after init | No changes |
| migrate --check | Passed |
| Full default backend suite | 63 passed, 11.876 seconds, no skips |
| Redis | PONG; cache and RQ also exercised by smoke test |
| Real HLS smoke | PASS: upload, cache, RQ, 480p/720p/1080p, auth |
| Dependency consistency | pip check passed |
| Real HTTP authentication/API checks | Passed; details below |
| Restart and persistence | Passed; DB user, Redis and media retained |
| Post-rebuild default suite and HLS smoke | 63 passed, 11.467s, no skips; smoke PASS |
| Email-based createsuperuser CLI and HTTP login | Passed; no username required |
| Ruff and diff whitespace checks | Passed |
| DA naming/function-size check | 40 Python files, 197 functions <=14 lines |

Python 3.12.15, FFmpeg 8.1.2 and FFprobe 8.1.2 were executed in the fresh image.
The standard suite includes an actual FFmpeg conversion; the smoke test also
uses a real worker and Redis against the separate application database.

Real HTTP checks covered registration, inactive login rejection, invalid/valid
activation, login CSRF, both JWT-cookie names/paths/lifetimes/HttpOnly/SameSite,
local Secure behavior, credentialed CORS, user/video endpoints, missing detail,
anonymous HLS playlist/segment denial, refresh, logout and saved-token rejection.
Password reset returned the same response for known/unknown addresses; a console
mail link reset the password, could not be reused and enabled a new login while
the old password was rejected. No framework test client replaced these HTTP calls.

## Restart verification

The test stack was stopped with docker compose stop, then rebuilt and restarted
with docker compose up --build --wait --wait-timeout 120. A database user, a Redis
value and a media file survived. Both generated initial-migration hashes stayed
identical; init reported no changes and no migrations to apply. Exactly one RQ
worker was registered after restart. Temporary fixtures/markers were removed. The isolated test stack was stopped
after verification; its new volumes were retained.
All Docker volumes present before this test still exist. Previous stacks were
not stopped or reconfigured. Hash and normalized-source comparisons confirm that
the original Docker references and application auth/video/core code are unchanged.

## Limits

External SMTP delivery, email-provider rendering, macOS and native Linux host
execution were not tested. Frontend/browser playback was not rerun for this
Docker-only change; the real HLS server/worker smoke was executed. Source mounts
must be writable; generated migrations may be root-owned on Linux. Docker image
major tags and installed OS packages are not frozen by the source snapshot.
Production HTTPS/static hosting and actual legal-page contents belong to separate
deployment/frontend work. No Academy approval is claimed.

## Earlier records

The retired setup report is preserved in history/ABGABE_CHECK_before_direct_compose.md.
It is historical evidence, not the current installation instructions.
