# SPEC — MOVEMENT

> Spec d'implémentation du système de mouvement d'OVERDRIVE. **Blueprint only (R1).**
> Aucune valeur numérique ici : toutes les clés renvoient à `Docs/07_TUNING.md`.
> Assets : `Docs/05_ARCHITECTURE.md`. Nommage : `Docs/06_CONVENTIONS.md`. Données : `Docs/08_DATA_SCHEMAS.md`.
> Toutes les valeurs sont lues depuis `DA_Movement_Default` (`PDA_MovementData`), jamais en dur.

---

## 1. Vue d'ensemble

### 1.1 Qui pilote quoi

| Acteur | Responsabilité | Interdit |
|---|---|---|
| `CharacterMovementComponent` (CMC) | Moteur physique : gravité, collision, step-up, `MOVE_Walking/Falling/Flying` | Ne pas le remplacer |
| `BPC_MovementState` | **Seul propriétaire** de `E_MovementState`. Vitesse interne, momentum, décroissance, grace, air strafe, pilotage frame par frame du CMC | Ne connaît pas les inputs |
| `BPC_Slide` | Logique de slide uniquement. Demande l'état, ne l'écrit pas | Ne touche pas au momentum global |
| `BPC_Dash` | Charges, cooldown, direction, profil de vélocité | idem |
| `BPC_WallRide` | Traces murales, accroche, wall jump, cooldown same-wall | idem |
| `BP_PlayerCharacter` | Reçoit les inputs Enhanced Input, appelle `TryStartX()` sur les composants, relaie les dispatchers vers le HUD | Aucune logique de mouvement |
| `BPC_PlayerStats` | Applique les upgrades sur les valeurs lues de `DA_Movement_Default` | — |

**Règle de flux** : `Input → BP_PlayerCharacter → BPC_<Mécanique>.TryStartX() → BPC_MovementState.RequestState() → (accepté ?) → la mécanique s'exécute.`
Un composant qui n'obtient pas l'état **annule silencieusement** sa mécanique et ne consomme aucune ressource (charge, cooldown).

### 1.2 Machine à états `E_MovementState`

```
                       ┌──────────────────────────────────────────────┐
                       │                  DASHING                     │
                       │  transitoire — entrable depuis TOUT état     │
                       │  sauf Dashing. Sortie => recalcul d'état     │
                       └──────────────────────────────────────────────┘
                          ▲  IA_Dash + charge dispo          │ fin (Dash_Duration)
     ─────────────────────┴──────────────────────────────────┴─────────────────────

        ┌────────┐  input mvt   ┌─────────┐  IA_Sprint + fwd  ┌───────────┐
        │  IDLE  │◄────────────►│ WALKING │◄─────────────────►│ SPRINTING │
        └────────┘   speed~0    └─────────┘   relâche/recul   └───────────┘
             │                       │                              │
             │ IA_Jump               │ IA_Jump                      │ IA_Slide
             │                       │                              │ ET Speed >= Slide_MinEntrySpeed
             │                       │                              ▼
             │                       │                        ┌──────────┐
             │                       │                        │ SLIDING  │
             │                       │                        └──────────┘
             │                       │                              │
             │                       │      IA_Jump / fin timer / vitesse < seuil / dé-crouch OK
             ▼                       ▼                              ▼
        ┌──────────────────────────────────────────────────────────────┐
        │                          JUMPING                             │
        └──────────────────────────────────────────────────────────────┘
                                    │ VelZ <= 0
                                    ▼
        ┌──────────────┐   accroche mur valide    ┌──────────────┐
        │   FALLING    │◄────────────────────────►│  WALLRIDING  │
        └──────────────┘   wall jump / fin / plus └──────────────┘
                │           de mur / input opposé
                │ Landed
                ▼
        retour IDLE | WALKING | SPRINTING  (selon input + vitesse)
```

### 1.3 Table de transitions autorisées

| Depuis \ Vers | Idle | Walking | Sprinting | Sliding | Jumping | Falling | WallRiding | Dashing |
|---|---|---|---|---|---|---|---|---|
| **Idle** | — | oui | non¹ | **oui**² | oui | oui | non | oui |
| **Walking** | oui | — | oui | **oui**² | oui | oui | non | oui |
| **Sprinting** | non | oui | — | oui | oui | oui | non | oui |
| **Sliding** | non | oui | oui | — | oui | oui | non | oui |
| **Jumping** | non | non | non | non | — | oui | oui | oui |
| **Falling** | oui | oui | oui | non³ | non⁴ | — | oui | oui |
| **WallRiding** | non | non | non | non | oui⁵ | oui | non | oui |
| **Dashing** | oui | oui | oui | oui | oui | oui | oui | — |

¹ passe obligatoirement par `Walking` (le sprint exige de la vitesse).
² **Modifié au J4 (D23), sur décision de Louis.** La table exigeait auparavant de passer par `Sprinting`,
ce qui contredisait `Slide_MinEntrySpeed` (900, soit **sous** `Speed_Walk` = 1000) : `Ctrl` en marche
simple ne faisait rien. **Le slide ne dépend plus de l'état, seulement de la vitesse.** La seule garde
est `HorizontalSpeed >= Slide_MinEntrySpeed`, comme le décrit `§4.1 [2]`.
En dessous du seuil, `TryStartSlide` fait un **`Crouch()` simple** — le joueur a un retour, il ne se
demande pas si la touche est cassée. Relâcher `IA_Slide` déclenche `ReleaseCrouch()`.
³ le slide en l'air est **bufferisé**, pas exécuté (cf. §11). ⁴ le double saut n'existe pas (`Jump_MaxCount`), sauf coyote time.
→ **Implémenté au J3 :** `Falling → Jumping` est **autorisé** dans `CanEnterState`, sinon un saut en
coyote time laisserait le joueur dans `Falling` avec une vélocité Z positive. Le double saut est bloqué
par **`bJumpConsumed`**, pas par la table.
⁵ = wall jump. `Dashing` sort toujours vers l'état recalculé à partir de `MovementMode` + input, jamais vers `PreviousState` aveuglément.

---

## 2. `BPC_MovementState`

Emplacement : `Content/OVERDRIVE/Player/Components/BPC_MovementState`.

### 2.1 Variables

| Nom | Type | Expo | Category | Rôle |
|---|---|---|---|---|
| `MovementData` | `PDA_MovementData` | Instance Editable | Movement | pointe `DA_Movement_Default` |
| `bDebugEnabled` | Bool | Instance Editable | Debug | active l'overlay §13 |
| `CurrentState` | `E_MovementState` | ReadOnly BP | Movement | **écriture privée** |
| `PreviousState` | `E_MovementState` | ReadOnly BP | Movement | |
| `HorizontalSpeed` | Float (uu/s) | ReadOnly BP | Movement | `VectorLength(Velocity.X, Velocity.Y, 0)` |
| `VerticalSpeed` | Float (uu/s) | ReadOnly BP | Movement | `Velocity.Z` |
| `CurrentSpeedCap` | Float (uu/s) | ReadOnly BP | Movement | cap actif, cf. §2.4 |
| `GraceTimeRemaining` | Float (s) | ReadOnly BP | Movement | tant que > 0, pas de décroissance |
| `LastGainAmount` / `LastGainSource` | Float / Name | ReadOnly BP | Debug | affichage debug |
| `bIsGrounded` | Bool | ReadOnly BP | Movement | cache de `CMC.IsMovingOnGround()` |
| `CachedCMC` | CharacterMovementComponent | — | — | résolu au `BeginPlay` (R6 §4) |
| `CachedMoveInput` | Vector2D | ReadOnly BP | Movement | **poussé** par `BP_PlayerCharacter` (D7), jamais relu depuis Enhanced Input |
| `bSprintHeld` | Bool | ReadOnly BP | Movement | idem, poussé par `SetSprintHeld()` |
| `Tune_*` | Float / Bool | — | Movement\|Cached | cache des valeurs de tuning lues chaque frame (D8) |

Toutes les valeurs de tuning sont lues via `MovementData`, filtrées par `BPC_PlayerStats.GetModified(<Key>)`.
Aucun `Get` de `DA_Movement_Default` en Tick : cacher la struct au `BeginPlay`, re-cacher sur `OnUpgradesApplied`.

> **D7 (J2)** — « `BPC_MovementState` ne connaît pas les inputs » (§1.1) s'applique à **Enhanced Input**,
> pas à la donnée. Le composant n'ouvre aucun `IA_*` : c'est `BP_PlayerCharacter` qui appelle
> `SetMoveInput(Vector2D)` et `SetSprintHeld(bool)` à chaque événement d'input. Le composant reçoit,
> il ne va pas chercher. `CachedMoveInput` existe des deux côtés (le character en a besoin pour la
> direction de dash, §8).

### 2.2 Fonctions publiques

