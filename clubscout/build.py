import csv
import json
import unicodedata
from collections import defaultdict
from pathlib import Path
from .scope import load_calendars

ROOT = Path(__file__).resolve().parents[1]


def norm(name):
    return ' '.join(unicodedata.normalize('NFKC', name).casefold().split())


def build(root=ROOT):
    config = json.loads((root/'config/clubs.json').read_text())
    # Team-ID is verplicht: 'KM Torhout A' is ook de naam van Res A.
    teams = {t['rbfa_team_id']: (c,t) for c in config['clubs'] for t in c['teams'] if t['include'] and t.get('rbfa_team_id')}
    source_calendars, scoped_calendars = load_calendars(root, config, teams)
    league_only = config.get('match_scope') == 'league_only'
    allowed = {tid: {m['url'] for m in matches if m.get('score') is not None}
               for tid, matches in scoped_calendars.items()}
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
            if league_only and report['source'] not in allowed.get(tid, set()):
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
    for tid, calendar in source_calendars.items():
        matches = scoped_calendars[tid]
        played = {m['url'] for m in matches if m.get('score') is not None}
        calendars[tid] = {'observed':len(matches), 'played':len(played),
                          'excluded':len(calendar['matches'])-len(matches),
                          'imported':len(played & coverage[tid]), 'fetched_at':calendar['fetched_at'],
                          'completeness':calendar.get('completeness','unverified'),
                          'preserved':calendar.get('preserved',0)}
    result = {'clubs':config['clubs'],'season':config['season'],'players':list(players.values()),
              'matchScope':config.get('match_scope','all'),
              'calendarCoverage':calendars,
              'coverage':{tid:len(urls) for tid,urls in coverage.items()},
              'notice':('Alleen competitiewedstrijden. ' if league_only else '')+'Selecties zijn geen gespeelde wedstrijden. Ontbrekende speelgegevens blijven onbekend. Een onbevestigde spelerkoppeling betekent dat nog niet bevestigd is dat dezelfde naam bij verschillende ploegen dezelfde persoon is.'}
    dest = root/'public/data/players.json'
    temp = dest.with_suffix('.tmp')
    temp.write_text(json.dumps(result,ensure_ascii=False,indent=2))
    temp.replace(dest)
    return result


if __name__ == '__main__':
    print(f"{len(build()['players'])} spelers opgeslagen")

