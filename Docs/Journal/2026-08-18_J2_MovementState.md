# Journal — 2026-08-18 — Jour 02

**Temps effectif** : ~3 h
**Objectif du jour (roadmap)** : J2 — `BPC_MovementState`, sprint, overlay debug.

---

## Fait

### `PDA_MovementData` / `DA_Movement_Default`
- Ajout de **3 clés manquantes** : `Speed_IdleThreshold` (50), `Input_MoveDeadZone` (0.05),
  `SpeedLoss_RecoveryGrace` (0.5). Les deux premières n'existaient nulle part et étaient
  nécessaires (résolution d'état + deadzone d'input) → ajoutées à `07_TUNING §3` avec `[À CALIBRER]`.
  La troisième existait déjà dans `07_TUNING §10` mais manquait dans le DataAsset.

### `BPC_MovementState` (`Player/Components/`) — **cœur du J2**
Composant `ActorComponent`, 33 variables, 6 dispatchers, 21 fonctions.

- **Variables** conformes à `SPEC_MOVEMENT §2.1`, réparties en catégories
  `Movement` · `Movement|Runtime` · `Movement|Internal` · `Movement|Cached` · `Debug`.
  `MovementData` pointe `DA_Movement_Default` par défaut, `bDebugEnabled = true` (dev).
- **`CacheTuning()`** au `BeginPlay` : les 13 valeurs lues chaque frame sont mises en cache dans
  des variables `Tune_*` (`SPEC_MOVEMENT §2.1` : « aucun Get de `DA_Movement_Default` en Tick »).
  Ce sera aussi le point de re-cache sur `OnUpgradesApplied` (`BPC_PlayerStats`, J20).
- **`BeginPlay`** : cache `CachedCharacter` / `CachedCMC`, appelle
  `AddTickPrerequisiteComponent(CachedCMC)` — le piège n°1 de `SPEC_MOVEMENT §15`
  (sinon le CMC écrase nos écritures de `Velocity` une frame sur deux).
