"""League-scoped rosters and game details from the leagues' public feeds."""
import concurrent.futures
import datetime
import json
from pathlib import Path

NL='https://www.nationalleague.ch'
LIIGA='https://liiga.fi/api/v2'

def key(value):return str(value).split(':',1)[0]
def number(v):
    if v is None or isinstance(v,bool):return None
    try:return float(v) if '.' in str(v) else int(v)
    except (ValueError,TypeError):return None

def clock(v,encoded=False):
    n=number(v)
    if n is None or n<0:return None
    n=int(n)
    seconds=(n//100)*60+n%100 if encoded else n
    if encoded and n%100>=60:return None
    return f'{seconds//60:02}:{seconds%60:02}'

def full_name(p):return ' '.join(str(p.get(k) or '') for k in ('firstName','lastName')).strip()
def position(v):return {'goalkeeper':'G','defender':'D','forwarder':'F','GOALKEEPER':'G','GOALIE':'G','STRIKER':'F','DEFENSEMAN':'D','CENTER':'C','LEFT_WING':'LW','RIGHT_WING':'RW'}.get(v,v)
def roster_row(p,liiga=False):
    return dict(id=p.get('id') if liiga else p.get('playerId'),name=full_name(p),number=p.get('jersey') if liiga else p.get('number'),position=position(p.get('role') if liiga else p.get('position')),country=p.get('nationality') or p.get('noc'))

def nl_box(raw,g,season):
    ov=raw.get('overview',{})
    if key(ov.get('gameId'))!=key(g['game_id']) or not key(g['game_id']).startswith(str(season)):raise ValueError('Game identity mismatch')
    out={'id':g['game_id'],'startTimeUTC':g['date'],'gameState':g['status'],'playerByGameStats':{}}
    for side in ('home','away'):
        if key(ov.get(side+'TeamId'))!=key(g[side+'_team_id']):raise ValueError('Team identity mismatch')
        teamstats=raw.get('teamStats'+side.title(),{});ps=raw.get('playerStats'+side.title())
        if not isinstance(ps,list) or not isinstance(teamstats,dict):raise ValueError('Missing box score')
        out[side+'Team']={'abbrev':g.get(side+'_code') or ov.get(side+'TeamShortName') or g[side+'_team_name'],'score':ov.get(side+'TeamResult'),'sog':teamstats.get('sog')}
        players={'forwards':[],'defense':[],'goalies':[]}
        for p in ps:
            goalie=p.get('position')=='goalkeeper'
            row={'name':{'default':p.get('name') or full_name(p)},'goals':p.get('g'),'assists':p.get('a'),'points':p.get('pts'),'sog':p.get('sog'),'toi':clock(p.get('mip') if goalie else p.get('toi'),True)}
            if goalie:
                rate=number(p.get('savePercentage'))
                row.update(saves=p.get('svs'),goalsAgainst=p.get('ga'),savePctg=rate/100 if rate is not None and p.get('sa') else None)
            players['goalies' if goalie else 'defense' if p.get('position')=='defender' else 'forwards'].append(row)
        out['playerByGameStats'][side+'Team']=players
    return out

def liiga_box(raw,stats,g,season):
    header=raw.get('game',{})
    if key(header.get('id'))!=key(g['game_id']) or header.get('season')!=season:raise ValueError('Game identity mismatch')
    out={'id':g['game_id'],'startTimeUTC':g['date'],'gameState':g['status'],'playerByGameStats':{},'playerShotsType':'attempts'}
    shots_against={}
    for side in ('home','away'):
        team=header.get(side+'Team',{});periods=stats.get(side+'Team')
        if key(team.get('teamId'))!=key(g[side+'_team_id']) or not isinstance(periods,list) or not periods:raise ValueError('Team statistics mismatch')
        names={key(p.get('id')):p for p in raw.get(side+'TeamPlayers',[])}
        accum={};seen=set();period_seen=set()
        for period in periods:
            pi=period.get('period')
            if pi in period_seen or not isinstance(pi,int) or pi<1:raise ValueError('Invalid periods')
            period_seen.add(pi)
            if key(period.get('teamId'))!=key(g[side+'_team_id']):raise ValueError('Period team mismatch')
            for group,goalie in (('periodPlayerStats',False),('goaliePeriodStats',True)):
                for p in period.get(group,[]):
                    pid=key(p.get('playerId'));unique=(pi,pid,goalie)
                    if unique in seen:raise ValueError('Duplicate period player')
                    seen.add(unique);bio=names.get(pid)
                    if not bio:raise ValueError('Player identity unavailable')
                    row=accum.setdefault((pid,goalie),dict(name={'default':full_name(bio)},position=position(bio.get('role')),goalie=goalie))
                    ps=p.get('period',{})
                    for target,source in (('goals','goals'),('assists','assists'),('points','points'),('sog','shots'),('seconds','timeofice'),('saves','saves'),('goalsAgainst','goalsAllowed'),('shotsAgainst','shotsOnGoal')):
                        value=number(ps.get(source))
                        if value is not None:row[target]=row.get(target,0)+value
        players={'forwards':[],'defense':[],'goalies':[]};sa=0;sa_known=False
        for (pid,goalie),p in accum.items():
            p['toi']=clock(p.pop('seconds',None));p['savePctg']=p.get('saves',0)/p['shotsAgainst'] if goalie and p.get('shotsAgainst') else None
            if goalie and 'shotsAgainst' in p:sa+=p['shotsAgainst'];sa_known=True
            players['goalies' if goalie else 'defense' if p['position']=='D' else 'forwards'].append({k:v for k,v in p.items() if k not in ('goalie','position','shotsAgainst')})
        shots_against[side]=sa if sa_known else None
        out[side+'Team']={'abbrev':g.get(side+'_code') or g[side+'_team_name'],'score':team.get('goals')}
        out['playerByGameStats'][side+'Team']=players
    out['homeTeam']['sog']=shots_against['away'];out['awayTeam']['sog']=shots_against['home']
    return out

def collect_details(league,entry,all_games,fetch,now,cache_dir='.detail-cache'):
    season=entry['season'];teams=entry['standings'];ids={key(t['team_id']) for t in teams}
    out={'updated':now.isoformat(),'source':entry['source'],'rosterBasis':'season','games':{},'history':{},'rosters':{}}
    # Season player endpoints include goalies and registered players with zero appearances.
    def roster(team):
        tid=key(team['team_id'])
        try:
            raw=fetch(f'{NL}/api/player/team/{tid}?season={season}')
            if not isinstance(raw,list) or not raw:raise ValueError('Empty roster')
            if any(key(p.get('teamId'))!=tid for p in raw):raise ValueError('Roster team mismatch')
            return tid,{'status':'ok','players':[roster_row(p) for p in raw]}
        except Exception as exc:return tid,{'status':'error','players':[],'error':type(exc).__name__}
    if league=='nl':
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:out['rosters']=dict(pool.map(roster,teams))
    else:
        try:
            raw=fetch(f'{LIIGA}/players/info?fromSeason={season}&toSeason={season}&tournament=runkosarja')
            if not isinstance(raw,list) or not raw:raise ValueError('Empty roster')
            for tid in ids:
                ps=[roster_row(p,True) for p in raw if key(p.get('teamId'))==tid and not p.get('removed')]
                out['rosters'][tid]={'status':'ok' if ps else 'error','players':ps}
        except Exception as exc:out['rosters']={tid:{'status':'error','players':[],'error':type(exc).__name__} for tid in ids}
    for t in teams:
        tid=key(t['team_id']);recent=sorted((g for g in all_games if g['status']=='finished' and tid in (key(g['home_team_id']),key(g['away_team_id'])) and g['score_home'] is not None and g['score_away'] is not None and datetime.datetime.fromisoformat(g['date'])<=now),key=lambda g:g['date'],reverse=True)[:10]
        rows=[]
        for g in recent:
            won=(g['score_home']>g['score_away'])==(tid==key(g['home_team_id']))
            outcome=g.get('outcome')
            rows.append(dict(id=g['game_id'],date=g['date'],away=g.get('away_code') or g['away_team_name'],home=g.get('home_code') or g['home_team_name'],away_score=g['score_away'],home_score=g['score_home'],outcome=outcome,result='W' if won else 'OT' if outcome in ('OT','SO') else 'L' if outcome=='REG' else None))
        out['history'][tid]={'status':'ok' if all_games else 'error','games':rows}
    cache=Path(cache_dir);cache.mkdir(parents=True,exist_ok=True)
    def box(g):
        gid=key(g['game_id']);path=cache/f'{league}_{season}_{gid}.json'
        try:
            if not gid.isdigit():raise ValueError('Invalid game id')
            if path.exists():
                saved=json.loads(path.read_text())
                if saved.get('identity')==[league,season,gid,key(g['home_team_id']),key(g['away_team_id']),g['score_home'],g['score_away']] and 0<=now.timestamp()-saved['fetched']<86400:return gid,{'status':'ok','data':saved['data']}
            if league=='nl':data=nl_box(fetch(f'{NL}/api/games/{gid}'),g,season)
            else:data=liiga_box(fetch(f'{LIIGA}/games/{season}/{gid}'),fetch(f'{LIIGA}/games/stats/{season}/{gid}'),g,season)
            if g['status']=='finished':path.write_text(json.dumps({'identity':[league,season,gid,key(g['home_team_id']),key(g['away_team_id']),g['score_home'],g['score_away']],'fetched':now.timestamp(),'data':data}))
            return gid,{'status':'ok','data':data}
        except Exception as exc:return gid,{'status':'error','error':type(exc).__name__}
    games=[g for g in entry['games'] if g['status'] in ('finished','live','in_progress')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:out['games']=dict(pool.map(box,games))
    print(f'Europe {league} details: {sum(v["status"]=="ok" for v in out["games"].values())}/{len(games)} boxes, {sum(v["status"]=="ok" for v in out["rosters"].values())}/{len(teams)} rosters',flush=True)
    return out
