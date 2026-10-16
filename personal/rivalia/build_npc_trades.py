#!/usr/bin/env python3
"""Rebuild the buy/sell lists of every NPC in npcs.json so they are CLEAR and COMPLETE.

Problem with the Rivalia site's npcs.php?npc=NAME pages: item names are truncated to ONE word
("sword", "shield", "helmet"), and "Sell Offers" mixes both directions. So we use the item pages instead:
  items.php?item=<slug> -> "Traded by" table = (NPC, city, Buys, Sells)   [wiki-2026-10/item-traders.json]
where, from the PLAYER's point of view:
  Sells column = what the NPC PAYS you when you sell it to him   -> npc['buys']   ("Buys from you")
  Buys  column = what you PAY when you buy it from him           -> npc['sells']  ("Sells to you")
(verified on Haroun/Nah'bob/Zarith against the in-game vanilla behaviour and the NPC pages)

Extra rows that exist on the NPC page but not in the item DB (artifacts, some wands...) are resolved by
price + word match, by item id (learned across NPCs + GitBook artifact table) and, for Zarith, by the GitBook
"What he buys" list. What still can't be resolved is kept in npc['other'] with the truncated name.

Usage: python3 build_npc_trades.py            (reads/patches npcs.json in place)
Env:   NPC_CACHE=<dir with cached npcs.php pages> (missing pages are fetched)
"""
import json, re, os, html, collections, urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.join(HERE, 'wiki-2026-10')
CACHE = os.environ.get('NPC_CACHE', '/tmp/npc_pages_trades')
os.makedirs(CACHE, exist_ok=True)
UA = 'Mozilla/5.0 (X11; Linux x86_64) Chrome/120.0'
GATED = {"Zarith The Accredited", "Nah'bob", "Haroun", "Alesar", "Yaman"}

T = json.load(open(os.path.join(W, 'item-traders.json'))); NAMES = T['names']
CATS = json.load(open(os.path.join(W, 'item-categories.json')))
CAT_LABEL = {'swords': 'Swords', 'axes': 'Axes', 'clubs': 'Clubs', 'distance-weapons': 'Distance weapons', 'ammunition': 'Ammunition',
             'wands': 'Wands & staffs', 'runes': 'Runes', 'helmets': 'Helmets', 'armors': 'Armors', 'legs': 'Legs', 'boots': 'Boots',
             'shields': 'Shields', 'amulets': 'Amulets', 'rings': 'Rings', 'containers': 'Containers', 'artifacts': 'Artifacts',
             'food': 'Food', 'jewelry': 'Jewelry', 'creature-products': 'Creature products', 'other': 'Other'}
ARTIFACTS = [a['name'] for a in json.load(open(os.path.join(W, 'artifacts.json')))]
ART_IDS = {int(k): v for k, v in json.load(open(os.path.join(W, 'gitbook-artifact-ids.json'))).items()}
ZGB = {n: p for n, p in json.load(open(os.path.join(W, 'zarith-gitbook-buy-list.json')))['buys']}
npcs_doc = json.load(open(os.path.join(HERE, 'npcs.json')))
npcs = npcs_doc['npcs']

fn = lambda n: re.sub(r'[^A-Za-z0-9]', '_', n) + '.html'
def fetch(n):
    f = os.path.join(CACHE, fn(n))
    if os.path.exists(f): return n
    for _ in range(3):
        try:
            h = urllib.request.urlopen(urllib.request.Request('https://rivaliaonline.com/npcs.php?npc=' + urllib.parse.quote_plus(n), headers={'User-Agent': UA}), timeout=25).read().decode('utf-8', 'replace')
            open(f, 'w').write(h); return n
        except Exception:
            pass
    return None
with ThreadPoolExecutor(12) as ex: list(ex.map(fetch, [n['name'] for n in npcs]))

# ---- item DB lists per NPC ----
item_by = collections.defaultdict(list)       # npc -> [(item, side, price)]
for s, rows in T['traders'].items():
    for npc, city, b, se in rows:
        if se: item_by[npc].append((NAMES[s], 'buys', se))
        if b:  item_by[npc].append((NAMES[s], 'sells', b))

