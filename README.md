# Videoflix Backend

Django-/DRF-Backend fuer das Videoflix-Kursprojekt der Developer Akademie.
Registrierung, Aktivierung, JWT-Cookies, Passwort-Reset, geschuetzte Videobibliothek
und HLS-Konvertierung sind implementiert. Das bereitgestellte Vanilla-JavaScript-
Frontend wird separat verwaltet und ist nicht Bestandteil des Backend-Repositories.

Entwickelt im Rahmen des Weiterbildungsprogramms der Developer Akademie GmbH.
Die verwendeten Maildesigns und das Logo stammen aus dem Kurs-Frontend;
[Referenzen und Lizenz](docs/email_reference/README.md) sind dokumentiert.

## Abnahmestand und Quellen

Aktueller Nachweis: [docs/ABGABE_CHECK.md](docs/ABGABE_CHECK.md).
Verbindlich sind `docs/Videoflix Checkliste.pdf` und
`docs/APIDoku_Videoflix (1).txt`. [requirements.md](docs/requirements.md) ist eine
Ableitung, keine zusaetzliche Akademie-Vorgabe. Architektur:
[docs/architecture.md](docs/architecture.md).

Backend-Kernfunktionen sind getestet. Eine vollstaendige PDF-Abnahme wird wegen
fehlender fertiger Rechtstexte im separaten Demo-Frontend nicht behauptet.
SMTP-Postfachzustellung und reale Mailclients sind ohne freigegebene Testdaten
nicht geprueft; die Mail-Erzeugung und Links werden lokal getestet.

## Projektstruktur

```text
auth_app/       E-Mail-User, Auth-API, Mailtemplates/-Logo, Tests und Migrationen
video_app/      Video-API, Cache, HLS, Signals/RQ, Tests und Migrationen
core/           Settings, CORS, Routing und isolierter Akademie-Adapter
docker/academy/ Unveraenderte Originale, eigene Erweiterung und Herkunftsnachweis
scripts/        Vorbereitung, Compose-Wrapper und Abgabepruefung
docs/           Verbindliche Quellen, Referenzen und aktuelle Abnahme
Dockerfile / compose.yaml   Bisheriges eigenes lokales Docker-Profil
```

Python 3.12 im Container, Django 5.2, DRF, SimpleJWT, PostgreSQL, Redis, Django RQ,
FFmpeg/FFprobe und Gunicorn. Python-Abhaengigkeiten: `requirements.txt`.

## Akademie-Abgabe: offizielles Docker-Profil mit eigener Erweiterung

Voraussetzungen: Python 3, Docker Desktop mit Linux-Engine und
Docker Compose >= 2.24.4 fuer `!override` und `!reset`.

Im Projekt-Root unter PowerShell:

```powershell
python scripts/prepare_academy.py
.\scripts\academy.ps1 config --quiet
.\scripts\academy.ps1 up --build -d --wait --wait-timeout 120
.\scripts\academy.ps1 ps --all
```

Backend: http://127.0.0.1:8001/api/csrf/; Admin: http://127.0.0.1:8001/admin/.
Die automatisch erzeugten lokalen Admin-Zugangsdaten stehen ausschliesslich in
`docker/academy/.runtime/.env`. Diese Datei ist ignoriert; vorhandene Werte werden
beim erneuten Vorbereiten erhalten. Auch die Root-`.env` bleibt unveraendert.

Fuer die Abgabe wird **original/docker-compose.yml + compose.compat.yaml** verwendet.
Die sechs offiziellen Dateien sind byte-identisch auf Commit
`4796b17de2b7656d62b6904d4d04e5b74cbc41c6` festgehalten. Der offizielle Entrypoint
setzt ein username-Feld voraus; der getrennte eigene Adapter verwendet unser
E-Mail-Usermodell, einen Migrationsdienst und einen eigenen RQ-Worker. Originale
werden nicht editiert. Details: [Docker-Integration](docker/academy/README.md).

Der Projektname `videoflix-academy` isoliert Netzwerk und Volumes vom bisherigen
Stack. Nach Quellcodeaenderungen vor dem Build erneut prepare ausfuehren: Das
Image verwendet einen vorbereiteten Snapshot, keinen Live-Bind-Mount.

```powershell
.\scripts\academy.ps1 logs --tail 100 web worker migrate
.\scripts\academy.ps1 stop
.\scripts\academy.ps1 up -d --wait --wait-timeout 120
```

Diese Befehle erhalten die Volumes. PostgreSQL-16-Volumes des bisherigen Profils
werden nicht mit PostgreSQL 18 geoeffnet; ein Datentransfer erfordert Dump/Restore.

## Bisheriges eigenes lokales Docker-Profil

