"""Conservatieve parser voor gerenderde RBFA-wedstrijdbladen (stdlib)."""
import re
from html.parser import HTMLParser


class Node:
    def __init__(self, tag='', attrs=()):
        self.tag, self.attrs, self.children = tag, dict(attrs), []

    @property
    def text(self):
        return ' '.join(' '.join(c.text if isinstance(c, Node) else c for c in self.children).split())

    def has(self, cls):
        return cls in self.attrs.get('class', '').split()

    def find(self, tag=None, cls=None):
        for c in self.children:
            if isinstance(c, Node):
                if (tag is None or c.tag == tag) and (cls is None or c.has(cls)):
                    yield c
                yield from c.find(tag, cls)


class DOM(HTMLParser):
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs)
        self.stack[-1].children.append(n)
        if tag not in self.VOID:
            self.stack.append(n)

    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                break

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def event_minute(text, duration=90):
    m = re.fullmatch(r"\s*(\d+)(?:\s*\+\s*(\d+))?\s*['’‘′]?\s*",text)
    return min(duration,int(m[1])) if m else None


def enrich_minutes(players, duration=90):
    """Alleen toepassen bij expliciet gescheiden basis- en wisselspelers."""
    for p in players:
        markers=p['events_observed']
        def values(kind):
            return [event_minute(e['text'],duration) for e in markers if kind in e['type'].split()]
        ins,outs=values('in'),values('out')
        reds=values('red')+values('yellowred')
        if len(ins)>1 or len(outs)>1 or None in ins+outs+reds:
            continue
        start=0 if p['started'] else (ins[0] if ins else None)
        if start is None:
            if outs:continue
            p.update(minutes=0,bench_only=True,subbed_in=False)
            continue
        ends=[duration]+outs+reds
        end=min(ends)
        if end<start or (p['started'] and ins):continue
        p.update(minutes=end-start,bench_only=False,subbed_in=not p['started'])
    # Ontbrekende of tegenstrijdige wissels mogen geen betrouwbaar percentage opleveren.
    for tid in {p['team_rbfa_id'] for p in players}:
        group=[p for p in players if p['team_rbfa_id']==tid]
        loss=0
        for p in group:
            if p['minutes'] is None:continue
            red=[event_minute(e['text'],duration) for e in p['events_observed'] if {'red','yellowred'} & set(e['type'].split())]
            if red and not p['bench_only']:
                loss+=duration-min(red)
        if any(p['minutes'] is None for p in group) or sum(p['minutes'] or 0 for p in group)!=11*duration-loss:
            for p in group:p.update(minutes=None,bench_only=None)


def parse_report(html, source):
    root = DOM(html).root
    summary = next(root.find(cls='event-summary'), None)
    if summary is None:
        raise ValueError('Geen wedstrijdheader: mogelijk onvolledig geladen of geblokkeerd')
    teams = []
    for team in summary.find(cls='team'):
        link = next(team.find('a'), None)
        heading = next(team.find('h4'), None)
        match = re.search(r'/club/(\d+)/ploeg/(\d+)', link.attrs.get('href','')) if link else None
        if match and heading:
            teams.append({'club_rbfa_id': match[1], 'team_rbfa_id': match[2], 'name': heading.text})
    if len(teams) != 2:
        raise ValueError('Geen twee herkenbare ploegen')
    score_node = next(summary.find(cls='score'), None)
    score = re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)', score_node.text) if score_node else None
    if not score:
        raise ValueError('Geen numerieke score; nog niet gespeeld of onbekende status')
    players = []
    lineups = next(root.find(cls='opstelling-tabel'), None)
    tables=list(lineups.find('table')) if lineups else []
    first_rows=list(tables[0].find('tr')) if tables else []
    first_cells=[c for row in first_rows for c in row.find('td') if c.has('player') and list(c.find(cls='name'))]
    has_bench_heading=bool(lineups and any(re.fullmatch(r'Wisselspelers|Substitutes|Remplaçants',n.text,re.I) for n in lineups.find() if n.tag in ('h2','h3','h4','h5','h6')))
    full=has_bench_heading and len(tables)>=2 and sum(not c.has('text-align-right') for c in first_cells)==11 and sum(c.has('text-align-right') for c in first_cells)==11
    starter_cells={id(c) for c in first_cells} if full else set()
    if lineups:
        for row in lineups.find('tr'):
            cells = [n for n in row.children if isinstance(n, Node) and n.tag == 'td']
            if list(row.find(cls='staff')):
                continue
            for i, cell in enumerate(cells):
                if not cell.has('player'):
                    continue
                name = next(cell.find(cls='name'), None)
                if name is None or not name.text:
                    continue
                away = cell.has('text-align-right')
                side = int(away)
                number_index = i + 1 if away else i - 1
                number = cells[number_index].text if 0 <= number_index < len(cells) and cells[number_index].has('digit') else None
                markers = []
                for extra in cell.find(cls='extra-info'):
                    markers.extend({'type': n.attrs.get('class',''), 'label': n.attrs.get('title',''), 'text': n.text} for n in extra.find(cls='item'))
                # Volgorde, rugnummer en afwezige events bewijzen geen basisplaats,
                # bankplaats, nul goals of speelminuten. Ook een kaart kan op de bank.
                players.append({**teams[side], 'name': re.sub(r'\((GK|C|n/a)\)', '', name.text,flags=re.I).strip(),
                                'number': number, 'goalkeeper': '(GK)' in name.text,
                                'captain': '(C)' in name.text, 'listed': True,
                                'started': (id(cell) in starter_cells) if full else None, 'subbed_in': None, 'bench_only': None,
                                'minutes': None, 'goals': None, 'events_observed': markers})
    if not players:
        raise ValueError('Geen spelerslijst: vorige data behouden')
    if full:enrich_minutes(players)
    return {'source': source, 'score': [int(score[1]),int(score[2])], 'teams': teams,
            'parser_version':2,'duration':90,'quality': 'full_lineup' if full else 'selection_only', 'players': players}

