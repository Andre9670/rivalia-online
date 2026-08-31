# Piano — feature "HOW TO GET THERE" (pathfinding cross-piano)

_Rivalia reverse map. Data: 2026-07-07. Personale._

## ✅ STATO: SHIPPATO + CORRETTO (2026-07-07)
Feature live su OneDrive. Parametri FINALI:
- **block=1 (per-tile)**: 1 nodo = 1 tile di gioco (la minimap è 1px=1tile). Massima precisione E
  sicurezza: un muro è semplicemente un tile non-walkable → impossibile attraversarlo, ZERO aggregazione.
- **A* 3D** con **binary heap** (necessario: ~870k nodi/piano), diagonali + no-corner-cutting,
  transizioni gialle validate cross-piano (costo 3). Chiave numerica compatta fl*W*H+y*W+x.
- Perf: rotta di 1060 passi su floor7 in **~174ms**. Componente principale floor7 = 406k tile.
- Asset: `pathdata-grid.json` (RLE per-riga, 1.4MB) + `pathdata-trans.json` (1814 transizioni, 27KB).
  Generati da `build_pathdata_b1.py`. File OneDrive inline ~5.5MB (ok).
- UI: bottone "🧭 Come ci arrivo" → click partenza + destinazione → traccia + step + ⬆/⬇.

### Storia decisionale (perché block=1)
- Tentativo 1: block=8 → verifica avversariale bocciata (488 muri + 407 lava attraversati: A* centro-a-centro tagliava dentro i blocchi).
- Tentativo 2: block=4 + 100%-walkable → 0 muri (verificato, 460 rotte) MA **troppe micro-isole**:
  una strada larga 3 tile non riempie un blocco 4×4 → sparisce dal grafo → "nessun percorso" per
  strade visibilmente connesse (segnalato dall'utente sul campo).
- Tentativo 3 (FINALE): **block=1** → risolve entrambi. A risoluzione piena non c'è aggregazione,
  quindi né tagli-muro né strade perse. Costo: grid più pesante + serve heap per la performance.

### Limite residuo (onesto)
Minimap con copertura sparsa in profondità → alcune zone profonde restano genuinamente
scollegate (void non mappato). Lì "nessun percorso" è corretto. Non inventiamo rotte.

## Obiettivo
Punti un target sulla mappa → la mappa calcola e disegna **come arrivarci**: un percorso che
cammina sui tile calpestabili di un piano e **cambia piano** alle transizioni (corda/scala = su,
buco/shovel = giù), senza attraversare muri. Output: traccia disegnata + step testuali
("vai a X, sali con la corda, prosegui, scendi nel buco a Y").

## Vincoli / fatti verificati (2026-07-07)
- **Nessun dato di transizione disponibile** in `map-data.json` / `hunt-spots.json`. Vanno DERIVATI.
- Le minimap sono **1 pixel = 1 tile** (coord→pixel: `px=x−31744`, `py=y−30701`; 16 piani allineati).
- Colori chiave minimap (RGB): void/muro `(51,0,204)`, acqua-ish scuri, pavimenti = verde
  `(0,204,0)/(0,102,0)`, sabbia `(255,204,153)`, grigio `(102,102,102)/(153,153,153)`,
  **giallo transizione `(255,255,0)`**.
- Il giallo grezzo è **rumoroso**: ~1500 cluster/piano → non tutti sono scale (decoro incluso).
  Va **validato** incrociando i piani.
- Il file è un HTML monolitico (~4MB inline per OneDrive). Attenzione al peso e alla performance:
  16 piani × 1685×2827 ≈ 76M tile → **A* full-res live NON è fattibile** nel browser.

## Decisione di design (approvata)
Estraggo il giallo dalle minimap + filtro; incrocio pixel sopra/sotto; traccio percorso su tile
calpestabili muovendomi tra i piani. → **serve una pipeline offline (Python, build-time)** che
produce i dati, e un **A* a griglia ridotta** a runtime.

---

## FASE 0 — Estrazione dati (offline, Python, in `build_html.py` o script dedicato)

### 0a. Walkability per piano
Per ogni `floor-N.png`, classifica ogni pixel:
- **walkable** = pavimenti (verde/sabbia/grigio/marrone entro tolleranza colore)
- **blocked** = void `(51,0,204)`, acqua, nero, bordo
Output: bitmap di walkability per piano (bit-packed o RLE per stare leggeri).

### 0b. Candidati transizione (giallo)
Estrai pixel `(255,255,0)`, clusterizza (grid 3–4px o connected-components).
Ogni cluster = candidato `{x,y,floor}`.

### 0c. VALIDAZIONE cross-piano (il cuore)
Un candidato su piano N è una **transizione reale** se:
- **UP** (corda/scala su → piano N−1, indice più piccolo): il tile corrispondente su N−1 è walkable.
- **DOWN** (buco/shovel giù → piano N+1, indice più grande): il tile su N+1 è walkable.
- Scarta i gialli isolati senza pavimento adiacente sullo stesso piano (probabile decoro).
- Marca `type: up|down|both` e i due piani collegati.
Output: **`transitions.json`** = `[{x,y,floorFrom,floorTo,type}]`.
→ Questo è l'asset fondante; se resta rumoroso, iterare i filtri qui (soglie colore, dimensione
cluster minima, richiesta di pavimento su ENTRAMBI i lati).

