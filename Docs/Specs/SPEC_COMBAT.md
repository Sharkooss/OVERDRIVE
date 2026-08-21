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
| `OwnerCharacter` / `OwnerController` | refs | Cachées au `BeginPlay`, jamais de cast en Tick. **Prérequis : cocher `Set Owner` sur `ChildActor_Laser`** — sans ça `GetOwner()` est nul et les deux refs restent nulles (`12_PIEGES §6.26`). `OwnerController` est en plus rafraîchi par `EnsureOwnerRefs` en tête de `TryFire`, pour le respawn |
| `bCanFire` | Bool | Gate du cooldown |
| `bUseMuzzleConfirmTrace` | Bool | Défaut `false` (§3.4) |
| `TryFire()` | Event | Point d'entrée unique depuis `IA_Fire` (§3) |
| `ResolveShot()` | Function | **Un** sphere trace + point d'impact. **Aucun effet de bord.** Sorties : `Hit`, `bBlockingHit` (§11) |
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
| `OnOverheatStarted` / `OnOverheatEnded` | Dispatchers | Relayés depuis `BPC_Heat`. **Marquent l'entrée/sortie du maximum de pénalité de style, pas un verrou de tir** (`11_ARBITRAGES D58`, §4) |

> **`SPEC_COMBAT` fait foi sur les dispatchers de l'arme.** Les noms et signatures retenus sont
> `OnShotFired(Hit, bHit)` et `OnHitConfirmed(Target, bHeadshot, bKilled)` : toute autre doc qui les
> nomme autrement s'aligne sur cette section.