# ---- NPC page rows (truncated names + item ids) ----
ROW = re.compile(r'<img src="https?://items\.znote\.eu/(\d+)\.gif"\s+alt="([^"]*)".*?</td>\s*(?:<td[^>]*>([^<]*)</td>)\s*<td[^>]*>([\d,]+) gp</td>', re.S)
page = {}
for n in npcs:
    f = os.path.join(CACHE, fn(n['name']))
    h = open(f, errors='ignore').read() if os.path.exists(f) else ''
    rows = [(int(m.group(1)), html.unescape(m.group(2)), int(m.group(4).replace(',', ''))) for m in ROW.finditer(h)]
    page[n['name']] = rows

def match(cands, alt, price):
    a = alt.lower()
    return {c[0] for c in cands if c[2] == price and (c[0].lower().endswith(a) or a in c[0].lower().split() or c[0].lower().startswith(a))}

idname = {}                                   # item id -> full name (learned)
for iid, nm in ART_IDS.items(): idname[iid] = nm
learn = collections.defaultdict(collections.Counter)
for npc, rows in page.items():
    for iid, alt, price in rows:
        m = match(item_by.get(npc, []), alt, price)
        if len(m) == 1: learn[iid][next(iter(m))] += 1
for iid, c in learn.items():
    if len(c) == 1: idname[iid] = next(iter(c))

def sortk(l): return sorted(l, key=lambda o: (-o['price'], o['item']))
n_off = 0
for n in npcs:
    name = n['name']
    buys = {(i, p) for i, s, p in item_by.get(name, []) if s == 'buys'}
    sells = {(i, p) for i, s, p in item_by.get(name, []) if s == 'sells'}
    have = {i.lower() for i, p in buys | sells}
    other = []
    for iid, alt, price in page.get(name, []):
        cands = item_by.get(name, [])
        if match(cands, alt, price): continue                       # already covered by the item DB
        full = idname.get(iid)
        if not full and name == 'Zarith The Accredited':
            z = [k for k, p in ZGB.items() if p == price and (k.lower().endswith(alt.lower()) or alt.lower() in k.lower().split())]
            if len(z) == 1: full = z[0]
        if not full:                                                # artifacts the item DB doesn't list: match the truncated word, excluding artifacts whose id is already known
            known = set(ART_IDS.values())
            ar = [x for x in ARTIFACTS if x not in known and (x.lower().endswith(alt.lower()) or alt.lower() in x.lower().split())]
            if len(ar) == 1: full = ar[0]
        if full and full.lower() in have: continue
        if full and name == 'Zarith The Accredited':
            # GitBook "What he buys" is the COMPLETE buy list -> anything else he trades is something he SELLS you
            (buys if full in ZGB else sells).add((full, price)); have.add(full.lower()); continue
        other.append({'item': full or alt + ' (?)', 'price': price})
    if name == 'Zarith The Accredited':
        for k, p in ZGB.items():                                    # GitBook list: add what the item DB missed
            if k.lower() not in have: buys.add((k, p)); have.add(k.lower())
    n['buys'] = sortk([{'item': i, 'price': p, 'cat': CAT_LABEL.get(CATS.get(i, 'other'), 'Other')} for i, p in buys])
    n['sells'] = sortk([{'item': i, 'price': p, 'cat': CAT_LABEL.get(CATS.get(i, 'other'), 'Other')} for i, p in sells])
    n['other'] = sortk([dict(t) for t in {(o['item'], o['price']) for o in other} and [dict(item=i, price=p) for i, p in sorted({(o['item'], o['price']) for o in other})]])
    n.pop('sell', None); n.pop('buy', None)
    if n['buys'] or n['sells'] or n['other']: n_off += 1
    if name in GATED: n['gate'] = {"Zarith The Accredited": 'zarith', "Nah'bob": 'blue', "Haroun": 'blue', "Alesar": 'green', "Yaman": 'green'}[name]

npcs_doc['n_with_offers'] = n_off
json.dump(npcs_doc, open(os.path.join(HERE, 'npcs.json'), 'w'), indent=1, ensure_ascii=False)
z = next(n for n in npcs if n['name'] == 'Zarith The Accredited')
print(f"npcs.json patched: {n_off} NPCs with offers. Zarith: buys {len(z['buys'])}, sells {len(z['sells'])}, unresolved {len(z['other'])}")
print('unresolved rows overall:', sum(len(n['other']) for n in npcs))
