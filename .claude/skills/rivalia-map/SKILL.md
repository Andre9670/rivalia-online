---
name: rivalia-map
description: Operational runbook (single source of truth) for building, updating and PUBLISHING the Rivalia Online interactive reverse-hunt map (personal repo Andre9670/rivalia-online → GitHub Pages at map/index.html). Use whenever Andrea wants to rebuild/regenerate/refresh/republish the map, run the scrape→build pipeline, refresh the PK/relationship graph, work on the pathfinder / walkability grid, or debug the map build. Triggers on "aggiorna la mappa", "rebuild/regenerate the map", "ripubblica", "reverse map", "PK map refresh", "pathfinder", "walkgrid". For in-game advice (monster stats, spots, strategy) use the separate "rivalia" skill instead.
---

# Rivalia Reverse Map — Build & Publish Runbook

Unica fonte di verità per **costruire e pubblicare** la reverse map. Per i consigli di gioco → skill `rivalia`. Nessun overlap: qui stanno solo le operazioni.

Repo: `Andre9670/rivalia-online`. Sorgenti in `personal/rivalia/`. Deliverable pubblicato: **`map/index.html`** (radice repo), servito via **GitHub Pages** a https://andre9670.github.io/rivalia-online/map/ (il root `/` redirige a `/map/`).

## ⚠️ REGOLE VINCOLANTI (non violarle)
1. **La UI della mappa è in INGLESE.** Ogni testo user-facing (bottoni, label sidebar PLAYER/HUNT/NPC/MAP, tooltip `title=`, titoli/tab/note dei modal, placeholder, legenda, scanner, verdetti FARMABLE/RISKY/LETHAL, tab Insights, tabella PK, grafo relazioni, directory NPC, popup, pathfinder) deve essere in inglese. Feature NUOVE si scrivono in inglese da subito. Commenti/variabili/nomi-di-gioco restano come sono. (Standing instruction di Andrea, 28 ago 2026 — vedi `personal/rivalia/NOTES.md`.)
2. **Il crawl PK/relazioni filtra a `World==Aeternum`** (il mondo di Andrea). `build_pkdata.py` e `build_relationships.py` usano l'env `PK_WORLD_FILTER` (default Aeternum). NON aggirare/disabilitare il filtro: senza, entrano player di altri mondi (Legacy/Ascendia) e sporcano i grafi. NON confondere "World Aeternum" col "rate set Legacy" (cose diverse). Vedi `NOTES.md`.
3. **Solo `INLINE=1` produce il file pubblicabile.** La build self-contained (base64) è l'unica che funziona come singolo file su GitHub Pages.
4. **Pubblicare = commit+push di `map/index.html` su `main`.** Niente OneDrive/S3/Midway (roba del vecchio setup PC-lavoro, rimossa).

## AGGIORNAMENTO RAPIDO "solo mappa" (dati di gioco invariati)
Dalla radice repo:
```bash
cd personal/rivalia
python3 build_insights.py          # rigenera insights-data.json (loot/quest/farm/hunt-areas dai dati reali)
INLINE=1 python3 build_html.py     # build self-contained → scrive ../../map/index.html
cd ../.. && git add map/index.html personal/rivalia/insights-data.json
git commit -m "Update Rivalia Reverse Hunt Map" && git push origin main
```
GitHub Pages ripubblica da solo in ~1 min (link stabile).

> Build "esterna" leggera per test locali: `python3 build_html.py` senza `INLINE` → scrive `rivalia-reverse-map.html` (git-ignored, sprite serviti da `creatures/`). NON pubblicare questa.

## REFRESH COMPLETO PK-MAP (settimanale)
Rigenera anche il grafo PK/relazioni ri-scrapando `rivaliaonline.com` (pubblico, no auth). Script canonico:
```bash
bash personal/rivalia/cron/pk-map-refresh.sh
```
Pipeline: `build_seed.py` → `crawl_pk.py` → `build_pkdata.py` → `build_relationships.py` → `build_insights.py` → `INLINE=1 build_html.py` → `git add/commit/push`. Log in `personal/rivalia/cron-pk-map-refresh.log`. Se il build fallisce (rete/parse), lo script NON pubblica e tiene la mappa precedente.

**Automazione:** gira come **Claude Routine settimanale** (lunedì ~08:30 UTC, id `trig_019Vd9G93SoP16tWmhTh9e3E`, sessione fresca che fa push su `main`). `personal/rivalia/cron/registry-entry.json` tiene traccia dello schedule.

