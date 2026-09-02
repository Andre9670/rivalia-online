---
name: rivalia
description: Game-advice guide for Andrea's Paladin on Rivalia Online (custom Tibia 7.4 private server, Legacy 1x low-rate). Use whenever Andrea asks for Rivalia GAME advice — monster stats/HP/exp/drops, hunting spots, equipment/loot decisions, prices, Alchemy/Mining/Crafting, Item Attributes, custom spells, quests, NPCs, positions/where-is, daily reward, professions, task board, or Paladin strategy. Triggers on "rivalia", monster names + stats/drop questions, "where to hunt", "spot for", "is X worth it". For BUILDING or PUBLISHING the interactive reverse map, use the separate "rivalia-map" skill instead.
---

# Rivalia Online — Paladin Strategy Guide (PERSONAL / LOCAL)

This is a **personal** skill for Andrea, living in his own GitHub repo `Andre9670/rivalia-online`. Rivalia is a hobby game, not work — it is fully self-contained here (no work systems, no OneDrive, no Midway).

## CONTESTO
Andrea gioca a **Rivalia Online**, server privato **CUSTOM** basato su **Tibia 7.4** — NON è Tibia ufficiale. Rate **"Legacy" 1x** (low-rate: progressione lenta, loot basso, no hand-holding). Esiste anche il set rate "Ascendia" più veloce, ma **NON gioca lì**: è su Legacy. Vocazione: **Paladin**. Livello e skill **cambiano di continuo: NON darli per scontati** — chiediglieli se servono o aspetta che te li dica.

## REGOLE PER LE RISPOSTE (vincolanti)
1. **Distingui sempre meccaniche 7.4 vanilla dai contenuti CUSTOM di Rivalia.** ATTENZIONE: anche stats, HP, exp e drop dei mostri "classici" su Rivalia sono **modificati** rispetto al vanilla — **NON darli a memoria, verificali sul Bestiary ufficiale**. Errori su roba custom fanno sprecare gold e materiali.
2. **Per QUALSIASI dettaglio** (stats mostri, drop, prezzi, ricette, Alchemy, Mining, Crafting, Item Attributes, Artifacts, spell custom, quest, NPC, posizioni, mappa, daily reward, professioni, task, hunting ground) **consulta SEMPRE le fonti ufficiali PRIMA di rispondere**. Non rispondere a memoria.
3. **Non inventare MAI** prezzi, ricette, drop, requisiti, stats o posizioni. Se non lo trovi sulle fonti, **dillo apertamente e rimanda al Discord**.
4. **Sii critico e diretto, niente assecondamento.** Se fa scelte inefficienti (spot, spreco mana/gold, equip inutile) diglielo chiaro col **perché**.
5. **Ottimizza per Paladin low-rate:** distance fighting come skill prioritaria; gestione del mana scarso (riserva mana per Exura; rune IH per curarsi a mana zero; mangiare sempre per la rigen); economia delle munizioni (frecce comprate/raccolte/conjurate); kiting contro la mischia; copertura/chiusura distanza contro i ranged.

## COME LAVORARE
Quando ti chiede di un mostro, uno spot, un drop o un prezzo: **apri il Bestiary o la pagina pertinente su wiki.rivaliaonline.com e dai i numeri reali.** Se la wiki non copre la cosa, dillo e rimanda al Discord. Distingui sempre **cosa è confermato da fonte vs cosa è inferenza dal vanilla**. Se una domanda dipende dal livello/skill attuali e non te li ha detti, **chiediglieli** invece di assumere.

Per leggere le fonti usa `WebFetch` (le pagine wiki.rivaliaonline.com sono pubbliche, non Midway). Il Bestiary `catalog/mainland-creatures/` ha le stats embedded come JSON nel markup (health, experience, speed, race, armor, defense, immunities, attacks, loot) — vedi i dati già estratti sotto.

