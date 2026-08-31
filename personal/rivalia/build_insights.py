#!/usr/bin/env python3
"""Generate insights-data.json for the reverse map: loot-value hunting,
quests doable at your level, item-farming lookup, and REAL hunt areas
(dense kiteable spawn clusters). All numbers use REAL Rivalia data
(catalog-stats.json + hunt-spots.json). Combat uses the official 7.4 formula.

Tune the CHAR block to your current character. Re-run to refresh.
Usage: python3 build_insights.py
"""
import json, math, re, glob, os, collections, statistics

# ---- YOUR CHARACTER (edit when it changes) ----
CHAR = dict(level=30, distance=64, shielding=53, hp=515, ammo_atk=30, stance=1.2)
OX, OY = 31744, 30701
REF = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    '..', '..', '.claude', 'skills', 'rivalia', 'references'))

d  = json.load(open('catalog-stats.json'))
hs = json.load(open('hunt-spots.json'))
def slug(n): return n.lower().replace(' ', '-').replace("'", '')

avg = math.floor((5*CHAR['distance']+50)*CHAR['ammo_atk']*CHAR['stance']*49.5/10000)
maxhit = math.floor((5*CHAR['distance']+50)*CHAR['ammo_atk']*CHAR['stance']*99/10000)

def is_ranged(c):
    atks = ' '.join(c.get('attacks', []))
    return bool(re.search(r'(Physical \(\d+-[1-9]|Fire|Energy|Ice|Poison \()', atks)) and 'Melee' in atks

def spawn_count(name):
    return sum(p.get('amount', 1) for p in hs.get(slug(name), []))

# ---- value table: REAL NPC prices scraped from rivaliaonline.com/items.php ----
# items-prices.json is keyed by slug -> {sell, buy, traders, npc}. The "loot value"
# is the MAX NPC Sell price (what you pocket selling loot). 0 = no NPC buys it
# (junk, or player-market only). Refresh with: python3 scrape_prices.py --all
try:
    PRICES = json.load(open('items-prices.json'))
except Exception:
    PRICES = {}
def val(item):     return PRICES.get(slug(item), {}).get('sell') or 0
def buy_at(item):  return PRICES.get(slug(item), {}).get('buy')
def sell_npc(item):return PRICES.get(slug(item), {}).get('npc')
def traders(item): return PRICES.get(slug(item), {}).get('traders_list') or []

# reverse loot index item -> [(mob, hp)]
rev = collections.defaultdict(list)
for name, c in d.items():
    for it in c.get('loot', []):
        rev[it.strip().lower()].append(name)

# ---- SECTION 1: loot-value — ALL items in the bestiary ----
# Every distinct loot item, with up to 5 droppers (each clickable on the map to
# highlight where it spawns), market value where known (0 = unknown, verify on Rivalia).
loot_rows = []
for it, mobs in rev.items():
    # rank droppers by farmability (spawns / HP); keep top 5, each with slug for map lookup
    dl = []
    for n in set(mobs):
        hp = d[n].get('health') or 1
        sc = spawn_count(n)
        dl.append(dict(mob=n, slug=slug(n), hp=hp, spawns=sc,
                       score=round(sc/(hp/100), 1)))
    dl.sort(key=lambda x: -x['score'])
    best = min(dl, key=lambda x: x['hp']) if dl else None
    loot_rows.append(dict(item=it.title(), value=val(it),
                          sell_npc=sell_npc(it), buy=buy_at(it),
                          traders=traders(it),
                          droppers=len(dl), mobs=dl[:5],
                          easiest_hp=best['hp'] if best else 0,
                          top_spawns=dl[0]['spawns'] if dl else 0))
# sort: known value desc first, then by best dropper farmability for the unpriced ones
loot_rows.sort(key=lambda r: (-r['value'], -r['top_spawns']))
loot_value = loot_rows   # ALL of them

# ---- SECTION 2: quests doable at level ----
def field(txt, *names):
    for n in names:
        m = re.search(rf'(?im)^[-*]?\s*\**\s*{n}\s*\**\s*[:=]\s*(.+)$', txt)
        if m:
            v = m.group(1).strip().strip('*').strip()
            if v and v not in ('-', '?', '—'): return v
    return None
def lvlnum(s):
    if not s: return None
    m = re.search(r'(\d+)', s); return int(m.group(1)) if m else None

