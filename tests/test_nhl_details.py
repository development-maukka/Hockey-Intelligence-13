import copy,datetime,unittest
from nhl_details import last_ten,normalize_roster,collect_details,box_detail
NOW=datetime.datetime(2026,11,28,tzinfo=datetime.timezone.utc)
def game(i,home_score=3,away_score=1,period='REG',state='OFF'):
 return {'id':i,'startTimeUTC':f'2026-11-{i:02}T18:00:00Z','gameType':2,'gameState':state,'homeTeam':{'abbrev':'TOR','score':home_score},'awayTeam':{'abbrev':'BOS','score':away_score},'gameOutcome':{'lastPeriodType':period}}
class DetailTests(unittest.TestCase):
 def test_perspective_and_overtime(self):
  raw={'games':[game(1),game(2,1,2,'OT'),game(3,1,2,'SO'),game(4,1,2)]}
  self.assertEqual([g['result'] for g in last_ten(raw,'TOR',NOW)],['L','OT','OT','W'])
  self.assertEqual([g['result'] for g in last_ten(raw,'BOS',NOW)],['W','W','W','L'])
 def test_only_last_ten_completed_regular_season(self):
  rows=[game(i) for i in range(1,15)]+[game(15,state='LIVE'),game(16,state='FUT'),game(14)]
  rows[0]['gameType']=1;rows.append(game(29))
  r=last_ten({'games':rows},'TOR',NOW)
  self.assertEqual([x['id'] for x in r],list(range(14,4,-1)))
  self.assertEqual(last_ten({'games':rows},'SJS',NOW),[])
 def test_unknown_period_not_counted_as_regulation_loss(self):
  with self.assertRaises(ValueError):last_ten({'games':[game(1,1,2,None)]},'TOR',NOW)
 def test_roster_all_positions(self):
  raw={g:[{'id':i,'firstName':{'default':'Test'},'lastName':{'default':g},'positionCode':'G' if i==3 else 'C','sweaterNumber':i}] for i,g in enumerate(('forwards','defensemen','goalies'),1)}
  rows=normalize_roster(raw);self.assertEqual(len(rows),3);self.assertEqual(rows[-1]['position'],'G')
  with self.assertRaises(ValueError):normalize_roster({'forwards':[]})
 def test_box_identity(self):
  with self.assertRaises(ValueError):box_detail({'id':1,'playerByGameStats':{}},2)
 def test_failures_and_cached_box_are_independent(self):
  calls=[]
  def fetch(path):calls.append(path);raise TimeoutError()
  cached={1:{'id':1,'awayTeam':{'abbrev':'BOS'},'homeTeam':{'abbrev':'TOR'},'playerByGameStats':{'awayTeam':{},'homeTeam':{}}}}
  r=collect_details([game(1),game(1),game(2),game(3,state='FUT')],['TOR','BOS'],NOW,fetch,cached)
  self.assertEqual(r['games']['1']['status'],'ok');self.assertEqual(r['games']['2']['status'],'error')
  self.assertNotIn('3',r['games']);self.assertEqual(len(calls),4);self.assertTrue(all(v['status']=='error' for v in r['history'].values()))
