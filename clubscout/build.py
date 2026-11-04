import csv
import json
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def norm(name):
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())


def build(root=ROOT):
    config = json.loads((root/'config/clubs.json').read_text())
    # Team-ID is verplicht: 'KM Torhout A' is ook de naam van Res A.
    teams = {t['rbfa_team_id']: (c,t) for c in config['clubs'] for t in c['teams'] if t['include'] and t.get('rbfa_team_id')}
    overrides = {}
    with (root/'config/player_identity.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            key = (r['club_id'],r['team_id'],norm(r['name']))
            if key in overrides and overrides[key] != r['person_id']:
                raise ValueError('Tegenstrijdige identiteitskoppeling')
            overrides[key] = r['person_id']
    births = defaultdict(set)
    with (root/'data_raw/birthyears.csv').open(encoding='utf-8-sig') as f:
        for r in csv.DictReader(f, delimiter=';'):
            if r['birth_year'].isdigit() and 1900 <= int(r['birth_year']) <= 2100:
                births[(r['club_id'],r['person_id'])].add(int(r['birth_year']))
    players, reports_seen, coverage = {}, set(), defaultdict(set)
    for path in sorted((root/'data_raw/reports').glob('*.json')):
        report = json.loads(path.read_text())
        if report['source'] in reports_seen:
            raise ValueError('Dubbel wedstrijdverslag: '+report['source'])
        reports_seen.add(report['source'])
        for r in report['players']:
            tid = r['team_rbfa_id']
            if tid not in teams:
                continue
            c,t = teams[tid]
            if r['club_rbfa_id'] != c['rbfa_club_id']:
                raise ValueError('Ploeg hoort volgens bron bij andere club')
            coverage[tid].add(report['source'])
            name_key = norm(r['name'])
            explicit = overrides.get((c['id'],tid,name_key))
            # Geen stille koppeling op alleen een naam: voorlopig per ploeg.
            pid = explicit or f'unverified:{tid}:{name_key}'
            key = (c['id'],pid)
            p = players.setdefault(key, {'id':pid,'club_id':c['id'],'name':r['name'],
                                        'identity_verified': bool(explicit), 'teams':{},'birth_year':None})
            years = births.get(key,set())
            p['birth_year'] = next(iter(years)) if len(years)==1 else None
            stats = p['teams'].setdefault(tid, {'listed':0,'known_minutes':0,'minutes_known_matches':0,
                                              'known_starts':0,'known_bench_only':0,'matches':[]})
            if report['source'] in stats['matches']:
                raise ValueError('Speler dubbel op hetzelfde wedstrijdblad: '+r['name'])
            stats['listed'] += 1
            stats['known_starts'] += int(r['started'] is True)
            stats['known_bench_only'] += int(r['bench_only'] is True)
            if r['minutes'] is not None:
                stats['known_minutes'] += r['minutes']
                stats['minutes_known_matches'] += 1
            stats['matches'].append(report['source'])
    for p in players.values():
        p['multiple_teams'] = len(p['teams']) > 1
        p['signals'] = []
        a_ids = [t['rbfa_team_id'] for c in config['clubs'] if c['id']==p['club_id'] for t in c['teams'] if t['include'] and t['role']=='A']
        lower = sum(s['listed'] for tid,s in p['teams'].items() if tid not in a_ids)
        a_listed = sum(p['teams'].get(tid,{}).get('listed',0) for tid in a_ids)
        if p['identity_verified'] and lower >= 3 and not a_listed:
            p['signals'].append('Minstens 3 selecties elders; geen A-selectie in ingelezen data. Controleer A-dekking.')
        if p['multiple_teams']:
            p['signals'].append('Op wedstrijdbladen van meerdere ploegen')
    calendars = {}
    for path in (root/'data_raw/calendars').glob('*.json'):
        calendar = json.loads(path.read_text())
        tid = calendar['team_id']
        if tid not in teams:
            continue
        played = {m['url'] for m in calendar['matches'] if m.get('score') is not None}
        calendars[tid] = {'observed':len(calendar['matches']), 'played':len(played),
                          'imported':len(played & coverage[tid]), 'fetched_at':calendar['fetched_at'],
                          'completeness':calendar.get('completeness','unverified'),
                          'preserved':calendar.get('preserved',0)}
    result = {'clubs':config['clubs'],'season':config['season'],'players':list(players.values()),
              'calendarCoverage':calendars,
              'coverage':{tid:len(urls) for tid,urls in coverage.items()},
              'notice':'Selecties zijn geen gespeelde wedstrijden. Ontbrekende gegevens blijven onbekend. Ongekoppelde spelers worden per ploeg getoond.'}
    dest = root/'public/data/players.json'
    temp = dest.with_suffix('.tmp')
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    temp.replace(dest)
    return result


if __name__ == '__main__':
    print(f"{len(build()['players'])} spelers opgeslagen")
