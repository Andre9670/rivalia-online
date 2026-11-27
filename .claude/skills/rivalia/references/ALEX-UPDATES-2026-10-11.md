# Update ufficiali di Alex (Discord) — 8 ott → 27 nov 2026

Fonte: annunci di Alex incollati da Andrea il 27 nov 2026 (testo ufficiale degli sviluppatori, non wiki). I prezzi Zarith sotto sono stati ricontrollati sul sito live (`items.php?item=…`). Omessi perché irrilevanti per il gioco di Andrea: poker, store/outfit, cam mp4, Encyclopedia, Cyclopedia UI, Event Store dettagli minori.

⚠️ Il Hunt Finder (`layout/huntmap/spawns.json`) può mostrare i cambi di respawn **prima** del Server Save in cui Alex dice che entrano (il 27 nov mostrava già Fleshcursed rimossi e Bonereaper 12→28, annunciati "al prossimo save"). Non fidarti di quegli spawn finché il save non è passato.

## Per il Paladin di Andrea (Aeternum, Legacy 1x)
- **Aeternum, 28 ott:** tolta la riduzione di livello a 100 e 150 → exp monster 1x.
- **Dawnforged (annunciato 27 nov, "next Server Save"):** armi end-game più forti delle Annihilator, ricompensa finale Nivarya (una per personaggio, a scelta; più Warriors Blessing). **Dawnforged Crossbow: Atk 4, Hit +1, +2 distance. Dawnforged Bow: Atk 1, Hit +3, +2 distance.** Tutte danno ice damage over time e sono classe Brutal per l'upgrade. **Winterdawn:** click destro sull'arma mentre attacchi → spirito di ghiaccio, 6 colpi (1/s), danno scala col livello, cooldown 3 min, non in PZ/case; PvP a metà danno.
- **Artifacts 10 slot (24 nov):** slot 6–10 affittabili da Malor o Gabel dopo il reward Annihilator, 200.000–1.000.000 gp.
- **Line of sight simmetrica (19 nov):** un muro blocca la stessa area in ogni direzione (prima NW bloccava molto più di NE/SW/SE). Vale per rune, distance attacks, lanci e area spell. Non si lanciano più oggetti oltre un muro all'aperto; le wave aggirano meglio i magic wall diagonali.
- **Exeta (20 ott):** `exeta res` agisce subito e cancella le azioni in coda del mostro.
- **Logout (6 nov):** 1,5 s; se c'è un attacco già in volo ti mette in fight e blocca il logout.
- **Stamina:** in Safe Zone rigeneri come offline (20 ott). **Arance:** 12 min di regeneration (17 ott). **Eternal Effigy:** 1 mana ogni 8 s (prima 36), 30 ott.
- **Elite/influenced/fiend:** despawnano come le altre elite (18 ott). **Skull al logout/morte:** non resta più lo skull dopo save/campi di fuoco (17 e 21 ott).
- **World Transfer (17 nov):** i personaggi di Aeternum possono trasferirsi su Destiny dal sito ("World Transfer"), con fee su Destiny.
- **Event Points (14 nov):** Bronze Exchange Token 5 pt, Silver 10 pt (ogni mostro li droppa, elite molti di più). Blessing Gem 3.000 pt (dà tutte le blessing mancanti), Diabolic Skull 6.000 pt (toglie frag e skull, ti slogga).
- **Guild buff (18 ott):** da 7.500 RC a 500 RC totali (50/75/100/125/150). **Tournament guild (6 nov):** 10 pt per frag (max 30/giorno), 1 pt per 100k exp PvP, 1 pt per 100k exp hunting (max 3kk/giorno); il 24 nov l'exp della morte si divide solo tra chi ha attaccato di recente in PvP.

