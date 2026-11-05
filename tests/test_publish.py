import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from scripts import publish_data


class PublishTest(unittest.TestCase):
    def cmd(self,path,*args):
        return subprocess.run(['git',*map(str,args)],cwd=path,check=True,text=True,capture_output=True)

    def commit(self,path,message):
        self.cmd(path,'add','.');self.cmd(path,'-c','user.name=Test','-c','user.email=test@example.invalid','commit','-m',message)

    def test_stale_generated_json_and_concurrent_push_preserve_latest_birthyears_and_code(self):
        with tempfile.TemporaryDirectory() as folder:
            folder=Path(folder);origin=folder/'origin.git';seed=folder/'seed'
            self.cmd(folder,'init','--bare','--initial-branch=main',origin)
            self.cmd(folder,'clone',origin,seed)
            for p in ['scripts','data_raw/reports','public/data']:(seed/p).mkdir(parents=True,exist_ok=True)
            (seed/'data_raw/reports/old.json').write_text('{"parser_version":2}')
            (seed/'data_raw/birthyears.csv').write_text('old-year')
            (seed/'version').write_text('old-code')
            (seed/'public/data/players.json').write_text('{"old":true}')
            (seed/'scripts/import_birthyears.py').write_text("from pathlib import Path\nimport json\nr=Path('.')\nout={'reports':sorted(p.name for p in (r/'data_raw/reports').glob('*.json')),'years':(r/'data_raw/birthyears.csv').read_text(),'code':(r/'version').read_text()}\n(r/'public/data/players.json').write_text(json.dumps(out))\n")
            self.commit(seed,'initial');self.cmd(seed,'push','origin','main')
            worker=folder/'worker';self.cmd(folder,'clone',origin,worker)
            (worker/'data_raw/reports/new.json').write_text('{"parser_version":2}')
            (worker/'public/data/players.json').write_text('{"stale":true}')
            (seed/'data_raw/birthyears.csv').write_text('latest-year')
            (seed/'version').write_text('latest-code')
            (seed/'public/data/players.json').write_text('{"concurrent":true}')
            self.commit(seed,'concurrent user changes');self.cmd(seed,'push','origin','main')
            actual_git=publish_data.git;injected=False
            def race(root,*args,**kwargs):
                nonlocal injected
                if args and args[0]=='push' and not injected:
                    injected=True
                    (seed/'data_raw/birthyears.csv').write_text('newest-year-during-push')
                    self.commit(seed,'second concurrent change');self.cmd(seed,'push','origin','main')
                return actual_git(root,*args,**kwargs)
            with patch.object(publish_data,'git',side_effect=race):
                self.assertTrue(publish_data.publish(worker))
            verify=folder/'verify';self.cmd(folder,'clone',origin,verify)
            result=json.loads((verify/'public/data/players.json').read_text())
            self.assertEqual(result['reports'],['new.json','old.json'])
            self.assertEqual(result['years'],'newest-year-during-push')
            self.assertEqual(result['code'],'latest-code')
            self.assertTrue(injected)


if __name__=='__main__':unittest.main()
