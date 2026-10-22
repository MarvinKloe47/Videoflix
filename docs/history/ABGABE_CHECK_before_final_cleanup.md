# Historical report before final cleanup

This snapshot records previous results, not current submission instructions.
See ../ABGABE_CHECK.md for the final verified state.

# Videoflix - Abgabecheck

Aktueller Stand: 22.10.2026. Offizielles Akademie-Docker-Profil mit separater
Erweiterung erfolgreich getestet (60 Tests und echter RQ/HLS-Lauf).
Der aktuelle Nachweis steht im Abschnitt "Offizielles Akademie-Docker-Setup
22.10.2026" am Ende. Fruehere Backend-/Frontend-Berichte bleiben als Historie erhalten.
Gesamtabgabe wegen der dort genannten Nicht-Docker-Punkte weiterhin unter Vorbehalt.
Kein Commit, Push oder History-Rewrite.

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

## Frontend-Integration 22.10.2026

**Massgeblicher aktueller Integrationsstand: NICHT ABGABEBEREIT fuer die
vollstaendige Checkliste.** Die technischen Kernablaeufe bestehen lokal mit
Chromium und dem echten Docker-Backend. Die oben stehenden Angaben vom
21.10.2026 sind ein historischer Backend-Bericht; Aussagen wie "Frontend fehlt",
"Original-Maildesign fehlt" und "Browser ungeprueft" sind durch diesen Abschnitt
ersetzt. Es gab keine Backend-, Migrations-, Dockerfile- oder Compose-Aenderung.

### Bestand und API-Abgleich

- Tatsächlicher Ordner: `Videoflix_frontend/` (grosses V); statisches HTML/CSS
  und Vanilla JavaScript, **kein Angular/React/Vue und keine Framework-Version**.
  Vorher kein package.json, Build, Linter oder automatisierter Frontendtest.
- Vorhandener Player: **hls.js 1.6.7**, fest gepinnter CDN-Script in
  `pages/video_list/index.html`. Keine neue Player-Laufzeitabhaengigkeit.
- Alle aktiven HTML-Seiten und acht eigenen JS-Dateien, Styles/Breakpoints,
  Startanleitung sowie beide Maildesign-PNGs wurden untersucht. Generierte
  JSDoc-Dateien sind historische Dokumentation, keine ausgefuehrte Anwendung.
- API-Vertrag liegt unter `docs/APIDoku_Videoflix (1).txt`; PDF-Checkliste erneut
  vollstaendig mit pypdf ausgelesen. Tatsächlich heisst Compose `compose.yaml`.

| Frontend-Aufruf | Vertrag / Ergebnis |
|---|---|
| POST register/ | email, password, confirmed_password passen; optionale Datenschutz-Checkbox bleibt UI-Feld |
| GET activate/uid/token/ | Parameter uid/token aus Frontend-Link; API-Pfad und Status passen |
| POST login/ | email/password; Cookies verwenden, Response-JWT nicht speichern |
| POST token/refresh/ | leerer JSON-Body, Refresh-Cookie und CSRF; einmalige Wiederholung geschuetzter GETs |
| POST logout/ | leerer JSON-Body, Cookies und CSRF; HTTP-Ergebnis jetzt auswerten |
| POST password_reset/ | email; allgemeine Rueckmeldung |
| POST password_confirm/uid/token/ | new_password und confirm_password korrekt aus Formularnamen abgeleitet |
| GET video/ | flache Liste; id/created_at/title/description/thumbnail_url/category passen |
| GET video/id/quality/index.m3u8 | bestehende 480p/720p/1080p-Routen, Cookies ueber hls.js/native HLS |
| GET Segment-URL aus Playlist | bestehende geschuetzte TS-Route inkl. Slash, kein eigener neuer Vertrag |
| GET thumbnail_url | URL unveraendert vom Backend, Cookies und keine oeffentliche Medienfreigabe |
| GET csrf/ | bereits bestehende Backend-Erweiterung fuer dessen CSRF-Schutz; kein neuer Endpunkt |

Die vorhandene Detailansicht ist ein Hero mit Titel/Beschreibung und Player-Overlay,
keine separate Detailroute. Thumbnail-Auswahl aktualisiert die Details ohne
zusaetzlichen API-Vertrag. Die vorhandene API-Detailerweiterung muss dafuer nicht
verwendet werden. Backend-Sortierung DESC wird beibehalten und im Client abgesichert.

