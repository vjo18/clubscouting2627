"""Publiceer brondata bovenop actuele main; genereer JSON opnieuw, zonder rebase."""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def git(root, *args, check=True):
    result=subprocess.run(['git',*map(str,args)],cwd=root,text=True,capture_output=True)
    if check and result.returncode:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result


def publish(root, source=None, attempts=4):
    root=Path(root).resolve()
    source=Path(source or root/'data_raw').resolve()
    with tempfile.TemporaryDirectory(prefix='.publish-',dir=root.parent) as tmp:
        tmp=Path(tmp);snapshot=tmp/'snapshot';snapshot.mkdir()
        # De eigen run kan achterlopen op nieuwe geboortejaren of uploads op main.
        # Alleen opgehaalde wedstrijdbronnen worden overgezet, geen master-CSV/JSON.
        for folder in ['reports','calendars']:
            if (source/folder).exists():shutil.copytree(source/folder,snapshot/folder)
        if (source/'scrape_status.json').exists():shutil.copyfile(source/'scrape_status.json',snapshot/'scrape_status.json')
        for attempt in range(attempts):
            git(root,'fetch','origin','main')
            work=tmp/f'publish-{attempt}'
            git(root,'worktree','add','--detach',work,'origin/main')
            try:
                base=git(work,'rev-parse','HEAD').stdout.strip()
                for folder in ['reports','calendars']:
                    for file in (snapshot/folder).glob('*.json'):
                        dest=work/'data_raw'/folder/file.name
                        dest.parent.mkdir(parents=True,exist_ok=True)
                        if folder=='reports' and dest.exists():
                            old=json.loads(dest.read_text());new=json.loads(file.read_text())
                            if old.get('parser_version',1)>new.get('parser_version',1):continue
                        shutil.copyfile(file,dest)
                if (snapshot/'scrape_status.json').exists():
                    shutil.copyfile(snapshot/'scrape_status.json',work/'data_raw/scrape_status.json')
                # De nieuwste code gebruikt de nieuwste CSV-uploads en geboortejaren.
                subprocess.run([sys.executable,'scripts/import_birthyears.py'],cwd=work,check=True)
                git(work,'add','data_raw','public/data/players.json')
                if git(work,'diff','--cached','--quiet',check=False).returncode==0:
                    print('Geen gegevenswijzigingen te publiceren.');return False
                git(work,'-c','user.name=github-actions[bot]','-c','user.email=41898282+github-actions[bot]@users.noreply.github.com',
                    'commit','-m','Werk clubdata en geboortejaren bij op actuele main')
                result=git(work,'push','origin','HEAD:main',check=False)
                if result.returncode==0:
                    print('Brondata en opnieuw berekend dashboard gepubliceerd.');return True
                git(root,'fetch','origin','main')
                if git(root,'rev-parse','origin/main').stdout.strip()==base:
                    raise RuntimeError(result.stderr.strip())
                print(f'Main wijzigde tijdens publicatie; bouw opnieuw op actuele main ({attempt+1}/{attempts}).')
            finally:
                git(root,'worktree','remove','--force',work,check=False)
        raise RuntimeError('Main bleef wijzigen; brongegevens staan in het workflow-artifact voor herstel zonder herscrapen.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path)
    args=p.parse_args();publish(Path(__file__).resolve().parents[1],args.source)
