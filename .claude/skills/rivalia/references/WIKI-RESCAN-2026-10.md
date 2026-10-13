# Rescan completo wiki — 13 ott 2026 (rivaliaonline.com/wiki.php)

Fonte: scrape diretto di `rivaliaonline.com` (curl + User-Agent browser funziona; la wiki NON è giù).
Dati strutturati in `personal/rivalia/wiki-2026-10/` (`creatures.json` con rarità loot, `spells.json`,
`hunting-zones.json`, `raids.json`, `artifacts.json`). `catalog-stats.json` è stato aggiornato (stats + loot).

Struttura attuale del wiki (hub `wiki.php`): Creatures 214 (30 boss) · Spells 80 · Items (20 categorie, ~1200 item) ·
NPC 355 · Raids 35 · Quests 5 questlines + 222 reward chest · Hunt Finder · Hunting Zones 164 ·
Game Features: Artifacts, Prestige Arena, Upgrading Items, Mining, Task Board, Guild System, Charms, Market, Premium, Referral.
Pagine vuote/rotte: `changelog.php` ("no change logs"), `serverinfo.php`, `market.php` (errore config server).

## Mondi / contesto
- Mondi: **Aeternum** (low-rate, lanciato 18 mag 2026 — quello di Andrea), Legacy, Ascendia, **Destiny** (PvP, nuovo:
  lancio 5 ott 2026, rate 2x exp/skill/loot/spawn/regen, magic 1x, rune a pagamento ma conjurate con carica doppia).
- Novità del lancio Aeternum: Prestige Arena, Task Board, Daily Rewards, Hunt Finder, New Spells (si comprano liberamente),
  Nivarya + Port Hope, Daily Bosses, Artifacts potenziati.
- Giu 2026: nuovo **Rivalia Launcher** obbligatorio (anti multi-client/bot). Regole: 1 solo char online, no VPN/VPS/remote desktop
  (ExitLag/NoPing ok), no bot/macro/VM, zero tolleranza.
- Da news Destiny (set 2026, "recent changes"): skill **Skinning** (coltelli dai pick merchant, Skinning Pouch in store),
  +5% exp ai premium che castano pubblicamente, **5 Disenchantment Shard → 1 Aether Shard** (crafting), mining non distrugge più
  i reward, pouch illimitati, **Event Calendar** nel client. (Non verificato che valgano anche su Aeternum.)

## ⚠️ Sistema di upgrade equip — CAMBIATO (sostituisce la "sezione A" vecchia della SKILL)
Pagina `upgrading_items.php` + `mining.php`. Il vecchio modello (Aethernite Small/Medium/Large comprata da NPC, rune
Astralite/Celestium/Mythraline/Eclipsite) **non compare più** sul wiki. Ora:
1. Materiale: **Aether Shard** (mining o elite con teschio-stella ★/★★/★★★) → crafting station in città: **5 Shard → 1 Large Aethernite**
   (100% success, 0 gold). **5 Disenchantment Shard → 1 Disenchantment Rune** (success base bassa, scala con Crafting).
2. **Rarity Upgrade module** con 3 azioni: **Upgrade** (aggiunge attribute, poi promuove tier), **Reroll** (cambia 1 attribute), **Disenchant**.
3. **Lock** attribute = 5 Rivalia Coins ciascuno. **Boosted Chance** = costo ×2, success più alto.
- Reroll (rarità → gold / Large Aeth / base% / boosted%): 1: 800/5/25/35 · 2: 2.4k/12/20/28 · 3: 7.2k/24/15/22 · 4: 21.6k/48/10/15 · 5: 64.8k/96/5/8.
- Upgrade (rarità target): 1: 800/12/25/35 · 2: 2.4k/24/20/28 · 3: 7.2k/48/15/22 · 4: 21.6k/96/10/15 · 5: 64.8k/192/5/8.
- Disenchant: gold per classification 1..5 = 200/600/1.8k/5.4k/16.2k + 1 Rune; rende 2-4 / 4-6 / 8-12 / 12-20 / 20-30 shard per attribute.
  Success per #attribute tolti (non lockati): 1→50/75% · 2→40/65 · 3→30/55 · 4→20/45 · 5→10/35 (base/boosted).
- Conto rapido: un Reroll rar.5 costa ~96 Large = 480 shard a tentativo con 5% → **non inseguire rar.5**; rar.1-2 sono abbordabili.
- L'**Exaltation Forge** (Dust/Slivers/Cores, Fusion/Transfer, Find Fiend) descritto in SKILL viene dalla guida Discord e **NON è sul wiki**:
  trattalo come non confermato. **Find Fiend** (`exiva moe res`) esiste davvero: Zoltan, 2.000 gp, tutte le vocazioni.

