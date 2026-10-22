# Academy Docker integration

This directory contains unchanged upstream references and our separate project adapter.

## Upstream snapshot

Source: https://github.com/Developer-Akademie-Backendkurs/material.videoflix-docker-files

Commit: `4796b17de2b7656d62b6904d4d04e5b74cbc41c6` (2025-11-05).
Retrieved and tested on 2026-10-22.

All six upstream files are in `original/`, including the original README and
public example environment. Their Git blob SHA-1, SHA-256 and sizes are recorded
in `upstream.json`. `.gitattributes` disables line-ending conversion for these
references. `scripts/prepare_academy.py` verifies the Git blob hashes before use.
The example credentials in upstream `.env.template` are public reference data;
the runtime never uses them. Random local credentials are generated separately.

## Why the original entrypoint needs an adapter

The unchanged Dockerfile builds successfully with our unchanged requirements.
It really uses Python 3.12 Alpine, despite its descriptive label mentioning 3.14.
It includes FFmpeg, FFprobe and PostgreSQL client libraries.

The unchanged entrypoint was executed against an isolated PostgreSQL database.
Collectstatic and all initial migrations succeeded. It then exited with
`FieldError: Cannot resolve keyword 'username' into field`: our User deliberately
has no username field and logs in by email. Changing this User model would risk
breaking the working authentication contract.

The tested submission profile therefore merges the original Compose file with
`compose.compat.yaml`, a clearly separate extension. The original entrypoint stays
in the image unchanged; the extension selects our own entrypoint explicitly.

## Own files

- `compose.compat.yaml`: original services db/redis/web plus migrate and worker;
  separate lifecycle, health dependencies, image snapshots rather than host binds,
  localhost port 8001, project-scoped container names, PostgreSQL 18/Redis 8 major tags.
- `entrypoint.sh`: bounded database readiness, migrate/collectstatic/bootstrap as a
  one-shot service; Gunicorn and RQ each run as their container's foreground process.
  No automatic generation of new migrations during regular startup.
- `bootstrap_admin.py`: uses DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD;
  existing credentials are retained. DJANGO_SUPERUSER_USERNAME remains in the env
  template for compatibility but does not become a field in our email-based User.
- `.env.example`: preserves the Academy variable names; safe placeholders and local
  console-mail settings. No runtime password or secret is checked in.
- `core/academy_settings.py`: isolated settings module for REDIS_LOCATION,
  CSRF_TRUSTED_ORIGINS, EMAIL_USE_SSL and the Academy static volume `/app/static`.
  Existing core/settings.py and local CACHE_URL/FRONTEND_ORIGINS behavior are unchanged.
- `core/academy_test_settings.py`: existing isolated test settings plus the adapter's
  path/origin/SSL values. Cache and mail remain isolated during unit tests.
- `scripts/prepare_academy.py`: verifies originals, recreates ONLY its generated
  `.runtime/context`, stages allowlisted project sources and exact upstream build
  files, and creates `.runtime/.env` only if absent. Existing root `.env` is untouched.
- `scripts/academy.ps1`: fixed Compose project and explicit file/env/path selection;
  forwards Docker CLI arguments, including `-d`, unchanged.

The root `.dockerignore` only gained an exclusion for `.runtime` so that its local
credentials and generated context cannot enter a later build of the old profile.
The official `.dockerignore` is unchanged and used in the staged Academy build.
No new Python runtime dependency was required. Django's existing Redis cache and
local static route work with the Academy variable/volume adapter.

## Reproduce on Windows / PowerShell

Run from the repository root; Python 3 and Docker Desktop Linux containers are
required. Docker Compose >= 2.24.4 is required for `!override` / `!reset`.

```powershell
python scripts/prepare_academy.py
.\scripts\academy.ps1 config --quiet
.\scripts\academy.ps1 up --build -d --wait --wait-timeout 120
.\scripts\academy.ps1 ps --all
.\scripts\academy.ps1 exec -T web python manage.py check
.\scripts\academy.ps1 exec -T web python manage.py makemigrations --check --dry-run
.\scripts\academy.ps1 exec -T web python manage.py migrate --check
.\scripts\academy.ps1 exec -T web python manage.py test --settings=core.academy_test_settings --noinput
.\scripts\academy.ps1 exec -T web python manage.py smoke_hls
```

Admin: http://127.0.0.1:8001/admin/; CSRF API: http://127.0.0.1:8001/api/csrf/.
Local admin credentials are ONLY in ignored `docker/academy/.runtime/.env`.
The existing frontend still uses port 8000; this isolated backend test does not
silently redirect that working frontend to the new database. To test it against
Academy instead, configure its API port to 8001 separately, or use Academy port
8000 after explicitly stopping the old backend. The two stacks cannot bind the
same host port simultaneously.

After source changes, rerun prepare before `up --build`: the image uses a staged
snapshot, not a live source bind. Changing the local runtime env needs `up -d`
to recreate affected containers. Re-running prepare preserves that env file.

Stop/start without deleting data:

```powershell
.\scripts\academy.ps1 stop
.\scripts\academy.ps1 up -d --wait --wait-timeout 120
```

All network and volume names are scoped to `videoflix-academy`. No external volumes
are reused. Existing `videoflix_*` volumes belong to the old stack and are not
mounted here. PostgreSQL 16 data is not opened using PostgreSQL 18; any intended
future data transfer needs an explicit dump/restore, not a volume substitution.
The major-version image tags remain mutable; upstream commit pinning freezes
reference files, not OS packages or image registries. The tested runtime versions
are recorded in docs/ABGABE_CHECK.md.

## Submission choice

Use **original/docker-compose.yml + compose.compat.yaml**, invoked through the
wrapper above, for the Academy submission. Keep all original files byte-identical
and include the separate adapter and preparation scripts. The existing root
Dockerfile/compose.yaml remain an independent local profile.

The unextended original entrypoint is NOT compatible with our email-based User.
This is an explicit, tested limitation, not an assertion that the unmodified
upstream stack ran successfully. The extended Academy profile passed all 60 backend
tests and real HLS conversion, including a complete stop/start with persistent data.
For remaining non-Docker submission points, see docs/ABGABE_CHECK.md.
