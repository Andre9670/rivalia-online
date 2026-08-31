# CLAUDE.md — working guide for this repo

Personal Rivalia Online project (hobby). This repo is self-contained: no work systems,
no OneDrive, no Midway, no AIM package. Publishing is **GitHub Pages** (`map/index.html`).

## Use the skill
For anything about the game (monster stats, hunting spots, loot, prices, quests, NPCs,
map/positions, Paladin strategy), the **`rivalia` skill** in `.claude/skills/rivalia/`
applies. Follow its rules: never give Rivalia numbers from memory — verify against
`personal/rivalia/catalog-stats.json` / `hunt-spots.json` and `wiki.rivaliaonline.com`.

## Standing rules (see personal/rivalia/NOTES.md)
- The reverse map's user-facing UI is **English**. Don't reintroduce Italian UI strings.
- The PK/relationship crawl filters to **World == Aeternum** (Andrea's world). Don't
  confuse this with the "Legacy" *rate set* (that's about rates, not the world value).

## Regenerating & publishing the map
```bash
cd personal/rivalia
python3 build_insights.py
INLINE=1 python3 build_html.py     # writes ../../map/index.html
```
Then commit `map/index.html` and push — GitHub Pages republishes. `INLINE=1` = the
self-contained (base64) build that gets published. Without it you get a lighter
local-test build (`rivalia-reverse-map.html`, git-ignored) needing `creatures/`.

## Data pipeline (all local Python, public scraping)
`build_seed.py → crawl_pk.py → build_pkdata.py → build_relationships.py →
build_insights.py → build_html.py`. The weekly refresh is
`personal/rivalia/cron/pk-map-refresh.sh` (intended as a Claude Routine).

## Conventions
- All Rivalia sources/output live in `personal/rivalia/`; the only published file is
  `map/index.html`.
- Verify HTML visually with headless Chromium at `/opt/pw-browsers/chromium` if needed.
