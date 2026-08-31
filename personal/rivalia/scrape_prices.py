#!/usr/bin/env python3
"""Scrape NPC trade prices for every loot item from rivaliaonline.com/items.php?item=<slug>.

The "loot value" we care about = the MAX NPC Sell price (what you pocket selling loot).
We also keep the MIN NPC Buy price (cheapest place to buy it) for reference.

Only scrapes the DISTINCT loot items present in catalog-stats.json (the exact set the
loot-value tab renders), so we don't hammer the site for irrelevant pages.

Output: items-prices.json  ->  {slug: {"item": Name, "sell": int|None, "buy": int|None,
                                        "traders": int, "npc": "<best sell NPC> (<city>)"}}
Idempotent + resumable: re-reads the existing cache and only fetches missing/forced slugs.
Usage:  python3 scrape_prices.py            # fill in missing only
        python3 scrape_prices.py --all       # re-scrape everything
"""
import json, re, sys, time, html, urllib.request
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
CACHE = 'items-prices.json'
ROW = re.compile(
    r'<td><a href="npcs\.php[^"]*">([^<]+)</a></td>\s*'
    r'<td class="it-city">([^<]+)</td>\s*'
    r'<td class="it-num">([^<]+)</td>\s*'
    r'<td class="it-num">([^<]+)</td>')
HEAD = re.compile(r'<h3>Traded by <span[^>]*>(\d+)</span>')

def slug(n): return n.lower().replace(' ', '-').replace("'", '')

def gp(x):
    x = x.replace('&mdash;', '').replace('—', '').replace('gp', '').replace(',', '').strip()
    return int(x) if x.isdigit() else None

def scrape(item):
    s = slug(item)
    url = f'https://rivaliaonline.com/items.php?item={s}'
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            h = urllib.request.urlopen(req, timeout=20).read().decode('utf-8', 'replace')
            break
        except Exception as e:
            if attempt == 2:
                return s, {'item': item, 'sell': None, 'buy': None, 'traders': 0, 'npc': None, 'err': str(e)}
            time.sleep(1.0)
    hm = HEAD.search(h)
    n = int(hm.group(1)) if hm else 0
    rows = ROW.findall(h)
    best_sell, best_npc, best_city = None, None, None
    min_buy = None
    traders = []                     # full list: every NPC with its city + buy/sell
    for npc, city, buy, sell in rows:
        sv, bv = gp(sell), gp(buy)
        traders.append({'npc': html.unescape(npc.strip()),
                        'city': html.unescape(city.strip()),
                        'buy': bv, 'sell': sv})
        if sv is not None and (best_sell is None or sv > best_sell):
            best_sell, best_npc, best_city = sv, npc.strip(), city.strip()
        if bv is not None and (min_buy is None or bv < min_buy):
            min_buy = bv
    return s, {'item': item, 'sell': best_sell, 'buy': min_buy, 'traders': n,
               'npc': html.unescape(f'{best_npc} ({best_city})') if best_npc else None,
               'traders_list': traders}

def main():
    force = '--all' in sys.argv
    d = json.load(open('catalog-stats.json'))
    items = sorted({it.strip() for c in d.values() for it in c.get('loot', [])})
    try:
        cache = json.load(open(CACHE))
    except Exception:
        cache = {}
    todo = [it for it in items if force or slug(it) not in cache]
    print(f'{len(items)} loot items, {len(todo)} to scrape ({"forced all" if force else "missing only"})')
    done = 0
    with ThreadPoolExecutor(max_workers=6) as ex:
        for s, rec in ex.map(scrape, todo):
            cache[s] = rec
            done += 1
            if done % 25 == 0:
                json.dump(cache, open(CACHE, 'w'), indent=0)
                print(f'  {done}/{len(todo)} ... last: {rec["item"]} sell={rec["sell"]}')
    json.dump(cache, open(CACHE, 'w'), indent=0)
    priced = sum(1 for v in cache.values() if v.get('sell'))
    print(f'DONE. {len(cache)} cached, {priced} have an NPC sell price.')

if __name__ == '__main__':
    main()
