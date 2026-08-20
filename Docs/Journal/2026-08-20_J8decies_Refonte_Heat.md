# Journal — 2026-08-20 — J8decies — Refonte de la chaleur

**Temps effectif** : ~1 h (documentation seule)
**Objectif du jour (roadmap)** : aucun. Journée **hors roadmap** : transcrire dans la doc une décision
de design tranchée par Louis, **avant** que le J9 ne commence dans une autre session.

> **Aucun code, aucun Blueprint, aucun `.uasset` touché.** L'éditeur Unreal n'a pas été ouvert.
> Ce que raconte cette entrée, c'est une **décision** — pas une implémentation.

---

## Fait

- **`11_ARBITRAGES D58` posé** : *« la chaleur ne bloque plus rien : jauge de discipline de tir,
  payée en style »*. Le verrou de tir de `Heat_OverheatDuration` est **supprimé**.
- **`07_TUNING §11` refait** : 4 clés neuves, 6 marquées `INACTIVE` avec leur raison,
  `Heat_Max` / `Heat_WarningThreshold` / `Heat_TickInterval` conservées et actives.
  **`§14`** : `Style_Loss_Heat` ajoutée.
- **`SPEC_COMBAT §4` réécrit** : nouveau diagramme d'états, sources et puits, API, feedback.
  Le modèle à verrou devient une **note historique**. `§3.1` (`TryFire`), `§2`, `§6`, `§10`, `§12`
  alignés.
- **`SPEC_SCORE_RANK`** : nouveau `§4.2b` — le Style Meter gagne une source de perte **continue**,
  hors `E_StyleEvent`. Tableau des gains/pertes, §4.3, checklist et §11 alignés.
- **`SPEC_UI_HUD §3.3` réécrit** + nouveau `§3.3a` (affichage provisoire du coût). `§3.1.7`
  (crosshair) corrigé.
- **`08_DATA_SCHEMAS`** : sémantique d'`E_HeatState.Overheated`, et les 4 champs à ajouter à
  `PDA_WeaponData` au J9.
- **`04_ROADMAP` J9 réécrit**, et une ligne de **dette datée au J18** ajoutée des deux côtés (J9 et J18).

## Pas fait / reporté

- **Rien n'est implémenté.** Tout le travail d'asset est du **J9**, dans une autre session.
- **Back-port de D34 à D57 dans `11_ARBITRAGES.md`** : ces numéros ont été attribués pendant les
  J4→J8 mais rédigés dans `04_ROADMAP.md` et `07_TUNING.md`, jamais recopiés dans le fichier
  d'arbitrages. Constaté en cherchant le prochain numéro libre. **Signalé, pas corrigé** — hors
  périmètre de la décision du jour. Un encart de numérotation a été posé dans `11_ARBITRAGES.md`
  pour que le prochain agent ne réutilise pas un numéro déjà pris.
- **`S_Overheat_Deny` (`SPEC_AUDIO §2`)** : le son du clic refusé n'a plus d'objet, aucun tir n'étant
  refusé. **Non touché** — le sort d'une entrée du catalogue SFX relève de `SPEC_AUDIO`, pas de D58.
  À trancher avec Louis.

## Décisions prises

> Toute décision qui n'était pas dans la doc. Elle doit être répercutée dans le fichier concerné.

| Décision | Fichier de doc mis à jour |
|---|---|
| **D58** — l'overheat ne bloque plus le tir ; la chaleur devient une jauge de discipline de tir dont la seule conséquence est une perte de style | `11_ARBITRAGES.md` |
| Montée **uniquement sur les tirs ratés** ; un tir qui touche ne chauffe pas, un body shot ne fait rien bouger | `07_TUNING §11`, `SPEC_COMBAT §3.1`/`§4.1` |
| **Aucune décroissance passive** : le refroidissement se mérite (headshot, ou vitesse) | `07_TUNING §11`, `SPEC_COMBAT §4.2` |
| `Heat_CoolSpeedThreshold` = **le même seuil** que `Style_Gain_HighSpeedSustain`, volontairement | `07_TUNING §11`/`§14`, `SPEC_SCORE_RANK §4.2b` |
| Conséquence = **perte de style**, pas de canal de score séparé | `SPEC_SCORE_RANK §4.2b` |
| Le J9 livre un **affichage provisoire du coût réel** (`STYLE −0.20/s`), pas un pourcentage inventé | `SPEC_UI_HUD §3.3a`, `04_ROADMAP` J9 |
| `E_HeatState` **conservé tel quel** ; seule la sémantique d'`Overheated` change | `08_DATA_SCHEMAS §1` |
| 6 clés passées `INACTIVE`, **conservées** dans `PDA_WeaponData` / `DA_Weapon_Laser`, lues par personne | `07_TUNING §11`, `08_DATA_SCHEMAS §3` |
| Le vrai câblage de `Style_Loss_Heat` est une **dette datée au J18** | `04_ROADMAP` J9 **et** J18 |

## Valeurs modifiées

