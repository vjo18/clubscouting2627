"""Alleen expliciet toegelaten competitienamen; onbekend is niet competitief."""
import json
import re
from datetime import datetime
from zoneinfo import ZoneInfo


def label(value):
    return ' '.join(str(value or '').casefold().split())


def is_league_fixture(team, match):
    if team.get('competition_id') and match.get('competition_id'):
        return team['competition_id']==match['competition_id']
    approved = {label(name) for name in team.get('league_competitions', []) if label(name)}
    return bool(label(match.get('competition'))) and label(match.get('competition')) in approved


MONTHS = dict(zip(
    ('januari', 'februari', 'maart', 'april', 'mei', 'juni', 'juli', 'augustus', 'september', 'oktober', 'november', 'december'),
    range(1, 13),
))


def fixture_date(match, season):
    text = str(match.get('text') or '').casefold()
    found = re.search(r'\b(\d{1,2})\s+(' + '|'.join(MONTHS) + r')\b', text)
    if not found:
        return None
    start = int(str(season).split('-')[0])
    month = MONTHS[found.group(2)]
    year = start if month >= 7 else start + 1
    try:
        return datetime(year, month, int(found.group(1))).date()
    except ValueError:
        return None


def is_future_fixture(match, season, today=None):
    date = fixture_date(match, season)
    return date is not None and date > (today or datetime.now(ZoneInfo('Europe/Brussels')).date())


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
                scoped[tid]=[]
                continue
            matches = [m for m in calendars[tid]['matches'] if is_league_fixture(team, m) and not is_future_fixture(m, config['season'])]
            if not matches:
                raise ValueError('Geen wedstrijd met de goedgekeurde reeksnaam voor ploeg '+tid)
            scoped[tid] = matches
    else:
        scoped = {tid: [m for m in c['matches'] if not is_future_fixture(m, config['season'])] for tid, c in calendars.items()}
    return calendars, scoped