### Gefundene Probleme und Korrekturen

| Problem vorher | Massnahme / Status |
|---|---|
| Login/Refresh/Logout ohne CSRF-Header -> 403 | Frischen maskierten Token von csrf/ holen und X-CSRFToken bei POST senden; Cookie-Credentials immer include |
| Festes 127.0.0.1-Backend bei localhost-Frontend -> SameSite-Konflikt | API-Host aus Seitenhostname, lokaler API-Port 8000; E-Mail-Links separat konfigurieren |
| Refresh alle 20 Minuten bei 5 Minuten Access-Laufzeit | Alle 4 Minuten; zusaetzlich geschuetzte GETs nach 401 einmal erneuern/wiederholen, parallele Refreshs zusammenfassen |
| Kein Sitzungsabbruch bei ungueltigem Refresh | Videoseite leitet zum Login; wiederhergestellte BFCache-Seite wird neu validiert |
| Logout meldete auch bei HTTP 403 Erfolg | Gemeinsamen CSRF-POST verwenden; nur bei Erfolg weiterleiten und Timer beenden |
| Netzwerkfehler enthielten keine fuer UI lesbaren Daten | Einheitliches data.detail fuer bestehende Fehlerdarstellung |
| Leere Liste verursacht VIDEOS[0]-Fehler | Eigener Leerzustand ohne Play-Button; Lade- und Serverfehler klar getrennt |
| Titel nur im Alt-Text der Thumbnails | Sichtbaren Titel ergaenzt, Genre-Gruppierung und Sortierung erhalten |
| Metadaten/Fehlertexte ungefiltert per innerHTML | Metadaten per textContent, Toast-/Aktivierungstexte HTML-escaped |
| Thumbnail-Credentials nicht explizit | use-credentials vor src; fehlende Bilder behalten Alternativtext |
| Overlay setzt ausgewaehlte Video-ID nicht zuverlaessig | currentVideo beim Oeffnen setzen; Qualitaetswechsel nutzt diese ID |
| Zwei grosse duplizierte Player-Konfigurationen | Gemeinsame kleine Player-Erzeugung mit bestehendem hls.js; Vorschau beim Overlay pausieren |
| Kein HLS-Supportcheck / nativer Fallback | Hls.isSupported, nativer HLS-Pfad, Meldung fuer ununterstuetzte Browser |
| HLS-Fehler nur in Konsole, 401 nicht erneuert | UI-Fehler bei fehlendem Stream; Refresh bei 401 mit Cookies |
| Qualitaetswechsel startet am Anfang | Vorherige Abspielposition nach Metadaten wieder setzen |
| Registrierung trotz leerer Pflichtfelder abschickbar | Button ueber checkValidity deaktiviert; fehlerhaftes required-Attribut repariert |
| Passwort-Reset-Validierung greift auf fehlendes confirmed_password zu | repeated_password alternativ verwenden; fehlende Resetparameter abfangen |
| Header mit URL-Query / Aktivierung fehlerhaft | pathname auswerten, Aktivierungslogin-Link und leeren Standardwert; Zurueck-Fallback absolut |
| Zusaetzliches schliessendes section-Tag | HTML-Struktur der Videoseite repariert |
| Mobile Hero-Ueberlappung bei langen Titeln | Flexible Artikelhoehe, Umbruch und begrenzte Thumbnail-Kartenbreite; Design/Farben erhalten |
| Keine reproduzierbaren Frontendtests | 7 Node-Regressionstests, Syntaxcheck und Playwright-Szenario; nur Test-DevDependency mit Lockfile |
| Unklarer Frontend-Start | README: separater statischer Server mit korrektem Webroot/Port; Compose unveraendert |

Geaendert im vorhandenen Frontend: `shared/js/api.js`, `config.js`, `auth.js`,
`header.js`, `ui_helper.js`, `pages/auth/register.html`,
`pages/video_list/video_list.js`, `index.html`, `video_list.css`, `readme.md`.
Neu: `.gitignore`, `package.json`, `package-lock.json`, `tests/api.test.cjs`,
`tests/player.test.cjs`, `tests/check.cjs`, `tests/browser.cjs`.
Im Backend-Repository nur README und dieser Bericht bearbeitet. Der bereits zu
Beginn unversionierte Frontend-Ordner wurde weder gestaged noch committed.

