import unittest,datetime,tempfile,copy
from europe_details import clock,nl_box,liiga_box,collect_details,roster_row
from europe_data import normalize,form
NOW=datetime.datetime(2026,11,28,tzinfo=datetime.timezone.utc)
G={'game_id':20271105000001,'date':'2026-11-27T18:00:00+00:00','status':'finished','home_team_id':11,'away_team_id':22,'home_team_name':'Home','away_team_name':'Away','home_code':'H','away_code':'A','score_home':2,'score_away':1,'outcome':'OT'}
def nl_raw():
 return {'overview':{'gameId':str(G['game_id']),'homeTeamId':'11','awayTeamId':'22','homeTeamResult':2,'awayTeamResult':1},'teamStatsHome':{'sog':30},'teamStatsAway':{'sog':20},'playerStatsHome':[{'name':'Keeper','position':'goalkeeper','mip':6000,'svs':19,'ga':1,'sa':20,'savePercentage':95},{'name':'Skater','position':'defender','toi':1259,'g':1,'a':1,'pts':2,'sog':3}],'playerStatsAway':[]}
def liiga_raw():
 game={'game':{'id':G['game_id'],'season':2027,'homeTeam':{'teamId':'11:h','goals':2},'awayTeam':{'teamId':'22:a','goals':1}},'homeTeamPlayers':[{'id':1,'firstName':'Home','lastName':'Skater','role':'DEFENSEMAN'},{'id':2,'firstName':'Home','lastName':'Keeper','role':'GOALIE'}],'awayTeamPlayers':[{'id':3,'firstName':'Away','lastName':'Skater','role':'STRIKER'},{'id':4,'firstName':'Away','lastName':'Keeper','role':'GOALIE'}]}
 stats={}
 for side,tid,pid in [('home',11,1),('away',22,3)]:
  stats[side+'Team']=[{'teamId':str(tid)+':x','period':period,'periodPlayerStats':[{'playerId':pid,'period':{'goals':1,'assists':2,'points':3,'shots':5,'timeofice':300}}],'goaliePeriodStats':[{'playerId':pid+1,'period':{'saves':9,'shotsOnGoal':10,'goalsAllowed':1,'timeofice':1200}}]} for period in (1,2)]
 return game,stats
class EuropeDetailTests(unittest.TestCase):
 def test_clocks_distinguish_units(self):
  self.assertEqual(clock(1259,True),'12:59');self.assertEqual(clock(1259),'20:59');self.assertEqual(clock(6000,True),'60:00');self.assertIsNone(clock(1260,True));self.assertIsNone(clock(None))
 def test_nl_goalies_and_team_identity(self):
  b=nl_box(nl_raw(),G,2027);self.assertEqual(b['playerByGameStats']['homeTeam']['goalies'][0]['savePctg'],.95);self.assertEqual(b['playerByGameStats']['homeTeam']['defense'][0]['toi'],'12:59')
  with self.assertRaises(ValueError):nl_box(nl_raw(),dict(G,home_team_id=99),2027)
  with self.assertRaises(ValueError):nl_box(nl_raw(),G,2026)
 def test_liiga_periods_aggregate_once(self):
  raw,stats=liiga_raw();b=liiga_box(raw,stats,G,2027);p=b['playerByGameStats']['homeTeam']['defense'][0]
  self.assertEqual((p['goals'],p['assists'],p['points'],p['sog'],p['toi']),(2,4,6,10,'10:00'));self.assertEqual(b['homeTeam']['sog'],20);self.assertEqual(b['playerShotsType'],'attempts');self.assertEqual(b['playerByGameStats']['homeTeam']['goalies'][0]['savePctg'],.9)
  stats['homeTeam'].append(stats['homeTeam'][0])
  with self.assertRaises(ValueError):liiga_box(raw,stats,G,2027)
 def test_liiga_team_and_season_scope(self):
  raw,stats=liiga_raw()
  with self.assertRaises(ValueError):liiga_box(raw,stats,G,2026)
  stats['homeTeam'][0]['teamId']='99:wrong'
  with self.assertRaises(ValueError):liiga_box(raw,stats,G,2027)
 def test_goalie_roster_position(self):
  self.assertEqual(roster_row({'id':1,'role':'GOALIE','firstName':'A','lastName':'B'},True)['position'],'G')
 def test_status_and_overtime_normalization(self):
  row={'game_id':1,'date':'2026-11-28T18:00:00Z','home_team_id':1,'away_team_id':2,'home_team_name':'A','away_team_name':'B','base_status':'beforeStartOfPlay','home_team_result':0,'away_team_result':0,'is_overtime':False,'is_shootout':False}
  n=normalize('nl','games',[row])[0];self.assertEqual(n['status'],'scheduled');self.assertIsNone(n['score_home'])
  games=[dict(G,outcome=o,game_id=i) for i,o in enumerate(('REG','OT','SO'))]
  rec=form([{'team_id':22,'team_name':'Away'}],games)[0];self.assertEqual((rec['wins'],rec['losses'],rec['ot_losses']),(0,1,2))
 def test_cache_and_roster_failures_are_independent(self):
  entry={'season':2027,'source':'NL','standings':[{'team_id':11,'team_name':'Home'}],'games':[G]};calls=[]
  def fetch(url):
   calls.append(url)
   if '/player/team/' in url:raise TimeoutError()
   return nl_raw()
  with tempfile.TemporaryDirectory() as tmp:
   a=collect_details('nl',entry,[G],fetch,NOW,tmp);b=collect_details('nl',entry,[G],fetch,NOW,tmp)
   self.assertEqual(a['games'][str(G['game_id'])]['status'],'ok');self.assertEqual(b['rosters']['11']['status'],'error');self.assertEqual(sum('/games/' in u for u in calls),1)
   # A score correction invalidates the cached box.
   entry['games']=[dict(G,score_home=3)];collect_details('nl',entry,[G],fetch,NOW,tmp);self.assertEqual(sum('/games/' in u for u in calls),2)
 def test_liiga_removed_players_and_team_scope(self):
  entry={'season':2027,'source':'Liiga','standings':[{'team_id':11,'team_name':'Home'}],'games':[]}
  raw=[{'id':1,'teamId':'11:h','firstName':'Current','role':'GOALIE'},{'id':2,'teamId':'11:h','removed':True},{'id':3,'teamId':'22:a'}]
  with tempfile.TemporaryDirectory() as tmp:
   r=collect_details('liiga',entry,[],lambda _:raw,NOW,tmp);self.assertEqual([p['id'] for p in r['rosters']['11']['players']],[1]);self.assertEqual(r['history']['11']['status'],'error')
