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
      → `LevelPrototyping/Materials|Textures|Meshes` conservés, seul `Interactable/` supprimé.
      **D1 validée par Louis le 2026-08-18**, **exécutée le 2026-08-19 après le J4** : les 16 assets
      restants de `LevelPrototyping/` sont supprimés. `Content/` ne contient plus que `OVERDRIVE/`.
      → `Content/Input/` **supprimé au J2** (9 assets : 4 `IA_*`, 2 `IMC_*`, 3 assets tactiles) :
      doublons de nom avec `OVERDRIVE/Player/Input/`, l'éditeur se liait au mauvais asset.
      Zéro référence entrante. Cf. journal J2 D9.
- [x] Créer `GM_Overdrive`, `GS_Overdrive`, `PC_Overdrive`, `GI_Overdrive`, `PS_Overdrive`
- [x] Créer `BP_PlayerCharacter` (capsule, caméra, bras FP placeholder)
- [x] Configurer les canaux de collision et presets (`Docs/06_CONVENTIONS.md §7`)
- [x] Créer tous les Enums (`Docs/08_DATA_SCHEMAS.md §1`)
      → Assets créés par outil, **entrées saisies à la main par Louis** : aucun outil
      (52 toolsets MCP + API Python UE) ne sait écrire les entrées d'un `UserDefinedEnum`.
      `E_MovementState` / `E_HeatState` / `E_Rank` au J1, **les 10 autres au J2**.
      **Les 13 sont complets et conformes à `08_DATA_SCHEMAS §1`** (vérifié entrée par entrée)
- [x] Créer `IMC_Gameplay` + toutes les `IA_*` (`Docs/09_INPUT.md`)
- [x] Créer `L_Sandbox_Movement` vide avec un sol de 20000 uu
- [x] Réglages projet : DefaultMap, GameMode, gravité, `MaxStepHeight`
      → `Gravity` et `MaxStepHeight` sont des réglages du **CMC** de `BP_PlayerCharacter`
      (`Gravity` = multiplicateur `×G`), pas des réglages projet
- [x] **Ne pas toucher aux réglages de rendu** — Lumen et VSM restent actifs (`Docs/11_ARBITRAGES.md D2`)

### J2 — Vitesse & sprint  *(commencé le 2026-08-18)*
- [x] `PDA_MovementData` + `DA_Movement_Default` (toutes les valeurs de `Docs/07_TUNING.md`)
      → 70 propriétés `Instance Editable`, miroir de `07_TUNING §2–§10`.
      `MaxHealth` exclu volontairement : il appartient à `BPC_Health` (`05_ARCHITECTURE`)
- [x] `BPC_MovementState` : machine à états, vitesse interne, momentum, décroissance
      → 34 variables, 6 dispatchers, 24 fonctions, boucle de Tick complète
      (grounded → **résolution d'état** → cap → grace → décroissance → pilotage CMC →
      hard clamp → broadcast → debug), `CacheTuning` au `BeginPlay`,
      `AddTickPrerequisiteComponent(CMC)`.
      → Machine à états : table `§1.3` complète en `Switch on E_MovementState` imbriqué,
      `RequestState` / `CanEnterState` / `GetCurrentState` / `ResolveState`.
      Les 6 éléments typés enum ont été **créés à la main par Louis** (aucun outil MCP ne
      sait le faire, cf. journal J2).
      → La décroissance est gardée par l'état `{Idle, Walking, Sprinting}` (`IsDecayAllowedState`)
- [x] Sprint — rampe `Speed_Walk → Speed_SprintCap` en `Sprint_TimeToMax` (`FInterpTo Constant`),
      garde `Sprint_RequiresForwardInput`, cap figé en l'air (`SPEC_MOVEMENT §3`)
- [x] Overlay debug à l'écran : état, vitesse, cap, grace, sol, dernier gain, état du CMC
- [x] Câblage input `BP_PlayerCharacter` (hors J2 à l'origine, mais rien n'est testable sans) :
      `IA_Move`, `IA_Look`, `IA_Walk`, `IA_DebugToggle` + `AddMappingContext` au `BeginPlay`