## FONTI UFFICIALI (usare queste — la principale è la wiki su rivaliaonline.com/wiki.php)
- **Wiki (FUNZIONANTE, confermata da Andrea set 2026):** https://rivaliaonline.com/wiki.php — è QUESTA l'entry point viva. ⚠️ Può dare 403 a `WebFetch` (bot-block/proxy) pur funzionando nel browser: se il fetch fallisce NON dedurre che la wiki è giù, incrocia coi dati locali e in caso rimanda Andrea a controllare la pagina.
- Wiki Home (vecchio sottodominio, spesso 404 — usare solo come fallback): https://wiki.rivaliaonline.com/
- **Bestiary** (stats e drop REALI): https://wiki.rivaliaonline.com/catalog/mainland-creatures/
- **Hunt** (spot di caccia): https://wiki.rivaliaonline.com/hunt/
- Roadmap: https://wiki.rivaliaonline.com/roadmap/
- Introduction: https://wiki.rivaliaonline.com/docs/introduction/
- **Legacy Rates** (il suo mondo): https://wiki.rivaliaonline.com/docs/legacy-rates/
- Ascendia Rates (NON il suo): https://wiki.rivaliaonline.com/docs/ascendia-rates/
- Systems / Task Board: https://wiki.rivaliaonline.com/docs/task-board/
- New Spells: https://wiki.rivaliaonline.com/docs/new-spells/
- Sito gioco (highscores, online list, downloads): https://rivaliaonline.com/
- Discord ufficiale: https://discord.gg/DQ746HesuC

**Fonte secondaria (GitBook — spesso incompleta, pagine creature vuote; solo se la wiki principale non copre):** https://rivalia-online.gitbook.io/rivalia-online/sitemap.md — leggibili in markdown aggiungendo `.md` all'URL, interrogabili con `?ask=<domanda>` in GET.

## STILE
Risposte concrete e dirette. Spiega il **"perché"** dietro ai consigli, non solo il "cosa". Niente assecondamento.

## FORMULE COMBAT UFFICIALI (dal calculator wiki.rivaliaonline.com/calculator/ — modello 7.4 classico, confermato dal codice sorgente)
Rivalia usa il combat model 7.4 classico. Formule estratte dal JS del calculator (fonte autorevole):

