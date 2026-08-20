# Journal — 2026-08-20 — J8 bis · Viser en slidant (`D53`)

**Temps effectif** : ~2 h
**Objectif** : rendre le slide compatible avec la visée, **sans toucher au demi-tour serré de `D26`**.
**Statut** : ⏳ **implémenté, compilé, vérifié en PIE — PAS ENCORE JOUÉ.** Rien n'est commité (R10).

---

## Le problème

Retour de Louis, laser en main : *« comme le slide est orienté avec la souris, quand on veut viser
en slidant ça nous fait tourner »*.

Depuis `D26` (J4), pendant un slide le vecteur vitesse pivote vers le regard à `Slide_TurnRate`
= 720 °/s. C'est ce qui donne le demi-tour en 0.25 s **validé manche en main** — on n'y touche pas.
Mais depuis le J8 le regard sert aussi à **viser**, et les deux usages se marchent dessus.

## La solution retenue par Louis — « option D : filtre passe-bas sur le cap »

Le slide ne suit plus le regard **instantané**, il suit un **cap** `SlideHeadingDir` qui ne réagit
qu'à la composante **soutenue** de l'orientation.

- Coup d'œil bref pour viser puis retour = excursion qui s'annule → le cap ne bouge presque pas.
- Direction **tenue** = consigne soutenue → le cap converge, le slide tourne comme avant.
- **Pas de zone morte, pas de seuil, pas de mode caché.** Un lissage continu, un seul curseur.

```
ENTRÉE DE SLIDE — InitSlideHeading()
  n = Normalize(Velocity.X, Velocity.Y, 0)
  SlideHeadingDir = |n| > 0.5 ? n : ActorForwardVector       ← le slide part LÀ OÙ ON VA

CHAQUE FRAME — UpdateSlideHeading(dt, AimDir)                ← 1ᵉʳ nœud exec de SlideStep
  target = Normalize(AimDir.X, AimDir.Y, 0)
  SlideHeadingDir = Normalize( VInterpTo(SlideHeadingDir, target, dt, Slide_HeadingFollowSpeed) )

VIRAGE (D26, inchangé)
  tgtYaw = MakeRotFromX(SlideHeadingDir).Yaw                 ← ex-regard direct
```

**Le lissage est vectoriel, jamais angulaire.** Un `RInterpTo` sur un yaw flottant casserait au
passage ±180° : viser derrière soi ferait faire au joueur un **tour complet**. `VInterpTo` +
normalisation n'a pas ce défaut.

---

## Fait — `Content/OVERDRIVE/Player/Components/BPC_Slide` uniquement

| Élément | Détail |
|---|---|
| Variable `SlideHeadingDir` | `Vector`, cat. `Slide`, **non** Instance Editable |
| Variable `TuneSlideHeadingFollowSpeed` | `float`, cat. `Slide`, Instance Editable (défaut BP `0.0`) |
| Fonction `InitSlideHeading()` | 14 nœuds — cap initial depuis `CMC.Velocity`, repli sur le regard |
| Fonction `UpdateSlideHeading(DeltaSeconds, AimDir)` | 10 nœuds — le filtre passe-bas |
| `CacheTuning` | 57 → **59** nœuds : lecture de `Slide_HeadingFollowSpeed` **depuis le DataAsset**, insérée juste avant `SetbTuningCached` |
| `StartSlide` | 19 → **20** nœuds : `InitSlideHeading()` appelée après `AddSpeedGain` |
| `SlideStep` | 93 → **95** nœuds : `UpdateSlideHeading` inséré **entre `FunctionEntry` et `GetFloorNormal`** ; le `MakeRotFromX` de la cible lit désormais `GetSlideHeadingDir` au lieu du `Select` regard/strafe |

Hors `BPC_Slide` : `PDA_MovementData` (+1 variable `Slide_HeadingFollowSpeed`, cat. `Movement|Slide`)
et `DA_Movement_Default` (**2.5**).

**Non touchés** : `BPC_MovementState`, `BPC_Dash`, `BPC_WallRide`, `BP_PlayerCharacter`,
`CrouchStep`, `UpdateSlidePhysics`, `SlidePhysicsStep`, `CheckSlideExit`, `EndSlide`.

---

## Décisions

