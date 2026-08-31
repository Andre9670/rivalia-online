# Pathfinder Lessons

What these hand-written route walkthroughs reveal that a naive A* over the tile grid would miss. Grouped/prefixed by route.

## mainland-trails
- **mainland-trails:** The overland "trails" are a curated safe-corridor network, NOT the shortest tile path. A* would cut straight across wilds; the wiki route deliberately follows yellow roads because off-road spawns escalate (Dragon at Venore lair, Orc Berserker/Leader near Orc Fortress). Cost function must weight monster-density, not just distance.
- **mainland-trails:** Water is a hard barrier with NO land path — the NW archipelago (Folda, Senja, Vega, Ghostlands, Isle of the Kings) is boat-only (red lines). A grid A* sees ocean as impassable and returns "no path"; the real graph needs explicit boat/travel EDGES between port nodes to connect these islands at all.
- **mainland-trails:** Short ferry hops (cyan: Thais→Fibula, Kazordoon A↔B) are teleport-like edges that bypass a huge overland detour. These are named-NPC/boat transitions the map author knows but a tile-walker cannot infer — model them as zero-length travel edges.
- **mainland-trails:** The text encodes a risk policy A* has no notion of: "stay on the paths EXCEPT Thais–Venore and Kazordoon–Carlin." Two specific legs are safe to shortcut; everywhere else the road detour is mandatory. That's per-edge human knowledge, not geometry.

## thaian-venorean-road
- **thaian-venorean-road:** The road goes deliberately UP and over Mount Sternum (a peak) rather than around it — a distance-only A* would route around the mountain along flatter tiles; the actual walkable road climbs the pass because that's where the bridge/traversable terrain is. Elevation/terrain-walkability matters more than 2D distance.
- **thaian-venorean-road:** The route hugs the NORTH edge of the Jakundaf Desert rather than crossing it. A* on open sand would happily cut through the middle; the human route treats desert interior as high-exposure and skirts it. Again a soft cost, not a wall.
- **thaian-venorean-road:** River crossings only happen at specific bridge tiles. A straight-line planner would try to cross anywhere the river is narrow; the real graph only connects the two banks at the one bridge — chokepoints must be explicit edges.

## route-edron-bog-raider-cave
- **route-edron-bog-raider-cave:** This is a 3D descent through 5 stacked floors (z7→z11) connected only by specific hole/descent tiles. A 2D A* is useless here — pathfinding must be multi-floor with z-transitions keyed to exact hole coordinates, and each hole is one-way-ish (need a Rope to climb back).
- **route-edron-bog-raider-cave:** The maze panels are non-convex (spiral, snaking corridors) where the descent hole is often at the FAR end of a coil, i.e. you must walk AWAY from the goal's straight-line direction to progress. A greedy/heuristic A* biased toward the goal bearing would thrash; the walls force a counter-intuitive path only the map reveals.
- **route-edron-bog-raider-cave:** The entrance is a surface hole at fixed coords (130.22/124.43 z7) with no signposting — the "start" is a point you'd never find by tile search from the destination. Route knowledge = knowing the entry hole location, which A* cannot discover without the annotated map.

## route-hellgate
- **route-hellgate:** Deep dungeon with ~10 alternating up/down transitions where the CORRECT hole among several is route-critical — "go down the FIRST hole" / "not the second roping spot (poison spiders)". A* has no way to know which of two adjacent holes is the safe/correct one; this is per-hole human knowledge.
- **route-hellgate:** Vertical progress needs CONSUMABLES the grid doesn't model: "6 Parcels or Levitate to climb up 2 floors". Some transitions aren't ladders/holes at all — they require items/spells, i.e. conditional edges.
- **route-hellgate:** A SWITCH must be pulled to open a bridge one floor up before the path exists — the graph is stateful (an edge only opens after an action elsewhere), which pure A* over a static grid cannot represent.

## route-demona
- **route-demona:** The entry hole must be DUG open with a Shovel (coord ~127.0/123.136/7) — the transition literally doesn't exist on the tile grid until an action creates it. Same class as Hellgate's switch: action-gated edges.
- **route-demona:** A SWITCH behind trees (turn RIGHT) opens the MoLS entrance — another stateful, off-path action gating the main route.
- **route-demona:** Inside the MoLS straying off the blue line = Dragons/Dragon Lords/Giant Spiders. The safe path is deliberately NOT the shortest; monster-danger is the dominant cost, and the maze is non-convex so greedy heuristics thrash.

## route-femor-hills
- **route-femor-hills:** This is a spawn/escape MAP, not a single route — the same x/y stacks 4 floors (z5 top .. z8 underground) linked by numbered up/down markers. Confirms transitions must be keyed to exact marker tiles; danger escalates with depth/height (Hunters + Demon Skeletons on the TOP level, not the bottom), inverting the usual "deeper = harder" assumption.