| Signature | Type | Rôle |
|---|---|---|
| `RequestState(NewState) → bool` | fonction | Vérifie §1.3, applique, fire `OnMovementStateChanged`. Retourne false si refusé |
| `CanEnterState(NewState) → bool` | pure | Lit la table §1.3 (implémentée en `Switch on Enum` imbriqué, pas en DataTable) |
| `GetCurrentState() → E_MovementState` | pure | |
| `GetHorizontalSpeed() → Float` | pure | |
| `GetSpeedRatio01() → Float` | pure | `HorizontalSpeed / Speed_HardCap`, clampé 0–1. Sert au **remplissage de `WBP_SpeedMeter`** uniquement. **Ne sert ni au FOV ni à `MPC_Global.PlayerSpeed01`** (cf. `11_ARBITRAGES D9` et §2.5) |
| `AddSpeedGain(Amount, Source)` | fonction | Ajoute `Amount` uu/s dans l'axe horizontal courant, clamp `Speed_HardCap`, reset la grace, fire `OnSpeedGained` |
| `ApplySpeedPenaltyPercent(Percent, Reason)` | fonction | Multiplie la vélocité horizontale par `(1 - Percent)`, arme `SpeedLoss_RecoveryGrace`, fire `OnSpeedPenaltyApplied` (`11_ARBITRAGES D11 / D12`) |
| `SetHorizontalSpeed(NewSpeed)` | fonction | Conserve la direction, écrit `CMC.Velocity`. **Point d'entrée unique** des composants |
| `SetSpeedCapOverride(NewCap, Duration)` | fonction | Cap temporaire (dash, wall ride) ; `Duration = 0` → permanent jusqu'à `ClearSpeedCapOverride()` |
| `SetMoveInput(MoveInput: Vector2D)` | fonction | Appelée par `BP_PlayerCharacter` sur `IA_Move` (Triggered **et** Completed → zéro). Cf. D7 |
| `SetSprintHeld(bHeld: bool)` | fonction | Appelée par `BP_PlayerCharacter` sur `IA_Sprint` Started / Completed. Cf. D7 |
| `ToggleDebug()` | fonction | Bascule `bDebugEnabled` (F1, `IA_DebugToggle`) |
| `StartGrace(Duration)` | fonction | Arme `GraceTimeRemaining = Duration` (typiquement `MomentumDecay_GraceTime`) : suspend la décroissance §2.4-5. Appelée par `BPC_Dash` (§8), `BPC_WallRide` (§9.3) et les pénalités §10.2 |
| `IsGrounded() → bool` | pure | |

### 2.3 Event Dispatchers

`OnMovementStateChanged(OldState, NewState)` · `OnSpeedChanged(NewSpeed, Delta)` · `OnSpeedGained(Amount, Source)` ·
`OnSpeedPenaltyApplied(OldSpeed, NewSpeed, Percent, Reason)` · `OnLanded(ImpactSpeed, bWasHardImpact)` · `OnGraceExpired()`

Le HUD (`WBP_SpeedMeter`) **bind** `OnSpeedChanged`, il ne tick pas (`05_ARCHITECTURE §3`) et se rafraîchit à **20 Hz** (§2.5).

### 2.4 Boucle par frame

Tick **activé et justifié en commentaire dans le BP** (exception explicite à `06_CONVENTIONS §4.6` : le momentum est continu).
`Tick Group = TG_PrePhysics`. Au `BeginPlay`, appeler `AddTickPrerequisiteComponent(CachedCMC)` pour que nos écritures
de `Velocity` arrivent **après** la mise à jour interne du CMC (sinon elles sont écrasées le même frame).

```
TICK(dt)
 1. bIsGrounded = CMC.IsMovingOnGround()
    HorizontalSpeed = Length(Velocity * (1,1,0)) ; VerticalSpeed = Velocity.Z
 2. RESOLVE_STATE : si l'état courant n'est pas piloté par un composant (Sliding/Dashing/WallRiding),
    recalculer Idle/Walking/Sprinting/Jumping/Falling depuis MovementMode + input + HorizontalSpeed.
 3. EffectiveCap = Speed_SprintCap          (07_TUNING §3, modulé par BPC_PlayerStats)
    CurrentSpeedCap = SpeedCapOverride si actif, sinon EffectiveCap
 4. GRACE : si GraceTimeRemaining > 0 → GraceTimeRemaining -= dt ; si passe à 0 → OnGraceExpired
 5. DECAY : si HorizontalSpeed > CurrentSpeedCap ET GraceTimeRemaining <= 0 ET bIsGrounded
              ET CurrentState ∈ {Idle, Walking, Sprinting} :
       NewSpeed = Max(CurrentSpeedCap, HorizontalSpeed - MomentumDecayRate * dt)
       SetHorizontalSpeed(NewSpeed)
    → la décroissance ne s'applique **jamais** en l'air, en slide, en dash ni en wall ride.
 6. AIR_STRAFE : si CMC.MovementMode == Falling ET CurrentState ∉ {Dashing, WallRiding} → §7
 7. HARD_CLAMP : si HorizontalSpeed > Speed_HardCap → SetHorizontalSpeed(Speed_HardCap)
 8. DRIVE_CMC :                                    ← APRÈS toute écriture de Velocity, cf. §7.4
       CMC.MaxWalkSpeed      = Max(CurrentSpeedCap, HorizontalSpeed)   ← anti-freinage, cf. §15
       CMC.MaxAcceleration   = Accel_Ground si au sol, sinon Accel_Air
       CMC.GravityScale      = Gravity, sauf override composant (Dash/WallRide)
       CMC.AirControl        = AirStrafe_AirControl
 9. si |HorizontalSpeed - LastBroadcastSpeed| > 1.0 → OnSpeedChanged
10. si bDebugEnabled → §13
```

> **L'ordre 6–8 est critique** (corrigé au J3). `DriveCMC` placé avant l'air strafe calcule
> `MaxWalkSpeed` sur la vitesse d'avant le gain ; le CMC reclampe dessus à la frame suivante et
> le joueur reste bloqué à `Speed_SprintCap`. Détail et règle générale : **§7.4**.

**Aucune écriture dans `MPC_Global` en Tick** : elle se fait dans le timer 20 Hz de §2.5.

**Momentum** = tout ce qui dépasse `Speed_SprintCap`. Il n'existe pas de variable `Momentum` séparée :
le momentum **est** la vélocité du CMC. Une seule source de vérité, aucune désynchronisation possible.

### 2.5 Timer 20 Hz — effets de vitesse (`11_ARBITRAGES D9`)

Un **timer looping unique à 20 Hz**, démarré au `BeginPlay` de `BPC_MovementState`, est le **seul écrivain**
de `MPC_Global.PlayerSpeed01`. Il alimente aussi le vent (`MS_Wind_Speed`) : une seule cadence, un seul
point de maintenance.

```
EVENT SpeedEffectsTick   (timer looping, 20 Hz)
  PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                         / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )   (07_TUNING §16)
  SetScalarParameterValue(MPC_Global, "PlayerSpeed01", PlayerSpeed01)
  MS_Wind_Speed = PlayerSpeed01                                    // même valeur, même cadence
```

- La normalisation se fait sur `SpeedLines_StartSpeed` / `SpeedLines_FullSpeed`, **jamais** sur `Speed_HardCap` :
  ce scalaire n'existe que pour les **effets de vitesse** (speed lines, aberration chromatique, vignette).
  Normalisé sur le hard cap, les effets seraient invisibles avant 5000 uu/s.
- **`BPC_PlayerStats` n'écrit rien dans `MPC_Global`.**
- **Le FOV n'utilise pas `PlayerSpeed01`** : il lit la vitesse brute via `CF_FOVBySpeed` (`SPEC_CAMERA_JUICE §2`).

---

## 3. Sprint

- **Entrée** : `IA_Sprint` (mode `Sprint_Mode`, 07_TUNING §4) + input avant si `Sprint_RequiresForwardInput` + `bIsGrounded`.
> **`D25` (J4) — on court par défaut, `Shift` fait marcher.** La course est l'essence du jeu, elle ne
> se mérite pas. L'inversion vit dans `BP_PlayerCharacter.SetSprintInput` (`SetSprintHeld(NOT bHeld)`),
> **pas** dans `BPC_MovementState` : la sémantique interne (`bSprintHeld` = « le joueur veut courir »)
> reste juste. `BeginPlay` appelle `SetSprintInput(false)` une fois — sans ça on marcherait jusqu'au
> premier appui sur `Shift`. L'asset porte encore le nom `IA_Sprint` ; renommage en `IA_Walk` à valider.

- **Montée** : `CurrentSpeedCap` interpolé de `Speed_Walk` à `Speed_SprintCap` en `Sprint_TimeToMax` (`FInterp To Constant`).
- **Sortie** : relâche (mode Hold), input arrière, perte du sol (→ `Jumping`/`Falling`, le cap reste), entrée en `Sliding`.
- **Interaction avec le cap** : le sprint **ne peut jamais** dépasser `Speed_SprintCap`. Si `HorizontalSpeed` est déjà
  au-dessus (momentum acquis), le sprint ne freine pas — il maintient simplement `MaxWalkSpeed` (étape 6 §2.4) et
  laisse la décroissance §2.4-5 opérer. Sprint = **plancher confortable**, pas un accélérateur.

---

## 4. Slide — `BPC_Slide`

### 4.1 Séquence d'implémentation

```
[1] IA_Slide pressé (BP_PlayerCharacter) → BPC_Slide.TryStartSlide()
[2] GARDES (toutes doivent passer, sinon crouch simple ou rien) :
      bIsGrounded == true
      HorizontalSpeed >= Slide_MinEntrySpeed            (07_TUNING §5)
      TimeSince(LastSlideEnd) >= Slide_Cooldown
      MovementState.RequestState(Sliding) == true
    → si bIsGrounded == false : ne rien faire, armer SlideBufferTimestamp (cf. §11)
    → si vitesse insuffisante : Crouch() simple, pas de slide, pas de cooldown consommé
[3] RESIZE CAPSULE :
      CachedHalfHeight = Capsule.GetScaledCapsuleHalfHeight()
      SetCapsuleSize(CapsuleRadius, CapsuleHalfHeight_Slide, bUpdateOverlaps=true)   (07_TUNING §2)
      Compenser la caméra : offset -(CapsuleHalfHeight - CapsuleHalfHeight_Slide) interpolé
      sur Slide_CameraDrop, + roulis Slide_CameraTilt
[4] BOOST : MovementState.AddSpeedGain(Slide_EntryBoost, "SlideEntry")
      Direction = vélocité horizontale normalisée (PAS la caméra : on ne tourne pas gratuitement)
[5] FRICTION : CMC.GroundFriction = Slide_Friction ; CMC.BrakingDecelerationWalking = 0
      Courbe de fin : CF_SlideFrictionOverTime (08_DATA_SCHEMAS §5), domaine = T/Slide_MaxDuration
[6] PENTES (évalué chaque frame du slide) :
      Trace descendante depuis le bas de la capsule (longueur = MaxStepHeight)
      SlopeDot = Dot(FloorNormal, VelocityDir)
        SlopeDot > 0.05  (descente) → AddImpulse horizontal = VelocityDir * Slide_SlopeAccelBonus * dt
                                       ET ne PAS décrémenter le timer de durée
        SlopeDot < -0.05 (montée)   → friction ×2, le slide s'éteint naturellement
        sinon (plat)                → rien
[7] TIMER : Slide_MaxDuration. Sur plat/montée uniquement (cf. [6]).
[8] SORTIE — déclencheurs : timer écoulé · relâche de IA_Slide · HorizontalSpeed < Slide_ExitSpeedMin
      · IA_Jump (→ §4.3) · perte du sol
```

