# Videoflix - Abgabecheck

Stand: 21.10.2026. Backend technisch getestet; Gesamtabgabe unter Vorbehalt der
externen Frontend- und Vorlagenpruefung. Kein Commit, Push oder History-Rewrite.

## Verbindliche Quellen

1. `Videoflix Checkliste.pdf`: vollstaendig per pypdf ausgelesen, primaere DoD.
2. `APIDoku_Videoflix (1).txt`: die angeforderte API-Dokumentation liegt unter
   diesem Dateinamen in docs vor.
3. Quellcode, Migrationen und Tests in auth_app, video_app und core.
4. `requiremnts.md`: vorhandene Ableitung REQ-001 bis REQ-044. Da diese nicht
   alle Frontend-Punkte der PDF enthaelt, folgen zusaetzliche Einzelpunkte unten.

Nicht vorhanden: separates Akademie-Frontend, dessen E-Mail-Designvorlagen und
vorgegebene Akademie-Docker-Dateien. Auch die erreichbare Git-Historie enthaelt
keine Docker-/Compose-Pfade. Die neue Docker-Konfiguration ist deshalb als eigene
Konfiguration gekennzeichnet. Keine Akademie-Datei wurde ersetzt oder veraendert.
Der unversionierte Ordner videoflix_backend ist nicht der verwendete Projekt-Root.

## Phase A: Bestandsaufnahme

| Anfangsstatus | Befund | Ergebnis |
|---|---|---|
| Vollstaendig implementiert | Registrierung, inaktive Accounts, Aktivierung, Login, CSRF, Reset, PUBLIC-Liste, DESC-Sortierung und geschuetzte HLS-Routen | Beibehalten und weiter getestet |
| Teilweise implementiert | RQ-Trigger ohne Aenderungserkennung/Deduplizierung; Queue-Ausfall nur geloggt | Quellversion, eindeutiger Job, Commit-Hooks und Fehlerstatus implementiert |
| Fehlerhaft | Normales save() startet Konvertierung; ungueltiger Logout kann 500 liefern; alte JWTs nach Passwortwechsel/Logout nutzbar | Behoben und Regressionstests ergaenzt |
| Fehlerhaft | DEBUG fest true, Dev-Schluessel im Code, MEDIA_ROOT Projekt-Root, automatischer Unique-Fehler verraet Kontoexistenz | Umgebungskonfiguration, eigener Media-Root und allgemeiner Fehler |
| Fehlerhaft | requirements UTF-16, fehlende Manager-Migration | UTF-8 und neue Migration |
| Fehlend | Echter Redis-Cache, Thumbnail-Auslieferung, README, Docker und HTML-Mail | Implementiert |
| Noch nicht getestet | Docker und realer Upload durch Queue/Worker in drei Qualitaeten | Jetzt erfolgreich geprueft |
| Weiterhin ungeprueft | SMTP-Zustellung, Akademie-Frontend, Browser-Player und Original-Maildesign | Externe Voraussetzungen fehlen |

## REQ-Nachweis

ERFUELLT bezieht sich auf den angegebenen Backend-Umfang. Frontend-Verhalten wird
nicht aufgrund eines API-Tests als bestanden ausgegeben.

