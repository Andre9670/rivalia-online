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

## 3. Wiki rescan 13 Oct 2026

Full rescan of rivaliaonline.com/wiki.php (creatures 214, spells 80, zones 164, raids 35, systems pages).
Summary + findings in `.claude/skills/rivalia/references/WIKI-RESCAN-2026-10.md`; structured dumps in
`personal/rivalia/wiki-2026-10/`. `catalog-stats.json` updated (loot lists were truncated; 2 stat changes; 3 new bosses
Ignaroth/Zatharak/Zyphera). New: Destiny PvP world (launched 5 Oct 2026), Rarity Upgrade replaces old Aethernite model.
Not rescanned: per-category item pages (`items.php?...`), Hunt Finder map, per-quest details.

## 4. Andrea's current character (13 Oct 2026, from skills screenshot)
Paladin, world Aeternum: Level 62, HP 725, Mana 845 (max; the 218 in the skills screenshot was current mana), Magic Level 15, Distance 79, Shielding 62, Melee 19, Fist 32, Fishing 30, Capacity 1441, Speed 171 base, 206 equipped.
Map defaults (`CHAR_DEF` in build_html.py, `CHAR` in build_insights.py) updated. With the crossbow (two-handed): Armor 34, Defense 0 (no shield), Speed 206 (171 +35), Attack 30, Atk interval 2s, Crit +1%/+10%. Second setup: shield (Dragon Shield) + Royal Spears = Attack 34, Armor 34, Defense 31, Speed 206. Map default = this shield + Royal Spear setup (weapAtk 34, shieldDef 31); the crossbow setup is Attack 30 / Defense 0.
Note: the map stores edited PG stats in browser localStorage (`rivalia_party`), which overrides these defaults on a browser that already saved values.

## 5. Map farmability engine (build_html.py `runAssess`) — rules as of 13 Oct 2026
One general model for every monster, driven by monster stats + the PG (no per-monster overrides):
- Damage per turn = sum of EXPECTED damage: melee scaled by `meleeExposure(monSpeed/mySpeed)` (r>=0.9 -> 100%; else 0.05+0.95*(r/0.9)^6, +0.30 if the monster paralyzes),
  melee/physical reduced by armor + shield block; physical ranged attacks hit EVERY turn (armor + block reduce them); elemental/drain spells fire with chance `SPELL_P`=35%/turn (Andrea: distance always hits, elementals ~35% on dragons).
- Survival budget = HP + (max mana / healMana) * healAmt (Exura Vita: 370 HP / 80 mana). Score = 100 - pressure*60 - fight-length penalty (>20s, up to -20). FARMABLE >= 75 (`FARM_MIN`, raised from 70 on 13 Oct 2026), RISKY >= 40, else LETHAL.
- NOT modeled: several monsters at once, summons, conditions other than paralyze, mana drain effect, potions/rings. Heuristics to tune: SPELL_P, meleeExposure shape, penalty.

## 6. GitBook refreshed 13 Oct 2026 (rivalia-online.gitbook.io)
`personal/rivalia/llms-full.txt` re-exported (91 KB -> 114 KB; new: Mining, Alchemy, Crafting, Guild Management, Artifacts, Food/Equipment item pages, Elites, Analyzer).
It has NO combat formulas, NO monster attack chances, and the creature pages (Hero, Dragon, Black Knight...) are empty; item pages list only weight/possible attributes (no Defense/Armor values).
Useful bits: Monster Elites (2% chance the next spawn is a 1-3 star elite: more HP/damage/armor/speed), item attributes (Defense / Shielding / Armor / Dodge / Hit Chance, tiers 1-5), Edron Heroes custom spawn ("Recommended: 50+").

## 7. Paladin loadout toggle (map, "My character" panel)
Two buttons for paladins: "Shield + spears" (Attack 34, Shield def 31) and "Crossbow / bow" (Attack 30, Shield def 0 — two-handed, no shield). Defined in `PAL_SETUPS` (build_html.py).
Armor 34 and Speed 206 are the same in both setups (Combat Stats screenshots, 13 Oct 2026). The fields stay editable; the active button is derived from Shield def (>0 = spears).

## 8. Paladin loadout: Auto per monster (default)
`loadout:'auto'` (CHAR_DEF): for each monster the engine picks the setup. The shield only absorbs PHYSICAL damage, so: if >= 40% of the expected damage is physical
(melee that reaches me + physical ranged, e.g. Hero, Black Knight) -> shield + spears (Attack 34, def 31); otherwise (mostly elemental/spells, e.g. Dragon) -> crossbow (Attack 30, def 0).
The verdict note says which loadout was used. Buttons: Auto / Shield + spears / Crossbow-bow force a setup; typing Attack or Shield def by hand switches to 'manual'.
Split today: 124 monsters pick spears, 91 pick crossbow. Threshold `PHYS_SHARE_SPEARS` = 0.4 (heuristic).
