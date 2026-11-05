"""Clubgebonden CSV-import, inclusief het MacroDroid-formaat uit scouting2627."""
import csv
import io
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


def norm(value):
    import unicodedata
    return ' '.join(unicodedata.normalize('NFKC',str(value or '')).casefold().split())


def read_csv(path):
    if not path.exists() or not path.stat().st_size:return []
    raw=path.read_bytes()
    try:text=raw.decode('utf-8-sig')
    except UnicodeDecodeError:text=raw.decode('cp1252')
    first=text.splitlines()[0]
    sep=';' if first.count(';')>=first.count(',') else ','
    return list(csv.DictReader(io.StringIO(text,newline=''),delimiter=sep))


def import_uploads(root):
    data=json.loads((root/'public/data/players.json').read_text())
    known_players={(p['club_id'],p['id']):p for p in data['players']}
    aliases={}
    def alias(name,cid):
        if norm(name):aliases.setdefault(norm(name),set()).add(cid)
    for club in data['clubs']:
        alias(club['id'],club['id']);alias(club['name'],club['id'])
    teams={t['rbfa_team_id']:c['id'] for c in data['clubs'] for t in c['teams'] if t.get('rbfa_team_id')}
    for file in (root/'data_raw/reports').glob('*.json'):
        report=json.loads(file.read_text())
        for team in report.get('teams',[]):
            if team['team_rbfa_id'] in teams:alias(team['name'],teams[team['team_rbfa_id']])
    dest=root/'data_raw/birthyears.csv'
    records={}
    current_year=datetime.now(ZoneInfo('Europe/Brussels')).year
    for r in read_csv(dest):
        year=str(r.get('birth_year','')).strip()
        if not year.isdecimal() or not 1900<=int(year)<=current_year:continue
        key=(r['club_id'],r['person_id'])
        if key in records and records[key]['birth_year']!=year:raise ValueError('Tegenstrijdig bestaand geboortejaar: '+str(key))
        records[key]={'club_id':key[0],'person_id':key[1],'birth_year':year}
    added=skipped=0
    conflicts=[]
    for file in sorted((root/'data_raw/birthyear_uploads').glob('*.csv')):
        for r in read_csv(file):
            if not {'Naam','Geboortejaar'}.issubset(r):raise ValueError(str(file)+': kolommen Naam en Geboortejaar ontbreken')
            if norm(r.get('Gevonden')) in {'false','onwaar','nee','no','0','niet gevonden'}:skipped+=1;continue
            club=r.get('ClubID') or r.get('ClubRBFA') or r.get('Club') or r.get('Ploeg') or ''
            ids=aliases.get(norm(club),set())
            year=r.get('Geboortejaar','').strip()
            if len(ids)!=1 or not year.isdecimal() or len(year)!=4 or not 1900<=int(year)<=current_year:
                skipped+=1;continue
            cid=next(iter(ids));pid='name:'+norm(r.get('Naam'))
            key=(cid,pid)
            if key not in known_players:skipped+=1;continue
            existing=records.get(key)
            if existing:
                if existing['birth_year']!=year:conflicts.append(str(key))
                continue
            p=known_players[key]
            if p.get('birth_year') is not None and p['birth_year']!=int(year):conflicts.append(str(key));continue
            records[key]={'club_id':cid,'person_id':pid,'birth_year':year};added+=1
    if conflicts:raise ValueError('Geboortejaarconflicten; niets overschreven: '+', '.join(sorted(set(conflicts))))
    temp=dest.with_suffix('.tmp')
    with temp.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['club_id','person_id','birth_year'],delimiter=';',lineterminator='\n')
        writer.writeheader();writer.writerows(records[k] for k in sorted(records))
    temp.replace(dest)
    return {'added':added,'skipped':skipped,'known':len(records)}
