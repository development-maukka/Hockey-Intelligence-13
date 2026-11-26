import json, os, datetime, urllib.request, concurrent.futures
from zoneinfo import ZoneInfo
from pathlib import Path
BASE='https://api-web.nhle.com/v1/'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Hockey Intelligence 13/0.1'}),timeout=25) as r: return json.load(r)
def nhl(path): return get(BASE+path)
def collect():
    now=datetime.datetime.now(ZoneInfo('Europe/Zurich')); day=now.date()-datetime.timedelta(days=1)
    standings=nhl('standings/now')['standings']; games=nhl('score/'+str(day))['games']
    def box(g):
        try: return nhl(f"gamecenter/{g['id']}/boxscore")
        except Exception: return None
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool: boxes=list(pool.map(box,games))
    finns=[]; errors=[]; rosters={}
    def roster(t):
        try: return t,nhl('roster/'+t+'/current')
        except Exception: return t,None
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for t,r in pool.map(roster,[s['teamAbbrev']['default'] for s in standings]):
            if r is None: errors.append('Roster: '+t); continue
            for group in r.values():
                if isinstance(group,list):
                    for p in group:
                        if p.get('birthCountry')=='FIN': rosters[p['id']]=p
    for g,b in zip(games,boxes):
        if not b: errors.append('Boxscore: '+str(g['id'])); continue
        for side in ('awayTeam','homeTeam'):
            for group in b.get('playerByGameStats',{}).get(side,{}).values():
                for p in group:
                    if p.get('playerId') in rosters: finns.append(dict(p,team=b[side]['abbrev']))
    data={'updated':now.isoformat(),'date':str(day),'games':games,'standings':standings,'finns':finns,'errors':errors,'brief':{}}
    key=os.getenv('GROQ_API_KEY')
    if key:
        compact={'games':[{k:g.get(k) for k in ('awayTeam','homeTeam','gameState')} for g in games],'finns':finns,'standings':[{k:s.get(k) for k in ('teamAbbrev','points','l10Wins','l10OtLosses')} for s in standings]}
        for lang in ('fi','de','en'):
            try:
                payload={'model':os.getenv('GROQ_MODEL','llama-3.3-70b-versatile'),'messages':[{'role':'system','content':'Write a concise NHL briefing in '+lang+'. Use only supplied facts. Do not invent news, injuries or rumors. Plain text.'},{'role':'user','content':json.dumps(compact)}]}
                req=urllib.request.Request('https://api.groq.com/openai/v1/chat/completions',data=json.dumps(payload).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=60) as r: data['brief'][lang]=json.load(r)['choices'][0]['message']['content']
            except Exception: errors.append('AI: '+lang)
    path=Path('site/data.json'); tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False)); tmp.replace(path)
if __name__=='__main__': collect()