| ID | Anforderung | Status | Dateien / Testnachweis |
|---|---|---|---|
| 001 | Registrierung E-Mail/Passwort/Bestaetigung | ERFUELLT | auth_app/serializers.py, Registrierungstests |
| 002 | Validierung und doppelte E-Mail ablehnen | ERFUELLT | RegistrationSerializer; Duplikat-/Mismatch-/Invalid-Tests |
| 003 | Allgemeine Registrierungsfehler | ERFUELLT | Automatischen Unique-Validator ersetzt, Fehlermeldung getestet |
| 004 | Account initial inaktiv | ERFUELLT | RegistrationSerializer.create und Test |
| 005 | Aktivierungs-Mail | ERFUELLT | services.py und HTML-Template, Outbox-Test |
| 006 | Aktivierung vor Login | ERFUELLT | ActivationView; gueltige/ungueltige/abgelaufene Tokens |
| 007 | E-Mail-/Passwort-Login | ERFUELLT | LoginView, Login-/Cookie-Tests |
| 008 | Generische Login-Fehler | ERFUELLT | Falschpasswort-/Inaktiv-Test |
| 009 | Authentifizierter Zugriff | ERFUELLT | CookieJWTAuthentication, 401-/PRIVATE-Tests |
| 010 | Sichere Abmeldung | ERFUELLT | Cookie-Loeschung, Refresh-Blacklist und gespeichertes Access-Token getestet |
| 011 | Reset anfordern | ERFUELLT | PasswordResetRequestView, Tests |
| 012 | Keine Kontoauskunft beim Reset | ERFUELLT | Gleicher Status/Body fuer bekannt/unbekannt |
| 013 | Reset-Mail mit Link | ERFUELLT | services.py und Frontend-Link-Test; SMTP separat offen |
| 014 | Neues Passwort setzen | ERFUELLT | Confirm-View/Serializer; neuer Login, Replay, alte JWTs getestet |
| 015 | Video-Liste | ERFUELLT | VideoListView, API-Tests |
| 016 | Titel/Beschreibung/Kategorie/Datum/Thumbnail | ERFUELLT | VideoSerializer, exakte Vertragsfelder getestet |
| 017 | Datum DESC | ERFUELLT | List-Queryset und Sortierungstest |
| 018 | Genre-Gruppierung ermoeglichen | ERFUELLT | category-Anzeigenamen; Gruppierung im Frontend |
| 019 | Hero-Standbild ermoeglichen | ERFUELLT | Geschuetztes thumbnail_url; UI separat ungeprueft |
| 020 | Thumbnail bereitstellen | ERFUELLT | Upload-Feld, ThumbnailView, Datei-Lesetest |
| 021 | Authentifiziert streamen | ERFUELLT | HLS-Views und echter Smoke-Test |
| 022 | HLS erzeugen | ERFUELLT | hls.py, echter FFmpeg-Test und Docker-Smoke |
| 023 | 480p/720p/1080p | ERFUELLT | Echter 1080p-Upload mit allen drei Qualitaeten; kein Upscaling getestet |
| 024 | Manuelle Qualitaetsauswahl ermoeglichen | ERFUELLT | Aufloesungsspezifische Routen; Player-UI separat offen |
| 025 | M3U8 ausliefern | ERFUELLT | MIME application/vnd.apple.mpegurl, API-/Smoke-Test |
| 026 | TS ausliefern | ERFUELLT | MIME video/MP2T, API-/Smoke-Test |
| 027 | Frontend/Backend getrennt, REST | ERFUELLT | Backend-Repository und DRF-Routing |
| 028 | DRF | ERFUELLT | requirements.txt, Views und Serializer |
| 029 | PostgreSQL statt SQLite | ERFUELLT | settings.py und Compose; lokale/Docker-Tests auf PostgreSQL |
| 030 | Redis als echter Cache | ERFUELLT | RedisCache DB 1, utils.py; echtes set/get/delete im Smoke |
| 031 | Hintergrundtasks mit Django RQ | ERFUELLT | signals.py/tasks.py, laufender Worker, echter Upload-Smoke |
| 032 | Videoverarbeitung | ERFUELLT | FFprobe/FFmpeg, Status/Fehler, sichere Pfade und Jobtests |
| 033 | Vollstaendiger Docker-Start | ERFUELLT | Eigener Dockerfile/compose.yaml, erfolgreicher Build/Start/Migrationen |
| 034 | Clean Code | ERFUELLT | Gezielte Refaktorierung, Ruff E/F und AST-Pruefung |
| 035 | Funktionen maximal 14 Zeilen | ERFUELLT | AST: keine Ueberschreitungen in Apps/core inkl. Tests; generierte Migrationen ausgenommen |
| 036 | Eine Aufgabe je Funktion | ERFUELLT | Getrennte Validierung, Responses und Fachhelfer |
| 037 | snake_case, sprechende Namen | ERFUELLT | Fachfunktionen snake_case; setUp/tearDown sind Django-Test-Hooks |
| 038 | Kein ungenutzter/auskommentierter Code | ERFUELLT | Ungenutzte Imports/Funktion entfernt, Ruff F erfolgreich |
| 039 | Views und Hilfsfunktionen getrennt | ERFUELLT | Responses in views.py, Hilfslogik in utils.py bzw. bestehenden Fachmodulen |
| 040 | PEP-8 soweit moeglich | ERFUELLT | Ruff E/F erfolgreich; historische generierte Migrationen unveraendert |
| 041 | Aussagekraeftige README | ERFUELLT | README.md: Installation, Infrastruktur, API, Upload, Tests, Fehlerbehebung |
| 042 | Projektdokumentation | ERFUELLT | README, aktualisierte architecture.md, dieser Bericht und Originalquellen |
| 043 | Nur Backend im Repository | ERFUELLT | git ls-files: Backend, Dokumente und Infrastruktur; kein Frontend |
| 044 | Akademie-Docker unveraendert | ERFUELLT | Keine solchen Dateien vorhanden, neue eigene Konfiguration gekennzeichnet |

