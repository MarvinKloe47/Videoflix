# Videoflix Backend

Django-/DRF-Backend fuer das Videoflix-Projekt der Developer Akademie.
Es bietet E-Mail-Registrierung, Aktivierung, JWT-Cookies, Passwort-Reset,
eine geschuetzte Videobibliothek und HLS-Streaming. Das Frontend ist separat.
Verbindliche Referenzen liegen in `docs/`: PDF-Checkliste und
`APIDoku_Videoflix (1).txt`. Der Abnahmestand steht in [docs/ABGABE_CHECK.md](docs/ABGABE_CHECK.md).

## Stack und Struktur

Python 3.12 (Docker), Django 5.2, DRF, SimpleJWT, PostgreSQL 16, Redis 7,
Django RQ/RQ, FFmpeg/FFprobe und Gunicorn. Die exakten Python-Versionen
stehen in `requirements.txt` (UTF-8).

```text
auth_app/   Benutzer, Serializer, Authentifizierung, E-Mails, Tests
video_app/  Videos, geschuetzte Dateien, Signals, HLS, RQ-Tasks, Tests
core/       Settings, Routing, CORS und isolierte Testkonfiguration
docs/       Verbindliche Quellen, Architektur, Abnahme
manage.py   Django-Kommandozeile
compose.yaml / Dockerfile   Eigenstaendige lokale Docker-Konfiguration
```

## Docker-Start (empfohlen)

