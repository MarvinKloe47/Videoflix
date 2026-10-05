# Videoflix – Architecture

## 1. Zweck

Dieses Dokument beschreibt die geplante technische Architektur des
Videoflix-Backends.

Die Architektur orientiert sich an den Anforderungen der Developer Akademie
und soll während der Entwicklung als technischer Bauplan dienen.

Das Frontend und das Backend sind getrennte Anwendungen und kommunizieren
über eine REST-API.


---

# 2. Gesamtarchitektur

Die Anwendung besteht grundsätzlich aus folgenden Bereichen:

```text
┌─────────────────────┐
│      FRONTEND       │
│                     │
│ Registrierung       │
│ Login               │
│ Dashboard           │
│ Video Player        │
└──────────┬──────────┘
           │
           │ HTTP Request
           │ REST API
           ▼
┌─────────────────────┐
│   DJANGO BACKEND    │
│                     │
│ Django              │
│ Django REST         │
│ Framework           │
└──────────┬──────────┘
           │
           ├──────────────────┐
           │                  │
           ▼                  ▼
┌─────────────────┐   ┌─────────────────┐
│   PostgreSQL    │   │      Redis      │
│                 │   │                 │
│ Benutzer        │   │ Cache           │
│ Videos          │   │ Job Queue       │
│ Metadaten       │   │                 │
└─────────────────┘   └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │    Django RQ    │
                      │     Worker      │
                      │                 │
                      │ Background Jobs │
                      └────────┬────────┘
                               │
                               ▼
                      ┌─────────────────┐
                      │     FFmpeg      │
                      │                 │
                      │ Video → HLS     │
                      │ Thumbnail       │
                      └─────────────────┘
```


---

# 3. Geplante Django-Struktur

Das Backend wird in fachlich getrennte Django-Apps aufgeteilt.

```text
Videoflix/
│
├── docs/
│   ├── intent.md
│   ├── requirements.md
│   └── architecture.md
│
└── videoflix_backend/
    │
    ├── manage.py
    │
    ├── core/
    │
    ├── auth_app/
    │
    └── video_app/
```

## core

`core` enthält die zentrale Konfiguration des Django-Projekts.

Dazu gehören insbesondere:

- Django Settings
- zentrale URL-Konfiguration
- Datenbankkonfiguration
- REST-Framework-Konfiguration
- Redis-Konfiguration
- weitere globale Einstellungen


## auth_app

`auth_app` ist für Benutzer und Authentifizierung verantwortlich.

Dazu gehören:

- Registrierung
- Account-Aktivierung
- Login
- Logout
- Token-Erneuerung
- Passwort-Reset


## video_app

`video_app` ist für Videos und Streaming verantwortlich.

Dazu gehören:

- Video-Metadaten
- Videoübersicht
- Kategorien
- Thumbnails
- HLS-Manifeste
- HLS-Segmente
- Videoverarbeitung


---

# 4. Grundprinzip eines API-Requests

Ein Request durchläuft grundsätzlich mehrere Schichten.

Nicht jeder Request benötigt jede Schicht.

```text
Frontend
   │
   │ HTTP Request
   ▼
URL / Routing
   │
   ▼
View
   │
   ├──────────────┐
   │              │
   ▼              ▼
Serializer     Funktionen /
   │           Services
   ▼
Model
   │
   ▼
PostgreSQL
   │
   ▼
Response
   │
   ▼
Frontend
```

Die einzelnen Komponenten haben unterschiedliche Verantwortungen.


## URL / Routing

Die URL entscheidet, welche View für einen Request zuständig ist.

Beispiel:

```text
POST /api/register/
```

wird an die zuständige Registrierungs-View weitergeleitet.


## View

Die View nimmt den HTTP-Request entgegen.

Sie koordiniert die notwendigen Schritte und gibt anschließend eine
HTTP-Response zurück.

Komplexe Hilfslogik soll nicht direkt in der View implementiert werden.


## Serializer

Serializer bilden die Schnittstelle zwischen externen API-Daten und
Python-/Django-Daten.

Sie können insbesondere:

- eingehende Daten prüfen
- Daten validieren
- Python-Daten in JSON-fähige Daten umwandeln
- Daten für Models vorbereiten


## Model

Models beschreiben die Datenstruktur der Anwendung.

Django verwendet Models, um mit der PostgreSQL-Datenbank zu kommunizieren.

