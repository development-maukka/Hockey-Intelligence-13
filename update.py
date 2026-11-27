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
    from groq import Groq
    with Groq(api_key=key, timeout=60.0, max_retries=1) as client:
        if endpoint == 'models':
            return client.models.list().model_dump()
        if endpoint == 'chat/completions':
            return client.chat.completions.create(**payload).model_dump()
        raise ValueError('Unsupported endpoint')

def safe_error(exc):
    status=getattr(exc,'status_code',None)
    if isinstance(status,int):
        return 'HTTP '+str(status)+' ('+type(exc).__name__+')'
    if isinstance(exc, urllib.error.HTTPError):
        return 'HTTP '+str(exc.code)
    if isinstance(exc, urllib.error.URLError):
        return 'Connection error'
    if isinstance(exc, TimeoutError):
        return 'Timeout'
    return type(exc).__name__

def compact_nhl(day, games, finns, standings, level=0):
    def name(v):
        return v.get('default','') if isinstance(v,dict) else (v or '')
    g=[ [x['awayTeam']['abbrev'],x['awayTeam'].get('score'),x['homeTeam']['abbrev'],x['homeTeam'].get('score'),x.get('gameState')] for x in games]
    p=[[name(x.get('name')),x.get('team'),x.get('goals'),x.get('assists'),x.get('saves')] for x in finns]
    s=[[name(x.get('teamAbbrev')),x.get('points'),x.get('l10Wins'),x.get('l10Losses'),x.get('l10OtLosses')] for x in standings]
    if level==1:
        p=[x for x in p if (x[2] or 0)+(x[3] or 0)>0 or (x[4] or 0)>0]
        s=sorted(s,key=lambda x:x[1] or 0,reverse=True)[:8]
    elif level>=2:
        p=sorted(p,key=lambda x:((x[2] or 0)+(x[3] or 0),x[4] or 0),reverse=True)[:8]
        s=[]
    return {'date':str(day),'detail_level':level,'games_columns':['away','away_score','home','home_score','state'],'games':g,'players_columns':['name','team','goals','assists','saves'],'players':p,'standings_columns':['team','points','last10_wins','last10_losses','last10_ot_losses'],'standings':s}

def compact_json(value):
    return json.dumps(value,ensure_ascii=False,separators=(',',':'))

def completion_with_budget(key,payload,day,games,finns,standings,ai,coverage_data):
    for level in range(3):
        facts=compact_nhl(day,games,finns,standings,level)
        if level==0:
            facts['news_headlines']=[x['title'][:180] for x in coverage_data.get('news',{}).get('items',[])[:6]]
            facts['reported_transactions']=[x['title'][:180] for x in coverage_data.get('transactions',{}).get('items',[])[:5]]
        raw=compact_json(facts)
        payload['messages'][1]['content']=raw
        size=len(compact_json(payload).encode('utf-8'))
        ai['payload_bytes']=size
        ai['estimated_input_tokens']=(size+2)//3
        ai['detail_level']=level
        print('Groq: payload bytes='+str(size)+'; estimated input tokens='+str(ai['estimated_input_tokens'])+'; detail level='+str(level),flush=True)
        if size>10000 and level<2:
            continue
        ai['attempted']+=1
        try:
            return groq_request('chat/completions',key,payload)
        except Exception as exc:
            if getattr(exc,'status_code',None)==413 and level<2:
                print('::warning::Groq HTTP 413; retrying with reduced data',flush=True)
                continue
            raise

def parse_brief(raw):
    raw=raw.strip()
    if raw.startswith('```'):
        raw=raw.split('\n',1)[-1].rsplit('```',1)[0].strip()
    parsed=json.loads(raw)
    if not isinstance(parsed,list) or not 1<=len(parsed)<=5:
        raise ValueError('Invalid briefing structure')
    items=[]
    for item in parsed:
        if not isinstance(item,dict) or not isinstance(item.get('title'),str) or not isinstance(item.get('body'),str):
            raise ValueError('Invalid briefing item')
        title=item['title'].strip()
        body=item['body'].strip()
        if not title or not body or len(title)>140 or len(body)>500:
            raise ValueError('Invalid briefing length')
        items.append({'title':title,'body':body})
    return items

