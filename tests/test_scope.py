import json
import tempfile
import unittest
from pathlib import Path
from clubscout.build import build
from clubscout.scope import is_league_fixture


class LeagueScopeTest(unittest.TestCase):
    def test_exact_positive_allowlist(self):
        team={'league_competitions':['U19 Interprov Voetb V A']}
        self.assertTrue(is_league_fixture(team,{'competition':'  U19  Interprov Voetb V A  '}))
        for name in ['',None,'U19','Beker U19','Oefenwedstrijd','Croky Cup']:
            self.assertFalse(is_league_fixture(team,{'competition':name}))

    def test_old_cup_and_friendly_rows_excluded_from_all_totals(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for p in ['config','data_raw/reports','data_raw/calendars','public/data']:
                (root/p).mkdir(parents=True,exist_ok=True)
            team={'include':True,'rbfa_team_id':'1','role':'A','league_competitions':['Reeks A']}
            config={'season':'2026-2027','match_scope':'league_only','clubs':[{'id':'club','rbfa_club_id':'10','teams':[team]}]}
            (root/'config/clubs.json').write_text(json.dumps(config))
            (root/'config/player_identity.csv').write_text('club_id;team_id;name;person_id\n')
            (root/'data_raw/birthyears.csv').write_text('club_id;person_id;birth_year\n')
            labels=['Reeks A','Beker','Oefenwedstrijd','']
            matches=[{'url':'match-'+str(i),'competition':name,'score':[1,0]} for i,name in enumerate(labels)]
            (root/'data_raw/calendars/1.json').write_text(json.dumps({'team_id':'1','matches':matches,'fetched_at':'test'}))
            for i,m in enumerate(matches):
                player={'team_rbfa_id':'1','club_rbfa_id':'10','name':'Jan','started':True,'bench_only':False,'minutes':40 if i==0 else 90}
                rows=[player]
                if i==1:rows.append({**player,'name':'Alleen Beker'})
                (root/f'data_raw/reports/{i}.json').write_text(json.dumps({'source':m['url'],'players':rows}))
            result=build(root)
            self.assertEqual(len(result['players']),1)
            stats=result['players'][0]['teams']['1']
            self.assertEqual(stats['listed'],1)
            self.assertEqual(stats['known_minutes'],40)
            self.assertEqual(stats['known_starts'],1)
            self.assertEqual(stats['matches'],['match-0'])
            self.assertEqual(result['coverage'],{'1':1})
            self.assertEqual(result['calendarCoverage']['1']['played'],1)
            self.assertEqual(result['calendarCoverage']['1']['excluded'],3)
            previous=(root/'public/data/players.json').read_bytes()
            team['league_competitions']=['Onbekende reeks']
            (root/'config/clubs.json').write_text(json.dumps(config))
            with self.assertRaises(ValueError):build(root)
            self.assertEqual((root/'public/data/players.json').read_bytes(),previous)


if __name__=='__main__':unittest.main()
