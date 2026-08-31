#!/usr/bin/env python3
"""Build the highscores seed list for the PK crawl -> /tmp/all_players.json (Aeternum).

Loops all 10 skill-type highscore boards x 5 pages on world=2 and extracts the unique
player names. This is the seed the recursive crawler (crawl_pk.py) expands from.
"""
import re, html, json, urllib.request, os
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
WORLD = os.environ.get('PK_WORLD', '2')  # 2=Aeternum
HERE = os.path.dirname(os.path.abspath(__file__))
# Persistent cumulative roster: every run UNIONS what it discovers, so coverage of the
# server grows week over week (a pure victim like Helsan enters once he's online/ranked
# once, and then stays known forever). This is how we approach full-server coverage
# despite no page listing every character.
KNOWN = os.path.join(HERE, 'known-players.json')

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        return urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')
    except Exception:
        return ''

def names_in(h):
    return {html.unescape(n.replace('+', ' ')).strip()
            for n in re.findall(r"characterprofile\.php\?name=([^\"'&]+)", h)}

names = set()
# 1) highscores: 10 skill boards x 5 pages
jobs = [f"https://rivaliaonline.com/highscores.php?world={WORLD}&type={t}&page={p}"
        for t in range(1, 11) for p in range(1, 6)]
# 2) online list (whoever is online right now) + global recent deaths feed (recent victims)
jobs += ["https://rivaliaonline.com/onlinelist.php",
         "https://rivaliaonline.com/deaths.php",
         f"https://rivaliaonline.com/deaths.php?world={WORLD}"]
with ThreadPoolExecutor(max_workers=12) as ex:
    for h in ex.map(get, jobs):
        names |= names_in(h)

# union with the persistent roster from prior runs
prev = set()
if os.path.exists(KNOWN):
    try: prev = set(json.load(open(KNOWN)))
    except Exception: prev = set()
names = {n for n in names if n and len(n) < 40}
roster = sorted(names | prev)
json.dump(roster, open(KNOWN, 'w'), ensure_ascii=False)

# the crawler reads these two; frontier = the full known roster so pure victims are scanned
json.dump(roster, open('/tmp/all_players.json', 'w'), ensure_ascii=False)
json.dump(roster, open('/tmp/frontier.json', 'w'), ensure_ascii=False)
print(f"seed: {len(names)} discovered this run, {len(prev)} from prior roster -> {len(roster)} total known")