ESPN='https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/'
def coverage():
    out={}
    for kind in ('news','injuries','transactions'):
        try:
            raw=get(ESPN+kind+'?limit=50')
            rows=[]
            if kind=='news':
                for a in raw['articles']:
                    rows.append({'title':a.get('headline'),'body':a.get('description'),'date':a.get('published'),'url':a.get('links',{}).get('web',{}).get('href')})
            elif kind=='injuries':
                for team in raw['injuries']:
                    for a in team.get('injuries',[]):
                        rows.append({'team':team.get('displayName'),'title':a.get('athlete',{}).get('displayName'),'status':a.get('status'),'body':a.get('shortComment'),'date':a.get('date'),'return':a.get('details',{}).get('returnDate')})
            else:
                for a in raw['transactions']:
                    team=a.get('team') or {}
                    rows.append({'title':a.get('description') or a.get('text') or a.get('headline'),'team':team.get('displayName') if isinstance(team,dict) else str(team),'date':a.get('date')})
            rows=[x for x in rows if x.get('title')]
            out[kind]={'status':'ok','source':'ESPN','items':rows[:50]}
            print('Coverage '+kind+': '+str(len(rows)),flush=True)
        except Exception as exc:
            out[kind]={'status':'error','source':'ESPN','items':[]}
            print('::warning::Coverage '+kind+': '+safe_error(exc),flush=True)
    out['cap']={'status':'not_configured','source':'PuckPedia / CapWages','items':[]}
    return out

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
    data['coverage']=coverage()
    key=os.getenv('GROQ_API_KEY','').strip()
    model=os.getenv('GROQ_MODEL','openai/gpt-oss-120b').strip()
    preferred=list(dict.fromkeys([model,'openai/gpt-oss-120b','openai/gpt-oss-20b','qwen/qwen3.8-27b']))
    candidates=[]
    ai={'status':'not_configured','model':model,'key_configured':bool(key),'model_available':None,'attempted':0,'successful':0,'tokens':{'prompt':0,'completion':0,'total':0},'last_success':None,'checked_at':utcnow(),'errors':[],'languages':{}}
    data['ai']=ai
    print('NHL: '+str(len(games))+' games; '+str(len(standings))+' teams; '+str(len(finns))+' Finnish players; '+str(len(errors))+' data warnings',flush=True)
    print('Groq: transport=official Python SDK',flush=True)
    print('Groq: API key configured: '+str(bool(key))+'; model: '+model,flush=True)
    if key:
        ai['status']='error'
        try:
            models=groq_request('models',key)
            available={m.get('id') for m in models.get('data',[]) if m.get('active',True)}
            candidates=[m for m in preferred if m in available]
            ai['model_available']=bool(candidates)
            ai['available_models']=sorted(x for x in available if isinstance(x,str))
            if candidates:
                model=candidates[0]
                ai['model']=model
            print('Groq: available models: '+', '.join(ai['available_models']),flush=True)
            print('Groq: selected model: '+model,flush=True)
            print('Groq: model available: '+str(ai['model_available']),flush=True)
            if not ai['model_available']:
                ai['errors'].append('No approved text model available')
                print('::warning::Groq no approved text model available',flush=True)
        except Exception as exc:
            msg=safe_error(exc)
            ai['errors'].append('Model check: '+msg)
            print('::warning::Groq model check: '+msg,flush=True)
        # A failed model-list request does not prove that completions are unavailable.
        if ai['model_available'] is None:
            candidates=preferred
        if candidates:
            for lang in ('fi','de','en'):
                for model in list(candidates):
                    print('Groq: requesting '+lang+' via '+model,flush=True)
                    try:
                        payload={'model':model,'messages':[{'role':'system','content':'Write a useful morning NHL news briefing in '+{'fi':'Finnish','de':'German','en':'English'}[lang]+'. Return ONLY a valid JSON array of 3 to 5 objects with keys title and body (fewer if there are fewer meaningful facts). Each title must be under 100 characters and each body 1 or 2 short sentences, at most 350 characters. Focus on notable finished games, outstanding Finnish player performances, streaks and meaningful standings changes only when supported. Do not repeat the standings or list all results. Distinguish games from season statistics. Attribute news headlines and reported transactions to ESPN; do not treat speculation as confirmed. Never invent facts, trends, injuries, news or rumors. No Markdown, no introduction, no code fences. Use natural journalistic language. On a day without games say so and highlight only genuinely noteworthy form.'},{'role':'user','content':''}]}
                        result=completion_with_budget(key,payload,day,games,finns,standings,ai,data['coverage'])
                        brief=result['choices'][0]['message']['content']
                        if not isinstance(brief,str) or not brief.strip():
                            raise ValueError('Empty completion')
                        data['brief'][lang]=parse_brief(brief)
                        usage=result.get('usage') or {}
                        tokens={k:int(usage.get(k+'_tokens') or 0) for k in ('prompt','completion','total')}
                        for k,v in tokens.items(): ai['tokens'][k]+=v
                        ai['successful']+=1
                        ai['model']=model
                        ai['model_available']=True
                        candidates=[model]+[x for x in candidates if x!=model]
                        ai['last_success']=utcnow()
                        ai['languages'][lang]={'status':'ok','tokens':tokens}
                        print('Groq: '+lang+' OK; tokens: '+str(tokens['total']),flush=True)
                        ai['languages'][lang]['model']=model
                        break
                    except Exception as exc:
                        msg=safe_error(exc)
                        ai['languages'][lang]={'status':'error','error':msg}
                        ai['errors'].append(lang+': '+msg)
                        print('::warning::Groq '+lang+' via '+model+': '+msg,flush=True)
                        status=getattr(exc,'status_code',None)
                        if status in (401,403):
                            candidates=[]
                            break
                        if status in (400,404,413,429) or isinstance(exc,ValueError):
                            candidates=[x for x in candidates if x!=model]
                            continue
                        break
        ai['status']='ok' if ai['successful']==3 else ('partial' if ai['successful'] else 'error')
    print('Groq: status='+ai['status']+'; completions='+str(ai['successful'])+'/'+str(ai['attempted'])+'; tokens='+str(ai['tokens']['total']),flush=True)
    path=Path('site/data.json'); tmp=path.with_suffix('.tmp'); tmp.write_text(json.dumps(data,ensure_ascii=False)); tmp.replace(path)
if __name__=='__main__': collect()
