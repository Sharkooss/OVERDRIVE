# 08 — DATA SCHEMAS

> Toutes les Enums, Structs, DataAssets et DataTables du projet.
> **Crée-les exactement comme décrit ici.** Si tu as besoin d'un champ qui n'existe pas :
> ajoute-le à ce document en premier, puis à l'asset.
>
> Emplacement : `Content/OVERDRIVE/Data/{Enums,Structs,DataAssets,DataTables,Curves}/`

---

## 1. Enums (`Data/Enums/`)

### `E_MovementState`
`Idle` · `Walking` · `Sprinting` · `Sliding` · `Jumping` · `Falling` · `WallRiding` · `Dashing`

### `E_HeatState`
`Cooling` · `Building` · `Warning` · `Overheated`

> **L'enum est INCHANGÉ. Seule sa sémantique change** (`11_ARBITRAGES D58`, 2026-08-20).
> Il a été saisi **à la main par Louis** et aucun outil du projet ne sait créer ou modifier un enum
> (`12_PIEGES §5.2`) : **on n'y touche pas**, on redéfinit ce que ses valeurs veulent dire.

| Valeur | Sémantique (depuis `D58`) |
|---|---|
| `Cooling` | la chaleur **descend** — headshot encaissé, ou vitesse ≥ `Heat_CoolSpeedThreshold` |
| `Building` | la chaleur **monte** — un tir **raté** vient de partir |
| `Warning` | `CurrentHeat >= Heat_WarningThreshold` — **`Style_Loss_Heat` s'applique** |
| `Overheated` | `CurrentHeat >= Heat_Max` — **pénalité de style au MAXIMUM.** ⚠️ Ce n'est **plus** « tir bloqué » : plus rien n'est bloqué par la chaleur, jamais (`SPEC_COMBAT §4`) |

### `E_Rank`
`D` · `C` · `B` · `A` · `S`
*(ordre croissant volontaire : `D=0` … `S=4`, pour comparer avec `>=`)*

### `E_Rarity`
`Common` · `Rare` · `Epic`

### `E_EnemyType`
`Grunt` · `Shooter` · `Tank` · `Boss`

### `E_DamageType`
`Laser` · `LaserHeadshot` · `Melee` · `WallSlam` · `EnemyProjectile` · `EnemyMelee` · `Environment`

### `E_StyleEvent`
`Kill` · `Headshot` · `MeleeKill` · `WallSlamKill` · `SlideKill` · `AirKill` ·
`WallRideTick` · `Dash` · `HighSpeedTick` · `TookDamage` · `Idle` · `Death`

### `E_UpgradeStat`
`MaxHealth` · `LaserDamage` · `MeleeDamage` · `MaxSpeed` · `Acceleration` · `SpeedRetention` ·
`DashCooldown` · `DashCharges` · `SlideBoost` · `WallRideDuration` · `HeatCapacity` · `HeatRecovery`

### `E_UpgradeModifier`
`None` · `DashRechargeOnKill` · `OverchargedLaser` · `MomentumCore` · `Impact` · `ThermalCore`

### `E_GameState`
`MainMenu` · `RunStarting` · `Gameplay` · `Paused` · `LevelComplete` · `Loot` ·
`Transitioning` · `RunComplete` · `RunFailed`

### `E_LevelSection`
`Intro` · `SpeedSpace` · `Combat` · `MovementSection` · `FinalRun` · `BossArena`
*(sert uniquement au level design et au debug, pas au gameplay)*

### `E_BossState`
`Dormant` · `Intro` · `Phase1` · `PhaseTransition` · `Phase2` · `Stunned` · `Dying`
*(machine à états de `BP_BossBase`. `PhaseTransition` dure `Boss_PhaseTransitionPause`,
`Stunned` correspond au `Boss02_SelfStunDuration`. Max 2 phases, cf. `PDA_BossData.PhaseCount`)*

