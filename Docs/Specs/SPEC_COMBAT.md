# SPEC — COMBAT

> Portée : `BP_LaserWeapon`, `BPC_Heat`, `BPC_Melee`, `BPC_KnockbackReceiver`, `BPI_Damageable`, dégâts subis.
> Hors portée : IA (`SPEC_ENEMIES.md`), score (`SPEC_SCORE_RANK.md`), mouvement (`SPEC_MOVEMENT.md`), HUD (`SPEC_UI_HUD.md`).
> **Aucune valeur numérique ici** : tout renvoie à `Docs/07_TUNING.md` par nom de clé. Blueprint only (CLAUDE.md R1).

## 1. Philosophie du combat
Le combat est un **sous-produit du mouvement**, jamais son interruption. Le joueur traverse, il ne visite pas.

| Principe | Conséquence technique |
|---|---|
| On ne s'arrête **jamais** pour tirer | Zéro ADS, zéro ralentissement au tir, zéro rooting d'anim. Tirer n'écrit jamais dans `BPC_MovementState`. |
| Deux outils, zéro arsenal | Pas de switch d'arme, pas de reload, pas de slot. |
| Les ennemis meurent vite | `TimeToKill` cible par archétype : `07_TUNING §13`. Un Grunt au-dessus de la cible = bug de design. |
| Munitions = rythme, pas gestion | La chaleur impose des pauses courtes, pas de la comptabilité. Aucun pickup de munitions. |
| Le juice EST le gameplay | Hitmarker, hit-stop headshot, son de wall slam : implémentés **en même temps** que la logique, pas après. |
| L'erreur coûte de la vitesse | Un hit ne tue pas, il ralentit (`07_TUNING §10`). On punit le joueur sur son axe de fierté. |

**Interdits** : bonus de précision à l'arrêt · spread / bloom / sway · recoil qui dérive l'aim · full-auto ·
anim qui bloque le mouvement · TTK long · ennemi éponge (le Tank est un puzzle de positionnement, pas un sac
à PV) · cooldown de tir supérieur au cooldown de dash.

## 2. `BP_LaserWeapon`
`Content/OVERDRIVE/Weapons/Laser/` — **Child Actor Component** de `BP_PlayerCharacter` (`ChildActor_Laser`,
socket `S_Weapon` de `SK_PlayerArms`). **Tick désactivé** — sauf la dérogation ci-dessous.

