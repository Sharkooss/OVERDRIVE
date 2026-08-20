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

### J5 — Dash  *(implémenté le 2026-08-19, cf. `Docs/Journal/2026-08-19_J5_Dash.md`)*
- [x] `BPC_Dash` : direction 360°, charges, cooldown, conservation de vitesse
      → composant **autonome** : 32 variables, 15 fonctions, `EventGraph` de 8 nœuds, 1 dispatcher
      (`OnDashPerformed`). Zéro modification du Tick de `BPC_MovementState`, comme `BPC_Slide` (D22).
      → **D32 — il tick APRÈS `BPC_MovementState`**, l'inverse du slide : le dash doit avoir le dernier
      mot sur la vélocité. Il écrit lui-même `MaxWalkSpeed`, donc ni `ApplyAirStrafe` ni `ClampToHardCap`
      ni `DriveCMC` ne peuvent le contredire — c'est ce qui implémente « air strafe pendant dash :
      désactivé » (`SPEC_MOVEMENT §11`) **sans toucher au code validé du J3**.
      → **D30 — le dash conserve la norme, il ne la crée pas.** On voyage à 5625 uu/s pendant 0.16 s,
      mais on **ressort à sa vitesse d'entrée** (plancher `Dash_MinExitSpeed`). Le dash est une
      **réorientation 360° à vitesse conservée**, pas une source de vitesse (GDD §13).
      → **D31 — pas de `GravityScale`** : `DriveCMC` la réécrit chaque frame. L'apesanteur vient de la
      réécriture complète du vecteur vélocité. `Dash_GravityScale` passe **INACTIVE**.
- [x] Feedback provisoire (FOV kick + son placeholder)
      → `Dash_FOVKick` (+12°) appliqué sur `FirstPersonCamera`, ramené par `FInterpTo` sur la nouvelle
      clé **`Dash_FOVReturnSpeed`** (`07_TUNING §8`). Ligne `DASH` dans l'overlay `F3`.
      → **son : câblé, asset manquant.** Variable `DashSFX` (`Instance Editable`, `SoundBase`), vide.
      `PlaySound2D` ignore un son nul. Louis n'a qu'à déposer un asset dessus.
- [x] **Dette J4 levée** : `Dashing → Sliding` passe à **refusé** dans `CanEnterState`
      (1 cellule sur 64, les 63 autres vérifiées inchangées). Corrige une **contradiction** entre la
      table `SPEC_MOVEMENT §1.3` (qui disait `oui`) et `§11` (qui dit « refusé »). La bufferisation
      demandée n'a besoin d'aucun code : `UpdateLandingBuffer` retente déjà `TryStartSlide` chaque frame.
- [x] **`Jump pendant Dash`** (`SPEC_MOVEMENT §11`) : `TryJump` teste `CurrentState != Dashing` et
      bufferise. Ajouté **en insertion de nœuds** (3 nœuds, 2 recâblages), sans réécrire la fonction.