### 4.1 ter — **D24 : le slide conserve, il n'accélère pas** (refonte après playtest, J4)

Verdict de Louis sur le premier prototype : *« le slide donne un trop grand boost de vitesse sans
aucun effort, ça devient trop facile et mécaniquement 0 difficulté »*. Le modèle est refondu.

**Principe : sur le plat, le slide ne crée pas de vitesse — il la protège.** C'est une mécanique de
**virage**, la seule qui permette un demi-tour à 180° sans perdre un uu/s. La vitesse ne s'obtient
que par les pentes, proportionnellement à leur inclinaison.

```
SLIDESTEP(dt)                                            ← ordre réel, écritures en dernier
  spd      = |Velocity.XY|
  curYaw   = MakeRotFromX(Velocity.XY).Yaw
  tgtYaw   = MakeRotFromX(Character.GetActorForwardVector()).Yaw       ← [0] VIRAGE
  newYaw   = RInterpToConstant(curYaw, tgtYaw, dt, Slide_TurnRate).Yaw
  turned   = GetForwardVector(newYaw) * spd                            ← norme conservée
  N        = GetFloorNormal()
  newVel   = turned + (N.X, N.Y) * Slide_SlopeAccelBonus * dt          ← [1] pente, VECTORIEL
  rawSpd   = |newVel|
  accelerating = rawSpd > |Velocity.XY| + 0.5
  hold     = accelerating ? Slide_HoldTime : max(0, hold - dt)          ← [2] conservation
  decaying = !accelerating AND hold <= 0
  finalSpd = decaying ? rawSpd - Slide_Friction * rawSpd * dt : rawSpd  ← [3] décroissance
  ─────────────────────────────────────────────────────── écritures :
  Velocity                = Normalize(newVel) * finalSpd  (Z conservé)
  CMC.MaxWalkSpeedCrouched = finalSpd
  SlideTimer, HoldRemaining
  CheckSlideExit()
```

**[0] Le virage angulaire — `D26`.** Compter sur `CMC.MaxAcceleration` pour tourner était une erreur
de conception : à 2500 uu/s, inverser sa course demande **5000 uu/s** de changement de vélocité,
soit **1.25 s** à `Accel_Ground` = 4000 uu/s². Le joueur voyait sa caméra tourner instantanément et
son corps continuer tout droit — *« je glisse sur le sol et n'arrive pas à faire un demi-tour serré »*.

`BPC_Slide` fait donc **pivoter le vecteur vitesse lui-même** vers le yaw du regard, à
`Slide_TurnRate` °/s, **norme strictement conservée**. `bUseControllerRotationYaw = true` sur
`BP_PlayerCharacter`, donc `GetActorForwardVector()` **est** la direction du regard : pas besoin
de passer par le `Controller`. À 720 °/s, un demi-tour prend **0.25 s** — c'est la sensation
d'accroche recherchée.

La rotation est appliquée **avant** l'accélération de pente, ce qui laisse la pente corriger la
trajectoire ensuite : on ne peut pas remonter une pente en la regardant.

**[1] Pourquoi `(N.X, N.Y)` et pas `Dot(N, VelocityDir)`.** Les composantes horizontales de la normale
du sol **pointent déjà vers l'aval** et ont pour norme `sin(θ)`. L'accélération est donc à la fois
bien orientée et correctement mise à l'échelle par l'inclinaison, sans un seul appel trigonométrique.
Surtout : c'est **vectoriel**, donc ça marche **à vitesse nulle** — on se laisse glisser d'une pente
sans presser l'avant, ce que la version scalaire du J4 initial ne permettait pas. En montée, le même
vecteur freine : le cas particulier « friction ×2 » de `§4.1 [6]` disparaît.

**[2] La fenêtre de conservation.** Tant que `Slide_HoldTime` court, la vitesse est **strictement**
conservée. Elle **se réarme intégralement dès que la pente fait ré-accélérer** : enchaîner
plat → descente → plat relance le compteur. `Slide_MaxDuration` ne compte que le temps de
**décroissance**, jamais le temps passé à accélérer.

**[3] Sortie sur vitesse basse** (`Slide_ExitSpeedMin`) : évaluée **uniquement** quand la fenêtre de
conservation est épuisée. Sans ça, un slide démarré à l'arrêt en haut d'une pente s'annulerait
à la première frame.

**Impossible d'accélérer accroupi.** `CMC.MaxWalkSpeedCrouched` est réécrit **chaque frame** à la
vitesse courante du slide — et à **0** quand on est accroupi sans slider,
**sauf si `bForcedSlide`** : sous un plafond bas ce 0 serait un **softlock** (ni se lever, ni bouger),
donc le plancher passe à `Speed_Walk` pour permettre de ramper dehors (**`D27`**). Le CMC prime sur
`MaxWalkSpeed` dès que le personnage est accroupi (`12_PIEGES_OUTILLAGE §6.6`), donc c'est cette clé
qui gouverne. Conséquences voulues :
- l'input **réoriente** la vélocité mais ne peut jamais dépasser sa norme → **virage à vitesse constante** ;
- accroupi à 0 uu/s, pousser l'avant ne fait **rien**.

### `D30` — maintenir la touche **est** l'état slide

Règle unique : **au sol, `IA_Slide` tenu ⇒ `Sliding`.** Il ne doit exister **aucun** instant où le
joueur tient la touche sans être en slide. Toutes les gardes qui pouvaient créer cet écart sont
supprimées — `Slide_MinEntrySpeed`, `Slide_ExitSpeedMin`, `Slide_MaxDuration` et `Slide_Cooldown`
passent **`INACTIVE`** dans `07_TUNING §5`.

```
TryStartSlide()          ← retenté CHAQUE FRAME tant que la touche est tenue
  si pas au sol   : mémorise l'instant (pas de fenêtre à respecter)
  sinon si pas déjà en slide : StartSlide()          ← aucune autre condition

CheckSlideExit()
  relâche de la touche  OU  perte du sol            ← rien d'autre
```

La relance chaque frame rend le système **auto-réparant** et rend le buffer d'atterrissage inutile :
toucher le sol touche tenue déclenche le slide au contact. Elle absorbe aussi le décalage d'une frame
du `piège §6.7` (à l'atterrissage `CurrentState` vaut encore `Falling`, donc `RequestState(Sliding)`
est refusé — la frame suivante il passe).

On peut rester en slide **jusqu'à 0 uu/s** : la vitesse se gère par la décroissance, pas par un seuil
qui éjecte le joueur de l'état.

### `D31` — direction = regard **+** strafe

La cible du virage n'est plus le regard seul :

```
aim = ActorForward * MoveInput.Y + ActorRight * MoveInput.X      ← regard + strafe
      (repli sur ActorForward si l'input est nul)
```

`Q`/`D` infléchissent donc la trajectoire **en plus** de la souris, ce qui donne le contrôle total
demandé au playtest. Le reste du modèle est inchangé : rotation à `Slide_TurnRate`, norme conservée.

`Slide_EntryBoost` est passé à **0** dans `DA_Movement_Default`. La clé et le nœud
`AddSpeedGain` restent en place : c'est un bouton disponible, pas du code mort.

### 4.1 bis — Écarts d'implémentation (J4, 2026-08-19)

`BPC_Slide` est un composant **autonome** : il ne modifie rien dans `BPC_MovementState`.
Il tick **avant** lui grâce à `MovementState.AddTickPrerequisiteComponent(self)` posé dans son
`BeginPlay` (**D22**) — c'est ce qui satisfait la règle §7.4 sans toucher au code validé du J3.