## Mining (pagina `mining.php`)
- Nodi (respawn 30 min, stack 1-5, drop equiprobabili): **Lava Hole** (id 389) → Aether Shard / Disenchantment Shard (50% Aether = miglior fonte);
  **Blue Shrine** (1354) → Aether, Disench., Small Sapphire, Small Emerald; **Red Shrine** (1355) → Disench., Small Ruby, Small Amethyst.
- Swings per nodo: random 5-10, −1 ogni 25 skill, −tier pick. Break roll: floor **28%** (fino a skill ~71), cap **90%** (skill 234+; Golden già a 180).
  Skill +1 progress per nodo rotto (riuscito o no). Costo livello +10% per livello.
- Pick (Uzgod, Kazordoon): Pick/Multi-tool base (id 2553/5170) · **Advanced** 25 skill 25k (×1.15, +12 stack, −1 swing) · **Modified** 40 skill 100k
  (×1.20, +22, −2) · **Enhanced** 55 skill 250k (×1.25, +32, −2) · **Golden** 70 skill 500k (×1.30, +42, −3).
  Resa a skill 70 (materiali/100 swing): 6.7 / 10.7 / 16.2 / 19.2 / 30.0 → **Modified = miglior rapporto qualità/prezzo; Enhanced = upgrade peggiore.**
- Pouch (store): Mining Pouch 100 Coins, **Golden Mining Pouch 500 Coins** (tiene i pick, click destro sul nodo). Cooldown **15 min dopo ogni login**, no PZ.
- Nodo condiviso per tile: chi dà il colpo finale prende il drop.
- **Aether Prism** (artifact): 0.1% per mine riuscita; 5% di dare 1 Large Aethernite al posto degli Aether Shard.
- 10 Small gem → 1 Giant gem (artifact Giant Sapphire/Emerald/Ruby/Amethyst).

## Artifacts (38) — da `artifacts.json`
Slot artifact (ring-like). Utili per un Paladin: **Sniper Gloves** (1% preserva munizioni, 62 oz), Cyclops Hand (crit +5%/+10%),
Percht Head (life leech 5%/7%), Demon Heart (HP regen +2/6s, healing +3%), Warriors Blessing (5% heal full on death), Rabbit's Foot (spawn luck),
Protector Charm (25% riduce skill loss — consumato), Seal of Preservation (100% sposta container protetti al depot alla morte — consumato),
Artifact of Loss (20% preserva amulet of loss), Ancestral Spirit Ring / Cobra Spirit (ML+1, mana regen), Giant Ruby/Sapphire/Emerald/Amethyst (HP/mana regen o max, a tempo),
Aether Prism (mining), Alchemist Shades (alchemy). Alcuni senza descrizione (Draconian Sigil, Medusa Head, Void Core, Worldshaper…).

## Charm System (pagina `charms.php`)
Charm Points = si guadagnano completando stage del Bestiary. 1 Charm per creatura; cambiare costa gold in base al livello.
Costi: Wound 140 · Enflame 160 · Zap 160 · Poison 180 · Freeze 160 (5% chance, 5% maxHP come danno elementale) · Adrenaline Burst 120 · Dodge 140 ·
Numb 120 · Parry 180 · Cripple 140 · Carnage 200 · Void Inversion 140 · **Overpower 300** (5%: danno = 5% tuo maxHP) · **Overflux 300** (5%: 2.5% tuo maxMana).
Per Paladin a distanza: i 5 charm "5% maxHP del mostro" sono i migliori contro mostri con HP alti (boss/Dragon Lord…). Non funzionano in Prestige Arena.

## Task Board (pagina `task_board.php`) — completo
- Valute: **Bounty Points** (daily; Talisman + slot Preferred), **Re-Roll Tokens/dadi** (1 free/giorno + dai task), **Hunting Points** (weekly; shop outfit).
- Daily: max 3 task, 24 h ciascuno. Tier (kill / BP / exp cap): Beginner 50-100 / 3 / 30k · Adept 100-200 / 6 / 100k · Expert 200-400 / 11 / 300k · Master 300-600 / 16 / 800k.
  Exp ≈ monster_exp × kills × 0.33 × mult (con cap). Silver ~8% (exp ×1.5, BP ×2), Gold ~6% (exp ×2, BP ×4). Party: max 2 beneficiari per kill.
- **Bounty Talisman** (artifact slot): solo vs i mostri bounty attivi: danno +2.5→15%, life leech +2.5→12%, loot +2.5→30%, bestiary ×2 chance +5→50%.
  Upgrade costo BP = 5×(lvl+1)²+2.