### Tatsächlich ausgefuehrte Pruefungen

| Pruefung | Ergebnis am 22.10.2026 |
|---|---|
| Lokale PostgreSQL-Backendtests | 57/57 bestanden, 2.166 s, keine ausgelassenen Tests |
| Docker-PostgreSQL-Backendtests | 57/57 bestanden, 0.941 s, keine ausgelassenen Tests |
| Django check lokal und Docker | Keine Probleme |
| makemigrations --check --dry-run lokal und Docker | Keine ausstehenden Migrationen |
| Ruff E/F ohne Migrationen | Bestanden: `ruff check auth_app video_app core --select E,F --extend-exclude migrations` |
| Ruff inklusive historischer Migrationen | 13 bestehende E501-Zeilenlaengenfehler; generierte Dateien unveraendert |
| docker compose config --quiet und up -d --build | Bestanden nach Start von Docker Desktop; anfangs Engine nicht erreichbar |
| PostgreSQL, Redis, Django | Laufend und healthy; migrate-Service erfolgreich abgeschlossen |
| RQ | Ein registrierter Worker; echten Konvertierungsjob erfolgreich bearbeitet |
| smoke_hls im Container | PASS: echter Admin-Upload, Redis-Cache, RQ/FFmpeg, alle drei Qualitaeten und Authentifizierung |
| npm test | 7/7 bestanden: CSRF/Credentials, geteilter Refresh, Netzwerkfehler, begrenzte Wiederholung, native/fehlende HLS-Unterstuetzung, Playerfehler |
| npm run check | Syntax aller 8 eigenen JS-Dateien bestanden |
| Frontend-Build | Nicht anwendbar: statisches Frontend ohne Bundler/Build-Skript |
| Frontend-Lint | Nicht eingerichtet; Syntaxcheck wird ausdruecklich nicht als Lint ausgegeben |
| Chromium headless / Playwright 1.64.1 | Vollstaendiges Integrationsszenario bestanden; Details unten |
| SMTP/echtes E-Mail-Postfach | Nicht ausgefuehrt: Console-Mailbackend; Links aus tatsaechlich erzeugten Docker-Konsolenmails verwendet |
| Firefox, Safari/iOS und native Safari-HLS-Wiedergabe | Nicht ausgefuehrt; nativer Codepfad nur isoliert mit Mocks getestet |

Browser-Szenario gegen http://127.0.0.1:5500 und echtes Django auf Port 8000:

- Anonymer Aufruf der Videoseite leitet zum Login.
- Registrierung: initial deaktivierter Button, Pflichtfelder, Checkbox, HTTP-201;
  Login vor Aktivierung abgelehnt; Aktivierung ueber Konsolenmail-Link.
- Login und Weiterleitung zur Uebersicht; access_token und refresh_token sind
  HttpOnly. Keine Token-Schluessel im Local Storage.
- Leere Liste und HTTP-500 absichtlich per Playwright-Route simuliert;
  entsprechende Zustaende korrekt. Diese beiden Faelle sind keine echten DB-Ausfaelle.
- Echtes 1080p-Testvideo erzeugt, ueber bestehende Modellsignale an RQ uebergeben,
  vom Worker konvertiert; authentifizierte Liste, Genre und echtes Thumbnail geladen.
- Access-Cookie gezielt entfernt: Videoliste erneuert Session und wiederholt GET.
- Thumbnail-Navigation aktualisiert Hero-Details und ausgewaehlten Player.
- 480p, 720p und 1080p: echte Manifest-/TS-HTTP-200, videoHeight jeweils 480/720/1080,
  currentTime > 0: **tatsaechliche Dekodierung/Wiedergabe**. Manueller Wechsel getestet.
- Access-Cookie vor Wechsel auf 720p gezielt entfernt: HLS-401 wird erneuert;
  danach erfolgreiche Wiedergabe. Kein fuenfminuetiger Wallclock-Ablauftest.