| # | Décision | Doc |
|---|---|---|
| **D53** | **Le slide suit un cap lissé, pas le regard instantané.** Filtre passe-bas **vectoriel** sur la cible du virage, à `Slide_HeadingFollowSpeed`. `Slide_TurnRate`, la conservation de la norme et tout le reste de `D26` sont intacts. | `SPEC_MOVEMENT §4`, `07_TUNING §5` |
| **D53a** | **Le filtre s'applique à la cible de `D31` (`regard + strafe`), pas au regard seul.** La consigne littérale disait « forward de la `ControlRotation` aplati ». Les deux sont **identiques quand l'input de déplacement est nul** (`bUseControllerRotationYaw = true` ⇒ `ActorForwardVector` **est** le forward du regard aplati). Filtrer le regard seul aurait **supprimé le pilotage au strafe de `D31`**, validé au J4 et jamais remis en cause. J'ai donc amendé le modèle au lieu de le remplacer : `Q`/`D` infléchissent toujours la trajectoire, simplement à travers le même lissage. **À dire à Louis** — si le strafe doit rester instantané, c'est un fil de plus à couper, pas un réglage. | ce journal + `SPEC_MOVEMENT §4 D53` |
| **D53b** | **Le cap ne dérive jamais hors slide.** Sa seule écriture par frame vit dans `SlideStep`, atteint uniquement via `UpdateSlidePhysics` — le `switch` dont les pins `Dashing` / `WallRiding` ne sont branchés à rien (`D42`, `12_PIEGES §6.13`). Pendant un dash ou un wall ride le cap est **gelé** avec le reste du slide et retrouvé intact ensuite (`RestoreStateAfterDash`). Péremption bornée par `Dash_Duration` = 0.16 s. | `SPEC_MOVEMENT §4 D53` |

### Deux constantes numériques qui ne sont **pas** du tuning

- `0.5` dans `InitSlideHeading` : test « ce vecteur normalisé est-il unitaire ou nul ? ». C'est un
  contrôle de dégénérescence, pas une vitesse ni un seuil de gameplay — même famille que le `0.05`
  déjà présent dans `SlideStep` depuis `D31`. La vraie tolérance est celle de `Normalize` (1e-4).
- `Z = 0.0` dans les deux `MakeVector` : aplatissement, pas une valeur.

---

## Valeur ajoutée à `07_TUNING §5`

| Clé | Valeur | Unité | Statut |
|---|---|---|---|
| `Slide_HeadingFollowSpeed` | **2.5** | /s | **[À CALIBRER]** |

Monter ⇒ le slide colle au regard (à `+∞` on retrouve exactement `D26`, donc le bug).
Baisser ⇒ slide plus « lourd », visée plus libre, virages voulus plus lents.

---

## Vérifié

### Comptes de nœuds & accessibilité exec (2.2b / 2.2c / 2.31)

| Graphe | Avant | Après | Racines (topologiques) | Nœuds morts |
|---|---|---|---|---|
| `CacheTuning` | 57 | **59** | 1 | 0 |
| `StartSlide` | 19 | **20** | 1 | 0 |
| `SlideStep` | 93 | **95** | 1 | 0 |
| `InitSlideHeading` | 1 | **14** | 1 | 0 |
| `UpdateSlideHeading` | 1 | **10** | 1 | 0 |
| `CrouchStep` / `UpdateSlidePhysics` / `SlidePhysicsStep` / `TickSlide` | — | inchangés | 1 | 0 |

Racine définie par la **topologie** (sortie `Exec` + aucune entrée `Exec`), jamais par le nom (2.31).
Chaîne d'exec de `CacheTuning` relue nœud par nœud : 33 maillons, le nouveau `SetTuneSlideHeadingFollowSpeed`
en avant-dernière position, `SetbTuningCached` toujours en dernier.

### Contrôle `self` (2.21)

- `GetSlide_HeadingFollowSpeed.self` ← **directement** `K2Node_VariableGet_116` (le `Get MovementData`
  qui alimente déjà les 21 autres getters). Aucun nœud intercalé.
- `GetVelocity.self` ← directement `GetCachedCMC` ; `GetActorForwardVector.self` ← directement
  `GetCachedCharacter`. Types de pins conformes (`Movement Component` / `Actor`).

### Ordre d'évaluation (2.3b / 2.3c)

