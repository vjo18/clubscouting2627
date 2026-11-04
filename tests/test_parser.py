import json
import tempfile
import unittest
from pathlib import Path
from clubscout.parser import parse_report
from clubscout.build import build

FIXTURE=Path(__file__).parent/'fixtures/reserves.html'


class ParserTest(unittest.TestCase):
    def setUp(self):
        self.report=parse_report(FIXTURE.read_text(),'https://www.rbfa.be/nl/wedstrijd/7544599')

    def test_real_report(self):
        r=self.report
        self.assertEqual(r['score'],[3,5])
        self.assertEqual(len(r['players']),30)
        torhout=[p for p in r['players'] if p['team_rbfa_id']=='364285']
        self.assertEqual(len(torhout),15)
        self.assertTrue(all(p['minutes'] is None and p['started'] is None and p['goals'] is None for p in r['players']))
        self.assertFalse(any(p['name']=='Jens Dhelft' for p in r['players']))

    def test_second_goalkeeper_is_not_a_starter(self):
        p=next(p for p in self.report['players'] if p['name']=='Rhune Rosseel')
        self.assertTrue(p['goalkeeper'])
        self.assertIsNone(p['started'])
        self.assertIsNone(p['minutes'])

    def test_cards_are_not_goals_or_substitutions(self):
        p=next(p for p in self.report['players'] if p['name']=='Matheo Bleyaert')
        self.assertEqual(p['events_observed'][0]['label'],'Gele kaart')
        self.assertIsNone(p['subbed_in'])

    def test_blocked_page_rejected(self):
        with self.assertRaises(ValueError):parse_report('<html>Access denied</html>','x')


class BuildTest(unittest.TestCase):
    def test_identity_and_deduplication(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for p in ['config','data_raw/reports','public/data']:(root/p).mkdir(parents=True,exist_ok=True)
            (root/'config/clubs.json').write_text(json.dumps({'season':'2026-2027','clubs':[{'id':'club','rbfa_club_id':'1','teams':[{'include':True,'rbfa_team_id':t,'role':role} for t,role in [('a','A'),('r','reserves')]]}]}))
            (root/'config/player_identity.csv').write_text('club_id;team_id;name;person_id\n')
            (root/'data_raw/birthyears.csv').write_text('club_id;person_id;birth_year\n')
            report={'source':'fixture','players':[{'team_rbfa_id':t,'club_rbfa_id':'1','name':'Jan Janssens','started':None,'bench_only':None,'minutes':None} for t in ['a','r']]}
            (root/'data_raw/reports/one.json').write_text(json.dumps(report))
            self.assertEqual(len(build(root)['players']),1)
            self.assertTrue(build(root)['players'][0]['multiple_teams'])
            (root/'config/player_identity.csv').write_text('club_id;team_id;name;person_id\nclub;a;Jan Janssens;p1\nclub;r;Jan Janssens;p1\n')
            result=build(root)
            self.assertEqual(len(result['players']),1)
            self.assertTrue(result['players'][0]['multiple_teams'])
            self.assertEqual(result['players'][0]['teams']['a']['minutes_known_matches'],0)
            previous=(root/'public/data/players.json').read_bytes()
            (root/'data_raw/reports/two.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError):build(root)
            self.assertEqual((root/'public/data/players.json').read_bytes(),previous)


if __name__=='__main__':unittest.main()

