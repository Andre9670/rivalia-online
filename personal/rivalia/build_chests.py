#!/usr/bin/env python3
"""Fetch + parse Rivalia's 222 reward chests from rivaliaonline.com/quests.php?view=chests.
Each chest: name, loot items, and real x/y/z coordinates (geolocated).
Output: chests.json (consumed by build_html.py as a map layer + insights tab).
Re-run to refresh. Public page, no auth needed.
"""
import re, json, html as htmlmod, urllib.request

OX, OY = 31744, 30701
URL = "https://rivaliaonline.com/quests.php?view=chests"
UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36"

req = urllib.request.Request(URL, headers={'User-Agent': UA})
h = urllib.request.urlopen(req, timeout=60).read().decode('utf-8', 'replace')

def clean(s):
    s = re.sub(r'<span class="qs-chest-count">([^<]*)</span>\s*', r'\1 ', s)  # keep "12×"
    s = re.sub(r'<[^>]+>', '', s)
    return htmlmod.unescape(re.sub(r'\s+', ' ', s)).strip()

chests = []
for a in re.split(r'<article class="qs-chest">', h)[1:]:
    mt = re.search(r'qs-chest-title">([^<]+)</h3>', a)
    if not mt:
        continue
    items = [clean(x) for x in re.findall(r'<li>(.*?)</li>', a, re.S)]
    items = [i for i in items if i]
    c = {'name': htmlmod.unescape(mt.group(1)).strip(), 'items': items}
    mc = re.search(r'huntfinder\.php\?x=(\d+)&(?:amp;)?y=(\d+)&(?:amp;)?z=(\d+)', a)
    if mc:
        x, y, z = int(mc.group(1)), int(mc.group(2)), int(mc.group(3))
        px, py = x - OX, y - OY
        if 0 <= px <= 1685 and 0 <= py <= 2827:
            c.update({'x': x, 'y': y, 'z': z, 'px': px, 'py': py})
    chests.append(c)

json.dump(chests, open('chests.json', 'w'), indent=1)
loc = sum(1 for c in chests if 'px' in c)
print(f"chests.json: {len(chests)} chests, {loc} geolocated")
