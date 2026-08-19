# Journal — 2026-08-19 — Jour 03

**Temps effectif** : ~3 h
**Objectif du jour (roadmap)** : J3 — saut, coyote time, jump buffer, air strafe Quake,
conservation de la vitesse à l'atterrissage.

---

## Fait

### Saut (`SPEC_MOVEMENT §5`)

4 nouvelles fonctions dans `BPC_MovementState` :

- **`UpdateJumpTimers()`** — étape 1bis du Tick. Écrit `LastGroundedTime` chaque frame où
  `bIsGrounded`. C'est la seule source de la fenêtre de coyote time.
- **`TryJump() → bJumped`** — appelée par `IA_Jump` (Started). Saute si au sol **ou** si
  `Now - LastGroundedTime < Jump_CoyoteTime` **et** `!bJumpConsumed`. Sinon **arme le buffer**
  (`JumpBufferedTime = Now`) et retourne `false`.
- **`DoJump()`** — `Velocity = (XY × SpeedRetention_Jump, Jump_ZVelocity)` en **`Set Velocity`**,
  puis `SetMovementMode(MOVE_Falling)`. Jamais `Launch Character` (`SPEC_MOVEMENT §15`).
  Consomme le saut et désarme le buffer.
- **`HandleLanded()`** — appelée par `Event On Landed` de `BP_PlayerCharacter`.
  Cache `PreLandSpeed`, libère `bJumpConsumed`, applique `SpeedRetention_Landing` sur `Velocity.XY`,
  arme la grace, fire `OnLandedSpeed`, et **rejoue le saut bufferisé** si on est dans la fenêtre.

### Air strafe — modèle Quake (`SPEC_MOVEMENT §7`)

**`ApplyAirStrafe(DeltaSeconds)`**, insérée à l'**étape 7 du Tick**, entre `DriveCMC` et
`ClampToHardCap`, exactement comme prévu.

Le cœur est conforme à la spec au nœud près : projection scalaire `Dot(HorizVel, WishDir)`,
`AddSpeed = WishSpeedCap − CurrentSpeed`, double clamp (`MaxAccel × dt` puis `SpeedGainPerSec × dt`),
`ClampVectorSize` au `Speed_HardCap`, **Z jamais touché**.

4 garde-fous, dans cet ordre : `IsFalling` · norme d'input > `Input_MoveDeadZone` ·
`HorizontalSpeed < AirStrafe_NoGainAboveSpeed` · `Dot(WishDir, VelDir) > cos(90 + GainAngleMax)`.

`AirControl` est désormais écrit **chaque frame par `DriveCMC`** depuis `Tune_AirControl` :
un seul propriétaire, comme `GravityScale` (`SPEC_MOVEMENT §15`).

### Correctif : `ClampToHardCap` ne clampait rien