Beispiele:

```text
User
├── email
├── password
└── is_active
```

und:

```text
Video
├── title
├── description
├── category
├── created_at
└── thumbnail
```


## PostgreSQL

PostgreSQL ist die persistente Datenbank des Projekts.

Hier werden dauerhaft unter anderem gespeichert:

- Benutzer
- Video-Metadaten
- Kategorien
- benötigte Referenzen auf Dateien


---

# 5. Registrierung

Der Registrierungsprozess ist grundsätzlich folgendermaßen aufgebaut:

```text
Frontend
│
│ E-Mail
│ Passwort
│ Passwortbestätigung
│
│ POST /api/register/
▼
URL
│
▼
Registration View
│
▼
Serializer
│
├── Eingaben prüfen
├── Passwörter prüfen
└── E-Mail prüfen
│
▼
User Model
│
▼
PostgreSQL
│
│ User wird zunächst
│ inaktiv gespeichert
▼
Aktivierungs-E-Mail
│
▼
Response
│
▼
Frontend
```

Ein neuer Benutzer darf sich noch nicht anmelden, bevor sein Account
aktiviert wurde.


---

# 6. Account-Aktivierung

Nach der Registrierung erhält der Benutzer eine Aktivierungs-E-Mail.

Der Ablauf ist:

```text
Registrierung
      │
      ▼
Aktivierungs-E-Mail
      │
      ▼
Benutzer klickt Link
      │
      ▼
Frontend
      │
      │ Aktivierungsdaten
      ▼
Django Backend
      │
      ▼
Benutzer identifizieren
      │
      ▼
Aktivierung prüfen
      │
      ▼
User.is_active = True
      │
      ▼
PostgreSQL
      │
      ▼
Response
```

Erst danach darf sich der Benutzer anmelden.


---

# 7. Login und Authentifizierung

Der Login beginnt mit:

```text
Frontend
│
│ E-Mail
│ Passwort
│
│ POST /api/login/
▼
Backend
│
├── Benutzer suchen
├── Passwort prüfen
├── Account-Aktivierung prüfen
│
▼
Authentifizierung erfolgreich
│
▼
JWT Tokens
│
├── Access Token
└── Refresh Token
│
▼
HttpOnly Cookies
│
▼
Response
```

Die Tokens sollen nicht vom Frontend manuell gespeichert werden.

Sie werden über HttpOnly-Cookies übertragen.


## Access Token

Der Access Token dient zur Authentifizierung geschützter API-Anfragen.

Beispiel:

```text
GET /api/video/
```

Das Backend prüft:

```text
Request
   │
   ▼
Access Token vorhanden?
   │
   ├── Nein → Zugriff verweigern
   │
   └── Ja
        │
        ▼
    Token gültig?
        │
        ├── Nein → Zugriff verweigern
        │
        └── Ja → Request bearbeiten
```


## Refresh Token

Der Refresh Token ermöglicht die Ausstellung eines neuen Access Tokens,
wenn der bisherige Access Token abgelaufen ist.


---

# 8. Logout

Beim Logout wird die aktive Authentifizierung beendet.

```text
Frontend
   │
   │ POST /api/logout/
   ▼
Backend
   │
   ├── Refresh Token ungültig machen
   └── Auth-Cookies löschen
   │
   ▼
Response
```

Anschließend muss eine erneute Anmeldung notwendig sein, um geschützte
Inhalte aufzurufen.


---

# 9. Passwort-Reset

Der Passwort-Reset besteht aus zwei Schritten.


## Reset anfordern

```text
Frontend
│
│ E-Mail
▼
Backend
│
▼
Reset-Anfrage verarbeiten
│
▼
Reset-E-Mail
│
▼
Benutzer
```

Die Response darf nicht verraten, ob ein Benutzer mit der angegebenen
E-Mail-Adresse existiert.


## Neues Passwort setzen

```text
Reset-Link
    │
    ▼
Frontend
    │
    │ neues Passwort
    ▼
Backend
    │
    ├── Reset-Daten prüfen
    ├── Passwort validieren
    └── Passwort ändern
    │
    ▼
PostgreSQL
```


---

# 10. Video-Dashboard

Ein authentifizierter Benutzer kann verfügbare Videos abrufen.

