# Hockey Intelligence 13 — 0.3.9
Development Maukka

Personal NHL, National League and Liiga dashboard. European statistics use sportsdataverse 0.2.0b1 with the official National League and Liiga sources; install it for local runs. SIHF public access is discontinued. European news, transfer and injury reports show dated source headlines from swisshockeynews.ch and Jatkoaika, with SuomiKiekko as the Liiga fallback. Injury reports are not a current absence register; source text remains in its original language. European data failures do not block the NHL update. Enable Settings > Pages > GitHub Actions, optionally add repository secret GROQ_API_KEY, then manually run Update NHL dashboard. Public Pages is publicly accessible. No API key is sent to the browser. Scheduled runs are UTC and may be delayed. ESPN news, transactions and injuries are collected automatically, subject to endpoint availability. Source text is displayed in its original language. Salary cap uses the public CC0 nhl-contracts mirror at EyeWall Analytics; estimates are not official cap space. Transfer rumours are labelled separately from other contract reports. Finnish players are matched by current roster birth country. No live API validation yet. SVG icon and PWA manifest included; offline support not implemented.

Local use: python3 -m pip install 'groq>=0.30,<2', then python3 update.py, then python3 -m http.server 8000 --directory site.

Changelog:
- 0.3.9: Corrected the final game status. Improved National League tables on phones.
- 0.3.8: Added today’s NHL games and pregame odds.
- 0.3.7: Added National League and Liiga news, transfer reports and injury updates.
- 0.3.6: Fixed National League and Liiga scores, standings and player statistics.
- 0.3.5: Improved browser shortcut icons.
- 0.3.4: Added a language selector in settings.
- 0.3.3: Improved briefing language and factual accuracy.
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

NHL matchdays use America/New_York; tip-off dates and times display in device local time. The new Today & odds view uses NHL schedules and optional ESPN scoreboard DraftKings two-way pregame moneylines converted to decimal. This market includes overtime and shootouts ([provider rules](https://sportsbook.draftkings.com/help/general-betting-rules/general-rules)). Only matching start times and both team identities are joined; missing quotes never become estimates. Opening, live, spread and regulation-only markets are not substituted. Retrieved time is collection time, since the feed does not supply a quote update time. Data follows scheduled dashboard updates and is not a live betting feed. After start, pregame prices are hidden. Current and following NHL matchdays are collected to support midnight rollover; missing current-day data is shown explicitly.

