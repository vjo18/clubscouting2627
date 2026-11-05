"""Importeer een gerenderd HTML-bestand; schrijft pas na succesvolle parsing."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clubscout.parser import parse_report

p = argparse.ArgumentParser()
p.add_argument('html',type=Path)
p.add_argument('--source',required=True,help='Exacte RBFA-wedstrijd-URL of unieke lokale bronverwijzing')
p.add_argument('--output-dir',type=Path,default=Path(__file__).resolve().parents[1]/'data_raw/reports')
p.add_argument('--expected-score',help='Kalenderscore, bijvoorbeeld 3-5; afwijkingen weigeren')
a = p.parse_args()
r = parse_report(a.html.read_text(),a.source)
if a.expected_score and '-'.join(map(str,r['score'])) != a.expected_score:
    raise ValueError('Score op wedstrijdblad verschilt van kalender: '+a.source)
a.output_dir.mkdir(parents=True,exist_ok=True)
dest = a.output_dir/f'{hashlib.sha256(a.source.encode()).hexdigest()}.json'
temp = dest.with_suffix('.tmp')
temp.write_text(json.dumps(r,ensure_ascii=False,indent=2))
temp.replace(dest)
print(f"{len(r['players'])} namen; {r['quality']}; {dest.name}")