- [x] **Test** : le sprint plafonne bien à `Speed_SprintCap`
      → validé par Louis le 2026-08-19 : marche 1000, sprint 1500, **sans à-coup**,
      pas de sprint en marche arrière, cap qui redescend au relâchement. Aucune valeur retunée.

> **Prérequis enums : levé.** Les **13 enums** de `08_DATA_SCHEMAS §1` sont remplis et vérifiés
> entrée par entrée (les 10 derniers saisis par Louis au J2). Plus rien ne bloque côté données
> jusqu'aux Structs du J10.

### J3 — Saut & air control  *(implémenté le 2026-08-19, cf. `Docs/Journal/2026-08-19_J3_JumpAirStrafe.md`)*
- [x] Jump + coyote time + jump buffer
      → `TryJump` / `DoJump` / `HandleLanded` / `UpdateJumpTimers` dans `BPC_MovementState`.
      `Set Velocity` + `SetMovementMode(Falling)`, jamais `Launch Character` (`SPEC_MOVEMENT §15`).
      `CanEnterState` : **`Falling → Jumping` passe de refusé à autorisé** — c'est l'exception
      « sauf coyote time » de la note ⁴ de `SPEC_MOVEMENT §1.3`. Le garde-fou anti-double-saut
      reste `bJumpConsumed`, pas la table d'états.
- [x] Air strafing (modèle Quake, `Docs/Specs/SPEC_MOVEMENT.md §7`)
      → `ApplyAirStrafe(DeltaSeconds)`, inséré à l'**étape 7 du Tick** entre `DriveCMC` et
      `ClampToHardCap`. `Tune_AirStrafeGainAngleCos` = `cos(90 + GainAngleMax)` précalculé au
      `BeginPlay` (vérifié en PIE : **−0.7071** = cos 135°).
- [x] Conservation de la vitesse à l'atterrissage
      → `SpeedRetention_Landing` appliqué **explicitement** sur `Velocity.XY` dans `HandleLanded`,
      + `StartGrace(MomentumDecay_GraceTime)` pour que la décroissance ne mange pas le momentum
      dans la frame qui suit le contact (**décision D13**).