`UpdateSlideHeading` **écrit** `SlideHeadingDir`, et le getter pur qui le **relit** est tiré par
`SetVelocity`, donc plus loin dans la chaîne d'exec. La lecture est **postérieure** à l'écriture —
c'est voulu ici, et c'est l'inverse exact du piège 2.3b. Vérifié sur le graphe :
`FunctionEntry → UpdateSlideHeading → GetFloorNormal → SetVelocity → …`

### En PIE (`L_Sandbox_Movement`, spawn `(0, −3000, 300)`)

| Preuve | Relevé |
|---|---|
| `CacheTuning` a lu la clé **sur l'instance de jeu** | `tuneSlideHeadingFollowSpeed = 2.5` — le défaut du Blueprint est `0.0`, la valeur ne peut venir que de `DA_Movement_Default` |
| Le composant tick | `bWasGrounded = true`, `bTuningCached = true` |
| Rien d'autre n'a bougé | `tuneSlideTurnRate = 720`, `tuneSlideHoldTime = 1` |
| Cap **non initialisé** avant tout slide | `slideHeadingDir = (0, 0, 0)` |
| `InitSlideHeading` part de la **vélocité**, pas du regard | vélocité injectée `(0, 2000, 0)` + appui slide **dans le même script** (recette 4.11) → `slideHeadingDir = (0.0575, 0.9983, 0)`, soit **+Y**, alors que le regard est **+X**. Un cap initialisé sur le regard aurait donné `(1, 0, 0)` |
| `UpdateSlideHeading` tourne et **lisse** | le cap a déjà dérivé de **3.3°** vers le regard, et **6.9°** au relevé suivant. Norme = 1 aux deux relevés. À `Slide_HeadingFollowSpeed` = 2.5 /s on attend `α = 2.5 × dt` par frame : conforme |
| Le cap **gèle** hors slide (`D53b`) | dernier relevé : `bIsSliding = false` → `slideHeadingDir` figé à `(0.1200, 0.9928, 0)` malgré ~20 s de temps de jeu écoulé (piège 4.4) |

Compilation `BPC_Slide` + `PDA_MovementData` en **`warnings_as_errors`** : zéro erreur, zéro warning.
`save_assets` fait. Échafaudage de test **restauré et revérifié** : `IMC_Debug` remis à sa seule
entrée `F3` (contrôlé par relecture **et** par `git status` qui ne voit plus de diff sur l'asset),
`GameGetsMouseControl` remis à `false`.

### Non vérifiable par outil

Le **ressenti** : est-ce qu'on peut viser en slidant sans tourner, tout en gardant le demi-tour
serré quand on le veut ? C'est la seule question qui compte, et elle est pour Louis (R8).

---

## Pièges rencontrés — 2 entrées ajoutées à `12_PIEGES_OUTILLAGE.md`

### `2.33` 🔴 — le `type_id` d'un getter de variable d'une **autre** classe Blueprint

Il a fallu **9 formes d'id** pour lire `Slide_HeadingFollowSpeed` sur `PDA_MovementData`.
Les deux formes que l'outillage **affiche** sont toutes les deux inutilisables :

| Source | Forme affichée | `create_node` / `write_graph_dsl` |
|---|---|---|
| `read_graph_dsl` | `\|GetSlide_HeadingFollowSpeed` | ❌ *does not exist* |
| `find_node_types(context_pins=[pin PDA])` | `Variables\|Movement\|Slide\|GetSlideHeadingFollowSpeed` | ❌ *does not exist* |
| — | **`Class\|PDAMovementData\|GetSlideHeadingFollowSpeed`** | ✅ |

La règle : **`Class|<ClasseSansUnderscores>|Get<VariableSansUnderscores>`.**
`declaring_class` sur la classe générée (`…_C`) ne change rien. Et `find_node_types` **sans**
`context_pins` ne liste **aucun** getter d'une autre classe — pas même ceux déjà posés dans le
graphe qu'on interroge.

**Ce qui a tranché le diagnostic** : retenter la création avec un id **déjà présent dans le graphe**
(`|GetSlide_TurnRate`, posé au J4). Lui non plus n'est créable — donc ce n'était **pas** « la
variable est trop neuve » (2.19 / 5.20), c'était la **forme de l'id**. Sans ce contrôle sur un
élément déjà validé, j'aurais conclu à tort que la clé devait quitter le DataAsset.

### `2.34` ✅ — insérer un maillon plutôt que réécrire

Le réflexe était de réécrire `CacheTuning` en DSL. Ça aurait été **destructeur** : son DSL relu
contient `(Class|CapsuleCollision|GetCapsuleHalfHeight _movementdata)` — un artefact du lecteur
(2.6) pour un simple getter de variable du DataAsset. Réinjecté, il aurait posé de **vraies
fonctions moteur de capsule** avec un DataAsset en `self`, sur 6 clés de tuning. Recette
d'insertion (`create_node` + `break_pins` + 2 `connect_pins`) consignée.

---

## ⚙️ Checklist de test manuel (R8) — Louis

`L_Sandbox_Movement` en PIE. **`F3`** = overlay. Le curseur du jour est
**`Slide_HeadingFollowSpeed` = 2.5** dans `DA_Movement_Default` (`Data/DataAssets/`).

### 0. La question du jour, en 30 secondes
- [ ] Sprinter sur le plat, entrer en slide (`Ctrl`), **balayer la souris à gauche puis revenir**
      comme pour viser une cible de côté → **la trajectoire ne doit pas partir de travers.**
      Tu dois pouvoir aligner un tir sans que le corps suive
- [ ] Même chose vers une cible **derrière** toi : regarder en arrière, tirer, revenir devant →
      **aucun tour complet**, aucun à-coup. Si le joueur pivote sur lui-même, dis-le moi
      immédiatement, ça voudrait dire que le lissage est reparti en angles (il ne doit pas)

### 1. Le demi-tour serré doit être INTACT
- [ ] Sprinter, entrer en slide, **tourner la souris à 180° et TENIR le nouveau cap**
- [ ] Le corps doit suivre — un peu plus tard qu'avant, mais **complètement**, et
      **`SPEED` en sortie = `SPEED` en entrée** (aucun uu/s perdu)
- [ ] Si le demi-tour est devenu **mou / mou trop longtemps** → c'est
      **`Slide_HeadingFollowSpeed`** qu'il faut monter (3.5, 5), **pas** `Slide_TurnRate` (720,
      ne pas y toucher)
