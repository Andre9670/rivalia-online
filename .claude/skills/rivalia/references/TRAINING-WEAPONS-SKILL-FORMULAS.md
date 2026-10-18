# Training Weapons + formule skill (codice live del server) — 17/18 ott 2026

Fonte: "Training Weapons – How the System Works", foglio generato dal codice del server (Tyrhem / Rivalia), allegato Discord, 36 pagine, **valori a rate x1**.
PDF: `Training_Weapons_Reference_2026-10-17.pdf` (stessa cartella). Verifica mia: la formula riproduce le tabelle (Paladin distance 45→46 = 843 tries; 79→80 = 21.539).

## Formule (valgono anche per chi NON usa i Training Weapons)
- Tries da L a L+1 = BASE × MULT^(L−10); BASE melee/fist 50, distance 30, shielding 100.
- Mana per ML M→M+1 = 400 × MANAMULT^M.
- Moltiplicatori (melee / distance / shielding / magic-mana): **Paladin 1.2 / 1.1 / 1.1 / 1.4** · Knight 1.1 / 1.4 / 1.1 / 3.0 · Druid 1.8 / 1.8 / 1.5 / 1.1 · Sorcerer 2.0 / 2.0 / 1.5 / 1.1.
- Rate skill: rateSkill(mondo) × max(Voucher ×2, evento Skill boost) × Mad Santa scroll ×2 × Global Skill Gain +10%. Magic: rateMagic × evento × +10%, il voucher non conta. Per usare le tabelle: dividi ore/charges per il moltiplicatore totale (es. voucher + global = ÷2,2).
- Regola "draw blood" invariata: devi continuare a colpire il dummy per fare danno; tra un colpo che fa sangue e l'altro si contano al massimo 30 blocchi/attacchi.

