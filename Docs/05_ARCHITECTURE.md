# 05 — ARCHITECTURE BLUEPRINT

> Qui possède quoi, qui parle à qui. Aucun système ne s'ajoute hors de ce plan sans validation.

---

## 1. Principe directeur

**Le `BP_PlayerCharacter` n'est pas un god-object.** Il orchestre des composants.
Chaque composant est autonome, testable seul, et communique par **Event Dispatchers**.

```
BP_PlayerCharacter  (orchestrateur)
   ├── CharacterMovementComponent   (moteur, réglé — pas remplacé)
   ├── BPC_MovementState            ← état + vitesse + momentum
   ├── BPC_Slide
   ├── BPC_Dash
   ├── BPC_WallRide
   ├── BPC_Health
   ├── BPC_PlayerStats              ← lit les upgrades, applique les modificateurs
   ├── BPC_StyleMeter               ← alimente le score en direct
   ├── BP_LaserWeapon    (child actor)
   └── BPC_Melee
```

**Décision** : on **garde** le `CharacterMovementComponent` d'Unreal et on le pilote
(`MaxWalkSpeed`, `GravityScale`, `Velocity`, `AddImpulse`, `SetMovementMode`) plutôt que
d'écrire un movement custom from scratch. Raison : 4 semaines, solo, Blueprint only.
Le wall ride et le dash utilisent `MOVE_Flying` / `MOVE_Falling` + override de `Velocity`.

---

## 2. Arbre complet

### `Content/OVERDRIVE/Core/`
| Asset | Rôle |
|---|---|
| `GI_Overdrive` (GameInstance) | **Persiste sur toute la run** : upgrades actifs, niveau courant, score cumulé, seed |
| `GM_Overdrive` (GameMode) | Règles du niveau, spawn du joueur, transitions d'état |
| `GS_Overdrive` (GameState) | État partagé du niveau : timer, kills, ennemis restants, phase |
| `PC_Overdrive` (PlayerController) | Input mapping, gestion du HUD, pause, restart |
| `PS_Overdrive` (PlayerState) | Score courant, style, stats de run |
| `BPC_HitStop` (sur `PC_Overdrive`) | **Propriétaire unique du time dilation** (cf. `11_ARBITRAGES D6`). `RequestHitStop(RealDuration: float, Dilation: float, Priority: int)` → `bool bAccepted`. Priorités : `Headshot = 10` · `WallSlam = 20` · `Boss phase = 30`. Durée en temps réel, refusé si < `HitStop_MinInterval`. Audio et UI exclus du ralenti |
| `BPI_Damageable` | 4 fonctions — **signature définitive** (cf. `11_ARBITRAGES D10`) :<br>`ApplyDamage(DamageInfo: S_DamageInfo)` → `(bKilled: bool, DamageApplied: float)`<br>`ApplyKnockback(Impulse: Vector, Instigator: Actor)`<br>`IsAlive()` → `bool`<br>`GetHealthRatio()` → `float` *(pure)* |
| `BPI_ScoreEvent` | `NotifyScoreEvent(EventType, Payload)` |
| `BPI_Interactable` | Coffres, checkpoints, triggers de fin de niveau |
| `BPFL_Overdrive` | Fonctions pures : conversions de vitesse, calcul de rank, formatage du temps |

