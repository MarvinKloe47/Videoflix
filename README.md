# Videoflix Backend

Backend for the Developer Akademie Videoflix student project. It provides
account registration, email activation, login, password reset and video streaming.

## Technologies

Python, Django, Django REST Framework, PostgreSQL, Redis, Django RQ,
FFmpeg and Docker.

## Requirements

- Git
- Python 3.12 or newer for the setup script
- Windows with PowerShell
- Docker Desktop with Linux containers and Docker Compose 2.24.4 or newer

## Setup

Clone the repository and prepare the local environment:

```powershell
git clone https://github.com/MarvinKloe47/Videoflix.git
cd Videoflix
python scripts/prepare_academy.py
```

The script creates `docker/academy/.runtime/.env` with local credentials.
Existing settings are kept. Do not commit this file.
Application dependencies and FFmpeg are installed inside Docker.

## Start the Academy Docker setup

Run these commands from the repository root:

```powershell
.\scripts\academy.ps1 config --quiet
.\scripts\academy.ps1 up --build -d --wait --wait-timeout 120
.\scripts\academy.ps1 ps --all
```

This uses the unchanged Academy files with a separate project adapter.
Database migrations run automatically. Local admin credentials are stored
in `docker/academy/.runtime/.env`.

Open the admin page at http://127.0.0.1:8001/admin/.

After code changes, run the preparation script again before rebuilding.
See [Docker setup details](docker/academy/README.md) for configuration notes.

To stop the services without deleting data:

```powershell
.\scripts\academy.ps1 stop
```

## Tests

With the containers running:

```powershell
.\scripts\academy.ps1 exec -T web python manage.py check
.\scripts\academy.ps1 exec -T web python manage.py makemigrations --check --dry-run
.\scripts\academy.ps1 exec -T web python manage.py test --settings=core.academy_test_settings --noinput
.\scripts\academy.ps1 exec -T web python manage.py smoke_hls
```

The HLS smoke test creates and removes temporary test data.
Use it only in a local development environment.

## About

This repository contains the backend for my Videoflix project, developed during my training at Developer Akademie.

The frontend is maintained in a separate project.
