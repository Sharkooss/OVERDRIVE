# 04 — ROADMAP

> **Budget : 4 semaines × ~20 h = ~80 h.** Jour = **~3 h de travail effectif**.
> Coche les cases au fur et à mesure. Un jour non terminé se reporte, il ne se supprime pas :
> c'est le **scope** qui se réduit (`Docs/03_SCOPE_LOCK.md §6`), jamais la qualité du core.

**Démarrage : 2026-08-18.**

Légende : `[ ]` à faire · `[~]` en cours · `[x]` fait · `[!]` bloqué · `[-]` coupé du scope

---

## SEMAINE 0 — Setup (fait)

- [x] Projet UE 5.8 créé, template First Person
- [x] Structure de dossiers `Content/OVERDRIVE/`
- [x] Documentation complète `Docs/`
- [x] Règles agents `CLAUDE.md` + `.claude/`
- [x] Nettoyage du template (voir J1)
- [x] Dépôt git initialisé + premier commit

---

## SEMAINE 1 — MOVEMENT PROTOTYPE

> **Objectif** : un graybox où on peut se déplacer 10 minutes sans s'ennuyer.
> **Critère DONE** : le mouvement est déjà fun **sans aucun ennemi**.

### J1 — Fondations ✅ (2026-08-18, cf. `Docs/Journal/2026-08-18_J1_Fondations.md`)
- [x] Supprimer `Content/FirstPerson`, `Content/Characters`, `Content/LevelPrototyping` (garder `Input/` et les matériaux de grid le temps du blockout)
      → `LevelPrototyping/Materials|Textures|Meshes` conservés, seul `Interactable/` supprimé (décision D1 du journal, **à valider**)
- [x] Créer `GM_Overdrive`, `GS_Overdrive`, `PC_Overdrive`, `GI_Overdrive`, `PS_Overdrive`
- [x] Créer `BP_PlayerCharacter` (capsule, caméra, bras FP placeholder)
- [x] Configurer les canaux de collision et presets (`Docs/06_CONVENTIONS.md §7`)
- [!] Créer tous les Enums (`Docs/08_DATA_SCHEMAS.md §1`)
      → **13 assets créés mais VIDES.** Aucun outil (52 toolsets MCP + API Python UE)
      ne sait écrire les entrées d'un `UserDefinedEnum`. **Saisie manuelle requise
      avant le J2** — liste ordonnée dans `08_DATA_SCHEMAS §1`
- [x] Créer `IMC_Gameplay` + toutes les `IA_*` (`Docs/09_INPUT.md`)
- [x] Créer `L_Sandbox_Movement` vide avec un sol de 20000 uu
- [x] Réglages projet : DefaultMap, GameMode, gravité, `MaxStepHeight`
      → `Gravity` et `MaxStepHeight` sont des réglages du **CMC** de `BP_PlayerCharacter`
      (`Gravity` = multiplicateur `×G`), pas des réglages projet
- [x] **Ne pas toucher aux réglages de rendu** — Lumen et VSM restent actifs (`Docs/11_ARBITRAGES.md D2`)

### J2 — Vitesse & sprint
- [ ] `PDA_MovementData` + `DA_Movement_Default` (toutes les valeurs de `Docs/07_TUNING.md`)
- [ ] `BPC_MovementState` : machine à états, vitesse interne, momentum, décroissance
- [ ] Sprint
- [ ] Overlay debug à l'écran : état, vitesse, cooldowns
- [ ] **Test** : le sprint plafonne bien à `Speed_SprintCap`

### J3 — Saut & air control
- [ ] Jump + coyote time + jump buffer
- [ ] Air strafing (modèle Quake, `Docs/Specs/SPEC_MOVEMENT.md §7`)
- [ ] Conservation de la vitesse à l'atterrissage
- [ ] **Test** : gagner de la vitesse en strafant en l'air est perceptible et apprenable

### J4 — Slide
- [ ] `BPC_Slide` : entrée, resize capsule, `CanUncrouch()`, friction, boost, pentes, timer
- [ ] Enchaînements `Sprint → Slide` et `Sprint → Slide → Jump`
- [ ] Zone de test pentes + plafond bas dans le sandbox
- [ ] **Test** : le slide donne envie d'être enchaîné, jamais subi

### J5 — Dash
- [ ] `BPC_Dash` : direction 360°, charges, cooldown, conservation de vitesse
- [ ] Feedback provisoire (FOV kick + son placeholder)
- [ ] **Test** : le dash sert à corriger une trajectoire, pas à aller vite

### J6 — Wall ride
- [ ] `BPC_WallRide` : détection, accroche, maintien, wall jump, cooldown same-wall
- [ ] Object type `WallRideSurface` + un mur de test
- [ ] Zone sandbox : 2 murs opposés, 3 murs en escalier
- [ ] **Test** : enchaîner 3 murs consécutivement est possible et satisfaisant

