# Videoflix - implementierte Architektur

Stand: 21.10.2026. Verbindlich sind die PDF-Checkliste und die API-Dokumentation.
Dieses Dokument beschreibt den vorhandenen Stand; Abnahme und Risiken stehen in
`ABGABE_CHECK.md`, konkrete Startbefehle in `../README.md`.

Separates Frontend -> Django/DRF -> PostgreSQL.
Django -> Redis DB 0 (RQ) -> Linux-RQ-Worker -> FFprobe/FFmpeg -> persistentes Media-Volume.
Django -> Redis DB 1 (Video-Metadaten-Cache, 60 Sekunden).

`auth_app` besitzt das E-Mail-Usermodell und die dokumentierten Auth-Endpunkte.
CookieJWTAuthentication prueft JWT, Passwortaenderung, Sitzungsblacklist und CSRF.
Refresh prueft Benutzerstatus und Passwortstand separat. E-Mail-Links gehen zum
Frontend; Plaintext und eigenes responsives HTML werden gemeinsam versendet.

`video_app` liefert eine flache, nach Erstellungsdatum absteigende PUBLIC-Liste.
Genres sind `category`-Anzeigewerte; Gruppen bildet das Frontend. Geschuetzte
Thumbnails und HLS-Assets werden ausschliesslich nach Authentifizierung und
aktueller Sichtbarkeitspruefung gelesen. Originaldateien werden nicht angeboten.

`pre_save` erkennt Quelldateiaenderungen und erzeugt eine neue Job-UUID.
`post_save` registriert Queue- und Cache-Aktionen mit `transaction.on_commit`.
RQ-Jobeindeutigkeit und DB-Zeilensperren verhindern doppelte Konvertierungen.
Nur READY-Assets werden ausgeliefert. Fehler werden im Admin und in RQ sichtbar.
Die lange Konvertierungstransaktion verbirgt PROCESSING bis zum Abschluss fuer
andere Verbindungen und kann gleichzeitiges Bearbeiten desselben Videos blockieren.

FFmpeg generiert HLS in maximal der Quellaufloesung. Thumbnails werden separat
hochgeladen, nicht automatisch durch FFmpeg erzeugt. MP4-Dateien unter 480p
werden abgelehnt. API-Pfade und Formate bleiben gemaess `APIDoku_Videoflix (1).txt`.

`core` enthaelt Konfiguration, Origins/CSRF/CORS und Routing. `.env` bleibt lokal.
Docker trennt Backend, einmalige Migrationen, DB, Redis und Worker. Die eigene
Docker-Konfiguration ersetzt keine vorgegebenen Akademie-Dateien; solche lagen
nicht vor. Admin-Static wird lokal mit Django bedient; oeffentliches Deployment
benoetigt eine eigene TLS-/Static-Proxy-Konfiguration.

Tests nutzen weiterhin PostgreSQL, isolieren aber Cache und E-Mail im Prozess.
Der Smoke-Test verwendet die echte Queue, den laufenden Worker und Redis-Cache.