> ### ⚠️ Dérogation PROVISOIRE au « Tick désactivé » — J8, à retirer au J14
>
> Le Tick de `BP_LaserWeapon` est **activé** (`bCanEverTick` + `bStartWithTickEnabled`), pour **une
> seule chose** : redessiner le faisceau de debug depuis la position **courante** du muzzle.
>
> **Pourquoi elle est nécessaire.** Louis, manche en main : *« le laser ne part pas du muzzle si on se
> déplace, on a l'impression qu'il part depuis le vide, et le rayon disparaît trop vite. »* Les deux
> demandes — origine toujours au canon **et** durée plus longue avec fondu — sont **contradictoires**
> tant qu'on dessine une ligne figée en espace monde : à 3000 uu/s le canon parcourt ~50 uu par frame
> pendant que la ligne reste sur place. La seule façon d'avoir les deux est de **redessiner le
> faisceau à chaque frame**. C'est le piège 10 du §13, vécu.
>
> **Périmètre strict.** L'`EventTick` ne contient **qu'un** nœud d'appel : `UpdateBeam(DeltaSeconds)`.
> Aucune logique de gameplay, aucune trace, aucun cast, aucun dispatcher n'y entre — jamais.
> `UpdateBeam` ne fait que : entretenir `BeamStart` pendant la fenêtre d'accroche, dessiner
> (halo + cœur) tant que `BeamTimeRemaining` est positif, et le décrémenter.
>
> **Correctif J8bis — accroche puis décrochage.** Redessiner en relisant le muzzle **à chaque frame**
> pendant toute la vie du faisceau produisait un **éventail de segments** : à ~1900 uu/s le canon
> bouge de ~32 uu par frame et chaque segment vit `LaserDebug_DrawLifetime` (≈ 3 frames). Louis,
> manche en main : *« je vois deux rayons qui divergent depuis le point d'impact »*. La lecture du
> muzzle est donc bornée à `LaserDebug_AttachTime` ; ensuite l'origine est **figée en espace monde**
> et tous les redessins se superposent. Le faisceau est aussi passé à **0.35 s** avec un fondu en
> **racine carrée**, et doublé d'un **halo** concentrique (un debug line ne peut pas émettre).
>
> **Date de péremption : J14.** Quand `NS_LaserBeam` existe (Niagara, **World Space, positions figées
> à l'émission**, §13 piège 10), il remplace le dessin, `UpdateBeam` et l'`EventTick` sont supprimés,
> les variables `BeamEnd` / `BeamTimeRemaining` / `DebugBeamDuration` avec, et le Tick repasse à
> **désactivé**. Cette dérogation n'autorise **aucun** autre usage du Tick sur l'arme d'ici là.

| Élément | Type | Rôle |
|---|---|---|
| `SM_Weapon_LaserPistol` | StaticMesh (root) | Mesh FP (asset existant, `Art_Source/`), collision `NoCollision` |
| `Muzzle` | Scene | Origine **cosmétique** du beam et du muzzle flash |
| `BPC_Heat` | Component | Jauge de chaleur. **Vit sur l'arme, pas sur le character** (`05_ARCHITECTURE §2`) |
| `WeaponData` | `PDA_WeaponData` | Instance Editable, cat. `Combat`, défaut `DA_Weapon_Laser`. **Seule source des valeurs.** |
| `OwnerCharacter` / `OwnerController` | refs | Cachées au `BeginPlay`, jamais de cast en Tick |
| `bCanFire` | Bool | Gate du cooldown |
| `bUseMuzzleConfirmTrace` | Bool | Défaut `false` (§3.4) |
| `TryFire()` | Event | Point d'entrée unique depuis `IA_Fire` (§3) |
| `ResolveShot()` | Function | Traces + point d'impact. **Aucun effet de bord.** Sorties : `Hit`, `bBlockingHit`, **`bAssisted`** (J8sept, §11) |
| `ProcessHit(Hit, bHeadshot)` | Function | Construit `S_DamageInfo`, appelle `BPI_Damageable` |
| `PlayFireFX(ImpactPoint, Hit)` | Function | VFX/SFX/shake/recoil. **Aucune logique de gameplay.** **Ne dessine plus le faisceau : il l'arme** (`BeamEnd` + `BeamTimeRemaining`, cf. §2 dérogation). |
| `IsHeadshot(Hit)` | Pure | **`Hit.Component.ComponentHasTag("Head")`** — **jamais** `Hit.BoneName` (§5.1, encadré « écart d'implémentation ») |
| `EndFireCooldown()` | Event | Callback timer → `bCanFire = true` |
| `BeamStart` | Vector, cat. `Debug`, **non** `Instance Editable` | **PROVISOIRE J8bis→J14.** Origine du faisceau. Posée à `Muzzle.GetWorldLocation()` par `PlayFireFX`, **réécrite chaque frame par `UpdateBeam` tant que `Elapsed < LaserDebug_AttachTime`**, puis **figée en espace monde**. C'est le décrochage qui supprime la duplication de rayons (§13 piège 10bis). |
| `BeamEnd` | Vector, cat. `Debug` | **PROVISOIRE J8→J14.** Bout du faisceau, figé à l'émission : `Hit.ImpactPoint`, ou `Hit.TraceEnd` (= `Start + Dir × Range`) si le tir part à vide. |
| `DebugAttachTime` / `DebugGlowWidthMult` / `DebugGlowAlphaMult` | Float ×3, cat. `Debug`, `Instance Editable` | **PROVISOIRE J8bis→J14.** Fenêtre d'accroche au canon, largeur et alpha du halo. Valeurs et sémantique : `07_TUNING §16`. |
| `BeamTimeRemaining` | Float, cat. `Debug` | **PROVISOIRE J8→J14.** Temps de vie restant du faisceau. Armé à `LaserDebug_BeamDuration`, décrémenté par `UpdateBeam`. Laissé `Instance Editable` **à dessein** : c'est la sonde qui prouve que le Tick tourne en headless (`12_PIEGES §4.10`). |
| `UpdateBeam(DeltaSeconds)` | Function | **PROVISOIRE J8bis→J14.** Seul contenu de l'`EventTick`. Si `BeamTimeRemaining > 0` : (1) `BeamStart = select(Elapsed < LaserDebug_AttachTime, Muzzle.GetWorldLocation(), BeamStart)` — accroche puis **décrochage** ; (2) dessine le **halo** (`thickness × GlowWidthMult`, `alpha × GlowAlphaMult`) ; (3) dessine le **cœur** (`thickness`, `alpha`) ; (4) **puis** décrémente. `alpha = sqrt(BeamTimeRemaining / LaserDebug_BeamDuration)` — **fondu en racine carrée, pas linéaire**. Durée de dessin = `LaserDebug_DrawLifetime`. **Les deux traits lisent la même `BeamStart` et la même `BeamEnd`** : deux origines différentes recréeraient la duplication. L'ordre compte : décrémenter avant de dessiner ferait démarrer le faisceau déjà entamé (`12_PIEGES §2.3b`). |
| `OnShotFired(Hit, bHit)` | Dispatcher | → `BP_PlayerCharacter` → `WBP_HUD`, `BPC_StyleMeter` |
| `OnHitConfirmed(Target, bHeadshot, bKilled)` | Dispatcher | → hitmarker, `BPC_StyleMeter`, `BPC_HitStop` |
| `OnOverheatStarted` / `OnOverheatEnded` | Dispatchers | Relayés depuis `BPC_Heat` |

> **`SPEC_COMBAT` fait foi sur les dispatchers de l'arme.** Les noms et signatures retenus sont
> `OnShotFired(Hit, bHit)` et `OnHitConfirmed(Target, bHeadshot, bKilled)` : toute autre doc qui les
> nomme autrement s'aligne sur cette section.

**Répartition** — `BP_PlayerCharacter` possède l'arme et relaie inputs + dispatchers, **aucune** logique de
trace / dégâts / chaleur. `BP_LaserWeapon` : trace, dégâts, FX, recoil, cooldown. `BPC_Heat` : jauge, états,
`MPC_Global`. `BPC_Melee` est sur le **character**, pas sur l'arme (le melee reste dispo en overheat).

## 3. Le tir — séquence complète
`IA_Fire` (Digital Bool, trigger **`Pressed`** seul, `IMC_Gameplay`) → `BP_PlayerCharacter.HandleFireInput()`
→ `BP_LaserWeapon.TryFire()`. Maintenir le bouton ne fait rien : relâcher et re-cliquer.

### 3.1 `TryFire()`
```
TryFire():
    if (BPC_Heat.CurrentState == Overheated): PlayDenyFeedback(); return   // gate 1, §4
    if (!bCanFire): return                                                 // gate 2, silencieux
    if (OwnerCharacter.BPC_Health.bIsDead): return                         // gate 3
    bCanFire = false
    SetTimerByEvent(EndFireCooldown, WeaponData.FireCooldown)   // 07_TUNING §11 Laser_FireCooldown
    ShotResult = ResolveShot()                                  // §3.2-3.4 + §11
    if (ShotResult.bBlockingHit):
        ProcessHit(ShotResult.Hit, IsHeadshot(ShotResult.Hit) AND NOT ShotResult.bAssisted)  // §3.5 + §11
    PlayFireFX(ShotResult.ImpactPoint, ShotResult.Hit)          // toujours, même à vide
    ApplyRecoil()                                               // §3.6
    BPC_Heat.AddHeat(WeaponData.HeatPerShot)                    // 07_TUNING §11 — TOUJOURS en dernier
    OnShotFired.Broadcast(ShotResult.Hit, ShotResult.bBlockingHit)
```
> **Ordre imposé** : la chaleur s'ajoute **après** la résolution, sinon le tir qui déclenche l'overheat serait
> annulé par sa propre chaleur.

### 3.2 Origine du trace — la règle
| | Origine | Direction | Longueur |
|---|---|---|---|
| **Gameplay (autoritaire)** | `Camera.GetWorldLocation()` | `OwnerController.GetControlRotation().ForwardVector` | `WeaponData.Range` (`07_TUNING §11`) |
| **Beam VFX (cosmétique)** | `Muzzle.GetWorldLocation()` | vers `ImpactPoint` | — |

**Le hit est décidé par la caméra, le VFX part du canon.** `NS_LaserBeam` reçoit `BeamStart = Muzzle` et
`BeamEnd = ImpactPoint` : le rayon part de l'arme et finit exactement sous le réticule ; divergence
imperceptible au-delà de ~200 uu. **Le muzzle n'est jamais l'origine du trace de gameplay** — à 3000 uu/s le
décalage caméra→canon fait rater des cibles centrées et toucher des murs invisibles.

**Couleur** : le faisceau, le muzzle flash, les impacts du joueur et le hitmarker sont en
**`OD_Magenta_Player`** — la couleur du joueur et de tout ce qu'il projette
(`Docs/ArtDirection/PALETTE.md §3`, qui fait autorité ; `11_ARBITRAGES D3`).
Les tokens `OD_*` sont les seuls valides ; `OD_Magenta_Primary`, `OD_Pink_Glow`, `OD_Cyan_Accent` et
`OD_Red_Enemy` **n'existent plus**.

> **Un faisceau lumineux ne se voit pas sur un monde blanc.** Le rendu est éclairé, en plein jour
> (`11_ARBITRAGES D2`) : un beam purement **additif** posé sur une façade `OD_White_Structure` sature
> vers le blanc et **disparaît**. Construction imposée :
> **cœur saturé et foncé** en `OD_Magenta_Player` (opaque ou faiblement additif, c'est lui l'objet) +
> **contour plus sombre** (`OD_Navy_Ink`) qui garantit le découpage sur n'importe quel fond +
> glow additif étroit **par-dessus**, jamais à la place. Même règle pour le muzzle flash et les impacts.
> Si le tir se lit mal en playtest, on **assombrit le cœur** ; on ne monte jamais l'intensité additive.

### 3.3 Trace & collision
```
LineTraceByChannel(
    Start = CameraLocation, End = CameraLocation + ControlForward * Range,
    TraceChannel = Weapon,            // canal custom à créer, 06_CONVENTIONS §7, réponse défaut = Block
    bTraceComplex = FALSE,            // non négociable
    bReturnPhysicalMaterial = TRUE,   // choix du VFX d'impact
    ActorsToIgnore = [OwnerCharacter, self])
```
| Composant / preset | Réponse au canal `Weapon` |
|---|---|
| `OD_Player` · `OD_EnemyProjectile` | Ignore |
| `OD_LevelGeo` · `OD_WallRideSurface` | **Block** |
| **Capsule** du Character ennemi, preset `OD_Enemy` | **Block** — c'est la hitbox **corps** |
| **`SphereCollision` `Head`** (socket de tête), canal `Weapon` | **Block** — c'est la hitbox **headshot** |
| `SkeletalMeshComponent` de `BP_EnemyBase` | **`NoCollision`** — il n'est jamais tracé |

- **Modèle de hitbox : Sphere Collision, pas de Physics Asset.** `SkeletalMeshComponent` en `NoCollision`,
  la **capsule** porte le corps, une **`SphereCollision` nommée `Head`** attachée au socket de tête porte le
  headshot (`SPEC_ENEMIES §2` détaille la hiérarchie complète, `WeakPointHitbox` du Tank compris).
  **Aucun `PHYS_Enemy_*` n'est produit**, et le per-bone tracing est interdit sur les ennemis : à 3000 uu/s
  de vitesse relative il est coûteux, imprécis, et dépendant de la topologie du mesh. Une sphère est gratuite,
  déterministe et se règle visuellement.
> **Écarts constatés à l'implémentation (J8) — cette note fait foi sur le code réel.**
> - Le canal `Weapon` est **`ECC_GameTraceChannel3`** et se pose sur le pin `TraceChannel` sous la
>   valeur **`TraceTypeQuery3`** (prouvé, cf. `12_PIEGES_OUTILLAGE 5.18`).
> - **`bReturnPhysicalMaterial` n'existe pas** sur le nœud Blueprint `Line Trace By Channel`
>   (`UKismetSystemLibrary::LineTraceSingle` ne l'expose pas). Le pin `PhysMat` du `Break Hit Result`
>   restera donc vide. Sans conséquence au J8 : il ne sert qu'au choix du VFX/SFX d'impact décor (J14).
>   Si le J14 en a besoin, la parade Blueprint est un `Line Trace By Profile`/`ForObjects`
>   ou la lecture du `PhysicalMaterial` du composant touché — **jamais** du C++ (R1).
> - `ActorsToIgnore` contient **`[OwnerCharacter]`** seulement : `bIgnoreSelf = true` couvre déjà
>   l'acteur arme, et un pin tableau ne se remplit pas en une passe (`12_PIEGES 2.22`).
> - Signature réelle : **`PlayFireFX(Hit : HitResult, bBlockingHit : bool)`** — le point d'impact est
>   relu du `Hit` (et `Hit.TraceEnd` sert de bout de ligne quand le tir part à vide).

- **`bTraceComplex = false`** : le complex trace est coûteux et ne sert à rien ici — la discrimination
  corps / tête vient du **composant touché**, pas de la géométrie.
- `bReturnPhysicalMaterial` ne sert qu'au choix du VFX/SFX d'impact sur le décor, jamais à la logique de hit.
- Trace unique, non-multi. Pas de pénétration, pas de ricochet, pas de spread (`Laser_Spread = 0`).

### 3.4 Trace de confirmation muzzle (`bUseMuzzleConfirmTrace`, défaut `false`)
Cas limite : joueur collé à un mur, la caméra voit par-dessus, le canon est *dans* le mur. Si activé, après un
hit valide : `LineTrace(Muzzle → Hit.ImpactPoint)` ; si ce trace touche de la géométrie **avant** la cible, le
tir devient un impact mural. Désactivé par défaut — 2 traces/tir pour un cas rare, et ça produit des « tirs
mangés » frustrants à haute vitesse. N'activer que si le playtest le remonte.

### 3.5 Traitement du hit → dégâts
```
ProcessHit(Hit, bHeadshot):
    if (!Hit.Actor implements BPI_Damageable):
        SpawnImpactFX(Hit); SpawnDecal(DEC_LaserScorch, Hit); return       // mur / prop
    Info = S_DamageInfo {
        Amount = bHeadshot ? WeaponData.BodyDamage * WeaponData.HeadshotMultiplier
                           : WeaponData.BodyDamage,                        // 07_TUNING §11
        Type   = bHeadshot ? LaserHeadshot : Laser,
        HitLocation = Hit.ImpactPoint, HitNormal = Hit.ImpactNormal,
        HitBone = Head | WeakPoint | Body,      // déduit de Hit.Component, JAMAIS de Hit.BoneName
        Instigator = OwnerCharacter, KnockbackImpulse = (0,0,0), SpeedPenaltyPercent = 0 }
    (bKilled, DamageApplied) = BPI_Damageable.ApplyDamage(Hit.Actor, Info)
    OnHitConfirmed.Broadcast(Hit.Actor, bHeadshot, bKilled)
```
> **Décision** : la source de vérité du headshot est **`Laser_HeadshotMultiplier`** appliqué sur
> `Laser_Damage_Body` (`07_TUNING §11`) ; la létalité garantie vient de `PDA_EnemyData.bHeadshotIsLethal` (§5).
> `Laser_Damage_Head` devient une valeur **dérivée**.

### 3.6 Recoil
**Le recoil ne déplace jamais l'aim.** `BP_PlayerCameraManager` expose `RecoilPitchOffset` ; à chaque tir
`RecoilPitchOffset += WeaponData.RecoilPitch` (`07_TUNING §11`), retour vers 0 par `FInterp To` dans
`BlueprintUpdateCamera`, qui sort `Rotation = ControlRotation + (RecoilPitchOffset, 0, 0)`. Le trace utilise
`ControlRotation` **brut** → réticule exact, seule la caméra bouge. *Justification* : à 3000 uu/s, un recoil qui
dérive l'aim force à compenser donc à ralentir. Le kick est du juice, pas une taxe. **Jamais
`AddControllerPitchInput`** (§13.13).

## 4. Système de Heat — `BPC_Heat`
Attaché à `BP_LaserWeapon`, lit le `WeaponData` de son owner. Valeurs : `07_TUNING §11 > Heat`.
États `E_HeatState` (`08_DATA_SCHEMAS §1`) :
```
                  AddHeat()                   Heat >= Heat_WarningThreshold
   ┌──────────┐ ────────────▶ ┌──────────┐ ────────────────────────────────▶ ┌──────────┐
   │ Cooling  │               │ Building │                                   │ Warning  │
   │ decay ON │ ◀──────────── │          │ ◀──────────────────────────────── │          │
   └──────────┘  Heat < Warn  └──────────┘            Heat < Warn            └──────────┘
        │         & decay actif     ▲                                             │ AddHeat()
        │ Heat == 0 → prêt          │ OverheatDuration ÉCOULÉ                     │ → Heat >= Heat_Max
        ▼  (pas un état)            │ ET Heat <= Heat_OverheatExitThreshold        ▼
   ┌────────────┐         ┌─────────┴───────────────────────────────────────────────┐
   │  Heat = 0  │         │                      Overheated                          │
   └────────────┘         │ TIR BLOQUÉ · decay × Heat_OverheatDecayMultiplier        │
                          │ verrou dur minimum : Heat_OverheatDuration               │
                          └─────────────────────────────────────────────────────────┘
```
| Règle | Détail |
|---|---|
| Ajout | `AddHeat(Amount)` → `Clamp(CurrentHeat + Amount, 0, Heat_Max)`. Ré-arme le délai de décroissance. |
| Délai | `Heat_DecayDelay` après **le dernier tir**. Tout tir le ré-arme. |
| Décroissance | `Heat_DecayRate` /s via un timer à fréquence fixe (`Heat_TickInterval`, `07_TUNING §11`). **Jamais en Tick.** |
| Décroissance en overheat | `× Heat_OverheatDecayMultiplier`, et **sans attendre** `Heat_DecayDelay`. |
| Entrée en overheat | `CurrentHeat >= Heat_Max` après un tir. Le tir déclencheur **part quand même**. |
| Sortie | Conditions **cumulatives** : `Heat_OverheatDuration` écoulé **ET** `CurrentHeat <= Heat_OverheatExitThreshold`. |
| Bloqué pendant l'overheat | **Uniquement `TryFire()`.** Melee, dash, slide, wall ride, saut : jamais bloqués. |
| Upgrades | `HeatCapacity` / `HeatRecovery` (`E_UpgradeStat`) lus via `BPC_PlayerStats` au `BeginPlay`. Jamais en dur. |

**Rythme visé** : `Heat_Max / Heat_PerShot` ≈ **9 tirs** consécutifs, puis pause. Un joueur qui enchaîne 9 tirs
sans bouger a déjà perdu son momentum : la chaleur *sanctionne l'immobilité par le tempo*. Si l'overheat
n'arrive jamais en playtest, **baisser `Heat_Max`** — ne pas monter `Heat_PerShot`.

**API** : `CurrentHeat` · `CurrentState` · `GetHeatRatio()` (pure) · `IsOverheated()` (pure). Dispatchers
`OnHeatChanged(Ratio, State)` → `WBP_HeatBar` (bind, pas de Tick), `OnOverheatStarted` / `OnOverheatEnded`,
`OnWarningEntered`. `BPC_Heat` écrit `HeatRatio` et `OverheatActive` dans `MPC_Global`
(`08_DATA_SCHEMAS §6`) : les matériaux de l'arme chauffent **sans une ligne de BP supplémentaire**.

| Feedback | `Building` | `Warning` | `Overheated` |
|---|---|---|---|
| `WBP_HeatBar` | remplissage froid | **pulse** + couleur chaude | pleine, clignote, icône verrou |
| Audio | `SC_Laser_Fire` | `SC_Heat_Warning` (loop montant) | `SC_Overheat_Start`, puis `SC_Overheat_Ready` à la sortie |
| VFX arme | — | émissif piloté par `MPC_Global.HeatRatio` | `NS_OverheatVent` (vapeur au muzzle) en boucle |
| Anim | idle | idle | **l'arme pend** : `ABP_PlayerArms` → `A_Laser_Overheated`, canon vers le bas. Retour instantané à la sortie. |
| Clic bloqué | — | — | `SC_Laser_Deny` (clic sec), **pas de shake**, crosshair barré en `OD_Amber_Heat` bref |

## 5. Headshots
### 5.1 Détection — `SphereCollision` dédiée, jamais de bone name
```
IsHeadshot(Hit):
    if (!IsValid(Hit.Component)) return false
    return Hit.Component == Hit.Actor.HeadHitbox            // comparaison de COMPOSANT
```
`BP_EnemyBase.HeadHitbox` : `SphereCollision` nommée **`Head`**, attachée au socket de tête du
`SkeletalMeshComponent` (lui-même en `NoCollision`), canal `Weapon` en `Block`. **Aucun `PHYS_Enemy_*`,
aucun test sur `Hit.BoneName`** : `Hit.BoneName` n'est ni fiable ni nécessaire dans ce modèle.

La sphère doit être **généreuse** — elle englobe le crâne et déborde un peu : un headshot raté de 3 cm à
3000 uu/s est vécu comme un bug. Elle se règle visuellement dans le viewport, indépendamment du mesh, en
quelques secondes (`SPEC_ENEMIES §12.11`). Corollaire : comme la hitbox n'épouse plus la silhouette animée,
le tick de pose n'est plus critique pour la validité du hit — `Only Tick Pose When Rendered` + URO restent
**activés** (§13.3).

> ### ⚠️ Écart d'implémentation assumé — J8sept. Cette note fait foi sur le code réel.
>
> **Le test réel est `Hit.Component.ComponentHasTag("Head")`, pas `Hit.Component == Hit.Actor.HeadHitbox`.**
>
> ```
> IsHeadshot(Hit):
>     return Hit.Component.ComponentHasTag("Head")     // 4 nœuds, aucun cast
> ```
>
> **Pourquoi.** La comparaison de composant suppose de connaître la classe de la cible pour lire
> `HeadHitbox` — donc un `Cast<BP_EnemyBase>` **dans l'arme**. Or (a) `BP_EnemyBase` n'existe pas
> avant le J12, (b) l'arme ne doit pas connaître le type de ce qu'elle touche (`05_ARCHITECTURE`),
> (c) le Tank aura des `WeakPointHitbox` qui ne sont pas des têtes et le boss d'autres points
> faibles encore : un tag est extensible, une comparaison de composant nommé ne l'est pas.
>
> **Ce que l'écart ne change pas** : l'interdit réel de cette section est **`Hit.BoneName`**, et il
> tient toujours. La discrimination vient du **composant touché**, comme prévu — on l'identifie
> simplement par son **tag** au lieu de son nom de variable.
>
> **Contrat de nommage** (les deux sont obligatoires sur toute cible) :
> composant nommé **`HeadHitbox`** · **Component Tag = `Head`**.
> Un composant sans le tag est un composant corps, sans erreur ni warning — c'est le mode d'échec
> à surveiller au J12.
>
> ⚠️ **Le rayon de la sphère doit dépasser la demi-DIAGONALE du volume du corps, pas sa demi-largeur.**
> Mesuré au J8sept sur `BP_TargetDummy` (corps 60 × 60) : avec un rayon de 40 uu la tête dépasse de
> 10 uu de face mais **rentre à l'intérieur du corps dès 45° d'incidence** (demi-diagonale = 42.4 uu),
> et le headshot devient impossible en approche oblique — c'est-à-dire précisément en pleine course.
> Rayon retenu : **50 uu** (`07_TUNING §11`). Règle générale : `R_tête > demi_diagonale_corps + marge`.

### 5.2 Dégâts
`Damage = Laser_Damage_Body × Laser_HeadshotMultiplier` (`07_TUNING §11`), **puis** : si
`PDA_EnemyData.bHeadshotIsLethal` → mort garantie quel que soit le calcul.

| Ennemi | `bHeadshotIsLethal` | Effet |
|---|---|---|
| Grunt / Shooter | `true` | **One-shot**, toujours |
| Tank | `false` | Dégâts × `HeadshotMultiplier` seulement (`07_TUNING §13`). Le Tank se tue au wall slam. |
| Boss | `false` | idem via `PDA_BossData` |

`BPC_Health` applique `bHeadshotIsLethal` **avant** le calcul de PV (`CurrentHealth = 0` direct) : aucune
upgrade de PV ne peut casser la règle.

### 5.3 Feedback spécifique (tout obligatoire)
| Canal | Body shot | **Headshot** |
|---|---|---|
| Hitmarker | `WBP_Hitmarker` **`OD_Navy_Ink` bordé de blanc**, fin | **`OD_Magenta_Player`, épais, tourné 45°**, scale-punch |
| SFX | `SC_Laser_Impact_Flesh` | `SC_Headshot` — **son distinct**, plus aigu et plus court, mixé au-dessus, prioritaire dans `SCC_Impacts` |
| VFX | `NS_LaserImpact` | `NS_LaserImpact_Head` : gerbe plus large + **flash `OD_Magenta_Player` saturé** 1 frame |

> **Pourquoi ces couleurs ont changé.** Un hitmarker **blanc** sur une ville blanche est invisible : le
> body shot passe en `OD_Navy_Ink` bordé de blanc, exactement la règle des éléments de HUD sans panneau
> (`PALETTE.md §7`). Le hitmarker de headshot passe du rouge au **magenta joueur** : en v2 le rouge est
> pris par la traversée et le danger (`11_ARBITRAGES D3`), et cette confirmation-là émane du joueur.
> Le **flash blanc** de `NS_LaserImpact_Head` devient un flash **saturé** pour la même raison — un flash
> blanc sur fond blanc en plein soleil ne produit aucune lecture. Le crosshair, lui, reste
> `OD_Navy_Ink` bordé de blanc et **jamais magenta** (`PALETTE.md §7`) : il ne doit pas se confondre
> avec le faisceau.
| Caméra | `CS_LaserFire` × `Shake_LaserFire` | `CS_Headshot` × `Shake_Headshot` (`07_TUNING §16`) |
| Temps | — | **hit-stop** `HitStop_Headshot` (§5.4) |
| Style | `Kill` | `Headshot` (`E_StyleEvent`), bonus `07_TUNING §14` |

### 5.4 Hit-stop — `BPC_HitStop`, **sur `PC_Overdrive`**

**Un seul propriétaire, le PlayerController.** Il survit au respawn du pawn, contrairement au
`BP_PlayerCharacter`. `BPFL_Overdrive::DoHitStop` **n'existe pas** : une Function Library ne peut pas
porter d'état.
```
BPC_HitStop  (sur PC_Overdrive)
  RequestHitStop(RealDuration: float, Dilation: float, Priority: int) → bool bAccepted

RequestHitStop(RealDuration, Dilation, Priority):
    if (bHitStopActive && Priority <= ActivePriority) return false        // strictement supérieure, sinon ignoré
    if (GameTime - LastHitStopTime < HitStop_MinInterval) return false    // 07_TUNING §16
    bHitStopActive = true ; ActivePriority = Priority
    SetGlobalTimeDilation(Dilation)                                       // 07_TUNING §16 HitStop_TimeDilation
    // ⚠ les timers du monde sont comptés en temps MONDE, or le monde tourne au ralenti.
    //   La durée est en TEMPS RÉEL : armer la sortie sur un timer non affecté par la dilatation.
    ArmRealTimeTimer(EndHitStop, RealDuration)
    return true
EndHitStop():
    SetGlobalTimeDilation(1.0); bHitStopActive = false; ActivePriority = 0; LastHitStopTime = GameTime
```
| Politique | Règle |
|---|---|
| Empilement | Si un hit-stop est actif, une requête n'est acceptée **que si sa `Priority` est strictement supérieure**. Sinon elle est ignorée et `bAccepted = false`. |
| Cadence | Refusée si moins de `HitStop_MinInterval` (`07_TUNING §16`) s'est écoulé depuis le dernier. |
| Durée | En **temps réel**. Le timer de sortie utilise un timer non affecté par la dilatation — jamais un `Set Timer by Event` du monde ralenti. |
| Exclus du ralenti | L'**audio** (`Sound Class` dont le pitch n'est pas lié au time dilation) et l'**UI**. |
| Priorités | `Headshot = 10` · `WallSlam = 20` · `Boss phase = 30`. |

**Précautions, à respecter à la lettre :** (1) **Un seul endroit du projet** appelle `Set Global Time
Dilation` : `BPC_HitStop` ; un hit-stop imbriqué qui restaure `1.0` en plein hit-stop d'un autre laisse le
jeu figé — c'est précisément ce que la règle de priorité empêche. (2) `EndHitStop` doit **toujours**
s'exécuter : le rappeler dans `EndPlay`, à la pause, et au `BeginPlay` du level (anti-freeze après
rechargement). (3) Réservé au **headshot**, au **melee/wall slam** et aux **transitions de phase de boss** —
jamais sur un body shot, à ~5 tirs/s c'est un diaporama. (4) `Min Global Time Dilation` (Project Settings >
General) doit être ≤ `HitStop_TimeDilation`, sinon la valeur est silencieusement écrêtée. (5) Jouer les SFX
**avant** l'appel : les Sound Cues à modulation temporelle voient leur attaque étirée.

