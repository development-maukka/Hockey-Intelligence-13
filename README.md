# Hockey Intelligence 13 — 0.3.2
Development Maukka

Personal NHL, National League and Liiga dashboard. European statistics use optional sportsdataverse 0.2.0b1; install it separately for local runs. European news, injuries and transactions currently link to external sources. European data failures do not block the NHL update. Enable Settings > Pages > GitHub Actions, optionally add repository secret GROQ_API_KEY, then manually run Update NHL dashboard. Public Pages is publicly accessible. No API key is sent to the browser. Scheduled runs are UTC and may be delayed. ESPN news, transactions and injuries are collected automatically, subject to endpoint availability. Source text is displayed in its original language. Salary cap uses the public CC0 nhl-contracts mirror at EyeWall Analytics; estimates are not official cap space. National League injuries link directly to the Sport.ch Medical Report pending verified ingestion; rumours are not collected separately. Finnish players are matched by current roster birth country. No live API validation yet. SVG icon and PWA manifest included; offline support not implemented.

Local use: python3 -m pip install 'groq>=0.30,<2', then python3 update.py, then python3 -m http.server 8000 --directory site.

Changelog:
- 0.3.2: Added settings for theme and followed leagues.
- 0.3.1: Added NHL salary cap estimates and a National League medical report link.
- 0.3.0: Added National League and Liiga sections.
- 0.2.1: Added team logos to news, transactions and injury reports.
- 0.2.0: Added division standings, news, transactions and injury reports.
- 0.1.5: Redesigned the interface and made daily briefings easier to read.
- 0.1.4: Improved AI briefing reliability.
- 0.1.3: Automatically selects an available AI model and switches to a fallback when needed.
- 0.1.2: Official Groq Python SDK, safe HTTP status diagnostics and workflow syntax check.
- 0.1.1: Groq model availability, safe HTTP diagnostics, per-run token counts and localized status panel.
- 0.1.0: Initial release.
