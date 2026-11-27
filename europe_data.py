"""Normalize the leagues' official season tables into the dashboard schema."""
import datetime
import json
from zoneinfo import ZoneInfo


def normalize(league, kind, rows):
    out = []
    for r in rows:
        if r.get('row_type', 'data') != 'data':
            continue
        if league == 'liiga' and r.get('tournament') not in (None, 'runkosarja', 'regular'):
            continue
        if kind == 'standings':
            x = dict(team_id=r.get('team_id'), team_name=r.get('name') if league == 'nl' else r.get('team_name'),
                     rank=r.get('rank') if league == 'nl' else r.get('ranking'),
                     games_played=r.get('gp') if league == 'nl' else r.get('games'),
                     points=r.get('po') if league == 'nl' else r.get('points'),
                     goals_for=r.get('g') if league == 'nl' else r.get('goals'),
                     goals_against=r.get('ga') if league == 'nl' else r.get('goals_against'),
                     team_logo=r.get('team_logos_light_bg'))
            if not x['team_name'] or x['rank'] is None or x['points'] is None:
                raise ValueError('Incomplete standings row')
        elif kind == 'players':
            if r.get('position') == 'goalkeeper' or r.get('goalkeeper'):
                continue
            x = dict(player_id=r.get('player_id'), player_name=' '.join(str(r.get(k) or '') for k in ('first_name', 'last_name')).strip(),
                     team_id=r.get('team_id'), team_name=r.get('team_name'),
                     games_played=r.get('gp') if league == 'nl' else r.get('played_games', r.get('games')),
                     goals=r.get('g') if league == 'nl' else r.get('goals'), assists=r.get('assists'), points=r.get('points'))
            if not x['player_name'] or x['points'] is None:
                raise ValueError('Incomplete player row')
        else:
            if league == 'nl' and r.get('is_exhibition'):
                continue
            date = r.get('date') if league == 'nl' else r.get('start')
            if not date:
                raise ValueError('Missing game date')
            start = datetime.datetime.fromisoformat(date.replace('Z', '+00:00'))
            status = r.get('base_status') or r.get('status') if league == 'nl' else ('finished' if r.get('ended') else 'live' if r.get('started') else 'scheduled')
            x = dict(game_id=r.get('game_id'), date=start.astimezone(ZoneInfo('Europe/Zurich' if league == 'nl' else 'Europe/Helsinki')).isoformat(),
                     home_team_id=r.get('home_team_id'), away_team_id=r.get('away_team_id'),
                     home_team_name=r.get('home_team_name') if league == 'nl' else r.get('home_name'),
                     away_team_name=r.get('away_team_name') if league == 'nl' else r.get('away_name'), status=status,
                     score_home=r.get('home_team_result') if league == 'nl' else r.get('home_goals'),
                     score_away=r.get('away_team_result') if league == 'nl' else r.get('away_goals'))
            if status not in ('finished', 'live', 'in_progress', 'playing'):
                x['score_home'] = x['score_away'] = None
            if not x['home_team_name'] or not x['away_team_name']:
                raise ValueError('Missing team name')
        out.append(x)
    if kind == 'standings':
        out.sort(key=lambda x: x['rank'])
        if len({x['team_id'] for x in out}) != len(out):
            raise ValueError('Duplicate standings teams')
    if kind == 'players':
        out.sort(key=lambda x: (x['points'], x['goals'] or 0), reverse=True)
    return out


def form(standings, games):
    records = []
    for team in standings:
        recent = sorted((g for g in games if g['status'] == 'finished' and team['team_id'] in (g['home_team_id'], g['away_team_id']) and g['score_home'] is not None and g['score_away'] is not None), key=lambda g: g['date'], reverse=True)[:10]
        wins = sum((g['score_home'] > g['score_away']) == (team['team_id'] == g['home_team_id']) for g in recent)
        records.append(dict(team_name=team['team_name'], games=len(recent), wins=wins, losses=len(recent)-wins))
    return sorted(records, key=lambda x: x['wins'], reverse=True)


def collect_league(league, season, now, error_text):
    if league == 'nl':
        from sportsdataverse.hockey.nl import nl_standings, nl_schedule, nl_player_stats
        calls = {'standings': lambda: nl_standings(season=season), 'games': lambda: nl_schedule(season=season), 'players': lambda: nl_player_stats(season=season)}
    else:
        from sportsdataverse.hockey.liiga import liiga_standings, liiga_games, liiga_player_stats
        calls = {'standings': lambda: liiga_standings(season=season), 'games': lambda: liiga_games(season=season, tournament='runkosarja'), 'players': lambda: liiga_player_stats(season_from=season, season_to=season, tournament='runkosarja')}
    entry = dict(standings=[], games=[], players=[], form=[], brief={}, errors=[], season=season, source='National League' if league == 'nl' else 'Liiga', source_url='https://www.nationalleague.ch/' if league == 'nl' else 'https://liiga.fi/', updated=now.isoformat())
    all_games = []
    for name, call in calls.items():
        try:
            rows = normalize(league, name, call().to_dicts())
            if not rows:
                raise ValueError('Empty '+name)
            if name == 'games':
                all_games = rows
                start = now.date() - datetime.timedelta(days=7)
                end = now.date() + datetime.timedelta(days=1)
                rows = [r for r in rows if start <= datetime.date.fromisoformat(r['date'][:10]) <= end]
            entry[name] = rows
            print(f'Europe {league} {name}: {len(rows)}', flush=True)
        except Exception as exc:
            entry['errors'].append(name+': '+error_text(exc))
            print(f'Europe {league} {name}: {type(exc).__name__}: {str(exc)[:200]}', flush=True)
    entry['form'] = form(entry['standings'], all_games)
    entry['status'] = 'partial' if entry['errors'] else 'ok'
    return entry