- **Boucle de Tick** (`SPEC_MOVEMENT §2.4`), dans l'ordre :
  1. `bIsGrounded`, `HorizontalSpeed` (`VectorLengthXY`), `VerticalSpeed`
  2. *(résolution d'état — manquante, cf. « Pas fait »)*
  3. `UpdateSpeedCap` — rampe de sprint + override (dash / wall ride)
  4. `UpdateGrace` — décrément + `OnGraceExpired`
  5. `ApplyMomentumDecay` — au sol, hors grace, au-dessus du cap
  6. `DriveCMC` — `MaxWalkSpeed = Max(cap, speed)`, `MaxAcceleration`, `GravityScale`
  7. *(air strafe — J3)*
  8. `ClampToHardCap`
  9. `BroadcastSpeed` (seuil `SpeedBroadcastMinDelta`)
  10. `DrawDebugOverlay`
- **API publique** posée pour les composants des J4–J6 : `SetHorizontalSpeed`, `AddSpeedGain`,
  `ApplySpeedPenaltyPercent`, `SetSpeedCapOverride` / `ClearSpeedCapOverride`, `StartGrace`,
  `GetHorizontalSpeed`, `GetSpeedRatio01`, `IsGrounded`.
- **Dispatchers** : `OnMovementStateChanged`, `OnSpeedChanged`, `OnSpeedGained`,
  `OnSpeedPenaltyApplied`, `OnLandedSpeed`, `OnGraceExpired`.

### Sprint (`SPEC_MOVEMENT §3`)
`CurrentSpeedCap` interpolé `Speed_Walk → Speed_SprintCap` en `Sprint_TimeToMax`
(`FInterpTo Constant`, vitesse = `(SprintCap − Walk) / TimeToMax`).
Garde `Sprint_RequiresForwardInput` via `Input_MoveDeadZone`.
**Le cap est figé en l'air** (`target = cap courant` si `!bIsGrounded`) : le sprint ne peut pas
« retomber » à la vitesse de marche pendant un saut, conforme à « perte du sol → le cap reste ».
Le sprint n'accélère jamais au-delà du cap : c'est un **plancher**, la décroissance fait le reste.

### Overlay debug (`SPEC_MOVEMENT §13.1`)
4 lignes à l'écran via `PrintString` (Key stable, `Duration 0`, pas de log) :
`SPEED / HUD / VZ` · `CAP / GRACE / GROUND` · `GAIN + source + âge` · `CMC MaxWalkSpeed / MaxAccel / GravityScale`.
Toggle par `IA_DebugToggle` (F1). **La ligne `STATE` manque** (dépend de l'enum).

### `BP_PlayerCharacter`
- Composant `MovementState` ajouté.
- Variables `CachedMoveInput`, `DefaultMappingContext` (→ `IMC_Gameplay`),
  `DebugMappingContext` (→ `IMC_Debug`), toutes `Instance Editable`.
- `BeginPlay` : `AddMappingContext` des deux IMC (priorités 0 et 1).
- Fonctions `HandleMoveInput`, `HandleLookInput`, `SetSprintInput`, `ToggleMovementDebug`.
- Événements Enhanced Input câblés : `IA_Move` (Triggered + Completed → reset à zéro),
  `IA_Look` (Triggered), `IA_Sprint` (Started/Completed), `IA_DebugToggle` (Started).
- Suppression de 2 nœuds d'event orphelins hérités du template (`Event Tick`, `ActorBeginOverlap`) :
  un `Event Tick` présent, même vide, active le tick de l'acteur (`06_CONVENTIONS §4.6`).

---

## Pas fait / reporté

- **La machine à états.** Le toolset MCP ne sait créer **ni variable ni paramètre typé enum**
  (`add_variable` n'accepte que les primitives et 5 structs, `add_object_variable` refuse un
  `UserDefinedEnum`). C'est le même trou d'outillage que les entrées d'enum (J1, D6).
  Manquent donc : `CurrentState`, `PreviousState`, `RequestState`, `CanEnterState`,
  `GetCurrentState`, `ResolveState`, et la ligne `STATE` de l'overlay.
  → **Saisie manuelle par Louis**, liste exacte en fin de fichier. Je remplis la logique ensuite.
- **Gate de décroissance sur l'état** (`SPEC_MOVEMENT §2.4-5` : `CurrentState ∈ {Idle, Walking, Sprinting}`).
  Aujourd'hui la garde est `bIsGrounded` seule — strictement équivalente tant que `BPC_Slide`
  n'existe pas (J4). **À rebrancher au J4**, sinon le slide sera rongé par la décroissance.
- **Timer 20 Hz `MPC_Global.PlayerSpeed01`** (`SPEC_MOVEMENT §2.5`) : `MPC_Global` n'existe pas
  avant le J14, et les clés `SpeedLines_StartSpeed` / `_FullSpeed` ne sont pas dans le DataAsset.
- **Jump / coyote / buffer** : c'est le J3, pas le J2. Sans saut, seuls le sprint, la marche et
  la décroissance sont testables aujourd'hui.
- Pas de playtest de ma part (R8) — cf. checklist ci-dessous.

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| **D7** — `BPC_MovementState` ne lit **jamais** l'input : `BP_PlayerCharacter` le **pousse** via `SetMoveInput(Vector2D)` et `SetSprintHeld(bool)`. `SPEC_MOVEMENT §1.1` dit « ne connaît pas les inputs » mais §2.4/§7 ont besoin de l'input dans le Tick. Le push respecte la règle : le composant reçoit une donnée, il ne connaît pas Enhanced Input. `CachedMoveInput` existe des deux côtés (le character en a besoin pour la direction de dash au J5). | `Docs/Specs/SPEC_MOVEMENT.md` §2.1/§2.2 ✅ |
| **D8** — Les valeurs de tuning lues chaque frame sont mises en cache dans des variables préfixées **`Tune_`** (catégorie `Movement|Cached`). Aucune convention n'existait ; `T_` était pris par les textures. | `Docs/06_CONVENTIONS.md` §2 ✅ |
| **D9** — `Content/Input/` (template First Person) **supprimé**. Ses `IA_Move` / `IA_Look` / `IA_Jump` portaient les mêmes noms que les nôtres et l'éditeur liait les nœuds d'input au mauvais asset, sans moyen de désambiguïser par outil. Zéro référence entrante. **Validé par Louis.**<br>⚠️ La suppression du dossier a aussi emporté `Content/Input/Touch/` (`BPI_TouchInterface`, `UI_Thumbstick`, `UI_TouchSimple`) — **9 assets au total**, pas 6 comme annoncé au moment de la question. Sans impact : `Config/DefaultInput.ini` a `DefaultTouchInterface=None` et `bAlwaysShowTouchInterface=False`, et le tactile est hors scope (PC Windows uniquement, `CLAUDE.md §4`). Restaurable via `git checkout` si besoin. | `Docs/04_ROADMAP.md` J1 ✅ |
| **D10** — `Speed_IdleThreshold` et `Input_MoveDeadZone` créées (R3 : pas de nombre en dur). | `Docs/07_TUNING.md` §3 + §19 ✅ |
| **D1 (rappel)** — validée : `Content/LevelPrototyping/` est supprimé **après le J4**, pas avant. | `Docs/04_ROADMAP.md` J1 + J4 ✅ |
| **D11** — **Clavier de référence = AZERTY.** UE mappe par caractère produit, pas par position physique : `W A S D` disperse les touches sur un clavier français. Passage à **`Z Q S D`**, et le dash passe de `Q` à **`A`** (même position physique qu'avant, et `Q` est désormais pris par le déplacement). Support QWERTY = rebinding, backlog post-v1. Décidé sur playtest de Louis. | `Docs/09_INPUT.md` §1 ✅ |
| **D12** — **`IA_DebugToggle` passe de `F1` à `F3`.** `F1` est le raccourci **Wireframe** du viewport éditeur (codé en dur dans `FEditorViewportCommands`, absent des `.ini`) : chaque appui basculait le rendu en fil de fer pendant le PIE. `F3` retenu par Louis, atteinte du jeu vérifiée en PIE. Replis testés et libres si le viewport réagit aussi : `F5`, `F6`. | `Docs/11_ARBITRAGES.md` D15 + `09_INPUT.md` ✅ |

## Valeurs modifiées

| Clé | Ancien | Nouveau | Raison |
|---|---|---|---|
| `Speed_IdleThreshold` | *(inexistante)* | `50` uu/s | Seuil de bascule vers `Idle` |
| `Input_MoveDeadZone` | *(inexistante)* | `0.05` | Deadzone de `IA_Move`, était en dur dans la spec |
| `SpeedLoss_RecoveryGrace` | *(absente du DataAsset)* | `0.5` s | Existait dans `07_TUNING §10`, manquait dans `PDA_MovementData` |

## Ressenti de playtest

Playtest de Louis, 2026-08-19, après correction du bug d'input :

- **Marche à 1000, sprint à 1500, « sans à-coup »** — la rampe `Sprint_TimeToMax = 0.6 s` passe
  le test, aucun effet « collant ». Pas de retuning nécessaire.
- Sprint refusé en marche arrière : conforme. Relâcher Shift fait redescendre le cap proprement.
- `GROUND` bascule bien à `false` en chute.
- Overlay debug lisible, toggle fonctionnel.

**Rien à retuner au J2.** Les valeurs de `07_TUNING §3–§4` restent telles quelles ; elles ne seront
vraiment jugeables qu'avec le saut (J3) et le slide (J4), quand il deviendra possible de dépasser
le cap et donc d'éprouver la décroissance de momentum.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| **Aucun input en PIE** — ni déplacement ni caméra. Les `IMC_*` créés par outillage au J1 ont leurs mappings dans le tableau **déprécié `Mappings`** au lieu de **`DefaultKeyMappings`**, seul évalué par UE 5.8. Contexte appliqué (`HasMappingContext` = `true`) mais **vide** : aucune action ne se déclenche jamais, et **aucune erreur nulle part**. | **Bloquant** | Oui — 14 mappings migrés sur `IMC_Gameplay`, 1 sur `IMC_Debug`. Vérifié : `W` → `MoveInput (0, 1)` |
| `get_node_type_pins` instancie un nœud temporaire dans le graphe interrogé. Sans surveillance, ça laisse des nœuds orphelins. | Faible (piège) | Contourné — interroger un graphe puis vérifier avec `read_graph_dsl` |
| Les type_ids du DSL de graphe qui contiennent des parenthèses (`Math|Float|Clamp(Float)`, `Utilities|String|ToString(Float)`) cassent le parseur S-expression. | Moyen | Contourné — `select` à la place de `Clamp`/`Min`/`Max`, et **autocast implicite** float→String sur les pins de `Append` |
| Premier appel positionnel sur une fonction membre (`(CallFunction|Foo x)`) : l'argument part sur le pin `self`, pas sur le premier paramètre. | Faible | Contourné — toujours nommer les pins (`:NewSpeed x`) |
| `arrange_nodes` ne fait rien (0 graphe arrangé, sans erreur). | Cosmétique | Non — les nœuds sont positionnés par le writer DSL, c'est lisible |
| **Faux négatif de mon harnais de test.** `SlateInspectorToolset.PressKey` n'atteint le jeu que si `Game Gets Mouse Control` est actif. Après l'avoir remis à `false`, j'ai conclu à tort que `F3` ne fonctionnait pas. | Moyen (méthode) | Oui — réactiver le réglage **le temps du test** puis le remettre. `F3` fonctionne bien. |

## Demain

- **Aucun préalable bloquant.** Les 13 enums sont remplis, la machine à états est complète et
  vérifiée en jeu, l'input fonctionne.
- J3 — Jump, coyote time, jump buffer, air strafe (modèle Quake), conservation à l'atterrissage.
  L'air strafe s'insère à l'**étape 7 du Tick**, entre `DriveCMC` et `ClampToHardCap`
  (`SPEC_MOVEMENT §2.4`). `StartGrace` et le hard clamp sont déjà en place.
- Premier vrai test de la **décroissance de momentum** : c'est le J3/J4 qui permettra enfin de
  dépasser `Speed_SprintCap`, donc de juger `MomentumDecayRate` et `MomentumDecay_GraceTime`.

---

## ⚙️ À faire à la main dans l'éditeur (Louis) — ~5 min

Dans **`BPC_MovementState`** :

| # | Élément | État |
|---|---|---|
| 1 | Variable `CurrentState` — `E_MovementState`, cat. `Movement\|Runtime` | ✅ fait |
| 2 | Variable `PreviousState` — idem | ✅ fait |
| 3 | Fonction `RequestState(NewState: E_MovementState) → bAccepted: bool` | ✅ fait |
| 4 | Fonction `CanEnterState(NewState: E_MovementState) → bCanEnter: bool` | ✅ fait (impure, cf. ci-dessous) |
| 5 | Fonction `GetCurrentState() → E_MovementState` **Pure** | ✅ fait |
| 6 | Dispatcher `OnMovementStateChanged` — params `OldState` / `NewState` : `E_MovementState` | ✅ fait |
| 7 | `GetHorizontalSpeed` · `IsGrounded` · `GetSpeedRatio01` cochées **Pure** | ✅ fait |

Les corps ont été remplis à l'outil au fur et à mesure. **Tout est clos au 2026-08-19.**

`CanEnterState` reste volontairement **impure** : `RequestState` l'appelle par exec, la passer
en Pure casserait le graphe. Divergence assumée avec `SPEC_MOVEMENT §2.2`.

Le flag `Pure` n'est **pas exposé par l'outillage** (`K2Node_FunctionEntry.ExtraFlags` illisible
en MCP) — c'est un cochage manuel, comme les enums.

---

## Vérification finale (2026-08-19, en PIE)

Chaîne complète validée bout en bout, sans instrumentation :

| Vérifié | Résultat |
|---|---|
| Compilation, `warnings_as_errors` | 4/4 (composant, character, PC, PDA) |
| État au repos | `Idle`, cap 1000, `bIsGrounded` true |
| `Z` → `IA_Move` → `AddMovementInput` | `HorizontalSpeed = 1000.0` — pile `Speed_Walk` |
| Machine à états | `Idle → Walking`, `PreviousState = Idle` |
| `F3` → `IA_DebugToggle` | `bDebugEnabled` bascule |
| Erreurs runtime | **0** |

## Vérifications de fin de journée

- [x] Tous les BP recompilés, zéro warning (`compile_blueprint` en `warnings_as_errors`)
- [x] 3 minutes de jeu réel — checklist passée par Louis, tout OK
- [x] Roadmap cochée
- [x] Tuning à jour (§3 + §19) — aucune valeur modifiée au playtest
- [x] Commit fait

## Checklist de test manuel (R8)

Lancer `L_Sandbox_Movement` en PIE. L'overlay debug doit s'afficher immédiatement (F1 pour couper).

**Ce qu'il faut regarder**
- [ ] ZQSD déplace, la souris tourne, le regard n'est pas inversé
- [ ] Sans sprint, `SPEED` se stabilise à **1000** (`Speed_Walk`) et `CAP` affiche 1000
- [ ] Shift maintenu vers l'avant : `CAP` monte de 1000 à **1500** en ~0,6 s, sans à-coup
- [ ] `SPEED` se stabilise **exactement** à 1500, jamais au-dessus
- [ ] Shift + marche arrière : pas de sprint (`Sprint_RequiresForwardInput`)
- [ ] Shift relâché : `CAP` redescend vers 1000 à la même vitesse
- [ ] `GROUND` passe à `false` en tombant du bord, `VZ` devient négatif
- [ ] `CMC MaxWalkSpeed` suit toujours `CAP` (jamais bloqué à 1000)
- [ ] F1 coupe et rallume l'overlay

**Ce qu'il faut sentir**
- [ ] La montée en vitesse du sprint ne donne pas l'impression d'être « collante »
- [ ] 1500 uu/s **paraît** rapide dans le sandbox, ou c'est un signal pour retuner

**Ce qui n'est pas testable aujourd'hui** : décroissance de momentum (rien ne dépasse encore le cap
sans slide/dash/bunny hop), machine à états, saut.
