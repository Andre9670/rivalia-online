# The Djinn War — versione LIVE Rivalia (letta dal wiki il 13 ott 2026)

Fonte: `rivaliaonline.com/quests.php?quest=the-djinn-war` + pagine NPC + pagine item (`items.php?item=<slug>`, sezione "Traded by").
Questa nota **sostituisce** le due vecchie (`the-djinn-war-efreet-faction.md` / `-marid-faction.md`, copiate da Fandom/vanilla) per NPC e ricompense.

## La quest (3 missioni nel quest log)
1. **Greeting the Djinns** — impari il saluto `djanni'hah`, poi **scegli** Marid (blu) o Efreet (verde).
2. **Marid Faction** — Ashta'daramai: Bo'ques (libro di cucina nanico) → Fa'hradin (rubare lo spy report a Mal'ouquah dall'ingresso posteriore) → Gabel
   (mettere la lampada di Fa'hradin nella stanza di Malor, lampada presa all'Orc King). Fine: **"Marid's gratitude and trading rights"**.
3. **Efreet Faction** — Mal'ouquah: Baa'leal (trovare il ladro di rifornimenti a Carlin) → Alesar (rubare la Tear of Daraman a Ashta'daramai) → Malor
   (catturare la lampada di Fa'hradin e metterla nelle stanze di Malor). Il log dice testualmente: **"earn access to Efreet traders Alesar and Yaman"**.

⚠️ Il quest log Rivalia NON nomina i trader Marid: "Nah'bob e Haroun" è la regola vanilla (Fandom) ed è coerente con le pagine NPC (Nah'bob/Haroun
sono i trader di Ashta'daramai, Alesar/Yaman quelli di Mal'ouquah). La **scelta esclusiva** (una fazione sola) e il livello 40 sono vanilla: **non confermati su Rivalia**.
Coordinate NPC approssimate (Tibiantis 7.7, `npcs.json`): Ashta'daramai ~(33104,32520), Mal'ouquah ~(33045,32620).

## Chi compra cosa (prezzo che incassi vendendo all'NPC) — nomi completi ricostruiti dalle pagine item
(⚠️ le pagine NPC del sito troncano i nomi: "sword", "shield"… per questo qui i nomi vengono dalle pagine item. Dati: `personal/rivalia/wiki-2026-10/item-traders.json`.)

### MARID → Nah'bob (compra equip) + Haroun (compra gioielli/varie)
**Nah'bob (21 item, nessun altro NPC li compra tranne dove indicato):** Royal Helmet 30.000 · Boots of Haste 30.000 · Phoenix Shield 16.000 · Crown Legs 12.000 ·
Crown Armor 12.000 · Blue Robe 10.000 · Dragon Lance 9.000 · Fire Axe 8.000 · Crown Shield 8.000 · Crusader Helmet 6.000 · Fire Sword 4.000 (altrove 1.000) ·
Dragon Shield 4.000 (altrove 360) · Crown Helmet 2.500 · Guardian Shield 2.000 (altrove 180) · War Hammer 1.200 (altrove 470) · Beholder Shield 1.200 ·
Spike Sword 1.000 (altrove ~240) · Ice Rapier 1.000 · Noble Armor 900 · Obsidian Lance 500 · Broadsword 500.
**Haroun (compra):** Orb 750 · Stone Skin Amulet 500 · Stealth Ring 200 · Mind Stone 100 · Melee Ring 100 · Elven Amulet 100 · Life Crystal 50 · Garlic Necklace 50 ·
Distance Ring 50 · Bronze Amulet 50 · Magic Light Wand 35. (Vende anche: Stealth Ring 5.000, Melee Ring 500, Elven Amulet 500, Magic Light Wand 120, Garlic Necklace/Distance Ring/Bronze Amulet 100.)

### EFREET → Alesar (compra equip) + Yaman (compra anelli/amuleti)
**Alesar (18 item):** Giant Sword 17.000 · Vampire Shield 15.000 · Tower Shield 8.000 · Skull Staff 6.000 · Warrior Helmet 5.000 (altrove 696) ·
Knight Legs 5.000 (altrove 375) · Knight Armor 5.000 (altrove 875) · Knight Axe 2.000 · Dragon Hammer 2.000 · Serpent Sword 900 · Ancient Shield 900 ·
Black Shield 800 · Strange Helmet 500 · Dark Armor 400 · Dark Helmet 250 · Scimitar 150 · Mystic Turban 150 · Poison Dagger 50.
**Yaman (compra):** Might Ring 250 · Time Ring 100 · Ring of Healing 100 · Protection Amulet 100 · Energy Ring 100 · Dwarven Ring 100 · Dragon Necklace 100 · Ankh 100 ·
Silver Amulet 50 · Mysterious Fetish 50 · Life Ring 50 · Strange Talisman 30. (Vende anche Might Ring 5.000, Time/Healing/Energy/Dwarven Ring 2.000, Dragon Necklace 1.000, Life Ring 900, Protection Amulet 700.)

## Chi droppa gli item di Nah'bob / Alesar (wiki creature, rarità)
- **Nah'bob:** Royal Helmet → Dragon Lord, Hydra, Frost Dragon, Serpent Spawn, Chaos Hydra (tutti *Almost Never*) · Boots of Haste → Necromancer, Cold Ambusher, Hydra, Wight (*A.N.*), Black Knight (*Extremely Rare*) ·
  Crown set (armor/legs/helmet *Extremely Rare*, shield *A.N.*) → Forsaken Knight, Hero · Dragon Lance 9k (*Rare* Undead Dragon) · Crusader Helmet 6k (*Rare* Undead Dragon) · Fire Axe 8k (*Very Rare* Demon) · Phoenix Shield → Mahrdis (*A.N.*).
- **Alesar:** Giant Sword 17k (*Very Rare* → Demon, Frozemoth, Abomination, Undead Dragon, Behemoth) · Vampire Shield 15k (*A.N.* → Vampire, Ice Witch) ·
  Tower Shield 8k (*Rare* Abomination/Undead Dragon; *A.N.* Dragon Lord/Frost Dragon/Serpent Spawn) · Skull Staff 6k (*Rare* Undead Dragon, Warlock, Wight, Bonereaper) ·
  Warrior Helmet 5k (*Rare* Abomination, Black Knight) · Knight set 5k (*Rare* Shadow Drake; *Very Rare* Winter Guardian, Hydra, Medusa).

## Lettura critica per un Paladin low-rate
- Il valore "best NPC" mostrato dalla mappa/Loot-value **somma NPC di fazioni opposte**: non puoi incassare insieme Royal Helmet 30k (Nah'bob) e Giant Sword 17k (Alesar) se la scelta è esclusiva. Va scelto UNA fazione.
- Nah'bob ha i prezzi singoli più alti, ma quasi tutto è *Almost Never/Extremely Rare* (Royal Helmet, Crown set, Boots of Haste che comunque terrai). Alesar ha item molto più realistici da droppare
  (Giant Sword *Very Rare*, Tower Shield *Rare*, Skull Staff *Rare*, Warrior Helmet *Rare*) sui mob di fascia alta di Nivarya (Abomination, Undead Dragon, Frozemoth, Demon).
- Le percentuali esatte delle etichette di rarità NON sono pubblicate dal wiki: la raccomandazione è un'inferenza dalle etichette, non un calcolo.
- Alcuni item di valore (es. Dragon Scale Mail 40k, Magic Plate Legs 120k) li compra Zarith the Accredited (Kazordoon) → serve la **Trade Faction Accreditation** (100.000 gp), quest separata.