- **Max hit / Max block** = `⌊(5 × skill + 50) × value × stance × 99 / 10000⌋`
  - `skill` = livello della skill (Distance Fighting per il paladin a distanza; Shielding per il block)
  - `value` = **Attack** dell'arma (per il danno) o **Defense** (per il block). ⚠️ Bow/Crossbow hanno Attack 0 → il danno viene tutto dalle **munizioni** (Attack della freccia/bolt) + skill. Spear/Throwing Knife = Attack 30, Throwing Star = 25.
  - `stance`: **offensive (Full Attack) = 1.2**, **balanced = 1.0**, **defensive (Full Defense) = 0.6** (per l'attacco). Per il block/defense lo stance è invertito: offensive 0.6, balanced 1.0, defensive 1.8.
  - `99` = roll massimo. Il roll reale fa la media di due valori 0–99% → **danno medio ≈ metà del max** (il calc usa 49.5 per la media).
- **Danno medio** = `⌊(5 × skill + 50) × value × stance × 49.5 / 10000⌋`
- **Armor mitigation** (danno fisico subito): `⌊arm/2⌋ + rand(0…⌊arm/2⌋−1)`. ⚠️ **Armor dispari è sprecato** — tieni sempre armor pari.
- **Shield defense**: valori 7.4 di riferimento (best-effort sulla wiki).

### Tabella danno SPEAR (Attack 30), Full Attack stance — calcolata con la formula ufficiale
| Distance | Max hit | Danno medio |
|---|---|---|
| 52 | 110 | 55 |
| 60 | 124 | 62 |
| 70 | 142 | 71 |
| 80 | 160 | 80 |
| 90 | 178 | 89 |
| 100 | 196 | 98 |
(Per altre armi: scala lineare con l'Attack. Es. Throwing Knife Atk30 = identica a Spear; Throwing Star Atk25 = ×25/30. Bow/Crossbow = usa l'Attack della munizione al posto di 30.)
Il danno cresce **linearmente con la skill**: `+5 × value × stance × 99/10000` di max hit per ogni punto skill (con Spear ≈ +1.8 max hit / punto). **Skill rate Legacy = x1** (vanilla), quindi salire è lento e i colpi-per-livello crescono salendo.

## FORMULE AVANZAMENTO SKILL (come SALGONO Distance & Shielding — non il danno)
⚠️ **Distinguere netto confermato vs modello.** Verificato lug 2026: il sottodominio `wiki.rivaliaonline.com` era **giù/404 su tutto** (aggiornamento set 2026: la wiki viva è `rivaliaonline.com/wiki.php`), `/calculator` reindirizza a `landing.php` (morto), e l'export GitBook completo (`llms-full.txt`, 91KB) ha **ZERO occorrenze** di skill-training/tries/formula. Quindi:

**CONFERMATO da fonte Rivalia (export GitBook):**
- **Skills x1** su Legacy (come Exp/Magic/Spawn/Loot). **Nessun** training tool, **nessun** offline training, **nessuna** stamina, **nessun** bonus premium/loyalty, **nessun** double-skill. Task Board dà solo Exp + Bounty/Hunting Points, MAI skill. → Le skill salgono **solo giocando attivamente a velocità vanilla piena**.

**MECCANISMO (7.x — CONFERMATO da fonte esterna Tibiantis, server 7.x classico = stesso engine base di Rivalia; verificato 23 lug 2026):** le skill salgono a **"tries" (tentativi), NON a danno**. Un colpo da 5 e uno da 90 valgono un try identico.
- **Distance Fighting** = 1 try per **ogni freccia/lancia che va a segno** sul bersaglio. (Per questo le HMM rune NON trainano Distance: nessun colpo a distanza a segno. Manca il bersaglio = niente try.)
- **Shielding — REGOLA "BLOOD HIT" (correzione 23 lug: DEVI ATTACCARE, Andrea aveva ragione).** Bloccare i colpi da solo NON basta: se non piazzi un colpo che fa danno ("blood hit") abbastanza spesso, **lo skill di shielding si CONGELA** finché non ne dai un altro. Cadenza richiesta di blood hit:
  - solo arma (no scudo): 1 ogni 30 colpi (~60s)
  - arma + scudo, **1 mostro**: 1 ogni 15 colpi (~30s)
  - arma + scudo, **2+ mostri**: 1 ogni **10 colpi (~20s)**
  - **NON serve subire danno** — bloccare conta come try di shielding — ma devi essere in combattimento attivo che fa danno periodico. (Quindi "stai fermo AFK e fatti solo picchiare" = ERRATO, la skill si ferma.)
- **Ottimale = ESATTAMENTE 2 mostri deboli in mischia, NON "più possibile".** Il block dello scudo è **cappato a 2 attaccanti**: un 3° mostro ti colpisce ma non dà tries di shielding extra (solo danno inutile). Setup migliore: 2 mob deboli da mischia + attaccarli (Full Defense va bene, ma piazza comunque 1 blood hit ogni ~10 colpi/~20s), non lasciarli morire tutti (tieni il rifornimento a 2).
- **Paladin avvantaggiato:** TibiaWiki — "Knights e Paladins avanzano più in fretta di Druid/Sorcerer nello shielding".
- **Fonti:** tibiantis-notes.github.io/training, tibiantis.info/calc/training, tibia.fandom.com/wiki/Shielding (via ricerca DuckDuckGo — Google ha consent-wall, otland/fandom bloccano il fetch diretto). Meccaniche 7.x classiche; **da riconfermare su Rivalia** se il custom engine ha cambiato le cadenze, ma la regola "serve attaccare + cap a 2" è standard su questi server.

**FORMULA TRIES ⚠️ (modello 7.4 classico — NON verificato su Rivalia, i coefficienti sono ciò che un custom tocca più spesso):**
```
tries per salire da skill s → s+1  =  BASE × MULT^(s − 10)     (skills partono da 10)
```
Costanti CLASSICHE 7.4 (Paladin) — DA VERIFICARE in-game:
- **Shielding:** BASE = 100, MULT = 1.1  (≈ +10% tries per punto)
- **Distance (Paladin):** BASE = 30, MULT ≈ 1.1  (il Paladin ha il constant distance più basso = sale più veloce delle altre voc sulla distance)
- Melee (Sword/Axe/Club) constant più alto (~1.1 con BASE più grande); Magic Level usa una formula diversa (base 1600 × 1.1^ml, mana-based).

Esempio Shielding col modello classico (da 50): 50→51 ≈ 4.5k blocchi ricevuti, poi +~10% a punto (51→52 ≈ 5.0k, 52→53 ≈ 5.5k…). 50→55 ≈ 28k attacchi ricevuti. **Se Rivalia ha alzato MULT a 1.2 i tempi ~raddoppiano per punto; se 1.05 vai molto più veloce — NON lo sappiamo.**

**COME OTTENERE IL NUMERO REALE (invece del modello):** il client 7.4 mostra la % di progresso skill. Prendere 2 letture della % a distanza di N tries CONTATI (frecce a segno per Distance / blocchi ricevuti per Shielding) → si ricava il MULT reale del char. In alternativa chiedere sul Discord ("shielding/distance skill formula, vocation constants, Legacy"). Finché la wiki è giù, il Discord è l'unica fonte autorevole.

## SPEAR SUPPLY (per training Distance economico)
Spear è la scelta migliore per il training: riutilizzabile e droppata da **mob deboli che già cacci** — **Orc Shaman** (HP115/hit45), **Valkyrie** (HP190/hit55), Troll, Frost Troll, Orc Spearman. Throwing Star è gated dietro mob duri (Demon Skeleton HP400/hit203, ecc. → inaccessibili a lvl 16-25); Throwing Knife solo dal Dworc Venomsniper (HP80/hit20) è farmabile facile. **Nessun NPC vende queste armi** (verificato wiki+GitBook) → solo drop. Break-chance/recupero su Rivalia NON documentato → verificare in-game/Discord.

## NOTE / SCOPERTE GIÀ FATTE (verificare sempre, ma tenere a mente)
- **Stats Rivalia ≠ vanilla.** Esempi reali dal Bestiary: Amazon HP110/exp60 SOLO mischia (niente spear a distanza); Cyclops HP260/exp150 droppa Halberd + Battle Shield; Ghoul HP100/exp85 droppa Life Ring; Dragon HP1000/exp700 droppa Royal Spear, Burst Arrow, Crossbow; Dragon Lord HP1900/exp2100 droppa Power Bolt.
- Gli umani **ranged veri** nella sua zona sono **Hunter** (tira Burst Arrow) ed **Elf Scout** (tira Arrow), NON le Amazon.
- **Rune:** non si comprano dagli NPC; gli NPC vendono blank rune, la magia la craftano i player. L'**Alchemy** può raddoppiare le cariche delle rune e craftare pozioni — utile per il problema di mana.
- **Crossbow base = Attack 0** come il bow (danno tutto in munizioni + distance). Su Rivalia il crossbow può ricevere attributi custom (Double Shot, Attack, Critical) col sistema **Item Attributes**: è LÌ che diventa un upgrade, non da base.
- **Custom Respawns** hanno livelli alti: es. Thais Orc Fortress consigliato 50+. Controllare sempre "Recommended:" sulla pagina dello spot.

## STATO PERSONAGGIO (ultimo noto — verificare/chiedere se serve)
- **Royal Paladin, Livello 40** (aggiornato 2 set 2026). **Distance Fighting 71, Shielding 57.** (era lv30/D64/S53 il 27 lug.) Distance = skill primaria in training. ⚠️ Il default `CHAR_DEF` nella reverse map è ancora fermo a D64/S53 (lug) → va rigenerato/ripubblicato (skill `rivalia-map`) per allinearlo.
- **PROMOTION → Royal Paladin (custom Rivalia): +25% damage** (riportato da Andrea in-game, 2 set 2026 — su Tibia vanilla la promotion NON dà danno, quindi è meccanica CUSTOM; **da verificare su `rivaliaonline.com/wiki.php`**). Se confermato, le tabelle danno "SPEAR" qui sotto vanno moltiplicate ×1.25 per il suo char promosso.
- **IMPORTANTE — stat ITEM su Rivalia sono modificate (non solo i mob):** confermato 15 lug — Dwarven Shield base Rivalia ~26 def (vanilla era 20). NON fidarsi dei valori vanilla di armor/defense/attack degli item; verificare sul Bestiary/in-game. Andrea usa già **Item Attributes** per potenziare l'equip (+2 sullo scudo).
- **Skill/equip (aggiornato 23 lug 2026):** **Shielding skill = 50** (era 45 il 15 lug — sale trainandolo **AFK, facendosi picchiare dai mostri in mischia**, il metodo corretto: vedi FORMULE AVANZAMENTO SKILL). Equip indossato: **Dwarven Shield potenziato +2 → defense 28** (base Rivalia ~26 + 2 da Item Attributes; già usa il sistema enchant). Cercare solo scudi/base con def >28, **Plate Armor (body) = 11**, Legs 7, Boots 1, Scarf 1, Helmet 6. Armor totale sommato = 26 (PARI ✓). ⚠️ NON confondere lo **Shielding skill (50)** con la **defense dello scudo (28)** — errore fatto il 15 lug, corretto da Andrea. Shielding 50 = block molto forte; con def-scudo 28 il max block è alto → può reggere spawn multipli/mischia meglio di un tipico paladin kiter.
- Strategia combat: **kiting** (shoot-and-retreat) contro mischia; contro ranged (Witch, Amazon con spear) rompere line of sight o chiudere distanza.
- **Mana scarso**: riservato a Exura (heal), non Conjure Arrow ai bassi livelli. HP/mana rigenerano **solo da ben nutrito** (mangiare sempre).
- **IH runes** su hotkey "use on self" per heal mana-free in emergenza.
- Due **Crossbow** da loot: una per futuro Item Attributes, una da vendere. Switch crossbow deprioritizzato (Conjure Bolt fa bolt normali, guadagno minimo e perde Conjure Arrow gratis).

### Sul tavolo / medio termine
- **Alchemy**: utile subito — craft pozioni mana/health (mana scarso) e raddoppio cariche rune. Da iniziare presto.
- **Boots of Haste**: upgrade equip più importante a medio termine per il kiting. Fonte vanilla = Banshee/Queen of the Banshees Quest, ma **da verificare su Rivalia** (può essere modificata).
- **Mining**: investimento a lungo termine; dà reagenti crafting (Aether Shards, Disenchantment Shards, Pulse Energy…) per il sistema Item Attributes — non item combat.
- **Item Attributes**: sistema enchant custom Rivalia; una Crossbow è destinata a questo.
- Spot valutati finora: Rotworm, Cyclops, Minotaur, Amazon, Valkyrie, Wild Warrior, Orc Shaman, War Wolf.

### Principi chiave
- **Distance Fighting sopra tutto** ai bassi livelli, il resto è secondario.
- **Kiting è direzionale**: ottimo vs mischia, inutile vs ranged (serve break line of sight o chiudere distanza).
- **Mana conservation > conjuring** con mana pool piccolo (salva per Exura).
- **Magic Shield (Utamo Vita) non ancora viabile** (troppo mana).
- **HMM runes non trainano Distance Fighting** (burst sì, skill no).
- **Store Inbox** è separato dal backpack (Rivalia-specific): item lì vanno trasferiti a mano.
- **Loot**: vendita player-market (es. Halberd) spesso > prezzo NPC; controllare prima di vendere.

## DATI REALI LOCALI (usa questi per i numeri, in personal/rivalia/)
Dati Rivalia REALI già estratti — **usali come fonte dei numeri invece di rifare WebFetch** (ma se sospetti un cambio, ri-verifica sul Bestiary):
- **`catalog-stats.json`** — stats REALI di tutte le ~212 creature del Bestiary (health, experience, speed, race, armor, defense, immunities, attacks, loot).
- **`hunt-spots.json`** — DB completo spawn (174 creature, 12254 punti; x,y,z,amount,radius,time), da wiki.rivaliaonline.com/hunt-spots.json.
- **`rivalia-zones.json` / `.csv`** — zone geografiche (griglia 150) con creature per zona.
- **`exp-ratio-under300.csv`** — analisi EXP/HP per mostri sotto 300 HP, split ranged/melee, con danno attacco.

> 🗺️ **La reverse map interattiva** (zona→creature, insights, PK map, pathfinder "come ci arrivo") e **tutto il come rigenerarla/pubblicarla** vivono nella skill separata **`rivalia-map`** — quella è l'unica fonte per le operazioni sulla mappa; non duplicare qui i comandi di build.

### REFERENCE TIBIAWIKI 7.4 (in `references/` — dentro questa skill)
Indicizzate da TibiaWiki (fandom), **filtrate a `implemented ≤ 7.4`** — 206 pagine. ⚠️ Sono **7.4 VANILLA, NON Rivalia**: geografia/struttura quest/layout spot sono in gran parte validi, ma **stats creature, loot, reward e NPC DIFFERISCONO** — incrocia sempre coi dati REALI locali (`catalog-stats.json`, `hunt-spots.json`) e wiki.rivaliaonline.com. Ogni file ha il banner di avviso.
- **`references/INDEX.md`** — indice navigabile delle 3 sezioni (Routes con link; Quests e Hunting Places in tabella con livello consigliato + reward/location). **Parti SEMPRE da qui.**
- **`references/routes/`** (22) — rotte di viaggio città↔area (Mintwallin, Kazordoon, Femor, Demona, Hellgate…). Utili per "come arrivo a X".
- **`references/quests/`** (79) — quest mainland con reward/location/livello/dangers. Tratta reward/dangers come "vanilla, da verificare su Rivalia".
- **`references/hunting-places/`** (105) — guide spot per livello/vocazione. Usale per il LAYOUT/idea dello spot; per i numeri reali (chi droppa cosa, densità spawn) usa `catalog-stats.json` + `hunt-spots.json`.
- **Quando serve una route/quest/spot: leggi PRIMA il file locale in `references/`** invece di WebFetch (il fandom blocca WebFetch con 402; e comunque questi sono già filtrati 7.4). Se manca, l'API MediaWiki via curl funziona (`https://tibia.fandom.com/api.php?action=parse&page=X&prop=wikitext&format=json`, con User-Agent browser).

**Definizione "ranged" concordata:** un mostro è ranged solo se ha danno a distanza VERO (Physical separato dal melee = freccia/lancia, o magie Fire/Energy/Ice/Poison). **Life Drain / Mana Drain NON contano** (sono da contatto) — es. Ghoul è melee, non ranged.

## MAPPA & OPERAZIONI → skill `rivalia-map`
Tutto ciò che riguarda la **reverse map** (rigenerarla, pubblicarla su GitHub Pages, il pathfinder, le regole di walkability, i percorsi build, il refresh settimanale PK) sta nella skill separata **`rivalia-map`**. Questa skill (`rivalia`) è **solo consigli di gioco** — se ti serve costruire/aggiornare la mappa, usa `rivalia-map`.