- Preferred list ×5 più probabile, Unwanted rimosso; 1 slot ciascuno → 5 (slot n costa owned×200 BP; assegnare costa 10 BP).
- Weekly (reset **lunedì 08:00**): 6 kill + 6 delivery (espandibili a 9+9 con 1.000 Shop Points l'uno). Slot kill 1 = "Any Creature".
  Hunting Points per kill task: 20/35/55/75 (Beg/Adept/Exp/Master); delivery 60 HP flat. Barra moltiplicatore (tabella wiki): 5→×1.5, 8→×2, 12→×3, 16→×4. ✅ **CORREZIONE di Andrea (in-game, 13 ott): su Aeternum il weekly arriva a ×8 con 12 task** — la tabella del wiki è sbagliata/obsoleta, il testo della pagina che cita ×8 era quello giusto. Quindi basta chiudere 12 task, non 16.
- Shop: outfit base 8.000 HP, addon 4.000 HP ciascuno (set completo 16.000).
- Pool mostri per tier: Beginner (rat, orc, troll…), Adept (cyclops, dragon, kongra, minotaur*, vampire…), Expert (hydra, wyrm, banshee, cold ambusher, lich, serpent spawn…),
  Master (demon, dragon lord, behemoth, frost dragon, frozemoth, undead dragon, manticore, grim reaper…).

## Prestige Arena (`prestige_arena.php`)
Duelli ranked 1v1, **lvl 100+, 5.000 gp a coda**, solo da tempio. Match al meglio di 2 round; danno mostri cresce ogni 60 s; morire in arena non perde exp.
Consumabili (rune/mana fluid) infiniti; ring e amulet no. Prey wildcard, charm e weapon proficiency NON attivi. Divisioni (punti): Newbie 0 · Wooden 300 · Gold 700 · Platinum 1200 ·
Crystal 1800 · Terror 2500 · Champion 3200 · Exalted 4000 · Megalomaniac 5000 · Sanguinum 6000+ · Warlord 7000+. Premi divisione: Gold 1 Roulette Coin, Platinum 7 VIP days,
Crystal 15 VIP + 1 Boosted Exercise Present. Fine stagione top 10: 5.000/3.000/2.000/1.500/1.000/800/600/400/300/200 Rivalia Coins. Stagione 1 in corso.

## Guild System (`guild_system.php`)
Crea: lvl 8 + premium, gratis; 25 emblemi; nome 1-20 lettere/spazi/underscore. Livello guild: costo N×100k gold (lvl 18 = 15,3M totali), +5 slot membro per livello (10 a lvl 1).
Ogni 2 livelli un buff slot (9 slot, 2 opzioni esclusive): regen HP/mana (2/14s→2/4s) · crit chance/danno · movement/attack speed · prot. fisica/elementale · life/mana steal ·
**Magic Level/All Skills (+2..+7)** (lvl 12) · prot vs mostri/player · danno vs mostri/player · mana cost/cooldown reduction. Upgrade con Rivalia Coins (500..2500 per rank, 7.500 totali), 1 upgrade/24 h.
Guerre a frag, senza skull, emblema war; roster bloccato in guerra.

## Hunting Zones (164) e Zone Boost
Ogni zona si può **boostare** (menu laterale "Zone Boost", gold, fino a 3 h, respawn più veloce per tutti). Dati in `hunting-zones.json`.
Top exp per mostro (media pesata): Dragon Graveyard (Undead Dragon 18.5k) · Shadowdrake Roost (11.5k) · Queen's Shrine (Carlin) · Manticore Den (Port Hope 5.7k) · Drefia Reaper Halls · Grimaw Chasm (Nivarya: Demon 6k, Grimaw 2.9k).
Nivarya (19 zone) e Port Hope (16) sono i nuovi contenuti di fascia alta. Il boost +10% era attivo su Port Hope Troll Mire al momento dello scan.

## Creature (214) — differenze rispetto ai dati vecchi
- **3 boss nuovi, nessun loot, nessuno spawn naturale (evento/raid?)**: **Ignaroth** (150k HP, 350k exp, fuoco, summona Hellforged Devil ×2), **Zatharak** (150k HP, 350k exp, energia, summona Wyrm ×3),
  **Zyphera** (120k HP, 350k exp, veleno, armor 90/def 120, summona Hydra ×3). Speed 180.
- Stats cambiate: **Cold Ambusher** 120→1180 HP, 90→800 exp, speed 130 (48 spawn in Ambusher's Pass, Nivarya) · **Skeleton Mage** 50→800 HP, 35→900 exp, speed 120 · Grim Reaper speed 260→160.
  (Probabile che i dati vecchi fossero di una versione precedente o di un'altra fonte.)
- I loot table sul wiki sono molto più completi dei dati locali precedenti (che erano troncati a ~12 item): ora 76 creature hanno item in più. `Skullar` non è più sul wiki.
- Rarità loot: Common, Uncommon, Semi-Rare, Rare, Very Rare, Extremely Rare, Almost Never.
- 🔑 **Boots of Haste** (target kiting di Andrea) — fonti vere dal wiki: Necromancer (Almost Never, 109 spawn, 580 exp), Cold Ambusher (A.N., 48 spawn), Hydra (A.N.),
  Wight (A.N.), Black Knight (Extremely Rare), Skull Reaper, Omruc, High Necromancer, Necropharus; boss: Apocalypse/Bazir/Infernatil/Morgaroth/Orshabaal/Ferumbras (Very Rare).
  La Banshee/Queen Quest è solo l'ipotesi vanilla. "Almost Never" ≈ la rarità più bassa: aspettati migliaia di kill.
- Armi distance dai mostri: Crossbow (Dragon Semi-Rare, Minotaur Archer Semi-Rare, Forsaken Knight, Wyrm), **Scaled Quiver** (Dragon, Hydra — A.N.), Royal Spear (Dragon, Rare),
  Poisoned Bow (Manticore, Very Rare), Spectral Bow (Shadow Wraith, A.N.), Crystallized Bow/Crossbow (Crystal Wolf, Frozemoth, Forsaken Knight), Composite Hornbow (Wyrm, Elder Wyrm).

## Spell (80) — Paladin
Compra libera da NPC appena rispettati i requisiti. Paladin: Light/Intense/Ultimate Healing (170/350/1000 gp, ML 1/2/8), **Magic Shield `utamo vita`** (ML 4, 450 gp), Haste `utani hur` (prem, ML 4, 600),
Invisibility, **Stealth `utana gran vid`** (ML 18, 10.000 gp, cooldown 6s), Magic Rope, Levitate, **Conjure Arrow `exevo con`** (ML 2, 40 mana, 450),
Poisoned Arrow (ML 5, 70), **Conjure Bolt `exevo con mort`** (ML 6, 70 mana, 750 — 1 NPC), Explosive Arrow (prem, ML 10, 120), **Conjure Power Bolt `exevo con vis`** (prem, ML 14, 200 mana, 2.000),
Training Spear `exevo con lancea` (prem, 50 mana), Food, Great Light, Antidote, Find Person/Find Fiend, rune: Light MM, Heavy MM, Fireball, Destroy Field, Desintegrate.
Nuovi/custom per altre vocazioni: Force/Energy/Flame Strike, Berserk (Knight, 40% mana), Cleanse, Heal Friend, Purity of Life, Mass Healing.

## Raid (35)
Intervallo = gap minimo tra due esecuzioni, non un timer. Dati in `raids.json` (posizioni + mostri). Invasioni ogni 6 mesi: Scarab (Ankrahmun), Undead, Orc, Elf.
Boss raid: Orshabaal (1 anno), Demodras, Necropharus, Dharalion, The Old Widow, Horned Fox, Mino General, The Evil Eye, Grorlam (6 punti, 14 giorni), Fernfang.

## Quest / NPC / Items
- Quests: solo 5 questline tracciate (Cult of the Queen 4 mission, Nivarya 12, Trade Faction 1, Djinn War 3, Postman 10) + 222 reward chest classici.
- NPC: 355 (invariato). Items: ~1200 in 20 categorie (Swords 36, Axes 30, Clubs 28, Dist. weapons 17, Ammo 7, Wands 13, Runes 29, Helmets 45, Armors 42, Legs 26, Boots 15, Shields 43, Amulets 30, Rings 18, Containers 89, Artifacts 40, Food 41, Jewelry 15, Creature products 208, Other 428).
  Le pagine item per categoria (`items.php?...`) NON sono state scrapate in questo giro.

## Prezzi NPC dei drop mancanti
`items-prices.json` mancava di 64 item di loot (Dragon Scale Mail 40k, Magic Plate Legs 120k, Scaled Quiver 4k, Boots of Haste 30k…) perché la lista loot vecchia era troncata. Riscrapati il 13 ott: ora 514 item, 229 con prezzo di vendita NPC. Alcuni (Ouroboros, Dragonbone Sigil…) non hanno NPC che li compra.

## Non verificato / TODO
- Pagine item per categoria, dettagli di ogni quest/raid per region, Hunt Finder (mappa JS), daily reward e premium benefits non letti riga per riga.
- Se serve il prezzo/stat di un item specifico, vai su `items.php` e fetcha la categoria.
