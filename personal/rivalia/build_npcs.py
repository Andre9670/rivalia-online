#!/usr/bin/env python3
"""Merge scraped Rivalia NPCs (/tmp/npc_scraped.json) with approximate Tibiantis 7.7
coordinates -> npcs.json.

Rivalia data is AUTHORITATIVE (name, city, buy/sell offers) but has NO map coords.
Tibiantis 7.7 (map-npcs.js) provides coords in the SAME absolute Tibia coordinate space,
matched here BY NAME only -> flagged coord_source='tibiantis-7.7-approx' (NOT authoritative;
7.7 geography ≈ 7.4 but Rivalia may have moved/added NPCs -> verify in-game).

Map pixel formula (Rivalia reverse map): px = x - 31744, py = y - 30701.
"""
import re, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OX, OY = 31744, 30701   # reverse-map origin (px=x-OX, py=y-OY)

npcs = json.load(open('/tmp/npc_scraped.json'))

# --- Tibiantis 7.7 coords: const mapNpcs = [["Name",x,y,z,...], ...] ---
tib = {}
mj = '/tmp/map-npcs.js'
if os.path.exists(mj):
    raw = open(mj, encoding='utf-8', errors='replace').read()
    for m in re.finditer(r'\["((?:[^"\\]|\\.)*)",\s*(\d+),\s*(\d+),\s*(\d+)', raw):
        nm = m.group(1).replace('\\', '')
        tib[nm.lower()] = (int(m.group(2)), int(m.group(3)), int(m.group(4)))

out = []
matched = 0
for name, n in sorted(npcs.items()):
    rec = {'name': name, 'city': n.get('city'), 'type': n.get('type'),
           'sell': n.get('sell') or [], 'buy': n.get('buy') or []}
    c = tib.get(name.lower())
    if c:
        x, y, z = c
        rec.update({'x': x, 'y': y, 'z': z, 'px': x - OX, 'py': y - OY,
                    'coord_source': 'tibiantis-7.7-approx'})
        matched += 1
    out.append(rec)

from collections import Counter
data = {
    'source': 'Rivalia npcs.php (authoritative: name/city/offers) + Tibiantis 7.7 coords (approx, name-matched)',
    'n_npcs': len(out),
    'n_with_coords': matched,
    'n_with_offers': sum(1 for r in out if r['sell'] or r['buy']),
    'cities': dict(Counter(r['city'] for r in out if r['city']).most_common()),
    'npcs': out,
}
path = os.path.join(HERE, 'npcs.json')
json.dump(data, open(path, 'w'), ensure_ascii=False)
print(f"wrote {path}: {len(out)} NPCs, {matched} with approx coords, "
      f"{data['n_with_offers']} with offers, {len(data['cities'])} cities")
print("  cities:", list(data['cities'].items())[:10])