Voraussetzungen: Docker Desktop mit laufender Linux-Engine und Compose v2.
Die Dateien sind eine eigene Konfiguration; Akademie-Docker-Dateien lagen
weder im aktuellen Repository noch in der untersuchten Git-Historie vor.

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# .env bearbeiten: SECRET_KEY und DB_PASSWORD durch eigene Werte ersetzen.
# Vorhandene .env NICHT ueberschreiben; stattdessen fehlende Variablen ergaenzen.
docker compose config --quiet
docker compose up --build -d
docker compose ps
docker compose exec backend python manage.py createsuperuser
```

Backend: http://localhost:8000, Administration: http://localhost:8000/admin/,
RQ-Uebersicht (nur Staff): http://localhost:8000/django-rq/.
PostgreSQL und Redis haben keine veroeffentlichten Host-Ports.
Migrationen und `collectstatic` laufen im einmaligen `migrate`-Service vor
Backend und Worker. DB, Redis, Media und Static verwenden persistente Volumes.
DB, Redis und Backend haben Healthchecks; Worker-Status und Jobs sind ueber RQ pruefbar.

```powershell
docker compose logs --tail 100 backend worker migrate
docker compose stop
# Wieder starten, ohne Daten zu loeschen:
docker compose up -d
```

`DEBUG=true` ist fuer lokale HTTP-Entwicklung vorgesehen. Bei HTTPS-Deployment:
`DEBUG=false`, echte Hosts/Frontend-Origins, SMTP und TLS-Reverse-Proxy konfigurieren.
Die beiliegende statische Django-Auslieferung fuer die Admin-Oberflaeche dient
lokaler Abgabe/Entwicklung. Fuer oeffentlichen Betrieb Static ueber den Proxy
bedienen. Niemals `MEDIA_ROOT` pauschal oeffentlich freigeben.

## Lokale Einrichtung unter Windows

Voraussetzungen: Python (mit 3.14 lokal getestet), PostgreSQL, Redis (z.B. in
WSL oder einem eigenen Docker-Container), FFmpeg und FFprobe im PATH.

```powershell
python -m venv env
.\env\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# .env bearbeiten; existierende Datei erhalten.
```

PostgreSQL in `psql` mit Administratorrechten einrichten (eigenes Passwort einsetzen):

```sql
CREATE USER videoflix WITH PASSWORD 'replace-with-your-local-database-password';
CREATE DATABASE videoflix OWNER videoflix;
-- Fuer den Testlauf muss der Benutzer Testdatenbanken anlegen duerfen:
ALTER USER videoflix CREATEDB;
```

`DB_HOST=127.0.0.1`, `DB_PORT=5432`, `DB_NAME`, `DB_USER` und `DB_PASSWORD`
muessen zu dieser Datenbank passen. Docker setzt den Host intern auf `db`.

```powershell
# Separater lokaler Redis fuer Windows-Entwicklung (nicht fuer Compose erforderlich):
docker run -d --name videoflix-local-redis -p 127.0.0.1:6379:6379 redis:7-alpine
ffmpeg -version
ffprobe -version
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
# Separates Terminal, gleiche virtuelle Umgebung:
python manage.py rqworker default --worker-class rq.worker.SimpleWorker
```

Der SimpleWorker vermeidet `fork()` unter Windows. Linux/Docker verwendet den
normalen RQ-Worker mit Prozessisolation. Unter Windows gelten fuer produktive
lange Jobs die Einschraenkungen des SimpleWorker; Docker ist der Abgabeweg.

## Umgebung und Sicherheit

`.env.example` enthaelt nur Platzhalter. `.env`, Medien, virtuelle Umgebungen
und generierte Dateien sind ignoriert und werden nicht ins Image kopiert.
Ohne `SECRET_KEY` startet Django bewusst nicht. Historische hart codierte
Entwicklungsschluessel sind im Abnahmebericht dokumentiert; deployed verwendete
Schluessel muessen rotiert werden. Die Git-Historie wurde nicht veraendert.

Queue: Redis DB 0 (`REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`).
Cache: separate DB 1 (`CACHE_URL`). Gecacht werden ausschliesslich Video-Metadaten
fuer 60 Sekunden, keine Benutzer, JWTs oder HTTP-Responses. Authentifizierung und
PUBLIC-Sichtbarkeit werden vor jedem Zugriff frisch geprueft. Aenderungen und
Loeschungen invalidieren nach dem Commit. Bei Cache-Ausfall erfolgt ein
protokollierter Datenbank-Fallback; Queue-Ausfaelle setzen den Verarbeitungsstatus
auf FAILED. `QuerySet.update()` umgeht Signale und kann Metadaten bis zu 60 Sekunden
veraltet lassen; die Sichtbarkeit wird weiterhin frisch geprueft.

CORS erlaubt nur `FRONTEND_ORIGINS` mit Credentials. JWT-Cookies sind HttpOnly,
SameSite=Lax und bei `DEBUG=false` Secure. Fuer das uebliche lokale Frontend auf
einem anderen Port zuerst CSRF abrufen und Cookies mitsenden:

```javascript
const api = 'http://127.0.0.1:8000/api';
const {csrfToken} = await fetch(`${api}/csrf/`, {credentials: 'include'}).then(r => r.json());
await fetch(`${api}/login/`, {
  method: 'POST', credentials: 'include',
  headers: {'Content-Type': 'application/json', 'X-CSRFToken': csrfToken},
  body: JSON.stringify({email: 'user@example.com', password: 'your-password'})
});
```

Login, Refresh und Logout brauchen CSRF. Cookie-authentifizierte Schreibzugriffe
werden ebenfalls geprueft. Frontend und API muessen bei SameSite=Lax dieselbe
Site nutzen; `localhost` und `127.0.0.1` nicht mischen. Ein Betrieb auf verschiedenen
Sites benoetigt eine eigene Cookie-/CSRF-Konfiguration und ist nicht voreingestellt.

## API

| Methode | URL | Erfolg | Zweck |
|---|---|---|---|
| POST | `/api/register/` | 201 | email, password, confirmed_password |
| GET | `/api/activate/<uidb64>/<token>/` | 200 | Account aktivieren |
| GET | `/api/csrf/` | 200 | CSRF-Cookie und Token (Erweiterung) |
| POST | `/api/login/` | 200 | email/password, Access-/Refresh-Cookies |
| POST | `/api/logout/` | 200 | Cookies loeschen, Refresh sperren |
| POST | `/api/token/refresh/` | 200 | Access-Cookie erneuern |
| POST | `/api/password_reset/` | 200 | Reset-Link anfordern |
| POST | `/api/password_confirm/<uidb64>/<token>/` | 200 | new_password, confirm_password |
| GET | `/api/user/` | 200 | Angemeldeten Benutzer lesen (Erweiterung) |
| GET | `/api/video/` | 200 | PUBLIC-Videos nach created_at DESC |
| GET | `/api/video/<id>/` | 200 | Videodetail (Erweiterung) |
| GET | `/api/video/<id>/thumbnail/` | 200 | Geschuetztes Thumbnail (Erweiterung) |
| GET | `/api/video/<id>/<resolution>/index.m3u8` | 200 | HLS-Playlist |
| GET | `/api/video/<id>/<resolution>/<segment>/` | 200 | TS-Segment |

Video-Endpunkte benoetigen ein gueltiges Access-Cookie (sonst 401), private und
fehlende Ressourcen liefern 404. Refresh/Logout: fehlendes Refresh-Cookie 400,
ungueltiges/gesperrtes Token 401; fehlendes CSRF bei Schreibzugriffen 403.
Die Videoantwort enthaelt exakt `id`, `created_at`, `title`, `description`,
`thumbnail_url`, `category`; Kategorien werden als z.B. `Drama` ausgegeben.
Die flache Liste bleibt API-vertragskonform; das Frontend gruppiert nach category.

## E-Mail-Aktivierung und Passwort-Reset

Neue Benutzer bleiben inaktiv. Aktivierungs- und Reset-Links zeigen auf die
konfigurierten Frontend-Seiten mit `uid` und `token`. Das Frontend ruft danach den
jeweiligen API-Endpunkt auf. E-Mails enthalten Plaintext und responsives HTML.
Die eigene HTML-Vorlage wurde nicht mit der nicht vorliegenden Akademie-Frontend-
Vorlage abgeglichen. Reset-Antworten sind fuer bekannte und unbekannte E-Mails
gleich. Doppelte Registrierung liefert eine allgemeine Fehlermeldung; wegen
unterschiedlicher HTTP-Ergebnisse ist Registrierung nicht vollstaendig gegen
Enumeration verborgen (der Vertrag verlangt Ablehnung doppelter Adressen).

Standardmaessig schreibt das Console-Backend E-Mails in die Serverlogs. Fuer echten
Versand `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` und die
`EMAIL_*`-Variablen konfigurieren. Externe SMTP-Zustellung wurde nicht getestet.
Logout sperrt auch gespeicherte Access-Tokens derselben Sitzung; Passwortwechsel
invalidiert vorher ausgestellte Access- und Refresh-Tokens.

## Videoupload und HLS

Uploads erfolgen als Staff/Superuser ueber `/admin/video_app/video/add/`.
Es gibt gemaess API-Vertrag keinen oeffentlichen Upload-Endpunkt.
MP4 und ein Thumbnail (JPG/PNG/WebP) angeben. Die Admin-Validierung prueft
Dateiendungen; FFprobe prueft den Videostream im Hintergrund. Beschaedigte Dateien
werden FAILED. Ein Bild wird bereitgestellt, nicht automatisch extrahiert.

Nur neue/ersetzte Quelldateien planen nach dem DB-Commit einen RQ-Job ein.
Metadaten- und Statusspeicherungen starten keine neue Konvertierung. Jobs besitzen
UUIDs je Quellversion; Redis erzwingt eindeutige Jobs. PostgreSQL-Zeilensperren
serialisieren Konvertierungen; veraltete und bereits abgeschlossene Jobs werden
uebersprungen. Status: PENDING, PROCESSING, READY oder FAILED. Die Verarbeitung
haelt eine Transaktion: PROCESSING ist fuer andere DB-Verbindungen waehrenddessen
noch nicht sichtbar; READY/FAILED werden beim Abschluss sichtbar.

FFmpeg erzeugt 480p/720p/1080p nur bis zur Quellhoehe (kein Upscaling).
Quellen unter 480 Pixeln Hoehe scheitern mit einer erklaerenden Statusmeldung.
Timeout: 30 Sekunden fuer FFprobe, 900 Sekunden je Qualitaet, RQ 3600 Sekunden.
Eingabeprotokolle sind auf file/pipe begrenzt. HLS-Struktur:

```text
media/videos/<quelle>.mp4
media/thumbnails/<bild>
media/hls/<video-id>/480p/index.m3u8
media/hls/<video-id>/480p/segment_000.ts
# ebenso 720p und 1080p, falls die Quelle sie unterstuetzt
```

Playlists verweisen ausschliesslich auf geschuetzte Segment-URLs.
Nicht fertige Videos, ungueltige Aufloesungen und Pfad-Traversal liefern 404.
Original-MP4s und das Medienverzeichnis werden nicht oeffentlich ausgeliefert.
Der Frontend-Player muss Cookies auch bei HLS-Anfragen mitsenden.

## Tests und Abnahme

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
# PostgreSQL bleibt die Testdatenbank; Cache/Mail werden lokal isoliert:
python manage.py test --settings=core.test_settings --noinput
# Im laufenden Docker-Stack:
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test --settings=core.test_settings --noinput
docker compose exec backend python manage.py smoke_hls
```