Dieses Profil bleibt erhalten und nutzt Port 8000, PostgreSQL 16 und Redis 7.
Nur bei Erstinstallation `.env.example` nach `.env` kopieren; eine bestehende Datei
nicht ueberschreiben. Eigene zufaellige Werte fuer SECRET_KEY und DB_PASSWORD setzen.

```powershell
Copy-Item .env.example .env
# Nur wenn noch keine .env existiert; Platzhalter durch eigene Werte ersetzen.
docker compose config --quiet
docker compose up --build -d --wait --wait-timeout 120
docker compose exec backend python manage.py createsuperuser
```

Backend/Admin: http://127.0.0.1:8000/admin/. Migrationen und collectstatic laufen
vor Webserver und Worker. DB/Redis werden nicht auf Host-Ports veroeffentlicht.
Medien werden ausschliesslich ueber geschuetzte API-Routen ausgeliefert.

## Lokale Python-Entwicklung

Voraussetzungen: PostgreSQL, Redis und FFmpeg/FFprobe im PATH. Lokale .env gemaess
.env.example einrichten; der DB-Benutzer benoetigt CREATEDB fuer die Testsuite.

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
# Zweites Terminal mit derselben Umgebung:
python manage.py rqworker default --worker-class rq.worker.SimpleWorker
```

Der SimpleWorker vermeidet fork() unter Windows; das Docker-Profil nutzt den
normalen Linux-RQ-Worker. Root-.env braucht lokale DB-/Redis-Hosts; das Akademie-Profil
setzt dagegen interne Dienstnamen db/redis.

## Authentifizierung und API

| Methode | URL | Zweck |
|---|---|---|
| POST | /api/register/ | email, password, confirmed_password; Account initial inaktiv |
| GET | /api/activate/uid/token/ | Konto aktivieren |
| GET | /api/csrf/ | Bestehende CSRF-Erweiterung |
| POST | /api/login/ | email/password; HttpOnly-Cookies |
| POST | /api/token/refresh/ | Leerer Body; Refresh-Cookie |
| POST | /api/logout/ | Cookies loeschen und Refresh-Session sperren |
| POST | /api/password_reset/ | Reset-Link anfordern, allgemeine Rueckmeldung |
| POST | /api/password_confirm/uid/token/ | new_password, confirm_password |
| GET | /api/user/ | Bestehende Benutzer-Erweiterung |
| GET | /api/video/ | PUBLIC-Videos, created_at DESC |
| GET | /api/video/id/ | Bestehende Detail-Erweiterung |
| GET | /api/video/id/thumbnail/ | Geschuetztes Thumbnail |
| GET | /api/video/id/480p/index.m3u8 | Playlist; ebenso 720p/1080p |
| GET | /api/video/id/480p/segment_000.ts/ | Geschuetztes TS-Segment |

Videoantworten enthalten exakt id, created_at, title, description, thumbnail_url
und category. Das Frontend gruppiert die flache Liste nach category. Anonyme
Videozugriffe liefern 401, private/fehlende Ressourcen 404. Kein oeffentlicher Upload.

Login, Refresh und Logout erfordern CSRF. Zuerst GET /api/csrf/ mit
`credentials: 'include'`, dann den csrfToken als X-CSRFToken im POST-Header senden.
Auch weitere API-/HLS-Anfragen muessen Cookies mitsenden. JWTs bleiben HttpOnly;
keine zusaetzliche Speicherung im Local Storage. localhost und 127.0.0.1 nicht
mischen: SameSite=Lax erfordert dieselbe Site. CORS/CSRF erlaubt nur konfigurierte
Origins mit Credentials. DEBUG=false aktiviert Secure-Cookies fuer HTTPS.

Root-Settings verwenden FRONTEND_ORIGINS/CACHE_URL, der eigene Akademie-Adapter
unterstuetzt CSRF_TRUSTED_ORIGINS/REDIS_LOCATION aus der offiziellen Vorlage.

## E-Mails und Videoverarbeitung

Aktivierungs-/Reset-Links zeigen auf FRONTEND_ACTIVATION_URL bzw.
FRONTEND_PASSWORD_RESET_URL mit uid/token. Mails enthalten Plaintext, HTML und ein
inline eingebettetes Logo. Autoescaping schuetzt personalisierte HTML-Inhalte;
Plaintext behaelt die unveraenderten Links. Der Ablauftext verwendet den tatsaechlichen
Django-PASSWORD_RESET_TIMEOUT (standardmaessig 72 Stunden), statt die 24 Stunden
aus der Designabbildung falsch zu versprechen. Der Tokenvertrag bleibt unveraendert.

Lokal schreibt das Console-Mailbackend in die Logs. SMTP nur mit freigegebenen
Testzugangsdaten und Empfaenger pruefen. Fuer Deployment EMAIL_BACKEND und EMAIL_*
konfigurieren; keine Zugangsdaten versionieren. Passwortwechsel invalidiert alte
JWTs; Logout sperrt auch vorher ausgestellte Access-Tokens derselben Sitzung.

Staff-Upload: /admin/video_app/video/add/ mit MP4 und JPG/PNG/WebP-Thumbnail.
Eine neue/ersetzte Quelldatei plant erst nach DB-Commit einen eindeutigen RQ-Job.
Metadaten-Speicherungen starten keine neue Konvertierung. Zeilensperre und Job-UUID
verhindern doppelte/veraltete Konvertierungen; READY/FAILED stehen im Admin.
FFmpeg erzeugt 480p/720p/1080p bis zur Quellhoehe, ohne Upscaling. Unter 480p wird
die Quelle FAILED. Nicht fertige/fehlende Qualitaeten liefern 404. Roh-MP4s bleiben
privat; Playlists referenzieren die geschuetzten Segmentrouten.

Queue: Redis DB 0; Metadaten-Cache: DB 1, 60 Sekunden. Sichtbarkeit und Authentifizierung
werden vor jedem Zugriff frisch geprueft. Commit-Hooks invalidieren den Cache;
Redis-Cache-Ausfall faellt auf die DB zurueck. Queue-Ausfaelle werden als FAILED erfasst.

## Qualitaetspruefung

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test --noinput
# Schnellere, isolierte Tests mit PostgreSQL, In-Memory-Mail/Cache und MD5-Testhasher:
python manage.py test --settings=core.test_settings --noinput
# Ruff ist ein separates Entwicklungswerkzeug, keine Runtime-Abhaengigkeit:
ruff check .
python scripts/check_submission.py
# Im Akademie-Container:
.\scripts\academy.ps1 exec -T web python manage.py check
.\scripts\academy.ps1 exec -T web python manage.py makemigrations --check --dry-run
.\scripts\academy.ps1 exec -T web python manage.py test --settings=core.academy_test_settings --noinput
.\scripts\academy.ps1 exec -T web python manage.py smoke_hls
```

