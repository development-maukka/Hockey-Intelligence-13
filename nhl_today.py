"""NHL matchday schedules and explicitly identified pregame moneylines."""
import datetime
import math
from zoneinfo import ZoneInfo

EASTERN=ZoneInfo('America/New_York')
ESPN='https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard?dates='
ALIASES={'LA':'LAK','SJ':'SJS','TB':'TBL','NJ':'NJD','WSH':'WSH','UTAH':'UTA'}

def decimal_odds(value):
    if isinstance(value,bool):return None
    try:n=float(value)
    except (ValueError,TypeError):return None
    if not math.isfinite(n) or abs(n)<100:return None
    return round(1+n/100 if n>0 else 1+100/abs(n),4)

def instant(value):
    d=datetime.datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Missing time zone')
    return d.astimezone(datetime.timezone.utc)

def event_key(start,away,home):
    def code(x):return ALIASES.get(x,x)
    return (instant(start),code(away),code(home))

def parse_odds(raw,now):
    out={}
    for event in raw.get('events',[]):
        for competition in event.get('competitions',[]):
            try:
                sides={c['homeAway']:c['team']['abbreviation'] for c in competition['competitors']}
                key=event_key(competition.get('date') or event['date'],sides['away'],sides['home'])
                state=competition.get('status',event.get('status',{})).get('type',{}).get('state')
                if state!='pre' or key[0]<=now:continue
                for quote in competition.get('odds',[]):
                    provider=quote.get('provider',{}).get('name')
                    # Only this provider's two-way market settlement has been verified.
                    if provider!='DraftKings':continue
                    money=quote.get('moneyline',{})
                    home=decimal_odds(money.get('home',{}).get('close',{}).get('odds'))
                    away=decimal_odds(money.get('away',{}).get('close',{}).get('odds'))
                    if home is None or away is None:continue
                    out[key]={'home':home,'away':away,'provider':provider,'source':'ESPN','market':'winner_including_ot_so','checked_at':now.isoformat()}
                    break
            except (ValueError,TypeError,KeyError):continue
    return out

def collect_today(now,fetch,nhl):
    day=now.astimezone(EASTERN).date()
    result={'updated':now.isoformat(),'timezone':'America/New_York','days':[]}
    for offset in (0,1):
        date=day+datetime.timedelta(days=offset)
        row={'date':date.isoformat(),'status':'error','odds_status':'error','games':[]}
        try:
            raw=nhl('score/'+str(date))
            if not isinstance(raw.get('games'),list):raise ValueError('Schedule missing')
            row.update(status='ok',games=raw['games'])
        except Exception as exc:
            print('NHL schedule:',date,type(exc).__name__,flush=True)
        try:
            quotes=parse_odds(fetch(ESPN+date.strftime('%Y%m%d')+'&limit=100'),now)
            row['odds_status']='ok'
            for game in row['games']:
                if game.get('gameState') not in ('FUT','PRE'):continue
                key=event_key(game['startTimeUTC'],game['awayTeam']['abbrev'],game['homeTeam']['abbrev'])
                if key in quotes:game['pregame_odds']=quotes[key]
        except Exception as exc:
            print('NHL odds:',date,type(exc).__name__,flush=True)
        result['days'].append(row)
    return result