Le `Speed_HardCap` **n'était jamais appliqué**. La fonction écrivait la variable `HorizontalSpeed`
(l'affichage) mais ne touchait jamais `CMC.Velocity`. Zéro symptôme au J2 parce que rien ne pouvait
encore dépasser 1500 ; l'air strafe est justement la première mécanique qui le peut.
Corrigé : la vélocité horizontale est remise à l'échelle sur `Speed_HardCap`.

C'est un bug de la même famille que celui repéré plus bas dans `HandleLanded` — voir « Pièges ».

---

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| **D13** — `HandleLanded` appelle **`StartGrace(MomentumDecay_GraceTime)`**. Sans ça, la décroissance de momentum (`§2.4-5`) attaque dès la frame de contact : `SpeedRetention_Landing = 0.92` devient invisible et le bunny hop du J7 est mort-né. La grace à l'atterrissage est ce qui rend le momentum *transportable* d'un saut au suivant. | `Docs/Specs/SPEC_MOVEMENT.md` §5.1 ✅ |
| **D14** — `WishDir` est lu via **`CMC.GetLastInputVector()`**, pas reconstruit depuis `ControlRotation` comme en `§7.1`. C'est le vecteur monde que le CMC vient de consommer : identique *par construction* à ce que `HandleMoveInput` a poussé. Reconstruire à part dupliquerait la convention « X = droite, Y = avant » à deux endroits — un rebinding ou un `SwizzleAxis` dans l'`IMC` désalignerait le gain d'air strafe du déplacement réel, sans aucun signal visible. | `Docs/Specs/SPEC_MOVEMENT.md` §7.3 ✅ |
| **D15** — `CanEnterState` autorise **`Falling → Jumping`**. Un saut en coyote time part forcément depuis `Falling` ; refusé, il laissait le joueur dans `Falling` avec une vélocité Z positive. La note ⁴ de `§1.3` prévoyait déjà l'exception. Le double saut reste bloqué par `bJumpConsumed`. | `Docs/Specs/SPEC_MOVEMENT.md` §1.3 ✅ |
| **D16** — `bJumpConsumed = true` et `JumpBufferedTime = -1` vivent dans **`DoJump`**, pas dans `TryJump` comme écrit en `§5`. `DoJump` est aussi le chemin du saut bufferisé : dans `TryJump`, ce chemin laissait `bJumpConsumed = false` et rouvrait un double saut par coyote time. | `Docs/Specs/SPEC_MOVEMENT.md` §5.1 ✅ |
| **D17** — `JumpBufferedTime` est initialisé à **`-1`** au `BeginPlay`. À 0, la condition `Now - 0 < Jump_BufferTime` est vraie pendant les 150 premières ms de jeu → saut fantôme au premier contact du sol. | `Docs/Specs/SPEC_MOVEMENT.md` §5.1 ✅ |

## Valeurs modifiées

**Aucune valeur de `07_TUNING` n'a bougé.** Les 10 clés du J3 (`Jump_*`, `AirStrafe_*`,
`SpeedRetention_*`) existaient déjà dans `PDA_MovementData` avec les bonnes valeurs — vérifié
propriété par propriété.

Deux **defaults du CMC** réalignés sur le tuning (ils n'étaient pas lus, mais laissaient traîner des
valeurs de template contradictoires) :

| Propriété CMC | Ancien | Nouveau | Raison |
|---|---|---|---|
| `JumpZVelocity` | 420 (template) | 900 | cohérence avec `Jump_ZVelocity` ; `DoJump` écrit la vélocité lui-même, mais 420 était un piège pour la relecture |
| `AirControl` | 0.05 (template) | 0.55 | cohérence avec `AirStrafe_AirControl` avant la première frame ; `DriveCMC` l'écrase ensuite chaque frame |

---

## Pièges rencontrés (outillage MCP)

