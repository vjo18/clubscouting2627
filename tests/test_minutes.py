import json
import tempfile
import unittest
from pathlib import Path
from clubscout.parser import parse_report,event_minute
from clubscout.build import build
from clubscout.birthyears import import_uploads


class MinutesTest(unittest.TestCase):
    def test_real_full_report_starters_substitutes_red_card_and_unused_bench(self):
        report=parse_report((Path(__file__).parent/'fixtures/full-match.html').read_text(),'sample')
        ps={p['name']:p for p in report['players']}
        self.assertEqual(report['quality'],'full_lineup')
        self.assertEqual(ps['Jasper Otte']['minutes'],45)
        self.assertEqual(ps['Jiri Struyf']['minutes'],68)
        self.assertEqual(ps['Michiel Clyncke']['minutes'],22)
        self.assertEqual(ps['Leandro Lieven Depaepe']['minutes'],0)
        self.assertTrue(ps['Leandro Lieven Depaepe']['bench_only'])
        self.assertEqual(ps['Leandro Lieven Depaepe']['number'],'77')
        totals={t['name']:sum(p['minutes'] for p in report['players'] if p['team_rbfa_id']==t['team_rbfa_id']) for t in report['teams']}
        self.assertEqual(totals,{'KFC Merelbeke':945,'Sportkring Roeselare':990})
        self.assertEqual(event_minute('90+4‘'),90)
        self.assertEqual(event_minute('45+2‘'),45)

    def test_percentage_includes_unused_selections_and_repeated_jerseys(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for d in ['config','data_raw/reports','data_raw/birthyear_uploads','public/data']:(root/d).mkdir(parents=True,exist_ok=True)
            config={'season':'2026-2027','clubs':[{'id':'club','name':'Club Eén','rbfa_club_id':'1','teams':[{'rbfa_team_id':'a','role':'A','include':True,'minutes_enabled':True},{'rbfa_team_id':'r','role':'reserves','include':True,'minutes_enabled':False}]}]}
            (root/'config/clubs.json').write_text(json.dumps(config))
            (root/'data_raw/birthyears.csv').write_text('club_id;person_id;birth_year\n')
            def report(i,tid,minutes,number):
                r={'source':str(i),'players':[{'team_rbfa_id':tid,'club_rbfa_id':'1','name':'Jan','started':False,'bench_only':minutes==0,'minutes':minutes,'number':number}]}
                (root/f'data_raw/reports/{i}.json').write_text(json.dumps(r))
            for i,(mins,number) in enumerate([(90,'7'),(30,'7'),(0,'18'),(0,'18')]):report(i,'a',mins,number)
            report(4,'r',90,'10')
            result=build(root);p=result['players'][0];a=p['teams']['a']
            self.assertEqual(a['listed'],4)
            self.assertEqual(a['possible_minutes'],360)
            self.assertEqual(a['minutes_pct'],33.3)
            self.assertEqual(a['number_counts'],{'7':2,'18':2})
            self.assertIsNone(p['teams']['r']['minutes_pct'])
            report(5,'a',None,'7')
            self.assertIsNone(build(root)['players'][0]['teams']['a']['minutes_pct'])
            upload=root/'data_raw/birthyear_uploads/input.csv'
            upload.write_text('Ploeg;Naam;Geboortejaar;Gevonden\nClub Eén;Jan;2006;true\nClub Eén;Onbekende speler;2007;true\n')
            self.assertEqual(import_uploads(root)['added'],1)
            self.assertEqual(build(root)['players'][0]['birth_year'],2006)
            self.assertEqual(import_uploads(root)['added'],0)
            before=(root/'data_raw/birthyears.csv').read_bytes()
            upload.write_text('ClubRBFA;Naam;Geboortejaar\nClub Eén;Jan;2005\n')
            with self.assertRaises(ValueError):import_uploads(root)
            self.assertEqual((root/'data_raw/birthyears.csv').read_bytes(),before)


if __name__=='__main__':unittest.main()