## PIPELINE — ruolo di ogni script (in personal/rivalia/)
- **`build_seed.py`** → seed player da highscores (Aeternum).
- **`crawl_pk.py`** → crawl ricorsivo dei profili fino a chiusura (`/tmp/pk_profiles.json`).
- **`build_pkdata.py`** → grafo who-kills-who + danger score → `pk-map-data.json` (filtra Aeternum).
- **`build_relationships.py`** → grafo alleati/nemici/co-fazione → `relationships.json` (filtra Aeternum).
- **`build_insights.py`** → `insights-data.json` (loot-value, quest fattibili, farming, hunt areas). Contiene il blocco `CHAR` (stat del PG di Andrea) editabile in cima.
- **`build_chests.py`** → `chests.json` + questline da rivaliaonline.com.
- **`build_npcs.py`** → `npcs.json` (directory NPC; opzionale, non nel cron settimanale).
- **`build_pathdata.py`** → `pathdata-grid.json` + `pathdata-trans.json` (walkgrid + transizioni A*, inlinati nell'HTML).
- **`build_html.py`** → assembla tutto nel singolo HTML. `INLINE=1` = base64 self-contained → `map/index.html`.

Dati di input principali (già presenti, real Rivalia): `map-data.json`, `img-b64.json`, `stats-all.json`, `catalog-stats.json`, `hunt-spots.json`, `creatures/_index.json` (+ sprite), `minimap/` (tiles). Immagini rotte: `.claude/skills/rivalia/references/routes/images/` (risolte relative dallo script).

## FUNZIONALITÀ DELLA MAPPA (cosa contiene)
- **Pannello "My PG" in cima:** Solo/Duo/Trio (1-3 PG), default = stat reali di Andrea in `CHAR_DEF`, salvato in localStorage. Tutti gli insight ripartono da qui (`refreshAll`→`buildDanger`).
- **Insights (modal, 5 tab):** Hunt areas · Loot-value (droppers cliccabili → highlight sulla mappa, pallino farmabilità 🟢🟡🔴 dal PG) · Quests (Fandom 79 / Questline Rivalia 5 / Chest 222) · Where to farm · Routes (14 walkthrough + immagini annotate).
- **Verdetto farmabilità:** motore `assess()` (FARMABLE/RISKY/LETHAL) dal PG, riusato ovunque.
- **Modal PK map** (☠️) e **Relationships** — dai grafi Aeternum.
- **Layer toggle sulla mappa:** 🎯 Hunt areas · 🏰 Cities (13 landmark) · 🎁 Chests (222 geolocalizzate).

## PATHFINDER "come ci arrivo" — walkability (GROUND TRUTH di Andrea, non cambiare a caso)
A* 3D multi-piano su walk-grid + transizioni (`build_pathdata.py` → `pathdata-grid.json` + `pathdata-trans.json`).
- **`block=1`**: 1 pixel minimap = 1 cella di gioco (trasformata 1:1). NIENTE downsampling — il vecchio `block=4` spezzava i corridoi. Rigen ~20s.
- **Grigio scuro `(102,102,102)` = SEMPRE muro, su TUTTI i piani** (montagna in superficie, roccia/parete sottoterra). NON reintrodurlo tra i walkable. Grigio chiaro `(153,153,153)` = pavimento calpestabile.
- **Transizioni yellow↔yellow**: un puntino giallo è passaggio valido se il piano adiacente ha un giallo allineato (non serve sia calpestabile) → recupera buchi shovel/rope (+~590 transizioni, +55%).
- **Danger-weighting**: costo A* extra sui tile vicino a mob 🔴 letali PER IL PG (toggle "Avoid lethal mobs"). Solo additivo, non rompe percorsi.
- **Limiti onesti residui:** copertura minimap sparsa in profondità (pozze isolate → "no path"); passaggi action-gated (shovel/leva/parcels/barca) esistono nel grid ma richiedono l'azione in-game.

## FORMULA COORDINATE → PIXEL MAPPA
Dal sito: `px = x − 31744`, `py = y − 30701`. Immagini piano 1685×2827. In Leaflet CRS.Simple va flippato: `lat = IMGH − py`.

## VERIFICA VISIVA
Controlla l'HTML con Chromium headless (in questo ambiente: `/opt/pw-browsers/chromium`) o Playwright se serve un check visivo prima di pubblicare.
