# Rivalia — Operational Notes

Migrated from the work-PC AgentSpaces "memory" store (28 Aug 2026). These are
standing rules for the Rivalia pipeline. See also `.claude/skills/rivalia/SKILL.md`.

## 1. Reverse map UI is ENGLISH (standing instruction, 28 Aug 2026)

The Rivalia reverse-hunt map (`build_html.py` → `map/index.html`, published via
GitHub Pages) is kept in **English** for all user-facing text.

**Why:** Andrea's explicit standing instruction — "questa mappa da ora in poi la
teniamo in inglese".

**How to apply:** All user-facing text in the map — buttons, sidebar section labels
(PLAYER / HUNT / NPC / MAP), tooltips (`title=`), modal titles/tabs/notes,
placeholders, legend, scanner, verdicts (FARMABLE / RISKY / LETHAL), Insights tabs,
PK table, relations graph, NPC directory, map popups, pathfinder — must be in English.
Any NEW feature (e.g. a Task Helper) must be authored in English from the start; do NOT
reintroduce Italian UI strings. Code comments, variable names, and game DATA
(creature/city/player/guild names) stay as-is. The `rivalia` skill's own guidance and
Andrea's chat remain Italian — this rule is only about the map's rendered UI.

## 2. PK / relationship crawl filters to World == Aeternum

Andrea's Rivalia character is on world **Aeternum** (confirmed 27 Aug 2026 — the
profile `World` field). The `characterprofile.php` crawl pulls in **three distinct
worlds** — Aeternum (~1650 profiles), Legacy (~290), Ascendia (~160), plus ~130
unknown — because `onlinelist.php` / `deaths.php` are world-agnostic and the recursive
crawl follows killer/victim names across worlds. Character names are globally unique on
Rivalia and PvP is intra-world, so foreign-world subgraphs detach cleanly when filtered.

**Rule:** `build_pkdata.py` and `build_relationships.py` filter to `World==Aeternum`
(env `PK_WORLD_FILTER`, default Aeternum): keep only in-world victims, and include a
referenced killer only if it's in-world or its world is unknown. Without this, foreign
players (e.g. Toni Kross, Ascendia Master Sorcerer lvl 326) contaminate the graphs.
Bug found + fixed 27 Aug 2026.

⚠️ **World vs rate-set:** the skill CONTESTO says Andrea plays the "**Legacy** 1x"
*rate set*. That is about rates / skill-training advice, NOT the profile world value —
his profile world is **Aeternum**. Don't conflate the two; don't delete the Legacy-rate
content when correcting world references.