### 0d. Griglia ridotta per il pathfinding
Downsample walkability a blocchi (es. 4×4 o 8×8 px → 1 nodo). Un blocco è walkable se
≥X% dei suoi pixel lo sono. Riduce 76M → ~1–5M nodi (tractabile). Le transizioni si agganciano
al nodo-blocco che le contiene. Risoluzione = parametro tarabile (precisione vs performance).

Output FASE 0: `walk-grid.json` (bitmap ridotte per piano) + `transitions.json`.
Entrambi inline nell'HTML (come già facciamo per sprite/tile).

## FASE 1 — Motore di pathfinding (JS a runtime)
- Grafo 3D: nodi = blocchi walkable; archi = 4/8-vicini sullo stesso piano (costo passo) +
  **archi-transizione** N↔N±1 ai punti validati (costo extra = "usa corda/scala/buco").
- **A*** con euristica = distanza 3D (Manhattan sul piano + penalità cambio-piano).
- Start: posizione cursore o "imposta partenza" con click. Target: click destinazione.
- Ritorna: sequenza di nodi + i punti-transizione attraversati (con tipo up/down).

## FASE 2 — UI
- Nuovo modo "🧭 Come ci arrivo": clicchi partenza (o usa il punto corrente) e destinazione.
- **Traccia disegnata** sulla mappa (polyline per-piano; ai cambi-piano un marker "⬆ corda / ⬇ buco").
- **Auto-follow**: seguendo il percorso, la mappa cambia piano da sola al passaggio.
- **Step testuali**: "Piano 7: vai a est → ⬆ scala → Piano 6: prosegui a nord → ⬇ buco → …".
- Fallback onesto: se non trova un percorso (dati transizione incompleti), lo dice chiaramente
  e mostra le **transizioni più vicine al target** come ripiego (non fingere una rotta che non c'è).

## FASE 3 — Verifica + publish
- Verifica headless (Chromium): estrazione produce transizioni sensate su un'area nota;
  A* trova un percorso plausibile; zero errori JS.
- Spot-check visivo su 2–3 rotte reali che conosci.
- Rebuild esterna + inline, publish su OneDrive.

---

## Rischi & mitigazioni
1. **Giallo rumoroso** → falsi positivi/negativi sulle scale. Mitigo con la validazione cross-piano
   (0c) e soglie tarabili; se troppo sporco, ripiego su "transizioni più vicine" invece della rotta.
2. **Performance** → griglia ridotta (0d) + A* con limite di nodi; se un piano è enorme, cap sul
   raggio di ricerca.
3. **Peso file** → walk-grid compressa (RLE/bit-pack); se pesa troppo, la carico solo on-demand
   nella versione "hosting" e la tengo inline solo dove serve.
4. **Accuratezza walkability** → i colori minimap sono un'approssimazione (un pavimento con muro
   invisibile non si distingue). Onestà: il percorso è una **guida**, non garanzia pixel-perfetta.

## Ordine di lavoro consigliato (incrementale, verifico ad ogni step)
1. FASE 0a+0b+0c su UN'area piccola nota → guardo `transitions.json`, taro i filtri.
2. FASE 0d + A* su quella stessa area (2 piani) → verifico che trovi il passaggio.
3. Estendo a tutti i piani.
4. UI (traccia + step + auto-follow).
5. Verifica + publish.

## Feature collaterale (già approvata, quick win separato)
Toggle **"🎯 Verdetto zona"** accanto allo scanner: attivo → muovendo il mouse vedi lo score-zona
live (usa `renderZoneVerdict`, già scritto ma oggi non attivabile dall'UI). Da fare subito,
indipendente dal pathfinding.
