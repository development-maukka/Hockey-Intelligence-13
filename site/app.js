const supportedLanguages=['fi','de','en'];
let languagePreference='auto';try{const saved=localStorage.getItem('hockey-language');if(supportedLanguages.includes(saved))languagePreference=saved}catch{}
const deviceLanguage=(navigator.language||'en').slice(0,2).toLowerCase();
const lang=languagePreference==='auto'?(supportedLanguages.includes(deviceLanguage)?deviceLanguage:'en'):languagePreference;
document.documentElement.lang=lang;
const t={
fi:{overview:'Katsaus',today:'Tänään & kertoimet',games:'Ottelut',finns:'Suomalaiset',standings:'Sarjataulukko',form:'Kuntopuntari',news:'Uutiset',trades:'Siirrot',injuries:'Loukkaantumiset',cap:'Palkkakatto',info:'Info',brief:'Aamukatsaus',updated:'Päivitetty',loading:'Ladataan…',empty:'Ei vielä tietoa.',error:'Tietojen lataus epäonnistui.',partial:'Osittainen data',team:'Joukkue',away:'Vieras',home:'Koti',score:'Tulos',status:'Tila',points:'P',played:'O',name:'Pelaaja',goals:'M',assists:'S',saves:'Torj.',source:'Avaa tietolähde',external:'Tietoja ei vielä kerätä automaattisesti.',dark:'Tumma teema',light:'Vaalea teema',refresh:'Päivitä',diagnostics:'AI-diagnostiikka',model:'Malli',calls:'Onnistuneet analyysit',tokens:'Tokenit',last:'Viimeisin onnistuminen tässä ajossa',available:'Malli saatavilla',yes:'Kyllä',no:'Ei',unknown:'Ei tiedossa',ok:'Toimii',errorStatus:'Virhe',partialStatus:'Osittainen',not_configured:'Ei määritetty',changelog:'Muutosloki',l10:'V–T–JA',aiNote:'AI-katsaus perustuu kerättyihin tilastoihin.'},
de:{overview:'Übersicht',today:'Heute & Quoten',games:'Spiele',finns:'Finnen',standings:'Tabelle',form:'Formkurve',news:'News',trades:'Transfers',injuries:'Verletzungen',cap:'Salary Cap',info:'Info',brief:'Morgenbericht',updated:'Aktualisiert',loading:'Laden…',empty:'Noch keine Daten.',error:'Daten konnten nicht geladen werden.',partial:'Unvollständige Daten',team:'Team',away:'Gast',home:'Heim',score:'Resultat',status:'Status',points:'Pkt',played:'Sp',name:'Spieler',goals:'T',assists:'A',saves:'Par.',source:'Quelle öffnen',external:'Noch keine automatische Datenerfassung.',dark:'Dunkles Design',light:'Helles Design',refresh:'Aktualisieren',diagnostics:'AI-Diagnose',model:'Modell',calls:'Erfolgreiche Analysen',tokens:'Tokens',last:'Letzter Erfolg in diesem Lauf',available:'Modell verfügbar',yes:'Ja',no:'Nein',unknown:'Unbekannt',ok:'Aktiv',errorStatus:'Fehler',partialStatus:'Teilweise',not_configured:'Nicht konfiguriert',changelog:'Änderungen',l10:'S–N–OT',aiNote:'Der AI-Bericht basiert auf erfassten Statistiken.'},
en:{overview:'Overview',today:'Today & odds',games:'Games',finns:'Finnish players',standings:'Standings',form:'Form guide',news:'News',trades:'Trades',injuries:'Injuries',cap:'Salary cap',info:'Info',brief:'Morning briefing',updated:'Updated',loading:'Loading…',empty:'No data yet.',error:'Unable to load data.',partial:'Partial data',team:'Team',away:'Away',home:'Home',score:'Score',status:'Status',points:'Pts',played:'GP',name:'Player',goals:'G',assists:'A',saves:'Sv',source:'Open source',external:'Automatic collection is not implemented yet.',dark:'Dark theme',light:'Light theme',refresh:'Refresh',diagnostics:'AI diagnostics',model:'Model',calls:'Successful analyses',tokens:'Tokens',last:'Last success in this run',available:'Model available',yes:'Yes',no:'No',unknown:'Unknown',ok:'Operational',errorStatus:'Error',partialStatus:'Partial',not_configured:'Not configured',changelog:'Changelog',l10:'W–L–OT',aiNote:'The AI briefing uses collected statistics.'}
}[lang];
const tabs=['overview','today','games','finns','standings','form','news','trades','injuries','cap','info'];
const $=id=>document.getElementById(id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
let data=null,failed=false,active='overview',serial=0;
function getStored(){try{return localStorage.getItem('hockey-theme')}catch{return null}}
let theme=getStored()|| (matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');
$('refresh').title=$('refresh').ariaLabel=t.refresh;
function section(title){const s=el('section');s.append(el('h2',title));$('main').append(s);return s}
function table(s,headers,rows){if(!rows.length){s.append(el('p',t.empty,'muted'));return}const wrap=el('div',undefined,'table-wrap'),tb=el('table'),head=el('thead'),hr=el('tr'),body=el('tbody');for(const h of headers){const th=el('th',h);th.scope='col';hr.append(th)}head.append(hr);for(const row of rows){const tr=el('tr');for(const x of row)tr.append(el('td',x??'—'));body.append(tr)}tb.append(head,body);wrap.append(tb);s.append(wrap)}
function nav(){leagueNav();const n=$('nav');n.replaceChildren();for(const id of leagueTabs()){const b=el('button',tabName(id));b.type='button';b.setAttribute('aria-current',String(id===active));b.onclick=()=>go(id);n.append(b)}n.querySelector('[aria-current=true]')?.scrollIntoView({block:'nearest',inline:'nearest'})}
function go(id){active=leagueTabs().includes(id)?id:'overview';if(location.hash!=='#'+active)history.replaceState(null,'','#'+active);render();window.scrollTo(0,0)}
function modules(s){const g=el('div',undefined,'modules');for(const id of leagueTabs().slice(1,-1)){const b=el('button');b.type='button';b.append(el('span',tabName(id)),el('span','›'));b.onclick=()=>go(id);g.append(b)}s.append(g)}
const clean=s=>String(s??'').replace(/\*\*|__|^[#]+\s*|^\s*[-•]\s*/gm,'').trim();
function brief(s,value){let items=[];if(Array.isArray(value)){items=value.filter(x=>x&&typeof x.title==='string'&&typeof x.body==='string').slice(0,5)}else if(typeof value==='string'){try{const v=JSON.parse(value);if(Array.isArray(v))items=v.filter(x=>x&&typeof x.title==='string'&&typeof x.body==='string').slice(0,5)}catch{}if(!items.length){const lines=value.replace(/\r/g,'').replace(/\*\*([^*\n]+)\*\*/g,'\n$1\n').split(/\n+/).map(clean).filter(Boolean);for(const line of lines){items.push({title:'',body:line});if(items.length>=12)break}}}if(!items.length){s.append(el('p',t.empty,'muted'));return}for(const item of items){const b=el('article',undefined,'brief-item');if(item.title)b.append(el('h3',clean(item.title)));b.append(el('p',clean(item.body)));s.append(b)}s.append(el('small',t.aiNote))}
function info(s){s.append(el('p','Development Maukka'),el('h3',t.changelog));for(const line of ['0.5.1 — Fixed missing Liiga scoring leaders.','0.5.0 — Added National League and Liiga game statistics, rosters and recent results. Added team logos across National League and Liiga views.','0.4.0 — Added NHL game statistics, team rosters and recent results. Added team logos to NHL games and form guide.'])s.append(el('p',line));const a=data?.ai;if(!a)return;const d=el('details'),status={ok:t.ok,partial:t.partialStatus,error:t.errorStatus,not_configured:t.not_configured}[a.status]||t.unknown;d.append(el('summary',t.diagnostics+' · '+status));table(d,[t.diagnostics,''],[[t.model,a.model],[t.available,a.model_available===true?t.yes:a.model_available===false?t.no:t.unknown],[t.calls,(a.successful??0)+' / '+(a.attempted??0)],[t.tokens,a.tokens?.total],[t.last,a.last_success?new Date(a.last_success).toLocaleString(lang):'—']]);for(const err of a.errors||[])d.append(el('p',err,'muted'));s.append(d)}
const extra={fi:{division:'Divisioonat',conference:'Konferenssit',league:'Koko liiga',wild:'Wild Card',wins:'V',losses:'T',ot:'JA',unavailable:'Tietolähde ei ole tällä hetkellä käytettävissä.',key:'Palkkakattodatan käyttöoikeutta ei ole vielä määritetty.',original:'Alkuperäinen lähdekieli',rumours:'Siirtohuhut eivät vielä sisälly automaattiseen hakuun.',return:'Paluuarvio',date:'Päivä'},de:{division:'Divisionen',conference:'Konferenzen',league:'Gesamtliga',wild:'Wild Card',wins:'S',losses:'N',ot:'OT',unavailable:'Datenquelle derzeit nicht verfügbar.',key:'Der Zugriff auf Salary-Cap-Daten ist noch nicht eingerichtet.',original:'Originalsprache der Quelle',rumours:'Transfergerüchte werden noch nicht automatisch erfasst.',return:'Rückkehr',date:'Datum'},en:{division:'Divisions',conference:'Conferences',league:'League',wild:'Wild Card',wins:'W',losses:'L',ot:'OT',unavailable:'Data source currently unavailable.',key:'Salary cap data access is not configured yet.',original:'Original source language',rumours:'Trade rumours are not collected automatically yet.',return:'Expected return',date:'Date'}}[lang];
let standingsMode='division';
const rank=(x,k)=>Number(x[k])||999;
const teamCode=x=>x.teamAbbrev?.default||'';
function standingsView(s,rows){
  const controls=el('div',undefined,'modules');controls.style.marginTop='0';controls.style.marginBottom='16px';
  for(const id of ['division','conference','wild','league']){const b=el('button',extra[id]);b.setAttribute('aria-pressed',String(standingsMode===id));if(standingsMode===id){b.style.background='var(--active)';b.style.color='var(--activeText)'}b.onclick=()=>{standingsMode=id;render()};controls.append(b)}s.append(controls);
  const headers=[t.team,t.played,extra.wins,extra.losses,extra.ot,t.points,t.l10];
  function group(title,list,key){if(title){const h=el('h3',title);h.style.marginTop='18px';s.append(h)}const sorted=[...list].sort((a,b)=>rank(a,key)-rank(b,key)||b.points-a.points);table(s,headers,sorted.map(x=>[teamCode(x),x.gamesPlayed,x.wins,x.losses,x.otLosses,x.points,[x.l10Wins,x.l10Losses,x.l10OtLosses].map(v=>v??'—').join('–')]));const tbl=s.querySelectorAll('table');const last=tbl[tbl.length-1];if(list.length&&last){[...last.querySelectorAll('tbody tr')].forEach((tr,i)=>{tr.firstChild.replaceChildren(teamLabel(teamCode(sorted[i]),sorted[i].teamLogo,true))})}}
  const divisions=['Atlantic','Metropolitan','Central','Pacific'];const conferences=['Eastern','Western'];const div=x=>x.divisionName;const conf=x=>x.conferenceName;
  if(standingsMode==='division'){for(const c of conferences){const h=el('h2',c+' Conference');h.style.marginTop='24px';s.append(h);for(const d of divisions.slice(c==='Eastern'?0:2,c==='Eastern'?2:4))group(d+' Division',rows.filter(x=>div(x)===d),'divisionSequence')}}
  else if(standingsMode==='conference'){for(const c of conferences)group(c+' Conference',rows.filter(x=>conf(x)===c),'conferenceSequence')}
  else if(standingsMode==='wild'){for(const c of conferences){const h=el('h2',c+' Conference');h.style.marginTop='24px';s.append(h);const teams=rows.filter(x=>conf(x)===c);for(const d of divisions.slice(c==='Eastern'?0:2,c==='Eastern'?2:4))group(d+' Division',[...teams.filter(x=>div(x)===d)].sort((a,b)=>rank(a,'divisionSequence')-rank(b,'divisionSequence')).slice(0,3),'divisionSequence');group('Wild Card',teams.filter(x=>rank(x,'divisionSequence')>3),'wildcardSequence')}}
  else group('',rows,'leagueSequence');
  if(rows.length&&!rows.some(x=>div(x))&&standingsMode!=='league')group(extra.league,rows,'leagueSequence')
}
const normTeam=s=>String(s??'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/[^a-z0-9]+/g,' ').trim();
const aliases={ANA:['Anaheim Ducks','Ducks'],BOS:['Boston Bruins','Bruins'],BUF:['Buffalo Sabres','Sabres'],CAR:['Carolina Hurricanes','Hurricanes'],CBJ:['Columbus Blue Jackets','Blue Jackets'],CGY:['Calgary Flames','Flames'],CHI:['Chicago Blackhawks','Blackhawks'],COL:['Colorado Avalanche','Avalanche'],DAL:['Dallas Stars'],DET:['Detroit Red Wings','Red Wings'],EDM:['Edmonton Oilers','Oilers'],FLA:['Florida Panthers'],LAK:['Los Angeles Kings','LA Kings','LA'],MIN:['Minnesota Wild'],MTL:['Montreal Canadiens','Canadiens','Habs'],NJD:['New Jersey Devils','Devils','NJ'],NSH:['Nashville Predators','Predators'],NYI:['New York Islanders','Islanders'],NYR:['New York Rangers','Rangers'],OTT:['Ottawa Senators','Senators'],PHI:['Philadelphia Flyers','Flyers'],PIT:['Pittsburgh Penguins','Penguins'],SEA:['Seattle Kraken','Kraken'],SJS:['San Jose Sharks','Sharks','SJ'],STL:['St Louis Blues','Blues'],TBL:['Tampa Bay Lightning','Lightning','TB'],TOR:['Toronto Maple Leafs','Maple Leafs'],UTA:['Utah Mammoth','Mammoth','Utah Hockey Club','UTH'],VAN:['Vancouver Canucks','Canucks'],VGK:['Vegas Golden Knights','Golden Knights','Vegas'],WPG:['Winnipeg Jets'],WSH:['Washington Capitals','Capitals','WSH','WAS']};
function logoTeams(tags=[],text=''){
  const result=new Map(), explicit=new Set(tags.map(normTeam).filter(Boolean)), body=' '+normTeam(text)+' ';
  for(const x of data?.standings||[]){
    const code=teamCode(x),name=x.teamName?.default,common=x.teamCommonName?.default,loc=x.placeName?.default;
    const all=[code,name,common,loc,...(aliases[code]||[])].map(normTeam).filter(Boolean);
    const phrases=[name,...(aliases[code]||[])].map(normTeam).filter(v=>v.length>3&&!['wild','stars','kings','panthers','jets','la','vegas'].includes(v));
    if(all.some(v=>explicit.has(v))||phrases.some(v=>body.includes(' '+v+' ')))result.set(code,x);
  }
  return [...result.values()]
}
function addLogos(node,teams){for(const x of teams){const u=x.teamLogo;if(typeof u!=='string'||!/^https:\/\/assets\.nhle\.com\//.test(u))continue;const img=el('img');img.src=u;img.alt=teamCode(x);img.width=24;img.height=24;img.loading='lazy';img.className='team-mark';img.onerror=()=>img.remove();node.prepend(img)}}
function externalView(s,id,coverage){
  const entry=coverage?.[id==='trades'?'transactions':id];const urls={news:'https://www.espn.com/nhl/',injuries:'https://www.espn.com/nhl/injuries',trades:'https://www.espn.com/nhl/transactions',cap:'https://puckpedia.com/'};
  if(!entry||entry.status!=='ok'){s.append(el('p',id==='cap'?extra.key:extra.unavailable,'muted'))}
  else {const items=entry.items||[];s.append(el('p',entry.source+' · '+extra.original,'muted'));if(!items.length)s.append(el('p',t.empty,'muted'));
    let lastTeam='';const rows=id==='injuries'?[...items].sort((a,b)=>String(a.team||'').localeCompare(String(b.team||''))):[...items].sort((a,b)=>String(b.date||'').localeCompare(String(a.date||'')));
    for(const x of rows){if(id==='injuries'&&x.team&&x.team!==lastTeam){const h=el('h3',x.team);addLogos(h,logoTeams([x.team,...(x.teams||[])]));h.style.marginTop='18px';s.append(h);lastTeam=x.team}const a=el('article',undefined,'brief-item');const heading=el('h3',x.title);if(id!=='injuries')addLogos(heading,logoTeams([x.team,...(x.teams||[])].filter(Boolean),[x.title,x.body].filter(Boolean).join(' ')));a.append(heading);const metadata=[id!=='injuries'?x.team:null,x.status,x.date?String(x.date).slice(0,10):null,x.return?extra.return+': '+x.return:null].filter(Boolean);if(metadata.length)a.append(el('p',metadata.join(' · '),'muted'));if(x.body)a.append(el('p',x.body));if(x.url&&/^https:\/\//.test(x.url)){const link=el('a',t.source);link.href=x.url;link.rel='noopener noreferrer';a.append(link)}s.append(a)}
  }
  if(id==='trades')s.append(el('p',extra.rumours,'muted'));
  const a=el('a',t.source+' · '+(id==='cap'?'PuckPedia':'ESPN'));a.href=urls[id];a.rel='noopener noreferrer';s.append(a)
}
const europeanLabels={fi:{players:'Pistepörssi',unavailable:'Tietolähde ei vielä käytettävissä.',date:'Päivä',gf:'TM',ga:'PM'},de:{players:'Skorerliste',unavailable:'Datenquelle noch nicht verfügbar.',date:'Datum',gf:'GT',ga:'GE'},en:{players:'Scoring leaders',unavailable:'Data source not yet available.',date:'Date',gf:'GF',ga:'GA'}}[lang];
const leagueOptions=[['nhl','NHL'],['nl','National League'],['liiga','Liiga']];
const settingsText={fi:{title:'Asetukset',language:'Kieli',automatic:'Automaattinen (laitteen kieli)',theme:'Teema',leagues:'Seurattavat sarjat',close:'Sulje',minimum:'Valitse vähintään yksi sarja.'},de:{title:'Einstellungen',language:'Sprache',automatic:'Automatisch (Gerätesprache)',theme:'Design',leagues:'Verfolgte Ligen',close:'Schliessen',minimum:'Mindestens eine Liga auswählen.'},en:{title:'Settings',language:'Language',automatic:'Automatic (device language)',theme:'Theme',leagues:'Followed leagues',close:'Close',minimum:'Select at least one league.'}}[lang];
let enabledLeagues=leagueOptions.map(x=>x[0]);
try{const saved=JSON.parse(localStorage.getItem('hockey-enabled-leagues'));if(Array.isArray(saved)){const valid=enabledLeagues.filter(id=>saved.includes(id));if(valid.length)enabledLeagues=valid}}catch{}
let league=enabledLeagues[0];try{const l=localStorage.getItem('hockey-league');if(enabledLeagues.includes(l))league=l}catch{}
function savePreference(key,value){try{localStorage.setItem(key,value)}catch{}}
function applyTheme(){document.documentElement.dataset.theme=theme}
function openSettings(){
 const dialog=$('settings-dialog'),body=$('settings-body');body.replaceChildren();
 $('settings-title').textContent=settingsText.title;$('settings-close').textContent=settingsText.close;
 const languageField=el('fieldset');languageField.append(el('legend',settingsText.language));
 const languageSelect=el('select');languageSelect.setAttribute('aria-label',settingsText.language);
 for(const [id,label] of [['auto',settingsText.automatic],['fi','Suomi'],['de','Deutsch'],['en','English']]){const o=el('option',label);o.value=id;languageSelect.append(o)}
 languageSelect.value=languagePreference;
 languageSelect.onchange=()=>{savePreference('hockey-language',languageSelect.value);try{sessionStorage.setItem('hockey-reopen-settings','1')}catch{}location.reload()};
 languageField.append(languageSelect);
 const field=el('fieldset');field.append(el('legend',settingsText.theme));
 for(const [id,label] of [['light',t.light],['dark',t.dark]]){const l=el('label'),r=el('input');r.type='radio';r.name='theme-choice';r.value=id;r.checked=theme===id;r.onchange=()=>{theme=id;savePreference('hockey-theme',theme);applyTheme()};l.append(r,document.createTextNode(label));field.append(l)}
 const group=el('fieldset');group.append(el('legend',settingsText.leagues));const boxes=[];
 function sync(){for(const b of boxes){b.checked=enabledLeagues.includes(b.value);b.disabled=b.checked&&enabledLeagues.length===1}}
 for(const [id,name] of leagueOptions){const l=el('label'),b=el('input');b.type='checkbox';b.value=id;boxes.push(b);b.onchange=()=>{const next=leagueOptions.map(x=>x[0]).filter(k=>k===id?b.checked:enabledLeagues.includes(k));if(!next.length){sync();return}enabledLeagues=next;savePreference('hockey-enabled-leagues',JSON.stringify(next));sync();if(!next.includes(league)){league=next[0];savePreference('hockey-league',league);go('overview')}else render()};l.append(b,document.createTextNode(name));group.append(l)}
 group.append(el('p',settingsText.minimum,'muted'));body.append(languageField,field,group);sync();dialog.showModal()
}
$('settings').title=$('settings').ariaLabel=settingsText.title;
$('settings').onclick=openSettings;
$('settings-close').onclick=()=>$('settings-dialog').close();
$('settings-dialog').addEventListener('close',()=>$('settings').focus());
applyTheme();
function leagueTabs(){return league==='nhl'?tabs:['overview','games','standings','players','form','news','trades','injuries','info']}
function tabName(id){return t[id]||europeanLabels[id]||id}
function leagueNav(){const n=$('leagues');n.replaceChildren();n.hidden=enabledLeagues.length===1;if(n.hidden)return;for(const [id,name] of leagueOptions.filter(x=>enabledLeagues.includes(x[0]))){const b=el('button',name);b.type='button';b.setAttribute('aria-current',String(id===league));b.onclick=()=>{league=id;savePreference('hockey-league',id);go('overview')};n.append(b)}}
function europeanReportView(s,id,d){
 const copy={fi:{injuries:'Päivätyt loukkaantumis- ja paluu-uutiset. Tämä ei ole ajantasainen poissaololista.',transfers:'Siirto- ja sopimusuutiset. Huhut ja neuvottelut eivät ole vahvistettuja siirtoja.',news:'Uutisotsikot alkuperäisellä kielellä. Avaa koko uutinen lähteestä.',empty:'Ei uusia raportteja viimeisen 30 päivän ajalta tässä lähteessä.',failed:'Raporttien haku epäonnistui. Avaa lähde tarkistaaksesi uusimmat tiedot.',report:'Siirto- tai sopimusraportti',rumour:'Huhu / neuvottelu',updated:'Tarkistettu',original:'Lähteen kieli'},de:{injuries:'Datierte Verletzungs- und Rückkehrmeldungen. Keine aktuelle Abwesenheitsliste.',transfers:'Transfer- und Vertragsmeldungen. Gerüchte und Verhandlungen sind keine bestätigten Transfers.',news:'Schlagzeilen in der Originalsprache. Vollständigen Artikel bei der Quelle öffnen.',empty:'Keine neuen Meldungen der letzten 30 Tage aus dieser Quelle.',failed:'Meldungen konnten nicht geladen werden. Aktuelle Informationen bei der Quelle prüfen.',report:'Transfer- oder Vertragsmeldung',rumour:'Gerücht / Verhandlung',updated:'Geprüft',original:'Quellsprache'},en:{injuries:'Dated injury and return reports. This is not a current absence list.',transfers:'Transfer and contract reports. Rumours and negotiations are not confirmed transfers.',news:'Headlines in their original language. Open the source for the full article.',empty:'No new reports from this source in the last 30 days.',failed:'Unable to fetch reports. Check the source for the latest information.',report:'Transfer or contract report',rumour:'Rumour / negotiation',updated:'Checked',original:'Source language'}}[lang];
 const key=id==='trades'?'transactions':id,entry=d?.coverage?.[key];
 s.append(el('p',id==='injuries'?copy.injuries:id==='trades'?copy.transfers:copy.news,'muted'));
 if(!entry||entry.status!=='ok')s.append(el('p',copy.failed,'muted'));
 else {
 if(entry.updated)s.append(el('p',copy.updated+': '+new Date(entry.updated).toLocaleString(lang),'muted'));
 if(!entry.items?.length)s.append(el('p',copy.empty,'muted'));
 for(const x of entry.items||[]){
 if(typeof x.url!=='string'||!/^https:\/\//.test(x.url))continue;
 const article=el('article',undefined,'brief-item'),heading=el('h3'),link=el('a',x.title);link.href=x.url;link.rel='noopener noreferrer';heading.append(link);article.append(heading);
 const date=x.date?.length===10?x.date:new Date(x.date).toLocaleString(lang);
 article.append(el('p',[date,x.source,copy.original+': '+({fi:'Suomi',en:'English',de:'Deutsch'}[x.language]||x.language)].filter(Boolean).join(' · '),'muted'));
 if(id==='trades')article.append(el('p',x.report_status==='rumour'?copy.rumour:copy.report,'muted'));
 s.append(article)
 }
 }
 const url=entry?.url||(league==='nl'?'https://swisshockeynews.ch/en/national-league':'https://www.jatkoaika.com/LIIGA');
 if(/^https:\/\//.test(url)){const a=el('a',t.source+' · '+(entry?.source||(league==='nl'?'swisshockeynews.ch':'Jatkoaika')));a.href=url;a.rel='noopener noreferrer';s.append(a)}
}
function euTeam(d,id){return (d.standings||[]).find(t=>String(t.team_id)===String(id))}
function euTeamLabel(d,id,name,clickable=false){
 const team=euTeam(d,id),code=team?.team_code||name||team?.team_name||'—',mark=teamLabel(code,team?.team_logo);
 if(!clickable){mark.title=team?.team_name||name||code;return mark}
 const b=detailButton('',(team?.team_name||name||code)+' · '+detailText.rosterHint,()=>openRoster(code,d.details?.rosters,String(id),d.details));b.append(mark);b.title=team?.team_name||name||code;return b;
}
function euGameLike(g,d){return {id:g.game_id,startTimeUTC:g.date,gameState:g.status==='scheduled'?'FUT':g.status==='finished'?'OFF':'LIVE',awayTeam:{abbrev:euTeam(d,g.away_team_id)?.team_code||g.away_code||g.away_team_name,score:g.score_away},homeTeam:{abbrev:euTeam(d,g.home_team_id)?.team_code||g.home_code||g.home_team_name,score:g.score_home}}}
function euGamesView(s,d){
 const statuses={fi:{finished:'Päättynyt',scheduled:'Tulossa',live:'Käynnissä',in_progress:'Käynnissä',postponed:'Siirretty',cancelled:'Peruttu'},de:{finished:'Beendet',scheduled:'Geplant',live:'Live',in_progress:'Live',postponed:'Verschoben',cancelled:'Abgesagt'},en:{finished:'Final',scheduled:'Scheduled',live:'Live',in_progress:'Live',postponed:'Postponed',cancelled:'Cancelled'}}[lang];
 const rows=[...(d.games||[])].sort((a,b)=>b.date.localeCompare(a.date));
 table(s,[extra.date,t.away,t.score,t.home],rows.map(g=>['','',g.score_away==null||g.score_home==null?'—':g.score_away+' : '+g.score_home,'']));
 const tbl=s.querySelector('table');if(!tbl)return;tbl.classList.add('nl-games');
 [...tbl.querySelectorAll('tbody tr')].forEach((tr,i)=>{const g=rows[i],date=new Date(g.date),tz=league==='nl'?'Europe/Zurich':'Europe/Helsinki';tr.children[0].append(el('span',date.toLocaleDateString(lang,{timeZone:tz,month:'2-digit',day:'2-digit'})),el('small',date.toLocaleTimeString(lang,{timeZone:tz,hour:'2-digit',minute:'2-digit',hour12:false})),el('small',statuses[g.status]||t.unknown));tr.children[1].append(euTeamLabel(d,g.away_team_id,g.away_team_name));tr.children[3].append(euTeamLabel(d,g.home_team_id,g.home_team_name));const score=tr.children[2].textContent;tr.children[2].replaceChildren(detailButton(score,g.away_team_name+' @ '+g.home_team_name+' · '+detailText.gameHint,()=>openGame(euGameLike(g,d),d.details)))})
}
function euFormView(s,d){
 const rows=[...(d.form||[])].filter(r=>r.games).sort((a,b)=>(2*b.wins+b.ot_losses)-(2*a.wins+a.ot_losses));
 table(s,[t.team,t.played,t.l10],rows.map(x=>['',x.games,[x.wins,x.losses,x.ot_losses].join('–')+(x.unknown_losses?' (+'+x.unknown_losses+' ?)':'')]));
 s.querySelectorAll('tbody tr').forEach((tr,i)=>{const x=rows[i],code=euTeam(d,x.team_id)?.team_code||x.team_name;tr.children[0].append(euTeamLabel(d,x.team_id,x.team_name));const value=tr.children[2].textContent;tr.children[2].replaceChildren(detailButton(value,x.team_name+' · '+detailText.historyHint,()=>openHistory(code,d.details,String(x.team_id))))});
}
function euView(s){
 const d=data?.leagues?.[league];const e=europeanLabels;
 if(!d){s.append(el('p',data?e.unavailable:failed?t.error:t.loading,'muted'));return}
 if(['news','trades','injuries'].includes(active)){europeanReportView(s,active,d);return}
 const standings=d.standings||[],stats=d.players||[];
 if(active==='overview'){brief(s,d.brief?.[lang]);modules(s)}
 else if(active==='standings'){
 table(s,['#',t.team,t.played,t.points,e.gf,e.ga],standings.map(x=>[x.rank,x.team_name,x.games_played,x.points,x.goals_for,x.goals_against]));
 const rows=s.querySelectorAll('tbody tr');rows.forEach((tr,i)=>tr.children[1].replaceChildren(euTeamLabel(d,standings[i].team_id,standings[i].team_name,true)))
 }
 else if(active==='form'){euFormView(s,d)}
 else if(active==='games'){euGamesView(s,d)}
 else if(active==='players'){
 if(league==='nl'||league==='liiga'){
 const players=stats.slice(0,100);
 table(s,[t.name,t.played,t.goals,t.assists,t.points],players.map(x=>['',x.games_played,x.goals,x.assists,x.points]));
 const tbl=s.querySelector('table');if(tbl){tbl.classList.add('nl-players');
 [...tbl.querySelectorAll('tbody tr')].forEach((tr,i)=>{const x=players[i];tr.children[0].append(el('span',x.player_name),el('small',x.team_name))});}
 }else table(s,[t.name,t.team,t.played,t.goals,t.assists,t.points],stats.slice(0,100).map(x=>[x.player_name,x.team_name,x.games_played,x.goals,x.assists,x.points]));
 }
 else {s.append(el('p',e.unavailable,'muted'));const a=el('a',t.source);a.href=league==='nl'?'https://swisshockeynews.ch/en/':'https://liiga.fi/';a.rel='noopener noreferrer';s.append(a)}
 if(d.errors?.length)s.append(el('p',t.partial,'muted'));
 if(d.source_url){const a=el('a',t.source+' · '+d.source);a.href=d.source_url;a.rel='noopener noreferrer';s.append(a)}
}

function capView(s,c){
 const labels={fi:{limit:'Palkkakatto',roster:'Kokoonpanon rasite',space:'Arvio vapaasta tilasta',dead:'Dead cap',coverage:'Kattavuus',warning:'Arvio ei sisällä kaikkia LTIR-helpotuksia, bonuksia tai muita oikaisuja. Puuttuvia lukuja ei lasketa nolliksi.',players:'Pelaajasopimukset',ltir:'LTIR-rasite'},de:{limit:'Obergrenze',roster:'Kader-Cap-Hit',space:'Geschätzter Spielraum',dead:'Dead Cap',coverage:'Abdeckung',warning:'Schätzung ohne vollständige LTIR-Entlastung, Boni und weitere Anpassungen. Fehlende Werte sind keine Nullwerte.',players:'Spielerverträge',ltir:'LTIR-Cap-Hit'},en:{limit:'Cap ceiling',roster:'Roster cap hit',space:'Estimated space',dead:'Dead cap',coverage:'Coverage',warning:'Estimate excludes full LTIR relief, bonuses and other adjustments. Missing values are not zero.',players:'Player contracts',ltir:'LTIR cap hit'}}[lang];
 const money=v=>typeof v==='number'?new Intl.NumberFormat(lang,{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:2}).format(v):'—';
 if(c?.status!=='ok'){s.append(el('p',data?extra.unavailable:t.loading,'muted'));return}
 s.append(el('p',labels.limit+': '+money(c.limits?.ceiling)),el('p',labels.warning,'muted'),el('p',c.source+(c.updated?' · '+c.updated.slice(0,10):''),'muted'));
 const byTeam=new Map((c.items||[]).map(x=>[x.team,x]));
 const rows=(data.standings||[]).map(x=>({code:teamCode(x),...byTeam.get(teamCode(x))})).sort((a,b)=>(b.capSpaceEstimate??-Infinity)-(a.capSpaceEstimate??-Infinity));
 table(s,[t.team,labels.roster,labels.dead,labels.ltir,labels.space,labels.coverage],rows.map(x=>[x.code,money(x.rosterCapHit),money(x.deadCapTotal),money(x.ltir?.capHitTotal),money(x.capSpaceEstimate),x.rosterCount!=null?(x.rosterWithFigure??'—')+'/'+x.rosterCount:'—']));
 [...s.querySelectorAll('tbody tr')].forEach((tr,i)=>addLogos(tr.firstChild,logoTeams([rows[i].code])));
 for(const x of rows){const players=(c.players||[]).filter(p=>p.currentTeam===x.code);if(!players.length)continue;const d=el('details'),h=el('summary',x.code+' · '+labels.players);addLogos(h,logoTeams([x.code]));d.append(h);table(d,[t.name,labels.roster,'UFA / RFA','Years'],players.map(p=>[p.player?.name,money(p.capHit),p.expiryType,p.yearsLeft]));s.append(d)}
 const a=el('a',t.source+' · nhl-contracts');a.href='https://github.com/ehlersio/nhl-contracts';s.append(a)
}

const detailText={
fi:{game:'Ottelutilastot',roster:'Roster',seasonRoster:'Kauden pelaajaluettelo',history:'Viimeiset 10 runkosarjaottelua',close:'Sulje',position:'Pelipaikka',country:'Maa',shots:'Lauk.',attempts:'Laukausyritykset',toi:'Peliaika',goalies:'Maalivahdit',saves:'Torjunnat',savePct:'Torjunta-%',against:'PM',result:'Tulos',unavailable:'Näitä tietoja ei saatu viimeisimmässä päivityksessä.',pregame:'Ottelutilastot tulevat saataville ottelun alettua.',note:'NHL:n tiedot viimeisimmän päivityksen hetkellä.',rosterHint:'Avaa joukkueen rosteri',gameHint:'Avaa ottelutilastot',historyHint:'Näytä viimeiset 10 ottelua'},
de:{game:'Spielstatistik',roster:'Kader',seasonRoster:'Spieler der Saison',history:'Letzte 10 Spiele der regulären Saison',close:'Schliessen',position:'Position',country:'Land',shots:'Schüsse',attempts:'Schussversuche',toi:'Eiszeit',goalies:'Torhüter',saves:'Paraden',savePct:'Fangquote',against:'GT',result:'Resultat',unavailable:'Diese Daten konnten beim letzten Update nicht abgerufen werden.',pregame:'Spielstatistiken sind nach Spielbeginn verfügbar.',note:'NHL-Daten zum Zeitpunkt der letzten Aktualisierung.',rosterHint:'Teamkader öffnen',gameHint:'Spielstatistik öffnen',historyHint:'Letzte 10 Spiele anzeigen'},
en:{game:'Game statistics',roster:'Roster',seasonRoster:'Season player register',history:'Last 10 regular-season games',close:'Close',position:'Position',country:'Country',shots:'Shots',attempts:'Shot attempts',toi:'TOI',goalies:'Goalies',saves:'Saves',savePct:'Save %',against:'GA',result:'Result',unavailable:'These details were unavailable at the last update.',pregame:'Game statistics become available after the game starts.',note:'NHL data as of the last update.',rosterHint:'Open team roster',gameHint:'Open game statistics',historyHint:'Show last 10 games'}
}[lang];
function detailButton(text,label,action){const b=el('button',text,'text-link');b.type='button';b.setAttribute('aria-label',label);b.onclick=action;return b}
function teamLabel(code,logo,roster=false){
 const node=roster?detailButton('',code+' · '+detailText.rosterHint,()=>openRoster(code)):el('span');node.classList.add('team-label');
 const url=logo||(data?.standings||[]).find(x=>teamCode(x)===code)?.teamLogo;
 if(typeof url==='string'&&/^https:\/\//.test(url)){const img=el('img');img.src=url;img.alt='';img.loading='lazy';img.onerror=()=>img.remove();node.append(img)}
 node.append(el('span',code||'—'));return node;
}
function openDetail(title,fill,source='NHL',updated=data?.details?.updated){const dialog=$('detail-dialog'),body=$('detail-content');$('detail-title').textContent=title;$('detail-close').textContent=detailText.close;body.replaceChildren();body.append(el('p',detailText.note.replace('NHL',source)+' '+(updated?new Date(updated).toLocaleString(lang):''),'muted detail-note'));fill(body);if(!dialog.open)dialog.showModal()}
$('detail-close').onclick=()=>$('detail-dialog').close();
function openRoster(code,rosters=data?.rosters,teamKey=code,store=data?.details){openDetail(code+' · '+detailText.roster,s=>{
 const r=rosters?.[teamKey];if(r?.status!=='ok'){s.append(el('p',detailText.unavailable));return}
 if(store?.rosterBasis==='season')s.append(el('p',detailText.seasonRoster,'muted'));
 table(s,['#',t.name,detailText.position,detailText.country],(r.players||[]).map(p=>[p.number,p.name,p.position,p.country]));s.querySelector('table')?.classList.add('roster-table');
},store?.source||'NHL',store?.updated)}
function openHistory(code,store=data?.details,teamKey=code){openDetail(code+' · '+detailText.history,s=>{
 const h=store?.history?.[teamKey];if(h?.status!=='ok'){s.append(el('p',detailText.unavailable));return}
 const result={W:extra.wins,L:extra.losses,OT:extra.ot};
 table(s,[extra.date,t.games,t.score,detailText.result],(h.games||[]).map(g=>[new Date(g.date).toLocaleDateString(lang),g.away+' @ '+g.home,g.away_score+' : '+g.home_score+(['OT','SO'].includes(g.outcome)?' ('+g.outcome+')':''),result[g.result]||'—']));s.querySelector('table')?.classList.add('last-ten');
},store?.source||'NHL',store?.updated)}
function openGame(g,store=data?.details){openDetail(g.awayTeam.abbrev+' @ '+g.homeTeam.abbrev+' · '+detailText.game,s=>{
 const record=store?.games?.[String(g.id)];
 if(record?.status!=='ok'){s.append(el('p',['FUT','PRE'].includes(g.gameState)?detailText.pregame:detailText.unavailable));return}
 const b=record.data,a=b.awayTeam,h=b.homeTeam;
 s.append(el('h3',a.abbrev+' '+(a.score??'—')+' : '+(h.score??'—')+' '+h.abbrev));
 s.append(el('p',new Date(b.startTimeUTC).toLocaleString(lang)+(['OT','SO'].includes(b.gameOutcome?.lastPeriodType)?' · '+b.gameOutcome.lastPeriodType:''),'muted'));
 table(s,['',a.abbrev,h.abbrev],[[detailText.shots,a.sog,h.sog]]);
 for(const [side,team] of [['awayTeam',a],['homeTeam',h]]){
  s.append(el('h3',team.abbrev));const p=b.playerByGameStats?.[side]||{};
  table(s,[t.name,t.goals,t.assists,t.points,b.playerShotsType==='attempts'?detailText.attempts:detailText.shots,detailText.toi],[...(p.forwards||[]),...(p.defense||p.defensemen||[])].map(x=>[x.name?.default||x.name,x.goals,x.assists,x.points,x.sog,x.toi]));
  s.append(el('h3',team.abbrev+' · '+detailText.goalies));
  table(s,[t.name,detailText.saves,detailText.against,detailText.savePct],(p.goalies||[]).map(x=>[x.name?.default||x.name,x.saves,x.goalsAgainst,Number.isFinite(x.savePctg)?(100*x.savePctg).toLocaleString(lang,{maximumFractionDigits:1})+' %':'—']));
 }
},store?.source||'NHL',store?.updated)}
function gamesView(s,games){
 table(s,[t.away,t.score,t.home,t.status],games.map(g=>[g.awayTeam?.abbrev,(g.awayTeam?.score??'—')+' : '+(g.homeTeam?.score??'—'),g.homeTeam?.abbrev,['OFF','FINAL'].includes(g.gameState)?'Final':g.gameState]));
 s.querySelectorAll('tbody tr').forEach((tr,i)=>{const g=games[i];tr.children[0].replaceChildren(teamLabel(g.awayTeam.abbrev,g.awayTeam.logo));tr.children[2].replaceChildren(teamLabel(g.homeTeam.abbrev,g.homeTeam.logo));const score=tr.children[1].textContent;tr.children[1].replaceChildren(detailButton(score,g.awayTeam.abbrev+' @ '+g.homeTeam.abbrev+' · '+detailText.gameHint,()=>openGame(g)))})
}
function formView(s){
 const rows=[...(data.standings||[])].sort((a,b)=>(2*b.l10Wins+b.l10OtLosses)-(2*a.l10Wins+a.l10OtLosses));
 table(s,[t.team,t.l10],rows.map(x=>[teamCode(x),[x.l10Wins,x.l10Losses,x.l10OtLosses].map(v=>v??'—').join('–')]));
 s.querySelectorAll('tbody tr').forEach((tr,i)=>{const code=teamCode(rows[i]);tr.children[0].replaceChildren(teamLabel(code,rows[i].teamLogo));const value=tr.children[1].textContent;tr.children[1].replaceChildren(detailButton(value,code+' · '+detailText.historyHint,()=>openHistory(code)))})
}
const todayText={
fi:{day:'NHL-ottelupäivä',zone:'Ottelupäivä: New York. Alkamisaika laitteen paikallisajassa.',snapshot:'Tilanteet ja kertoimet ovat päivityshetken tietoja, eivät reaaliaikainen syöte.',market:'Ottelun voittaja, jatkoaika ja voittolaukaukset mukana',none:'Ei kertoimia saatavilla.',closed:'Ennakkokertoimet eivät ole enää saatavilla.',empty:'Ei otteluita tänä NHL-ottelupäivänä.',stale:'Tämän NHL-ottelupäivän tietoja ei ole vielä päivitetty.',checked:'Haettu',scheduled:'Ei alkanut',live:'Käynnissä päivityshetkellä',final:'Päättynyt',postponed:'Siirretty',cancelled:'Peruttu',oddsError:'Kertoimien haku epäonnistui.'},
de:{day:'NHL-Spieltag',zone:'Spieltag: New York. Startzeit in der lokalen Gerätezeit.',snapshot:'Spielstände und Quoten entsprechen dem letzten Abruf und werden nicht in Echtzeit aktualisiert.',market:'Spielsieger inklusive Verlängerung und Penaltyschiessen',none:'Keine Quoten verfügbar.',closed:'Keine Vorabquoten mehr verfügbar.',empty:'Keine Spiele an diesem NHL-Spieltag.',stale:'Daten für diesen NHL-Spieltag noch nicht aktualisiert.',checked:'Abgerufen',scheduled:'Noch nicht begonnen',live:'Beim Abruf im Gange',final:'Beendet',postponed:'Verschoben',cancelled:'Abgesagt',oddsError:'Quoten konnten nicht geladen werden.'},
en:{day:'NHL matchday',zone:'Matchday: New York. Start times use your device’s local time.',snapshot:'Scores and odds are snapshots from the last update, not a live feed.',market:'Match winner including overtime and shootouts',none:'No odds available.',closed:'Pregame odds are no longer available.',empty:'No games on this NHL matchday.',stale:'Data for this NHL matchday has not been updated yet.',checked:'Retrieved',scheduled:'Not started',live:'In progress at last update',final:'Final',postponed:'Postponed',cancelled:'Cancelled',oddsError:'Unable to retrieve odds.'}
}[lang];
function nhlMatchday(now=new Date()){return new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit'}).format(now)}
function todayView(s){
 const tx=todayText,block=data?.today,date=nhlMatchday(),day=block?.days?.find(d=>d.date===date);
 s.append(el('h3',tx.day+' · '+date),el('p',tx.zone,'muted'),el('p',tx.snapshot,'muted'));
 if(block?.updated)s.append(el('p',tx.checked+': '+new Date(block.updated).toLocaleString(lang),'muted'));
 if(!day){s.append(el('p',data?tx.stale:failed?t.error:t.loading,'muted'));return}
 if(day.status!=='ok'){s.append(el('p',extra.unavailable,'muted'));return}
 if(day.odds_status!=='ok')s.append(el('p',tx.oddsError,'muted'));
 const games=[...(day.games||[])].sort((a,b)=>new Date(a.startTimeUTC)-new Date(b.startTimeUTC));
 if(!games.length)s.append(el('p',tx.empty));
 for(const g of games){
  const a=el('article',undefined,'game-card'),state=g.gameState,start=new Date(g.startTimeUTC),q=g.pregame_odds;
  const title=el('h3');title.append(teamLabel(g.awayTeam?.abbrev,g.awayTeam?.logo),document.createTextNode(' @ '),teamLabel(g.homeTeam?.abbrev,g.homeTeam?.logo));a.append(title);
  const status=['OFF','FINAL'].includes(state)?tx.final:['LIVE','CRIT'].includes(state)?tx.live:state==='PPD'?tx.postponed:state==='CNCL'?tx.cancelled:['FUT','PRE'].includes(state)?tx.scheduled:state;
  a.append(el('p',start.toLocaleString(lang,{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})+' · '+status));
  if(!['FUT','PRE','PPD','CNCL'].includes(state)){const score=el('p',undefined,'game-score');score.append(detailButton((g.awayTeam?.score??'—')+' : '+(g.homeTeam?.score??'—'),g.awayTeam.abbrev+' @ '+g.homeTeam.abbrev+' · '+detailText.gameHint,()=>openGame(g)));a.append(score)}
  const pre=['FUT','PRE'].includes(state)&&start.getTime()>Date.now();
  if(pre&&q?.market==='winner_including_ot_so'&&Number.isFinite(q.away)&&q.away>1&&Number.isFinite(q.home)&&q.home>1){
   a.append(el('p',tx.market,'muted'));
   table(a,[t.away+' · '+g.awayTeam.abbrev,t.home+' · '+g.homeTeam.abbrev],[[q.away.toLocaleString(lang,{minimumFractionDigits:2,maximumFractionDigits:2}),q.home.toLocaleString(lang,{minimumFractionDigits:2,maximumFractionDigits:2})]]);
   a.append(el('p',q.provider+' · '+q.source+' · '+tx.checked+': '+new Date(q.checked_at).toLocaleString(lang),'muted'));
  }else a.append(el('p',pre?tx.none:tx.closed,'muted'));
  s.append(a);
 }
 const source=el('a',t.source+' · ESPN');source.href='https://www.espn.com/nhl/odds';source.rel='noopener noreferrer';source.target='_blank';s.append(source);
}
function render(){nav();$('main').replaceChildren();const s=section(active==='overview'?t.brief:tabName(active));if(active==='info'){info(s);return}if(league!=='nhl'){euView(s);return}if(active==='today'){todayView(s);return}if(active==='cap'){capView(s,data?.coverage?.cap);return}if(['news','injuries','trades','cap'].includes(active)){externalView(s,active,data?.coverage);return}if(!data){s.append(el('p',failed?t.error:t.loading,'muted'));if(active==='overview')modules(s);return}const d=data;if(active==='overview'){brief(s,d.brief?.[lang]);if(d.errors?.length)s.append(el('p',t.partial,'muted'));modules(s)}else if(active==='games'){gamesView(s,d.games||[])}else if(active==='finns'){table(s,[t.name,t.team,t.goals,t.assists,t.saves],(d.finns||[]).map(p=>[p.name?.default??p.name,p.team,p.goals,p.assists,p.saves]))}else if(active==='standings'){standingsView(s,d.standings||[])}else if(active==='form'){formView(s)}}
async function load(){const request=++serial;failed=false;if(!data)render();try{const r=await fetch('data.json',{cache:'no-store'});if(!r.ok)throw Error('fetch');const next=await r.json();if(request!==serial)return;data=next;$('stamp').textContent=t.updated+': '+new Date(data.updated).toLocaleString(lang)}catch{if(request!==serial)return;failed=true;$('stamp').textContent=t.error}render()}
$('refresh').onclick=load;$('info').onclick=()=>go('info');window.addEventListener('hashchange',()=>go(location.hash.slice(1)));active=leagueTabs().includes(location.hash.slice(1))?location.hash.slice(1):'overview';render();load();try{if(sessionStorage.getItem('hockey-reopen-settings')==='1'){sessionStorage.removeItem('hockey-reopen-settings');openSettings()}}catch{}