## Dungeon System (lanciato 26 ott)
- Entrata solo con **gold nel backpack** (mai dalla banca), resto in backpack o in banca; **nessun battle lock** (60 s dopo l'ultimo colpo, vale anche con i mostri); white/black skull non entrano, red skull sì senza lock; il lock sparisce uscendo o morendo dentro (30 ott). Dal 28 ott i red skull senza PZ lock entrano.
- Il dungeon livello 50 aveva il boss con troppo danno (avviso 26 ott, fix al save dopo). Dal 13 nov **loot moltiplicato** anche sui mostri normali quando alzi la difficoltà (prima solo il gold).
- **Rimefall Peaks:** livello 60, entrata 6.000 gp; ci sono i **Winter Dragon** (sostituiscono i frost dragon; anche il boss Hjalvorn the Frostmaw). **Ashen Caldera:** livello 65. **Frostfang Hold:** niente più Coldcrawler, solo jothun e jothun elder (molti più).
- **Come si vede nel Hunt Finder:** gli spawn dei dungeon stanno su coordinate fuori dall'immagine mappa (x 34.2k–36.7k, y ~32.4k), in ~10 gruppi tematici (orc, cyclops/beholder, tomba/mummy/vampire, lizard, jothun/ice, hydra/cobra, tarantula/spider, dragon/dragon lord/hellforged, winter dragon/rimewing, wyrm/elder wyrm). Frostfang Hold (jothun) e Rimefall Peaks (winter dragon+rimewing) coincidono con gli annunci; gli altri sono dedotti dalla composizione, non confermati. Vanno in `personal/rivalia/hunt-spots-offmap.json`, non sulla mappa.

## Respawn / mostri
- **Edron hero cave — respawn nascosto Black Knight + Wild Warrior (15 nov):** ora nel Hunt Finder (BK 4→42, WW 47→106). Cluster BK/WW a x 33.050–33.150, y 31.650–31.700, z 11–12 (sovrapposto agli `hero` della hero cave). Pensato per team/knight+mage e per le task.
- **Dragon Lord a nord di Darashia** e **Warlock/timer di Demona:** corretti (6 nov). Sea Tyrant: respawn fixato, 10 min → 3 min (26 ott; nel Hunt Finder il valore `time` è passato 900→300).
- **Souleater:** aggiunti mostri sotto il respawn (18 nov) — 36→89 punti.
- **Nivarya:** nuovo spawn Winter Dragon + Rimewing sulla mappa Nivarya (30 ott). Missione 9: Void Draken (1.000 Frost Dragon, poi Shadow Drake Respawn), missione 10: Essences of the Fallen. Dopo il task 100 Giant Demon Skeleton di Sereun si entra nel **respawn dei Winter Guardian**. **Glacial Wyrm** sostituisce i Chaos Hydra al seal est (e via gli Undead Dragon lì); HP 11.000→10.000, loot rifatto; "hunt viabile per livelli alti". Bonereaper e Fleshcursed più forti (24 nov); poi respawn Bonereaper rifatto: più Bonereaper, **Fleshcursed rimossi** da quell'area (25 nov). Sayron e Fherumin compaiono sui troni dopo 800 kill bestiary. **Sapiovor:** fino a 5 giocatori, 100.000 HP, chi lo danneggia completa la missione; flame del seal finale consuma le essence solo la prima volta.
- **Demon Overlord + danno Death** (nuovo tipo, lascia **Cursed** = DoT con icona): colpisce più di un Demon, usa death al posto del fuoco, campi di fuoco neri, evoca il nuovo Death Elemental (25 nov).
- **Zatharak** (boss del weekend, 6 nov): speed 180→230, HP 150k→155k, area electrify, energy blast raggio 7, chiama 2 Wyrm invece di 3.
- **Elder Wyrm:** corpi decadono (21 ott); loot table ampliata (13 nov); ora droppa **Wyrm Scales** (28 ott). **Medusa/Manticore/Giant Cobra:** corpi decadono (21 nov).

## Loot e NPC
- **Giant Cobra** può droppare una **green gem**; la comprano per **5.000 gp** Briasol, Gail, Hanna, Ishina, Iwan, Odemara, Tesha, Tezila (30 ott; ricontrollato: 8 trader).
- **Bonereaper (25 nov):** revenant set (mask, armor, legs, boots) molto più frequente; droppa anche black pearl, knight armor, knight legs, vampire shield, infernal hood, infernal boots, ancestral spirit ring. **Undead Dragon** può droppare hellforged helmet e legs. Winter Guardian: loot rifatto. Souleater/Medusa/Grim Reaper products → Creature Product Pouch.
- **Zarith The Accredited** (compra a Kazordoon; prezzi verificati sul sito il 27 nov): ancient armor 75.000, ancient helmet 42.000, ancient legs 45.000, golden legs 30.000, mastermind shield 50.000, spectral bow 80.000, bright sword 6.000, daramanian waraxe 1.600, violet gem 10.000, hibiscus dress 3.000, frozen legs/armor/helmet 5.000 ciascuno, frozen shield 29.000, The Stinger 7.000, Terra Legs 11.000, Lightning Boots 2.500, Magician Hat 8.000, revenant mask/armor/legs/boots 6.000 ciascuno. Resta valido: serve aver fatto la quest con King Tibianus per vendere dallo stash (8 ott). Hellforged Armor 600.000 e Legs 100.000 (già presenti).
- Item stash: Ice Rapier va nello stash e torna con le cariche (28 ott); i prodotti store in inbox non cadono più alla morte (22 ott).
- Rune: small explosive rune da 5 a 10 per conjure (+ opzione "max" = 20), 19 ott; Frostwarden wand usabile con le small explosive rune (22 ott).
- Viaggi: Charles (Port Hope) → Ankrahmun; Pemaret (Eremo) → Cormaya; Captain Frosty ora ha le mappe; click destro su un NPC apre la mappa subito.