| Point de la spec | Ce qui est implémenté | Décision |
|---|---|---|
| `[3]` resize capsule manuel + offset caméra | **`Character::Crouch()` / `UnCrouch()`** du CMC, avec `CrouchedHalfHeight = CapsuleHalfHeight_Slide` et `MaxWalkSpeedCrouched = Speed_HardCap` posés au `BeginPlay`. Le moteur gère le recentrage au sol ; la caméra descend physiquement avec la capsule, donc `Slide_CameraDrop` n'a pas de code dédié. `Slide_CameraTilt` part au J14 avec le juice | **D21** |
| `[5]` `CMC.GroundFriction = Slide_Friction` | `CMC.GroundFriction = 0` **et** `BrakingDecelerationWalking = 0`. La friction est appliquée **par nous** dans `SlideStep` : `Speed -= Slide_Friction × Speed × dt`. Motif : `DriveCMC` colle `MaxWalkSpeed` à la vitesse courante, donc la friction moteur ne s'applique jamais. `CF_SlideFrictionOverTime` n'existe pas encore | **D18** |
| `[6]` bonus de pente en tout-ou-rien | bonus **mis à l'échelle par `SlopeDot`** : `Speed += Slide_SlopeAccelBonus × SlopeDot × dt`. Sinon 15° et 45° accélèrent pareil. **En descente la friction est suspendue**, sinon elle mange presque tout le bonus | **D19** |
| `[6]` trace de sol | `LineTraceByChannel` (Visibility) vers le bas, longueur **`CapsuleHalfHeight + MaxStepHeight`** (138 uu), normale par défaut `(0,0,1)` si rien n'est touché. **La portée se calibre sur la capsule DEBOUT** : sous le centre d'une capsule sur un plan incliné, le sol est à `(HH − R) + R/cos θ` — 102 uu à 45°, pas 88. Une portée de 94 ratait tout au-delà de 30° (`12_PIEGES §6.8`) | — |
| — | **`CrouchStep`** : accroupi **sans** slider, l'accélération vers l'aval s'applique quand même (décélération sur le plat). On ne peut donc **jamais** rester figé sur une pente. Tant que `IA_Slide` est tenu, `TryStartSlide` est **retenté chaque frame** — le slide est auto-réparant | **`D29`** |
| — | **`IsCeilingBlocked()`** : sphere trace vers le haut (rayon `CapsuleRadius`, distance `CapsuleHalfHeight − CapsuleHalfHeight_Slide`), **seulement si accroupi**. `BP_PlayerCharacter` intercale un `Branch` entre `IA_Jump.Started` et `TryJump` : **pas de saut sous un plafond bas**. Debout la fonction sort immédiatement, le slide-jump §4.3 n'est pas touché | **`D28`** |
| — | **`MaxAcceleration` n'est pas touchée** pendant le slide. Le CMC ne peut pas dépasser `MaxWalkSpeed`, qui est recalculé par `DriveCMC` *après* notre friction : il ne se bat donc pas contre nous, il fournit le pilotage. **Conséquence assumée : le slide est dirigeable à vitesse constante.** Si le playtest juge ça trop libre, brancher `MaxAcceleration` sur une nouvelle clé `Slide_SteerAccel` | **D16** |
| `[8]` sortie « état perdu » | **pas implémentée au J4** : `(not IsMovingOnGround)` couvre le saut, et le dash n'existe pas encore. **À ajouter au J5** avec la comparaison d'état `!= Sliding` |

### 4.2 Le piège du dé-crouch bloqué

`SetCapsuleSize` **ne teste rien** : agrandir la capsule sous un plafond bas la fait pénétrer la géométrie,
puis le CMC la dépénètre violemment (téléport vertical, perte totale de vitesse, parfois chute à travers le sol).

Procédure obligatoire à la sortie de slide :

```
CanUncrouch():
    Start = ActorLocation
    End   = ActorLocation + (0,0, CapsuleHalfHeight - CapsuleHalfHeight_Slide)
    Hit   = CapsuleTraceForObjects(
              Start, End,
              Radius     = CapsuleRadius,
              HalfHeight = CapsuleHalfHeight,
              ObjectTypes = [WorldStatic, WorldDynamic, WallRideSurface],
              IgnoreSelf = true)
    return NOT Hit.bBlockingHit

EndSlide():
    if CanUncrouch():
        SetCapsuleSize(CapsuleRadius, CapsuleHalfHeight)  → état recalculé
    else:
        rester en Sliding, bForcedSlide = true
        friction = Slide_Friction (on continue de glisser sous le plafond)
        retester CanUncrouch() chaque frame
        si HorizontalSpeed atteint 0 sous le plafond → rester crouché, autoriser le déplacement lent
```

Le timer `Slide_MaxDuration` est **suspendu** tant que `bForcedSlide` est vrai : on ne peut pas être puni
d'être coincé sous un plafond.

> **Implémenté autrement (J4, D17).** `UCharacterMovementComponent::UnCrouch()` fait **déjà** ce test
> d'encroachment : si la capsule ne peut pas grandir, il **refuse de se relever** et réessaie à chaque
> frame tant que `bWantsToCrouch` est faux. La procédure ci-dessus était une réimplémentation de ce que
> le moteur fait mieux — et la capsule trace `ForObjects` demandait une liste d'`ObjectTypes` que
> l'outillage ne sait pas remplir.
>
> - `CanUncrouch()` retourne désormais **« la capsule est-elle à hauteur pleine »** (`NOT bIsCrouched`).
> - `bForcedSlide` = `Character.bIsCrouched` juste après un `UnCrouch()`, retesté chaque frame
>   par `UpdateForcedSlide`.
> - **La friction normale est restaurée dès `EndSlide`**, même coincé : sous le plafond on décélère
>   normalement en accroupi (`MaxWalkSpeedCrouched = Speed_HardCap`, donc aucun clamp brutal).
>   Le timer n'a plus besoin d'être suspendu — le slide est déjà terminé.
> - Le piège §12 (« un mesh en `OD_WallRideSurface` n'est plus `WorldStatic` ») **ne s'applique plus
>   au dé-crouch** : le test moteur est un overlap de canaux de collision, pas une trace `ForObjects`.

### 4.3 Slide → Jump

Un `IA_Jump` pendant un slide, ou dans les `Slide_JumpWindow` secondes qui suivent sa fin, **conserve intégralement**
`HorizontalSpeed` (aucun re-clamp par `MaxWalkSpeed`, cf. §15) et applique `Jump_ZVelocity`. C'est le combo central du jeu.
~~Passer par `CanUncrouch()` avant : si bloqué, le saut est refusé et l'input part dans le jump buffer (§5).~~

> **D20 (J4) — le saut pendant un slide n'est jamais refusé.** Un saut avalé sans feedback est pire
> qu'un saut accroupi. Comme on ne redresse pas la capsule au décollage, il n'y a **aucun risque de
> dépénétration** : le personnage saute en capsule basse et se relève à l'atterrissage
> (`UpdateForcedSlide`). `EndSlide` est appelé par `CheckSlideExit` dès que le sol est perdu.

---

## 5. Jump / Coyote time / Jump buffer

```
VARIABLES (BPC_MovementState)
  LastGroundedTime   : Float  ← World Time Seconds, écrit chaque frame où bIsGrounded
  JumpBufferedTime   : Float  ← World Time Seconds au moment d'un IA_Jump non consommé
  bJumpConsumed      : Bool   ← empêche le double saut pendant la coyote window

TryJump()  ← appelé par IA_Jump ET par OnLanded
  if bIsGrounded OR ( (Now - LastGroundedTime) <= Jump_CoyoteTime AND NOT bJumpConsumed ):
        DoJump()
        bJumpConsumed = true
        JumpBufferedTime = -1
  else:
        JumpBufferedTime = Now                     ← buffer armé

DoJump()
  SavedHorizontal = Velocity * (1,1,0) * SpeedRetention_Jump      (07_TUNING §3)
  BunnyHopCheck()                                                  ← §6, AVANT l'impulsion
  Velocity = SavedHorizontal + (0,0, Jump_ZVelocity)               ← Set Velocity, PAS Launch (§15)
  RequestState(Jumping)

OnLanded(Hit)                                                      ← Event Landed du Character
  bJumpConsumed = false
  LandedTime    = Now
  Velocity.XY  *= SpeedRetention_Landing                           (07_TUNING §3)
  if (Now - JumpBufferedTime) <= Jump_BufferTime:
        JumpBufferedTime = -1
        DoJump()                                                   ← saut immédiat, même frame
```

`Jump_MaxCount = 1` (07_TUNING §6) : `CMC.JumpMaxCount = 1`, le double saut est remplacé par le dash.
`CMC.bApplyGravityWhileJumping = true`, `AirControl` = `AirStrafe_AirControl` (§7).

### 5.1 Écarts d'implémentation (J3, 2026-08-19)

| Point | Spec ci-dessus | Implémenté | Pourquoi |
|---|---|---|---|
| `bJumpConsumed = true` / `JumpBufferedTime = -1` | dans `TryJump()` | dans **`DoJump()`** | `DoJump` est aussi appelé depuis `HandleLanded` (saut bufferisé). Placé dans `TryJump`, le saut bufferisé laissait `bJumpConsumed = false` et ouvrait un double saut par coyote time. |
| `OnLanded(Hit)` | événement du Character | fonction **`HandleLanded()`** du composant, relayée par `Event On Landed` de `BP_PlayerCharacter` | le composant ne peut pas recevoir l'événement ; le character se contente de relayer, il ne contient aucune logique (`§1.1`). |
| — | *(rien)* | `HandleLanded` appelle **`StartGrace(MomentumDecay_GraceTime)`** | **D13.** Sans ça, la décroissance §2.4-5 attaque le momentum dès la frame de contact et `SpeedRetention_Landing` ne se voit jamais. Le bunny hop du J7 en dépend. |
| `LastGroundedTime` | « écrit chaque frame où `bIsGrounded` » | fonction **`UpdateJumpTimers()`**, étape 1bis du Tick | isolé pour rester lisible. |
| `JumpBufferedTime` initial | *(non précisé)* | **`-1`** au `BeginPlay` | sinon `Now - 0 < Jump_BufferTime` est vrai pendant les 0,15 premières secondes de jeu et déclenche un saut fantôme au premier contact du sol. |

---

## 6. Bunny hop

Le bunny hop est le mécanisme qui **annule la punition de l'atterrissage** et donne un gain net.

| Élément | Comportement | Clé |
|---|---|---|
| Fenêtre | `Now - LandedTime <= BHop_PerfectWindow` au moment de `DoJump()` | `BHop_PerfectWindow` (§6) |
| Skip de friction | Si `BHop_FrictionSkip` : dès `OnLanded`, `GroundFriction = 0` et `BrakingDecelerationWalking = 0` pendant toute la fenêtre. Restauration à `GroundFriction`/`BrakingDecelerationWalking` (07_TUNING §2) à l'expiration | `BHop_FrictionSkip` |
| Annulation de la perte | Dans la fenêtre, `SpeedRetention_Landing` **n'est pas appliqué** (restaurer la vitesse d'avant-atterrissage mise en cache dans `PreLandSpeed`) | — |
| Gain | `AddSpeedGain(BHop_SpeedGain, "BunnyHop")` | `BHop_SpeedGain` |
| Plafond de chaîne | `ChainGainAccumulated += BHop_SpeedGain`, clampé à `BHop_MaxChainGain`. Au-delà : hop valide (pas de perte) mais gain = 0 | `BHop_MaxChainGain` |
| Reset de chaîne | `ChainGainAccumulated = 0` et `ChainCount = 0` dès qu'un atterrissage n'est **pas** suivi d'un saut dans la fenêtre, ou sur `ApplySpeedPenaltyPercent` | — |