## 6. `BPC_Melee`
Composant du **`BP_PlayerCharacter`** (`Weapons/Melee/`), pas de l'arme : le melee reste disponible en overheat.

**Décision : `SphereTraceMultiByChannel`, pas d'overlap.** Un volume d'overlap piloté par notify exige un
composant permanent, produit des faux négatifs quand le joueur traverse un ennemi à 3000 uu/s (overlap manqué
entre deux frames), et ne donne pas de point d'impact exploitable. Le sphere trace est ponctuel, déterministe,
et renvoie un `HitResult` par cible.
```
DoMeleeTrace():
    Start = Camera.GetWorldLocation();  End = Start + ControlForward * Melee_Range      // 07_TUNING §12
    Hits = SphereTraceMultiByChannel(Start, End, Melee_Radius, Weapon, bTraceComplex=false, Ignore=[Self])
    HitActorsThisSwing.Empty()
    foreach Hit in Hits:
        if (HitActorsThisSwing.Contains(Hit.Actor)) continue      // dédoublonnage OBLIGATOIRE (§13.5)
        HitActorsThisSwing.Add(Hit.Actor); ApplyMeleeHit(Hit)
```
| Élément | Règle |
|---|---|
| Input | `IA_Melee`, trigger `Pressed`, gate `bCanMelee` |
| Windup | `Melee_WindupTime` (`07_TUNING §12`), quasi nul |
| Déclenchement | `AN_MeleeHit` posé sur `AM_Melee_Punch` à `Melee_WindupTime` |
| **Filet de sécurité** | `BPC_Melee` arme **en parallèle** un `Set Timer by Event(Melee_WindupTime)` ; le premier des deux résout le coup (`bSwingResolved` empêche le double). **Le gameplay ne dépend jamais d'un asset d'anim.** |
| Fenêtre | **Un seul trace ponctuel.** Pas d'`ANS_MeleeWindow`, pas de trace continu : `Melee_Range` couvre déjà largement. |
| Cooldown | `Melee_Cooldown` (`07_TUNING §12`), timer → `bCanMelee = true`. Indépendant du cooldown laser. |
| Montage | `AM_Melee_Punch`, slot Upper Body sur `ABP_PlayerArms`. **Ne bloque jamais le mouvement.** Interruptible. |
| Multi-cibles | Tous les ennemis du trace prennent **100 %** de `Melee_Damage` et **100 %** du knockback : pas de dégressivité, frapper un groupe est une récompense de positionnement. Hit-stop déclenché **une seule fois** par swing. |

