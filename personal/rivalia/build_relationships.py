#!/usr/bin/env python3
"""Build the player-relationship graph -> relationships.json (Aeternum).

Consumes the SAME crawl the PK map uses (no extra fetching):
  - /tmp/pk_profiles.json      : per-player death history (killers[] per death)
  - /tmp/pk_profiles/*.html     : cached profile pages (for Guild + Previous Name)
  - pk-map-data.json            : per-killer danger score / class / stats

Emits a typed-edge relationship graph:
  - ally_guild          : same guild (declared)                         🟩
  - ally_cokill         : appeared together as co-killers on one death   🟩
  - enemy_reciprocal    : A killed B AND B killed A                      🟥
  - cofaction_shared    : >=3 common victims (hunt the same targets)     🟨

Identity: a renamed character (Previous Name) collapses to its CURRENT name so
edges don't fragment across a rename. Clusters = union-find over ALLY edges.

Run order:  crawl_pk.py -> build_pkdata.py -> build_relationships.py -> build_html.py
Pure function of the cached crawl -> deterministic, no Date.now / network.
"""
import json, re, html, glob, os, urllib.parse
from collections import defaultdict, Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PROF = os.environ.get('PK_PROFILES', '/tmp/pk_profiles.json')
CACHE = os.environ.get('PK_CACHE', '/tmp/pk_profiles')
SHARED_MIN = 3          # min common victims to draw a co-faction edge
COKILL_MIN = 1          # min co-kills to draw an ally edge

prof = json.load(open(PROF))
pkdata = json.load(open(os.path.join(HERE, 'pk-map-data.json')))
PK = pkdata['players']

# ---------- declared facts from cached HTML: guild (name+rank) + previous name ----------
guild_of, rank_of, prev_of = {}, {}, {}
for f in glob.glob(os.path.join(CACHE, '*.html')):
    nm = urllib.parse.unquote(os.path.basename(f)[:-5])
    h = open(f, encoding='utf-8', errors='replace').read()
    # Guild value shape: <strong>RANK</strong> of <a href="guilds.php?name=GUILD">GUILD</a>
    mg = re.search(r'cp-row-label">\s*Guild\s*</[^>]+>\s*<[^>]*cp-row-value">(.*?)</div>', h, re.S)
    if mg:
        blk = mg.group(1)
        ga = re.search(r'guilds\.php\?name=[^"]*"?[^>]*>([^<]+)</a>', blk)
        gr = re.search(r'<strong>([^<]+)</strong>', blk)
        if ga:
            guild_of[nm] = html.unescape(ga.group(1)).strip()
            if gr:
                rank_of[nm] = html.unescape(gr.group(1)).strip()
    mp = re.search(r'cp-row-label">\s*Previous Name\s*</[^>]+>\s*<[^>]*cp-row-value">(.*?)</', h, re.S)
    if mp:
        pv = re.sub(r'<[^>]+>', ' ', mp.group(1))
        pv = re.sub(r'\s+', ' ', html.unescape(pv)).strip()
        if pv:
            prev_of[nm] = pv

# ---------- identity map: previous_name -> current_name ----------
canon = {}
for cur, prev in prev_of.items():
    canon[prev] = cur
def C(name):
    seen = set()
    while name in canon and name not in seen:
        seen.add(name); name = canon[name]
    return name

# ---------- world filter: keep ONLY Andrea's world (Aeternum) ----------
# The crawl mixes worlds (Aeternum/Legacy/Ascendia). Names are globally unique and PvP is
# intra-world, so restricting to in-world (canonical) nodes detaches foreign subgraphs cleanly.
WORLD = os.environ.get('PK_WORLD_FILTER', 'Aeternum')
world_of = {n: p.get('world') for n, p in prof.items()}
allowed = {C(n) for n, p in prof.items() if p.get('world') == WORLD}
def _inworld(cn):
    return (cn in allowed) or (world_of.get(cn) is None)   # unknown world = uncrawled → same-world by PvP logic

# ---------- behavioral edges from the death graph ----------
directed = Counter()      # (killer -> victim) count
cokill = Counter()        # unordered co-killer pair -> count
for vname, p in prof.items():
    v = C(vname)
    if v not in allowed:
        continue
    for d in p['deaths']:
        if not d['is_pvp']:
            continue
        ks = list(dict.fromkeys(k for k in (C(x) for x in d['killers']) if _inworld(k)))
        for k in ks:
            if k != v:
                directed[(k, v)] += 1
        for i in range(len(ks)):
            for j in range(i + 1, len(ks)):
                cokill[tuple(sorted((ks[i], ks[j])))] += 1

vict_of = defaultdict(set)
for (k, v), _ in directed.items():
    vict_of[k].add(v)

