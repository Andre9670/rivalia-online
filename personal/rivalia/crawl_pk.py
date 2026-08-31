#!/usr/bin/env python3
"""Recursive PK crawl to closure (Aeternum).

Starts from a frontier of known names (highscores + online list + every killer/victim
already seen) and keeps fetching profiles, extracting NEW killer/victim names from each,
until no new names appear. This closes the gap where a killer only shows up in the
death record of an unranked victim (e.g. Papa Frita killing Nymeria).

Caps: MAX_ROUNDS and MAX_TOTAL guard against runaway. Profiles cached in /tmp/pk_profiles/.
Output: rewrites /tmp/pk_profiles.json with every profile parsed.
"""
import json, os, glob, urllib.parse
from concurrent.futures import ThreadPoolExecutor
import importlib.util

spec = importlib.util.spec_from_file_location('s', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scrape_pk.py'))
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)

MAX_ROUNDS = 15
MAX_TOTAL = 4000   # hard ceiling on profiles fetched

def cached_names():
    out = set()
    for f in glob.glob('/tmp/pk_profiles/*.html'):
        out.add(urllib.parse.unquote(os.path.basename(f)[:-5]))
    return out

def load_frontier():
    names = set()
    if os.path.exists('/tmp/frontier.json'):
        names |= set(json.load(open('/tmp/frontier.json')))
    if os.path.exists('/tmp/all_players.json'):
        names |= set(json.load(open('/tmp/all_players.json')))
    return {n for n in names if n and len(n) < 40}

def main():
    profiles = {}
    if os.path.exists('/tmp/pk_profiles.json'):
        profiles = json.load(open('/tmp/pk_profiles.json'))
    frontier = load_frontier() | set(profiles.keys()) | {'Nymeria'}
    seen = set(profiles.keys())
    total = len(seen)

    for rnd in range(1, MAX_ROUNDS + 1):
        todo = sorted(frontier - seen)
        if not todo:
            print(f"round {rnd}: nothing new -> closure reached")
            break
        if total + len(todo) > MAX_TOTAL:
            todo = todo[:max(0, MAX_TOTAL - total)]
            print(f"round {rnd}: capping to MAX_TOTAL, fetching {len(todo)}")
        print(f"round {rnd}: fetching {len(todo)} new profiles (total so far {total})")

        def work(nm):
            return nm, s.parse_profile(nm, s.fetch(nm))

        new_names = set()
        with ThreadPoolExecutor(max_workers=10) as ex:
            for nm, pr in ex.map(work, todo):
                seen.add(nm)
                if pr:
                    profiles[nm] = pr
                    # expand from every KILLER name found (their own profile may reveal more victims)
                    for d in pr['deaths']:
                        for k in d['killers']:
                            new_names.add(k)
        total = len(seen)
        frontier |= {n for n in new_names if n and len(n) < 40}
        json.dump(profiles, open('/tmp/pk_profiles.json', 'w'), ensure_ascii=False)
        if total >= MAX_TOTAL:
            print("hit MAX_TOTAL, stopping"); break

    ok = len(profiles)
    pvp = sum(1 for r in profiles.values() for d in r['deaths'] if d['is_pvp'])
    print(f"DONE: {ok} profiles cached, {pvp} PvP deaths total")

if __name__ == '__main__':
    main()
