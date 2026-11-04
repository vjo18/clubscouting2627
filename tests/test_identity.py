import json
import tempfile
import unittest
from pathlib import Path
from clubscout.build import build


class AutomaticIdentityTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        for p in ['config','data_raw/reports','public/data']:
            (self.root/p).mkdir(parents=True,exist_ok=True)
        config={'season':'2026-2027','clubs':[
            {'id':'one','rbfa_club_id':'1','teams':[{'include':True,'rbfa_team_id':t,'role':role} for t,role in [('a','A'),('r','reserves')]]},
            {'id':'two','rbfa_club_id':'2','teams':[{'include':True,'rbfa_team_id':'b','role':'A'}]}
        ]}
        (self.root/'config/clubs.json').write_text(json.dumps(config))
        (self.root/'data_raw/birthyears.csv').write_text('club_id;person_id;birth_year\n')

    def tearDown(self):
        self.temp.cleanup()

    def report(self, match, team, name):
        row={'team_rbfa_id':team,'club_rbfa_id':'2' if team=='b' else '1','name':name,
             'started':None,'bench_only':None,'minutes':None}
        (self.root/f'data_raw/reports/{match}.json').write_text(json.dumps({'source':match,'players':[row]}))

    def test_same_club_name_merges_without_any_manual_mapping(self):
        self.report('a1','a','Jan Janssens')
        for i in range(3):self.report('r'+str(i),'r','  ＪＡＮ   JANSSENS ')
        self.report('b1','b','Jan Janssens')
        self.report('a2','a','Jan Janssen')
        result=build(self.root)
        self.assertEqual(len(result['players']),3)
        p=next(p for p in result['players'] if p['club_id']=='one' and p['id']=='name:jan janssens')
        self.assertEqual(p['identity_method'],'club_name')
        self.assertTrue(p['multiple_teams'])
        self.assertEqual(p['teams']['a']['listed'],1)
        self.assertEqual(p['teams']['r']['listed'],3)
        self.assertFalse(any('geen A-selectie' in s for s in p['signals']))
        self.assertEqual(p['teams']['r']['minutes_known_matches'],0)

    def test_birthyears_from_old_ids_survive_and_conflicts_remain_unknown(self):
        self.report('a1','a','Jan Janssens')
        self.report('r1','r','Jan Janssens')
        (self.root/'config/player_identity.csv').write_text('club_id;team_id;name;person_id\none;a;Jan Janssens;old-a\none;r;Jan Janssens;old-r\n')
        births=self.root/'data_raw/birthyears.csv'
        births.write_text('club_id;person_id;birth_year\none;old-a;2006\n')
        self.assertEqual(build(self.root)['players'][0]['birth_year'],2006)
        births.write_text('club_id;person_id;birth_year\none;old-a;2006\none;old-r;2005\n')
        result=build(self.root)
        self.assertEqual(len(result['players']),1)
        self.assertIsNone(result['players'][0]['birth_year'])


if __name__=='__main__':unittest.main()
