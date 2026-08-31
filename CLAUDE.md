# CLAUDE.md — working guide for this repo

Personal Rivalia Online project (hobby). This repo is self-contained: no work systems,
no OneDrive, no Midway, no AIM package. Publishing is **GitHub Pages** (`map/index.html`).

## Two skills (no overlap)
- **`rivalia`** (`.claude/skills/rivalia/`) — GAME advice only: monster stats, hunting
  spots, loot, prices, quests, NPCs, positions, Paladin strategy. Rule: never give
  Rivalia numbers from memory — verify against `personal/rivalia/catalog-stats.json` /
  `hunt-spots.json` and `wiki.rivaliaonline.com`.
- **`rivalia-map`** (`.claude/skills/rivalia-map/`) — the **single source of truth** for
  building/updating/**publishing** the interactive reverse map (the pipeline, the
  pathfinder, the weekly PK refresh). Use this whenever you touch the map.

## Standing rules (see personal/rivalia/NOTES.md)
- The reverse map's user-facing UI is **English**. Don't reintroduce Italian UI strings.
- The PK/relationship crawl filters to **World == Aeternum** (Andrea's world). Don't
  confuse this with the "Legacy" *rate set* (that's about rates, not the world value).

## Regenerating & publishing the map
The full runbook (quick "map-only" update, full weekly PK refresh, the pipeline, the
pathfinder rules, gotchas) lives in the **`rivalia-map`** skill — that's the single
source of truth, don't duplicate it here. Quick reference only:
```bash
cd personal/rivalia && python3 build_insights.py && INLINE=1 python3 build_html.py
# then commit map/index.html and push origin main → GitHub Pages republishes
```

## Conventions
- All Rivalia sources/output live in `personal/rivalia/`; the only published file is
  `map/index.html`.
- Verify HTML visually with headless Chromium at `/opt/pw-browsers/chromium` if needed.