- Fehlendes Manifest absichtlich als HTTP-404 simuliert: sichtbare Fehlermeldung.
- Logout loescht beide JWT-Cookies; geschuetzte Seite danach gesperrt.
  Direkte anonyme Manifest- und TS-Anfragen liefern jeweils 401.
- Passwort vergessen, echter Console-Reset-Link, neues Passwort und erneuter Login.
- Dashboard bei 390x844 und 1440x900; Screenshots im lokalen Temp-Verzeichnis
  visuell geprueft. Langer Testtitel ueberlappt nach Korrektur nicht mehr mit Genre.
  Zusaetzlich Start-, Registrierungs-, Login-, Forgot-/Confirm-Passwort-,
  Datenschutz- und Impressumsseite bei 390px ohne horizontalen Seitenueberlauf
  geprueft. Keine JavaScript-pageerror-Ereignisse im erfolgreichen Szenario.

Die Browserdaten erhalten zufaellige Testnamen und werden im finally-Block mit
ihren Medien entfernt. Bestehende Benutzer/Videos wurden nicht geloescht.
Die ersten Testversuche scheiterten an Test-Locatoren (versteckte Custom-Checkbox,
mehrfaches Thumbnail in "New" und Genre), nicht an uebersprungenen Assertions;
die korrigierten Szenarien wurden erneut vollstaendig ausgefuehrt.

### Offene Punkte und finale Empfehlung

1. **Maildesign entspricht nicht den nun vorhandenen Akademie-PNGs.** Visuell
   nachgewiesen: Backend verwendet eine generische dunkle Karte statt der weissen
   Layouts mit Videoflix-Logo und Aktivierungs-/Reset-Button. Kein Auth-/API-Fehler;
   deshalb in diesem Integrationstest keine funktionierenden Backend-Maildienste
   umgebaut. Vorlage umsetzen und in Mailclients pruefen, bevor volle DoD behauptet wird.
2. **Rechtliche Seiten sind inhaltlich Platzhalter.** Privacy Policy enthaelt
   Lorem ipsum; Impressum Max Mustermann/Sample Street/info@example.com.
   Echte Betreiberangaben und passende Texte kann der Test nicht erfinden.
   Frontend-Herkunftskennzeichnung vor einer Veroeffentlichung ergaenzen.
3. **Abgabeorganisation:** PDF verlangt nur Backend im GitHub-Repo. Der lokale
   Frontend-Ordner ist vollstaendig unversioniert. Die Frontendkorrekturen separat
   sichern/einreichen und keine pauschale Aufnahme in das Backend-Repo vornehmen.
   Es wurde kein automatischer Commit/Push ausgefuehrt.
4. Echter SMTP-Versand und Darstellung in echten Mailclients bleiben ungeprueft;
   ebenso Safari/iOS/Firefox, produktives HTTPS und native HLS-Wiedergabe.
5. Originale Akademie-Docker-Dateien liegen weiterhin nicht identifizierbar vor;
   die existierende eigene Konfiguration blieb unveraendert. Frontend wird wie
   erlaubt separat gestartet; sein Docker-Service ist nicht Teil dieses Stacks.
6. CDN-Ausfall verhindert hls.js-Wiedergabe in Browsern ohne native HLS-Unterstuetzung.
   Das ist eine bestehende externe Laufzeitvoraussetzung, jetzt mit UI-Meldung.
   Generierte JSDoc ist historisch; Code und aktuelle READMEs sind massgeblich.

**Empfehlung: NICHT ABGABEBEREIT fuer die vollstaendige PDF-Checkliste.**
Frontend-/Backend-Kernintegration und geschuetzte HLS-Wiedergabe sind in Chromium
nachgewiesen funktionsfaehig. Vor der finalen Gesamtabgabe Maildesign, rechtliche
Inhalte und getrennte Repository-Abgabe abschliessen; fehlende SMTP-/Browsernachweise
gezielt nachholen. Docker- und Backend-Quellcode wurden unveraendert gelassen.

## Offizielles Akademie-Docker-Setup 22.10.2026