| Piège | Gravité | Résolution |
|---|---|---|
| **`read_graph_dsl` ne restitue pas les branches des events Enhanced Input.** `BP_PlayerCharacter:EventGraph` se lit comme 5 events **au corps vide** alors qu'il contient 19 nœuds : le lecteur ne suit que le pin `then` par défaut, jamais `Triggered` / `Started` / `Completed`. **Un `write_graph_dsl` sur ce graphe aurait effacé tout le câblage d'input du J2.** | **Critique** | Contourné — `create_node` + `connect_pins` sur ce Blueprint. Vérifié après coup : 19 → 25 nœuds, les 18 liens d'origine intacts. |
| **La sortie de `read_graph_dsl` n'est pas toujours réinjectable.** Le lecteur écrit `(CallFunction|UpdateSpeedCap DeltaSeconds)` ; réécrit tel quel, l'argument positionnel part sur le pin `self` et le write échoue. | Moyen | Toujours **nommer les pins** : `(CallFunction|UpdateSpeedCap :DeltaSeconds DeltaSeconds)`. |
| **`CallFunction|SetHorizontalSpeed` s'est résolu vers le *setter de variable* homonyme.** La fonction `SetHorizontalSpeed` et la variable `HorizontalSpeed` génèrent deux nœuds au nom proche ; le writer a choisi la variable. Résultat : `HandleLanded` mettait à jour l'affichage sans jamais toucher la vélocité — **exactement le bug de `ClampToHardCap`**, silencieux et invisible à la compilation. | **Élevé** | Détecté en **relisant systématiquement chaque graphe après écriture**. Contourné en écrivant la vélocité directement (`Class|MovementComponent|SetVelocity`), sans passer par la fonction. |
| Les setters de variables ne s'écrivent pas sous la forme courte `|SetFoo` du lecteur : il faut le chemin de catégorie complet **sans underscores** (`Variables|Movement|Cached|SetTuneSpeedWalk` pour `Tune_SpeedWalk`). | Moyen | `find_node_types` avec un filtre avant chaque écriture. |
| Les `type_id` à parenthèses (`Math|Trig|Cos(Degrees)`, `Utilities|String|ToString(Float)`) **fonctionnent**, contrairement à ce que laissait croire le J2 — à condition de nommer le pin (`:A`, `:InDouble`). | Faible | Noté. |
| `Transformation|GetVelocity` (lu par le DSL) n'accepte pas un CMC en `self`. | Faible | `Class|MovementComponent|GetVelocity`. |
| Un nœud orphelin `ToString(Boolean)` traînait dans `BP_PlayerCharacter` depuis le J2 (sonde `get_node_type_pins`, piège connu). | Cosmétique | Supprimé. |

---

## Pas fait / reporté

- **Bunny hop** (`§6`) — c'est le J7. `PreLandSpeed`, `LandedTime` et `bJumpConsumed` sont déjà
  posés et alimentés pour lui ; il ne manquera que la fenêtre, le skip de friction et le gain.
- **Playtest** — cf. R8 et « Vérification » ci-dessous.
- `PerchRadiusThreshold` est à **0** sur le CMC alors que `§15` recommande `> 0` contre l'accrochage
  d'arêtes. Aucune clé n'existe dans `07_TUNING` : je ne l'invente pas (R3). À trancher au J4/J15,
  quand il y aura de vraies arêtes de modules à franchir.
- `PrimaryComponentTick.tickGroup` de `BPC_MovementState` vaut `TG_DuringPhysics`, la spec `§2.4`
  dit `TG_PrePhysics`. Sans effet tant que `AddTickPrerequisiteComponent(CMC)` garantit l'ordre,
  mais l'écart est réel. À aligner si un problème d'ordre apparaît.
- `IMC_Gameplay` porte ses 14 mappings **en double** : dans `DefaultKeyMappings` (lu par UE 5.8)
  **et** dans le tableau déprécié `Mappings`. Sans impact aujourd'hui, mais c'est une double source
  de vérité qui piégera au prochain rebinding. À nettoyer.

---

## Vérification (2026-08-19)

Statique, en éditeur :

| Vérifié | Résultat |
|---|---|
| Compilation `warnings_as_errors` | **2/2** — `BPC_MovementState`, `BP_PlayerCharacter` |
| Relecture DSL de chaque graphe écrit | 9/9 conformes à l'intention (2 bugs corrigés au passage) |
| Câblage d'input du J2 préservé | 18 liens d'origine intacts, 25 nœuds au total |
| `IA_Jump` → `SpaceBar` dans `DefaultKeyMappings` | présent |
| Cache de tuning en PIE | les 11 `Tune_*` du J3 chargés depuis `DA_Movement_Default` |
| `Tune_AirStrafeGainAngleCos` | **−0.7071** = `cos(135°)` ✅ conforme à `§7.1` |
| Erreurs runtime au `BeginPlay` | **0** |

**Ce que je n'ai pas pu vérifier :** le comportement en jeu. Le monde PIE n'avance pas quand
l'éditeur n'a pas le focus — les appels MCP s'exécutent sur le game thread. Même limite qu'au J2.
`BeginPlay` s'exécute bien (caches résolus, `CachedCMC` / `CachedCharacter` valides), mais aucun
Tick ne tourne tant que Louis n'a pas la fenêtre au premier plan.