## 7. Knockback & Wall Slam — la mécanique signature
### 7.1 Décision : `Launch Character`, pas `Simulate Physics`
| Option | Verdict |
|---|---|
| `Simulate Physics` + `Add Impulse` sur le mesh | **REJETÉ.** Détache le CMC, casse StateTree et navigation, impose un relevé coûteux, rend le `HitResult` mural imprévisible, et le mesh simulé perd ses hitboxes de headshot. **Aucune simulation physique n'existe dans le projet, à aucun moment.** |
| `LaunchCharacter(V, bXYOverride=true, bZOverride=true)` | **RETENU.** Le CMC gère la collision par sweep, `Event Hit` remonte la normale du mur, la vitesse reste lisible, l'ennemi reste un Character. |
| `Add Impulse` sur la capsule | Sans effet : la capsule d'un Character n'est pas simulée. |

**À la mort — y compris pour un ennemi tué en plein vol — l'ennemi joue un `dissolve`**, jamais autre chose :
`SPEC_ENEMIES §8` fait foi (`DissolveAmount` sur `M_Toon_Enemy`, durée `Death_DissolveDuration`, puis
`DestroyActor`).

### 7.2 Application (joueur) puis réception (ennemi)
```
ApplyMeleeHit(Hit):                                        // BPC_Melee
    Dir = Camera.ForwardVector.Normalize()                 // la CAMÉRA, pas Player→Enemy
    Impulse = Dir * Melee_Knockback + Up * Melee_KnockbackUp                 // 07_TUNING §12
    Info = S_DamageInfo { Amount = Melee_Damage, Type = Melee, HitLocation/Normal/Bone = Hit.*,
                          Instigator = Player, KnockbackImpulse = Impulse, SpeedPenaltyPercent = 0 }
    BPI_Damageable.ApplyDamage(Hit.Actor, Info)                              // dégâts d'abord
    BPI_Damageable.ApplyKnockback(Hit.Actor, Impulse, Player)                // PUIS propulsion — c'est
                                                                             // l'appelant qui enchaîne (§8)
    PC_Overdrive.BPC_HitStop.RequestHitStop(Melee_HitStop, HitStop_TimeDilation, 20)
                                        // priorité « WallSlam » du barème §5.4 · 07_TUNING §12 / §16
                                        // → bAccepted ignoré ici : un refus n'annule jamais le coup

ReceiveKnockback(Impulse, Instigator):                     // BPC_KnockbackReceiver, sur BP_EnemyBase
    Final = Impulse * (1 - PDA_EnemyData.KnockbackResistance)                // 0–1, 08_DATA_SCHEMAS §3
    if (Final.Size() < WallSlam_MinImpactSpeed): PlayStagger(); return       // 07_TUNING §12 — cf. §7.4
    AIController.BrainComponent.StopLogic("Knockback"); SetMovementMode(Falling)
    LaunchCharacter(Final, XYOverride=true, ZOverride=true)
    bIsAirborneFromKnockback = true; bSlamConsumed = false
    EnableVelocityTracking()                                                 // Tick local, §13.6
    SetTimerByEvent(EndKnockbackWindow, Knockback_MaxFlightTime)             // 07_TUNING §12, anti-blocage
```
La direction vient de **la caméra** : le joueur vise le mur, pas l'ennemi. C'est ce qui rend la mécanique
*pilotable*. Variables du receiver : `bIsAirborneFromKnockback` · `LastFrameVelocity` · `bSlamConsumed`.