Der Smoke-Test laedt ein echtes generiertes 1080p-MP4 ueber den Admin hoch,
prueft Redis-Cache und Queue, wartet auf den laufenden Worker und liest alle drei
HLS-Qualitaeten authentifiziert. Seine temporaeren Benutzer, Videos und Medien
werden entfernt. Nur in einer Entwicklungs-/Abnahmeumgebung ausfuehren.
Die Tests enthalten ausserdem einen echten lokalen FFmpeg-Lauf; fehlt FFmpeg,
wird ausschliesslich dieser Test explizit uebersprungen.

## Fehlerbehebung

- Docker-Engine fehlt: Docker Desktop starten, Linux-Container aktivieren.
- DB-Verbindung: lokale `.env` pruefen; in Docker ist der Host `db`.
- `SECRET_KEY` fehlt: eigenen zufaelligen Wert in `.env` setzen.
- Keine E-Mail im Postfach: Console-Backend schreibt in Logs; SMTP konfigurieren.
- 403 bei Login/Refresh/Logout: CSRF-Cookie holen, Header und Credentials mitsenden.
- 401 bei HLS: Access-Cookie fehlt/abgelaufen oder Sitzung wurde beendet.
- FAILED: `processing_error` im Admin und Worker-Logs lesen; FFmpeg/Quelle pruefen.
- Queue-Ausfall: Redis wieder starten, Quelldatei erneut hochladen.
- Fehlgeschlagener RQ-Job: nach Fehlerbehebung ueber die Staff-RQ-Uebersicht erneut
  einreihen; neues Hochladen erzeugt ebenfalls eine neue Quellversion.
- Fehlendes Thumbnail: Bild tatsaechlich hochladen; DB-Dateiname allein erzeugt keine Datei.
- Bestehende lokale Medien: nach Umstellung auf `media/` eigene vorhandene Dateien
  aus den alten Ordnern `videos/`, `thumbnails/`, `hls/` dorthin kopieren.
  Dieser Sprint hat vorhandene Medien nicht verschoben oder geloescht.

Technische Referenzen: [Django-Transaktionen](https://docs.djangoproject.com/en/5.2/topics/db/transactions/),
[Django-Cache](https://docs.djangoproject.com/en/5.2/topics/cache/),
[RQ-Jobeindeutigkeit](https://python-rq.org/docs/),
[FFmpeg HLS](https://ffmpeg.org/ffmpeg-formats.html).
