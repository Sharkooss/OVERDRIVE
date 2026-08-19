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

## ⛔ Régression introduite puis corrigée le même jour — à lire

**Le premier commit du J3 (`f8b7b0b`) cassait tout le jeu.** Louis l'a constaté immédiatement :
plus d'overlay `F3`, plus de sprint, pas de saut. Chronologie et leçons.

### Le bug

`EventBeginPlay` appelait **`SetComponentTickEnabled(false)`**. J'avais écrit la ligne en positionnel :

```
(Components|Tick|SetComponentTickEnabled true)
```

L'argument positionnel part sur le pin **`self`** (piège connu, documenté dans mes propres notes).
Le booléen a été silencieusement jeté et le pin `bEnabled` est resté à son défaut `false`.
**Le Tick de `BPC_MovementState` était donc désactivé dès le `BeginPlay`.**

Tout en découle par une seule cause : pas de Tick → pas de `DrawDebugOverlay` (F3 bascule un booléen
que plus personne ne lit), pas de rampe de sprint, et surtout `bIsGrounded` jamais mis à jour →
`TryJump` échoue systématiquement sa garde.

La ligne d'à côté avait le même défaut : `AddTickPrerequisiteComponent` avait le CMC sur `self` et
son pin `PrerequisiteComponent` **vide** — le correctif du piège n°1 de `§15` était mort lui aussi.

### Pourquoi la vérification ne l'a pas vu

Elle **l'avait vu**. Le relevé PIE affichait `bIsGrounded = false` et `MaxAcceleration = 2048`
(le défaut moteur, pas nos 4000) : le Tick ne tournait pas. J'ai attribué ça à
« l'éditeur n'a pas le focus » et j'ai commité.

La donnée qui tranchait était disponible et je ne l'ai pas cherchée : `CMC.MovementMode` valait
**`MOVE_Walking`**, donc le personnage avait atterri, donc **le monde ticke**. Seul notre composant
était mort. Une hypothèse d'environnement invoquée sans la tester coûte plus cher que pas de
vérification du tout : elle donne une fausse assurance.

### Deuxième erreur : `write_graph_dsl` empile, il n'écrase pas

En cherchant la cause j'ai découvert que l'`EventGraph` contenait **101 nœuds** : 5 copies de la
chaîne de Tick, dont 4 orphelines datant du **J2**. `write_graph_dsl` **ajoute** les nœuds sans
supprimer les anciens, et `read_graph_dsl` ne montre que la chaîne branchée — les orphelines sont
invisibles. C'est ce qui a masqué le problème.

Le nettoyage automatique que j'ai lancé ensuite a **supprimé les 5 events Enhanced Input** de
`BP_PlayerCharacter` : `find_nodes(entry_points_only=True)` ne les considère pas comme des points
d'entrée, donc mon calcul d'accessibilité les classait morts. Reconstruits à la main
(`create_node` + `connect_pins`), vérifiés nœud par nœud.

### Règles qui en sortent

1. **Ne jamais écrire un argument en positionnel** dans le DSL, même en recopiant la sortie de
   `read_graph_dsl` — qui, elle, écrit en positionnel. Toujours `:NomDuPin valeur`.
2. **Après écriture, relire les *valeurs de pins*, pas seulement le DSL.** Un argument perdu laisse
   le défaut du pin (`false`, `0.0`) : le graphe compile, la relecture DSL paraît correcte, et le
   comportement est faux. Un balayage « pin non connecté ET valeur vide » ne suffit pas — `false`
   n'est pas vide.
3. **`write_graph_dsl` empile.** Après chaque écriture, compter les nœuds
   (`find_nodes(graph, title="")`) et purger l'accessibilité par **exec**, en traitant les events
   Enhanced Input comme des points d'entrée (`find_nodes(entry_points_only=True)` les rate).
4. **Une hypothèse d'environnement se teste, sinon elle ne compte pas.** Ici : une seule propriété
   (`MovementMode`) séparait « le monde ne ticke pas » de « notre composant ne ticke pas ».

---

## Vérification (2026-08-19, après correction)

En jeu, en PIE, input simulé — `bThrottleCPUWhenNotForeground` est à `false` sur ce poste, donc PIE
tourne à 60 fps même sans focus et le test bout en bout est fiable :

| Vérifié | Résultat |
|---|---|
| Compilation `warnings_as_errors` | **2/2** |
| Le Tick tourne | `MaxAcceleration` = **4000** (`Accel_Ground`, écrit par `DriveCMC`), `bIsGrounded` = **true**, `LastGroundedTime` incrémenté chaque frame |
| **F3** → `IA_DebugToggle` | `bDebugEnabled` bascule `true` → `false` ✅ |
| **Espace** → `IA_Jump` → `TryJump` → `DoJump` | `Idle → Jumping`, `VerticalSpeed` = **860.8** (900 − 1 frame de gravité) ✅ |
| Cycle d'atterrissage | `PreviousState` = `Falling`, `LandedTime` = 22.97 s pour un saut à 22.19 s → **0,77 s d'air**, conforme à `Jump_ZVelocity 900` / `Gravity 2.4` ✅ |
| `HandleLanded` s'exécute | `bJumpConsumed` remis à `false`, `JumpBufferedTime` = `-1` ✅ |
| `Tune_AirStrafeGainAngleCos` | **−0.7071** = `cos(135°)` ✅ conforme à `§7.1` |
| Graphes purgés | `BPC_MovementState` 101 → 35 nœuds, doublons J2 inclus ; `BP_PlayerCharacter` 24 nœuds, 5 events d'input recâblés |
| Erreurs runtime | **0** |