### J7 — Bunny hop & intégration
- [ ] Bunny hop : fenêtre de timing, skip de friction, gain, plafond
- [ ] Matrice d'interactions validée (`Docs/Specs/SPEC_MOVEMENT.md §11`)
- [ ] Parcours sandbox complet enchaînant les 7 mécaniques
- [ ] Premier passage de tuning avec Louis
- [ ] **🚦 GATE SEMAINE 1** — cf. `Docs/10_DEFINITION_OF_DONE.md §3`

---

## SEMAINE 2 — COMBAT + JUICE

> **Objectif** : courir → tirer → headshot → melee → projeter un ennemi → dash → wall ride → continuer.

### J8 — Laser
- [ ] `PDA_WeaponData` + `DA_Weapon_Laser`
- [ ] `BP_LaserWeapon` : trace, origine caméra + VFX muzzle, dégâts, portée
- [ ] Cibles de test dans le sandbox
- [ ] **Test** : tirer en courant est naturel

### J9 — Heat & overheat
- [ ] `BPC_Heat` : machine à états, décroissance, délai, overheat, sortie
- [ ] Feedback provisoire (barre debug + son)
- [ ] **Test** : le rythme tirer/refroidir est lisible sans regarder le HUD

### J10 — Headshots & feedback
- [ ] Hitboxes de tête, détection, multiplicateur
- [ ] Hitmarker, hit-stop, son distinct
- [ ] `BPI_Damageable` + `S_DamageInfo`
- [ ] **Test** : un headshot procure une vraie satisfaction (Test 4)

### J11 — Melee & wall slam
- [ ] `BPC_Melee` : sphere trace, montage, cooldown
- [ ] Knockback + `BPC_KnockbackReceiver`
- [ ] Détection d'impact mural + dégâts
- [ ] **Test** : écraser un ennemi contre un mur est la meilleure sensation du jeu

### J12 — Ennemi de base
- [ ] `BPC_Health`, `BP_EnemyBase`, `PDA_EnemyData`
- [ ] Mort, dissolve, notification de score
- [ ] Système d'activation par distance (`BP_LevelManager` provisoire)

### J13 — Grunt & Shooter
- [ ] `BP_Enemy_Grunt` + FSM
- [ ] `BP_Enemy_Shooter` + StateTree + `BP_EnemyProjectile`
- [ ] `DA_Enemy_Grunt`, `DA_Enemy_Shooter`
- [ ] **Test** : un projectile est évitable à 3000 uu/s (Test 5)

### J14 — Premier passage de juice
- [ ] FOV dynamique + `CF_FOVBySpeed`
- [ ] Camera tilt, camera shakes `CS_*`
- [ ] `NS_LaserImpact`, `NS_Muzzle`, `NS_Headshot`, `NS_EnemyDeath`, `NS_Dash`
- [ ] SFX placeholder sur toutes les actions P0
- [ ] `MPC_Global` + speed lines
- [ ] **🚦 GATE SEMAINE 2**

---

## SEMAINE 3 — VERTICAL SLICE

> **Objectif** : 1 niveau complet + boss + scoring + loot, jouable du début à la fin.

### J15 — Blockout Level 01
- [ ] Kit modulaire minimal (`SM_Module_*`, `Docs/Specs/SPEC_LEVELDESIGN.md §3`)
- [ ] Blockout complet de `L_W1_01_Ignition`
- [ ] `BP_LevelManager`, `BP_LevelEndTrigger`, `BP_Checkpoint`

### J16 — Espaces de vitesse
- [ ] Sections de vitesse + corridors de wall ride
- [ ] Une bifurcation Safe Way / Speed Way
- [ ] **Test** : traverser le niveau sans tirer est déjà agréable

### J17 — Sections de combat
- [ ] `BP_Enemy_Tank` + `DA_Enemy_Tank`
- [ ] Placement des ennemis du niveau 01
- [ ] **Test** : il vaut mieux tuer en mouvement qu'à l'arrêt (Test 3)

### J18 — Scoring
- [ ] `BPC_ScoreManager` : temps, kills, vitesse, `S_LevelScore`
- [ ] `BPC_StyleMeter` + `DT_StyleEvents`
- [ ] Affichage temps réel du style

### J19 — Rank, résultats & vies
- [ ] Calcul du rank, `S_RankThresholds`, `PDA_LevelData`
- [ ] `WBP_HUD` complet + `WBP_LivesCounter`
- [ ] `WBP_Results` + comparaison S RANK vs YOUR RUN
- [ ] Système de vies : `Run_MaxLives`, `ConsumeLife()`, `WBP_RunFailed` (`11_ARBITRAGES D1/D31`)
- [ ] Calibration des seuils du niveau 01
- [ ] **Test** : on comprend en 2 s pourquoi on a eu A et pas S (Test 6)

