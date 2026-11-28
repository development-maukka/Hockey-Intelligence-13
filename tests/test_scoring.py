import copy,unittest
from scoring import nhl_goals,nl_goals,liiga_goals,safe_goals
BOX={'id':123,'awayTeam':{'abbrev':'A','score':1},'homeTeam':{'abbrev':'H','score':1}}
def nhl_raw():
 return {'id':123,'awayTeam':{'abbrev':'A'},'homeTeam':{'abbrev':'H'},'summary':{'scoring':[
 {'periodDescriptor':{'number':2,'periodType':'REG'},'goals':[{'timeInPeriod':'01:20','teamAbbrev':{'default':'A'},'firstName':{'default':'Away'},'lastName':{'default':'Scorer'},'assists':[],'awayScore':1,'homeScore':1}]},
 {'periodDescriptor':{'number':1,'periodType':'REG'},'goals':[{'timeInPeriod':'10:05','teamAbbrev':{'default':'H'},'firstName':{'default':'Home'},'lastName':{'default':'Scorer'},'assists':[{'name':{'default':'First Assist'}},{'name':{'default':'Second Assist'}}],'awayScore':0,'homeScore':1}]}]}}
class ScoringTests(unittest.TestCase):
 def test_nhl_chronology_full_names_assists_and_cumulative_clock(self):
  r=nhl_goals(nhl_raw(),BOX);self.assertEqual([g['scorer'] for g in r['goals']],['Home Scorer','Away Scorer']);self.assertEqual(r['goals'][1]['time'],'21:20');self.assertEqual(r['goals'][0]['assists'],['First Assist','Second Assist']);self.assertEqual(r['goals'][1]['assists'],[])
 def test_unknown_assists_are_not_unassisted(self):
  raw=nhl_raw();del raw['summary']['scoring'][0]['goals'][0]['assists'];self.assertIsNone(nhl_goals(raw,BOX)['goals'][1]['assists'])
 def test_wrong_game_team_or_incomplete_sequence_is_unavailable(self):
  for raw in [dict(nhl_raw(),id=999),dict(nhl_raw(),awayTeam={'abbrev':'X'})]:self.assertEqual(safe_goals(nhl_goals,raw,BOX)['status'],'error')
  raw=nhl_raw();raw['summary']['scoring'].pop();self.assertEqual(safe_goals(nhl_goals,raw,BOX)['status'],'error')
 def test_shootout_decision_not_an_assisted_goal(self):
  box=copy.deepcopy(BOX);box['awayTeam']['score']=2;box['gameOutcome']={'lastPeriodType':'SO'};raw=nhl_raw();raw['summary']['scoring'].append({'periodDescriptor':{'number':5,'periodType':'SO'},'goals':[{'invalid':'must not become a goal'}]});r=nhl_goals(raw,box);self.assertEqual(len(r['goals']),2);self.assertEqual(r['shootoutWinner'],'A')
 def test_nl_revoked_goal_and_mmss(self):
  raw={'actions':[{'actions':[{'action':'revokedGoal'},{'action':'goal','third':1,'homeTeam':True,'time':'48','playerFirstName':'Home','playerLastName':'Scorer','assist1FirstName':'First','assist1LastName':'Assist','assist2FirstName':'Second','assist2LastName':'Assist','awayTeamResult':0,'homeTeamResult':1}]}]};box=copy.deepcopy(BOX);box['awayTeam']['score']=0;r=nl_goals(raw,box,'REG');self.assertEqual(r['goals'][0]['time'],'00:48');self.assertEqual(r['goals'][0]['assists'],['First Assist','Second Assist'])
 def test_liiga_penalty_miss_and_overtime(self):
  g={'period':4,'gameTime':3717,'scorerPlayer':{'firstName':'OT','lastName':'Scorer'},'assistantPlayers':[],'homeTeamScore':1,'awayTeamScore':0};miss=dict(g,period=1,gameTime=100,goalTypes=['RL0'],homeTeamScore=0)
  raw={'game':{'homeTeam':{'goalEvents':[miss,g]},'awayTeam':{'goalEvents':[]},'finishedType':'ENDED_DURING_EXTENDED_GAME_TIME'}};box=copy.deepcopy(BOX);box['awayTeam']['score']=0;r=liiga_goals(raw,box);self.assertEqual(len(r['goals']),1);self.assertEqual(r['goals'][0]['time'],'61:57')
 def test_empty_timeline_is_distinct_from_missing_source(self):
  raw=nhl_raw();raw['summary']['scoring']=[];box=copy.deepcopy(BOX);box['awayTeam']['score']=box['homeTeam']['score']=0;self.assertEqual(nhl_goals(raw,box)['goals'],[]);del raw['summary']['scoring'];self.assertEqual(safe_goals(nhl_goals,raw,box)['status'],'error')
 def test_duplicate_goal_rejected(self):
  raw=nhl_raw();raw['summary']['scoring'].append(copy.deepcopy(raw['summary']['scoring'][0]));self.assertEqual(safe_goals(nhl_goals,raw,BOX)['status'],'error')
