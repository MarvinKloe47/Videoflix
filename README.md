# Videoflix Backend

Developer Akademie student project with account authentication and protected
HLS video streaming. The frontend is maintained separately.

## Technologies

Python, Django REST Framework, PostgreSQL, Redis, Django RQ, FFmpeg and Docker.

## Requirements

Git and Docker with Linux containers and Docker Compose 2.24.4 or newer.
Use Docker Desktop on Windows/macOS or Docker Engine with Compose on Linux.
No Python or PowerShell installation is required on the host.

## Installation

```sh
git clone https://github.com/MarvinKloe47/Videoflix.git
cd Videoflix
```

Copy `.env.example` to `.env` using your editor or file manager.
Alternatively, use `cp .env.example .env` on macOS/Linux or
`Copy-Item .env.example .env` in Windows PowerShell.

Edit `.env` and replace **SECRET_KEY** and **DB_PASSWORD** with different long,
random values. Configure your SMTP provider: **EMAIL_HOST**, **EMAIL_HOST_USER**,
**EMAIL_HOST_PASSWORD** and a verified **DEFAULT_FROM_EMAIL**. Use TLS on port 587
or SSL on 465, never both. Never commit `.env`. For local tests without delivery,
explicitly set `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`.

Start from the repository root:

```sh
docker compose up --build
```

The init service creates project migrations, applies all database migrations and
collects static files. Web and worker start only after init succeeds. No separate
initialization command is needed. The database and media use persistent volumes.

Backend: http://127.0.0.1:8000/api/csrf/
Admin: http://127.0.0.1:8000/admin/

The local Academy profile (`DEBUG=true`) automatically creates the official test
admin: **admin@example.com / adminpassword**. Do not expose this setup publicly.
Set both `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` to use your own
credentials. Existing passwords are retained; partial values fail initialization.
With `DEBUG=false`, no default admin is created: configure both values explicitly.
Alternatively, create an administrator in a second terminal:

```sh
docker compose exec web python manage.py createsuperuser
```

This uses email and password; there is no username field.
Users can be searched, edited, deactivated and deleted in the Django admin.

Login, refresh and logout accept the supplied frontend without a CSRF header.
Other authenticated writes and Django admin retain CSRF protection. See the
[security notes](docs/architecture.md#csrf-and-frontend-compatibility) for the tradeoff.

## Tests

Run in a second terminal while the services are running:

```sh
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web python manage.py migrate --check
docker compose exec web python manage.py test --noinput
docker compose exec web python manage.py smoke_hls
```

The HLS smoke test creates and removes temporary data. Use it only locally.
Stop services without deleting data with `docker compose stop`; start them again
with `docker compose up --build`. Do not delete volumes to fix startup errors.

The unchanged Academy files are extended by `docker-compose.override.yml`.
See [Docker details](docker/academy/README.md) and
[test evidence and limitations](docs/ABGABE_CHECK.md).
