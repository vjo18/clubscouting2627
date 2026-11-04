"""Alleen expliciet toegelaten competitienamen; onbekend is niet competitief."""
import json


def label(value):
    return ' '.join(str(value or '').casefold().split())


def is_league_fixture(team, match):
    approved = {label(name) for name in team.get('league_competitions', []) if label(name)}
    return bool(label(match.get('competition'))) and label(match.get('competition')) in approved


def load_calendars(root, config, teams):
    calendars = {}
    for path in (root/'data_raw/calendars').glob('*.json'):
        calendar = json.loads(path.read_text())
        if calendar['team_id'] in teams:
            calendars[calendar['team_id']] = calendar
    scoped = {}
    if config.get('match_scope') == 'league_only':
        for tid, (_, team) in teams.items():
            if not team.get('league_competitions'):
                raise ValueError('Geen goedgekeurde competitie voor ploeg '+tid)
            if tid not in calendars:
                raise ValueError('Geen kalender voor competitiefilter: '+tid)
            matches = [m for m in calendars[tid]['matches'] if is_league_fixture(team, m)]
            if not matches:
                raise ValueError('Geen wedstrijd met de goedgekeurde reeksnaam voor ploeg '+tid)
            scoped[tid] = matches
    else:
        scoped = {tid: c['matches'] for tid, c in calendars.items()}
    return calendars, scoped