quests = []
for f in sorted(glob.glob(f'{REF}/quests/*.md')):
    txt = open(f).read()
    mt = re.search(r'(?m)^#\s+(.+)', txt)
    title = mt.group(1).strip() if mt else os.path.basename(f)[:-3]
    rl = field(txt, 'Recommended Level', 'lvlrec', 'Recommended level')
    rw = field(txt, 'Reward', 'Rewards')
    n = lvlnum(rl)
    # doable = no rec level stated, OR rec level <= your level
    doable = (n is None) or (n <= CHAR['level'])
    quests.append(dict(title=title, rec_level=n, reward=rw or '?',
                       doable=doable, file='quests/'+os.path.basename(f)))
def has_val(rw):
    keys = ['armor','helmet','shield','ring','amulet','sword','boots','rune','spear',
            'crossbow','axe','hammer','gem','lance','rapier']
    return any(k in (rw or '').lower() for k in keys)
# doable first, then valuable-reward, then by level
quests.sort(key=lambda x: (not x['doable'], not has_val(x['reward']), x['rec_level'] or 0))

# ---- SECTION 3: item farming — EVERY item, droppers ranked by farmability (density/HP) ----
farm = {}
for it_lower, mobs in rev.items():
    out = []
    for name in set(mobs):
        hp = d[name].get('health') or 1
        nmob = spawn_count(name)
        score = round(nmob / (hp/100), 1)   # keep even 0-spawn droppers, ranked last
        out.append(dict(mob=name, slug=slug(name), hp=hp, mobs=nmob, score=score))
    out.sort(key=lambda x: -x['score'])
    farm[it_lower.title()] = out[:5]        # top 5 droppers per item

# ---- HUNT AREAS: from the fandom hunting-place references (NOT synthesized) ----
# Each named 7.4 area with a Mapper Coords in its ref file becomes a map pin.
# We enrich it with REAL Rivalia data: which of its listed creatures actually spawn
# near that coord, and the exp/shot you'd get on the kiteable (melee, HP<=350) ones.
HUNT_REF = os.path.join(REF, 'hunting-places')

def parse_first_coord(txt):
    m = re.search(r'(\d{1,3})\.(\d{1,3})/(\d{1,3})\.(\d{1,3})/(\d{1,2})', txt)
    if not m: return None
    xh, xl, yh, yl, z = [int(x) for x in m.groups()]
    return xh*256+xl, yh*256+yl, z

def field_ref(txt, *names):
    for n in names:
        m = re.search(rf'(?im)^-\s*\**\s*{n}\s*\**\s*:\s*(.+)$', txt)
        if m: return m.group(1).strip().lstrip('*').strip()
    return None

def creatures_list(txt):
    return [m.group(1).strip() for m in re.finditer(r'(?m)^-\s+([A-Z][A-Za-z\' ]+?)\s*$', txt)]

