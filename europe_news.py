"""Dated headlines and source links; reports are not a live injury register."""
import datetime
import re
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

SHN='https://swisshockeynews.ch'
JATKO='https://www.jatkoaika.com'
SOURCES={'nl':{'news':SHN+'/en/national-league','transactions':SHN+'/en/national-league','injuries':SHN+'/en/national-league/medicals'},'liiga':{k:JATKO+'/LIIGA' for k in ('news','transactions','injuries')}}


def fetch_page(url):
    with urlopen(Request(url,headers={'User-Agent':'Hockey Intelligence 13/0.3.7'}),timeout=25) as response:
        return response.read(3_000_000).decode('utf-8')


def report_kind(title):
    text=title.casefold()
    injury=bool(re.search(r'loukkaantu|leikkauk|sivuun|sivussa|sairastu|toipila|paluuarvio|palaa kokoonpano|palasi kokoonpano|injur|infirmary|health|comeback|out indefinitely|returns? to .*lineup',text))
    transfer=bool(re.search(r'sopimuk|jatkosopimus|solmi .*jatkon|jatkaa .*asti|jatkaa .*saakka|siirty|hankki|vahvistukse|purki|pelaajakau|contract|signs?\b|signed\b|joins?\b|join\b|extends?\b|loan\b|future lie|interested in|interest from|negotiat|parts? ways',text))
    return injury,transfer


def transfer_status(title):
    # A headline match selects a report; it never proves a completed transfer.
    return 'rumour' if re.search(r'\?|reportedly|might|could|interested|interest |neuvotte|huhu|tietojen mukaan|negotiat',title,re.I) else 'report'


def item(title,url,date,source,language):
    date=datetime.datetime.fromisoformat(date).isoformat() if 'T' in date else datetime.date.fromisoformat(date).isoformat()
    if urlsplit(url).scheme!='https' or urlsplit(url).hostname not in ('swisshockeynews.ch','www.swisshockeynews.ch','www.jatkoaika.com','jatkoaika.com'):
        raise ValueError('Unexpected article destination')
    return dict(title=title.strip()[:300],url=url,date=date,source=source,language=language)


def parse_shn(html,medical=False):
    soup=BeautifulSoup(html,'html.parser')
    cards=soup.select('.timeline article')
    if not cards:
        raise ValueError('News list not found')
    rows=[]
    for card in cards+soup.select('article.raxo-item-top'):
        a=card.select_one('.raxo-title a[href]');d=card.select_one('.raxo-date')
        if a is None or d is None:continue
        path=a['href']
        if medical:
            if '/shn/medical/' not in path:continue
        elif '/shn/men/swiss-hockey/nl/' not in path:continue
        try:date=datetime.datetime.strptime(d.get_text(strip=True),'%d.%m.%Y').date().isoformat()
        except ValueError:continue
        rows.append(item(a.get_text(' ',strip=True),urljoin(SHN,path),date,'swisshockeynews.ch','en'))
    return rows


def parse_jatko(html):
    soup=BeautifulSoup(html,'html.parser');cards=soup.select('.article-list-item')
    if not cards:raise ValueError('Liiga news list not found')
    rows=[]
    for card in cards:
        a=card.select_one('a.article-list-item--link[href]');title=card.select_one('.article-list-item--title');d=card.select_one('time[datetime]')
        if a is None or title is None or d is None:continue
        url=urljoin(JATKO,a['href'])
        if '/Uutiset/' not in url:continue
        rows.append(item(title.get_text(' ',strip=True),url,d['datetime'],'Jatkoaika','fi'))
    return rows


def recent_unique(rows,now,days=30):
    cutoff=now.date()-datetime.timedelta(days=days);seen=set();out=[]
    for row in sorted(rows,key=lambda x:x['date'],reverse=True):
        date=datetime.date.fromisoformat(row['date'][:10])
        if date<cutoff or date>now.date() or row['url'] in seen:continue
        seen.add(row['url']);out.append(row)
    return out[:30]


def national_league_report(title,teams,players):
    import unicodedata
    def norm(value):return unicodedata.normalize('NFKD',value.casefold()).encode('ascii','ignore').decode()
    text=norm(title)
    if any(x in text for x in ('women', 'dames', 'mesplede', 'academy')):return False
    aliases=['ajoie','ambri','bern','scb','biel','davos','hcd','fribourg','gotteron','hcfg','geneve','servette','kloten','lausanne','lhc','lugano','lakers','rapperswil','scl','tigers','zsc','zug']
    names=[norm(t.get('team_name','')) for t in teams]+aliases
    names += [norm(p.get('player_name','').split()[-1]) for p in players if p.get('player_name') and len(p['player_name'].split()[-1])>4]
    return any(re.search(r'(?<![a-z])'+re.escape(n)+r'(?![a-z])',text) for n in names if n)


def collect_coverage(league,now,fetch=fetch_page,teams=(),players=()):
    urls=SOURCES[league];out={};cache={}
    for kind,url in urls.items():
        result=dict(status='error',items=[],url=url,updated=now.isoformat(),source='swisshockeynews.ch' if league=='nl' else 'Jatkoaika',report_type='dated_reports')
        try:
            if url not in cache:
                try:cache[url]=fetch(url)
                except Exception as exc:cache[url]=exc
            if isinstance(cache[url],Exception):raise cache[url]
            rows=parse_shn(cache[url],medical=kind=='injuries') if league=='nl' else parse_jatko(cache[url])
            if not rows:raise ValueError('No dated league articles parsed')
            rows=recent_unique(rows,now)
            if league=='nl' and kind=='injuries':rows=[r for r in rows if national_league_report(r['title'],teams,players)]
            if kind=='transactions':
                rows=[dict(r,report_status=transfer_status(r['title'])) for r in rows if report_kind(r['title'])[1]]
            elif kind=='injuries' and league=='liiga':rows=[r for r in rows if report_kind(r['title'])[0]]
            result.update(status='ok',items=rows)
        except Exception as exc:
            result['error']=type(exc).__name__
        print(f'Europe {league} {kind}: {result["status"]} ({len(result["items"])})',flush=True)
        out[kind]=result
    return out
