import unittest
from europe_data import normalize, form

class EuropeTests(unittest.TestCase):
    def test_liiga_regular_season_only(self):
        rows=[dict(team_id=1,team_name='A',ranking=1,points=12,games=4,goals=15,goals_against=8,tournament=t) for t in ['runkosarja','valmistavat_ottelut']]
        actual=normalize('liiga','standings',rows)
        self.assertEqual(len(actual),1)
        self.assertEqual((actual[0]['games_played'],actual[0]['goals_for']),(4,15))
    def test_nl_stat_fields(self):
        row=dict(team_id=1,name='A',rank=1,gp=20,po=40,g=60,ga=30)
        actual=normalize('nl','standings',[row])[0]
        self.assertEqual((actual['team_name'],actual['games_played'],actual['points'],actual['goals_for']),('A',20,40,60))
    def test_players_and_goalkeepers(self):
        common=dict(player_id=1,first_name='A',last_name='B',team_name='Club',gp=10,g=4,assists=8,points=12)
        rows=normalize('nl','players',[dict(common,position='forward'),dict(common,position='goalkeeper')])
        self.assertEqual(len(rows),1)
        self.assertEqual((rows[0]['player_name'],rows[0]['goals']),('A B',4))
    def test_future_and_exhibitions(self):
        row=dict(game_id=1,date='2026-11-28T18:45:00Z',home_team_id=1,away_team_id=2,home_team_name='A',away_team_name='B',base_status='scheduled',home_team_result=0,away_team_result=0)
        rows=normalize('nl','games',[row,dict(row,is_exhibition=True)])
        self.assertEqual(len(rows),1)
        self.assertIsNone(rows[0]['score_home'])
        self.assertEqual(rows[0]['date'],'2026-11-28T19:45:00+01:00')
    def test_form_uses_only_completed_last_ten(self):
        games=[dict(date=f'2026-11-{i:02}',status='finished',home_team_id=1,away_team_id=2,score_home=3,score_away=1) for i in range(1,13)]
        games.append(dict(games[0],date='2026-11-28',status='scheduled',score_home=None,score_away=None))
        records=form([dict(team_id=1,team_name='A'),dict(team_id=2,team_name='B')],games)
        self.assertEqual([(r['games'],r['wins'],r['losses']) for r in records],[(10,10,0),(10,0,10)])
    def test_missing_and_duplicate_data_rejected(self):
        with self.assertRaises(ValueError): normalize('nl','standings',[dict(name='A')])
        row=dict(team_id=1,name='A',rank=1,gp=1,po=3)
        with self.assertRaises(ValueError): normalize('nl','standings',[row,row])
if __name__=='__main__': unittest.main()