### `E_ScoreComponent`
`Kills` · `Speed` · `Time` · `Style`
*(sert à `GetLimitingStat()` sur l'écran de résultats. Ordre de départage en cas d'égalité :
**TIME > KILLS > STYLE > SPEED** — cf. `11_ARBITRAGES D13`)*

---

## 2. Structs (`Data/Structs/`)

### `S_LevelScore`
| Champ | Type | Note |
|---|---|---|
| `LevelID` | Name | ex. `W1_01` |
| `TimeSeconds` | Float | |
| `Kills` | Int | |
| `TotalEnemies` | Int | |
| `Headshots` | Int | |
| `MaxSpeed` | Float | uu/s |
| `AverageSpeed` | Float | uu/s |
| `PeakStyleMultiplier` | Float | |
| `FinalStyleMultiplier` | Float | |
| `Deaths` | Int | |
| `DamageTaken` | Float | |
| `ScoreKills` | Int | |
| `ScoreSpeed` | Int | |
| `ScoreTime` | Int | |
| `TotalScore` | Int | |
| `Rank` | `E_Rank` | |

### `S_RankThresholds`
| Champ | Type | Note |
|---|---|---|
| `ScoreS` / `ScoreA` / `ScoreB` / `ScoreC` | Int | |
| `ParTimeSeconds` | Float | |
| `TargetKills` | Int | |
| `TargetStyle` | Float | |
| `TargetAverageSpeed` | Float | uu/s — **c'est ce champ qui sert à la comparaison de score** |
| `TargetMaxSpeed` | Float | uu/s — **affichage seulement**, jamais comparé au score |

*Sert aussi à alimenter l'écran de comparaison « S RANK vs YOUR RUN » (GDD §42).*

> **`11_ARBITRAGES D14`** : la vitesse comparée au S Rank est l'**`AverageSpeed`**, parce que c'est
> elle qui alimente `ScoreSpeed` (`ScoreSpeed = round(AvgSpeed / 10) × 5`). `TargetMaxSpeed` reste
> dans le struct comme repère de lecture au HUD de résultats, mais n'entre dans aucun calcul.

### `S_UpgradeInstance`
| Champ | Type | Note |
|---|---|---|
| `UpgradeID` | Name | |
| `DisplayName` | Text | localisable |
| `Description` | Text | |
| `Rarity` | `E_Rarity` | |
| `Stat` | `E_UpgradeStat` | |
| `Modifier` | `E_UpgradeModifier` | `None` si upgrade de stat pure |
| `Value` | Float | additif ou multiplicatif selon `bIsPercentage` |
| `bIsPercentage` | Bool | |
| `Icon` | Texture2D (soft) | |
| `MaxStacks` | Int | 0 = illimité |

### `S_LootRollResult`
| Champ | Type |
|---|---|
| `Offers` | Array\<`S_UpgradeInstance`\> |
| `ChestRank` | `E_Rank` |

### `S_EnemySpawnEntry`
| Champ | Type | Note |
|---|---|---|
| `EnemyData` | `PDA_EnemyData` (soft) | |
| `SpawnTransform` | Transform | |
| `SectionTag` | Name | pour le spawn par section |
| `bCountsForScore` | Bool | défaut `true` |

### `S_RunState`
| Champ | Type | Note |
|---|---|---|
| `CurrentLevelIndex` | Int | |
| `ActiveUpgrades` | Array\<`S_UpgradeInstance`\> | **conservé à la mort**, vidé seulement par `StartNewRun()` |
| `LivesRemaining` | Int | initialisé à `Run_MaxLives`. `0` → `E_GameState.RunFailed` (`11_ARBITRAGES D1`) |
| `LevelScores` | Array\<`S_LevelScore`\> | |
| `TotalRunScore` | Int | |
| `TotalDeaths` | Int | |
| `RunStartTime` | Float | |