**Feedback attendu** (obligatoire, sinon la mécanique est illisible) : son de hop dont le pitch monte avec `ChainCount`,
flash court sur `WBP_SpeedMeter`, compteur `x N` à l'écran. Un hop raté doit s'entendre différemment d'un hop réussi.

---

## 7. Air strafing — modèle Quake/Source

### 7.1 Modèle mathématique

Le CMC applique déjà un air control classique (`AirControl` = `AirStrafe_AirControl`, 07_TUNING §7) qui gère **la direction**.
Par-dessus, `BPC_MovementState` applique l'accélération vectorielle qui gère **le gain de vitesse** :

```
AIR_ACCELERATE(dt)
  ── entrées ────────────────────────────────────────────────────────────────
  MoveInput   = (IA_Move.X, IA_Move.Y)                      // -1..1, brut
  if Length(MoveInput) < 0.05          : return             // pas d'input → pas de gain
  WishDir     = Normalize( ControlRotationYawOnly.RightVector  * MoveInput.X
                         + ControlRotationYawOnly.ForwardVector * MoveInput.Y )
  WishDir.Z   = 0 ; WishDir = Normalize(WishDir)
  HorizVel    = Velocity * (1,1,0)

  ── garde-fous ─────────────────────────────────────────────────────────────
  if Length(HorizVel) >= AirStrafe_NoGainAboveSpeed : return
  VelDir = Normalize(HorizVel)  (si Length ~ 0 → VelDir = WishDir)
  // Gate : pas de gain si l'input pointe quasiment à l'opposé de la vélocité.
  // Seuil = cos(90° + AirStrafe_GainAngleMax)
  if Dot(WishDir, VelDir) < Cos( DegToRad(90 + AirStrafe_GainAngleMax) ) : return

  ── coeur Quake ────────────────────────────────────────────────────────────
  WishSpeed    = AirStrafe_WishSpeedCap        // 07_TUNING §7
  CurrentSpeed = Dot(HorizVel, WishDir)        // projection scalaire de la vélocité sur l'input
  AddSpeed     = WishSpeed - CurrentSpeed
  if AddSpeed <= 0 : return                    // déjà assez rapide dans cette direction

  AccelSpeed   = AirStrafe_MaxAccel * dt
  AccelSpeed   = Min(AccelSpeed, AddSpeed)                       // clamp #1 (Quake)
  AccelSpeed   = Min(AccelSpeed, AirStrafe_SpeedGainPerSec * dt) // clamp #2 (garde-fou OVERDRIVE)

  NewVel   = HorizVel + WishDir * AccelSpeed
  NewVel   = ClampVectorSize(NewVel, 0, Speed_HardCap)
  Velocity = (NewVel.X, NewVel.Y, Velocity.Z)                    // Z jamais touché
```

**Pourquoi ça marche** : `CurrentSpeed` est la projection, pas la norme. Quand `WishDir` est ~perpendiculaire à la
vélocité (souris qui tourne + strafe latéral maintenu), la projection est proche de 0, donc `AddSpeed ≈ WishSpeed`,
donc on ajoute un vecteur presque orthogonal → la **norme** augmente sans plafonner. C'est exactement ce qui rend
le strafe apprenable : le gain dépend de la coordination souris/clavier, pas du hasard.

`AirStrafe_WishSpeedCap` (`07_TUNING §7`) contrôle la « largeur » de la fenêtre de gain : valeur basse = strafe
exigeant, valeur haute = gain facile. Ne jamais la coder en dur ici — elle se règle dans `07_TUNING` uniquement.

### 7.2 Reproduction en Blueprint (sans C++)

1. `BPC_MovementState` : Tick activé, `AddTickPrerequisiteComponent(CachedCMC)` au `BeginPlay` → notre écriture de
   `Velocity` se produit après le calcul du CMC et survit jusqu'au frame suivant.
2. `MoveInput` est mis en cache par `BP_PlayerCharacter` dans une variable `CachedMoveInput` (écrite par `IA_Move`,
   remise à zéro sur `Completed`). Ne jamais relire l'input depuis le composant.
3. Écriture via **`Set Velocity`** sur le CMC (nœud `Velocity` exposé en BP), jamais `AddImpulse` ni `Launch Character` (§15).
4. `CMC.MaxAcceleration` doit valoir au moins `AirStrafe_MaxAccel` pendant `Falling`, sinon le CMC re-clampe (§15).
5. Ordre dans le Tick : l'air strafe passe **avant** le hard clamp (étape 8 §2.4).
   ⚠️ **Et `DriveCMC` passe APRÈS les deux** — corrigé au J3, cf. §7.4.
6. Vérification : en sandbox, sauter puis maintenir `Q` (strafe gauche, AZERTY — cf. D11) + tourner la souris
   lentement vers la gauche doit faire monter `SPEED` de façon continue. Si la vitesse stagne, le suspect n°1
   est `MaxAcceleration`, le n°2 est l'ordre de Tick.

### 7.3 Écart d'implémentation (J3, 2026-08-19) — **D14**

`WishDir` n'est **pas** reconstruit depuis `ControlRotation` comme en §7.1. Il est lu directement via
**`CMC.GetLastInputVector()`**, aplati en Z puis normalisé.

