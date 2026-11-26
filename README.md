# Hockey Intelligence 13 — 0.1.1
Development Maukka

Personal NHL dashboard. Enable Settings > Pages > GitHub Actions, optionally add repository secret GROQ_API_KEY, then manually run Update NHL dashboard. Public Pages is publicly accessible. No API key is sent to the browser. Scheduled runs are UTC and may be delayed. News, injuries, trades and salary cap currently link to external sources only. Finnish players are matched by current roster birth country. No live API validation yet. SVG icon and PWA manifest included; offline support not implemented.

Local use: python3 update.py, then python3 -m http.server 8000 --directory site.

Changelog:
- 0.1.1: Groq model availability, safe HTTP diagnostics, per-run token counts and localized status panel.
- 0.1.0: Initial release.