# reciprocal (feud) edges: A->B and B->A
recip = {}
for (k, v), c in directed.items():
    if directed.get((v, k)):
        key = tuple(sorted((k, v)))
        recip[key] = directed[(k, v)] + directed.get((v, k), 0)  # counted twice, fixed below
# fix double count: recompute cleanly
recip = {}
seen_pair = set()
for (k, v) in list(directed):
    key = tuple(sorted((k, v)))
    if key in seen_pair:
        continue
    a, b = key
    if directed.get((a, b)) and directed.get((b, a)):
        recip[key] = directed[(a, b)] + directed[(b, a)]
        seen_pair.add(key)

# co-faction: shared victims >= SHARED_MIN
killers = [k for k in vict_of if len(vict_of[k]) >= 2]
shared = {}
for i in range(len(killers)):
    for j in range(i + 1, len(killers)):
        common = vict_of[killers[i]] & vict_of[killers[j]]
        if len(common) >= SHARED_MIN:
            shared[tuple(sorted((killers[i], killers[j])))] = len(common)

# guild cliques
guild_members = defaultdict(set)
for nm, g in guild_of.items():
    if C(nm) in allowed:
        guild_members[g].add(C(nm))

# ---------- assemble edges ----------
edges = []
for (a, b), w in cokill.items():
    if w >= COKILL_MIN and a != b:
        edges.append({'a': a, 'b': b, 'type': 'ally_cokill', 'w': w})
guild_pairs = set()
for g, mem in guild_members.items():
    mem = sorted(m for m in mem if m)
    for i in range(len(mem)):
        for j in range(i + 1, len(mem)):
            guild_pairs.add((mem[i], mem[j], g))
for a, b, g in guild_pairs:
    edges.append({'a': a, 'b': b, 'type': 'ally_guild', 'w': 1, 'guild': g})
for (a, b), w in recip.items():
    edges.append({'a': a, 'b': b, 'type': 'enemy_reciprocal', 'w': w})
for (a, b), w in shared.items():
    edges.append({'a': a, 'b': b, 'type': 'cofaction_shared', 'w': w})

# ---------- clusters: union-find over ALLY edges (guild + cokill) ----------
parent = {}
def find(x):
    parent.setdefault(x, x)
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
def union(x, y):
    parent[find(x)] = find(y)
for e in edges:
    if e['type'] in ('ally_guild', 'ally_cokill'):
        union(e['a'], e['b'])
clusters = defaultdict(list)
node_names = set()
for e in edges:
    node_names.add(e['a']); node_names.add(e['b'])
for n in node_names:
    clusters[find(n)].append(n)
cluster_id = {}
for cid, (root, members) in enumerate(sorted(clusters.items(), key=lambda kv: -len(kv[1]))):
    for m in members:
        cluster_id[m] = cid

# ---------- node metadata ----------
players = {}
for n in node_names:
    pk = PK.get(n, {})
    prf = prof.get(n, {})
    players[n] = {
        'name': n,
        'level': pk.get('level') or prf.get('level'),
        'vocation': pk.get('vocation') or prf.get('vocation'),
        'residence': pk.get('residence') or prf.get('residence'),
        'guild': guild_of.get(n),
        'guild_rank': rank_of.get(n),
        'prev_name': prev_of.get(n),
        'kills': pk.get('kills', 0),
        'unjustified': pk.get('unjustified', 0),
        'times_died_pvp': pk.get('times_died_pvp', 0),
        'danger_score': pk.get('danger_score', 0),
        'class': pk.get('class'),
        'cluster': cluster_id.get(n),
    }

by_type = Counter(e['type'] for e in edges)
out = {
    'source': 'relationship graph derived from PK crawl (world=' + WORLD + ')',
    'world': WORLD,
    'captured': pkdata.get('captured'),
    'n_players': len(players),
    'n_edges': len(edges),
    'edges_by_type': dict(by_type),
    'n_guilds': len(guild_members),
    'n_clusters': len(clusters),
    'n_renames': len(prev_of),
    'guilds': {g: sorted(m) for g, m in sorted(guild_members.items(), key=lambda kv: -len(kv[1]))},
    'players': players,
    'edges': edges,
}
path = os.path.join(HERE, 'relationships.json')
json.dump(out, open(path, 'w'), ensure_ascii=False)
print(f"wrote {path}")
print(f"  players(nodes): {len(players)} | edges: {len(edges)} {dict(by_type)}")
print(f"  guilds: {len(guild_members)} | clusters: {len(clusters)} | renames merged: {len(prev_of)}")
big = sorted(clusters.items(), key=lambda kv: -len(kv[1]))[:6]
for root, mem in big:
    gs = Counter(guild_of.get(m) for m in mem if guild_of.get(m))
    tag = gs.most_common(1)[0][0] if gs else '(no guild / co-kill only)'
    print(f"  cluster #{cluster_id[mem[0]]}: {len(mem)} players  ~{tag}")