**Docker-Integrationsblocker behoben: kompatibel mit unveraenderten Originaldateien
PLUS eigener, separat dokumentierter Erweiterung.** Der unveraenderte Original-
Entrypoint allein ist mit dem E-Mail-User dieses Projekts nicht kompatibel.
Dieser aktuelle Abschnitt ersetzt saemtliche aelteren Aussagen in diesem Bericht,
dass offizielle Docker-Dateien fehlen oder nicht identifiziert werden konnten.
Die offenen Nicht-Docker-Punkte aus dem Frontendbericht bleiben bestehen.

### Quelle und unveraenderte Originale

Offizielles Repository:
https://github.com/Developer-Akademie-Backendkurs/material.videoflix-docker-files

Gepruefter main-Stand: `4796b17de2b7656d62b6904d4d04e5b74cbc41c6`
vom 05.11.2025; am 22.10.2026 heruntergeladen.
Alle sechs Repository-Dateien wurden untersucht und byte-identisch uebernommen:

- `docker/academy/original/backend.Dockerfile`
- `docker/academy/original/backend.entrypoint.sh`
- `docker/academy/original/docker-compose.yml`
- `docker/academy/original/.dockerignore`
- `docker/academy/original/.env.template`
- `docker/academy/original/README.md`

`docker/academy/upstream.json` dokumentiert Commit, Groessen, Git-Blob-SHA1 und
SHA256 aller Originale. Die Git-Blob-Pruefung besteht fuer alle sechs Dateien.
`.gitattributes` verhindert eine Veraenderung ihrer Zeilenenden durch Git.
Die oeffentlichen Beispielwerte der Original-env sind Referenzdaten; sie werden
niemals als Runtime-Zugangsdaten verwendet. Die eigenen lokalen Secrets sind
zufaellig generiert und liegen ausschliesslich in ignorierter `.runtime/.env`.

### Vergleich und notwendige Erweiterungen

| Bereich | Bisheriges eigenes Profil | Akademie-Original | Getestetes Akademie-Profil mit eigener Erweiterung |
|---|---|---|---|
| Dockerfile | Python 3.12 slim, FFmpeg, Gunicorn | Python 3.12 Alpine, FFmpeg/FFprobe, pg-client, Build-Werkzeuge | Exakt das unveraenderte offizielle Dockerfile; bestehende requirements unveraendert |
| Dienste | db, redis, migrate, backend, worker | db, redis, web; RQ im Web-Hintergrundprozess | db, redis, web erhalten; eigene migrate/worker-Dienste ergaenzt |
| DB-Image | postgres:16-alpine | postgres:latest | Eigene Erweiterung pinnt Major 18; eigene neue DB-Volumes, keine PG16-Daten uebernommen |
| Redis-Image | redis:7-alpine | redis:latest | Eigene Erweiterung pinnt Major 8 und aktiviert AOF |
| Container-/Netzwerknamen | Compose-Projekt videoflix | Feste Namen videoflix_database/redis/backend, Default-Netz | Feste Namen nur per Override zurueckgesetzt; alles im Projekt videoflix-academy |
| Host-Port | 127.0.0.1:8000 | 8000 auf allen Interfaces | Separat 127.0.0.1:8001; ACADEMY_HTTP_PORT konfigurierbar |
| DB-Volume | /var/lib/postgresql/data | /var/lib/postgresql | Offiziellen Mount beibehalten, neues videoflix-academy_postgres_data |
| Medien | media_data:/app/media | videoflix_media:/app/media | Offiziellen Volume-Key/Mount erhalten, projektspezifisch isoliert |
| Static | static_data:/app/staticfiles | videoflix_static:/app/static | Eigene Academy-Settings setzen STATIC_ROOT auf /app/static |
| Quellcode | Image-Snapshot | .:/app Bind-Mount | Eigene Erweiterung nutzt geprueften, generierten Build-Snapshot; kein Host-Bind |
| Env-Datei | Root .env | Root .env aus Originalkontext | Separate docker/academy/.runtime/.env; Root .env bleibt erhalten |
| Cache | CACHE_URL | REDIS_LOCATION | Eigene Academy-Settings lesen offiziellen Namen, bisherigen Namen als Fallback |
| CSRF/CORS | FRONTEND_ORIGINS | CSRF_TRUSTED_ORIGINS | Eigene Academy-Settings lesen offiziellen Namen; bestehende Middleware unveraendert |
| SMTP | EMAIL_USE_TLS | EMAIL_USE_TLS und EMAIL_USE_SSL | Eigene Settings ergaenzen EMAIL_USE_SSL; Test weiterhin Console-Mailbackend |
| Admin-Bootstrap | Manuell createsuperuser | User.objects.filter(username=...) | Eigener Bootstrap per DJANGO_SUPERUSER_EMAIL/PASSWORD, bestehendes Passwort bleibt erhalten |
| Startreihenfolge | Healthchecks und Migrate-Gate | DB-Warteschleife; nur depends_on fuer Redis | DB/Redis-Healthchecks, Migrate-Gate, begrenzte DB-Warteschleife und Restart-Policy |
| Startbefehle | Gunicorn / separater RQ | collectstatic, makemigrations, migrate, username-Admin, rqworker &, Gunicorn --reload | Eigener Entrypoint: migrate/collectstatic/bootstrap einmalig; Web/RQ jeweils im Vordergrund, keine generierten Migrationen beim Start |