---

## ⚙️ Checklist de test manuel (R8) — Louis

`L_Sandbox_Movement` en PIE. **`F3`** bascule l'overlay. La ligne à surveiller est **`JUMP`**.

### 1. Saut de base
- [ ] Espace fait sauter. `STATE` passe à `Jumping`, puis `Falling` quand `VZ` devient négatif
- [ ] `STATE` revient à `Idle` / `Walking` / `Sprinting` à l'atterrissage
- [ ] En sprintant : `SPEED` **ne chute pas** au décollage (`SpeedRetention_Jump = 1.0`)
- [ ] Deux appuis rapides ne donnent **pas** de double saut

### 2. Coyote time (`0.12 s`)
- [ ] Courir vers le bord d'une plateforme, **ne pas** sauter avant le vide, appuyer **juste après**
      avoir quitté le sol → le saut part quand même
- [ ] `JUMP coyote` doit être **< 0.12** au moment de l'appui pour que ça marche
- [ ] Après une vraie chute longue (coyote > 0.12) : **aucun** saut. Si tu peux sauter en pleine
      chute, `bJumpConsumed` est cassé

### 3. Jump buffer (`0.15 s`)
- [ ] En retombant, appuyer sur Espace **avant** de toucher le sol → le saut part **à l'impact**,
      sans avoir à réappuyer
- [ ] `JUMP buffer` affiche un temps ≥ 0 pendant que le buffer est armé, **`-1.00`** sinon
- [ ] Appuyer beaucoup trop tôt (~0,5 s avant le sol) : le buffer expire, **pas** de saut

### 4. Conservation à l'atterrissage
- [ ] Sprinter à 1500, sauter, atterrir → `SPEED` tombe à **~1380** (`0.92 × 1500`), pas à 1000
- [ ] `GRACE` passe à **0.35** au contact puis décompte. La décroissance ne démarre qu'après

### 5. Air strafe — **c'est le test du jour**
- [ ] Sauter, puis **maintenir `Q`** (strafe gauche) **et** tourner la souris lentement vers la gauche.
      `SPEED` doit **monter continûment** pendant tout le vol
- [ ] Même chose à droite avec `D` + souris à droite
- [ ] Sans tourner la souris : quasiment aucun gain. C'est normal — le gain vient de la coordination
- [ ] En strafant **contre** la vitesse (input à l'opposé) : aucun gain (garde `GainAngleMax`)
- [ ] `JUMP airgain` affiche un nombre **> 0** pendant un strafe réussi, **0** sinon.
      **C'est le chiffre à me donner si quelque chose cloche.**

### Ce qu'il faut sentir
- [ ] Le saut est **franc**, pas flottant (sinon : `Jump_ZVelocity` 900 ou `Gravity` 2.4)
- [ ] Le coyote time est **invisible** — il doit juste supprimer la frustration, jamais se remarquer
- [ ] L'air strafe est **apprenable** : on doit sentir qu'on y arrive mieux au 5ᵉ essai qu'au 1ᵉʳ

### Les deux curseurs, si ce n'est pas bon
| Symptôme | Clé à bouger | Sens |
|---|---|---|
| Le strafe ne donne rien / trop dur | `AirStrafe_WishSpeedCap` (60) | **monter** — c'est *le* curseur du modèle |
| Le strafe est gratuit, aucun skill | `AirStrafe_WishSpeedCap` | **baisser** |
| On vole, le contrôle aérien est trop fort | `AirStrafe_AirControl` (0.55) | **baisser** vers 0.2 — laisse le strafe Quake faire le travail |
| Le gain est correct mais trop lent | `AirStrafe_SpeedGainPerSec` (300) | monter |

**Ne change aucune valeur sans me le dire** — je répercute dans `07_TUNING` (R3).

### Ce qui n'est pas testable aujourd'hui
Bunny hop (J7), enchaînement slide → saut (J4), `Speed_HardCap` (rien n'atteint 6000 uu/s
avec le seul air strafe).