Der Smoke-Test erzeugt ein echtes temporaeres 1080p-Video, prueft Redis/RQ/FFmpeg
und alle geschuetzten Qualitaeten. Nur in einer lokalen Entwicklungs-/Abnahmeumgebung
nutzen. Testbenutzer und Medien werden anschliessend entfernt. Kein vorhandener
Datenbestand wird zum Aufraeumen geloescht. Fehlt FFmpeg lokal, kennzeichnet der
echte FFmpeg-Test den Skip; die Docker-Images enthalten FFmpeg.

Ruff E/F/I gilt fuer den eigenen Code. Nur die 13 bestehenden E501-Faelle der beiden
Initialmigrationen und die Imports einer generierten Migration sind gezielt ausgenommen.
Die 14-Zeilen-Pruefung zaehlt physische Zeilen von def bis zum letzten Statement,
einschliesslich Signatur, Leerzeilen und Docstrings; Decorators liegen ausserhalb.
Die PDF nennt keine Zaehldefinition. Generierte Migrationen und unveraenderte
Akademie-Originale sind ausgenommen; setUp/tearDown behalten ihre Django-Hooknamen.

## Separates Frontend und Deploymentgrenzen

Der lokale Ordner Videoflix_frontend/ ist gesichert und wird von Git und Docker
ignoriert. Es gibt keinen Angular-/Bundler-Build; hls.js 1.6.7 kommt vom CDN.

```powershell
python -m http.server 5500 --bind 127.0.0.1 --directory Videoflix_frontend
npm --prefix Videoflix_frontend test
npm --prefix Videoflix_frontend run check
# Playwright nur als Testwerkzeug installieren:
npm --prefix Videoflix_frontend ci
Push-Location Videoflix_frontend
npx playwright install chromium
Pop-Location
npm --prefix Videoflix_frontend run test:browser
```

Der vorhandene Browser-Test erwartet das bisherige Backend auf Port 8000. Fuer
Frontendtests gegen das Akademie-Profil den Port separat konfigurieren oder erst
den bisherigen Port freigeben und ACADEMY_HTTP_PORT=8000 setzen. Kein Stack wird
hierfuer automatisch beendet. Das statische Webroot muss der Frontend-Ordner sein.

Datenschutz/Impressum sind gekennzeichnete Kurs-Demoinhalte, keine verifizierten
Betreiberangaben. Vor oeffentlichem Deployment muessen korrekte Daten/Rechtstexte,
HTTPS, reale Hosts/Origins, SMTP und ein Static-Proxy eingerichtet werden. Die lokale
Django-Static-Auslieferung ist fuer die Abnahme vorgesehen; MEDIA_ROOT nie pauschal
veroeffentlichen. Historische Entwicklungsschluessel sind als kompromittiert zu
behandeln; bei frueherer Deployment-Nutzung dort rotieren und alte Sessions verwerfen.