C'est le vecteur monde que le CMC vient effectivement de consommer ce frame — donc *par construction*
identique à ce que `BP_PlayerCharacter.HandleMoveInput` a poussé via `AddMovementInput`. Reconstruire
`WishDir` à part dupliquerait la convention « `MoveInput.X` = droite, `.Y` = avant » à deux endroits :
la moindre divergence (rebinding, modificateur `SwizzleAxis` dans l'`IMC`, changement de base) donnerait
un gain d'air strafe **désaligné du déplacement réel**, bug quasi impossible à voir autrement qu'à l'aveugle.

Valide parce que `UMovementComponent::ConsumeInputVector()` recopie l'input dans `LastControlInputVector`
avant de le vider, et que `BPC_MovementState` tick **après** le CMC (`AddTickPrerequisiteComponent`).

`Tune_AirStrafeGainAngleCos` = `Cos(90 + AirStrafe_GainAngleMax)` est **précalculé au `BeginPlay`**
(dans `CacheTuning`) : aucune trigonométrie en Tick. Vérifié en PIE : `−0.866` pour `GainAngleMax = 60`.

### 7.4 L'ordre du Tick : `DriveCMC` doit passer **après** l'air strafe (J3)

L'ordre de `§2.4` (…`6. DRIVE_CMC` → `7. AIR_STRAFE` → `8. HARD_CLAMP`) est **faux** et plafonnait
la vitesse à `Speed_SprintCap` en toutes circonstances.

`DriveCMC` écrit `CMC.MaxWalkSpeed = Max(CurrentSpeedCap, HorizontalSpeed)`. Placé **avant** l'air
strafe, il calcule ce plafond à partir de la vitesse *d'avant le gain*. Le CMC, qui tick en premier
à la frame suivante, reclampe alors la vélocité horizontale sur ce plafond périmé
(`CalcVelocity` → `GetClampedToMaxSize2D`) et **efface le gain de la frame précédente**.
Le joueur ne dépasse jamais 1500 uu/s, quel que soit son strafe.

Ordre réel implémenté :

```
… 5. DECAY  →  6. AIR_STRAFE  →  7. HARD_CLAMP  →  8. DRIVE_CMC  →  9. BROADCAST  →  10. DEBUG
```

`ClampToHardCap` recalcule `HorizontalSpeed` depuis la vélocité réelle, donc `DriveCMC` voit toujours
la valeur définitive de la frame. `MaxAcceleration`, `GravityScale` et `AirControl` sont indifférents
à ce déplacement : le CMC les lit à sa propre frame, ils ont de toute façon une frame de retard.

**Règle générale : tout ce qui écrit `CMC.Velocity` doit s'exécuter avant l'écriture de
`MaxWalkSpeed`.** Vaut aussi pour `BPC_Dash` (§8), `BPC_WallRide` (§9) et le bunny hop (§6).

Vérifié en PIE : 2500 uu/s injectés en vol sont intacts à l'atterrissage (`PreLandSpeed = 2500`).

---

## 8. Dash 360° — `BPC_Dash`

```
TryDash()
 [1] GARDES : Charges > 0 ET CurrentState != Dashing ET RequestState(Dashing)
 [2] DIRECTION :
        if Length(CachedMoveInput) >= 0.05 :
             DashDir = Normalize( YawRight * Input.X + YawForward * Input.Y )   // 360° réel
        else :
             DashDir = CameraForwardVector                                       // fallback caméra
        if bIsGrounded AND Dash_ZLockOnGround : DashDir.Z = 0 ; renormaliser
 [3] CONSERVATION : EntrySpeed = Max( HorizontalSpeed * Dash_SpeedRetention, Dash_MinExitSpeed )
        DashSpeed  = Dash_Distance / Dash_Duration
        TargetSpeed = Max(EntrySpeed, DashSpeed)     ← un dash ne ralentit JAMAIS le joueur
 [4] EXÉCUTION : CMC.GravityScale = Dash_GravityScale ; CMC.BrakingDecelerationFalling = 0
        Timeline de longueur Dash_Duration, courbe CF_DashVelocity (08_DATA_SCHEMAS §5)
        chaque frame : Velocity = DashDir * TargetSpeed * CF_DashVelocity(Alpha)
        Z verrouillé à 0 pendant toute la durée si Dash_ZLockOnGround et dash au sol
 [5] FEEDBACK : Dash_FOVKick sur BP_PlayerCameraManager, OnDashPerformed → BPC_StyleMeter
 [6] SORTIE : restaurer GravityScale = Gravity
        HorizontalSpeed = Max(HorizontalSpeed, Dash_MinExitSpeed)
        MovementState.StartGrace(MomentumDecay_GraceTime)
        recalcul d'état depuis MovementMode + input (jamais PreviousState brut)
 [7] CHARGES : consommée à [1]. Recharge : timer Dash_Cooldown par charge, cumulable jusqu'à Dash_MaxCharges
        Upgrade `DashRechargeOnKill` : décrémente le timer, ne donne pas de charge instantanée
```

Toutes les clés : 07_TUNING §8. `Dash_IFrames = 0` → **le dash n'esquive pas**, il repositionne (GDD §13).

| | Ce qui annule le dash | Ce que le dash annule |
|---|---|---|
| | Atterrissage sur un mur bloquant (collision frontale §10) | `Sliding` (sortie propre : dé-crouch via `CanUncrouch()`) |
| | Mort / respawn | La friction de sol en cours |
| | Accroche wall ride réussie pendant le dash | La décroissance de momentum (grace armée à la sortie) |
| | — | L'inertie verticale (`GravityScale = 0` pendant la durée) |

Le dash **ne s'annule pas** sur un dégât reçu, ni sur un input contraire, ni sur un saut : sa durée est atomique.

---

## 9. Wall Ride — `BPC_WallRide`

### 9.1 Détection

```
DetectWall()                       ← Timer looping, actif UNIQUEMENT si CMC.MovementMode == Falling
  Origin = CapsuleWorldLocation
  for Side in [Right, Left]:
      Dir    = ActorRightVector * (Side == Right ? 1 : -1)
      Start  = Origin
      End    = Origin + Dir * (CapsuleRadius + WallRide_DetectDistance)      (07_TUNING §9)
      Hit    = LineTraceForObjects(Start, End, ObjectTypes = [WallRideSurface], IgnoreSelf = true)
      if Hit.bBlockingHit AND IsValidWall(Hit) : return Hit
  return none

IsValidWall(Hit)
  Verticalité : Abs( Dot(Hit.Normal, WorldUp) ) <= Sin( DegToRad(WallRide_MaxWallAngle) )
  Vitesse     : HorizontalSpeed >= WallRide_MinEntrySpeed
  Same-wall   : NOT ( Hit.Component == LastWallComponent
                      AND (Now - LastWallDetachTime) < WallRide_SameWallCooldown )
  Direction   : Dot( Normalize(HorizVel), Hit.Normal ) < 0     // on va vers le mur, pas dos à lui
```

- **Canal** : object type **`WallRideSurface`** exclusivement (07_TUNING §9, 06_CONVENTIONS §7). Traces `ForObjects`,
  jamais `ByChannel` : impossible d'accrocher un ennemi, un prop ou de la géo décorative.
- **Fréquence** : Timer looping à `WallRide_TraceInterval` (`07_TUNING §9`).
  Le timer est **démarré** sur `OnMovementModeChanged → Falling` et **stoppé** sur `Landed`. Aucune trace au sol.
- 2 traces par évaluation maximum. Ne jamais tracer depuis la caméra.

### 9.2 Accroche, maintien, sortie

| Phase | Comportement |
|---|---|
| Accroche | `RequestState(WallRiding)` · `SetMovementMode(MOVE_Flying)` · `GravityScale = WallRide_GravityScale` · `Velocity.Z += WallRide_UpwardBoost` · roulis caméra `WallRide_CameraTilt` vers l'extérieur |
| Maintien (par frame) | `WallDir = Cross(Hit.Normal, WorldUp)` orienté par `Dot(WallDir, HorizVel)` · `Velocity.XY = WallDir * HorizontalSpeed * WallRide_SpeedRetention^dt` · coller au mur : composante de `Velocity` le long de `-Normal` = 0 · re-trace chaque intervalle pour confirmer le mur |
| Sortie — durée | `WallRide_MaxDuration` écoulé → `Falling`, `GravityScale` restauré |
| Sortie — plus de mur | Trace négative 2 évaluations consécutives (anti-flicker sur les joints de modules) → `Falling` |
| Sortie — saut | `IA_Jump` → **Wall Jump** (§9.3) |
| Sortie — input opposé | `Dot(WishDir, Hit.Normal) > 0.7` maintenu ≥ 0.1 s → décrochage volontaire, `Falling`, conserve la vitesse |
| Dans tous les cas | `LastWallComponent = Hit.Component` · `LastWallDetachTime = Now` · `SetMovementMode(MOVE_Falling)` · reset `GravityScale = Gravity` · reset du roulis caméra |

### 9.3 Wall Jump

```
Velocity =  HorizVelPreserved                                  // momentum conservé
         +  Hit.Normal              * WallJump_AwayVelocity
         +  CameraForwardHorizontal * WallJump_ForwardBoost
         +  WorldUp                 * WallJump_ZVelocity
ClampVectorSize2D → Speed_HardCap ; RequestState(Jumping) ; StartGrace(MomentumDecay_GraceTime)
```
Le `WallRide_SameWallCooldown` s'applique aussi après un wall jump : impossible de pomper un mur unique.
Murs opposés → alternance libre (c'est le combo recherché, cf. 07_TUNING §17 distances entre murs).

---

## 10. Perte de vitesse & collisions

### 10.1 Classification d'un impact

Sur `Event Hit` du `CapsuleComponent` (activer *Simulation Generates Hit Events*) :

```
VelDir      = Normalize(Velocity * (1,1,0))
ImpactAngle = RadToDeg( Asin( Clamp( Dot(VelDir, -Hit.ImpactNormal), -1, 1 ) ) )
              // 90° = pleine face   |   0° = rasant (parallèle au mur)
```

| Condition | Effet | Source |
|---|---|---|
| `ImpactAngle > 60` ET `HorizontalSpeed > 2500` | `ApplySpeedPenaltyPercent(0.50, "HardCollision")` + `Shake_HardCollision` + son d'impact | 07_TUNING §10 / §16 |
| `ImpactAngle > 60` ET vitesse ≤ seuil | Aucune pénalité (le CMC arrête naturellement) | 07_TUNING §10 |
| `ImpactAngle < 30` | **0 %**. On glisse le long : `Velocity = Velocity - Normal * Dot(Velocity, Normal)`, renormalisé à la vitesse d'avant impact | 07_TUNING §10 |
| `30 <= ImpactAngle <= 60` | `ApplySpeedPenaltyPercent(SpeedLoss_Collision_MidAngle, "MidAngleCollision")` — transition continue entre 0 % et 50 % | 07_TUNING §10 |
| Projectile / melee ennemi encaissé | `ApplySpeedPenaltyPercent` avec `S_DamageInfo.SpeedPenaltyPercent` (08_DATA_SCHEMAS §2) | 07_TUNING §10 / §13 |

### 10.2 Grace de récupération

Toute pénalité arme `GraceTimeRemaining = SpeedLoss_RecoveryGrace` (07_TUNING §10). Pendant cette fenêtre :
la décroissance de momentum est suspendue, le joueur peut reconstruire (slide-jump, dash) sans être doublement puni.
Une pénalité **reset la chaîne de bunny hop** et **reset le `BPC_StyleMeter`** via `E_StyleEvent.TookDamage`.
Anti-spam : deux `Event Hit` sur le même composant à moins de 0.2 s → une seule pénalité (mise en cache de `LastHitComponent`).

---

## 11. Interactions entre mécaniques

| Situation | Résolution |
|---|---|
| **Dash pendant Slide** | Dash accepté. Fin de slide propre (`CanUncrouch()` ; si bloqué, la capsule reste basse et le dash s'exécute quand même). Direction = input, pas la direction de slide. |
| **Slide pendant Dash** | Refusé (`Dashing → Sliding` interdit, §1.3). L'input est bufferisé : si `IA_Slide` est encore maintenu à la fin du dash et que les gardes §4.1 passent, le slide démarre. |
| **Slide en l'air** | Aucun slide. `SlideBufferTimestamp = Now`. À l'atterrissage, si `Now - SlideBufferTimestamp <= Jump_BufferTime` et gardes OK → slide immédiat. C'est le « slide d'atterrissage », central pour le flow. |
| **Dash pendant Wall Ride** | Dash accepté, décroche le mur, arme `WallRide_SameWallCooldown`. Direction 360° normale. |
| **Wall Ride pendant Dash** | Refusé pendant `Dash_Duration` (la détection est stoppée). La détection reprend à la sortie ; un mur adjacent s'accroche donc au frame suivant. |
| **Jump pendant Slide** | Autorisé → §4.3, conserve tout le momentum. |
| **Jump pendant Wall Ride** | = Wall Jump, §9.3. Jamais un saut normal. |
| **Jump pendant Dash** | Refusé pendant la durée. Bufferisé via `JumpBufferedTime`, consommé à la sortie si dans `Jump_BufferTime`. |
| **Dash pendant Jump/Falling** | Accepté. `Dash_ZLockOnGround` ne s'applique pas → dash 3D possible vers le haut/bas. |
| **Sprint pendant Slide** | Ignoré. Le sprint reprend automatiquement à la sortie si `IA_Sprint` est maintenu. |
| **Wall Ride pendant Slide** | Impossible : le slide est un état sol, la détection murale ne tourne qu'en `Falling`. |
| **Bunny hop après Slide** | Oui : sortie de slide → saut dans `Slide_JumpWindow` → atterrissage → hop dans `BHop_PerfectWindow`. La chaîne cumule les deux gains, clampés par `BHop_MaxChainGain` puis `Speed_HardCap`. |
| **Air strafe pendant Dash** | Désactivé (`CurrentState == Dashing` exclu à l'étape 7 §2.4). Le dash est une trajectoire, pas une suggestion. |
| **Air strafe pendant Wall Ride** | Désactivé. Le wall ride pilote la vélocité intégralement. |
| **Dégât pendant Dash** | Le dash termine sa course. La pénalité de vitesse s'applique à la sortie, sur la vitesse post-dash. |
| **Dégât pendant Wall Ride** | Décrochage immédiat → `Falling` + pénalité. Feedback fort obligatoire (shake + son). |
| **Collision frontale pendant Slide** | Pénalité §10 normale + fin de slide forcée (si `CanUncrouch()` échoue, `bForcedSlide`). |
| **Collision frontale pendant Dash** | Le dash est interrompu (seul cas d'annulation). Pénalité §10 appliquée. |
| **Dash au sol vers le haut** | Impossible si `Dash_ZLockOnGround` : `DashDir.Z` forcé à 0. Sauter d'abord. |
| **2 dashs consécutifs** | Uniquement si `Dash_MaxCharges >= 2` (upgrade). Sinon refusé, aucun feedback trompeur : son « no charge » distinct. |

---

## 12. Setup de collision (Project Settings → Collision)

### Object Channels à créer
| Nom | Default Response |
|---|---|
| `WallRideSurface` | Block |

### Trace Channels à créer
| Nom | Default Response |
|---|---|
| `Weapon` | Block |

`ECC_GameTraceChannel1` = `Projectile`, déjà présent (template) → conservé (06_CONVENTIONS §7).

### Presets

| Preset | Object Type | WorldStatic | WorldDynamic | Pawn | PhysicsBody | WallRideSurface | Visibility | Camera | Projectile | Weapon |
|---|---|---|---|---|---|---|---|---|---|---|
| `OD_Player` | Pawn | Block | Block | Block | Block | Block | Block | Ignore | Block | Ignore |
| `OD_Enemy` | Pawn | Block | Block | Block | Block | Block | Block | Ignore | Block | Block |
| `OD_EnemyProjectile` | WorldDynamic | Block | Ignore | Block | Ignore | Block | Ignore | Ignore | Ignore | Ignore |
| `OD_WallRideSurface` | **WallRideSurface** | Block | Block | Block | Block | Block | Block | Block | Block | Block |
| `OD_LevelGeo` | WorldStatic | Block | Block | Block | Block | Block | Block | Block | Block | Block |

### Réglages CMC obligatoires pour le slide (J4)

Trois défauts d'UE hostiles à un jeu de vitesse, tous côté « crouch », tous silencieux :

| Propriété | Défaut UE | Valeur OVERDRIVE | Sans ça |
|---|---|---|---|
| `NavAgentProps.bCanCrouch` | `false` | **`true`** | `Crouch()` ne fait **rien**, sans warning (`12_PIEGES §6.5`) |
| `MaxWalkSpeedCrouched` | `300` | **piloté par `BPC_Slide`** | un slide à 1900 uu/s est écrasé à 300 (`§6.6`) |
| `bCanWalkOffLedgesWhenCrouching` | `false` | **`true`** | **mur invisible** au bord de chaque plateforme en slide (`§6.10`) |

À revérifier en bloc dès qu'une nouvelle mécanique accroupie apparaît.

**Piège** : un mesh en `OD_WallRideSurface` **n'est plus** de type `WorldStatic`. Toute trace `ForObjects` qui n'inclut
que `WorldStatic` cessera de le voir (notamment `CanUncrouch()` §4.2 et les traces de sol) → inclure systématiquement
`WallRideSurface` dans les listes d'object types de la navigation et des traces de dé-crouch.

---

## 13. Debug

### 13.1 Overlay (activé par `bDebugEnabled`, dessiné par `BPC_MovementState`)

```
STATE      : Sprinting   (prev: Walking)
SPEED      : 2840 uu/s   (HUD 284)   |   VZ: -120
CAP        : 1500        DECAY: ON   GRACE: 0.00 s
LAST GAIN  : +400  "SlideEntry"  (0.42 s ago)
BHOP       : chain 3     accum +360 / 1500
DASH       : 0/1 charges  cd 0.91 s
SLIDE      : t 0.00 / 1.20   cd 0.13 s   forced: no
WALLRIDE   : t --- / 2.00   samewall cd 0.00 s   last: SM_Module_Wall_800_12
JUMP       : coyote 0.00   buffer ---   consumed: yes
CMC        : MaxWalkSpeed 2840  MaxAccel 4000  GravityScale 2.4  Mode Walking
```

Dessins 3D : les 2 traces de wall ride (vert = valide, rouge = rejeté + raison), la capsule de `CanUncrouch()`,
le vecteur `WishDir` (bleu) et le vecteur `Velocity` (jaune), le point d'impact + `ImpactAngle` du dernier `Event Hit`.
Toggle : **`IA_DebugToggle` sur `F3`** (`11_ARBITRAGES D15`, `09_INPUT` — `F1` est le raccourci Wireframe
du viewport éditeur, cf. journal J2 D12), uniquement en build Development.

**État réel au J3** — 6 lignes, clés `OD_0_State` → `OD_5_CMC` :

```
STATE   Sprinting   prev Walking
SPEED   2840 uu/s   HUD 284      VZ -120
CAP     1500        GRACE 0.00   GROUND true
GAIN    +400  src SlideEntry  il y a 0.42
JUMP    coyote 0.08   buffer -1.00   consumed true   airgain 4.20
CMC     MaxWalkSpeed 2840   MaxAccel 2500   GravityScale 2.4
```

`buffer -1.00` = aucun saut bufferisé (sentinelle, cf. §5.1). `airgain` = `AccelSpeed` du dernier
frame d'air strafe, en uu/s : **c'est le chiffre à regarder pour juger `AirStrafe_WishSpeedCap`.**
Les lignes `BHOP` / `DASH` / `WALLRIDE` arrivent avec leurs composants (J5–J7).

**Ligne `SLIDE` ajoutée au J4**, clé `OD_6_Slide`, **dessinée par `BPC_Slide` lui-même**
(il lit `MovementState.bDebugEnabled`, donc `F3` pilote les deux — aucune modification de
`DrawDebugOverlay`) :

```
SLIDE   t 0.42 / 1.20   sliding true   forced false   slope 0.50   entry 1500.00
```

`slope` = `Dot(FloorNormal, DirectionHorizontale)` : **> 0 en descente** (0.26 / 0.50 / 0.71 à
15° / 30° / 45°), < 0 en montée, ≈ 0 sur le plat. `forced` = capsule coincée sous un plafond.
`entry` = `HorizontalSpeed` au moment de l'entrée en slide.

### 13.2 `L_Sandbox_Movement` (`Content/OVERDRIVE/Levels/Sandbox/`)

Grille 100 uu (06_CONVENTIONS §6). Chaque zone testable **isolément**, séparée et étiquetée par un `TextRender`.

| Zone | Construction | Ce qu'elle teste | État |
|---|---|---|---|
| A — Ligne droite | Couloir plat 8000 uu, largeur 800 uu, marques au sol tous les 1000 uu | Sprint cap, décroissance, lecture de vitesse | le sol plat de 20000 uu suffit pour l'instant |
| B — Tunnel bas | Tunnel de 20000 uu de long, hauteur intérieure **inférieure à `CapsuleHalfHeight × 2`** et supérieure à `CapsuleHalfHeight_Slide × 2` | Slide sous obstacle + **dé-crouch bloqué** (§4.2) | ✅ **construit au J3** |
| C — Rampes | Rampes descendantes 15° / 30° / 45° et montantes idem, longueur 1600 uu | `Slide_SlopeAccelBonus`, extinction en montée | ✅ **construit au J3** |

#### Zones B et C telles que construites (2026-08-19)

Toute la géométrie est en `/Engine/BasicShapes/Cube` — **volontairement pas en `LevelPrototyping`**,
qui est promis à la suppression (décision D1). Rangée dans l'outliner sous `Sandbox/B_TunnelBas`
et `Sandbox/C_Rampes`, étiquetée par des `TextRender`.

**Zone B — tunnel bas**, à `Y = −3000`, de `X = 1000` à `X = 5000` :

| Mesure | Valeur | Contrainte |
|---|---|---|
| Hauteur intérieure | **130 uu** | `> 88` (`CapsuleHalfHeight_Slide × 2`) et `< 176` (`CapsuleHalfHeight × 2`) ✅ |
| Longueur | **4000 uu** | doit dépasser la distance d'un slide (~2400 uu à `Slide_MaxDuration = 1.2 s`) pour que le dé-crouch bloqué se produise |
| Largeur intérieure | 1000 uu | — |

> **Divergence assumée** : la spec dit 20000 uu. À cette longueur le tunnel demanderait 13 s de
> traversée accroupie et deviendrait inutilisable. 4000 uu suffisent à garantir qu'un seul slide ne
> le franchit pas — c'est la seule propriété dont dépend le test. Vérifié par trace physique :
> plafond à 130.0 uu sur les 5 points de contrôle.

**Zone C — rampes**, longueur de pente 1600 uu, largeur 800 uu, départ `X = 1500` :

| Angle | Y | Hauteur atteinte | Emprise au sol | Plateau (face sup.) |
|---|---|---|---|---|
| 15° | 2000 | 414 uu | 1546 uu | 438.3 uu |
| 30° | 3200 | 800 uu | 1386 uu | 821.7 uu |
| 45° | 4400 | 1131 uu | 1131 uu | 1149.0 uu |

Chaque rampe monte vers un plateau de 1200 × 800 uu : on la monte en sprint, on fait demi-tour, on
la redescend en slide. Ça teste `Slide_SlopeAccelBonus` **et** l'extinction en montée avec la même
géométrie. Le raccord rampe/plateau est calé sur la **face supérieure** de la rampe, pas sur son axe
— sinon une lèvre de ~24 uu accrocherait le slide. La marche à l'entrée de chaque rampe fait 18–24 uu,
sous `MaxStepHeight` (50).

45° reste franchissable : `WalkableFloorAngle = 50°`.

Zones restantes à construire (D–K) : au fur et à mesure des mécaniques (J5 dash, J6 wall ride).
| D — Escaliers | Marches de 25 / 50 / 75 uu | `MaxStepHeight`, accrochage d'arête (§15) |
| E — Couloir wall ride | 2 murs `OD_WallRideSurface` parallèles, écartements 600 / 1000 / 1400 uu (07_TUNING §17), hauteur 800 uu | Alternance de wall rides, `SameWallCooldown` |
| F — Mur unique | 1 mur `OD_WallRideSurface` de 1600 uu, sol supprimé sur 400 uu devant | Wall ride long, durée max, wall jump |
| G — Gouffres | Gaps de 600 / 900 / 1200 uu | Dash de franchissement, coyote time (bord marqué) |
| H — Plafond bas + saut | Plateforme à 300 uu avec plafond bas au-dessus | Jump buffer, dé-crouch bloqué en l'air |
| I — Piliers | 4 piliers 200×200 au milieu du couloir A | Collision frontale (>60°) |
| J — Murs biseautés | Murs à 15° et 25° par rapport à l'axe du couloir | Collision rasante (<30°), glissement |
| K — Circuit combo | Boucle fermée : rampe → slide → gap → wall ride → wall jump → atterrissage → hop | Enchaînement complet, mesure de vitesse de pointe |

Un `BP_SpeedGate` (Dev/Debug, jetable) placé en A et K : `Print` de la vitesse au passage.

---

## 14. Checklist de validation manuelle (Louis)

**Sprint**
- [ ] Sprint seul se stabilise exactement à `Speed_SprintCap`, jamais au-dessus
- [ ] Relâcher tout input au-dessus du cap : la vitesse redescend après `MomentumDecay_GraceTime`, pas avant
- [ ] La montée en vitesse ne donne pas l'impression d'être « collant »

**Slide**
- [ ] Le slide est refusé sous `Slide_MinEntrySpeed` (crouch simple, sans frustration)
- [ ] Le boost d'entrée se **sent** : gain net perceptible sans regarder le HUD
- [ ] En descente, le slide accélère ; en montée, il meurt tout seul
- [ ] Sous le tunnel bas (zone B) : impossible de se relever, aucun téléport, aucune perte brutale de vitesse
- [ ] Sortie de slide sous plafond puis sortie du tunnel : la capsule se relève sans à-coup
- [ ] Slide → Jump conserve la vitesse (comparer le HUD avant/après : écart ≤ 1 %)

**Jump / Coyote / Buffer**
- [ ] Sauter en quittant un bord (zone G) : le saut part, ça ne « mange » pas l'input
- [ ] Appuyer sur saut juste avant de toucher le sol : le saut part à l'atterrissage
- [ ] Aucun double saut possible

**Bunny hop**
- [ ] Enchaîner 5 hops : la vitesse monte visiblement puis se stabilise à `BHop_MaxChainGain`
- [ ] Un hop raté est audible et se sent (perte via `SpeedRetention_Landing`)
- [ ] La chaîne se reset après un atterrissage sans saut

**Air strafe**
- [ ] Sauter + strafe gauche + rotation souris gauche continue = la vitesse monte
- [ ] Le même geste dans le mauvais sens ne donne rien (pas d'exploit accidentel)
- [ ] Ça s'apprend en < 5 min mais reste dur à maîtriser

**Dash**
- [ ] Le dash part dans la direction du stick/clavier, pas de la caméra, quand il y a un input
- [ ] Sans input, il part droit devant la caméra
- [ ] Le dash ne ralentit jamais : vitesse de sortie ≥ vitesse d'entrée
- [ ] Au sol, le dash est parfaitement horizontal
- [ ] Le son « pas de charge » est distinct et immédiat

**Wall Ride**
- [ ] Accroche uniquement sur les murs `OD_WallRideSurface`, jamais sur les autres
- [ ] Accroche impossible sous `WallRide_MinEntrySpeed`
- [ ] L'alternance sur 2 murs opposés (zone E) est fluide et fait envie
- [ ] Impossible de pomper indéfiniment un seul mur
- [ ] Le tilt caméra aide à lire l'accroche sans donner la nausée

**Collisions**
- [ ] Percuter un pilier de face à haute vitesse fait mal (perte visible + shake) mais ne tue pas
- [ ] Frôler un mur biseauté (zone J) ne coûte rien, on glisse
- [ ] Après un gros hit, on peut immédiatement relancer sans être doublement puni

**Global**
- [ ] Le circuit K peut s'enchaîner sans jamais retomber sous `Speed_SprintCap`
- [ ] 5 minutes en sandbox donnent envie de continuer — **si non, arrêter et retuner avant d'ajouter quoi que ce soit**

---

## 15. Pièges connus UE5

| Piège | Symptôme | Correctif |
|---|---|---|
| `MaxWalkSpeed` re-clampe le momentum | La vitesse retombe instantanément à 1500 dès qu'on touche le sol | `MaxWalkSpeed = Max(CurrentSpeedCap, HorizontalSpeed)` **chaque frame** (§2.4 étape 6) |
| `MaxAcceleration` clampe tout | L'air strafe ne donne rien, le dash paraît mou | Monter `MaxAcceleration` à `Accel_Air` en `Falling`. Ne jamais laisser la valeur par défaut (2048) |
| `AirControl` par défaut | Contrôle aérien pâteux ou au contraire trop fort | Régler explicitement sur `AirStrafe_AirControl`. Si le strafe Quake fait tout le travail, descendre `AirControl` vers 0 |
| `Launch Character` vs `Set Velocity` | `Launch Character` avec `bXYOverride = false` **additionne**, avec `true` **écrase** → gains incohérents | Utiliser **`Set Velocity`** partout dans ce système. `Launch Character` réservé au knockback subi |
| Perte de vitesse à l'atterrissage | On perd 30–50 % en touchant le sol | `bMaintainHorizontalGroundVelocity = true`, `BrakingDecelerationWalking` bas (07_TUNING §2), et `SpeedRetention_Landing` appliqué **explicitement** dans `OnLanded`, jamais laissé au CMC |
| Friction de sol invisible | Le bunny hop ne rend rien | `bUseSeparateBrakingFriction` + `GroundFriction = 0` pendant `BHop_PerfectWindow` (§6) |
| Capsule qui accroche les arêtes | Blocage net sur un joint de modules à haute vitesse | `MaxStepHeight` généreux (07_TUNING §2), `bUseFlatBaseForFloorChecks = true`, éviter les meshes concaves, `Perch Radius Threshold` > 0 |
| `SetCapsuleSize` sous un plafond | Téléport vertical, chute à travers le sol | `CanUncrouch()` obligatoire (§4.2). Ne jamais agrandir la capsule sans trace |
| CMC écrase notre `Velocity` | Le code marche « une frame sur deux » | `AddTickPrerequisiteComponent(CachedCMC)` au `BeginPlay` du composant (§7.2) |
| `MOVE_Flying` non réinitialisé | Le joueur reste en apesanteur après un wall ride | Restaurer `SetMovementMode(MOVE_Falling)` + `GravityScale` sur **toutes** les sorties, y compris mort et respawn |
| `GravityScale` empilé | Dash pendant wall ride → gravité à 0 définitive | Un seul propriétaire : `BPC_MovementState` réécrit `GravityScale` chaque frame (§2.4 étape 6) ; les composants demandent un override, ils n'écrivent pas |
| Tick order des composants | Le debug affiche des valeurs d'un frame de retard | Tout lire au même endroit (`BPC_MovementState`), les autres composants consomment via `Get` |
| Vitesse > CCD | Traversée de mur au-dessus de ~5000 uu/s | `Speed_HardCap` respecté + `bUseCCD = true` sur la capsule joueur |
| `Event Hit` non émis | Les collisions frontales ne sont jamais détectées | `Simulation Generates Hit Events = true` sur la capsule + `bNotifyRigidBodyCollision` |
| Enhanced Input relu en Tick | Input fantôme après un pause/menu | `CachedMoveInput` remis à zéro sur `Completed`/`Canceled` **et** sur changement d'`IMC_` |

---

## 16. Divergences arbitrées

`AirStrafe_WishSpeedCap` (§7), `WallRide_TraceInterval` (§9) et `SpeedLoss_Collision_MidAngle` (§10)
**existent dans `07_TUNING`** — aucune clé de ce document n'est orpheline.
Toutes les décisions qui touchent ce système sont consignées dans **`Docs/11_ARBITRAGES.md`**
(D9 `PlayerSpeed01`, D11/D12 pénalité de vitesse, D15 toggle debug, D16 restart).
