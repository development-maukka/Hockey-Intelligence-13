# Hockey Intelligence 13 — 0.1.5
Development Maukka

Personal NHL dashboard. Enable Settings > Pages > GitHub Actions, optionally add repository secret GROQ_API_KEY, then manually run Update NHL dashboard. Public Pages is publicly accessible. No API key is sent to the browser. Scheduled runs are UTC and may be delayed. News, injuries, trades and salary cap currently link to external sources only. Finnish players are matched by current roster birth country. No live API validation yet. SVG icon and PWA manifest included; offline support not implemented.

Local use: python3 -m pip install 'groq>=0.30,<2', then python3 update.py, then python3 -m http.server 8000 --directory site.

Changelog:
- 0.1.5: Redesigned the interface and made daily briefings easier to read.
- 0.1.4: Improved AI briefing reliability.
- 0.1.3: Automatically selects an available AI model and switches to a fallback when needed.
- 0.1.2: Official Groq Python SDK, safe HTTP status diagnostics and workflow syntax check.
- 0.1.1: Groq model availability, safe HTTP diagnostics, per-run token counts and localized status panel.
- 0.1.0: Initial release.
