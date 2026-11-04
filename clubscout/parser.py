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
                players.append({**teams[side], 'name': re.sub(r'\((GK|C)\)', '', name.text).strip(),
                                'number': number, 'goalkeeper': '(GK)' in name.text,
                                'captain': '(C)' in name.text, 'listed': True,
                                'started': None, 'subbed_in': None, 'bench_only': None,
                                'minutes': None, 'goals': None, 'events_observed': markers})
    if not players:
        raise ValueError('Geen spelerslijst: vorige data behouden')
    return {'source': source, 'score': [int(score[1]),int(score[2])], 'teams': teams,
            'quality': 'selection_only', 'players': players}