**Tatsaechlich nachgewiesener Originalfehler:** Der offizielle Entrypoint wurde
im frisch isolierten Stack ausgefuehrt. 155 Static-Dateien und alle Initial-
Migrationen wurden erfolgreich eingerichtet. Danach Exit 1 mit
`django.core.exceptions.FieldError: Cannot resolve keyword 'username' into field`.
Der bestehende User besitzt absichtlich kein username-Feld. Deshalb keine
Aenderung an User-Modell, Manager, Authentifizierung oder Datenbankschema.
Der Original-Entrypoint bleibt exakt im Image; der eigene Compose-Override waehlt
explizit `academy/entrypoint.sh`. Das ist kein behaupteter Erfolg des Originals allein.

### Ausgefuehrte Tests und Ergebnisse

| Pruefung | Tatsaechliches Ergebnis |
|---|---|
| Originaldateien gegen Git-Blob-Hashes | Alle 6 unveraendert; SHA256 von Dockerfile und Original-Entrypoint auch im gebauten Container identisch |
| docker compose config --quiet mit Original + Erweiterung | Bestanden; effektive Service-/Volume-/Env-Key-Zuordnung ohne Secret-Ausgabe kontrolliert |
| Build mit unveraendertem backend.Dockerfile | Bestanden, inklusive unveraenderter Python-Abhaengigkeiten und FFmpeg/FFprobe |
| pip check im Alpine-Container | No broken requirements found |
| Vollstaendiger Start mit up --build -d --wait | Bestanden; db/redis/web healthy, migrate Exit 0; worker laeuft und ist in RQ registriert |
| Django check | Keine Probleme |
| makemigrations --check --dry-run | Keine Aenderungen erkannt |
| migrate --check und showmigrations | Alle Migrationen angewendet; keine neue Projektmigration erzeugt |
| Gesamte Testsuite lokal, core.test_settings | 60/60 bestanden, 1.889 s; bisherige 57 plus 3 neue Adapter-Regressionstests |
| Gesamte Testsuite im Academy-Alpine-Container, core.academy_test_settings | 60/60 bestanden, 0.824 s, keine ausgelassenen Tests |
| Neue Konfigurationstests | Vorrang von REDIS_LOCATION, Vorrang von CSRF_TRUSTED_ORIGINS, offizieller Static-Pfad und SSL-Schalter |
| Echter smoke_hls | Zweimal PASS: echter Admin-Upload, Redis-Cache, Queue, RQ-Worker/FFmpeg, authentifizierte Playlists und TS in 480p/720p/1080p, anonymer Zugriff abgewiesen |
| Vollstaendiges stop und anschliessendes up -d --wait | Bestanden; DB-Admin, Redis-Pruefwert und Datei im Medienvolume erhalten; eigene Pruefmarker danach entfernt |
| Admin-Bootstrap erneut ausgefuehrt | Idempotent; aktiver Superuser vorhanden, bestehender Passwort-Hash unveraendert |
| RQ nach Neustart | Genau ein registrierter Worker; echter HLS-Job danach erneut erfolgreich |
| Echte HTTP-Anfragen vom Host auf :8001 | CORS, CSRF, Bootstrap-Admin-Login, geschuetzte Videoliste, Refresh, Logout/Cookie-Loeschung und danach 401 bestanden |
| HTTP :8000 und :8001 | CSRF-Endpunkt, Admin-Loginseite und admin/css/base.css jeweils HTTP 200; bestehender Stack blieb erreichbar |
| Ruff E/F fuer Apps/core/eigene Skripte ohne historische Migrationen | Bestanden |
| Vorhandene Frontend-Regressionstests | Erneut 7/7 bestanden; kein erneuter Browser-HLS-Test gegen Port 8001 behauptet |
| Secret-/Fixture-Pruefung | .runtime ignoriert; keine .env im App-Image; Smoke-Benutzer/Videos/Medien bereinigt |

