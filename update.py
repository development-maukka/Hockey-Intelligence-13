import json, os, datetime, urllib.request, urllib.error, concurrent.futures
from zoneinfo import ZoneInfo
from pathlib import Path
BASE='https://api-web.nhle.com/v1/'
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Hockey Intelligence 13/0.1'}),timeout=25) as r: return json.load(r)
def nhl(path): return get(BASE+path)
def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def groq_request(endpoint, key, payload=None):
    headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'}
    req=urllib.request.Request('https://api.groq.com/openai/v1/'+endpoint, data=json.dumps(payload).encode() if payload is not None else None, headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)

def safe_error(exc):
    if isinstance(exc, urllib.error.HTTPError):
        return 'HTTP '+str(exc.code)
    if isinstance(exc, urllib.error.URLError):
        return 'Connection error'
    if isinstance(exc, TimeoutError):
        return 'Timeout'
    return type(exc).__name__

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
    key=os.getenv('GROQ_API_KEY','').strip()
    model=os.getenv('GROQ_MODEL','llama-3.3-70b-versatile')
    ai={'status':'not_configured','model':model,'key_configured':bool(key),'model_available':None,'attempted':0,'successful':0,'tokens':{'prompt':0,'completion':0,'total':0},'last_success':None,'checked_at':utcnow(),'errors':[],'languages':{}}
    data['ai']=ai
    print('NHL: '+str(len(games))+' games; '+str(len(standings))+' teams; '+str(len(finns))+' Finnish players; '+str(len(errors))+' data warnings',flush=True)
    print('Groq: API key configured: '+str(bool(key))+'; model: '+model,flush=True)
    if key:
        ai['status']='error'
        try:
            models=groq_request('models',key)
            ai['model_available']=any(m.get('id')==model for m in models.get('data',[]))
            print('Groq: model available: '+str(ai['model_available']),flush=True)
            if not ai['model_available']:
                ai['errors'].append('Configured model not listed')
                print('::warning::Groq configured model not listed',flush=True)
        except Exception as exc:
            msg=safe_error(exc)
            ai['errors'].append('Model check: '+msg)
            print('::warning::Groq model check: '+msg,flush=True)
        # A failed model-list request does not prove that completions are unavailable.
        if ai['model_available'] is not False:
            compact={'games':[{k:g.get(k) for k in ('awayTeam','homeTeam','gameState')} for g in games],'finns':finns,'standings':[{k:s.get(k) for k in ('teamAbbrev','points','l10Wins','l10OtLosses')} for s in standings]}
            for lang in ('fi','de','en'):
                ai['attempted']+=1
                print('Groq: requesting '+lang,flush=True)
                try:
                    payload={'model':model,'messages':[{'role':'system','content':'Write a concise NHL briefing in '+{'fi':'Finnish','de':'German','en':'English'}[lang]+'. Use only supplied facts. Do not invent news, injuries or rumors. Plain text.'},{'role':'user','content':json.dumps(compact)}]}
                    result=groq_request('chat/completions',key,payload)
                    brief=result['choices'][0]['message']['content']
                    if not isinstance(brief,str) or not brief.strip():
                        raise ValueError('Empty completion')
                    data['brief'][lang]=brief.strip()
                    usage=result.get('usage') or {}
                    tokens={k:int(usage.get(k+'_tokens') or 0) for k in ('prompt','completion','total')}
                    for k,v in tokens.items(): ai['tokens'][k]+=v
                    ai['successful']+=1
                    ai['last_success']=utcnow()
                    ai['languages'][lang]={'status':'ok','tokens':tokens}
                    print('Groq: '+lang+' OK; tokens: '+str(tokens['total']),flush=True)
                except Exception as exc:
                    msg=safe_error(exc)
                    ai['languages'][lang]={'status':'error','error':msg}
                    ai['errors'].append(lang+': '+msg)
                    print('::warning::Groq '+lang+': '+msg,flush=True)
        ai['status']='ok' if ai['successful']==3 else ('partial' if ai['successful'] else 'error')
    print('Groq: status='+ai['status']+'; completions='+str(ai['successful'])+'/'+str(ai['attempted'])+'; tokens='+str(ai['tokens']['total']),flush=True)
    path=Path('site/data.json'); tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False)); tmp.replace(path)
if __name__=='__main__': collect()