### 7.3 Impact mural & dégâts
Sur `Event Hit` de `BP_EnemyBase` (`Simulation Generates Hit Events` = **true** sur la capsule) :
```
OnHit(Hit):
    if (!bIsAirborneFromKnockback || bSlamConsumed) return
    ImpactSpeed = |LastFrameVelocity|                              // AVANT résolution, §13.6
    bIsWall = Abs(Hit.ImpactNormal.Z) < WallSlam_MaxNormalZ        // 07_TUNING §13 — sinon c'est un sol
                                                                   // règle alignée sur SPEC_ENEMIES §9
    if (!bIsWall || ImpactSpeed < WallSlam_MinImpactSpeed): OnLandedWithoutSlam(); return
    if (!PDA_EnemyData.bCanBeWallSlammed): PlayBounce(); return
    bSlamConsumed = true
    SlamDamage = Clamp(ImpactSpeed * WallSlam_DamagePerSpeed, 0, WallSlam_Damage)     // 07_TUNING §12
    ApplyDamage(self, S_DamageInfo{ Amount=SlamDamage, Type=WallSlam, Instigator=Player, ... })
```
> **Décision** : formule proportionnelle plafonnée — elle réconcilie les deux clés de `07_TUNING §12`
> (`WallSlam_Damage` = **plafond**, `WallSlam_DamagePerSpeed` = **pente**) et rend le slam *dosé* : effleurer un
> mur ne tue pas, écraser à pleine vitesse tue. Dès que `CF_WallSlamDamageBySpeed` (`08_DATA_SCHEMAS §5`)
> existe, la courbe **remplace** cette formule linéaire.
> **`Instigator` = le joueur**, jamais le mur : indispensable pour créditer le kill au score et au style
> (`E_StyleEvent.WallSlamKill`).

### 7.4 Fenêtre de vol, atterrissage sans mur, résistants
| Cas | Comportement |
|---|---|
| Fenêtre de vulnérabilité | De `LaunchCharacter` au premier de : impact mural · `Event Landed` · `Knockback_MaxFlightTime`. Pendant ce temps l'ennemi ne tire pas, ne se déplace pas, et est **relançable** par un second melee (le vol se recalcule, `bSlamConsumed` repasse à `false`). |
| Atterrissage sans mur | `Event Landed` → **aucun** dégât de chute, `EndKnockbackWindow()`, relevé après `Knockback_RecoverTime` (`07_TUNING §12`) avec `A_Enemy_GetUp`, puis `ResumeLogic`. Le slam est raté : c'est la punition d'un mauvais angle. |
| `KnockbackResistance` élevée (**Tank**) | L'impulsion finale passe sous `WallSlam_MinImpactSpeed` → **pas de vol**, juste `PlayStagger()` (`A_Enemy_Stagger`, IA suspendue le temps du montage). Le Tank encaisse les dégâts melee normaux. |
| `bCanBeWallSlammed == false` | Vol possible si le seuil est franchi, mais l'impact mural ne fait **aucun** dégât de slam : `PlayBounce()` + SFX sourd. Réservé aux boss / cas scénarisés. |
| Ennemi mort en vol | Le receiver se désarme et l'ennemi joue son **dissolve en l'air** (`SPEC_ENEMIES §8`) : il ne tombe pas, il ne se simule pas, il se dissout sur place pendant `Death_DissolveDuration`. Pas de slam post-mortem (double crédit de score interdit). |

## 8. Interface de dégâts
### `BPI_Damageable` (`Content/OVERDRIVE/Core/`)
**4 fonctions, signature définitive** — elle vaut pour tout le projet, `05_ARCHITECTURE §2` compris.

| Fonction | Entrées | Sorties | Note |
|---|---|---|---|
| `ApplyDamage` | `DamageInfo : S_DamageInfo` | `bKilled : Bool`, `DamageApplied : Float` | `S_DamageInfo` (`08_DATA_SCHEMAS §2`) transporte `HitLocation`, `HitNormal`, `HitBone`, `KnockbackImpulse`, `SpeedPenaltyPercent` |
| `ApplyKnockback` | `Impulse : Vector`, `Instigator : Actor` | — | pure action |
| `IsAlive` | — | `bAlive : Bool` | |
| `GetHealthRatio` | — | `Ratio : Float` | `[pure]` |

> **Écarts constatés à l'implémentation (J8sexies) — cette note fait foi sur l'asset réel.**
> - `GetHealthRatio` est annotée `[pure]` ci-dessus mais l'asset `BPI_Damageable` la déclare
>   **impure** : son graphe a un pin `Exec`. Sans conséquence fonctionnelle (elle ne fait que lire) ;
>   le flag `Pure` n'est pas exposé par l'outillage (`12_PIEGES §5.3`), donc **si on le veut, c'est
>   Louis qui coche la case sur l'interface**. À trancher au J9 avec `BPC_Health`.
> - `ApplyKnockback` n'ayant aucune sortie, l'éditeur l'expose en **event** et non en fonction :
>   elle n'apparaît pas dans `list_graphs`. Normal, rien à corriger. Implémentée au **J11**.
> - Sur `BP_TargetDummy` (sandbox), la garde `bIsDead` du pseudo-code ci-dessous est transposée en
>   **`if (CurrentHealth <= 0) return (false, 0)`** en première ligne : le dummy n'a pas de
>   `BPC_Health` et se détruit immédiatement. Même sémantique, même position, §13 piège 9 couvert.