- [x] **Refonte après le 1ᵉʳ playtest** — « l'effet est bon, la vitesse est parfaite », deux correctifs :
      → **D37 — le dash suit le regard, point.** L'input `ZQSD` n'oriente plus rien et le Z-lock au sol
      saute : on se propulse exactement là où on vise, ciel compris. `Dash_ZLockOnGround` → **INACTIVE**.
      → **D38 — le slide ne récupérait plus jamais sa vraie vitesse.** `StartDash` lisait
      `MovementState.HorizontalSpeed`, calculée au tick **précédent** (le dash tick après, D32) : en
      enchaînant slide et dash on restait **bloqué à 5625 uu/s en permanence**. Lecture directe de
      `CMC.Velocity`, et le slide **reprend** à la sortie avec une fenêtre `Slide_HoldTime` neuve sur la
      vitesse restaurée — le dash **prolonge** le slide sans lui transmettre la vitesse de dash.
      → **D39, 3ᵉ passe** : « je peux spam dash en étant crouch et je vais à 5625 constamment ».
      D38 corrigeait ce que le dash *mémorise*, pas ce que le slide *observe*. Écrire `CMC.Velocity`
      la **publie** : `BPC_Slide` ticke avant le dash et, dans `CrouchStep` (friction 0.6/s) comme dans
      `SlideStep` (fenêtre qui se réarme à chaque accélération), il **lisait 5625 et le réécrivait**.
      `UpdateSlidePhysics` devient un `switch` sur `CurrentState` dont le pin **`Dashing` n'est
      connecté à rien**. Règle générale en `12_PIEGES §6.13`, à appliquer au wall ride (J6).
      → **D40, 4ᵉ passe — le bug n'était pas dans le dash.** « Je peux spam dash et **revenir** à max
      speed » : c'est le plafond qui restait haut, pas la vélocité. `ApplyMomentumDecay` écrivait la
      **variable** `HorizontalSpeed`, que `ClampToHardCap` **recalcule depuis la vélocité réelle deux
      étapes plus loin dans le même Tick**. La décroissance de momentum était donc **morte depuis le
      J2**, et `DriveCMC` (`MaxWalkSpeed = max(HorizontalSpeed, cap)`) faisait que le CMC ne freinait
      jamais : toute vitesse excédentaire était définitive. Invisible tant que rien ne poussait
      durablement au-dessus du sprint cap — **le dash n'a pas créé le bug, il l'a révélé.**
      La décroissance met désormais la **vélocité** à l'échelle. `12_PIEGES §6.14`.
      ⚠️ `MomentumDecayRate` (400 uu/s²) n'a **jamais rien piloté** : à retuner en priorité.
      → **D41, 5ᵉ passe** : « ce n'est plus un dash mais un boost ». **Mesuré** cette fois, via un
      déclencheur headless (`F4 → IA_Dash` temporaire dans `IMC_Debug`) : `entry = exit = 2246`, le
      dash **restaure exactement** la vitesse d'avant, il était innocent. Le coupable est le
      **réarmement de la fenêtre** : tout redémarrage de slide pose `HoldRemaining = Slide_HoldTime`,
      et `Dash_Cooldown` (1.4 s) à peine plus long que `Slide_HoldTime` (1.0 s) supprimait toute
      décroissance. Le dash **sauvegarde et restitue** désormais la fenêtre : il est **neutre en temps**.
      Au passage, `ResumeSlideIfNeeded` était morte depuis D38 (**piège 2.3b**, un `Set` avant un `if`
      qui lit la même variable) — corrigée, et le contrôle correspondant ajouté au registre (2.3c).
      → **D42, 6ᵉ passe — erreur d'architecture corrigée.** Le dash **coupait** le slide (`EndSlide`)
      puis tentait de le reconstruire ; D38/D39/D41 ne faisaient que réparer les dégâts de ce cycle.
      Le dash est désormais une **parenthèse** : le slide est **gelé** (`bIsSliding` reste `true`,
      `HoldRemaining`/`SlideTimer` n'avancent pas, capsule et frictions intactes) et l'état lui est
      simplement **rendu** en sortie. `CanEnterState[Dashing][Sliding]` repasse à `true` — c'est le
      canal de restitution ; le garde-fou anti-nouveau-slide est structurel (`bIsSliding` reste vrai).
      `DashStep` écrit aussi `MaxWalkSpeedCrouched` (piège 6.6). **Code mort supprimé** : `AbortSlide`,
      `ResumeSlideIfNeeded` et 2 variables → 33 variables / 14 fonctions, plus simple qu'au playtest n°2.
- [x] **Test** : le dash sert à corriger une trajectoire, pas à aller vite
      → **validé par Louis le 2026-08-19** au 7ᵉ playtest : « tout fonctionne correctement ».
      Le modèle a été refondu **six fois** sur son retour manche en main — direction (D37), vitesse
      mémorisée (D38), gel du slide (D39), décroissance de momentum ressuscitée (D40), fenêtre
      restituée (D41), puis **suppression pure et simple de l'interruption du slide (D42)**.
      Les cinq premières passes réparaient les dégâts d'une coupure qui n'avait pas lieu d'être.

### J6 — Wall ride  *(implémenté le 2026-08-19, cf. `Docs/Journal/2026-08-19_J6_WallRide.md`)*
- [x] `BPC_WallRide` : détection, accroche, maintien, wall jump, cooldown same-wall
      → composant **autonome** : 45 variables, 21 fonctions, `EventGraph` de 8 nœuds, 1 dispatcher
      (`OnWallRideStarted`). Zéro modification du Tick de `BPC_MovementState`, comme `BPC_Slide` (D22)
      et `BPC_Dash` (D32).
      → **Il tick APRÈS `BPC_MovementState`** (patron `BPC_Dash`, pas patron `BPC_Slide`) : il pilote
      la vélocité intégralement, il doit avoir le dernier mot. C'est ce qui implémente « air strafe
      pendant wall ride : désactivé » (`SPEC_MOVEMENT §11`) **sans toucher au code validé du J3**.
      → Les 4 règles de la passation J5 sont respectées : tick en dernier, lecture de `CMC.Velocity`
      jamais de `MovementState.HorizontalSpeed` (piège 6.12), `BPC_Slide.UpdateSlidePhysics` gelée
      pendant `WallRiding` (piège 6.13), et **le wall ride ne coupe rien** (D42).
      → **`CanEnterState` n'a pas été touchée.** Les 8 cellules de la ligne/colonne `WallRiding`
      étaient **déjà** conformes à `SPEC_MOVEMENT §1.3` (vérifiées une par une). Le garde-fou de
      « Wall ride pendant Dash : refusé » (§11) est **structurel** — la détection ne tourne pas quand
      `CurrentState == Dashing` — exactement la leçon de **D42**.
      → **D43** — détection par **accumulateur dans le Tick** au lieu du `Timer` de la spec.
      → **D45** — nouvelle condition de sortie : **contact du sol**. En `MOVE_Flying` le CMC ne
      détecte pas l'atterrissage ; sans ça le joueur rase le sol en volant jusqu'à la fin des 2 s.
      → **D46** — `WallRide_CameraTilt` **non câblé** : le roulis caméra est du juice, il est déjà
      planifié au J14. Le J6 livre la mécanique, pas son habillage (R4).
- [x] Object type `WallRideSurface` + un mur de test
      → l'object type `ECC_GameTraceChannel2` et le profil `OD_WallRideSurface` existaient depuis le
      J1. Les 9 murs des zones E et F les portent, **vérifié par requête physique** (`ObjectTypeQuery8`).
- [x] Zone sandbox : 2 murs opposés, 3 murs en escalier
      → **Zone E** — 3 couloirs de 6000 uu (X −7000 → −1000), murs de 800 uu de haut, aux 3 écartements
      de `07_TUNING §17` : **600 / 1000 / 1400 uu** (Y = 2500 / 0 / −2500).
      → **Zone F** — 3 murs alternés de 1500 uu, bases en escalier **Z 0 / 150 / 300**, couloir de
      1400 uu (Y = −6000), trous de 400 uu entre les murs.
      → Géométrie **vérifiée par trace physique** sur les 6 faces intérieures + les 3 bases.
      Détail : `SPEC_MOVEMENT §13.2`.
- [x] **Vérifié en PIE, sans Louis** — les 20 valeurs de tuning cachées correspondent au DataAsset,
      le composant tick, et **un wall ride complet a été mesuré** : `entrySpeed 2517.9` →
      `rideSpeed 2417.5` après 2 s, soit exactement `2517.9 × 0.98²`. Sorties `Duration`, `NoWall`
      et `Grounded` déclenchées et distinguées. Le saut normal **ne régresse pas** malgré
      l'insertion de `TryWallJump` devant lui dans la chaîne d'input.
- [x] **Test** : enchaîner 3 murs consécutivement est possible et satisfaisant
      → **validé par Louis le 2026-08-19** au 2ᵉ playtest : « le game feel sur les murs est nickel,
      c'est exactement ce que je voulais », « le tilt est good », « le dash ne fait pas bugger la
      vitesse », « la poussée à l'opposé fonctionne pour le décrochage ».
      → Le 1ᵉʳ playtest n'a produit **aucun bug** : cinq retours, tous sur le **modèle**. Le wall ride
      faisait exactement ce que la spec décrivait — et la spec décrivait la mauvaise chose. Une seule
      passe de refonte (**D47–D49**) a suffi, contre **six** au J5 et **cinq** au J4.
      → **Écartement de référence tranché : 1000 uu** (couloir E2). Reporté dans `07_TUNING §17`.
- [x] **Refonte après le 1ᵉʳ playtest** — le mur devient un **sol vertical** :
      → **D47** — accroche **illimitée**, **à l'horizontale**, à **vitesse strictement constante**.
      4 clés (`MaxDuration` 2→**0**, `GravityScale` 0.25→**0**, `UpwardBoost` 250→**0**,
      `SpeedRetention` 0.98→**1.0**) et 2 corrections de graphe. Le modèle d'origine **punissait** le
      joueur d'être resté sur le mur : il descendait, ralentissait, et était éjecté au bout de 2 s.
      Mesuré après coup : `entrySpeed = rideSpeed` **au dix-millième**, 5800 uu parcourus sans toucher
      le sol.
      → **D48** — le wall jump part **dans la direction du regard** (norme conservée, direction libre —
      même principe que D37 pour le dash), et il monte enfin plus haut qu'un saut normal :
      `WallJump_ZVelocity` valait **800** contre `Jump_ZVelocity` = **900**. C'était ça, « le saut du
      mur est trop faible ». → **1200**. `AwayVelocity` 700 → **1000**.
      → **D49** — **D46 annulée le jour même** : le roulis caméra est câblé. Ce n'était pas du juice,
      c'était de la **lisibilité** — collé au mur sans inclinaison, on ne voit pas où on va. Posé dans
      la `ControlRotation` (seule voie : `bUsePawnControlRotation` écrase tout `SetRelativeRotation`
      sur la caméra). Vérifié : valeur calculée `0.3699` → roulis réel de la caméra `0.3703`.
      → **Anti-héritage de la vitesse de dash** (demandé explicitement par Louis) : 3 garde-fous, dont
      **`AddTickPrerequisiteComponent(BPC_Dash)`** qui supprime la seule faille théorique — les deux
      composants avaient `MovementState` comme prérequis, leur **ordre relatif était indéterminé**.

### J7 — Bunny hop & intégration  *(implémenté le 2026-08-19, cf. `Docs/Journal/2026-08-19_J7_BunnyHop.md`)*
- [x] **Parcours sandbox complet enchaînant les 7 mécaniques** — *fait en premier, avant le code*
      → **Zone K** (`SPEC_MOVEMENT §13.2`), 10 acteurs : rampe d'accès 30° → plateau → rampe de slide
      30° → deck → **gap de 1200** → virage → couloir → **gap de 1800** → wall ride → wall jump →
      atterrissage → retour au sol pour la ligne de hops. Géométrie **vérifiée par traces physiques**.
      → Le sol du sandbox étant un mesh plein, **le circuit est surélevé à `Z = 400`** : c'est la seule
      façon d'avoir de vrais trous. Tomber = 400 uu de chute, jamais bloquant.
      → Les deux gaps sont dimensionnés sur la portée d'un saut (`v × 0.765 s`) : 1200 exige ~1600 uu/s,
      1800 exige ~2400 uu/s **ou** un wall ride. **Le gap 1 est l'instrument du retune du momentum.**
      → Premiers murs de wall ride qui ne sont pas des cubes : 2 × `SM_Module_WallRide_1600` du kit
      livré le même jour — c'est ce qui a contourné le piège **§5.15**.
- [-] **Bunny hop — COUPÉ DU SCOPE le jour même (D52), après playtest**
      → **« ça rajoute trop de vitesse, je n'aime pas ; juste avant c'était vraiment bien »** (Louis).
      Le gain de vitesse reste l'affaire du **seul air strafe**. `BPC_MovementState` est revenu
      exactement à son état du J6 — 15 nœuds dans `DoJump`, 37 dans le Tick, 33 fonctions,
      61 variables, vérifié compteur par compteur. Les 4 clés `BHop_*` restent dans `07_TUNING §6`
      marquées `COUPÉ`, lues par aucun code.
      → **Ce n'est pas un échec technique** : la feature marchait et était mesurée (2000 → 2120 uu/s).
      C'est `10_DEFINITION_OF_DONE §2` appliqué — *pas fun → supprimer*. Même famille que **D24**
      (le slide qui donnait « trop de boost sans effort »).
      → Ce que la journée garde quand même : le bug d'**`AddSpeedGain`** (ci-dessous) et la
      discipline qui a rendu la suppression triviale — **aucune réécriture de code validé**, donc
      retirer 4 nœuds d'appel a suffi à défaire la feature.
      → *Détail de ce qui avait été construit, pour le jour où la question se reposerait :*
      **dans `BPC_MovementState`**, pas un composant autonome : c'est une modification de
      l'atterrissage et du saut, pas un pilote de vélocité (`SPEC_MOVEMENT §6.1`).
      → 4 fonctions (`CacheBHopTuning`, `TryBunnyHop`, `UpdateBHopChain`, `DrawBHopDebug`),
      8 variables, et **3 insertions de nœuds** — zéro réécriture de code validé.
      → **D50** — l'annulation de la perte d'atterrissage se fait par
      `max(PreLandSpeed, VitesseCourante) + Gain`, appliqué à la **vélocité du CMC** et non à la
      variable `HorizontalSpeed` (leçon `12_PIEGES §6.14`). Le `max` évite qu'un hop *réduise* la
      vitesse quand on arrive d'une pente.
      → **D51** — `BHop_FrictionSkip` reste **sans code** : l'anti-freinage de `DriveCMC` rend la
      friction inopérante au-dessus du cap, et `BPC_Slide` possède déjà `GroundFriction`.
      → **Vérifié en PIE, sans Louis** : `2000 uu/s → hop → 2120 au ré-atterrissage`, chaîne à 1,
      gain 120, source `"BunnyHop"`. Échafaudage (fenêtre à 60 s, `F5 → IA_Jump`) **restauré et
      revérifié clé par clé**.
      → ⚠️ **`AddSpeedGain` est inopérante** (elle n'écrit que `HorizontalSpeed`, jamais la vélocité) :
      même famille que D40. **Zéro appelant** dans le projet, donc sans effet aujourd'hui — à réparer
      avant les upgrades du J20.
- [x] Matrice d'interactions validée (`Docs/Specs/SPEC_MOVEMENT.md §11`)
      → validée **sur la base des playtests J4/J5/J6 + la manche du J7** : dash pendant slide (D42),
      slide pendant dash, slide d'atterrissage, jump pendant wall ride, dash pendant wall ride.
      Les 2 lignes qui concernaient le bunny hop sont **sans objet** depuis D52.
- [x] **Retune `MomentumDecayRate` / `MomentumDecay_GraceTime`** — *chantier n°1 du J7*
      → **`400 → 800` et `0.35 → 0.25`**, tranché par Louis. Sortie de wall ride à 2500 uu/s : la
      vitesse excédentaire dure **1.50 s au lieu de 2.85 s** (~3000 uu au lieu de ~5700).
      Vérifié en PIE que le composant lit bien les nouvelles valeurs au `BeginPlay`.
      → Répond au constat du J6 : « c'est un peu trop simple d'accumuler de la vitesse sans la perdre ».
- [x] **`AddSpeedGain` réparée** — elle n'écrivait que la variable `HorizontalSpeed`, jamais la
      vélocité : même bug que D40, inopérante depuis le J2. **Zéro appelant**, donc aucune régression
      possible — la mine est désamorcée avant les upgrades du J20. L'écriture DSL avait **empilé**
      l'ancienne version (42 nœuds au lieu de 14) : 13 nœuds morts purgés par accessibilité exec.
      Nouveau piège **`12_PIEGES §2.2c`** — un contrôle d'orphelins qui cherche des nœuds *totalement*
      déconnectés ne voit **jamais** une chaîne empilée, qui est reliée à elle-même.
- [x] Premier passage de tuning avec Louis
- [x] **🚦 GATE SEMAINE 1 — PASSÉE** (`Docs/10_DEFINITION_OF_DONE.md §3`)
      → **Test 1 ✅** (depuis le J3) et **Test 2 ✅** : « tout marche correctement ».
      Passée avec **6 mécaniques et non 7**, le bunny hop ayant été coupé sur le feeling.
      **La semaine 2 (combat) est débloquée.**

---

## SEMAINE 2 — COMBAT + JUICE

> **Objectif** : courir → tirer → headshot → melee → projeter un ennemi → dash → wall ride → continuer.

### J8 — Laser
- [x] `PDA_WeaponData` + `DA_Weapon_Laser`
- [x] `BPI_Damageable` (4 fonctions) + `S_DamageInfo` (8 champs) — assets créés à la main par Louis (5.16 / 5.17)
- [x] Canal de trace `Weapon` = `ECC_GameTraceChannel3` → **`TraceTypeQuery3`** (prouvé, cf. journal)
- [x] `BP_LaserWeapon` : `EventBeginPlay`, `TryFire`, `ResolveShot`, `ProcessHit`, `IsHeadshot`,
      `PlayFireFX`, `EndFireCooldown` — hitscan depuis la caméra sur `ControlRotation` brute,
      dégâts via `BPI_Damageable`, cooldown par `Set Timer by Event`
- [x] `BP_PlayerCharacter` : `WeaponSpring` (SpringArm, montage **provisoire**) + `ChildActor_Laser`,
      `IA_Fire` → `HandleFireInput` → `TryFire`, child actor mis en cache au `BeginPlay` (§13.11)
- [~] Cibles de test dans le sandbox — `BP_TargetDummy` (`Dev/Sandbox/`, cube 60 × 60 × 180, `MaxHealth`
      `Instance Editable`) et **7 instances placées** dans `L_Sandbox_Movement`, dossier `Sandbox/L_Targets` :
      2 sur la ligne droite d'approche, 2 sur le deck 1 de la zone K, 1 sur le deck 3a après le wall jump,
      2 dans le couloir de wall ride E2. Bases vérifiées **pile** sur leur surface (`get_actor_bounds`).
      → Elles **bloquent déjà le canal `Weapon`** (collision par défaut), donc la ligne de tir s'y arrête :
      la visée en course est testable tout de suite.
      → ⏳ **Reste : cocher `BPI_Damageable` dans « Implemented Interfaces » de `BP_TargetDummy`** — geste
      manuel, aucun outil ne le fait (`12_PIEGES §5.16`). `ApplyDamage` / `IsAlive` / `GetHealthRatio`
      seront écrits par outil juste après.
- [x] **Correctif game feel (retour de Louis manche en main)** — *« le laser ne part pas du muzzle du
      pistolet si on se déplace, on a l'impression qu'il part depuis le vide, et le rayon disparaît
      trop vite »*. `PlayFireFX` **arme** désormais le faisceau (`BeamEnd`, `BeamTimeRemaining`) au
      lieu de le dessiner ; `UpdateBeam(DeltaSeconds)` — seul contenu d'un `EventTick` **dérogatoire
      et provisoire** — le redessine chaque frame depuis le muzzle **courant**, avec un alpha qui
      décroît. `LaserDebug_LineDuration` (0.06 s, ligne figée) **remplacée** par
      `LaserDebug_BeamDuration` = 0.12 s. Dérogation de Tick écrite dans `SPEC_COMBAT §2`,
      **à retirer au J14** avec `NS_LaserBeam`.
- [x] **Correctif game feel n°2 (retour de Louis manche en main, J8bis)** — *« il faut que quand on tire
      ça parte exactement du muzzle du canon puis ensuite il se détache pour rester en l'air là où on
      a tiré, je ne veux pas de duplication »*, *« un effet beaucoup plus glowy »*, *« qu'il reste
      encore un peu plus longtemps et fade un peu plus doucement »*. Relire le muzzle à **chaque**
      frame produisait un éventail de segments (3 vivants à la fois × 32 uu de déplacement par frame
      à 1900 uu/s) → **deux rayons divergents**. Correctif : nouvelle variable `BeamStart`, posée par
      `PlayFireFX` puis entretenue par `UpdateBeam` **uniquement pendant `LaserDebug_AttachTime`**
      (0.05 s), et **figée en espace monde ensuite** — accroche puis décrochage.
      `LaserDebug_BeamDuration` 0.12 → **0.35 s**, fondu passé en **racine carrée**
      (`alpha = sqrt(rem/dur)`), et faisceau doublé d'un **halo** concentrique
      (`LaserDebug_GlowWidthMult` = 5.0, `LaserDebug_GlowAlphaMult` = 0.3, halo dessiné **avant** le
      cœur, même `BeamStart`/`BeamEnd`). Les 3 clés neuves écrites sur le CDO **et** sur le
      `ChildActorTemplate` (`12_PIEGES §5.27`), relevé sur l'instance PIE à l'appui.
- [ ] **Test** : tirer en courant est naturel → **en attente du playtest de Louis (R8 / R10)**
- [ ] **Test** : le faisceau part du canon même à 3000 uu/s, **ne se dédouble pas**, et s'efface en
      fondu doux → **idem**

- [x] **Correctif mouvement × combat (`D53`, tranché par Louis)** — *« comme le slide est orienté avec
      la souris, quand on veut viser en slidant ça nous fait tourner »*. `BPC_Slide` seul : le virage
      de `D26` ne vise plus le regard **instantané** mais un **cap lissé** `SlideHeadingDir`
      (filtre passe-bas **vectoriel**, `VInterpTo` à `Slide_HeadingFollowSpeed` = 2.5 /s).
      Nouvelles fonctions `InitSlideHeading` (entrée de slide, cap = direction de `CMC.Velocity`) et
      `UpdateSlideHeading(dt, AimDir)` (1ᵉʳ nœud exec de `SlideStep`). `Slide_TurnRate`, la norme de la
      vitesse, `D29`, `D31` et le plancher `bForcedSlide` (`D27`) **inchangés**. Clé ajoutée à
      `PDA_MovementData` / `DA_Movement_Default` / `07_TUNING §5`.
- [ ] **Test** : on peut viser à la souris en slidant sans être dévié, **et** garder le demi-tour
      serré à 0.25 s quand on le veut → **en attente du playtest de Louis (R8 / R10)**

- [x] **Correctif mouvement × combat n°2 (`D54` / `D55` / `D56`, J8quater)** — *« il faudrait faire en
      sorte de pouvoir se décoller uniquement si on met la touche opposée au mur […] là on se décroche
      aussi si on regarde sur le côté […] au moins qu'on puisse regarder à droite si on est sur un mur,
      pour pouvoir tirer en étant en wall ride »*. Même conflit que `D53`, sur le wall ride.
      **Deux causes indépendantes**, toutes deux corrigées : (1) `ConfirmWall` traçait le long de
      `ActorRightVector × WallSide` — l'acteur tourne avec la caméra (`bUseControllerRotationYaw`),
      donc la trace de maintien sortait du mur vers 67° → sortie `NoWall` ; elle part désormais le long
      de **`-WallNormal`** mémorisée, portée inchangée (`12_PIEGES §6.21`). (2) `CheckDetachInput`
      jugeait l'input sur un `WishDir` construit dans la **base caméra** — tenir `Z` et tourner la tête
      de 30° suffisait à décrocher ; l'input est désormais reconstruit dans le **repère du mur**
      (`12_PIEGES §6.22`). Sorties renommées et séparées : **`InputAway`** (touche latérale opposée,
      seuil `WallRide_DetachDotThreshold` 0.7 → **0.5**) et **`LookAway`** (nouvelle, regard à plus de
      `WallRide_DetachLookAngle` = **90°** de la direction de déplacement, cosinus précalculé au
      `BeginPlay`). `Grounded` (`D45`), `WallJump` (`D48`), l'accroche illimitée (`D47`), le roulis
      (`D49`), le cooldown same-wall et l'anti-héritage de vitesse de dash : **intouchés**.
- [ ] **Test** : on peut viser à 90° pendant un wall ride **sans jamais décrocher**, et on décroche
      **uniquement** avec la touche opposée au mur → **en attente du playtest de Louis (R8 / R10)**

- [x] **Correctif mouvement n°3 (`D57`, J8quinquies)** — *« j'aimerais avoir le timer du dash oui, mais
      aussi faire que sur un long saut on ne puisse pas spam les dash. Donc avoir qu'un seul dash, et
      pour le récup il faut attendre le timer ET avoir touché une surface, donc sol ou wall ride. Car
      là on peut limite voler en spammant les dash. »* `BPC_Dash` seul, en **amendement** : nouveau
      drapeau `bSurfaceTouchedSinceDash`, mis à `false` par `StartDash`, remis à `true` par
      `UpdateSurfaceTouch` (`CMC.IsMovingOnGround()` hors dash, en tête de `TickDash`) et par
      l'abonnement au dispatcher **`OnWallRideStarted`** de `BPC_WallRide`. `CanDash` gagne une
      condition, **rien d'autre n'est touché** : `Dash_Charges`, `Dash_Cooldown`, `UpdateCharges`,
      `D30`, `D37`, `D38`, le gel du slide (`D39`/`D42`), le FOV kick, l'ordre de tick et
      `CanEnterState` sont intacts. Clé `Dash_RequiresSurfaceTouch` (défaut `true`) dans
      `PDA_MovementData` / `DA_Movement_Default` / `07_TUNING §8` — la mettre à `false` restaure
      l'ancien comportement à l'identique.
- [ ] **Test** : **un seul dash par saut**, récupéré au contact du sol **ou** d'un wall ride, et aucune
      régression du J5 (slide → dash → slide, pas de blocage à 5625 uu/s) →
      **en attente du playtest de Louis (R8 / R10)**

> Reporté hors J8, volontairement : passe 2 de l'aide à la visée (`SPEC_COMBAT §11`,
> `Laser_TraceRadius = 0` → serait du code mort non testable), `ApplyRecoil` (`§3.6`, exige un
> `BP_PlayerCameraManager` custom → J14), gate heat (J9), gate health (J12),
> `bUseMuzzleConfirmTrace` (`§3.4`, défaut `false`), decals / VFX d'impact décor (J14),
> `IsHeadshot` réel (J10 — `HeadHitbox` n'existe nulle part, la fonction renvoie `false` en dur).

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
- [ ] **Dette J8 à solder** : `NS_LaserBeam` (World Space, positions figées à l'émission) remplace la
      ligne de debug → supprimer `UpdateBeam`, l'`EventTick` de `BP_LaserWeapon`, les variables
      `BeamStart` / `BeamEnd` / `BeamTimeRemaining` / `DebugBeamDuration` / `DebugDrawLifetime` /
      `DebugAttachTime` / `DebugGlowWidthMult` / `DebugGlowAlphaMult` / `DebugLineThickness` / `DebugLineColor`,
      et **repasser le Tick de l'arme à désactivé** (`SPEC_COMBAT §2`, dérogation provisoire).
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
      → **entamé en avance le 2026-08-20** : `M_Weapon_Base` + les 4 `MI_Weapon_*` de l'arme FP sont
      créés et assignés aux 4 slots de `SM_Weapon_LaserPistol`
      (`Docs/Journal/2026-08-20_Materiaux_Arme.md`, `SPEC_ART_DIRECTION §6.4`).
      Restent au J22 : `PP_ToonPost`, `M_Env_Base`, `M_Env_Emissive`, `M_Sign`, `MPC_Global`.
      ⚠️ Tension de palette (arme rouge / tir magenta) en attente d'arbitrage — `§6.4.1`.
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
| S1 | 20 h | J1→J7 bouclés en **2 jours calendaires** (2026-08-18 → 19) | ✅ **oui**, le 2026-08-19 | **Bunny hop retiré du scope (D52)** — le mouvement v1 compte 6 mécaniques, pas 7. Retrait *par le test*, pas par manque de temps |
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
