"""Small, independently failing NHL detail snapshots for interactive views."""
import concurrent.futures
import datetime

def name(value):return value.get('default','') if isinstance(value,dict) else str(value or '')

def normalize_roster(raw):
    if not isinstance(raw,dict) or not all(isinstance(raw.get(k),list) for k in ('forwards','defensemen','goalies')):raise ValueError('Incomplete roster')
    rows=[]
    for group in ('forwards','defensemen','goalies'):
        for p in raw[group]:
            rows.append({'id':p['id'],'name':(name(p.get('firstName'))+' '+name(p.get('lastName'))).strip(),'number':p.get('sweaterNumber'),'position':p.get('positionCode'),'country':p.get('birthCountry'),'group':group})
    return rows

def last_ten(raw,team,now):
    if not isinstance(raw.get('games'),list):raise ValueError('Missing schedule')
    rows=[]
    for g in raw['games']:
        if g.get('gameType')!=2 or g.get('gameState') not in ('OFF','FINAL'):continue
        try:
            start=datetime.datetime.fromisoformat(g['startTimeUTC'].replace('Z','+00:00'))
            if start.tzinfo is None or start>now:continue
            away,home=g['awayTeam'],g['homeTeam'];a,h=away['score'],home['score']
            if team not in (away['abbrev'],home['abbrev']) or not isinstance(a,int) or not isinstance(h,int) or a==h:continue
            won=(h>a) if home['abbrev']==team else (a>h)
            period=g.get('gameOutcome',{}).get('lastPeriodType')
            if not won and period not in ('REG','OT','SO'):raise ValueError('Missing final period type')
            rows.append({'id':g['id'],'date':start.isoformat(),'away':away['abbrev'],'home':home['abbrev'],'away_score':a,'home_score':h,'outcome':period,'result':'W' if won else ('OT' if period in ('OT','SO') else 'L')})
        except (KeyError,TypeError):raise ValueError('Incomplete final game')
    rows.sort(key=lambda x:(x['date'],x['id']),reverse=True)
    unique={}
    for row in rows:unique.setdefault(row['id'],row)
    return list(unique.values())[:10]

def box_detail(raw,game_id):
    if raw.get('id')!=game_id or not isinstance(raw.get('playerByGameStats'),dict):raise ValueError('Incomplete box score')
    for side in ('awayTeam','homeTeam'):
        if not isinstance(raw.get(side),dict) or not raw[side].get('abbrev') or not isinstance(raw['playerByGameStats'].get(side),dict):raise ValueError('Missing team statistics')
    return {k:raw.get(k) for k in ('id','gameDate','startTimeUTC','gameState','awayTeam','homeTeam','playerByGameStats','gameOutcome')}

def collect_details(games,teams,now,nhl,cached_boxes=None):
    cache=cached_boxes or {};out={'updated':now.isoformat(),'source':'NHL','games':{},'history':{}}
    unique={g['id']:g for g in games if g.get('gameState') in ('OFF','FINAL','LIVE','CRIT')}
    def box(pair):
        game_id,g=pair
        try:
            raw=cache.get(game_id) or nhl(f'gamecenter/{game_id}/boxscore')
            return str(game_id),dict(status='ok',data=box_detail(raw,game_id))
        except Exception as exc:return str(game_id),dict(status='error',error=type(exc).__name__)
    def history(team):
        try:return team,dict(status='ok',games=last_ten(nhl(f'club-schedule-season/{team}/now'),team,now))
        except Exception as exc:return team,dict(status='error',games=[],error=type(exc).__name__)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        out['games']=dict(pool.map(box,unique.items()))
        out['history']=dict(pool.map(history,teams))
    print('NHL details:',sum(v['status']=='ok' for v in out['games'].values()),'boxes;',sum(v['status']=='ok' for v in out['history'].values()),'team histories',flush=True)
    return out
