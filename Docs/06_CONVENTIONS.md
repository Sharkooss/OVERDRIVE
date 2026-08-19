# 06 — CONVENTIONS

> Source de vérité pour le nommage et l'organisation. Toute violation est un bug à corriger.
> Base : Epic Games Style Guide (ex-Allar), adapté UE 5.8.

---

## 1. Règle d'or

**Tout le contenu du jeu vit dans `Content/OVERDRIVE/`.**
La racine de `Content/` ne contient que les dossiers du template d'origine (à supprimer, cf. Roadmap J1)
et les dossiers moteur (`Collections`, `Developers`).

Un asset ne se trouve **jamais** à deux endroits. Un asset est rangé par **domaine fonctionnel**,
pas par type. (`Enemies/Grunt/` contient le BP, le mesh, l'anim et le matériau du Grunt.)

---

## 2. Préfixes d'assets

### Blueprints & logique
| Préfixe | Type | Exemple |
|---|---|---|
| `BP_` | Blueprint Class (Actor, Pawn, Character…) | `BP_PlayerCharacter` |
| `BPC_` | Blueprint **Component** (ActorComponent) | `BPC_Health` |
| `BPI_` | Blueprint **Interface** | `BPI_Damageable` |
| `BPFL_` | Blueprint Function Library | `BPFL_MathHelpers` |
| `BPM_` | Blueprint Macro Library | `BPM_Movement` |
| `GM_` | GameMode | `GM_Overdrive` |
| `GS_` | GameState | `GS_Overdrive` |
| `PC_` | PlayerController | `PC_Overdrive` |
| `GI_` | GameInstance | `GI_Overdrive` |
| `PS_` | PlayerState | `PS_Overdrive` |
| `SUB_` | Subsystem BP | `SUB_RunManager` |
| `ST_` | **StateTree** (plugin `GameplayStateTree`) | `ST_Enemy_Shooter` |
| `SG_` | **SaveGame** | `SG_Overdrive_Settings` |

### Données
| Préfixe | Type | Exemple |
|---|---|---|
| `E_` | Enum | `E_Rank` |
| `S_` | Struct | `S_LevelScore` |
| `DA_` | Data Asset (instance) | `DA_Enemy_Grunt` |
| `PDA_` | Primary Data Asset (**classe**) | `PDA_EnemyData` |
| `DT_` | Data Table | `DT_LootTable_S` |
| `CF_` | Curve Float | `CF_FOVBySpeed` |
| `CV_` | Curve Vector | `CV_DashProfile` |

**Variables de cache de tuning** : une valeur d'un `DA_*` recopiée au `BeginPlay` pour éviter un
`Get` par frame se nomme **`Tune_<Clé>`** et vit dans la catégorie `<Système>|Cached`
(ex. `Tune_SpeedSprintCap` ← `DA_Movement_Default.Speed_SprintCap`). Elles sont remplies par une
fonction `CacheTuning()` — c'est le seul point à rappeler quand `BPC_PlayerStats` applique un
upgrade. *(Décision D8, J2 — `T_` était déjà pris par les textures.)*

### Art
| Préfixe | Type | Exemple |
|---|---|---|
| `SM_` | Static Mesh | `SM_Module_Wall_400` |
| `SK_` | Skeletal Mesh | `SK_Enemy_Grunt` |
| `SKEL_` | Skeleton | `SKEL_Enemy_Humanoid` |
| `PHYS_` | Physics Asset | `PHYS_Enemy_Grunt` |
| `M_` | Material (master) | `M_Toon_Base` |
| `MI_` | Material Instance | `MI_Toon_Wall_Purple` |
| `MF_` | Material Function | `MF_ToonShading` |
| `MPC_` | Material Parameter Collection | `MPC_Global` |
| `CS_` | Camera Shake (Legacy Camera Shake BP) | `CS_Headshot` |
| `PP_` | Post Process Material | `PP_SpeedLines` |
| `T_` | Texture | `T_Noise_Grunge` |
| `DEC_` | Decal Material | `DEC_LaserScorch` |

Suffixes de texture : `_D` (BaseColor), `_N` (Normal), `_ORM` (Occlusion/Rough/Metal),
`_E` (Emissive), `_M` (Mask), `_A` (Alpha).

### Animation
| Préfixe | Type | Exemple |
|---|---|---|
| `ABP_` | Animation Blueprint | `ABP_PlayerArms` |
| `A_` | Animation Sequence | `A_Laser_Fire` |
| `AM_` | Animation Montage | `AM_Melee_Punch` |
| `BS_` | Blend Space | `BS_Enemy_Locomotion` |
| `AN_` | Anim Notify | `AN_MeleeHit` |
| `ANS_` | Anim Notify State | `ANS_MeleeWindow` |
| `CR_` | Control Rig | `CR_PlayerArms` |

### VFX
| Préfixe | Type | Exemple |
|---|---|---|
| `NS_` | Niagara System | `NS_LaserImpact` |
| `NE_` | Niagara Emitter | `NE_Sparks` |
| `NM_` | Niagara Module | `NM_SpeedScale` |
| `NPC_` | Niagara Parameter Collection | `NPC_Combat` |

### Audio
| Préfixe | Type | Exemple |
|---|---|---|
| `S_`* | Sound Wave | `S_Laser_Fire_01` |
| `SC_` | Sound Cue | `SC_Laser_Fire` |
| `MS_` | MetaSound Source | `MS_Laser` |
| `SCL_` | Sound Class | `SCL_SFX` |
| `SMX_` | Sound Mix | `SMX_Default` |
| `ATT_` | Sound Attenuation | `ATT_Enemy3D` |
| `SCC_` | Sound Concurrency | `SCC_Impacts` |
| `MU_` | **Music** (piste musicale) | `MU_W1_Ignition` |

\* Les Sound Waves utilisent `S_` ; comme les Structs utilisent aussi `S_`, ils ne se croisent jamais
(dossiers `Audio/` vs `Data/Structs/`). Si ambiguïté, préfixe l'audio `SW_`.

### UI
| Préfixe | Type | Exemple |
|---|---|---|
| `WBP_` | Widget Blueprint | `WBP_HUD` |
| `WBP_` (composant) | Sous-widget réutilisable | `WBP_HeatBar` |
| `F_` | Font | `F_Overdrive_Display` |
| `SL_` | Slate Widget Style / Brush | `SL_ButtonPrimary` |

### Niveaux
| Préfixe | Type | Exemple |
|---|---|---|
| `L_` | Level (umap) | `L_W1_01_Ignition` |
| `LI_` | Level Instance / sous-niveau | `LI_W1_01_Lighting` |

Format des niveaux de jeu : `L_W<world>_<num>_<NomCourt>`
→ `L_W1_01_Ignition`, `L_W1_Boss`, `L_W2_04_Freefall`, `L_Menu`, `L_Sandbox_Movement`.

### Input
| Préfixe | Type | Exemple |
|---|---|---|
| `IA_` | Input Action | `IA_Dash` |
| `IMC_` | Input Mapping Context | `IMC_Gameplay` |

---

## 3. Nommage des variables Blueprint

- **Anglais**, `PascalCase` : `CurrentSpeed`, `MaxHeat`, `bIsSliding`.
- Booléens préfixés `b` et formulés en question : `bIsSliding`, `bCanDash`, `bHasOverheated`.
- **Jamais** de nom générique : `NewVar`, `Temp`, `Value2`, `Float3`.
- Toute variable de tuning : `Instance Editable` + **Category** obligatoire.
  Catégories autorisées : `Movement | Combat | Health | Score | Loot | Feedback | Debug`.
- Toute variable exposée porte un **Tooltip** contenant son unité (`uu/s`, `s`, `°`, `%`).

### Fonctions & événements
- Fonctions : verbe à l'infinitif, `PascalCase` → `ApplyDamage`, `TryStartSlide`, `ComputeRank`.
- Fonctions pures : préfixe `Get` / `Is` / `Can` → `GetSpeedRatio`, `CanWallRide`.
- Events custom : `On` + fait passé → `OnEnemyKilled`, `OnOverheatStarted`.
- Dispatchers : `On` + fait passé, suffixe explicite → `OnHeatChanged`, `OnRankComputed`.

---

## 4. Hygiène Blueprint

1. **Le graph se lit de gauche à droite.** Pas de fil qui remonte en arrière sans reroute node.
2. **Un Event Graph ne dépasse pas un écran et demi.** Au-delà → extraire en fonction.
3. **Commentaires obligatoires** : chaque bloc logique dans une Comment Box titrée.
4. **Pas de `Cast To` répété dans Tick.** Cache la référence au `BeginPlay`.
5. **Pas de `Get All Actors Of Class` dans Tick.** Jamais.
6. **Tick interdit par défaut.** Si tu actives Tick, tu justifies en commentaire dans le BP.
   Préférer Timers, Timelines, ou les events du Character Movement.
7. **Communication** :
   - Parent → enfant : appel direct / fonction.
   - Enfant → parent : **Event Dispatcher**.
   - Entre systèmes non liés : **Blueprint Interface** (`BPI_`) ou GameState.
   - Jamais de `Get Player Character` + `Cast` depuis un ennemi dans Tick.
8. **Zéro warning de compilation.** Un BP qui compile avec warnings n'est pas fini.

---

## 5. Organisation des dossiers `Content/OVERDRIVE/`

```
Content/OVERDRIVE/
├─ Core/           GM_, GS_, PC_, GI_, PS_, BPI_ globaux
├─ Player/
│  ├─ Blueprints/  BP_PlayerCharacter, BP_PlayerCameraManager, BP_DeathCam
│  │  └─ Shakes/   CS_LaserFire, CS_Headshot, CS_MeleeHit, CS_TakeDamage, CS_HardCollision, CS_WallSlam
│  ├─ Components/  BPC_Movement*, BPC_Health, BPC_PlayerStats
│  ├─ Animation/   ABP_, AM_, A_
│  ├─ Meshes/      SK_ bras FP, SM_ arme
│  └─ Input/       IA_, IMC_
├─ Weapons/
│  ├─ Laser/       BP_LaserWeapon, BPC_Heat, VFX/SFX propres
│  └─ Melee/       BPC_Melee, AM_Melee_Punch
├─ Enemies/
│  ├─ Base/        BP_EnemyBase, ABP_Enemy, BPI_Damageable   (BPC_Health est partagé, il vit dans Systems/Health/)
│  ├─ Grunt/ Shooter/ Tank/   BP + SK + anim + DA_
│  ├─ AI/          BP_AIController_*, ST_Enemy_Shooter, ST_Enemy_Tank   (le Grunt = FSM dans son BP)
│  └─ Shared/      BP_EnemyProjectile, hit reactions
├─ Bosses/
│  ├─ Base/        BP_BossBase
│  └─ Boss01/ Boss02/
├─ Systems/
│  ├─ Score/  Loot/  Upgrades/  Run/  Level/  Health/
├─ Data/
│  ├─ Enums/ Structs/ DataAssets/ DataTables/ Curves/
├─ Levels/
│  ├─ Menu/ World01/ World02/ Sandbox/
├─ Art/
│  ├─ Materials/{Master,Instances,Functions}
│  ├─ Meshes/{Modules,Props,Dev}
│  ├─ Textures/ Decals/ PostProcess/ Lighting/
├─ VFX/            Niagara/ Materials/ Textures/ Meshes/
├─ Audio/          SFX/{Movement,Combat,Enemy,UI}  Music/  MetaSounds/  Mix/
├─ UI/             HUD/ Menus/ Results/ Loot/ Common/ Fonts/
└─ Dev/            Debug/ Sandbox/   ← jetable, jamais référencé par du contenu final
```

**Règle** : si un asset est utilisé par 2 domaines ou plus, il monte d'un cran
(ex. un mesh utilisé par Grunt et Tank va dans `Enemies/Shared/`).

---

## 6. Modules d'environnement (grid)

Toute la géométrie de niveau est construite sur une **grille de 100 uu**.
Tailles standard des modules : **100 / 200 / 400 / 800 / 1600 uu**.
Nommage : `SM_Module_<Type>_<Taille>` → `SM_Module_Wall_800`, `SM_Module_Ramp_400`.
Snap éditeur : 50 uu (translation), 15° (rotation). Détail : `Docs/Specs/SPEC_LEVELDESIGN.md`.

---

## 7. Collision & canaux

| Canal | Usage |
|---|---|
| `ECC_GameTraceChannel1` — **Projectile** | déjà créé par le template, conservé |
| `WallRideSurface` (à créer) | **Object type** des surfaces autorisées au wall ride |
| `Weapon` (à créer) | **Trace channel** du laser et du melee. Default response : `Block` |

Presets de collision à créer : `OD_Player`, `OD_Enemy`, `OD_EnemyProjectile`, `OD_WallRideSurface`, `OD_LevelGeo`.
Détail dans `Docs/Specs/SPEC_MOVEMENT.md` et `Docs/Specs/SPEC_COMBAT.md`.

---

## 8. Documentation

- Fichiers de doc : `Docs/NN_NOM_MAJUSCULE.md` pour les fondations, `Docs/Specs/SPEC_NOM.md` pour les specs.
- Toute valeur numérique de gameplay écrite ailleurs que dans `Docs/07_TUNING.md` doit
  **renvoyer vers** ce fichier, pas le dupliquer.
- Les valeurs non encore validées en jeu portent le marqueur **`[À CALIBRER]`**.
- Les décisions prises en cours de route vont dans `Docs/Journal/`.

---

## 9. Fichiers sources d'art (hors `Content/`)

Les fichiers **sources** (`.blend`, `.fbx`, `.psd`…) ne vont **jamais** dans `Content/`.
UE ne les utilise pas, ils polluent le Content Browser et partent au cook.

```
Art_Source/                    ← racine du projet, à côté de Content/
├─ OD_<Asset>.blend            fichier de travail Blender
├─ SM_<Asset>.fbx              export prêt à importer
└─ prev_*.png / uv_layout.png  aperçus de contrôle
```

L'asset importé, lui, suit §5 (ex. `SM_Weapon_LaserPistol.fbx` → `Content/OVERDRIVE/Player/Meshes/`).

### Réglages d'export FBX pour UE (Blender)

> **Cette table fait foi.** `SPEC_ART_DIRECTION §6` doit s'y conformer — en cas de divergence,
> c'est la spec qui est en tort, pas cette table. Ne pas dupliquer ces réglages ailleurs : y renvoyer.

| Réglage | Valeur |
|---|---|
| Orientation modèle | canon / avant vers **−Y**, up **+Z** → devient **+X / +Z** dans UE |
| `axis_forward` / `axis_up` | `-Z` / `Y` |
| `apply_unit_scale` | `True`, `global_scale` 1.0, `apply_scale_options` `FBX_SCALE_NONE` |
| `bake_space_transform` | `False` |
| `mesh_smooth_type` | `FACE` · `use_tspace` `True` · `use_triangles` `True` |
| `object_types` | `{MESH, EMPTY}` — les empties `SOCKET_<Nom>` parentés au mesh deviennent des sockets UE `<Nom>` |

**Unités** : 1 m Blender = 100 uu UE = 100 cm. Un asset de 0,288 m mesure donc 28,8 uu.

---

## 10. Git

Le dépôt n'est pas encore initialisé. `.gitignore` et `.gitattributes` (Git LFS) sont prêts à la racine.
Convention de commit : `type(scope): message` en anglais.
`feat(movement): add wall ride entry detection` · `fix(laser): heat not decaying on overheat exit` ·
`tune(dash): reduce cooldown to 0.9s` · `docs(score): rank thresholds for W1` · `art(env): wall modules`