### Weitere einzelne PDF-Punkte

| PDF-Punkt | Status | Nachweis / Grenze |
|---|---|---|
| Technisch: responsive Benutzeroberflaeche | OFFEN | Separates Frontend fehlt |
| Story 1: Formular mit drei Pflichtfeldern | TEILWEISE | API vorhanden, UI ungeprueft |
| Story 1: Registrieren-Button bei fehlenden Pflichtfeldern deaktiviert | OFFEN | Frontend-Verhalten |
| Story 1: Wechsel zum Anmeldeformular | OFFEN | Frontend-Verhalten |
| Story 1 Backend: User anlegen und Existenz pruefen | ERFUELLT | Registrierungs-/Duplikat-Tests |
| Story 1 Backend: Initial inaktiv, Aktivierungslink zum Frontend | ERFUELLT | Mail-/Aktivierungs-/Login-Tests |
| Story 1: Akademie-E-Mail-Designvorlage | TEILWEISE | Eigenes responsives HTML; Originalvorlage fehlt |
| Story 2: Login-Formular | TEILWEISE | Backend getestet, Frontend ungeprueft |
| Story 2: Allgemeiner Fehler bei falschen Daten | ERFUELLT | API-Fehler getestet; UI-Anzeige ungeprueft |
| Story 2: Passwort-vergessen-Option | TEILWEISE | Reset-API vorhanden; UI ungeprueft |
| Story 2: Weiterleitung zur Startseite | OFFEN | Frontend-Verhalten |
| Story 2: Wechsel zum Registrierungsformular | OFFEN | Frontend-Verhalten |
| Story 2 Backend: Falsche/inaktive Daten ablehnen | ERFUELLT | Inaktiv-/Passworttest |
| Story 3: Logout-Option | TEILWEISE | Endpoint vorhanden; UI ungeprueft |
| Story 3: Sicher ausloggen und zum Login weiterleiten | TEILWEISE | Backend getestet; Weiterleitung ist Frontend |
| Story 3: Daten nach Logout nicht erreichbar | ERFUELLT | User-Endpoint und aufbewahrtes Access-Token liefern 401 |
| Story 3 Backend: Cookies loeschen, Response senden | ERFUELLT | Cookie-Pfade/HttpOnly/Max-Age und Response getestet |
| Story 4: Passwort-vergessen-Funktion im Login | TEILWEISE | Backend fertig; Frontend fehlt |
| Story 4: Keine Kontoauskunft nach Reset-Anfrage | ERFUELLT | Identische Antwort getestet |
| Story 4: Reset-Mail senden | ERFUELLT | Outbox/Link getestet; SMTP offen |
| Story 4: Reset-Mail responsiv/richtig angezeigt | TEILWEISE | Fluides HTML mit viewport; reale Mailclients/Originaldesign ungeprueft |
| Story 4: Neues Passwort ueber Link setzen | ERFUELLT | uid/token, Validierung/Replay/Expiry getestet |
| Story 4: Login mit neuem Passwort | ERFUELLT | Regressionstest |
| Story 4 Backend: Frontend-Link und Passwort ersetzen | ERFUELLT | Link und Django-Passworthash; alte JWTs invalidiert |
| Story 5: Hero-Teaser oder Standbild | TEILWEISE | Thumbnail-API vorhanden, Darstellung ungeprueft |
| Story 5: Gruppierung nach Genre anzeigen | TEILWEISE | category vorhanden, UI-Gruppierung ungeprueft |
| Story 5: Reihenfolge Datum DESC | ERFUELLT | API-Sortierungstest |
| Story 5: Thumbnail und Titel anzeigen | TEILWEISE | API/Bild vorhanden; UI ungeprueft |
| Story 5 Backend: M3U8, TS und Thumbnail | ERFUELLT | Datei-Tests und Smoke |
| Story 6: 480p/720p/1080p manuell waehlen | TEILWEISE | Alle Dateien/Routen real getestet; Player-Auswahl ungeprueft |
| Story 6: Play/Pause/Vor-/Zurueckspulen | OFFEN | Separater Player |
| Story 6: Vollbild | OFFEN | Separater Player |
| Story 6 Backend: M3U8/TS fuer Qualitaeten | ERFUELLT | Smoke liest alle drei Qualitaeten |
| Story 7: Footerlinks Datenschutz/Impressum | OFFEN | Frontend fehlt |
| Story 7: Rechtstexte klar/verstaendlich | OFFEN | Inhalte fehlen; keine Texte erfunden |
| Story 7: Rechtsseiten responsiv | OFFEN | Frontend-/Browserpruefung fehlt |
| Deployment: echte Angaben und Akademie-Kennzeichnung | OFFEN | Nur bei eigenem oeffentlichem Deployment; nicht durchgefuehrt |
| Abgabe als GitHub-Link | TEILWEISE | Git-Remote vorhanden; keine Einreichung/Push durchgefuehrt |
| Abgabe nur Backend | ERFUELLT | Versionierte Struktur geprueft |
| Akademie-Docker nicht veraendern | ERFUELLT | Keine vorhanden; eigene Dateien hinzugefuegt |
| E-Mail/HLS erarbeiten und Dokumentationen verwenden | ERFUELLT | Code analysiert, offizielle Transaktions-/RQ-/FFmpeg-Dokumentation konsultiert |

