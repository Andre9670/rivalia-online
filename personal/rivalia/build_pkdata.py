#!/usr/bin/env python3
"""Aggregate the crawled profiles (/tmp/pk_profiles.json) into pk-map-data.json.

Reads every scanned profile, turns each PvP death "victim killed by Killer" into an
edge Killer->victim, aggregates per killer (kills, unjustified, victims, avg victim
level, level gap), computes a danger score + threat class, and writes pk-map-data.json.

Run order:  crawl_pk.py  ->  build_pkdata.py  ->  build_pkmap.py + build_html.py
"""
import json, re, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.environ.get('PK_PROFILES', '/tmp/pk_profiles.json')
WORLD = os.environ.get('PK_WORLD_FILTER', 'Aeternum')   # keep ONLY this world; drop cross-world contamination
prof = json.load(open(PROF))

# Andrea plays a single world (Aeternum). onlinelist/deaths + the recursive crawl pull in
# other worlds (Legacy, Ascendia) — filter them out. Names are globally unique on Rivalia and
# PvP is intra-world, so a foreign-world subgraph detaches cleanly.
allowed = {n for n, p in prof.items() if p.get('world') == WORLD}
def _inworld(name):
    """Include a referenced killer if it's an allowed-world player, or its world is unknown
    (uncrawled/parse-failed) — such names come from an in-world victim's death, so same world."""
    w = prof.get(name, {}).get('world')
    return (name in allowed) or (w is None)

kill = defaultdict(lambda: {'kills': 0, 'unjustified': 0, 'victims': []})
died = defaultdict(int)
for vname, p in prof.items():
    if vname not in allowed:
        continue
    for d in p['deaths']:
        if not d['is_pvp']:
            continue
        died[vname] += 1
        for killer in d['killers']:
            if not _inworld(killer):
                continue
            k = kill[killer]
            k['kills'] += 1
            if d['unjustified']:
                k['unjustified'] += 1
            k['victims'].append({'victim': vname, 'lv': d['level'], 'date': d['date'], 'unjustified': d['unjustified']})

players = {}
for name, k in kill.items():
    p = prof.get(name, {})
    lvl = p.get('level'); kills = k['kills']; unj = k['unjustified']
    vl = [v['lv'] for v in k['victims'] if v['lv']]
    avg_v = round(sum(vl) / len(vl), 1) if vl else None
    gap = round(lvl - avg_v, 1) if (lvl and avg_v) else 0
    score = unj * 10 + kills * 1.5 + (max(0, gap) / 8 if unj else 0)
    if unj >= 5:
        cls = 'PK / Serial'
    elif unj >= 2:
        cls = 'PK / Assassin'
    elif unj == 1:
        cls = 'Occasional PK'
    else:
        cls = 'Guild-war / justified'
    players[name] = {
        'name': name, 'level': lvl, 'vocation': p.get('vocation'),
        'residence': p.get('residence'), 'last_login': p.get('last_login'),
        'times_died_pvp': died.get(name, 0),
        'kills': kills, 'unjustified': unj, 'justified': kills - unj,
        'avg_victim_level': avg_v, 'level_gap': gap,
        'danger_score': round(score, 1), 'class': cls,
        'victims': sorted(k['victims'], key=lambda v: v['date'], reverse=True),
    }

MONTHS = {'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
          'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12}
def dkey(s):
    m = re.match(r'(\d{2}) (\w+) (\d{4})', s or '')
    return (int(m.group(3)), MONTHS.get(m.group(2), 0), int(m.group(1))) if m else (0, 0, 0)
alld = sorted((v['date'] for kk in kill.values() for v in kk['victims']), key=dkey)
span = f"{alld[0]} – {alld[-1]}" if alld else "?"

# captured date: derive from newest death date (avoid Date.now dependency)
captured = alld[-1].split(' (')[0] if alld else 'unknown'

data = {
    'source': 'characterprofile.php recursive death-graph crawl, world=' + WORLD,
    'world': WORLD,
    'captured': captured,
    'window': 'profile death history (' + span + ')',
    'n_profiles_scanned': len(allowed), 'n_crawled_all_worlds': len(prof), 'n_killers': len(players),
    'total_kills': sum(p['kills'] for p in players.values()),
    'total_unjustified': sum(p['unjustified'] for p in players.values()),
    'players': players,
}
out = os.path.join(HERE, 'pk-map-data.json')
json.dump(data, open(out, 'w'), ensure_ascii=False, indent=1)
print(f"wrote {out}: {len(prof)} profiles, {len(players)} killers, "
      f"{data['total_kills']} kills, {data['total_unjustified']} unjustified | span {span}")