**`ApplyKnockback` est appelée *après* `ApplyDamage`, par l'appelant, jamais depuis `ApplyDamage`** :
le knockback doit s'appliquer même si la cible est morte, et l'appelant seul sait s'il veut projeter.
`BPFL_Overdrive` ne porte **aucun** hit-stop (une Function Library ne peut pas porter d'état) — c'est `BPC_HitStop`.

### `Content/OVERDRIVE/Player/`
| Asset | Rôle |
|---|---|
| `BP_PlayerCharacter` | Pawn. Possède les composants, expose l'API mouvement |
| `BP_PlayerCameraManager` | FOV dynamique, tilt, shakes |
| `BPC_MovementState` | **Cœur du système.** Machine à états + vitesse interne + momentum + décroissance |
| `BPC_Slide` | Entrée/sortie de slide, resize capsule, friction, boost |
| `BPC_Dash` | Charges, cooldown, direction 360°, conservation de vitesse |
| `BPC_WallRide` | Détection murs, accroche, wall jump, cooldown same-wall |
| `BPC_Health` | PV, dégâts, mort, i-frames. **Partagé avec les ennemis.** |
| `BPC_PlayerStats` | Applique les upgrades sur toutes les valeurs de tuning |
| `BPC_StyleMeter` | Multiplicateur de style, gains, décroissance |
| `ABP_PlayerArms` | Animation bras FP + arme |
| `BP_DeathCam` | Caméra temporaire de mort. Prend le view target pendant le fade, rendue au pawn au respawn |

#### `E_MovementState` (machine à états de `BPC_MovementState`)
```
Idle → Walking → Sprinting → Sliding
                     ↓            ↓
                  Jumping ← ← ← ← ┘
                     ↓
                  Falling ⇄ WallRiding
                     ↓
                  Dashing  (état transitoire, sortie vers l'état précédent)
```
Un seul état actif à la fois. `Dashing` peut être entré depuis n'importe quel état sauf lui-même.

### `Content/OVERDRIVE/Weapons/`
| Asset | Rôle |
|---|---|
| `BP_LaserWeapon` | Child Actor du joueur. Trace, dégâts, VFX, muzzle |
| `BPC_Heat` | Jauge de chaleur, overheat, refroidissement. **Attaché à l'arme, pas au joueur.** |
| `BPC_Melee` | Sphere trace, dégâts, knockback, détection wall slam |

### `Content/OVERDRIVE/Enemies/`
| Asset | Rôle |
|---|---|
| `BP_EnemyBase` | Parent de tous les ennemis. Implémente `BPI_Damageable`. Lit un `DA_EnemyData` |
| `BP_Enemy_Grunt` / `_Shooter` / `_Tank` | Enfants. **Ne redéfinissent que le comportement, pas les stats** |
| `BP_AIController_Enemy` | Contrôleur commun. Perception + StateTree |
| `ST_Enemy_Shooter` / `ST_Enemy_Tank` | StateTree, **uniquement pour ces 2 archétypes** (plugin `GameplayStateTree` déjà actif) |
| `ABP_Enemy` | Animation Blueprint commun aux 3 archétypes (`BS_Enemy_Locomotion` + états d'attaque/mort) |
| `BPC_KnockbackReceiver` | Reçoit l'impulsion melee, détecte l'impact mural, applique `WallSlam_Damage` |
| `BP_EnemyProjectile` | Projectile du Shooter |
| `BP_EnemyActivationVolume` | Volume placé dans le level. Active / désactive les ennemis d'une section (cf. `EnemyScan_Rate`, `DeactivateBehindDistance`) |

**Décision IA** : **StateTree**, pas Behavior Tree. Aucun `BT_` / `BB_` n'existe dans le projet.
Le **Grunt n'a pas de StateTree** : son comportement (idle → chase → windup → charge) tient dans une
**machine à états dans son propre Blueprint** — moins de 4 états, ne pas sur-outiller.
Seuls **Shooter** et **Tank** ont un `ST_Enemy_*`.

### `Content/OVERDRIVE/Bosses/`
| Asset | Rôle |
|---|---|
| `BP_BossBase` | Hérite de `BP_EnemyBase`. Ajoute : phases, barre de vie UI, events d'arène |
| `BP_Boss_01` / `BP_Boss_02` | 2 phases max chacun (GDD §31) |
| `BP_BossArenaElement` | Élément d'arène piloté par les phases : portes, plateformes, zones de sol brûlant (`ArenaBoundsTag`) |

### `Content/OVERDRIVE/Systems/`
| Asset | Rôle |
|---|---|
| `BP_LevelManager` | **1 par niveau, placé dans le level.** Start/end triggers, checkpoints, spawn des ennemis, `DA_LevelData` |
| `BP_RunManager` | Vit dans `GI_Overdrive`. Enchaînement des niveaux, upgrades actifs, run en cours |
| `BPC_ScoreManager` | Sur le `GS_`. Agrège kills/temps/vitesse/style → score → rank |
| `BP_LootChest` | Actor de fin de niveau. Tire dans la `DT_LootTable_<Rank>` |
| `BPC_UpgradeManager` | Sur le `GI_`. Stocke et applique les upgrades actifs |
| `BP_Checkpoint` | Trigger. Sauvegarde position + état de run |
| `BP_LevelEndTrigger` | Fin de niveau |
| `BP_SpeedGate` | Porte / booster de couloir de vitesse. Ne s'ouvre qu'au-dessus d'un seuil de vitesse, sinon bloque |
| `BP_LightingRig` | **1 par niveau.** Lit un `PDA_WorldData` et pousse l'ambiance dans `MPC_Global` (`SunDirection`, `SunColor`, `AmbientColor`, `FogColor`, `WorldTint`). Aucune lumière dynamique (rendu Unlit) |

### `Content/OVERDRIVE/UI/`
| Asset | Rôle |
|---|---|
| `WBP_HUD` | Conteneur. Crosshair, HP, Heat, Dash, Speed, Style, Timer |
| `WBP_HeatBar` / `WBP_SpeedMeter` / `WBP_StyleMeter` / `WBP_DashCharges` | Sous-widgets |
| `WBP_Results` | Écran de fin de niveau + comparaison S-Rank |
| `WBP_LootChest` | Ouverture de coffre + choix d'upgrade |
| `WBP_MainMenu` / `WBP_Settings` / `WBP_Pause` | Menus |
| `WBP_RunFailed` | Écran de fin de run ratée : niveau atteint, score total, upgrades collectés |
| `WBP_LivesCounter` | Vies restantes au HUD (`11_ARBITRAGES D31`) |
| `WBP_BossHealthBar` | |

---

## 3. Flux de communication

### Règle : **on ne cast pas vers le haut, on dispatch vers le haut.**

```
BPC_Dash  ──OnDashPerformed──▶  BP_PlayerCharacter  ──OnStyleEvent──▶  BPC_StyleMeter
                                        │
                                        └──OnSpeedChanged──▶  WBP_HUD  (bind, pas de Tick)
```

| De → Vers | Mécanisme |
|---|---|
| Composant → Character | Event Dispatcher |
| Character → HUD | Event Dispatcher, bind au `BeginPlay` du widget |
| Joueur → Ennemi (dégâts) | `BPI_Damageable` |
| Ennemi → Score | `BPI_ScoreEvent` vers le `GS_` |
| LevelManager → GameMode | Appel direct (référence connue) |
| Niveau → Run | via `GI_Overdrive` (persiste entre les maps) |
| Upgrades → Stats | `BPC_UpgradeManager` pousse dans `BPC_PlayerStats` au `BeginPlay` |

**Interdit** : `Get All Actors Of Class` en Tick · `Cast To BP_PlayerCharacter` en Tick depuis un ennemi ·
référence directe d'un ennemi vers le HUD · logique de score dans le `BP_PlayerCharacter`.

---

## 4. Cycle de vie d'une run

```
L_Menu
  │ Play
  ▼
GI_Overdrive.StartNewRun()        → reset upgrades, seed, index niveau = 0
  │
  ▼
OpenLevel(L_W1_01)
  │
  ├─ GM_Overdrive.BeginPlay       → spawn joueur, applique les upgrades depuis GI
  ├─ BP_LevelManager.BeginPlay    → charge DA_LevelData, arme les triggers
  ├─ [GAMEPLAY]                   → GS_ agrège kills / temps / vitesse / style
  │
  ▼
BP_LevelEndTrigger
  ├─ BPC_ScoreManager.ComputeScore()   → S_LevelScore
  ├─ WBP_Results                        → affichage + comparaison S-Rank
  ├─ BP_LootChest.Roll(Rank)            → 1..3 propositions
  ├─ WBP_LootChest                      → le joueur choisit
  ├─ GI_Overdrive.AddUpgrade()
  ▼
OpenLevel(niveau suivant)  …  jusqu'au Boss 02
  ▼
GI_Overdrive.EndRun(Success/Failed)
```

### Mort (`11_ARBITRAGES D1`)
```
BPC_Health.OnDeath (joueur)
  ├─ GI_Overdrive.ConsumeLife()   → S_RunState.LivesRemaining -= 1
  │
  ├─ SI LivesRemaining > 0
  │    ├─ GS_.RegisterDeath()     → Score_DeathPenalty, style reset à Style_Start
  │    ├─ le chrono CONTINUE de tourner (jamais mis en pause)
  │    ├─ fade Restart_FadeDuration (BP_DeathCam)
  │    └─ respawn au dernier checkpoint — upgrades CONSERVÉS, niveau conservé
  │
  └─ SI LivesRemaining == 0
       ├─ E_GameState.RunFailed
       ├─ WBP_RunFailed           → récap de la run, score total, niveau atteint
       └─ retour au menu → GI_Overdrive.StartNewRun() au prochain Play
```

### Portée des données (la règle qui décide de tout)

| Donnée | Survit à une mort | Survit au niveau suivant | Survit à une nouvelle run |
|---|---|---|---|
| `ActiveUpgrades` | ✅ | ✅ | ❌ |
| `LivesRemaining` | décrémenté | ✅ (jamais rechargé) | ❌ (reset à `Run_MaxLives`) |
| `LevelScores` | ✅ | ✅ | ❌ |
| `CurrentLevelIndex` | ✅ | incrémenté | ❌ |
| Style multiplier | ❌ (reset) | ❌ | ❌ |
| Chrono du niveau | ✅ (continue) | ❌ | ❌ |

**Tout ce qui survit vit dans `GI_Overdrive`. Tout ce qui meurt vit dans `GS_Overdrive`.**
C'est la seule règle à retenir pour savoir où ranger une variable.

---

## 5. Ordre d'implémentation (dépendances)

```
1. BPC_MovementState          ← rien ne fonctionne sans lui
2. BPC_Slide, BPC_Dash, BPC_WallRide
3. BP_LaserWeapon + BPC_Heat
4. BPC_Health + BPI_Damageable
5. BP_EnemyBase + DA_EnemyData
6. BPC_Melee + BPC_KnockbackReceiver
7. BP_LevelManager + DA_LevelData
8. BPC_ScoreManager + BPC_StyleMeter
9. WBP_HUD + WBP_Results
10. BP_LootChest + BPC_UpgradeManager + BPC_PlayerStats
11. BP_BossBase
12. Menus
```

Ne jamais commencer un maillon avant que le précédent soit **testé en jeu**, pas juste compilé.

---

## 6. Ce qui n'existe PAS dans cette architecture

Pas de : Gameplay Ability System · Common UI · système de save/load · réplication réseau ·
event bus global · injection de dépendances · manager de managers · pooling d'objets
(sauf si un profil de perf le prouve nécessaire) · state machine générique réutilisable.

Si tu es tenté d'en ajouter un : relis `Docs/03_SCOPE_LOCK.md`.