- [x] **Test** : gagner de la vitesse en strafant en l'air est perceptible et apprenable
      → **validé par Louis le 2026-08-19** au 3ᵉ playtest : « le straf me paraît correct ».
      A demandé 3 correctifs : le gain était effacé chaque frame (`DriveCMC` avant l'air strafe),
      les constantes étaient à l'échelle de Quake et non de la nôtre, et surtout le **modèle** était
      le mauvais — Quake 1/CPMA (touche latérale seule) au lieu de **Quake 3** (diagonale + souris).
      `AirStrafe_WishSpeedCap = Speed_SprintCap` : **première valeur `VALIDÉ` du projet.**
- [x] **Bonus** — le buffer de saut (`Jump_BufferTime`) était détruit par le CMC à chaque
      atterrissage (`SetPostLandedPhysics` remet `Velocity.Z` à 0). Sorti d'`OnLanded` vers
      `ConsumeBufferedJump()` dans le Tick. Le bunny hop du J7 en dépendait.

> **Le J3 a coûté 3 régressions**, toutes dues à un outil qui échoue en silence.
> D'où `Docs/12_PIEGES_OUTILLAGE.md` (registre des pièges, **obligatoire** — R9) et la règle
> **R10** : on ne commite pas une feature de gameplay avant que Louis l'ait jouée.

> **Correctif hors J3 :** `ClampToHardCap` n'écrivait que la variable `HorizontalSpeed`, jamais la
> vélocité du CMC — le `Speed_HardCap` n'était donc **jamais** appliqué. Corrigé au J3, avant que
> l'air strafe ne devienne la première mécanique capable de dépasser le cap.

### J4 — Slide  *(implémenté le 2026-08-19, cf. `Docs/Journal/2026-08-19_J4_Slide.md`)*
- [x] `BPC_Slide` : entrée, resize capsule, `CanUncrouch()`, friction, boost, pentes, timer
      → composant **autonome** : 30 variables, 15 fonctions, aucune modification de `BPC_MovementState`.
      Tick inséré **avant** lui par `AddTickPrerequisiteComponent` depuis son propre `BeginPlay` (**D22**),
      ce qui satisfait la règle du J3 (`12_PIEGES_OUTILLAGE §6.1`) sans toucher au code validé.
      → resize capsule = **`Crouch()` / `UnCrouch()` du CMC** (D21) ; `CanUncrouch()` s'appuie sur le test
      d'encroachment que le moteur fait déjà (**D17**) ; friction appliquée **par nous** en décroissance
      exponentielle, `CMC.GroundFriction = 0` pendant le slide (**D18**) ; bonus de pente **mis à l'échelle
      par `SlopeDot`**, friction suspendue en descente (**D19**).
      → **Vérifié en PIE** : composant instancié, `CacheTuning` a lu les 13 valeurs correctes,
      `CrouchedHalfHeight = 44`, `MaxWalkSpeedCrouched = 6000`, **et le composant tick**.
- [x] Enchaînements `Sprint → Slide` et `Sprint → Slide → Jump`
      → `IA_Slide` (`Ctrl`) câblé en `Started` / `Completed` vers `SetSlideInput`, avec **détection de front**.
      Le saut pendant un slide n'est **jamais refusé** (**D20**). Slide d'atterrissage réparé : le buffer
      est retenté chaque frame au lieu d'être consommé une fois (`12_PIEGES_OUTILLAGE §6.7`).
      → **Correctif après le 1ᵉʳ playtest** : `Ctrl` ne déclenchait **jamais** rien — un nœud `Get` pure
      était évalué *après* le `Set` qui l'écrasait, rendant la détection de front toujours fausse
      (`12_PIEGES_OUTILLAGE §2.3b`). Au passage, `write_graph_dsl` avait empilé **80 nœuds orphelins**
      sur deux graphes de **fonction**, ce que le registre disait impossible (`§2.2b`) — purgés, audit
      des 3 Blueprints propre.
      → **D23** : le slide ne dépend plus du sprint. `Idle → Sliding` et `Walking → Sliding` ouverts dans
      `CanEnterState` (62 autres transitions inchangées, vérifiées par diff). La **vitesse est la seule
      garde** ; sous `Slide_MinEntrySpeed` on fait un **crouch simple**.
      → **D24, refonte après le 2ᵉ playtest** : « trop grand boost sans aucun effort, 0 difficulté ».
      **Le slide ne crée plus de vitesse sur le plat, il la conserve** — `Slide_EntryBoost` 400 → **0**,
      conservation stricte pendant `Slide_HoldTime` (1 s) puis décroissance. La vitesse ne vient que
      des **pentes**, par accélération **vectorielle vers l'aval** mise à l'échelle par `sin(pente)` :
      on glisse d'une rampe à l'arrêt sans presser l'avant. Rejoindre une pente réarme la fenêtre.
      `MaxWalkSpeedCrouched` réécrit chaque frame à la vitesse courante → **impossible d'accélérer
      accroupi**, et **virage à 180° à vitesse constante** (la vraie valeur de la mécanique).
      → **D26, 3ᵉ passe** : le virage ne passe plus par `MaxAcceleration` (1.25 s pour un demi-tour à
      2500 uu/s — d'où le patinage) mais par une **rotation angulaire du vecteur vitesse** vers le
      regard, à `Slide_TurnRate` = 720 °/s → **demi-tour en 0.25 s, norme conservée**.
      Au passage : `BPC_Slide` n'avait **aucun prérequis de tick sur le CMC**, l'ordre
      `CMC → Slide → MovementState` n'était donc pas garanti. Corrigé.
      → **D25 — on court par défaut, `Maj` fait marcher.** Inversion dans
      `BP_PlayerCharacter.SetWalkInput` + init au `BeginPlay` (sinon on marche jusqu'au 1ᵉʳ appui).
      `IA_Walk` porte un nom devenu trompeur : renommage en `IA_Walk` **à valider par Louis**.
      → **D27, 4ᵉ passe** : « ça decay trop vite ». Le vrai problème était un **softlock** —
      `MaxWalkSpeedCrouched` piloté à 0 hors slide bloquait totalement le joueur coincé sous un
      plafond bas. Plancher à `Speed_Walk` quand `bForcedSlide`. Retune :
      `Slide_Friction` 0.4 → **0.15**, `Slide_MaxDuration` 1.2 → **3.0** → un slide à 1500 uu/s
      couvre ~3500 uu, le tunnel de la zone B en fait 4000.
      → **5ᵉ passe** : `GetFloorNormal` **ratait le sol dès 30°** — portée calibrée sur la capsule
      accroupie (94 uu) alors que sous le centre d'une capsule sur pente le sol est à 102 uu à 45°.
      La normale retombait sur `(0,0,1)` : **aucune pente n'existait**, ni accélération en descente ni
      freinage en montée. Portée → `CapsuleHalfHeight + MaxStepHeight` = 138 uu (`12_PIEGES §6.8`).
      → **D28** : `IsCeilingBlocked()` — **pas de saut** quand un plafond bas bloque le dé-crouch.
      → **D29** : `CrouchStep` — accroupi sans slider, l'accélération de pente s'applique quand même
      et `TryStartSlide` est retenté chaque frame. **On ne peut plus jamais être figé sur une pente.**
- [x] **Zone de test pentes + plafond bas dans le sandbox** — *fait en amont le 2026-08-19*
      → Zone B (tunnel 4000 × 1000, intérieur **130 uu**) et Zone C (rampes 15/30/45°, pente 1600 uu,
      chacune vers un plateau). Géométrie vérifiée par trace physique. Détail : `SPEC_MOVEMENT §13.2`.
- [x] **Test** : le slide donne envie d'être enchaîné, jamais subi
      → **validé par Louis le 2026-08-19** au 5ᵉ playtest : « tout me paraît bon ».
      Le modèle a été refondu **deux fois** en cours de journée sur son retour manche en main :
      d'abord « trop grand boost sans aucun effort, 0 difficulté » (→ `D24`, le slide conserve
      au lieu de créer), puis « je glisse sur le sol, pas de demi-tour serré » (→ `D26`, virage
      angulaire). C'est exactement la boucle `10_DEFINITION_OF_DONE §2`.
- [x] **Après le J4** : supprimer `Content/LevelPrototyping/` (décision D1, validée le 2026-08-18)
      → **exécutée le 2026-08-19.** Référenceurs revérifiés **un par un juste avant** la suppression
      (et non sur la foi de l'audit de la veille) : 16 assets, **zéro référence externe**, uniquement
      des renvois internes entre matériaux et meshes du dossier.
      `Content/` ne contient plus que `OVERDRIVE/` — conforme à **R6**.
      Vérifié en PIE après coup : le sandbox charge sans une seule référence manquante.
- [x] **Renommage `IA_Sprint` → `IA_Walk`** (le nom mentait depuis `D25`)
      → `IMC_Gameplay` a suivi tout seul. **L'event node a dû être recréé** : sa classe générée
      restait `EnhancedInputActionIA_Sprint` même après le renommage de l'asset.
      Fonction `BP_PlayerCharacter.SetSprintInput` → **`SetWalkInput`** (pas d'outil de renommage :
      nouvelle fonction, 3 sites d'appel recâblés, ancienne supprimée).

> **Dette du J3 levée en amont** : la garde de décroissance sur l'état (`IsDecayAllowedState`) était
> annoncée manquante par le journal J2 — elle existait déjà et fonctionne. Note corrigée.
> Rien à rebrancher. En revanche `BPC_Slide` écrit `Velocity` : il doit s'exécuter **avant**
> `DriveCMC` dans le Tick (`SPEC_MOVEMENT §7.4`, `12_PIEGES_OUTILLAGE §6.1`).

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
