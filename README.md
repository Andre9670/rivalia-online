# rivalia-online

Personal tooling and knowledge base for **Andrea's Paladin on [Rivalia Online](https://rivaliaonline.com/)**
— a custom Tibia 7.4 private server (Legacy 1x rate set, world *Aeternum*).

Hobby project. Everything is self-contained in this repo — no external systems.

## What's published

The headline deliverable is an interactive **Reverse Hunt Map** served via **GitHub Pages**:

- **`map/index.html`** — self-contained (base64-inlined) build of the reverse map:
  zone → creatures, floor overlays, mouse scanner, stats panel, an A* "how do I get
  there" pathfinder, and modals for Insights (loot-value / quests / farming / hunt areas),
  the **PK map** (who-kills-who on Aeternum), player **relationships**, and an NPC directory.

## Repo layout

```
map/index.html              # published reverse map (GitHub Pages) — generated, committed
.nojekyll                   # serve files as-is on Pages
.claude/skills/rivalia/     # the "rivalia" skill: strategy guide + TibiaWiki 7.4 references
  SKILL.md                  #   Paladin strategy, combat formulas, char state, sources
  references/               #   22 routes, 79 quests, 105 hunting-places (+ route images)
personal/rivalia/           # the pipeline: build scripts, scraped data, source assets
  build_*.py, scrape_*.py   #   generators (see "Regenerating the map" below)
  *.json                    #   real Rivalia data (catalog-stats, hunt-spots, pk-map, walk-grid…)
  creatures/ minimap/ …     #   sprite/tile/image assets used by the build
  cron/                     #   weekly PK-map refresh script + schedule record
  NOTES.md                  #   standing operational rules (UI language, world filter)
```

## Regenerating the map

From the repo root:

```bash
cd personal/rivalia
python3 build_insights.py            # rebuild insights-data.json from real data
INLINE=1 python3 build_html.py       # writes ../../map/index.html (self-contained)
```

Then commit `map/index.html` and push — GitHub Pages republishes automatically.

For a lighter local-only build (external sprites, faster to open) run
`python3 build_html.py` without `INLINE=1`; it writes `rivalia-reverse-map.html`
(git-ignored) and needs the `creatures/` folder alongside.

## Weekly PK-map refresh

`personal/rivalia/cron/pk-map-refresh.sh` runs the full scrape → build → **git push**
pipeline (public scraping of rivaliaonline.com; no auth). It's meant to run as a weekly
Claude Routine (Mon ~08:30 UTC); `cron/registry-entry.json` records the schedule.

## Notes

- All numbers about the game are **custom Rivalia values**, not Tibia 7.4 vanilla — see
  `.claude/skills/rivalia/SKILL.md` for why and for the authoritative sources
  (`wiki.rivaliaonline.com`).
- The map UI is kept in **English**; the skill guidance and dev notes are in Italian.
  See `personal/rivalia/NOTES.md`.