areas = []
for f in sorted(glob.glob(f'{HUNT_REF}/*.md')):
    txt = open(f).read()
    c0 = parse_first_coord(txt)
    if not c0: continue                          # only areas with a locatable coord
    rx, ry, rz = c0
    px, py = rx-OX, ry-OY
    if not (0 <= px <= 1685 and 0 <= py <= 2827): continue
    name = re.search(r'(?m)^#\s+(.+)', txt).group(1).strip()
    crs = creatures_list(txt)
    # which listed creatures actually spawn within 70 tiles of the coord (real Rivalia)?
    present, kite_exp, kite_shots, spawn_here = [], 0, 0, 0
    for cr in crs:
        pts = [p for p in hs.get(slug(cr), []) if abs(p['x']-rx) < 70 and abs(p['y']-ry) < 70]
        if not pts: continue
        present.append(cr)
        spawn_here += sum(p.get('amount', 1) for p in pts)
        cc = d.get(cr)
        if cc and 0 < (cc.get('health') or 0) <= 350 and not is_ranged(cc):
            hp = cc['health']; arm = cc.get('armor') or 0
            stk = math.ceil(hp/max(1, avg-arm//2))
            n_here = sum(p.get('amount', 1) for p in pts)
            kite_exp += cc['experience']*n_here; kite_shots += stk*n_here
    eps = round(kite_exp/kite_shots, 1) if kite_shots else 0
    # The parsed coord is usually the ENTRANCE (surface, z7). The actual hunting happens
    # on the floor where this area's creatures really spawn. Find that dominant floor
    # (near the entrance x/y) and place the map pin THERE, so "vai" lands on the mobs.
    floor_pts = collections.defaultdict(list)   # z -> [(x,y)]
    for cr in present:
        for p in hs.get(slug(cr), []):
            if abs(p['x']-rx) < 120 and abs(p['y']-ry) < 120:
                floor_pts[p['z']].append((p['x'], p['y']))
    if floor_pts:
        hz = max(floor_pts, key=lambda z: len(floor_pts[z]))   # busiest floor
        fp = floor_pts[hz]
        hx = round(statistics.mean(px2 for px2, _ in fp))
        hy = round(statistics.mean(py2 for _, py2 in fp))
        dists = sorted(((px2-hx)**2+(py2-hy)**2)**0.5 for px2, py2 in fp)
        radius = max(18, min(int(dists[int(len(dists)*0.8)]), 90))
    else:
        hz, hx, hy, radius = rz, rx, ry, 25       # fallback: entrance coord
    areas.append(dict(
        name=name,
        # map pin = dominant hunting floor + centroid
        x=hx, y=hy, z=hz, px=hx-OX, py=hy-OY, radius=radius,
        # entrance coord kept for reference (where you go DOWN from the surface)
        entrance=dict(x=rx, y=ry, z=rz, px=px, py=py),
        rec_level=field_ref(txt, 'Recommended Level'),
        loot=field_ref(txt, 'Notable Loot'),
        profit=field_ref(txt, r'Profit / Exp', 'Profit'),
        creatures_present=present[:12], spawn_near=spawn_here,
        exp_per_shot=eps, file='hunting-places/'+os.path.basename(f)))
# rank: those with real kiteable spawns first (by eps), then the rest by spawn density
areas.sort(key=lambda a: (a['exp_per_shot'] == 0, -a['exp_per_shot'], -a['spawn_near']))

# ---- CITY LANDMARKS (7.4 vanilla coords from TibiaWiki, validated in-bounds) ----
# Shown as always-on labels on the surface floors so you can orient on the map.
CITIES = [
    {"name": "Thais",       "px": 621,  "py": 1523, "z": 7},
    {"name": "Carlin",      "px": 599,  "py": 1091, "z": 7},
    {"name": "Venore",      "px": 1203, "py": 1380, "z": 6},
    {"name": "Kazordoon",   "px": 870,  "py": 1222, "z": 7},
    {"name": "Ab'Dendriel", "px": 921,  "py": 951,  "z": 7},
    {"name": "Edron",       "px": 1467, "py": 1129, "z": 7},
    {"name": "Darashia",    "px": 1492, "py": 1731, "z": 7},
    {"name": "Ankrahmun",   "px": 1402, "py": 2115, "z": 7},
    {"name": "Port Hope",   "px": 885,  "py": 2068, "z": 7},
    {"name": "Fibula",      "px": 517,  "py": 1684, "z": 7},
    {"name": "Svargrond",   "px": 534,  "py": 445,  "z": 7},
    {"name": "Liberty Bay", "px": 565,  "py": 2093, "z": 7},
    {"name": "Yalahar",     "px": 1061, "py": 533,  "z": 7},
]

# ---- ROUTES (walking logic extracted from fandom text+images, in routes-logic/) ----
ROUTES = []
rl_dir = 'routes-logic'
if os.path.isdir(rl_dir):
    for rf in sorted(glob.glob(f'{rl_dir}/*.json')):
        try:
            r = json.load(open(rf))
            if 'route' in r: ROUTES.append(r)
        except Exception:
            pass

# link a route to a hunting area when the route destination matches the area name
for a in areas:
    an = a['name'].lower()
    for r in ROUTES:
        dest = (r.get('to') or '').lower() + ' ' + r.get('slug', '')
        rn = r.get('route', '').lower()
        # match on the area name appearing in the route destination/name (e.g. Mintwallin, Femor Hills, Hellgate)
        key = an.split('(')[0].strip()
        if key and (key in dest or key in rn or key.replace(' ', '-') in r.get('slug', '')):
            a['route'] = {'slug': r['slug'], 'route': r['route']}
            break

# ---- REWARD CHESTS (222 geolocated) + narrative QUESTLINES (5), from rivaliaonline.com ----
CHESTS = []
if os.path.exists('chests.json'):
    try: CHESTS = json.load(open('chests.json'))
    except Exception: pass
QUESTLINES = []
if os.path.exists('questlines.json'):
    try: QUESTLINES = json.load(open('questlines.json'))
    except Exception: pass

out = dict(char=CHAR, avg_hit=avg, max_hit=maxhit,
           loot_value=loot_value, quests=quests, farm=farm, areas=areas,
           cities=CITIES, routes=ROUTES, chests=CHESTS, questlines=QUESTLINES)
json.dump(out, open('insights-data.json', 'w'), indent=1)
print(f"insights-data.json written: {len(loot_value)} loot rows, {len(quests)} quests, "
      f"{len(farm)} farm items, {len(areas)} hunt areas. avg hit={avg} max={maxhit}")