Getestete Laufzeit: Docker Engine 29.5.3, Compose 5.1.4, Python 3.12.15,
PostgreSQL 18.6, Redis 8.10.2, FFmpeg/FFprobe 8.1.2; Django/DRF/RQ-Versionen
unveraendert aus requirements.txt.

Image-Nachweise dieses Laufs:

- Python-Base: `python:3.12-alpine@sha256:92abd2ba1bdfb48b1e2ac224b582dd1558d0d4bb11c903b126b5bf9c448fd656`
- PostgreSQL: `postgres@sha256:83148c0bc09eac4d598b70a61e1404d0212b76c95c504bfd6c81a4c59ec91792`
- Redis: `redis@sha256:615b4cedaff0c1437a1548acae4222572df8c021eeb7382d64cb8b5e3a13ac7a`

Die Major-Tags und OS-Pakete bleiben beweglich. Getestet wurde das dokumentierte
Profil mit PG18/Redis8, nicht eine beliebige kuenftige Aufloesung der upstream
`latest`-Tags. Die offizielle README empfiehlt weitere Bibliotheken; fuer unsere
bestehende Redis-/Static-Implementierung war keine neue Laufzeitabhaengigkeit noetig.

### Fuer die Abgabe verwenden

**Original-Compose + eigene compose.compat.yaml ueber scripts/academy.ps1.**
Startanleitung, Voraussetzungen und Vergleich in `docker/academy/README.md` und
in der Root-README. Der Wrapper fixiert Projektname, Dateireihenfolge,
Projektverzeichnis und separate Env-Datei. PowerShell-Flags wie `-d` werden
unveraendert an Compose weitergegeben. Das Frontend bleibt separat auf Port 5500;
sein Default-Backend-Port 8000 wird durch diese Pruefung nicht automatisch umgestellt.

Neue eigene Dateien: `.gitattributes`, `core/academy_settings.py`,
`core/academy_test_settings.py`, `core/test_academy_settings.py`,
`scripts/prepare_academy.py`, `scripts/academy.ps1`,
`docker/academy/compose.compat.yaml`, `entrypoint.sh`, `bootstrap_admin.py`,
`.env.example`, `README.md`, `upstream.json` plus die sechs Originalreferenzen.
Root `.gitignore` ignoriert den generierten Runtime-Ordner und nimmt nur die
unveraenderte oeffentliche Referenz-env aus. Root `.dockerignore` erhaelt
lediglich einen Ausschluss fuer diesen neuen Runtime-Ordner, damit lokale Secrets
nicht in einen kuenftigen Build des bisherigen Profils gelangen.
Root `Dockerfile`, `compose.yaml`, `.env.example`, bestehende Settings,
Auth-/Video-Code und Migrationen wurden in diesem Auftrag nicht veraendert.
Bestehende Benutzer, Datenbank-/Medienvolumes und Netzwerk des alten Stacks
wurden nicht ersetzt. Kein down -v, kein Volume-Loeschen, kein Commit oder Push.

**Keine bekannten Docker-/RQ-/HLS-Abgabeblocker im getesteten erweiterten Profil.**
Die Gesamtabgabe bleibt gemaess Frontendbericht NICHT ABGABEBEREIT, solange
Maildesign und rechtliche Inhalte offen sind; SMTP/Mailclient-Nachweise und die
getrennte Verwaltung des unversionierten Akademie-Frontends bleiben zu beachten.
Eine Ausfuehrung ausschliesslich des unveraenderten Original-Entrypoints ohne
Adapter bleibt wegen des belegten username-Konflikts nicht moeglich.