| Clé | Ancien | Nouveau | Raison |
|---|---|---|---|
| `Heat_PerMissedShot` | — | **11** `[À CALIBRER]` | **neuve.** Remplace `Heat_PerShot`. Seuls les tirs **ratés** chauffent |
| `Heat_CoolPerHeadshot` | — | **25** `[À CALIBRER]` | **neuve.** Puits événementiel : le rachat est un acte de précision |
| `Heat_CoolRateAtSpeed` | — | **20 /s** `[À CALIBRER]` | **neuve.** Puits continu, actif au-dessus du seuil de vitesse |
| `Heat_CoolSpeedThreshold` | — | **3000 uu/s** `[À CALIBRER]` | **neuve.** Volontairement égale au seuil de `Style_Gain_HighSpeedSustain` |
| `Style_Loss_Heat` | — | **−0.20 /s** `[À CALIBRER]` | **neuve** (`§14`). Appliquée tant que `CurrentHeat >= Heat_WarningThreshold` |
| `Heat_PerShot` | 11 | ⛔ **INACTIVE** | remplacée par `Heat_PerMissedShot` |
| `Heat_DecayRate` | 45 /s | ⛔ **INACTIVE** | plus de décroissance passive |
| `Heat_DecayDelay` | 0.5 s | ⛔ **INACTIVE** | plus de décroissance passive, donc plus de délai |
| `Heat_OverheatDuration` | 1.5 s | ⛔ **INACTIVE** | **c'était le verrou.** Supprimé |
| `Heat_OverheatExitThreshold` | 25 | ⛔ **INACTIVE** | plus de verrou, donc plus de sortie à conditionner |
| `Heat_OverheatDecayMultiplier` | 1.5 × | ⛔ **INACTIVE** | multipliait une décroissance qui n'existe plus |

`Heat_Max` (100), `Heat_WarningThreshold` (75) et `Heat_TickInterval` (0.05 s) sont **inchangées et
actives**. Aucune valeur n'a été supprimée de `07_TUNING`.

## Ressenti de playtest

> Le plus important. Ce que le jeu fait *sentir*, pas ce qu'il fait techniquement.

- **Aucun playtest aujourd'hui** — il n'y avait rien à jouer. La décision ne vient pas d'une manche
  mais d'une **relecture** : `SPEC_COMBAT §1` interdit noir sur blanc que le combat interrompe le
  mouvement, et le verrou de 1,5 s était **la seule interruption du jeu**. La spec se contredisait
  elle-même depuis la préproduction.
- Ce que le verrou aurait produit, et qui a suffi à le condamner sans le construire : à 3000 uu/s,
  1,5 s d'arme muette pousse le joueur à **arrêter de tirer en avance** pour garder de la marge —
  c'est-à-dire à faire de la **comptabilité de munitions**, l'interdit explicite du même §1
  (*« Munitions = rythme, pas gestion »*).
- Le renversement tient en une phrase : la chaleur ne dit plus **« attends »**, elle dit
  **« tu arroses »**. Elle ne coûte plus du **temps** (la ressource sur laquelle le jeu est fier),
  elle coûte du **style** (la ressource sur laquelle le joueur est fier).
- **Ce qui reste à sentir manche en main au J9**, et que je ne peux pas juger (R8) : est-ce que
  refroidir *se mérite* sans devenir punitif ? Sans décroissance passive, un joueur qui rate
  beaucoup et roule lentement reste chaud longtemps. Les deux curseurs sont
  `Heat_CoolPerHeadshot` et `Heat_CoolRateAtSpeed`, à regarder **avant** de toucher à la montée.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| **`11_ARBITRAGES.md` s'arrête à D33 alors que D34–D57 sont attribués** dans `04_ROADMAP.md` et `07_TUNING.md` — un agent qui lit le seul fichier d'arbitrages pour trouver le prochain numéro libre poserait un **D34 en doublon** | 🟠 doc | **Contourné** : D58 vérifié par `grep` sur tout `Docs/`, et un encart de numérotation posé dans `11_ARBITRAGES.md`. **Le back-port des 24 entrées reste à faire** |
| `S_Overheat_Deny` / `PDA_WeaponData.DenySFX` : un son et un champ pour un clic refusé qui n'existe plus | ⚪ | **Signalé, non corrigé** (hors périmètre D58) |

## Demain

- **J9, dans une autre session.** L'ordre d'attaque est dans `04_ROADMAP` J9 :
  `PDA_WeaponData` (+4 champs, **0 suppression**) → `DA_Weapon_Laser` → `BPC_Heat` →
  `TryFire` (retirer la gate) → `MPC_Global.HeatRatio` → `WBP_HeatBar` + affichage du coût.
- **Le piège à ne pas refaire** : au J9, un `BPC_Heat` qui lirait `WeaponData.HeatDecayRate`
  (clé `INACTIVE`) **compilerait sans le moindre warning**, et la jauge aurait l'air de marcher.
  C'est la famille `12_PIEGES §6.24` — une valeur qui ne pilote rien et qu'on croit régler.
  Relire les clés lues par `BPC_Heat` **une par une** avant de conclure.
- **R10** : rien ne se commite avant que Louis ait joué la jauge.

---

## Vérifications de fin de journée

- [x] Tous les BP recompilés, zéro warning — *sans objet, aucun Blueprint touché*
- [x] 3 minutes de jeu réel — *sans objet, rien de jouable n'a changé*
- [x] Roadmap cochée — J9 réécrit, dette J18 posée des deux côtés
- [x] Tuning à jour — `§11` refait, `§14` complétée
- [x] Cohérence croisée vérifiée sur les 8 fichiers : **aucune mention résiduelle de tir bloqué**
- [ ] Commit fait — **c'est Louis qui commite**
