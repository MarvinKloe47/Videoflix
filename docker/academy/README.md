# Academy Docker setup

## Original files

Source: https://github.com/Developer-Akademie-Backendkurs/material.videoflix-docker-files

Snapshot: `4796b17de2b7656d62b6904d4d04e5b74cbc41c6`.
All six originals remain byte-identical in `original/`; hashes are recorded in
`upstream.json`. Root `backend.Dockerfile`, `backend.entrypoint.sh` and
`docker-compose.yml` are exact copies of their respective originals.
The public original environment template is reference data, never runtime input.

## Project extension

Compose automatically loads the root `docker-compose.override.yml`.
The original Dockerfile builds directly from the repository and installs Python,
FFmpeg/FFprobe and dependencies. No host Python, staging script or PowerShell
wrapper is involved. Its actual base is Python 3.12 Alpine, despite the unchanged
upstream label mentioning Python 3.14.

The extension chooses our `entrypoint.sh` because the original bootstrap expects
`User.username`, which our email-based User does not have. A single init service
runs before Gunicorn and a separate foreground RQ worker. Admin creation is
available through Django's built-in `createsuperuser` or the configured bootstrap
command inside the init container. No host initialization script is required.

The init service waits for PostgreSQL and runs:

```sh
python manage.py makemigrations auth_app video_app --noinput
python manage.py migrate --noinput
python manage.py bootstrap_admin
python manage.py collectstatic --noinput
```

`DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` configure automatic admin
creation. With both empty, `core.academy_settings` and `DEBUG=true` use the public
Academy test credentials `admin@example.com` / `adminpassword`, as specified in
the unchanged upstream entrypoint/template. The original username `admin` is not
passed to our email-only manager. These credentials are local development/submission
data, never a production default. With `DEBUG=false` or outside the Academy profile,
both empty means skip with a message; configure both explicitly for deployment.
New credentials use Django email/password validation. Only one supplied fails
initialization. An existing active superuser is retained
without changing its password. A conflicting regular or inactive account causes
a clear error and is never promoted/reactivated. Choose another email or resolve
that account deliberately. Repeated starts do not create duplicate users.

Per mentor feedback, each project migration directory contains only `__init__.py`
in the repository. Django generates initial migrations in the shared source bind
mount before admin/JWT migrations resolve the custom User. Generated project
migrations are ignored by Git and shared by web, worker, tests and later starts.
Do not delete them from an initialized setup. The checkout must be writable;
on Linux generated files may belong to the container's root user. This fresh-schema
approach must not be used to upgrade a database with the old migration history.

`core.academy_settings` maps official Redis/CORS/email names and the static volume
path while retaining application security settings. The isolated test settings
remain available. The default project is `videoflix-submission`; existing
`videoflix` and `videoflix-academy` volumes are not mounted. PostgreSQL 18 and Redis 8
major tags, readiness checks and a one-shot init gate provide a controlled startup.
Major tags remain mutable; this is not an image-digest lock.

## Operation

Follow the root README: copy `.env.example` to `.env`, set SECRET_KEY and
DB_PASSWORD and the SMTP provider/sender values, then run `docker compose up --build`.
Default host port is 8000. If an older stack occupies it, stop that stack without
removing volumes, or set HTTP_PORT to a free port in the new `.env`.
Do not reuse old PostgreSQL volumes or an old Compose project name for this setup.
For multiple fresh checkouts use a distinct COMPOSE_PROJECT_NAME environment
variable and HTTP_PORT for each.

The source bind mount exposes edits to containers; restart web/worker to load
changed Python code. Rebuild after dependency changes. Environment values and
volumes are retained. Stop with `docker compose stop`.
Host-platform test coverage is recorded in `../../docs/ABGABE_CHECK.md`;
Linux-container tests alone do not prove every host platform.

## SMTP delivery

SMTP is the default backend in both settings and `.env.example`. Supply EMAIL_HOST,
EMAIL_PORT, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD and DEFAULT_FROM_EMAIL using your
provider's verified sender. Use EMAIL_USE_TLS=true / EMAIL_USE_SSL=false on 587,
or false / true on 465. Django rejects both being enabled. The Academy adapter
inherits the same SMTP settings as the main settings; no duplicate SSL override.
Activation and password-reset services use this backend and the configured sender;
SMTP errors are not silently ignored. Provider authentication and sender policies
must be satisfied before real delivery can succeed.

Only for local tests without delivery, explicitly choose
`EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`. This prints mail
content and account links in local container logs, so do not share those logs.