## API-Vertragsabgleich

Alle dokumentierten URLs und Methoden existieren unveraendert. Registrierung:
201 mit user/id/email und Aktivierungstoken. Aktivierung: 200/message bzw. 400.
Login: 200/detail/user und HttpOnly-Cookies. Logout: 200/detail, Cookie-Loeschung
und Refresh-Blacklist. Refresh: 200/detail/access und Access-Cookie; fehlendes
Refresh-Cookie 400, ungueltiges 401. Reset und Confirm: 200/detail.
Videos: 200 als flache Liste der sechs dokumentierten Felder; anonym 401.
Fehlende/private/nicht fertige HLS-Ressourcen: 404. M3U8-/TS-MIME-Typen stimmen.

Korrigiert: undokumentiertes video_url auf Original-MP4 entfernt, category liefert
Anzeigenamen wie Drama statt DRAMA. thumbnail_url bleibt absolut und ist jetzt
geschuetzt. Bestehende csrf/user/detail-Erweiterungen bleiben erhalten; Thumbnail
und Staff-RQ-Uebersicht wurden ergaenzt. CSRF fuer Login/Refresh/Logout ist eine
dokumentierte Sicherheitsergaenzung. Der Vertrag fordert keine Backend-
Gruppenstruktur und keinen oeffentlichen Upload-Endpoint.

## Tatsaechlich ausgefuehrte Abnahme

