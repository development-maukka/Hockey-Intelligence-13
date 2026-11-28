"""Verified goal timelines; no reconstruction from player totals or shootout attempts."""
def text(v):return str(v.get('default') or '') if isinstance(v,dict) else str(v or '')
def person(p):return ' '.join(text(p.get(k)) for k in ('firstName','lastName')).strip() or text(p.get('name'))
def mmss(v):
    parts=str(v).split(':')
    if len(parts)==1:
        n=int(parts[0]);m,s=divmod(n,100)
    else:m,s=map(int,parts)
    if m<0 or not 0<=s<60:raise ValueError('Invalid goal time')
    return m*60+s

def finish(rows,box,shootout=False):
    rows.sort(key=lambda r:(r['seconds'],r['awayScore']+r['homeScore']))
    a=h=0
    for r in rows:
        if r['team']==box['awayTeam']['abbrev']:a+=1
        elif r['team']==box['homeTeam']['abbrev']:h+=1
        else:raise ValueError('Unknown scoring team')
        if (r['awayScore'],r['homeScore'])!=(a,h) or not r['scorer']:raise ValueError('Incomplete goal sequence')
        r['time']=f"{r['seconds']//60:02}:{r['seconds']%60:02}"
    fa,fh=box['awayTeam']['score'],box['homeTeam']['score']
    if shootout:
        if a!=h or (fa,fh) not in ((a+1,h),(a,h+1)):raise ValueError('Shootout score mismatch')
    elif (a,h)!=(fa,fh):raise ValueError('Goal score mismatch')
    return {'status':'ok','goals':rows,'shootoutWinner':box['awayTeam']['abbrev'] if shootout and fa>fh else box['homeTeam']['abbrev'] if shootout else None}

def nhl_goals(raw,box):
    if raw.get('id')!=box['id']:raise ValueError('Game identity mismatch')
    if any(raw.get(side,{}).get('abbrev')!=box[side]['abbrev'] for side in ('homeTeam','awayTeam')):raise ValueError('Scoring team mismatch')
    groups=raw.get('summary',{}).get('scoring')
    if not isinstance(groups,list):raise ValueError('Missing scoring summary')
    rows=[]
    for group in groups:
        p=group['periodDescriptor'];period=p['number'];kind=p['periodType']
        if kind=='SO':continue
        for g in group['goals']:
            seconds=mmss(g['timeInPeriod'])+1200*min(period-1,3)+(max(period-4,0)*1200)
            assists=[person(a) for a in g['assists']] if isinstance(g.get('assists'),list) else None
            rows.append(dict(seconds=seconds,period=period,team=text(g['teamAbbrev']),scorer=person(g),assists=assists,awayScore=g['awayScore'],homeScore=g['homeScore']))
    shootout=box.get('gameOutcome',{}).get('lastPeriodType')=='SO' or raw.get('periodDescriptor',{}).get('periodType')=='SO'
    return finish(rows,box,shootout)

def nl_goals(raw,box,outcome):
    groups=raw.get('actions')
    if not isinstance(groups,list):raise ValueError('Missing game actions')
    rows=[]
    for group in groups:
        for g in group['actions']:
            if g.get('action')!='goal':continue
            # Shootout decisions are reported separately, never as assisted goals.
            if int(g['third'])>4:continue
            team=box['homeTeam']['abbrev'] if g['homeTeam'] else box['awayTeam']['abbrev']
            scorer=' '.join(str(g.get('player'+k) or '') for k in ('FirstName','LastName')).strip()
            assists=[' '.join(str(g.get(f'assist{i}'+k) or '') for k in ('FirstName','LastName')).strip() for i in (1,2)]
            rows.append(dict(seconds=mmss(g['time']),period=int(g['third']),team=team,scorer=scorer,assists=[a for a in assists if a],awayScore=g['awayTeamResult'],homeScore=g['homeTeamResult']))
    return finish(rows,box,outcome=='SO')

def liiga_goals(raw,box):
    game=raw['game'];rows=[]
    for side in ('homeTeam','awayTeam'):
        if not isinstance(game[side].get('goalEvents'),list):raise ValueError('Missing goal events')
        for g in game[side]['goalEvents']:
            if g['period']>4 or 'RL0' in g.get('goalTypes',[]):continue
            assists=[person(p) for p in g['assistantPlayers']] if isinstance(g.get('assistantPlayers'),list) else None
            rows.append(dict(seconds=g['gameTime'],period=g['period'],team=box[side]['abbrev'],scorer=person(g['scorerPlayer']),assists=assists,awayScore=g['awayTeamScore'],homeScore=g['homeTeamScore']))
    return finish(rows,box,game.get('finishedType')=='ENDED_DURING_WINNING_SHOT_COMPETITION')

def safe_goals(parse,*args):
    try:return parse(*args)
    except Exception as exc:return {'status':'error','goals':[],'error':type(exc).__name__}