**Ce qui reste non vérifié, et ne peut pas l'être par un agent :** le *ressenti*. L'air strafe n'a
pas été éprouvé manche en main — c'est la checklist ci-dessous, et c'est la R8.

---

## Playtest de Louis n°2 — le strafe ne dépassait jamais 1500

> « le strafe ne marche pas, ça ne dépasse jamais 1500 · le air control est trop faible, aucune
> sensation · le air gain augmente rarement et ça demande de trop bouger la souris, du coup je perds
> tout le momentum »

Trois symptômes, **un bug et un problème d'échelle**.

### Le bug : `DriveCMC` s'exécutait avant l'air strafe

`DriveCMC` écrit `CMC.MaxWalkSpeed = Max(CurrentSpeedCap, HorizontalSpeed)`. Placé à l'étape 6, il
calculait ce plafond à partir de la vitesse **d'avant** le gain d'air strafe (étape 7). Le CMC, qui
tick en premier à la frame suivante, reclampait la vélocité horizontale sur ce plafond périmé
(`CalcVelocity` → `GetClampedToMaxSize2D`) et **effaçait le gain de la frame précédente**.

Chaque frame ajoutait ~5 uu/s, chaque frame suivante les reprenait. Plafond dur à `Speed_SprintCap`,
strafe ou pas. Ça expliquait aussi le contrôle aérien « mou » : à 1500 = `MaxWalkSpeed`, toute
accélération latérale était reclampée en norme.

Ordre corrigé — **`DriveCMC` passe en dernier**, après toute écriture de `Velocity` :

```
… DECAY → AIR_STRAFE → HARD_CLAMP → DRIVE_CMC → BROADCAST → DEBUG
```

Règle générale ajoutée à `SPEC_MOVEMENT §7.4` : elle vaudra aussi pour le dash (J5), le wall ride
(J6) et le bunny hop (J7), qui écrivent tous `Velocity`.

### Le problème d'échelle : les constantes étaient celles de Quake, pas les nôtres

Quake court à `320 u/s` avec `wishspeed = 30` et `sv_airaccelerate = 10` (≈ `300 u/s²` effectifs).
OVERDRIVE sprinte à `1500 uu/s` — un facteur **≈ 4.7**. Les valeurs de `07_TUNING §7` reprenaient les
chiffres de Quake **sans les rééchelonner** : la fenêtre de gain était ~2,5× trop étroite et le gain
~4× trop lent. D'où « il faut trop bouger la souris » — mathématiquement exact : avec
`WishSpeedCap = 60` à 1500 uu/s, il fallait un `WishDir` quasi parfaitement perpendiculaire.

| Clé | Avant | Après | Raisonnement |
|---|---|---|---|
| `AirStrafe_WishSpeedCap` | 60 | **150** | `30 × 4.7` — élargit la fenêtre de gain |
| `AirStrafe_SpeedGainPerSec` | 300 | **1200** | `300 × 4.7 ≈ 1400`, arrondi prudent. C'est **le** clamp actif |
| `AirStrafe_MaxAccel` | 2500 | **4000** | doit rester au-dessus du précédent, sinon il redevient le clamp |
| `AirStrafe_GainAngleMax` | 45 | **60** | seuil `cos(150°) = −0.866` au lieu de `cos(135°) = −0.707` |
| `AirStrafe_AirControl` | 0.55 | **0.85** | réponse au « aucune sensation de contrôle aérien » |
| `Accel_Air` | 2500 | **4000** | multiplicande d'`AirControl` : `0.85 × 4000 = 3400 uu/s²` |

**Note pour plus tard :** ces deux clés sont solidaires de `Speed_SprintCap`. Si le sprint cap bouge,
`WishSpeedCap` et `SpeedGainPerSec` doivent bouger dans le même rapport, sinon le strafe se
redésaccorde silencieusement. Consigné dans `07_TUNING §7`.

### Vérifié en PIE

2500 uu/s injectés dans la vélocité en plein vol : `PreLandSpeed = 2500` au moment du contact.
Le momentum au-dessus du sprint cap **survit maintenant à toute la phase aérienne**.
Avant le correctif, il était ramené à 1500 en une à deux frames.

Les 6 valeurs sont bien relues par `CacheTuning` au `BeginPlay`
(`Tune_AirStrafeGainAngleCos = −0.866` ✅).

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