- [ ] Si viser fait **encore** tourner → baisser `Slide_HeadingFollowSpeed` (1.5, 1.0)

### 2. L'entrée en slide
- [ ] Courir **en regardant sur le côté** (strafe + souris tournée) puis `Ctrl` →
      le slide doit partir **dans la direction où tu allais**, pas d'un coup vers le regard.
      C'est le changement de `InitSlideHeading`
- [ ] Entrer en slide **à l'arrêt** (vitesse nulle) → aucun comportement bizarre,
      le cap part du regard

### 3. Ce qui ne doit PAS avoir changé — régressions à chasser
- [ ] `Q`/`D` infléchissent toujours la trajectoire en slide (`D31`) — **mais désormais lissé** :
      un tap de `D` ne fait presque rien, `D` **tenu** fait tourner. **Dis-moi si le strafe doit
      redevenir instantané** : c'est un choix que j'ai tranché seul (`D53a`), il se défait en 1 nœud
- [ ] Pentes (zone C) : `slope` toujours ≈ 0.26 / 0.50 / 0.71 à 15/30/45°, on accélère en descente,
      on freine en montée
- [ ] Tunnel (zone B) : on le traverse d'un slide, `forced` passe à `true` sous le plafond,
      **on peut toujours ramper pour sortir** (jamais figé)
- [ ] Bords de plateforme : on tombe normalement en slidant, pas de mur invisible
- [ ] **Slide → Dash → slide** : le dash part, et à la sortie le slide reprend **sans à-coup de
      direction**. Le cap est gelé pendant le dash (`D53b`) — si tu sens une embardée à la sortie
      du dash, c'est là qu'il faut regarder
- [ ] Slide → `Espace` : le saut part, `SPEED` intacte
- [ ] Wall ride : inchangé

### Ce qu'il faut sentir
- [ ] **Viser en slidant est un geste libre**, pas un compromis
- [ ] Le slide a peut-être gagné un peu de « poids » — dis-moi si c'est agréable ou si c'est mou.
      Un seul chiffre pilote ça

**Ne change aucune valeur sans me le dire** — je répercute dans `07_TUNING` (R3).
**Rien n'est commité** : je le fais après ton retour (R10).