## Training Weapons
- Funzionano **solo su un Training Dummy**. 10.000 cariche; ogni attacco (a segno o no) o ogni blocco dello scudo consuma 1 carica; a 0 diventa la versione "depleted".
- Sostituiscono la penalità del dummy: **80% di un punto skill** a ogni tier (arma normale sul dummy: 50% sotto skill 50, 75% da 50 in su). **Set bonus +3%** (83%) con arma + scudo training insieme. **Transcendent: Focus 2%** (×2 tries; ~×1,02).
- Tier (solo velocità d'attacco): Charged 1800 ms · Overcharged 1700 · Overflux 1600 · Transcendent 1500. Le tries per carica sono uguali: tier più alto = stesso totale ma più veloce.
- **Training Spear** → Distance, **2 punti per colpo** (1 se il dummy para con la sua difesa): 1,60 tries/carica solo, 1,66 col set (T 1,693); 16.600 tries per item. Training Sword → melee (1 punto). **Training Shield** → Shielding, 1 punto per blocco (dummy attacca ogni 2 s → max 1.800 blocchi/h per tutti i tier; Transcendent solo Focus). Training Wand → ML solo sorcerer/druid. Spear/sword/shield senza vincolo di vocazione.
- Tries/ora col set (x1): Distance con spear: Charged 3.320 · Overcharged 3.515 · Overflux 3.735 · Transcendent 4.064; Shielding (scudo + arma training): 1.494 (C/O/OF) · 1.524 (T). Arma normale sul dummy: 1.800–2.700 tries/h distance (50%/75%), shielding 900/1.350.
- Un'arma normale con Attack Interval (attributo/artifact, 1,9→1,5 s) accorcia l'intervallo ma paga la penalità 50%/75%. Il buff guild Attack Speed accorcia anche i training weapons, quindi non cambia il confronto.

## Numeri per il Paladin di Andrea (Distance 79, Shielding 62), x1, senza voucher
- **+10 Distance (79→89): 343.269 tries.** Per livello: 79→80 = 21.539 tries; 80→85 = 144.645; 85→90 = 232.951.
  - Training Spear Transcendent col set sul dummy: **~84 h** continue (≈20 spear da 10.000 cariche). Charged: ~103 h.
  - In caccia (≈1 try per colpo a segno): a ~1.000 colpi/h ≈ 340 h; a 1.800 colpi/h (massimo teorico, 100% hit) ≈ 190 h.
- Shielding 62→72: 226.380 tries (62→63 = 14.204); con scudo + arma training Transcendent (1.524/h) ≈ 149 h.
- Magic level 15→16 per Paladin: 62.227 mana; 15→20: 681.114 mana.
- Se il Global Skill Gain +10% è attivo, dividi per 1,1 (voucher ×2 per ×2,2).

## Non c'è nel PDF
Dove si comprano/droppano i Training Weapons e quanto costano; se esistono dummy in ogni città. (Da chiedere / verificare in-game.)

---
# INSIGHTS TRAINING (analisi mia sui numeri del foglio; Paladin Andrea: Dist 79, Shield 62, ML 15; x1, senza voucher)
1. **Il set (spear + scudo training) allena DUE skill insieme.** La spear dà Distance (2 punti/colpo), lo scudo dà Shielding (1 punto/blocco, il dummy attacca ogni 2 s). 84 h di set Transcendent = **Distance 79→89 e Shielding 62→~68,7** (128k tries di shielding in più). Non allenare le due cose separatamente.
2. **Il tier cambia solo la velocità, non le tries per item.** Costo in item per livello = uguale per tutti i tier; Transcendent (1,5 s) = meno ore, e siccome lo **scudo si consuma a ritmo fisso (1.800 blocchi/h, dura 5,6 h)**, meno ore = meno scudi. Per +10 Distance: ~20 spear e ~15 scudi (Transcendent); a Charged ~103 h ≈ 18,5 scudi.
3. **I moltiplicatori dividono ore E item** (le cariche si consumano per azione, i moltiplicatori aumentano le tries per azione). Voucher ×2 (o evento skill, il più alto dei due), Mad Santa ×2, Global +10% → fino a ×4,4: 84 h → ~19 h e ~5 spear. Prima il boost, poi gli item.
4. **Rendimenti decrescenti forti.** Ogni +10 Distance costa ~2,6× il precedente per un guadagno di danno quasi costante: 79→89 = 343k tries (84 h) +11,2% danno; 89→99 = 890k (219 h) +10,1%; 99→109 = 2,31M (568 h) +9,2%. Oltre ~90 conviene alzare l'**Attack** (munizioni, attributi Attack/Critical/Distance) più che la skill. Shielding: 62→72 = 226k (149 h) +13,9% blocco; 72→82 = 587k (385 h) +12,2%.
5. **Perché Shielding conviene per il Paladin con scudo:** costa ~16k tries per +1% di blocco contro ~31k tries per +1% di danno della Distance. Su Hero da solo (shield + spears): +10 Shielding → danno subito −17%, +10 Distance → −15%, **entrambe → −29%** (cure 1,8 → 1,1 a kill). Il blocco però serve solo contro il fisico e con lo scudo in mano (con la crossbow la difesa è 0).
6. **Dummy vs caccia:** in caccia 1 try per colpo a segno (≤ 1.800/h); sul dummy col set 4.064 tries/h di Distance (≈ 2–4×) e 1.524 di Shielding, che da kiter in caccia quasi non alleni (blocchi rari). Ma 84 h di dummy = 84 h senza exp/loot (~42k exp/h al Dragon ≈ 3,5M exp): il training si paga quando la skill sblocca mostri nuovi o riduce rischio/cure, non "a prescindere".
7. **Magic Level è un sottoprodotto:** per il Paladin (mult 1,4) 15→16 costa 62k mana spesi (≈ 780 cure da 80 mana); non vale training dedicato (la wand è solo sorcerer/druid).
8. **Alternative alla skill pura:** attributi item Distance (+1…+5), Attack, Critical, Hit Chance (vedi skill, sezione Item Attributes) e artifact (Sniper Gloves ecc.) — spesso più rapidi di 84 h di dummy, ma costano Aether/gold.
9. **Dati ancora aperti:** prezzo/fonte dei Training Weapons, se i colpi che mancano consumano carica (sì: "each weapon attack, hit or miss"), quanti dummy ci sono e dove, se il Global Skill Gain +10% è attivo su Aeternum, hit chance reale della spear sul dummy.