```text
Frontend
   │
   │ GET /api/video/
   ▼
Authentication
   │
   ▼
Video View
   │
   ▼
Video Model
   │
   ▼
PostgreSQL
   │
   ▼
Video Serializer
   │
   ▼
JSON Response
   │
   ▼
Frontend Dashboard
```

Die Video-Daten enthalten die für das Frontend benötigten Metadaten wie:

- ID
- Titel
- Beschreibung
- Kategorie
- Erstellungsdatum
- Thumbnail


---

# 11. Videoverarbeitung

Die Videoverarbeitung kann rechenintensiv sein und soll deshalb nicht
innerhalb eines normalen HTTP-Requests durchgeführt werden.

Dafür werden Redis und Django RQ verwendet.

```text
Video
  │
  ▼
Background Job erstellen
  │
  ▼
Redis Queue
  │
  ▼
Django RQ Worker
  │
  ▼
FFmpeg
  │
  ├── 480p
  ├── 720p
  ├── 1080p
  └── Thumbnail
  │
  ▼
HLS Dateien
```

Dadurch kann das Backend weiterhin Requests beantworten, während Videos im
Hintergrund verarbeitet werden.


---

# 12. HLS Streaming

Videos werden für die Wiedergabe als HLS bereitgestellt.

Vereinfacht besteht ein verarbeitetes Video aus:

```text
Video
│
├── 480p/
│   ├── index.m3u8
│   ├── 000.ts
│   ├── 001.ts
│   └── ...
│
├── 720p/
│   ├── index.m3u8
│   ├── 000.ts
│   └── ...
│
└── 1080p/
    ├── index.m3u8
    ├── 000.ts
    └── ...
```


## Manifest Request

```text
Video Player
     │
     │ GET .../720p/index.m3u8
     ▼
Django
     │
     ├── Authentifizierung prüfen
     └── Manifest bereitstellen
     │
     ▼
.m3u8
```


## Segment Request

Anschließend fordert der Player die benötigten Videosegmente an:

```text
Video Player
     │
     │ GET .../720p/000.ts
     ▼
Django
     │
     ├── Authentifizierung prüfen
     └── Segment bereitstellen
     │
     ▼
.ts Datei
```

Der Player lädt während der Wiedergabe nacheinander die benötigten Segmente.


---

# 13. Redis

Redis übernimmt im Projekt zwei wichtige Aufgaben.

## Caching

Häufig benötigte Daten können temporär im Arbeitsspeicher gehalten werden,
damit nicht jede Anfrage erneut auf die persistente Datenbank zugreifen muss.


## Queue

Redis dient außerdem als Warteschlange für Django RQ.

```text
Django
   │
   │ Job
   ▼
Redis
   │
   │ nächster Job
   ▼
RQ Worker
```


---

# 14. E-Mail

Das Backend muss E-Mails für mindestens folgende Prozesse versenden können:

```text
E-Mail
│
├── Account-Aktivierung
│
└── Passwort-Reset
```

Die Links führen zunächst zum Frontend.

Das Frontend verarbeitet die notwendigen Parameter und kommuniziert
anschließend mit dem Backend.


---

# 15. Docker

Für die Abgabe soll das Projekt vollständig über Docker gestartet werden
können.

Die geplante Infrastruktur besteht grundsätzlich aus:

```text
Docker
│
├── Django Backend
│
├── PostgreSQL
│
├── Redis
│
└── Django RQ Worker
```

Die konkrete Docker-Konfiguration richtet sich nach dem von der Developer
Akademie bereitgestellten Setup.


---

# 16. Verantwortlichkeiten

Die Architektur soll nach dem Prinzip der klaren Verantwortlichkeiten
aufgebaut werden.

```text
urls.py
    → Routing

views.py
    → HTTP Request / Response

serializers.py
    → API-Daten und Validierung

models.py
    → Datenstruktur und Datenbank

functions.py / utils.py
    → wiederverwendbare Hilfslogik

tasks.py
    → Background Tasks
```

Eine Komponente soll nicht unnötig Aufgaben einer anderen Komponente
übernehmen.


---

# 17. Architekturprinzip

Für die Entwicklung gilt:

> So einfach wie möglich, aber so strukturiert wie nötig.

Es werden nur Komponenten und Abstraktionen eingeführt, die für die
Anforderungen des Videoflix-Projekts benötigt werden.

Die Architektur kann während der Implementierung konkretisiert werden,
wenn neue technische Erkenntnisse entstehen.