**Répartition** — `BP_PlayerCharacter` possède l'arme et relaie inputs + dispatchers, **aucune** logique de
trace / dégâts / chaleur. `BP_LaserWeapon` : trace, dégâts, FX, recoil, cooldown. `BPC_Heat` : jauge, états,
`MPC_Global`. `BPC_Melee` est sur le **character**, pas sur l'arme : le melee est une action du corps, pas de
l'arme, et il doit survivre à un changement ou à une perte d'arme.
*(Sa justification d'origine — « le melee reste dispo en overheat » — est caduque depuis `D58` : plus rien
n'est bloqué par la chaleur. Le placement, lui, ne change pas.)*

## 3. Le tir — séquence complète
`IA_Fire` (Digital Bool, trigger **`Pressed`** seul, `IMC_Gameplay`) → `BP_PlayerCharacter.HandleFireInput()`
→ `BP_LaserWeapon.TryFire()`. Maintenir le bouton ne fait rien : relâcher et re-cliquer.

### 3.1 `TryFire()`
```
TryFire():
    if (!bCanFire): return                                      // gate 1, silencieux
    if (OwnerCharacter.BPC_Health.bIsDead): return              // gate 2
    bCanFire = false
    SetTimerByEvent(EndFireCooldown, WeaponData.FireCooldown)   // 07_TUNING §11 Laser_FireCooldown
    ShotResult = ResolveShot()                                  // §3.2-3.4 + §11
    ApplyShotHeat(ShotResult.Hit, ShotResult.bBlockingHit)      // ── CHALEUR : ICI, avant tout dégât (§4)
    if (ShotResult.bBlockingHit):
        ProcessHit(ShotResult.Hit, IsHeadshot(ShotResult.Hit))  // §3.5 — headshot PLEIN, aucune condition
    PlayFireFX(ShotResult.Hit, ShotResult.bBlockingHit)         // toujours, même à vide
    ApplyRecoil()                                               // §3.6
    OnShotFired.Broadcast(ShotResult.Hit, ShotResult.bBlockingHit)

ApplyShotHeat(Hit, bBlockingHit):                               // BP_LaserWeapon, J9
    if (!bBlockingHit):                    Heat.NotifyShotResolved(false, false) ; return
    if (Cast<BPI_Damageable>(Hit.Actor) échoue): Heat.NotifyShotResolved(false, false) ; return
    Heat.NotifyShotResolved(true, IsHeadshot(Hit))              // body = neutre, tête = refroidit (§4.1)
```
> **Il n'y a plus de gate de chaleur** (`11_ARBITRAGES D58`) : la chaleur ne bloque **jamais** le tir.
> L'ancienne gate 1 « `if Overheated: PlayDenyFeedback(); return` » **a disparu**, et avec elle le
> `PlayDenyFeedback` du chemin de tir. Les deux gates restantes sont le cooldown et la mort.
> Il n'y a jamais eu de gate d'overheat dans le code : le J8 n'avait pas implémenté la chaleur,
> il n'y a donc **rien eu à retirer** au J9 — seulement à ne pas l'écrire.
>
> ### ⚠️ Ordre corrigé au J9 : la chaleur se calcule AVANT `ProcessHit`, pas après
>
> *La v1 de ce §3.1 plaçait la chaleur en **dernier**, au motif qu'elle « dépend du résultat du tir ».
> C'est vrai de la **résolution** (`ResolveShot`), c'est faux des **dégâts**.* `ProcessHit` appelle
> `ApplyDamage`, qui **détruit la cible** quand le coup est létal : un `Cast<BPI_Damageable>` exécuté
> après lui sur `Hit.Actor` porte sur un acteur `pending kill` et **échoue**.
> **Mesuré en PIE au J9** : un headshot létal était classé `MissedShot` et faisait **monter** la
> chaleur de +11 — l'exact inverse de `D58`. Le bug n'apparaissait que sur les tirs qui **tuent**.
> Détail et règle générale : `12_PIEGES §6.25`.
>
> **Ce qui compte n'a pas changé** : la chaleur reste calculée **après `ResolveShot()`**, puisqu'elle
> dépend de ce que le rayon a touché. Elle est simplement calculée **avant qu'on n'y touche**.
>
> **Deux tests d'interface par tir, assumé.** `ApplyShotHeat` refait le `Cast<BPI_Damageable>` que
> `ProcessHit` fait déjà (§3.5). Aucune divergence possible — c'est le **même cast sur le même
> acteur** — et l'alternative (faire remonter un `bool` de `ProcessHit`) coûtait une signature
> modifiée et un site d'appel recréé (`12_PIEGES §2.37`) pour économiser un cast par tir.

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
SphereTraceByChannel(
    Start = CameraLocation, End = CameraLocation + ControlForward * Range,
    Radius = WeaponData.TraceRadius,  // mercy de visée, §11 — 0 équivaut à un line trace
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
> - **Le nœud réel est `Collision|SphereTraceByChannel`**, pas `Line Trace By Channel` — décision de
>   Louis du 2026-08-20, cf. **§11**. C'est le **seul** trace de gameplay du tir : un par tir.
>   `Radius` est alimenté par `WeaponData.TraceRadius`.
> - Le canal `Weapon` est **`ECC_GameTraceChannel3`** et se pose sur le pin `TraceChannel` sous la
>   valeur **`TraceTypeQuery3`** (prouvé, cf. `12_PIEGES_OUTILLAGE 5.18`).
> - **`bReturnPhysicalMaterial` n'existe pas** sur les nœuds Blueprint de trace simple
>   (`UKismetSystemLibrary::SphereTraceSingle` ne l'expose pas). Le pin `PhysMat` du `Break Hit Result`
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
- **Trace unique, non-multi.** Pas de pénétration, pas de ricochet, pas de spread (`Laser_Spread = 0`),
  et **aucune seconde passe** : l'épaisseur du trace *est* toute l'aide à la visée (§11).

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

## 4. Système de Heat — `BPC_Heat` : une **jauge de discipline de tir**

> **Réécrit le 2026-08-20 — `11_ARBITRAGES D58`. La chaleur ne bloque plus jamais le tir.**
> Note historique en fin de section.

Attaché à `BP_LaserWeapon`, lit le `WeaponData` de son owner. Valeurs : `07_TUNING §11 > Heat`.

**Ce que la jauge mesure** : la **discipline de tir**, pas une réserve de munitions. Elle monte quand le
joueur **rate**, elle descend quand il **touche précisément** ou quand il **va vite**. Elle n'a qu'une
conséquence — une **perte de style continue** (`Style_Loss_Heat`, `07_TUNING §14`). Elle ne bloque ni le
tir, ni le melee, ni le mouvement : **rien, jamais**.

La phrase que le joueur doit pouvoir formuler : *« rate, et mon style fond ; touche et va vite, et je ne
vois jamais cette jauge. »*

### 4.1 Sources et puits

| Sens | Événement | Montant (`07_TUNING §11`) |
|---|---|---|
| **↑ Monte** | **tir raté** — le trace ne touche **aucun** acteur implémentant `BPI_Damageable` (mur, décor, ou rien) | `+ Heat_PerMissedShot` |
| **= Neutre** | **tir au corps qui touche une cible** | **rien.** Ni montée, ni descente |
| **↓ Descend** | **headshot** — montant **fixe**, événementiel | `− Heat_CoolPerHeadshot` |
| **↓ Descend** | **vitesse horizontale ≥ `Heat_CoolSpeedThreshold`** — continu, par le timer | `− Heat_CoolRateAtSpeed` /s |
| **⛔ Jamais** | **décroissance passive** | **il n'y en a aucune.** Le refroidissement se **mérite** |

**Le seuil de vitesse est partagé avec le style, exprès.** `Heat_CoolSpeedThreshold` est
**volontairement la même valeur** que le seuil de `Style_Gain_HighSpeedSustain` (`07_TUNING §14`) :
le joueur n'a **qu'une** règle à apprendre — *au-dessus de ce seuil je gagne du style **et** mon arme
refroidit*. **Les deux valeurs se déplacent ensemble** ; en changer une seule casse l'intention de D58.

### 4.2 États `E_HeatState` (`08_DATA_SCHEMAS §1`)

**L'enum est inchangé** — il a été saisi à la main et n'est pas modifiable par outil
(`12_PIEGES §5.2`). **Seule la sémantique d'`Overheated` change.**

```
       tir RATÉ  (+Heat_PerMissedShot)                Heat >= Heat_WarningThreshold
   ┌──────────┐ ─────────────────────▶ ┌──────────┐ ──────────────────────────────▶ ┌──────────────┐
   │ Cooling  │                        │ Building │                                 │   Warning    │
   │ Heat ↓   │ ◀───────────────────── │  Heat ↑  │ ◀────────────────────────────── │ Style_Loss_  │
   └──────────┘   headshot, ou vitesse └──────────┘   Heat < Heat_WarningThreshold   │ Heat ACTIVE  │
        │         ≥ CoolSpeedThreshold                                               └──────────────┘
        │ Heat == 0                                                                        │ tir raté
        ▼  (pas un état : juste le plancher)                                               ▼ → Heat >= Heat_Max
   ┌────────────┐              ┌──────────────────────────────────────────────────────────────┐
   │  Heat = 0  │              │                        Overheated                            │
   │ jauge vide │              │  LE TIR N'EST PAS BLOQUÉ.  Heat == Heat_Max (clampé).         │
   └────────────┘              │  Pénalité de style au MAXIMUM. Sortie : dès que la chaleur    │
                               │  redescend — headshot ou vitesse. Aucune durée minimale.      │
                               └──────────────────────────────────────────────────────────────┘
```

| Règle | Détail |
|---|---|
| Ajout | `AddHeat(Amount)` → `Clamp(CurrentHeat + Amount, 0, Heat_Max)`. **N'arme aucun délai** : il n'y en a plus. |
| Retrait | `RemoveHeat(Amount)` → `Clamp(CurrentHeat - Amount, 0, Heat_Max)`. Même clamp, même dispatcher. |
| Refroidissement continu | `Heat_CoolRateAtSpeed` /s, **uniquement** si `BPC_MovementState.GetHorizontalSpeed() >= Heat_CoolSpeedThreshold`. Appliqué par un timer à fréquence fixe (`Heat_TickInterval`, `07_TUNING §11`). **Jamais en Tick.** |
| Décroissance passive | **Aucune.** Un joueur qui a fait monter sa jauge puis s'arrête reste chaud aussi longtemps qu'il n'a ni touché une tête, ni repris de la vitesse. **Attendre ne refroidit rien.** |
| Entrée en `Warning` | `CurrentHeat >= Heat_WarningThreshold`. **`Style_Loss_Heat` s'applique à partir de là**, et jusqu'à ce que la chaleur repasse sous le seuil. |
| Entrée en `Overheated` | `CurrentHeat >= Heat_Max`. **Le tir continue de partir normalement.** C'est le maximum de la pénalité de style, pas un verrou. |
| Sortie d'`Overheated` | **Immédiate** dès que `CurrentHeat < Heat_Max`. Pas de durée minimale, pas de seuil de sortie, pas de condition cumulative. |
| Bloqué par la chaleur | **Rien.** Ni tir, ni melee, ni dash, ni slide, ni wall ride, ni saut. |
| Reset | `CurrentHeat = 0` à la mort du joueur et au chargement d'un niveau — comme le style (`SPEC_SCORE_RANK §4.3`). Chaque niveau est une performance indépendante. |
| Upgrades | `HeatCapacity` / `HeatRecovery` (`E_UpgradeStat`) lus via `BPC_PlayerStats` au `BeginPlay`. Jamais en dur. `HeatRecovery` surcharge désormais **`Heat_CoolRateAtSpeed` et `Heat_CoolPerHeadshot`** — `Heat_DecayRate` est `INACTIVE`. |

**Rythme visé** : le joueur qui touche ce qu'il vise **ne voit jamais la jauge bouger**. Les repères de
tempo (`Heat_Max / Heat_PerMissedShot`, `Heat_WarningThreshold / Heat_PerMissedShot`) et la règle de
réglage sont dans `07_TUNING §11` — pas ici (R3).

### 4.3 Conséquence : une perte de style, pas un canal de score

**Tant que `CurrentHeat >= Heat_WarningThreshold`, `Style_Loss_Heat` (`07_TUNING §14`) est appliquée en
continu** au `BPC_StyleMeter`, par le même timer `Heat_TickInterval` qui gère le refroidissement.

- C'est une perte **continue**, pas un `E_StyleEvent` ponctuel : la chaleur est un **état**. Elle
  n'entre pas dans `DT_StyleEvents` et n'est donc soumise ni à la dégressivité ni à l'anti-farm
  (`SPEC_SCORE_RANK §4.4`).
- Elle se **cumule** avec `Style_DecayPerSec`.
- **Il n'y a pas de canal de score dédié à la chaleur.** Le style est le seul terme multiplicatif du
  score (`SPEC_SCORE_RANK §2`) : y brancher la chaleur suffit, et évite un deuxième multiplicateur
  vivant alimenté par les mêmes entrées (`11_ARBITRAGES D58`, options écartées).

> ### ⏳ Dette datée au J18 — et pourquoi le J9 n'est pas vide pour autant
>
> `BPC_StyleMeter` **n'existe qu'au J18**. Le J9 livre donc la jauge, ses sources, ses puits, la
> couleur de l'arme (`MPC_Global.HeatRatio`) **et un affichage provisoire du coût à l'écran** qui
> montre **exactement** la perte qui s'appliquera — cf. `SPEC_UI_HUD §3.3`.
>
> **Ce n'est pas du confort, c'est une parade.** Une valeur de tuning qui ne pilote rien se calibre
> à l'aveugle et donne l'illusion de fonctionner : c'est le piège `Laser_TraceRadius`, qui a coûté
> deux chantiers au J8 (`04_ROADMAP` J8, `12_PIEGES §6.24`). **Pas de pourcentage de score inventé**
> au J9 : on affiche la **grandeur réelle** — `CurrentHeat` et `Style_Loss_Heat` telle quelle, en
> unités de style par seconde — jamais une approximation qu'il faudrait défaire au J18.
> Format exact et exemple chiffré : `SPEC_UI_HUD §3.3a`.

### 4.4 API & feedback

> ### ✅ État réel après le J9 (2026-08-20) — ce paragraphe fait foi sur le code
>
> `BPC_Heat` vit dans `Content/OVERDRIVE/Weapons/Laser/`, **attaché à `BP_LaserWeapon`** sous le nom
> de composant `Heat`. **21 variables, 18 fonctions, `EventGraph` vide** (aucun Tick, aucun event).
>
> | Prévu par la spec | Livré au J9 | Écart |
> |---|---|---|
> | `CurrentHeat`, `AddHeat`, `RemoveHeat`, `GetHeatRatio()`, `GetCurrentStylePenalty()`, `IsOverheated()` | ✅ tels quels | — |
> | `CurrentState : E_HeatState` | ❌ **remplacé par deux booléens** `bWarningActive` / `bOverheatActive` | **Aucun outil ne sait créer une variable typée enum** (`12_PIEGES §5.2`). L'enum `E_HeatState` **existe et reste valide** ; il sera branché le jour où Louis pose la variable à la main. Les deux booléens portent **exactement** la même information que `Warning` et `Overheated` ; `Cooling` / `Building` se déduisent du signe de `LastHeatDelta`. |
> | `OnHeatChanged(Ratio, State)` | ✅ `OnHeatChanged(Ratio, HeatValue, bWarning, bOverheat)` | même raison : pas de pin enum. Le dispatcher **existe et se déclenche** ; `WBP_HUD` s'y branchera au J19 sans rien réécrire. |
> | `OnWarningEntered` · `OnOverheatStarted` · `OnOverheatEnded` | ✅ tels quels | — |
> | Timer `Heat_TickInterval`, **jamais en Tick** | ✅ `SetTimerByFunctionName("HeatTickStep", TuneTickInterval, looping)` | armé par `InitializeHeat`, appelée en **tête** du `BeginPlay` de l'arme (`12_PIEGES §6.26`). |
> | `MPC_Global.HeatRatio` / `OverheatActive` | ❌ **non fait**, reporté au **J14** | `MPC_Global` n'existe pas encore et **aucun matériau d'arme ne l'échantillonne**. L'écrire au J9 aurait produit une valeur que personne ne lit — le piège `12_PIEGES §6.24` reconstruit. Le J14 crée déjà `MPC_Global` (`04_ROADMAP`), c'est là que la couleur de l'arme se branche. |
>
> **Fonctions internes non prévues par la spec, et pourquoi** : `ApplyHeatDelta(Delta, Source)` et
> `CommitHeat(NewHeat, Delta, Source)` — le clamp, les transitions d'état et le broadcast vivent en
> **un seul** endroit, et `Source` (chaîne : `MissedShot` / `Headshot` / `Speed` / `Reset`) rend
> chaque variation lisible en headless. `UpdateWarningFlag` / `UpdateOverheatFlag` sont séparées
> parce qu'un `if` **termine le flux d'exec** en Blueprint (`12_PIEGES §2.11`) : une fonction, un `if`.
> `EnsureCMC` et `PushToHeatBar` sont les deux résolutions **paresseuses** (voir juste après).
>
> **Résolution paresseuse — pourquoi rien n'est câblé au `BeginPlay`.**
> `BP_LaserWeapon` est un **Child Actor**, et son `BeginPlay` peut passer **avant `Possess()`**
> lors d'un respawn en cours de partie : le `PlayerController` n'y est donc pas garanti.
> ⚠️ **Mise à jour 2026-08-20** : la raison invoquée au J9 (« `OwnerCharacter` reste nul en jeu »)
> **n'était pas la bonne** — c'était `ChildActor_Laser.bSetOwner = false`, le défaut moteur d'UE 5.8
> (`12_PIEGES §6.26`, corrigé). `OwnerCharacter` est désormais **valide dès le `BeginPlay`**.
> La conception paresseuse reste néanmoins la bonne et **ne change pas** : elle ne dépend d'aucun
> cast, donc elle est robuste au respawn comme au démarrage.
> `InitializeHeat` ne fait que **lire le tuning et armer le timer**
> (le `WeaponData` est un défaut de classe, toujours valide), et `HeatTickStep` appelle `EnsureCMC`
> à **chaque tick tant que ce n'est pas résolu** — cette fonction récupère alors
> `GetPlayerCharacter(0).CharacterMovement`, crée la jauge et pose `bInitialized = true`.
> Le refroidissement par la vitesse (`CoolBySpeed`) et le cumul de perte de style sont gardés par ce
> drapeau ; **`AddHeat` / `RemoveHeat` / `NotifyShotResolved` fonctionnent sans lui.**

**API** : `CurrentHeat` · `CurrentState` · `AddHeat(Amount)` · `RemoveHeat(Amount)` ·
`GetHeatRatio()` (pure) · `GetCurrentStylePenalty()` (pure — renvoie `Style_Loss_Heat` si
`CurrentHeat >= Heat_WarningThreshold`, sinon `0` ; c'est elle qui alimente l'affichage provisoire du
J9 **et** le câblage réel du J18, sans que rien ne soit à réécrire).

`IsOverheated()` (pure) est **conservée** — elle répond désormais *« la pénalité de style est-elle au
maximum ? »*, plus jamais *« le tir est-il bloqué ? »*. **Aucun chemin de tir ne doit l'appeler.**

Dispatchers : `OnHeatChanged(Ratio, State)` → `WBP_HeatBar` (bind, pas de Tick) ·
`OnOverheatStarted` / `OnOverheatEnded` (**conservés** : ils marquent l'entrée et la sortie du maximum
de pénalité, pas un verrou) · `OnWarningEntered`. `BPC_Heat` écrit `HeatRatio` et `OverheatActive`
dans `MPC_Global` (`08_DATA_SCHEMAS §6`) : les matériaux de l'arme chauffent **sans une ligne de BP
supplémentaire**.

| Feedback | `Cooling` | `Building` | `Warning` | `Overheated` |
|---|---|---|---|---|
| `WBP_HeatBar` | la barre **descend** visiblement | remplissage froid | **pulse** + couleur chaude **+ coût affiché** (`SPEC_UI_HUD §3.3`) | pleine, clignote, **coût affiché**. **Aucune icône de verrou** |
| Audio | son court de rachat sur headshot | `SC_Laser_Fire` | `SC_Heat_Warning` (loop montant) | loop de warning entretenu |
| VFX arme | l'émissif retombe | — | émissif piloté par `MPC_Global.HeatRatio` | `NS_OverheatVent` (vapeur au muzzle) en boucle |
| Anim | idle | idle | idle | **idle.** L'arme **ne pend plus** : elle tire toujours, elle doit rester pointée |
| Clic | normal | normal | normal | **normal — le tir part.** Plus aucun clic refusé nulle part |

> **Ce que le feedback doit dire, et ne doit pas dire.** En `Warning` et en `Overheated`, l'arme est
> **chaude et bruyante, mais fonctionnelle**. Tout signe de verrouillage — icône de cadenas, canon
> baissé, clic sec, crosshair barré — **ment au joueur** et doit être retiré. Le message est
> *« tu es en train de payer »*, pas *« tu ne peux plus tirer »*.

> ### 🕮 Note historique — le modèle à verrou, spec'é puis abandonné avant implémentation
>
> *Jusqu'au 2026-08-20, ce §4 décrivait un overheat classique : à `Heat_Max` le tir était **bloqué**
> pendant `Heat_OverheatDuration` (1,5 s), la sortie exigeait `Heat_OverheatDuration` écoulé **ET**
> `CurrentHeat <= Heat_OverheatExitThreshold`, la décroissance passive tournait à `Heat_DecayRate`
> après un `Heat_DecayDelay`, accélérée par `Heat_OverheatDecayMultiplier` pendant le verrou. Le
> feedback comportait une icône de verrou, un `SC_Laser_Deny` sur clic refusé, et une animation
> d'arme qui pend.*
>
> **Ce modèle n'a jamais été implémenté.** Il a été abandonné au J9−1 parce qu'il contredisait le §1
> de cette même spec : *« le combat est un sous-produit du mouvement, jamais son interruption »*.
> Le verrou de tir était **la seule interruption du jeu**, et il poussait le joueur à faire de la
> comptabilité de munitions — l'interdit explicite du §1 (« Munitions = rythme, pas gestion »).
>
> *Ce qui reste vrai de cet épisode :* la chaleur devait bien **mesurer quelque chose** et
> **se voir** ; c'est la **conséquence** qui était mauvaise, pas la jauge. `E_HeatState`,
> `MPC_Global.HeatRatio`, `WBP_HeatBar` et les dispatchers sont intégralement réutilisés.
> Les 6 clés du modèle à verrou sont marquées `INACTIVE` dans `07_TUNING §11` et **conservées** en
> l'état dans `PDA_WeaponData` / `DA_Weapon_Laser` : **inertes, lues par personne.**

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

> **§5.4a — état réel de l'asset (2026-08-21), ce paragraphe fait foi sur deux points.**
>
> **1. `ArmRealTimeTimer` n'existe pas en Blueprint — et n'est pas nécessaire.** Aucun nœud BP
> n'expose de timer insensible au time dilation. La durée réelle s'obtient par un **timer monde
> de durée `RealDuration × Dilation`** : sous dilatation `d`, le monde avance de `d` seconde par
> seconde réelle, donc un timer monde de `RealDuration × d` expire après exactement
> `RealDuration` secondes réelles. C'est algébriquement identique à la spec, sans nœud custom.
> *(Vérification : `d = 0.05`, `RealDuration = 0.05` → timer monde de `0.0025 s`, soit 3 frames
> réelles à 60 fps.)*
>
> **2. La cadence est mesurée en TEMPS RÉEL, pas en `GameTime`.** Le pseudo-code dit
> `GameTime - LastHitStopTime`, mais `GameTime` est dilaté — or la garde de cadence sert
> précisément quand des hit-stops s'enchaînent, c'est-à-dire quand le temps est ralenti.
> `GetRealTimeSeconds` est utilisé des deux côtés. Identique à la spec quand `d = 1`, correct
> quand `d < 1`.
>
> **Ce qui est conforme sans écart** : priorité strictement supérieure, `HitStop_MinInterval`,
> propriétaire unique du `Set Global Time Dilation`, `EndHitStop` rappelée au `BeginPlay` **et**
> à l'`EndPlay` (précaution 2), SFX joué avant l'appel (précaution 5, dans
> `BP_LaserWeapon.SendHitFeedback`), réservé au headshot (précaution 3).
> **Précaution 4 non vérifiée en jeu** : `MinGlobalTimeDilation` n'est pas surchargé dans
> `Config/`, donc il vaut le défaut moteur `0.0001 ≤ 0.05` — mais cela n'a pas été relu à
> l'exécution.
>
> **Appelant** : `PC_Overdrive.NotifyHitConfirmed(bHeadshot, bKilled)`, qui porte les 3 clés
> `HitStop_Headshot` / `HitStop_TimeDilation` / `HitStop_HeadshotPriority` (`07_TUNING §16`).
> Le composant ne connaît aucun événement de jeu : c'est un service.

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
Composant du **`BP_PlayerCharacter`** (`Weapons/Melee/`), pas de l'arme : le melee est une action du corps
et ne dépend d'aucun état de l'arme (§2). Depuis `D58` la chaleur ne bloque plus rien, donc **aucune action
du joueur n'est conditionnée à l'état de `BPC_Heat`**.

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
| **Tir raté** | « j'ai payé ça » : la jauge de chaleur **bouge visiblement** au moment du tir manqué, sans casser le rythme du tir suivant | **aucun** | `WBP_HeatBar` +1 cran, monte vers le chaud | — |
| **Chaleur haute** (`Warning` / `Overheated`) | **coût lisible, pas frustration** : l'arme est chaude, bruyante et **parfaitement fonctionnelle**. Le joueur doit lire *« mon style fond »*, pas *« je ne peux plus tirer »* | **aucun shake** (ce n'est pas un impact) | `WBP_HeatBar` chaude + pulse, **et le coût de style affiché** (`SPEC_UI_HUD §3.3`). **Ni verrou, ni crosshair barré** | — |
| **Rachat de chaleur** | récompense **immédiate** de la précision et de la vitesse : la jauge **redescend** franchement sur un headshot, et fond en continu au-dessus de `Heat_CoolSpeedThreshold` | — | `WBP_HeatBar` descend, retour au froid | — |
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

## 11. Aide à la visée — **un seul sphere trace, dégâts pleins**

### La décision, dans les termes de Louis (2026-08-20, J8nonies)

> *« Au lieu d'un line trace ce soit un sphere trace pour être légèrement plus permissif.
> Je ne veux pas de réduction de dégâts et de traces qui sont effectués. C'est juste pour avoir
> un peu de mercy avec le joueur, c'est aussi simple que ça. Pour avoir la sensation que c'est ok.
> C'est pour ça que le radius ne doit pas être aberrant parce que ça se verrait trop, mais plutôt
> que le joueur n'ait pas la frustration d'avoir l'impression de toucher alors qu'il passe à 4 px près. »*

L'intention n'est **pas** un système d'assistance : c'est un **épaississement du rayon de tir**.
Le joueur ne doit ni le voir, ni savoir qu'il existe. Tout ce qui rend l'aide *observable* —
seconde passe, dégâts réduits, headshot refusé — la trahit et est donc **hors de la demande**.

| Option | Verdict |
|---|---|
| **A. Rien** (`Laser_TraceRadius = 0`) | Rejeté : à 3000 uu/s le taux de touche s'effondre, le joueur ralentit pour toucher → contredit le pilier n°1 |
| **B. Magnétisme / snap** | **Rejeté** : le réticule bouge tout seul, se bat avec un 180° en air strafe, coûteux en BP |
| **C. `TraceRadius` > 0, trace unique** | **RETENU** — 1 valeur à changer, 1 trace par tir, aucune branche |

### Le code réel

```
ResolveShot():
    Hit = SphereTraceByChannel(
            Start          = OwnerController.PlayerCameraManager.GetCameraLocation(),
            End            = Start + ControlRotation.ForwardVector * WeaponData.Range,
            Radius         = WeaponData.TraceRadius,        // 07_TUNING §11
            TraceChannel   = Weapon (TraceTypeQuery3),
            bTraceComplex  = false,
            ActorsToIgnore = [OwnerCharacter],
            bIgnoreSelf    = true)
    return (Hit, Hit.bBlockingHit)
```

Trois règles, et il n'y en a pas d'autre :

1. **Un seul trace par tir.** Pas de passe de rattrapage, pas de trace multi, pas de garde
   d'occlusion, pas de notion de « tir assisté ». Un sphere trace s'arrête sur le **premier**
   bloquant rencontré, mur compris — donc on ne tire jamais à travers un mur, gratuitement,
   sans code dédié. C'est ce qui rend le modèle en 2 passes inutile.
2. **Aucune réduction de dégâts.** Un headshot obtenu par le rayon de la sphère est un headshot
   **plein**, `Laser_Damage_Body × Laser_HeadshotMultiplier` = 150 pv. `TryFire` passe le résultat
   d'`IsHeadshot()` **directement** à `ProcessHit`, sans condition.
3. **Le rayon reste petit.** Il ne doit pas se voir. `Laser_TraceRadius` (`07_TUNING §11`) est
   **le** curseur de la mercy : monter si le joueur a l'impression de rater ce qu'il touchait,
   descendre si des tirs manifestement ratés touchent quand même.

> ### État d'implémentation — J8nonies : le pseudo-code ci-dessus EST le code réel
>
> `BP_LaserWeapon.ResolveShot` = **15 nœuds** (36 au J8oct), **un seul nœud de trace**
> (`Collision|SphereTraceByChannel`), une seule chaîne d'exec, un seul `ReturnNode`, zéro nœud mort.
> Signature : `(Hit : HitResult, bBlockingHit : bool)` — la sortie `bAssisted` **n'existe plus**.
> Dans l'`EventGraph`, `IsHeadshot(Hit)` alimente `ProcessHit.bHeadshot` **en direct** (le `NOT` et
> le `AND` ont été supprimés).
>
> **Prouvé en PIE le 2026-08-20** avec `TraceRadius = 12`, `MaxHealth = 100`, `BodyDamage = 50`,
> joueur à `(0, −3000, 300)`, cible à `(1000, −5000, 90)` (corps 60 × 60 × 180) :
>
> | Cas | Visée | Attendu | Mesuré |
> |---|---|---|---|
> | 1 | corps, plein centre | `−50` | `100 → 50`, `BeamEnd (979, −4970, 91.3)` à 2200.7 uu |
> | 2 | `HeadHitbox` (z = 165) | 1 coup | **acteur détruit**, `BeamEnd` à **exactement 50.0 uu** du centre de la sphère de tête |
> | 3 | **8 uu à côté du corps** (dans le rayon) | `−50` | `100 → 50`, `BeamEnd (1030.0, −4970.0, 90.6)` = **l'arête du corps** |
> | 4 | **30 uu à côté** (hors rayon) | `0` | les 7 cibles restent à `100`, faisceau **au-delà**, sur le mur à 2602 uu |
> | 5 | mur en face à 1000 uu | `0` + beam arrêté | `0` dégât, `BeamEnd` à **1000.0 uu** |
>
> Le cas 1 mesure 2200.7 uu contre 2203.4 au J8oct : l'impact tombe **2.7 uu plus tôt**, c'est le
> rayon de la sphère sur une face rasante. Invisible en jeu, et c'est le seul effet du changement
> sur un tir précis.
>
> #### 🕮 Note historique — le modèle à 2 passes, construit puis retiré
>
> *Des J8sept au J8oct, ce §11 décrivait une option « C, retenue en 2 passes » : `LineTrace` de
> précision, puis `MultiSphereTraceByChannel` de rattrapage, gate sur « je n'ai pas touché de
> cible », garde d'occlusion `(NOT Hit1.bBlockingHit) OR (h.Distance < Hit1.Distance)`, sortie
> `bAssisted`, et la règle « **l'assistance ne donne jamais de headshot** » — `TryFire` forçait
> `bHeadshot = IsHeadshot(Hit) AND NOT bAssisted`.*
>
> *Cette machinerie était correcte et prouvée en PIE. Elle a été **retirée le 2026-08-20** parce
> qu'elle ne servait pas l'intention : Louis ne demandait pas un système d'assistance à arbitrer,
> il demandait de ne pas rater à 4 px près. Les 21 nœuds de la seconde passe résolvaient un problème
> de game design que personne n'avait posé, et la règle « pas de headshot assisté » **contredit
> explicitement** « je ne veux pas de réduction de dégât ».*
>
> *Ce qui reste vrai de cet épisode et ne doit pas être reperdu :*
> - *Le piège `12_PIEGES §6.24` — « une aide conditionnée à *n'avoir rien touché* est morte dans un
>   niveau fermé » — reste valable pour toute future condition de ce type. Le trace unique le rend
>   sans objet ici : il n'y a plus de gate du tout.*
> - *La sortie de `ResolveShot` doit renvoyer le **vrai** `bBlockingHit` du trace, jamais un littéral,
>   sinon le faisceau cesse de s'arrêter sur les murs et file à 15 000 uu. Cas 5 ci-dessus.*
> - *`SPEC_ENEMIES` : le rayon de la `HeadHitbox` (50 uu) a été dimensionné pour battre la
>   demi-diagonale du corps (`12_PIEGES §6.23`), indépendamment de tout ceci.*

## 12. Checklist de validation manuelle
**Laser** — [ ] 1 clic = 1 tir, maintenir ne tire pas en rafale · [ ] le beam part du canon et finit sous le
réticule · [ ] tir à bout portant contre un mur : ne traverse pas · [ ] tirer en pleine course ne change ni
vitesse ni trajectoire · [ ] une cible à `Laser_Range` est touchée · [ ] le recoil bouge la caméra mais le tir
suivant part au centre du réticule.

**Mercy de visée (§11)** — [ ] je ne vois **pas** que le tir est épaissi : rien ne touche que je sache
avoir raté · [ ] un tir qui passe « à 4 px » d'un ennemi en pleine course touche · [ ] les headshots
sont toujours ceux que je vise, et ils tuent en un coup (aucun `−50` surprise sur un tir de tête).

**Heat — jauge de discipline de tir (§4, `D58`)** — [ ] **tirer dans un mur fait monter la jauge** ·
[ ] **toucher une cible au corps ne la fait pas bouger du tout** · [ ] un **headshot** la fait redescendre
d'un cran net et visible · [ ] **au-dessus de `Heat_CoolSpeedThreshold` la jauge fond en continu**, en
dessous elle ne bouge pas d'elle-même · [ ] rester immobile chaud : la jauge **ne redescend jamais toute
seule** · [ ] la barre pulse à `Heat_WarningThreshold` et le **coût de style s'affiche** ·
[ ] **jauge pleine : le tir part quand même** — vider un chargeur entier dans un mur ne coupe **jamais**
le tir · [ ] melee / dash / slide / wall ride / saut : **jamais bloqués**, à aucun moment ·
[ ] **aucun clic refusé, aucun son de deny, aucune icône de verrou, aucun crosshair barré** nulle part ·
[ ] l'arme **ne pend jamais**, elle reste pointée · [ ] mourir remet la chaleur à 0.

**Heat — affichage provisoire du coût (J9, dette J18)** — [ ] la valeur affichée est bien
`Style_Loss_Heat` **telle quelle**, en unités de style par seconde, pas un pourcentage de score inventé ·
[ ] elle apparaît **exactement** quand `CurrentHeat` franchit `Heat_WarningThreshold`, et disparaît
quand il repasse dessous.

**Heat — ressenti (R8)** — [ ] la jauge me dit **« tu arroses »**, jamais **« attends »** ·
[ ] je n'ai **jamais** eu à arrêter de tirer pour laisser refroidir · [ ] j'ai eu envie de viser la
tête **pour refroidir**, pas seulement pour les dégâts.

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
| 2 | **La capsule englobe la tête** : le trace unique retourne le premier bloquant, donc la capsule (corps) même quand le joueur vise le crâne → headshot impossible. | La `SphereCollision` `Head` doit **déborder** la capsule au niveau de la tête (elle est volontairement généreuse, §5.1) ; se règle dans le viewport en 30 s. Si un cas résiduel apparaît en playtest, passer le trace de §3.3 en variante `Multi` et **prioriser `HeadHitbox`** si les deux composants sont touchés. |
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
