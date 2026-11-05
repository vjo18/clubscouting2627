"""Valideer de complete tijdelijke dataset vóór publicatie; dashboard als laatste."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clubscout.build import build
from clubscout.birthyears import import_uploads

root=Path(__file__).resolve().parents[1]
stage=Path(sys.argv[1])
for file in (stage/'data_raw/reports').glob('*.json'):
    report=json.loads(file.read_text())
    if not report.get('players') or not report.get('teams'):
        raise ValueError('Onvolledig verslag: '+file.name)
build(stage)
print(import_uploads(stage))
build(stage)
for folder in ['reports','calendars']:
    for file in (stage/'data_raw'/folder).glob('*.json'):
        dest=root/'data_raw'/folder/file.name
        dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_suffix('.tmp');shutil.copyfile(file,temp);temp.replace(dest)
for name in ['birthyears.csv','scrape_status.json']:
    source=stage/'data_raw'/name
    if source.exists():
        target=root/'data_raw'/name
        tmp=target.with_suffix('.tmp');shutil.copyfile(source,tmp);tmp.replace(target)
dest=root/'public/data/players.json'
temp=dest.with_suffix('.tmp');shutil.copyfile(stage/'public/data/players.json',temp);temp.replace(dest)
print('Gevalideerde dataset bijgewerkt; onbekende speelgegevens behouden als onbekend.')