| Pruefung | Ergebnis |
|---|---|
| Ausgangssuite manage.py test --noinput | 33 bestanden, PostgreSQL, echter FFmpeg-Test ohne Skip |
| Final lokal manage.py check | Keine Probleme, env/Scripts/python.exe |
| Final lokal makemigrations --check --dry-run | No changes detected |
| Final lokal test --noinput mit DJANGO_SETTINGS_MODULE=core.test_settings | 57 bestanden, 0 Fehler, 0 Skips, PostgreSQL |
| Docker Compose config --quiet | Erfolgreich |
| Docker Compose up --build -d | Images, Migrationen und collectstatic erfolgreich; vier Laufzeitdienste gestartet |
| Docker check | Keine Probleme |
| Docker makemigrations --check --dry-run | No changes detected |
| Docker test --settings=core.test_settings --noinput | 57 bestanden, 0 Fehler, 0 Skips, PostgreSQL im Container |
| Docker smoke_hls | PASS: echter Admin-1080p-MP4-Upload, Redis/RQ, Linux-Worker, FFmpeg, drei Qualitaeten, geschuetzte Datei-GETs |
| Echter Redis-Cache | set/get/delete im Smoke erfolgreich, getrennt von Queue |
| Healthchecks | Backend, DB und Redis healthy, Worker laeuft |
| Ruff E/F ohne generierte Migrationen | Keine Fehler |
| AST-Funktionslaengen Apps/core inkl. Tests | Keine Funktion ueber 14 physische Zeilen |
| Git-Historie/Ignore/Remote | Historische Django-Schluessel gefunden; keine versionierte .env, keine Credentials in Remote-URL |

57 ist die Anzahl unterschiedlicher Tests je finaler Suite, nicht 114 Tests.
Der Smoke-Test ist zusaetzlich. Sein erwartetes anonymes 401 erscheint als
Unauthorized im Log. Unit-/API-Tests isolieren Mail/Cache im Prozess und mocken
gezielte Queue-/Konvertierungsfehler; der Smoke verwendet echte Redis-/RQ-/FFmpeg-
Integration. Externe SMTP-Zustellung und Browser-/Frontend-Funktion nicht getestet.

## Risiken und Sicherheitsbefunde

- Historische core/settings.py-Versionen enthalten hart codierte Django-Schluessel,
  u.a. ac3b31b2 und b2c190c8 sowie spaetere Entwicklungsschluessel. Werte werden
  nicht ausgegeben. Aktuell wird SECRET_KEY aus der Umgebung verlangt. Der
  vorhandenen ignorierten .env wurde lokal ein neuer zufaelliger Schluessel und
  DEBUG=true fuer HTTP-Entwicklung hinzugefuegt. Lokale DB-Zugangsdaten blieben
  unveraendert. Falls historische Schluessel deployed verwendet wurden: dort
  rotieren und alte Sessions/JWTs verwerfen. History-Cleanup nur koordiniert
  separat entscheiden. Der Musterscan garantiert keine vollstaendige Geheimnisfreiheit.
- SMTP benoetigt externe Zugangsdaten. Console-/Outbox-/HTML-Versand und Links
  sind geprueft; echte Postfachzustellung bleibt offen.
- Akademie-Frontend und Original-Mailvorlage fehlen. UI/Player/Responsivitaet,
  Rechtsseiten und Originaldesign sind nicht abgenommen.
- Eine Pflicht zum konkreten Akademie-Docker-Setup ist den vorhandenen Dateien
  nicht zu entnehmen. Falls dieses zwingend ist, Originaldateien nachreichen und
  abgleichen. Das eigene funktionierende Setup wird nicht als Original ausgegeben.
- Kein oeffentliches Deployment: HTTPS/Static-Proxy, echte Hosts/Origins, SMTP und
  rechtliche Angaben separat konfigurieren. Lokales DEBUG=true ist kein
  Produktionsprofil. Medien nie pauschal oeffentlich ausliefern.
