#!/usr/bin/env python3
"""Scrape Rivalia NPCs -> /tmp/npc_scraped.json (authoritative Rivalia data).

npcs.php lists ~356 NPCs; each npcs.php?npc=NAME page has:
  - city/region  (<i class="fa fa-map-marker"></i> CITY)
  - type badge   (Trader, ...)
  - Sell Offers  (NPC sells to player)  : item, amount, price gp
  - Buy Offers   (NPC buys from player) : item, amount, price gp
NO map coordinates — those are matched later from Tibiantis 7.7 (build_npcs.py).
"""
import re, html, json, os, urllib.parse, urllib.request, time
from concurrent.futures import ThreadPoolExecutor

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
CACHE = "/tmp/npc_pages"
os.makedirs(CACHE, exist_ok=True)
BASE = "https://rivaliaonline.com/npcs.php"

def fetch(url, fn):
    if fn and os.path.exists(fn) and os.path.getsize(fn) > 1000:
        return open(fn, encoding='utf-8', errors='replace').read()
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    for _ in range(3):
        try:
            h = urllib.request.urlopen(req, timeout=25).read().decode('utf-8', 'replace')
            if fn:
                open(fn, 'w', encoding='utf-8').write(h)
            return h
        except Exception:
            time.sleep(1.5)
    return None

def npc_list():
    h = fetch(BASE, None) or ''
    names = []
    for m in re.findall(r'\?npc=([^"\'&]+)', h):
        nm = html.unescape(urllib.parse.unquote(m.replace('+', ' '))).strip()
        if nm and nm not in names:
            names.append(nm)
    return names

def parse_offers(block):
    """Parse rows of a lib-table: item (img alt or td text), amount, price gp."""
    out = []
    for row in re.findall(r'<tr>(.*?)</tr>', block, re.S):
        alt = re.search(r'alt="([^"]+)"', row)
        tds = re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)
        if not tds:
            continue
        cells = [re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', c))).strip() for c in tds]
        item = alt.group(1).strip() if alt else (cells[0] if cells else '')
        nums = [c for c in cells if re.search(r'\d', c)]
        amount = re.sub(r'\D', '', nums[0]) if len(nums) >= 1 else ''
        price = re.sub(r'[^\d]', '', nums[-1]) if nums else ''
        if item:
            out.append({'item': item, 'amount': int(amount) if amount else None,
                        'price': int(price) if price else None})
    return out

def section(h, label):
    i = h.find(label + ' Offers')
    if i < 0:
        return []
    # take the FIRST table after the label; non-greedy stops at its own </table>
    # (no size cap — big general-store tables can exceed several KB)
    tbl = re.search(r'<table[^>]*>(.*?)</table>', h[i:], re.S)
    return parse_offers(tbl.group(1)) if tbl else []

def parse_npc(name, h):
    if not h:
        return None
    city = re.search(r'fa-map-marker"></i>\s*([^<&]+?)\s*(?:&nbsp;|<)', h)
    typ = re.search(r'fa-shopping-bag"></i>\s*([^<]+?)\s*</span>', h)
    return {
        'name': name,
        'city': html.unescape(city.group(1)).strip() if city else None,
        'type': html.unescape(typ.group(1)).strip() if typ else None,
        'sell': section(h, 'Sell'),   # NPC sells to player (you BUY here)
        'buy': section(h, 'Buy'),     # NPC buys from player (you SELL here)
    }

def main():
    names = npc_list()
    print(f"{len(names)} NPCs listed")
    def work(nm):
        url = BASE + '?npc=' + urllib.parse.quote(nm)
        fn = os.path.join(CACHE, urllib.parse.quote(nm, safe='') + '.html')
        return parse_npc(nm, fetch(url, fn))
    res = {}
    with ThreadPoolExecutor(max_workers=8) as ex:
        for i, r in enumerate(ex.map(work, names)):
            if r:
                res[r['name']] = r
            if (i + 1) % 50 == 0:
                print(f"  {i+1}/{len(names)}")
    json.dump(res, open('/tmp/npc_scraped.json', 'w'), ensure_ascii=False)
    wc = sum(1 for r in res.values() if r['city'])
    wo = sum(1 for r in res.values() if r['sell'] or r['buy'])
    print(f"done: {len(res)} NPCs, {wc} with city, {wo} with offers")

if __name__ == '__main__':
    main()