### J20 — Loot & upgrades
- [ ] `PDA_UpgradeDefinition` + le catalogue d'upgrades
- [ ] `DT_LootTable_D` → `_S`
- [ ] `BP_LootChest` + algorithme de tirage
- [ ] `BPC_UpgradeManager` + `BPC_PlayerStats`
- [ ] `WBP_LootChest`
- [ ] **Test** : le loot donne envie de continuer (Test 7)

### J21 — Boss prototype
- [ ] `BP_BossBase` : phases, barre de vie, arène
- [ ] `BP_Boss_01` prototype jouable, 3 attaques
- [ ] `L_W1_Boss` blockout
- [ ] **🚦 GATE SEMAINE 3** — le jeu se joue du début à la fin

---

## SEMAINE 4 — PRODUCTION + POLISH

> **Objectif** : le contenu. À ce stade on ne crée plus de système, on remplit.
> **Toute nouvelle idée de système va au backlog. Sans exception.**

### J22 — Finalisation Level 01
- [ ] Passe de polish complète sur `L_W1_01`
- [ ] Toon shader + matériaux appliqués
- [ ] `L_W1_01` sert de **référence de qualité** pour tous les autres

### J23 — Level 02
- [ ] Blockout + ennemis + seuils de rank
- [ ] Thème : grandes sections de vitesse

### J24 — Level 03
- [ ] Blockout + ennemis + seuils de rank
- [ ] Thème : movement + combat combinés

### J25 — Boss 01
- [ ] Finalisation du Boss 01 : 2 phases, VFX, SFX, arène habillée

### J26 — Level 04
- [ ] Thème : movement avancé. World 2, nouvelle palette

### J27 — Level 05
- [ ] Thème : vitesse optimisée, raccourcis exigeants

### J28 — Level 06 + Boss 02
- [ ] `L_W2_06` gauntlet final
- [ ] `BP_Boss_02` prototype
- [ ] Menus : `WBP_MainMenu`, `WBP_Settings`, `WBP_Pause`
- [ ] Chaînage complet de la run, de bout en bout
- [ ] **🚦 GATE FINALE**

---

## POST-PRODUCTION (jours restants)

Par ordre de priorité (`Docs/10_DEFINITION_OF_DONE.md §4`) :

1. **Movement** — dernière passe de tuning
2. **Combat** — équilibrage TTK, heat, headshots
3. **Audio** — remplacer tous les placeholders, mix
4. **VFX** — passe P1/P2
5. **Camera** — shakes, transitions, confort
6. **Level design** — seuils de rank de tous les niveaux, raccourcis
7. **UI** — polish, animations, DPI
8. **Art secondaire** — props, éclairage, décor
9. **Optimisation** — profiling, 60 fps stable
10. **Bugs**

---

## Suivi hebdomadaire

| Semaine | Heures prévues | Heures réelles | Gate passée ? | Décision de scope |
|---|---|---|---|---|
| S1 | 20 h | | | |
| S2 | 20 h | | | |
| S3 | 20 h | | | |
| S4 | 20 h | | | |

---

## Risques et parades

| Risque | Signal d'alerte | Parade |
|---|---|---|
| Movement trop compliqué | J7 pas atteint | Couper bunny hop, garder les 6 autres |
| Vitesse illisible | Impossible d'anticiper les obstacles | Baisser `Speed_HardCap`, élargir les espaces |
| Level design trop long | > 4 h pour un niveau | Réduire à 90 s, réutiliser des patterns |
| Trop de contenu | S4 J24 en retard | Passer au Repli 1 ou 2 (`Docs/03_SCOPE_LOCK.md §6`) |
| Loot trop complexe | Plus de 2 h sur l'algorithme | Retirer les modificateurs, garder les stats pures |
| Le joueur ignore les ennemis | Test 3 échoue | Augmenter le poids des kills dans le score |
| Le joueur s'arrête pour tirer | Test 7 échoue | Baisser le TTK, augmenter les gains de style en mouvement |
| **Perf : le rendu éclairé coûte trop cher** | < 60 fps sur un niveau chargé | Réduire `Dynamic Shadow Distance`, passer les meshes en `Static`, baisser la qualité Lumen. **Nouveau risque n°1 depuis la DA v2** |
| **Les 3 vies bloquent le joueur** | Il n'ose plus prendre la ligne rapide | Monter `Run_MaxLives` ou activer `Run_LivesRefillOnBoss` (`07_TUNING §18`) |
