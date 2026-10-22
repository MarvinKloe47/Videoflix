# Videoflix – Requirements

## 1. Ziel

Dieses Dokument beschreibt die Anforderungen an das Videoflix-Projekt.

Die Anforderungen basieren auf der Definition of Done der Developer Akademie.
Es werden keine zusätzlichen Produktfeatures umgesetzt, die für die Abgabe
nicht erforderlich sind.


# 2. Benutzer & Authentifizierung

## REQ-001 – Benutzerregistrierung

Ein neuer Benutzer muss sich mit folgenden Informationen registrieren können:

- E-Mail-Adresse
- Passwort
- Passwortbestätigung


## REQ-002 – Validierung der Registrierung

Die eingegebenen Registrierungsdaten müssen überprüft werden.

Eine Registrierung darf insbesondere nicht erfolgreich durchgeführt werden,
wenn die eingegebenen Daten ungültig sind oder die E-Mail-Adresse bereits
verwendet wird.


## REQ-003 – Allgemeine Fehlermeldungen

Bei einer fehlerhaften Registrierung dürfen keine unnötigen Informationen
über bestehende Benutzerkonten preisgegeben werden.

Fehlermeldungen müssen deshalb allgemein formuliert sein.


## REQ-004 – Inaktiver Account

Ein neu registrierter Benutzer darf nicht sofort vollständig aktiviert sein.

Der Account muss zunächst inaktiv bleiben.


## REQ-005 – Aktivierungs-E-Mail

Nach einer erfolgreichen Registrierung muss eine Aktivierungs-E-Mail an die
angegebene E-Mail-Adresse gesendet werden.


## REQ-006 – Account-Aktivierung

Ein Benutzer muss seinen Account über den Link aus der Aktivierungs-E-Mail
aktivieren können.

Erst nach erfolgreicher Aktivierung darf der Benutzer sich anmelden.


## REQ-007 – Benutzeranmeldung

Ein registrierter und aktivierter Benutzer muss sich mit folgenden Daten
anmelden können:

- E-Mail-Adresse
- Passwort


## REQ-008 – Login-Fehler

Bei ungültigen Login-Daten oder einem noch nicht aktivierten Account muss
die Anmeldung abgelehnt werden.

Fehlermeldungen müssen aus Sicherheitsgründen allgemein gehalten sein.


## REQ-009 – Authentifizierter Zugriff

Geschützte Videoflix-Inhalte dürfen nur für authentifizierte Benutzer
zugänglich sein.


## REQ-010 – Benutzerabmeldung

Ein angemeldeter Benutzer muss sich sicher von Videoflix abmelden können.

Nach der Abmeldung dürfen geschützte Inhalte nicht mehr ohne erneute
Authentifizierung erreichbar sein.


## REQ-011 – Passwort-Reset anfordern

Ein Benutzer muss über seine E-Mail-Adresse einen Passwort-Reset anfordern
können.


## REQ-012 – Datenschutz beim Passwort-Reset

Bei einer Passwort-Reset-Anfrage darf nicht offengelegt werden, ob zu der
angegebenen E-Mail-Adresse ein Benutzerkonto existiert.


## REQ-013 – Passwort-Reset-E-Mail

Für den Passwort-Reset muss eine E-Mail mit einem entsprechenden Link
versendet werden.


## REQ-014 – Neues Passwort setzen

Über den Passwort-Reset-Link muss der Benutzer ein neues Passwort festlegen
können.

Nach erfolgreicher Änderung muss das neue Passwort für zukünftige
Anmeldungen verwendet werden können.


# 3. Videobibliothek

## REQ-015 – Videoübersicht

Ein angemeldeter Benutzer muss eine Übersicht der verfügbaren Videos
abrufen können.


## REQ-016 – Videoinformationen

Für Videos müssen die für das Dashboard benötigten Informationen
bereitgestellt werden.

Dazu gehören insbesondere:

- Titel
- Beschreibung
- Kategorie
- Erstellungsdatum
- Thumbnail


## REQ-017 – Sortierung

Videos müssen nach ihrem Erstellungsdatum absteigend bereitgestellt werden.

Neuere Videos stehen damit vor älteren Videos.


## REQ-018 – Kategorien

Videos müssen nach Genres beziehungsweise Kategorien gruppiert dargestellt
werden können.


## REQ-019 – Hero-Inhalt

Für den Hero-Bereich muss ein hervorgehobener Video-Teaser beziehungsweise
ein geeignetes Standbild bereitgestellt werden können.


## REQ-020 – Thumbnail