- Die Konvertierung haelt eine DB-Transaktion/Zeilensperre. PROCESSING ist extern
  bis zum Abschluss nicht sichtbar; paralleles Bearbeiten desselben Videos kann
  warten. Fuer diesen Projektumfang akzeptiert.
- Quellen unter 480p werden FAILED; 720p wird nicht kuenstlich zu 1080p skaliert.
  Fehlende Qualitaeten liefern 404; eine Discovery-API ist nicht vorgegeben.
- Admin validiert Upload-Endungen, FFprobe prueft Inhalt im Worker. Thumbnails
  werden separat hochgeladen, nicht automatisch extrahiert.
- Registrierung weist Duplikate allgemein mit 400 zurueck. 201 gegen 400 laesst
  indirekte Enumeration weiterhin zu; keine absolute Anonymitaet behauptet und
  kein geforderter API-Vertrag aufgehoben.
- Vorhandene lokale Medien wurden nicht verschoben/geloescht. Eigene Altdateien
  bei Bedarf aus videos/thumbnails/hls nach media kopieren.

## Vollstaendiger Start

Im Repository-Root unter PowerShell, bei Erstinstallation ohne vorhandene .env:

```powershell
Copy-Item .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
# .env bearbeiten: eigenen SECRET_KEY und DB_PASSWORD setzen.
# Vorhandene .env erhalten und nur fehlende Variablen ergaenzen.
docker compose config --quiet
docker compose up --build -d
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py check
docker compose exec backend python manage.py makemigrations --check --dry-run
docker compose exec backend python manage.py test --settings=core.test_settings --noinput
docker compose exec backend python manage.py smoke_hls
docker compose ps
```

Administration: http://localhost:8000/admin/. Frontend separat starten.
README.md beschreibt lokale PostgreSQL-/Redis-/Windows-Worker-/FFmpeg-Einrichtung.

## Abgabeempfehlung

Backend-Code und eigener Docker-Stack sind technisch fuer die Backend-Durchsicht
bereit. Die vollstaendige Erfuellung aller PDF-Punkte kann ohne Frontend-Abgleich,
Original-Maildesign und abschliessende Einreichungspruefung nicht bestaetigt werden.
Vor Gesamtabgabe Frontend-Punkte pruefen, SMTP testen und gegebenenfalls die Pflicht
zum Akademie-Docker-Setup klaeren. Anschliessend selbst committen/pushen und den
GitHub-Link einreichen.

## Geaenderte und neue Dateien

- `.dockerignore`
- `.env.example`
- `.gitignore`
- `Dockerfile`
- `README.md`
- `auth_app/admin.py`
- `auth_app/authentication.py`
- `auth_app/migrations/0002_alter_user_managers.py`
- `auth_app/models.py`
- `auth_app/serializers.py`
- `auth_app/services.py`
- `auth_app/templates/auth_app/email.html`
- `auth_app/tests.py`
- `auth_app/urls.py`
- `auth_app/utils.py`
- `auth_app/views.py`
- `compose.yaml`
- `core/middleware.py`
- `core/settings.py`
- `core/test_settings.py`
- `core/urls.py`
- `docs/ABGABE_CHECK.md`
- `docs/architecture.md`
- `requirements.txt`
- `video_app/admin.py`
- `video_app/hls.py`
- `video_app/management/__init__.py`
- `video_app/management/commands/__init__.py`
- `video_app/management/commands/smoke_hls.py`
- `video_app/migrations/0003_video_hls_job_id_alter_video_thumbnail_file_and_more.py`
- `video_app/models.py`
- `video_app/serializers.py`
- `video_app/signals.py`
- `video_app/tasks.py`
- `video_app/tests.py`
- `video_app/urls.py`
- `video_app/utils.py`
- `video_app/views.py`

Zusaetzlich wurde die ignorierte lokale `.env` um einen zufaelligen SECRET_KEY
und DEBUG=true ergaenzt. Keine Zugangsdaten werden hier wiedergegeben.
Die neuen Migrationen wurden auch auf der lokalen PostgreSQL-Datenbank angewendet.