> **Portée d'une run (`11_ARBITRAGES D1`)** : `S_RunState` vit dans `GI_Overdrive` et survit à
> `OpenLevel`. Il n'est réinitialisé que par `StartNewRun()` — c'est-à-dire au retour au menu
> principal ou après un `RunFailed`. Une mort décrémente `LivesRemaining` et ne touche à rien d'autre.

### `S_StyleEventDef`
| Champ | Type |
|---|---|
| `Event` | `E_StyleEvent` |
| `Delta` | Float |
| `bIsPerSecond` | Bool |
| `DisplayText` | Text |

### `S_DamageInfo`
| Champ | Type |
|---|---|
| `Amount` | Float |
| `Type` | `E_DamageType` |
| `HitLocation` | Vector |
| `HitNormal` | Vector |
| `HitBone` | Name |
| `Instigator` | Actor (soft) |
| `KnockbackImpulse` | Vector |
| `SpeedPenaltyPercent` | Float |

---

## 3. Primary Data Assets (classes) — `Data/DataAssets/`

### `PDA_EnemyData`
Instances : `DA_Enemy_Grunt`, `DA_Enemy_Shooter`, `DA_Enemy_Tank`.
Valeurs de départ : `Docs/07_TUNING.md §13`.

| Champ | Type |
|---|---|
| `EnemyType` | `E_EnemyType` |
| `DisplayName` | Text |
| `MaxHealth` | Float |
| `bHeadshotIsLethal` | Bool |
| `HeadshotMultiplier` | Float |
| `MoveSpeed` | Float |
| `AcceptanceRadius` | Float |
| `DetectionRange` | Float |
| `AttackRange` | Float |
| `AttackCooldown` | Float |
| `AttackDamage` | Float |
| `PlayerSpeedPenaltyPercent` | Float |
| `ScoreBase` | Int |
| `StyleGainOnKill` | Float |
| `KnockbackResistance` | Float (0–1) |
| `bCanBeWallSlammed` | Bool |
| `SkeletalMesh` / `AnimBP` / `AIControllerClass` / `StateTree` | soft refs |
| `HitVFX` / `DeathVFX` / `HitSFX` / `DeathSFX` | soft refs |
| `ProjectileClass` | soft class (Shooter uniquement) |

### `PDA_LevelData`
Instances : `DA_Level_W1_01` … `DA_Level_W2_06`, `DA_Level_W1_Boss`, `DA_Level_W2_Boss`.

| Champ | Type |
|---|---|
| `LevelID` | Name |
| `DisplayName` | Text |
| `WorldIndex` | Int |
| `LevelIndex` | Int |
| `MapReference` | Soft World Reference |
| `RankThresholds` | `S_RankThresholds` |
| `TotalEnemies` | Int |
| `bIsBossLevel` | Bool |
| `MusicTrack` | soft ref |
| `NextLevel` | `PDA_LevelData` (soft) |
| `IntroHintText` | Text |

### `PDA_WeaponData`
Instance : `DA_Weapon_Laser`. Valeurs : `Docs/07_TUNING.md §11`.

| Champ | Type |
|---|---|
| `BodyDamage` / `HeadshotDamage` / `HeadshotMultiplier` | Float |
| `Range` / `FireCooldown` / `TraceRadius` / `RecoilPitch` | Float |
| `HeatMax` / `HeatWarningThreshold` / `HeatTickInterval` | Float |
| **`HeatPerMissedShot`** | Float — **À AJOUTER au J9** (`D58`) |
| **`HeatCoolPerHeadshot`** | Float — **À AJOUTER au J9** (`D58`) |
| **`HeatCoolRateAtSpeed`** | Float — **À AJOUTER au J9** (`D58`) |
| **`HeatCoolSpeedThreshold`** | Float — **À AJOUTER au J9** (`D58`) |
| ⛔ `HeatPerShot` / `HeatDecayRate` / `HeatDecayDelay` | Float — **INACTIVES** (`D58`), conservées, lues par personne |
| ⛔ `OverheatDuration` / `OverheatExitThreshold` / `OverheatDecayMultiplier` | Float — **INACTIVES** (`D58`), conservées, lues par personne |
| `RecoilReturnInterpSpeed` | Float |
| ~~`TraceChannel`~~ | **retiré au J8** — voir ci-dessous |
| `MuzzleVFX` / `BeamVFX` / `ImpactVFX` / `HeadshotImpactVFX` | `NiagaraSystem` (ref **dure**) |
| `FireSFX` / `ImpactSFX` / `HeadshotSFX` / ⛔ `DenySFX` | `SoundBase` (ref **dure**). `DenySFX` est **sans objet** depuis `D58` : aucun tir n'est refusé. Champ conservé, non lu |