Für jedes Video muss ein Thumbnail beziehungsweise ein geeignetes Bild aus
dem Video zur Verfügung stehen.


# 4. Video-Streaming

## REQ-021 – Videowiedergabe

Ein angemeldeter Benutzer muss verfügbare Videos über Videoflix streamen
können.


## REQ-022 – HLS

Videos müssen für die Wiedergabe im benötigten HLS-Format bereitgestellt
werden können.


## REQ-023 – Videoauflösungen

Ein Video muss in folgenden Auflösungen bereitgestellt werden können:

- 480p
- 720p
- 1080p


## REQ-024 – Manuelle Qualitätsauswahl

Der Benutzer muss zwischen den verfügbaren Videoauflösungen wählen können.


## REQ-025 – HLS-Manifeste

Die für die Videowiedergabe benötigten M3U8-Dateien müssen bereitgestellt
werden können.


## REQ-026 – HLS-Segmente

Die zur Wiedergabe benötigten Videosegmente müssen bereitgestellt werden
können.


# 5. Technische Anforderungen

## REQ-027 – Frontend und Backend

Frontend und Backend müssen voneinander getrennt sein.

Die Kommunikation zwischen beiden Anwendungen erfolgt über eine REST-API.


## REQ-028 – Django REST Framework

Für die REST-API des Backends muss Django REST Framework verwendet werden.


## REQ-029 – PostgreSQL

Als Datenbanksystem muss PostgreSQL anstelle von SQLite verwendet werden.


## REQ-030 – Redis

Redis muss als Main-Memory-Datenbank beziehungsweise Caching Layer
eingesetzt werden.


## REQ-031 – Background Tasks

Aufwendige Aufgaben müssen im Hintergrund ausgeführt werden.

Hierfür muss Django RQ verwendet werden.


## REQ-032 – Videoverarbeitung

Die benötigte Verarbeitung beziehungsweise Umwandlung der Videos für HLS
muss unterstützt werden.


## REQ-033 – Docker

Das Projekt muss für die Abgabe vollständig über Docker-Container gestartet
werden können.


# 6. Codequalität

## REQ-034 – Clean Code

Der Backend-Code muss den Clean-Code-Vorgaben der Developer Akademie
entsprechen.


## REQ-035 – Funktionsgröße

Funktionen sollen maximal 14 Zeilen lang sein.


## REQ-036 – Single Responsibility

Jede Funktion soll genau eine Aufgabe erfüllen.


## REQ-037 – Namenskonventionen

Funktionsnamen müssen der snake_case-Konvention folgen.

Variablen und Funktionen müssen aussagekräftige Namen besitzen.


## REQ-038 – Ungenutzter Code

Ungenutzte Variablen und Funktionen dürfen nicht im finalen Projekt
vorhanden sein.

Auskommentierter, nicht mehr benötigter Code muss entfernt werden.


## REQ-039 – Django-Dateistruktur

Code muss entsprechend seiner Verantwortung in den richtigen Dateien
abgelegt werden.

Views, die Responses zurückgeben, gehören in `views.py`.

Hilfsfunktionen sollen in geeignete Dateien wie `functions.py` oder
`utils.py` ausgelagert werden.


## REQ-040 – Python Style

Der Python-Code soll, soweit möglich, PEP-8-konform geschrieben werden.


# 7. Dokumentation

## REQ-041 – README

Das Backend-Projekt muss eine aussagekräftige README.md enthalten.


## REQ-042 – Projektdokumentation

Die für das Verständnis und die Verwendung des Backends erforderliche
Dokumentation muss vorhanden sein.


# 8. Abgabe

## REQ-043 – Backend-Repository

Das für die Abgabe verwendete Repository darf nur das Backend-Projekt
enthalten.


## REQ-044 – Vorgegebene Docker-Dateien

Von der Developer Akademie bereitgestellte Docker-Dateien dürfen nicht
eigenmächtig verändert werden.


# 9. Nicht Bestandteil des Projekts

Funktionen, die nicht von der Developer Akademie gefordert werden, werden
nicht ohne konkreten Bedarf implementiert.

Dazu gehören beispielsweise:

- Benutzerprofile bearbeiten
- Benutzerkonten löschen
- Bewertungen
- Kommentare
- Watchlists
- Abonnements
- Bezahlsysteme
- Videosuche
- Social Features

Diese Funktionen können grundsätzlich Teil einer Streaming-Plattform sein,
gehören jedoch nicht zu den Anforderungen dieser Videoflix-Abgabe.