> **`ApplyKnockback` est appelée APRÈS `ApplyDamage`, par l'appelant** — jamais depuis `ApplyDamage`.
> Deux raisons : le knockback doit s'appliquer **même si la cible est morte** (un corps projeté reste
> satisfaisant, et il se dissout en vol, §7.4), et **c'est l'appelant qui sait** s'il veut projeter ou non
> (le laser ne projette pas, le melee oui).
```
BP_LaserWeapon / BPC_Melee / BPC_KnockbackReceiver / BP_EnemyProjectile
        │ ApplyDamage(S_DamageInfo)     puis, si l'appelant le veut : ApplyKnockback(Impulse, Instigator)
        ▼
BP_EnemyBase (implémente BPI_Damageable) ──délègue──▶ BPC_Health.TakeDamage(Info)
        ├─ si bIsDead → return (false, 0)                    // anti double-kill
        ├─ si Type == LaserHeadshot && bHeadshotIsLethal → Health = 0
        ├─ sinon Health = Clamp(Health - Info.Amount, 0, MaxHealth)
        ├─ OnHealthChanged.Broadcast(Ratio)  ├─ SpawnHitFX(Info)      // §10
        └─ si Health <= 0 → bIsDead = true ; OnDeath.Broadcast(Info)

BP_EnemyBase.OnDeath(Info)
        ├─ BPI_ScoreEvent.NotifyScoreEvent(GS_Overdrive, EventType, ScoreBase, Info.Instigator)
        │     EventType déduit de Info.Type : LaserHeadshot→Headshot · WallSlam→WallSlamKill ·
        │     Melee→MeleeKill · sinon Kill   (surclassé SlideKill/AirKill selon l'état du joueur, SPEC_SCORE_RANK)
        ├─ GS_Overdrive.RegisterKill()          ├─ AIController détaché, capsule → NoCollision
        └─ Timeline DissolveAmount 0→1 sur M_Toon_Enemy pendant Death_DissolveDuration → DestroyActor()
                                                        // 07_TUNING §13 — SPEC_ENEMIES §8 fait foi.
                                                        // Aucune simulation physique. Aucun délai de cadavre.
```
Le score n'est **jamais** calculé par l'ennemi : il émet l'événement, `BPC_ScoreManager` décide.
`BP_PlayerCharacter` ne contient aucune logique de score (`05_ARCHITECTURE §3`) et implémente **aussi**
`BPI_Damageable` : même interface pour tout le monde.

## 9. Dégâts subis par le joueur
```
BP_PlayerCharacter.ApplyDamage(Info):
    if (bIsInGracePeriod) return (false, 0)                                  // §9.2
    BPC_Health.TakeDamage(Info)
    BPC_MovementState.ApplySpeedPenaltyPercent(Info.SpeedPenaltyPercent, Reason)   // 07_TUNING §10
    BPC_StyleMeter.NotifyStyleEvent(TookDamage)                              // 07_TUNING §14
    StartGracePeriod(); PlayDamageFeedback(Info)                             // §9.3
```
**9.1 Perte de vitesse — la vraie punition.** `Info.SpeedPenaltyPercent` est rempli par la **source**, depuis
`PDA_EnemyData.PlayerSpeedPenaltyPercent` (`07_TUNING §13`) ou la table des collisions (`07_TUNING §10`).

Signature retenue : **`ApplySpeedPenaltyPercent(Percent, Reason)`** sur `BPC_MovementState`. Elle multiplie
la **vitesse horizontale** courante, ne touche jamais à Z, et ne descend jamais sous `Speed_Walk`
(`07_TUNING §3`). Elle émet le dispatcher **`OnSpeedPenaltyApplied(OldSpeed, NewSpeed, Percent, Reason)`** —
c'est lui qui alimente le flash rouge du `WBP_SpeedMeter` et le debug ; personne ne recalcule la perte de
son côté.

**9.2 I-frames : NON. Grace period : OUI.** Pas d'i-frames sur le dash — `Dash_IFrames = 0` (`07_TUNING §8`) :
le dash sert à *bouger*, l'invincibilité en ferait la réponse universelle et tuerait le positionnement. Grace
period en revanche obligatoire : après tout dégât, `SpeedLoss_RecoveryGrace` (`07_TUNING §10`) pendant lequel
(a) aucune source ne peut infliger de dégât, (b) la décroissance de momentum est suspendue. *Justification* :
sans elle, deux Shooters alignés enchaînent deux pénalités en 0.2 s et la run est morte. La grace period
protège le **momentum**, pas les PV.

**9.3 Feedback directionnel.** `WBP_DamageDirection` (sous-widget de `WBP_HUD`) : arc rouge positionné par
`atan2` entre `Info.Instigator.Location - Player.Location` et le forward caméra, fade sur
`DamageIndicator_FadeTime` (`07_TUNING §16`) · vignette rouge post-process d'intensité `1 - GetHealthRatio()` ·
`CS_TakeDamage` × `Shake_TakeDamage` (`07_TUNING §16`) orienté vers la source · `SC_Player_Hurt` + low-pass
court sur `SMX_Default`. **Le HUD affiche la punition sur le compteur de vitesse** : `WBP_SpeedMeter` flashe
rouge et le chiffre décrémente visiblement. Le joueur doit lire la perte de vitesse, pas la perte de PV.

**9.4 Mort du joueur — le système de vies.** `BPC_Health` détecte la mort et **s'arrête là** : il ne
connaît ni les vies, ni les checkpoints, ni l'état de la run. Son seul devoir est de diffuser `OnDeath`
et d'appeler le propriétaire de la run.

```
BPC_Health.OnDeath (joueur)
    GI_Overdrive.ConsumeLife()          // S_RunState.LivesRemaining -= 1   (Run_MaxLives, 07_TUNING §18)
    SI LivesRemaining > 0  → respawn au dernier checkpoint du niveau courant, upgrades CONSERVÉS
    SINON                  → E_GameState.RunFailed → WBP_RunFailed → menu
```

> **`05_ARCHITECTURE §4` fait autorité sur le flux complet** (pénalité de score, reset du style, chrono
> qui continue, fade, `WBP_RunFailed`) et sur le **tableau de portée des données**. Il n'est pas dupliqué
> ici : `SPEC_COMBAT` ne décrit que le point d'entrée. Règle : `11_ARBITRAGES D1`.

Trois conséquences pour cette spec, et rien de plus :
- **`BPC_Health` ne branche pas lui-même.** Il ne teste jamais `LivesRemaining` : c'est `GI_Overdrive`
  qui décide, parce que la vie est une donnée de **run**, pas de pawn (`05_ARCHITECTURE §4`).
- **La mort ne coûte aucune upgrade** — elles vivent dans `GI_Overdrive` et survivent au respawn
  (`SPEC_LOOT_UPGRADES §8`). Au respawn, `BPC_PlayerStats` **recalcule** ses valeurs effectives à partir
  des `ActiveUpgrades` : aucun bonus n'est perdu, aucun n'est ré-empilé.
- **`BPC_HitStop` doit être remis à `1.0` sur le chemin de mort** : mourir pendant un hit-stop de headshot
  laisserait le jeu figé pendant le fade (§5.4, précaution 2). `EndHitStop()` est appelé depuis `OnDeath`
  au même titre que depuis `EndPlay`.

Le joueur doit **savoir immédiatement combien il lui reste** : le décompte du compteur de vies
(`WBP_LivesCounter`, `11_ARBITRAGES D31`) fait partie du feedback de mort, pas du HUD passif.
Sa mise en forme appartient à `SPEC_UI_HUD`.

## 10. Feedback obligatoire par action

> **Les catalogues font foi, pas cette section.** Les **sons** sont nommés et spécifiés dans
> **`SPEC_AUDIO §2`**, les **effets** dans **`SPEC_VFX §2`**. `SPEC_COMBAT` ne nomme plus aucun asset SFX ni
> VFX : il dit **ce qui doit être ressenti**, à charge des catalogues de fournir l'asset qui le produit.
> Chaque ligne ci-dessous est une **obligation de ressenti** — une action sans sa ligne n'est pas finie.

