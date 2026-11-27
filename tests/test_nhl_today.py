import unittest,datetime,copy
from nhl_today import decimal_odds,parse_odds,collect_today
NOW=datetime.datetime(2026,11,27,19,tzinfo=datetime.timezone.utc)
START='2026-11-28T00:30Z'
def event():
 return {'date':START,'status':{'type':{'state':'pre'}},'competitions':[{'competitors':[{'homeAway':'home','team':{'abbreviation':'NJ'}},{'homeAway':'away','team':{'abbreviation':'LA'}}],'odds':[{'provider':{'name':'DraftKings'},'moneyline':{'home':{'close':{'odds':'-125'}},'away':{'close':{'odds':'+110'}}}}]}]}
def game():return {'startTimeUTC':START,'gameState':'FUT','awayTeam':{'abbrev':'LAK'},'homeTeam':{'abbrev':'NJD'}}
class TodayTests(unittest.TestCase):
 def test_conversion(self):
  self.assertEqual(decimal_odds(-125),1.8);self.assertEqual(decimal_odds('+110'),2.1)
  for v in (None,True,0,99,'NaN','inf','EVEN','oops'):self.assertIsNone(decimal_odds(v))
 def test_only_complete_pregame_two_way_current_quotes(self):
  e=event();self.assertEqual(len(parse_odds({'events':[e]},NOW)),1)
  for change in ('live','started','missing_side','opening_only','other_provider'):
   e=event();c=e['competitions'][0];q=c['odds'][0]
   if change=='live':e['status']['type']['state']='in'
   elif change=='started':e['date']='2026-11-27T18:00Z'
   elif change=='missing_side':del q['moneyline']['home']
   elif change=='opening_only':q['moneyline']['home']={'open':{'odds':'-125'}}
   else:q['provider']['name']='Unknown'
   self.assertEqual(parse_odds({'events':[e]},NOW),{},change)
 def test_match_both_teams_and_start(self):
  for change in ('none','reversed','time','live'):
   g=game()
   if change=='reversed':g['awayTeam'],g['homeTeam']=g['homeTeam'],g['awayTeam']
   elif change=='time':g['startTimeUTC']='2026-11-28T01:00Z'
   elif change=='live':g['gameState']='LIVE'
   r=collect_today(NOW,lambda _: {'events':[event()]},lambda _: {'games':[copy.deepcopy(g)]})
   self.assertEqual('pregame_odds' in r['days'][0]['games'][0],change=='none')
 def test_failures_are_independent_and_empty_is_valid(self):
  def fail(_):raise TimeoutError()
  r=collect_today(NOW,fail,lambda _:{'games':[]})
  self.assertEqual(r['days'][0]['status'],'ok');self.assertEqual(r['days'][0]['odds_status'],'error')
  r=collect_today(NOW,lambda _:{'events':[]},fail)
  self.assertEqual(r['days'][0]['status'],'error');self.assertEqual(r['days'][0]['odds_status'],'ok')
 def test_eastern_midnight(self):
  now=datetime.datetime(2026,11,28,1,tzinfo=datetime.timezone.utc)
  r=collect_today(now,lambda _:{'events':[]},lambda _:{'games':[]})
  self.assertEqual([x['date'] for x in r['days']],['2026-11-27','2026-11-28'])
