# Supplied email design references

`activation.png`, `password_reset.png` and `Logo.svg` were copied unchanged from
`Videoflix_frontend/EmailTemplates_Backend/` supplied with the course frontend.
They are design references for the backend emails, not frontend application code.
The original course license is retained as LICENSE.md.

Entwickelt im Rahmen des Weiterbildungsprogramms der Developer Akademie GmbH.

The implemented HTML preserves the white background, blue call-to-action, logo
placement and message hierarchy of those references. Mail-client chrome in the
screenshots is not part of the template. The inline-email PNG is a 2x rasterization
of the supplied SVG, not a newly invented brand asset. Personalized names are
escaped in HTML; raw links remain usable in the plain-text part.

The reset reference mentions 24 hours. The implementation displays the actual
configured Django timeout (currently its default 72 hours), preserving existing
API/token behavior. Tests also cover a 24-hour override. Browser render checks were
performed at widths 390px and 900px; they do not replace Outlook/Gmail/mobile
mail-client testing. No external SMTP was used without authorized test credentials.