> ### 🔥 Refonte de la chaleur — `11_ARBITRAGES D58` (2026-08-20)
>
> **✅ FAIT au J9 (2026-08-20). 29 propriétés, comptées et relues.**
>
> **Ajouté au J9** — 4 propriétés `Instance Editable`, catégorie **`Heat`** (et non `Combat` :
> c'est celle qui portait déjà `HeatMax` / `HeatWarningThreshold` / `HeatTickInterval` depuis le J8),
> valeurs dans `07_TUNING §11` : `HeatPerMissedShot` **11** · `HeatCoolPerHeadshot` **25** ·
> `HeatCoolRateAtSpeed` **20** · `HeatCoolSpeedThreshold` **3000**.
> `DA_Weapon_Laser` renseigné puis **relu**, et les 7 valeurs **revérifiées sur l'instance PIE**
> via le cache de `BPC_Heat` — c'est la seule lecture qui prouve que le bon champ est lu.
>
> **À NE PAS supprimer** — les 6 propriétés marquées ⛔ ci-dessus (`HeatPerShot`, `HeatDecayRate`,
> `HeatDecayDelay`, `OverheatDuration`, `OverheatExitThreshold`, `OverheatDecayMultiplier`)
> **restent en place et restent renseignées dans `DA_Weapon_Laser`**. Elles deviennent **inertes** :
> **aucun Blueprint ne doit les lire**. Même convention que `Dash_GravityScale` (`D31`) et les
> `BHop_*` (`D52`) — une clé morte effacée revient un jour sous un autre nom.
> ⚠️ Corollaire de revue : au J9, un `BPC_Heat` qui lit `WeaponData.HeatDecayRate` **compile sans
> le moindre warning**. C'est le mode d'échec à surveiller.
>
> **`HeatMax` et `HeatWarningThreshold` sont conservées et actives**, `HeatTickInterval` aussi —
> c'est le timer de chaleur qui applique `HeatCoolRateAtSpeed` **et** `Style_Loss_Heat`.
>
> **Compte de propriétés** : 25 au J8 → **29 attendues** après le J9 (aucune suppression).

> **État réel au J8 : 25 propriétés `Instance Editable`**, créées par outil et relues une par une.
> Trois écarts assumés par rapport à la liste d'origine, tous documentés ici :
> - **`TraceChannel` n'existe pas.** Aucun outil ne sait créer une variable typée enum
>   (`12_PIEGES §5.2`), et `ETraceTypeQuery` en est une. Le canal `Weapon` est posé en **littéral
>   sur le pin** du nœud de trace, ce que `set_pin_value` sait faire. Ce n'est pas une valeur de
>   gameplay mais une constante de câblage : elle ne relève pas de R3. À rajouter à la main le jour
>   où une seconde arme aurait besoin d'un autre canal.
> - **`HeatTickInterval` et `RecoilReturnInterpSpeed` ont été ajoutés** : ces deux clés existaient
>   dans `07_TUNING §11` sans hôte. Toutes les clés du §11 ont désormais un champ.
> - **Les refs VFX/SFX sont dures, pas soft.** `add_object_variable` ne produit que des refs dures.
>   Sans conséquence à cette échelle — le DataAsset d'arme est chargé en permanence. À revoir si le
>   budget mémoire le demande, jamais avant.

### `PDA_MovementData`
Instance unique : `DA_Movement_Default`. **Miroir exact de `Docs/07_TUNING.md §2–§10.**
Le `BPC_MovementState` lit ce DataAsset ; les upgrades le surchargent via `BPC_PlayerStats`.
Un seul asset = un seul endroit à tweaker en playtest.

### `PDA_WorldData`
> **Rendu éclairé (`11_ARBITRAGES D2/D33`)** : cette classe pilote de **vraies lumières**, pas seulement
> `MPC_Global`. Champs d'éclairage obligatoires, lus par `BP_LightingRig` au `BeginPlay` :
> `SunIntensity` (lux) · `SunRotation` (Rotator) · `SunColor` · `SkyIntensity` ·
> `SkyZenithColor` · `SkyHorizonColor` · `FogDensity` · `FogColor` · `SignageAccentColor`.
> Valeurs de départ par ambiance : `Docs/ArtDirection/PALETTE.md §4`.
Instances : une par ambiance, **4 au total** (cf. `SPEC_ART_DIRECTION`, `ArtDirection/PALETTE.md`).
Lue par `BP_LightingRig`, qui pousse les valeurs dans `MPC_Global` au `BeginPlay` du niveau.

| Champ | Type | Note |
|---|---|---|
| `WorldID` | Name | ex. `W1_Neon` |
| `DisplayName` | Text | |
| `DominantColor` | Linear Color | dominante de l'ambiance (token `PALETTE.md`) |
| `AccentColors` | Array\<Linear Color\> | accents autorisés — **jamais** les couleurs réservées au gameplay (cf. `11_ARBITRAGES D3`) |
| `FogColor` | Linear Color | poussé dans `MPC_Global.FogColor` |
| `AmbientColor` | Linear Color | poussé dans `MPC_Global.AmbientColor` |
| `SunDirection` | Vector | direction du `N·L` simulé (rendu Unlit, cf. `11_ARBITRAGES D2`) |
| `SunColor` | Linear Color | poussé dans `MPC_Global.SunColor` |
| `EmissiveIntensity` | Float | multiplicateur global des émissifs de l'ambiance |
| `WorldTint` | Linear Color | poussé dans `MPC_Global.WorldTint` |
| `MusicTrack` | soft ref (`MU_*`) | musique de l'ambiance |

### `PDA_UpgradeDefinition`
Une instance par upgrade (`DA_Upg_MaxSpeed_Common`, `DA_Upg_ThermalCore_Epic`, …).
Champs = ceux de `S_UpgradeInstance`.

### `PDA_BossData`
Hérite conceptuellement de `PDA_EnemyData`, ajoute :

| Champ | Type |
|---|---|
| `PhaseCount` | Int (max 2) |
| `Phase2HealthThreshold` | Float (0–1) |
| `AttackPatterns` | Array\<Name\> |
| `ArenaBoundsTag` | Name |
| `IntroDuration` | Float |

---

## 4. Data Tables (`Data/DataTables/`)

### `DT_LootTable_D` / `_C` / `_B` / `_A` / `_S`
Row Struct : **`S_LootTableRow`**

| Champ | Type |
|---|---|
| `UpgradeDefinition` | `PDA_UpgradeDefinition` (soft) |
| `Rarity` | `E_Rarity` |
| `Weight` | Float |
| `bUniquePerRun` | Bool |

Probabilités de rareté par coffre : `Docs/07_TUNING.md §15`.
Algorithme : tirer la rareté selon la table du coffre → tirer une entrée pondérée dans cette rareté →
répéter `NbChoix` fois sans doublon.

### `DT_StyleEvents`
Row Struct : `S_StyleEventDef`. Une ligne par `E_StyleEvent`. Valeurs : `Docs/07_TUNING.md §14`.

### `DT_RankThresholds`
Row Struct : `S_RankThresholds`, une ligne par `LevelID`.
**Redondant avec `PDA_LevelData`** — choisir **une seule** des deux sources.
👉 **Décision : la source est `PDA_LevelData`.** Cette table n'est créée que si un besoin
d'édition en masse apparaît. Ne pas la créer en J1.

---

## 5. Curves (`Data/Curves/`)

| Asset | Domaine → Image | Usage |
|---|---|---|
| `CF_FOVBySpeed` | `uu/s` → `°` additifs | FOV dynamique |
| `CF_SpeedLinesBySpeed` | `uu/s` → `0–1` | intensité post-process |
| `CF_CameraTiltByStrafe` | `-1..1` → `°` | roulis caméra |
| `CF_MusicIntensityBySpeed` | `uu/s` → `0–1` | mix musique (optionnel) |
| `CF_DashVelocity` | `0–1` (temps normalisé) → ratio | profil du dash |
| `CF_SlideFrictionOverTime` | `0–1` → friction | fin de slide progressive |
| `CF_WallSlamDamageBySpeed` | `uu/s` → `pv` | dégâts d'impact mural |

**Les courbes remplacent les `Lerp` en dur.** Elles sont éditables sans recompiler un BP :
c'est le levier de tuning le plus rapide.

---

## 6. Material Parameter Collection

### `MPC_Global` (`Art/Materials/`)
| Paramètre | Type | Écrit par |
|---|---|---|
| `PlayerSpeed01` | Scalar | `BPC_MovementState` |
| `StyleMultiplier01` | Scalar | `BPC_StyleMeter` |
| `HeatRatio` | Scalar | `BPC_Heat` |
| `OverheatActive` | Scalar | `BPC_Heat` |
| `DamageFlash01` | Scalar | `BPC_Health` |
| `DashFlash` | Scalar | `BPC_Dash` |
| `DamageVignette` | Scalar | `BPC_Health` |
| `WorldTint` | Vector | `BP_LevelManager` |
| `SunDirection` | Vector | `BP_LightingRig` (depuis `PDA_WorldData`) |
| `SunColor` | Vector | `BP_LightingRig` (depuis `PDA_WorldData`) |
| `AmbientColor` | Vector | `BP_LightingRig` (depuis `PDA_WorldData`) |
| `FogColor` | Vector | `BP_LightingRig` (depuis `PDA_WorldData`) |

### Formule officielle de `PlayerSpeed01` (`11_ARBITRAGES D9`)

```
PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                       / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )
```

- **Écrit par `BPC_MovementState` uniquement.** Aucun autre composant n'y touche
  (`BPC_PlayerStats` n'écrit **rien** dans `MPC_Global`).
- **Cadence : timer unique 20 Hz** dans `BPC_MovementState`, qui alimente aussi le vent (`MS_Wind_Speed`)
  et `WBP_SpeedMeter`. Pas de Tick.
- **Ne sert PAS au FOV** : le FOV lit la vitesse brute via `CF_FOVBySpeed`.
  Ce scalaire n'existe que pour les effets de vitesse (speed lines, aberration, vignette).
- Seuils : `SpeedLines_StartSpeed` / `SpeedLines_FullSpeed` (`Docs/07_TUNING.md §16`).

Permet aux matériaux d'environnement et de post-process de réagir à la vitesse **sans logique BP**.

---

## 7. Ordre de création recommandé

```
1. Enums (tous, d'un coup — ça débloque tout le reste)
2. S_DamageInfo + BPI_Damageable
3. PDA_MovementData + DA_Movement_Default
4. PDA_WeaponData + DA_Weapon_Laser
5. PDA_EnemyData + les 3 DA_Enemy_*
6. S_LevelScore, S_RankThresholds, PDA_LevelData
7. S_UpgradeInstance, PDA_UpgradeDefinition, DT_LootTable_*
8. Curves (au fur et à mesure du besoin)
```
