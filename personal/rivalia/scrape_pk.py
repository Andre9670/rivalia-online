#!/usr/bin/env python3
"""Rivalia PK-graph scraper (Aeternum).

1. Reads player list from /tmp/all_players.json (built from highscores).
2. Downloads each character profile (cached to /tmp/pk_profiles/).
3. Parses the profile: vocation/level/last-login + FULL recent-deaths list
   (date, victim=this char, killers[], unjustified flag).
4. Emits an edge list "victim <- killer" that we aggregate elsewhere.

Killer links in the deaths section use SINGLE quotes: href='characterprofile.php?name=X'.
Only PvP deaths carry a <a> killer link; monster deaths are plain text -> skipped as PvE.
"""
import re, html, json, os, sys, urllib.parse, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
CACHE = "/tmp/pk_profiles"
os.makedirs(CACHE, exist_ok=True)

def fetch(name):
    fn = os.path.join(CACHE, urllib.parse.quote(name, safe='') + ".html")
    if os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return open(fn, encoding='utf-8', errors='replace').read()
    url = "https://rivaliaonline.com/characterprofile.php?name=" + urllib.parse.quote(name)
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for attempt in range(3):
        try:
            h = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')
            open(fn, 'w', encoding='utf-8').write(h)
            return h
        except Exception as e:
            time.sleep(1.5)
    return None

def parse_profile(name, h):
    if not h:
        return None
    h2 = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', h, flags=re.S | re.I)
    txt = re.sub(r'<[^>]+>', ' ', h2); txt = html.unescape(txt)
    txt = re.sub(r'[ \t]+', ' ', txt); txt = re.sub(r'\n\s*\n+', '\n', txt)
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    d = {}
    for i, l in enumerate(lines):
        if l in ('Sex', 'Vocation', 'Level', 'World', 'Residence', 'Last Login') and i + 1 < len(lines):
            d[l] = lines[i + 1]
    # deaths: each .cp-death block
    deaths = []
    for m in re.finditer(r'<div class="cp-death-time">([^<]+)</div>\s*<div class="cp-death-detail">(.*?)</div>', h, flags=re.S):
        date = m.group(1).strip(); body = m.group(2)
        lvl = re.search(r'Killed at level (\d+)', body)
        killers = [(html.unescape(nm.replace('+', ' ')), html.unescape(disp))
                   for nm, disp in re.findall(r"characterprofile\.php\?name=([^'\"]+)['\"]>([^<]+)</a>", body)]
        unj = "'unjustified'" in body or 'unjustified' in re.sub(r'<[^>]+>', ' ', body).lower()
        deaths.append({'date': date, 'level': int(lvl.group(1)) if lvl else None,
                       'killers': [k[1] for k in killers], 'unjustified': unj,
                       'is_pvp': bool(killers)})
    def toi(v):
        try: return int(str(v).strip())
        except: return None
    return {'name': name, 'level': toi(d.get('Level')), 'vocation': d.get('Vocation'),
            'world': d.get('World'), 'residence': d.get('Residence'),
            'last_login': d.get('Last Login'), 'deaths': deaths}

def main():
    players = json.load(open('/tmp/all_players.json'))
    print(f"scraping {len(players)} profiles...", file=sys.stderr)
    results = {}
    def work(nm):
        return nm, parse_profile(nm, fetch(nm))
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, (nm, pr) in enumerate(ex.map(work, players)):
            if pr: results[nm] = pr
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(players)}", file=sys.stderr)
    json.dump(results, open('/tmp/pk_profiles.json', 'w'), ensure_ascii=False)
    ok = sum(1 for r in results.values() if r)
    tot_deaths = sum(len(r['deaths']) for r in results.values())
    pvp = sum(1 for r in results.values() for d in r['deaths'] if d['is_pvp'])
    print(f"done: {ok} profiles, {tot_deaths} death entries, {pvp} PvP deaths", file=sys.stderr)

if __name__ == '__main__':
    main()