| Action | Ce qui doit être ressenti | Caméra | UI | Réaction ennemie |
|---|---|---|---|---|
| **Tir laser** | départ sec et instantané ; le rayon part visiblement du canon et meurt sous le réticule en ≤ 1 frame | `CS_LaserFire` × `Shake_LaserFire` + recoil caméra | crosshair kick ; `WBP_HeatBar` +1 cran | — |
| **Impact mur / décor** | « j'ai touché *ça*, pas un ennemi » : matière lisible, marque persistante, son variant selon le PhysMat | — | — | — |
| **Impact ennemi (body)** | confirmation immédiate et **lisible en périphérie** : flash sur la cible + son de chair/métal distinct du mur | — | hitmarker `OD_Navy_Ink` bordé de blanc | hit react additif léger, **jamais de stagger** (casserait le TTK) |
| **Headshot** | récompense **surclassante** : plus large, plus aigu, plus court, reconnaissable les yeux fermés | `CS_Headshot` × `Shake_Headshot` | hitmarker **`OD_Magenta_Player` 45°** + `+HEADSHOT` flottant | mort si `bHeadshotIsLethal` |
| **Kill** | « c'est mort » su **avant** la fin du dissolve : son de mort ≠ son de hit, flash de mort, dissolve qui nettoie la scène | — | `+SCORE` flottant, `WBP_StyleMeter` monte | dissolve `Death_DissolveDuration` puis `DestroyActor` (§8) |
| **Melee (swing)** | poids et allonge : un whoosh qui dit la portée avant même de toucher | léger kick de FOV | — | — |
| **Melee (hit)** | impact **lourd**, contact franc, la frappe « accroche » | `CS_MeleeHit` × `Shake_MeleeHit` + hit-stop `Melee_HitStop` | hitmarker épais | **projeté** (§7), IA suspendue |
| **Wall slam** | **le pic de satisfaction du jeu** : grave, lourd, plus fort que tout le reste, gerbe + onde + marque murale | `CS_MeleeHit` × `Shake_MeleeHit` + hit-stop | `+WALL SLAM` en gros, gros gain de style | mort quasi certaine (§7.3) |
| **Overheat** | frustration **lisible et courte** : l'arme vente, le clic répond « non » au lieu de se taire | **aucun shake** (ce n'est pas un impact) | `WBP_HeatBar` verrouillée + clignotante, crosshair barré | — |
| **Dégât subi** | la punition se lit sur **la vitesse**, pas sur les PV : voile rouge bref, étouffement du mix, direction de la source | `CS_TakeDamage` × `Shake_TakeDamage` orienté source | `WBP_DamageDirection` + `WBP_SpeedMeter` rouge | — |

**Mixage** : la règle de priorité et l'exemption du wall slam (il doit **toujours** passer, quoi qu'il se
joue par-dessus) sont spécifiées dans `SPEC_AUDIO §2`.
**Couleurs** : tout ce qui vient du **joueur** (faisceau, muzzle, impacts, hitmarker, dash, melee, traînée)
est **`OD_Magenta_Player`** ; tout ce qui vient d'un **ennemi** est **`OD_Amber_Enemy`** ; ce qui **va tuer**
(attaque imminente, kill volume) est **`OD_Red_Danger`**. `ArtDirection/PALETTE.md §3` fait autorité
(`11_ARBITRAGES D3`). **Le cyan n'existe plus**, et le rouge appartient désormais aux surfaces de traversée :
aucun VFX de combat ne doit être rouge vif hors télégraphe de danger.
Rappel de la contrainte v2 : **le fond est clair**, donc tout VFX de combat a besoin d'un **cœur foncé ou
très saturé** — un additif seul se délave et disparaît (§3.2).

## 11. Aide à la visée
| Option | Pour | Contre | Verdict |
|---|---|---|---|
| **A. Rien** (`Laser_TraceRadius = 0`) | Pureté, headshots 100 % mérités | À 3000 uu/s + strafe le taux de touche s'effondre → le joueur ralentit pour toucher → **contredit le pilier n°1** | Rejeté seul |
| **B. Magnétisme / snap** | Confort max | Le réticule bouge tout seul et se bat avec un 180° en air strafe ; headshots gratuits ou impossibles selon la cible la plus proche ; coûteux en BP | **Rejeté** |
| **C. `TraceRadius` > 0** | 1 valeur à changer, déjà prévue en tuning, prévisible | Un rayon trop gros donne des headshots involontaires | **Retenu, en 2 passes** |
```
ResolveShot():
    Hit1 = LineTraceByChannel(Camera → Range, Weapon)          // passe 1 : précision pure
    if (Hit1.bBlockingHit) return Hit1                         // headshot possible ICI uniquement
    if (WeaponData.TraceRadius > 0):                           // passe 2 : assistance, corps seulement
        Hit2 = SphereTraceByChannel(Camera → Range, TraceRadius, Weapon)
        if (Hit2.bBlockingHit && Hit2.Actor implements BPI_Damageable):
            bAssisted = true                                   // ⚠ force bHeadshot = false en aval
            return Hit2
    return miss
```
La passe 2 ne se déclenche **que si la passe 1 rate tout** : elle ne peut ni dégrader un tir précis, ni voler un
headshot. Un hit issu de la passe 2 est traité comme un **body shot quel que soit le composant touché** — même
si le sphere trace a accroché la `HeadHitbox`, `IsHeadshot()` n'est pas consulté : **l'assistance ne donne
jamais de headshot**, la récompense reste au skill.
Filtrée sur les acteurs `BPI_Damageable` : jamais d'assistance qui fait toucher un mur. Valeur :
`Laser_TraceRadius` (`07_TUNING §11`) ; protocole de playtest : monter par paliers depuis 0
jusqu'au confort à `3000 uu/s`, sans dépasser le rayon de la capsule ennemie, puis consigner dans `07_TUNING §18`.

> ### État d'implémentation — J8sept : implémenté **littéralement**, et ça pose une question à trancher
>
> `ResolveShot` (30 nœuds) implémente le pseudo-code ci-dessus **au mot près**, sortie `bAssisted`
> comprise, et `TryFire` force `bHeadshot = IsHeadshot(Hit) AND NOT bAssisted`. Prouvé en PIE :
> un tir dont la passe 1 rate tout et dont la passe 2 accroche la `HeadHitbox` inflige **50 pv**
> (corps), pas 150 — l'assistance ne donne jamais de headshot.
>
> **⚠️ CONTRADICTION MESURÉE, non résolue par moi — décision de Louis attendue.**
> La condition d'entrée de la passe 2 est `!Hit1.bBlockingHit`, c'est-à-dire *« la passe 1 n'a
> touché **rien du tout** sur 15 000 uu »*. Or le canal `Weapon` est **Block** sur `OD_LevelGeo`
> (§3.3, piège 1) : **dans un niveau fermé, il y a presque toujours un mur derrière l'ennemi.**
>
> Mesure PIE du J8sept, tir volontairement à 45 uu à côté d'une cible (soit 11 uu à côté du corps,
> largement dans le rayon de 25) : la passe 1 a touché **le mur situé 442 uu derrière la cible**
> (`BeamEnd` à 2678 uu, cible à 2236) → la passe 2 ne s'est **pas** déclenchée → **0 dégât**.
> Le seul tir assisté que j'ai pu produire est un tir vers **le ciel** (la passe 1 ne rencontrait
> réellement rien).
>
> **Conséquence : tel qu'écrit, `Laser_TraceRadius` n'aidera presque jamais en jeu réel.** Il aide
> uniquement les tirs vers le vide — exactement les tirs que le joueur sait déjà avoir ratés.
> Le symptôme sera « le tuning ne change rien », pas une erreur.
>
> **Les deux corrections possibles** (aucune n'est appliquée, elles changent le comportement) :
> 1. **Gate sur la cible, pas sur le vide** — la passe 2 se déclenche si la passe 1 n'a pas touché
>    d'acteur `BPI_Damageable` (mur compris). Il faut alors **rejeter un hit de passe 2 plus
>    lointain que le hit de passe 1**, sinon on tire à travers les murs.
> 2. **Une seule passe `SphereTraceMulti`** : trier les hits, prendre le `BPI_Damageable` le plus
>    proche s'il est devant le premier bloquant non-damageable, sinon ce dernier. Une trace au lieu
>    de deux, mais s'éloigne du pseudo-code voté.
>
> Tant que la question n'est pas tranchée, **le comportement en place est celui de la spec**.

## 12. Checklist de validation manuelle
**Laser** — [ ] 1 clic = 1 tir, maintenir ne tire pas en rafale · [ ] le beam part du canon et finit sous le
réticule · [ ] tir à bout portant contre un mur : ne traverse pas · [ ] tirer en pleine course ne change ni
vitesse ni trajectoire · [ ] une cible à `Laser_Range` est touchée · [ ] le recoil bouge la caméra mais le tir
suivant part au centre du réticule.

**Heat** — [ ] ~9 tirs déclenchent l'overheat, le tir déclencheur part quand même · [ ] en overheat : tir
bloqué, melee/dash/slide/wall ride **fonctionnels** · [ ] le clic en overheat produit un son de refus, pas un
silence · [ ] l'arme pend puis se relève instantanément · [ ] la barre pulse à `Heat_WarningThreshold` ·
[ ] après un tir isolé la chaleur redescend à 0 sans jamais bloquer.

**Headshot** — [ ] un tir dans la tête d'un Grunt le tue en 1 coup, systématiquement · [ ] le son est
reconnaissable les yeux fermés · [ ] le hit-stop se sent mais ne coupe pas le mouvement (test en pleine
course) · [ ] 3 headshots en 1 s : pas de saccade, pas de dilation bloquée · [ ] headshot sur ennemi en pleine
course : pas de désync de hitbox.

**Melee & wall slam** — [ ] un melee sur 3 ennemis groupés les touche tous les 3, une seule fois chacun ·
[ ] un ennemi projeté contre un mur meurt, le même projeté dans le vide survit · [ ] le son de wall slam est le
son le plus satisfaisant du jeu · [ ] le Tank ne s'envole pas mais encaisse et recule · [ ] un ennemi projeté
qui atterrit se relève et reprend son IA · [ ] aucun ennemi ne reste bloqué en état « en vol » · [ ] on peut
re-frapper un ennemi déjà en vol.

**Dégâts subis** — [ ] un projectile encaissé fait chuter le compteur de vitesse de façon lisible ·
[ ] l'indicateur directionnel pointe la bonne source · [ ] deux ennemis qui tirent simultanément n'infligent
qu'une punition · [ ] on ne meurt jamais « sans comprendre pourquoi ».

**Mort & vies (§9.4)** — [ ] mourir décrémente le compteur de vies, visiblement · [ ] respawn au dernier
checkpoint du **niveau courant**, upgrades toujours actives et stats correctes · [ ] mourir à 1 vie restante
enchaîne sur `WBP_RunFailed` puis le menu · [ ] mourir **pendant un hit-stop** ne fige pas le jeu (dilatation
restaurée à `1.0`) · [ ] traverser 3 morts d'affilée ne ré-empile aucun bonus d'upgrade.

**Lisibilité sur fond clair (§3.2)** — [ ] le faisceau reste visible tiré **contre une façade blanche en plein
soleil** · [ ] le hitmarker de body shot se voit sur un mur blanc · [ ] le flash de headshot se lit sans être
un aplat blanc · [ ] le crosshair ne se confond jamais avec le faisceau.

**Ressenti (R8)** — [ ] je n'ai jamais eu envie de m'arrêter pour tirer · [ ] tuer un ennemi n'a jamais cassé
mon rythme · [ ] j'ai voulu refaire un wall slam immédiatement après le premier.

## 13. Pièges connus UE5
| # | Piège | Parade |
|---|---|---|
| 1 | **Trace caméra qui traverse un mur collé** : la caméra est en retrait de la capsule ; collé à un mur le trace démarre *dans* le collider et ne le détecte pas. | Canal `Weapon` = **Block** sur `OD_LevelGeo`. Ne jamais sortir la caméra de la capsule. Activer `bUseMuzzleConfirmTrace` (§3.4) **uniquement** si le cas se produit en playtest. |
| 2 | **La capsule englobe la tête** : le trace unique retourne le premier bloquant, donc la capsule (corps) même quand le joueur vise le crâne → headshot impossible. | La `SphereCollision` `Head` doit **déborder** la capsule au niveau de la tête (elle est volontairement généreuse, §5.1) ; se règle dans le viewport en 30 s. Si un cas résiduel apparaît en playtest, passer la passe 1 en `LineTraceMulti` et **prioriser `HeadHitbox`** si les deux composants sont touchés. |
| 3 | **Optimisations d'anim et hitbox.** Avec un physics asset, `URO` faisait retarder les corps sur le mesh → headshots fantômes. | **Non applicable** : D4 supprime le physics asset. La hitbox est une sphère large attachée à un socket, tolérante à un léger retard de pose → le tick de pose n'est **pas critique pour la validité du hit**. `SPEC_ENEMIES §12.4` fait foi : **`Only Tick Pose When Rendered` + URO activés** sur les meshes d'ennemi. |
| 4 | **`Global Time Dilation` casse les timers** : un timer armé sous dilatation est compté en temps monde. | La durée d'un hit-stop est en **temps réel** : armer la sortie sur un timer non affecté par la dilatation (§5.4). Un seul appelant, `BPC_HitStop` sur `PC_Overdrive`. Restaurer `1.0` dans `EndPlay` et au `BeginPlay`. Vérifier `Min Global Time Dilation`. |
| 5 | **Multi-hit du sphere trace** : `SphereTraceMulti` renvoie un `HitResult` **par composant bloquant** → capsule + `HeadHitbox` (+ `WeakPointHitbox` sur le Tank) = un ennemi prend 2 à 3× les dégâts melee. | `HitActorsThisSwing : Array<Actor>` vidé à chaque swing, `Contains()` avant traitement (§6). Le dédoublonnage se fait **par acteur**, jamais par composant. |
| 6 | **`Event Hit` ne donne pas la vitesse d'avant impact** : `GetVelocity()` y est déjà écrasée par la résolution du CMC. | `LastFrameVelocity` mis à jour par un Tick **actif seulement pendant le vol** (activé au launch, coupé par `EndKnockbackWindow`). |
| 7 | **`Simulation Generates Hit Events` = false** par défaut sur la capsule → aucun `Event Hit` pendant le knockback. | L'activer sur la capsule de `BP_EnemyBase`. |
| 8 | **Tunneling** : un `Melee_Knockback` élevé peut traverser un mur fin. | `bUseCCD = true` sur la capsule ennemie ; murs d'au moins un module de grille (`06_CONVENTIONS §6`) ; `Speed_HardCap` respecté. |
| 9 | **Double kill / double score** : melee + slam + projectile dans la même frame. | Garde `bIsDead` en **première ligne** de `TakeDamage` ; `bSlamConsumed` par vol. |
| 10 | **Beam Niagara à durée non nulle** : reste visible alors que le joueur avance de ~50 uu par frame. | Durée ≤ 1 frame, ou beam en **World Space** avec positions figées à l'émission. **Vécu au J8** sur la ligne de debug (`DrawDebugLine` en espace monde, 0.06 s) : Louis a rapporté un rayon *« qui part depuis le vide »*. Corrigé en redessinant le faisceau chaque frame depuis le muzzle courant (§2, dérogation de Tick). ⚠️ Corollaire mesuré dans la source moteur : pour `Draw Debug Line`, **`Duration <= 0` ne vaut PAS « une frame »** — le moteur retombe sur `ULineBatchComponent::DefaultLifeTime = 1.0 s`. Passer `DeltaSeconds`. Cf. `12_PIEGES §6.18`. |
| 10bis | **Une origine de faisceau relue chaque frame produit un ÉVENTAIL, pas un rayon.** Le correctif du piège 10 (redessiner depuis le muzzle courant) a créé le bug inverse : chaque segment vit `LaserDebug_DrawLifetime` (0.05 s ≈ 3 frames) et le canon se déplace de ~32 uu par frame à 1900 uu/s → **3 segments d'origines différentes coexistent**, lus par le joueur comme *« deux rayons qui divergent depuis le point d'impact »* (Louis, manche en main, J8bis). Zéro erreur, zéro warning : les deux versions « fonctionnent ». | **Accroche puis décrochage.** Relire le muzzle **seulement** pendant `LaserDebug_AttachTime` (0.05 s), puis **figer l'origine en espace monde**. L'éventail résiduel de la fenêtre d'accroche est ce qui donne « ça part du canon » ; passé la fenêtre, tous les redessins se superposent au pixel près. Règle générale : **une origine mobile et une durée de vie de segment supérieure à une frame sont incompatibles** — il faut borner l'une des deux. |
| 11 | **`Child Actor Component` null** si la référence est lue trop tôt. | `Get Child Actor` dans le `BeginPlay` du character après le parent, puis mise en cache. Jamais résolue en Tick. |
| 12 | **`StopLogic` sans `ResumeLogic`** : un ennemi projeté dont la récupération ne se déclenche pas reste figé pour la partie. | `Knockback_MaxFlightTime` armé systématiquement ; `EndKnockbackWindow` appelé aussi depuis `Event Landed` et `OnDeath`. |
| 13 | **Recoil via `AddControllerPitchInput`** : se cumule avec l'input souris, le retour auto se bat avec le joueur. | Recoil **caméra uniquement** (§3.6). |
| 14 | **Timers de cooldown empilés** : un clic très rapide peut ré-armer le timer. | Gate `bCanFire` testé **avant** l'armement. `Set Timer by Event`, jamais `by Function Name`. |

## 14. Arbitrages

Toutes les clés utilisées par cette spec existent dans `Docs/07_TUNING.md` et toutes les corrections de
cohérence sont faites. Les décisions qui ont tranché les contradictions (hitboxes, dissolve, hit-stop,
shakes, `BPI_Damageable`, couleurs, catalogues SFX/VFX) sont consignées dans **`Docs/11_ARBITRAGES.md`**,
qui a autorité immédiatement après `CLAUDE.md`.
