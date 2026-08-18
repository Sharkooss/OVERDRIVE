# SPEC — ENNEMIS

> `BP_EnemyBase`, les 3 archétypes, perception, knockback, placement. **Aucun chiffre ici** : les valeurs vivent dans
> `Docs/07_TUNING.md` — `§13` (ennemis), `§10` (perte de vitesse), `§12` (melee/wall slam), `§14` (score/style), `§17`
> (niveaux). Assets : `05_ARCHITECTURE §2`. Données : `08_DATA_SCHEMAS`. Blueprint uniquement (R1).
> **Couleurs : `ArtDirection/PALETTE.md` fait autorité, par token, sans exception** — l'ennemi est
> `OD_Amber_Enemy` (`11_ARBITRAGES D3`). Rendu **éclairé**, Lumen et VSM actifs (`11_ARBITRAGES D2`) : §2.2.

## 1. Rôle des ennemis dans un jeu de vitesse

L'ennemi d'OVERDRIVE n'est pas un adversaire : c'est un **élément de level design mobile**.

| Fonction | Traduction en jeu |
|---|---|
| **Rythme** | un pic d'attention toutes les 5–10 s de course |
| **Obstacle** | occuper un volume, forcer un changement de trajectoire — pas un arrêt |
| **Décision** | « je tue, je contourne, ou je slam ? » à 3000 uu/s, en < 0.5 s |

**Contrat de vitesse** : `TimeToKill` cible par archétype (`§13`). Un ennemi qui survit au-delà est un bug de design, pas
un défi.

**Ce qu'un ennemi ne doit JAMAIS faire.** (1) **Arrêter le joueur** : pas de grab, stun, root — la punition est une **perte
de vitesse** (`§10`), jamais une perte de contrôle. (2) **Tirer sans télégraphe.** (3) **Toucher à coup sûr** : aucun
hitscan, aucun homing (`Projectile_Homing = 0`). (4) **Poursuivre hors de sa zone** (§3). (5) Esquiver, se couvrir,
flanquer, appeler des renforts : zéro IA tactique. (6) **Être plus rapide que le joueur.** (7) **Exiger de la précision.**

## 2. `BP_EnemyBase`

`Enemies/Base/BP_EnemyBase`, parent **Character** (on garde le CharacterMovement, `05_ARCHITECTURE §1`).
```
BP_EnemyBase (Character)
├── CapsuleComponent   [root] preset OD_Enemy — hitbox CORPS
│    └── SkeletalMeshComponent   collision NoCollision (jamais tracé)
│         ├── HeadHitbox      (Sphere) socket "head" — canal Weapon
│         └── WeakPointHitbox (Sphere) socket "back" — désactivé sauf Tank
├── BPC_Health   ├── BPC_KnockbackReceiver (§9)   └── CharacterMovementComponent
```
**Décision hitbox — tranchée, `SPEC_COMBAT §3.3 / §5.1` s'y aligne** : ni trace par bone, ni Physics Asset — deux
`Sphere Collision` + la capsule. `SkeletalMeshComponent` en **`NoCollision`**, la **capsule** porte le corps, la
`SphereCollision` **`HeadHitbox`** (socket `head`, canal `Weapon`) porte le headshot. Aucun `PHYS_Enemy_*` à produire
(aucune simulation physique dans le projet, §8), trace bien moins chère, hitbox tête **généreuse et réglable
indépendamment du mesh** (indispensable à 3000 uu/s). `BP_LaserWeapon` lit le **Hit Component** — jamais `Hit.BoneName` —
et renseigne `HitBone = Head | WeakPoint | Body`. Les enfants **ne redéfinissent que le comportement, pas les stats**
(`05_ARCHITECTURE §2`) : un `float Damage` dans un enfant est un bug.

| Dans la base (jamais redéfini) | Dans `BP_Enemy_<Type>` |
|---|---|
| Lecture du `DA_EnemyData` + application des stats | Comportement (FSM ou StateTree) |
| `BPI_Damageable`, mort, dissolve, nettoyage | Pattern d'attaque + télégraphe |
| Flash matériau, hit VFX/SFX, knockback, wall slam | Animation d'attaque |
| Activation/désactivation (§3), `BPI_ScoreEvent` | — |

**Lecture du `DA_EnemyData` au `BeginPlay`.** `EnemyData` : `PDA_EnemyData`, `Instance Editable`, Category `Combat`,
assignée dans les Class Defaults de chaque enfant (`DA_Enemy_Grunt`/`_Shooter`/`_Tank`).
```
BeginPlay
├─ IsValid(EnemyData)? ─non─▶ Print "MISSING EnemyData" + DestroyActor + return
├─ ApplyEnemyData() : Health.Initialize(MaxHealth) · MaxWalkSpeed = MoveSpeed
│    · Mesh.SetSkeletalMesh / SetAnimInstanceClass   ← soft refs chargées ICI (§12.6)
│    · KnockbackReceiver.Resistance / .bCanBeWallSlammed
│    · WeakPointHitbox.SetCollisionEnabled( EnemyType == Tank )
│    · MID_Body = CreateDynamicMaterialInstance(0)   ← CACHÉ UNE FOIS (§7, §12.5)
├─ SetActorTickEnabled(false)   ← Tick OFF par défaut (06_CONVENTIONS §4.6)
├─ RegisterWithLevelManager()   ← l'ennemi s'inscrit ; il ne cherche JAMAIS le joueur
└─ SetActivationState(Dormant)  ← §3
```
`AIControllerClass` et `StateTree` viennent aussi du DataAsset : un seul `BP_AIController_Enemy` sert les 3 archétypes
(possession + `MoveTo` + hébergement du StateTree).

**`BPI_Damageable` — 4 fonctions, signature définitive** (elle vaut pour tout le projet, `05_ARCHITECTURE §2` compris) :
```
ApplyDamage    (DamageInfo: S_DamageInfo)  → (bKilled: bool, DamageApplied: float)
ApplyKnockback (Impulse: Vector, Instigator: Actor)
IsAlive        ()                          → bool
GetHealthRatio ()                          → float          [pure]
```
`S_DamageInfo` (`08_DATA_SCHEMAS §2`) porte `HitLocation`, `HitNormal`, `HitBone`, `KnockbackImpulse` et
`SpeedPenaltyPercent` : l'ennemi a besoin de `HitLocation/Normal` (orientation du VFX) et l'appelant du reste.
**`ApplyKnockback` est appelée APRÈS `ApplyDamage`, par l'appelant** (`SPEC_COMBAT §7.2 / §8`), jamais depuis
`ApplyDamage` : le knockback doit s'appliquer même si la cible est morte, et c'est l'appelant qui sait s'il veut
projeter (le laser non, le melee oui).
```
ApplyDamage(Info) : if bIsDead → return                  ← garde anti double-kill
  Final = Info.Amount
  Head      : bHeadshotIsLethal ? Final = Health.Current : Final ×= HeadshotMultiplier
  WeakPoint : Final ×= HeadshotMultiplier                ← Tank, §6
  Health.ApplyDamage(Final) · PlayHitFeedback (§7)
  if Health.Current <= 0 → Die(Info)                     ← §8, entièrement géré par la base

ApplyKnockback(Impulse, Instigator) : délègue à BPC_KnockbackReceiver (§9)
                                       ← appel SÉPARÉ, à l'initiative de l'appelant
```

### 2.1 Lisibilité sur fond blanc — silhouette foncée, émissif orange

> **C'est le point critique de la v2.** Le monde est une ville **blanche en plein jour**
> (`11_ARBITRAGES D2`, `PALETTE.md §1`). Un ennemi clair sur une ville blanche est **invisible**.
> La contrainte de la v1 (« fond sombre, l'émissif fait tout ») est **caduque** : ici c'est la
> **valeur foncée** qui porte la silhouette, et l'émissif qui porte l'identité.

**Recette d'un ennemi, non négociable** — couleurs par token, `PALETTE.md` fait autorité :

| Couche | Traitement | Rôle |
|---|---|---|
| **Corps / silhouette** | valeur **foncée** : `OD_Navy_Deep` dominant, ombres en `OD_Navy_Ink` | c'est ça qui rend l'ennemi visible. Aucun panneau clair, aucun blanc sur le corps |
| **Visière** | émissif **`OD_Amber_Enemy`**, la surface la plus lumineuse de l'ennemi | « c'est hostile », lisible en périphérie |
| **Points d'articulation** (épaules, hanches, poignets, chevilles) | petits accents émissifs `OD_Amber_Enemy` | **ils décrivent le mouvement** : à 3000 uu/s on lit une pose par ses points, pas par sa silhouette complète |
| **Télégraphe d'attaque** | montée d'intensité de l'orange, puis `OD_Red_Danger` au moment où le coup part | l'ambre dit « il est là », le rouge dit « ça va me toucher » (`11_ARBITRAGES D3`) |
| **Point faible du Tank** | `OD_Amber_Heat` pulsé (§6) | se distingue de l'ambre de base par sa **pulsation**, pas par sa teinte |

**`OD_Red_Enemy` et `OD_Cyan_Accent` n'existent plus** (`11_ARBITRAGES D3`) : le rouge est passé aux
**surfaces de traversée**, le cyan a disparu de la palette. **`OD_Amber_Enemy` est la seule couleur
d'ennemi du jeu**, pour les 3 archétypes, les projectiles et les boss.

**Garantir la lecture sur les deux fonds** — un ennemi est vu tantôt devant un mur blanc, tantôt
découpé sur le ciel bleu. Les deux cas se traitent différemment et **les deux doivent passer** :

| Fond | Ce qui porte la lecture | Parade |
|---|---|---|
| **Mur / sol blanc** (`OD_White_Structure`) | le **contraste de valeur** : navy sur blanc, écart maximal | rien à faire de plus. C'est le cas facile, et c'est pour lui qu'on choisit une silhouette foncée |
| **Ciel bleu** (`OD_Sky_Blue` → `OD_Sky_Pale`) | l'écart de valeur se resserre, et le navy vire vers la même famille froide que le ciel | c'est **l'émissif orange** qui sauve la lecture : teinte **chaude**, absente du ciel comme du décor. D'où le choix de l'ambre (`PALETTE.md §3`). L'outline `OD_Navy_Ink` du post-process (`11_ARBITRAGES D2`) referme le contour |
| **Contre-jour** (ennemi entre le joueur et le soleil) | tout s'aplatit | l'émissif ne dépend pas de la lumière reçue : la visière et les points d'articulation restent lisibles. C'est le seul élément fiable dans ce cas |

> **Test obligatoire (R8)** : poser le même ennemi devant un mur blanc, sur fond de ciel, et à contre-jour.
> S'il n'est pas identifiable **à `DetectionRange`** dans les trois cas, le problème est la **valeur du corps**,
> jamais l'intensité de l'émissif — la monter ne fait que délaver l'ennemi sur fond clair.

### 2.2 Rendu : les ennemis sont ÉCLAIRÉS et projettent une ombre

Le rendu est **éclairé, Lumen et Virtual Shadow Maps actifs** (`11_ARBITRAGES D2`). Toute mention
d'Unlit dans les anciennes versions de cette spec est caduque. Conséquences concrètes :

- **L'ombre portée est un indice de position gratuit — c'est un gain, pas un coût.** Un ennemi en
  hauteur projette son ombre au sol : le joueur voit qu'il y a quelqu'un **avant** de lever les yeux,
  et sait *où*. C'est exactement l'information que §10 demande au level designer de garantir, obtenue
  ici sans une ligne de Blueprint. **`Cast Shadow` reste activé sur le `SkeletalMeshComponent` des 3 archétypes.**
- Le mesh est en **`Movable`** (il bouge réellement) — c'est l'exception assumée à la règle
  « tout est `Static` » de `SPEC_LEVELDESIGN §12`. C'est aussi pour ça que le budget d'ennemis
  simultanés (`Enemy_MaxEngagedSimultaneous`, `§13`) se surveille au **GPU** autant qu'au CPU :
  chaque ennemi visible invalide une page de VSM.
- Un ennemi `Dormant` hors écran ne coûte pas d'ombre (`Only Tick Pose When Rendered`, §12.4).
- **Le dissolve de mort (§8) éteint l'ombre en même temps que le mesh** : pas d'ombre fantôme après la mort.

## 3. Perception & activation

**Problème** : 15–30 ennemis par niveau (`§17`), joueur à 2000–5000 uu/s. 30 ennemis qui tournent en Tick, castent vers le
joueur et tracent leur ligne de vue = le budget CPU du jeu.

**Décision : pas d'`AIPerception`. Check de distance centralisé.**

| | `AIPerception` | **Distance check centralisé** |
|---|---|---|
| Setup | composant + `StimuliSource` joueur + config des sens | 1 timer dans `BP_LevelManager` |
| Coût | update de sens générique par acteur | 1 `DistSquared` par ennemi |
| Ce qu'on en utilise | ~5 % (Sight, un seul stimulus) | 100 % |
| Réactivité à 3000 uu/s | latence de refresh interne | contrôlée par nous |

`AIPerception` est un outil d'infiltration à N stimuli. Ici il y a **un seul stimulus, le joueur**, et une seule question :
*est-il assez près et visible ?* **Zéro `AIPerceptionComponent` dans le projet.**
```
        dist < DetectionRange && LOS            Dormant : Tick off · UnPossess · anim OnlyTickPoseWhenRendered
Dormant ──────────────────────────▶ Engaged    Engaged : Tick off (timers) · possédé · FSM/ST actif · anim full
   ▲                                   │       Collision ON dans les deux cas → tuable avant son éveil
   └── dist > DetectionRange×Hysteresis ┘  OU dépassé de DeactivateBehindDistance
```
`BP_LevelManager` tient `RegisteredEnemies` + un timer à `EnemyScan_Rate` (`§13`) :
```
ScanEnemies()   ← timer ; jamais de Tick ni de GetAllActorsOfClass
  PlayerLoc = CachedPlayerPawn.GetActorLocation()      ← cache pris au BeginPlay
  foreach E: d2 = DistSquared(PlayerLoc, E.Location)   ← squared, jamais de sqrt
     if d2 < E.DetectionRangeSq && !E.bEngaged && HasLineOfSight(E) → Engaged
     else if d2 > E.DetectionRangeSq × Hysteresis && E.bEngaged     → Dormant
```
- **LOS** : un `LineTraceByChannel` (Visibility) **uniquement** pour les candidats à l'activation, jamais pour un engagé
  ni un hors-portée. Plafond `MaxLOSTracesPerScan` **[À CALIBRER]**, round-robin.
- **Volumes** : `BP_EnemyActivationVolume` (Box Trigger) force `Engaged` sur un groupe entier — pour les arènes, où tout
  doit s'allumer d'un coup.
- **Derrière le joueur** : si `Dot(PlayerVelocity, EnemyLoc − PlayerLoc) < 0` et `dist > DeactivateBehindDistance` **[À
  CALIBRER]** → `Dormant` immédiat. À 3000 uu/s, un ennemi dépassé est mort pour le joueur : il ne doit plus coûter un
  cycle.

**Budget** : `Enemy_MaxEngagedSimultaneous` `Engaged` simultanés au maximum (`§13`) · ≤ 1.5 ms CPU IA/frame ·
≤ 2 traces/frame · **0** Tick actif (hors `Launched`, §9). Contrôle : `stat game`, `stat anim`.

## 4. Grunt — `BP_Enemy_Grunt`

**Fantasme** : la cible qui explose. Il existe pour être détruit sans ralentir. Stats : `§13` colonne Grunt. Headshot =
kill. `TimeToKill` < 0.3 s.

**Décision : machine à états simple dans le BP, pas de StateTree.** 3 états — `05_ARCHITECTURE §2` : *« moins de 4 états →
simple machine à états, ne pas sur-outiller »*. Pas de `ST_Enemy_Grunt`.
```
        Engaged           dist < AttackRange           fin d'attaque
Dormant ───────▶ Chase ───────────────────▶ ChargeAttack ──────────▶ Chase
                  ▲                              │
                  └────── raté / hors portée ◀────┘   (AttackCooldown)
```
- `Chase` : `MoveToActor(Player, AcceptanceRadius)` **une fois**, ré-émis par timer à `GruntRepathRate` **[À CALIBRER]**.
  Jamais de `MoveTo` en Tick.
- `ChargeAttack` : il **se fige** pendant `Grunt_ChargeWindup` (`§13`), puis `LaunchCharacter` en ligne droite vers la
  position **mémorisée au windup**, sans correction — un joueur qui bouge esquive toujours. Sphère de contact pendant la
  charge → `AttackDamage` + `PlayerSpeedPenaltyPercent` (`§10`), **une seule touche possible par charge**.

**Lisibilité à haute vitesse** : silhouette la plus petite et la plus anguleuse des trois (identifiable en 3 frames),
**foncée** (§2.1) · visière `OD_Amber_Enemy` constante · flash + son court à l'entrée du windup (`ATT_Enemy3D`) · recul
d'anticipation pendant le windup · **il ne tire jamais** — voir un Grunt = « qu'il ne me touche pas au corps », sans
ambiguïté. Son ombre portée au sol le trahit avant qu'il n'entre dans le champ (§2.2).

## 5. Shooter — `BP_Enemy_Shooter`

**Fantasme** : la mine spatiale. Il ne vous vise pas, il **remplit un couloir**. Stats : `§13` colonne Shooter. Headshot =
kill. `TimeToKill` < 0.4 s.

**Décision : StateTree `ST_Enemy_Shooter`** (5 états ≥ 4 → l'outil est justifié).
```
Dormant ─▶ Acquire ─▶ Telegraph ─▶ Fire ─▶ Recover ─┐
             ▲  ▲          │                        │
             │  └─ interruption si touché (§7)       │  (AttackCooldown)
             └──────────────────────────────────────┘
```
- `Acquire` : **ne se déplace pas** (repositionnement latéral court seulement si la LOS est perdue). Rotation limitée à
  `ShooterTurnRate` **[À CALIBRER]** : il ne peut pas suivre un joueur qui le contourne à 3000 uu/s. **C'est voulu.**
- `Telegraph` : `Shooter_TelegraphTime` (`§13`) — laser de visée fin **à cœur foncé** (§2.1 : un trait purement lumineux
  disparaît sur un mur blanc), montée d'émissif, son qui monte. Le joueur doit pouvoir dire *« ça part »* avant que ça parte.
- `Fire` : **1 `BP_EnemyProjectile` par cycle** au MVP. `Recover` : `AttackCooldown`.

**`BP_EnemyProjectile`** (`Enemies/Shared/`) — root `SphereComponent` de rayon `Projectile_Radius`, preset
`OD_EnemyProjectile` · `ProjectileMovementComponent`, `InitialSpeed = MaxSpeed = Projectile_Speed`, gravité 0 ·
`InitialLifeSpan = Projectile_LifeTime` · **homing 0** (`§13`), non négociable au MVP · sweep + **CCD** (§12.3),
ignore ennemis et projectiles.

**Lecture du projectile sur fond clair — c'est du gameplay, pas de la décoration.** Le joueur *doit* voir
le projectile arriver : c'est la condition d'existence de la mécanique d'esquive (« garantie d'esquive »
ci-dessous). Sur une ville blanche en plein jour, **une boule lumineuse additive disparaît purement et
simplement**. Construction imposée, en trois couches :

| Couche | Traitement | Pourquoi |
|---|---|---|
| **Noyau** | mesh sphère low-poly **foncé** (`OD_Navy_Ink`), opaque, non additif, échelle visuelle ≥ rayon de collision | c'est **lui** qui rend le projectile visible devant un mur blanc. Le noyau est l'objet ; le reste est de la lecture |
| **Halo** | anneau/billboard **`OD_Amber_Enemy`** serré autour du noyau | identité « hostile » (§2.1) + lecture quand le projectile passe devant une zone d'ombre |
| **Trail** | `NS_EnemyProjectile_Trail` **plus long que la distance parcourue en 0.3 s**, en `OD_Amber_Enemy` | dit **d'où ça vient**, donc de quel côté esquiver |

Un projectile qui « disparaît » en playtest se corrige en assombrissant le **noyau**, jamais en montant
l'intensité du halo : sur fond clair, monter l'émissif délave et aggrave le problème.

**Prédiction de tir (lead) : NON.** Il tire vers la position du joueur **à l'instant du tir** ; le champ
`Projectile_LeadFactor` (`§13`) vaut **0 au MVP**. Trois raisons : (1) un impact coûte
**−45 % de vitesse** (`§10`) — une punition de cette taille infligée par un tir à visée corrigée serait de la taxe, pas du
gameplay ; (2) sans lead, le projectile est un **objet posé sur une trajectoire**, qu'on esquive en changeant de ligne
(strafe, dash, wall ride) : exactement la mécanique qu'on veut entraîner ; (3) il reste dangereux là où il doit l'être,
**quand on fonce droit sur lui**.

**Garantie d'esquive à 3000 uu/s** — contrainte vérifiée en jeu (§11) : `FenêtreUtile = (DistanceDeTir /
Projectile_Speed) − Shooter_TelegraphTime ≥ 0.35 s` **[À CALIBRER]**. Trop courte → baisser `Projectile_Speed` ou augmenter
la distance de placement (§10). **On ne corrige jamais en réduisant les dégâts** : le problème est temporel.

**Impact sur le joueur** : `AttackDamage` → `BPC_Health` · `ApplySpeedPenaltyPercent(PlayerSpeedPenaltyPercent, Reason)`
→ dispatcher `OnSpeedPenaltyApplied(OldSpeed, NewSpeed, Percent, Reason)` (−45 %, `§10`)
puis `SpeedLoss_RecoveryGrace` (pas de décroissance juste après → on peut rebondir) · `E_StyleEvent::TookDamage` (`§14`) ·
`Shake_TakeDamage` + flash écran · `NS_ProjectileImpact` + destroy. Sur géométrie : VFX + destroy. Sur un autre ennemi :
**il traverse** (pas de friendly fire).

## 6. Tank — `BP_Enemy_Tank`

**Fantasme** : le péage. Il ne vous tue pas, il vous **coûte du temps**. Stats : `§13` colonne Tank. Headshot **non
létal** (×3). `TimeToKill` < 2 s.

**Décision : StateTree `ST_Enemy_Tank`** (4 états).
```
Dormant ─▶ Advance ─▶ SlamWindup ─▶ Slam ─┐   Advance : marche lente, trajectoire prévisible,
              ▲                            │   jamais de repath agressif
              └────────────────────────────┘   (AttackCooldown)
```
- `SlamWindup` : `TankWindupTime` **[À CALIBRER]**, le plus long télégraphe du jeu — bras levés + décalque/anneau au sol
  marquant la zone d'impact **avant** le coup.
- `Slam` : AoE au sol, `AttackDamage` + **−60 %** de vitesse (`§10`, ligne melee).

**Résistances** : `KnockbackResistance` proche de 1 (`DA_Enemy_Tank`) → il bouge à peine · `bCanBeWallSlammed = true` mais
il ne part pas loin · wall slam **non létal** (`WallSlam_Damage` < `MaxHealth` Tank, `§12`/`§13`) · stagger **uniquement
sur point faible** (§7).

**Point faible** : `WeakPointHitbox` au socket dorsal, **émissif `OD_Amber_Heat` et pulsant** — la **pulsation** est ce
qui le distingue de l'ambre de visière (§2.1), pas la teinte —, `HeadshotMultiplier` appliqué. Conséquence :
on tue un Tank **en le contournant**, donc en bougeant (wall ride latéral, dash de contournement, slide sous le slam) —
c'est le seul ennemi qui récompense explicitement le kit de mouvement.

**La décision qu'il impose** : le tuer (temps perdu, mais `ScoreBase` élevé + style) · le contourner (vitesse gardée, zéro
score, il reste dans le dos) · le slammer (gratuit si un mur est proche, mais ne le tue pas). Un Tank **ne doit jamais être
un mur obligatoire** : s'il bloque le seul passage, il n'impose plus une décision mais un arrêt → §10.

## 7. Réaction aux dégâts

| Élément | MVP | Détail |
|---|---|---|
| Flash de matériau | **oui** | `MID_Body.SetScalarParameter("HitFlash",1)` + Timeline retour à 0 sur `HitFlash_Duration` **[À CALIBRER]**. MID créé **une fois** au BeginPlay |
| Hit VFX / SFX | oui | `HitVFX` à `HitLocation`, orienté sur `HitNormal` ; son distinct Head / WeakPoint |
| Hit stop | **joueur uniquement** | `HitStop_Headshot` (`§16`) — l'ennemi ne gèle pas |
| Stagger | **Tank uniquement**, sur point faible | Grunt/Shooter meurent trop vite pour qu'une anim de hit existe |
| Interruption | **Shooter : oui** — un dégât pendant `Telegraph` annule le tir, « supprimer » un Shooter devient une vraie option | **Grunt : non** (ce qui part arrive). **Tank : non pendant `Slam`**, oui pendant `SlamWindup` sur point faible |
| Popup de dégâts | **NON** | illisible à 3000 uu/s ; pollue un champ visuel déjà chargé (speed lines, aberration) ; le feedback arcade passe par flash + son + hit stop. Score et style s'affichent au **HUD** (`SPEC_UI_HUD`), pas dans le monde |

**Règle** : le feedback de hit doit être lisible **en périphérie**. Si Louis doit regarder l'ennemi pour savoir qu'il l'a
touché, le feedback a échoué.

## 8. Mort

**Décision : dissolve, pas de ragdoll.**

| | Ragdoll | **Dissolve (retenu)** |
|---|---|---|
| Assets | 1 `PHYS_Enemy_*` par archétype à régler | aucun |
| Coût | simulation physique × N cadavres | 1 scalaire animé |
| Arène | corps qui traînent = bruit visuel + collisions parasites à 3000 uu/s | scène propre en < 1 s |
| Style toon low-poly | ragdoll mou = anti-toon | dissolve émissif = raccord direct avec la DA |
| Timing | imprévisible | déterministe, cadençable au frame près |

**`M_Toon_Enemy`** expose `DissolveAmount` (0→1) + masque de bruit + bord émissif — c'est **ce matériau-là** qui porte le
paramètre, pas `M_Toon_Base` ni un `M_VFX_Dissolve` séparé. `Die()` lance une Timeline sur `MID_Body` pendant
`Death_DissolveDuration` (`§13`). **`Corpse_LifeSpan` n'existe plus** : `Death_DissolveDuration` est le seul délai entre
la mort et le `DestroyActor`.
```
Die(Info) : bIsDead = true · Dormant + UnPossess + StopMovement
  Capsule.SetCollisionEnabled(NoCollision)   ← T+0 : plus aucun cadavre percutable
  NotifyScoreEvent (BPI_ScoreEvent → GS_Overdrive) : ScoreBase + bonus headshot / wall slam (§14) ;
     E_StyleEvent Kill | Headshot | MeleeKill | WallSlamKill | SlideKill | AirKill
  DeathVFX + DeathSFX · Timeline Dissolve 0→1 (Death_DissolveDuration) → DestroyActor()
```
**Le score part avant le VFX** (si une frame saute, on ne perd jamais un kill) · **`bIsDead` empêche le double comptage**
: laser + wall slam simultanés = 1 kill, type retenu = le premier reçu · **pas de pooling** (`05_ARCHITECTURE §6`),
ennemis pré-placés et jamais re-spawnés · **timing perçu** : la mort est validée par le son + le flash **avant** la fin du
dissolve — on n'attend jamais la fin d'une animation pour savoir qu'on a tué.

## 9. `BPC_KnockbackReceiver`

Côté ennemi : reçoit l'impulsion de `BPC_Melee`, gère le vol et l'impact mural. Valeurs : `§12` (`Melee_Knockback`,
`Melee_KnockbackUp`, `WallSlam_MinImpactSpeed`, `WallSlam_Damage`, `WallSlam_DamagePerSpeed`, courbe
`CF_WallSlamDamageBySpeed`) et `§13` (`WallSlam_MaxNormalZ`).

**Point d'entrée : `ApplyKnockback(Impulse, Instigator)`** de `BPI_Damageable` (§2), appelée **après** `ApplyDamage`
par l'appelant.
```
Grounded ──ApplyKnockback──▶ Launched ──Hit(mur)──▶ WallSlam ──▶ mort ou Grounded
      ▲                          └──── Landed / LaunchTimeout ────────┘

ApplyKnockback(Impulse, Instigator)
  if Resistance >= 1.0 → return                                 ← Tank : pas de vol
  Impulse = Impulse × (1 − Resistance)
  if Impulse.Size < KnockbackMinImpulse [À CALIBRER] → return    ← pas de micro-vol ridicule
  StopMovement + UnPossess · SetMovementMode(Falling)            ← Falling AVANT le launch (§12.8)
  LaunchCharacter(Impulse + Up × Melee_KnockbackUp, XY, Z)
  Capsule.SetNotifyRigidBodyCollision(true)                      ← Simulation Generates Hit Events
  State = Launched · LauncherActor = Instigator · SetActorTickEnabled(true)      ← SEUL Tick autorisé
  SetTimer(LaunchTimeout [À CALIBRER]) → EndLaunch()

OnCapsuleHit(...)   ← événement, pas de trace en Tick
  if State != Launched → return ; ImpactSpeed = |Velocity| au hit
  bIsWall = Abs(Hit.ImpactNormal.Z) < WallSlam_MaxNormalZ (§13)               ← mur vs sol
  if bIsWall && bCanBeWallSlammed && ImpactSpeed > WallSlam_MinImpactSpeed
     Damage = CF_WallSlamDamageBySpeed.Eval(ImpactSpeed)
     Owner.ApplyDamage({Amount:Damage, Type:WallSlam, Instigator:LauncherActor}) + NS_WallSlam
  EndLaunch() → Tick off, hit events off, re-Possess si vivant, retour Engaged
```
**Règle du mur** : c'est `Abs(Hit.ImpactNormal.Z) < WallSlam_MaxNormalZ` (`§13`) qui distingue un mur d'un sol, et rien
d'autre — pas de comparaison au `WalkableFloorAngle`. **`SPEC_COMBAT §7.3` s'aligne sur cette règle.**

`KnockbackResistance` (0–1) vient du `DA_EnemyData` : Grunt/Shooter ≈ 0 (envol franc, c'est le spectacle du melee), Tank ≈ 1.
L'upgrade **`Impact`** (+50 %, `§15`) multiplie l'impulsion **avant** l'application de la résistance.
**Crédit du kill** : `LauncherActor` est conservé pendant tout le vol — un ennemi qui meurt d'un wall slam 2 s après le coup
crédite quand même le joueur (`Style_Gain_WallSlamKill`, `§14`).

## 10. Placement dans les niveaux (règles pour le level designer)

**Densité** — `§17` : 15–30 ennemis/niveau, en **poches de 3–6**, jamais étalés. Une poche = un pic de rythme ; entre deux
poches, **au moins 3 s de course pure**. Grunts majoritaires, Shooters en second, **Tank ≤ 2** par niveau.

**Distance minimale à l'entrée d'une zone à haute vitesse** : `DistanceMin = VitesseDeCroisièreDeLaZone (uu/s) ×
Placement_MinReactionTime (s)` (`§13`). Plus près = **injuste par construction** : le joueur
percute avant d'avoir vu. Ça se mesure en courant la zone, pas sur le plan.

| Ligne de vue — règle | Raison |
|---|---|
| Shooter visible **avant** d'être à portée de tir | sinon le télégraphe ne sert à rien |
| Shooter tire **en travers** de la trajectoire, jamais dans son axe | un tir frontal n'est pas esquivé, il est subi |
| Aucun ennemi en angle mort en sortie de virage rapide | punirait la vitesse au lieu de la récompenser |
| Aucun ennemi hors champ au moment où il attaque | pas de dégât venu de nulle part |
| Tank **à côté** de la ligne idéale, pas dessus | il impose une décision, pas un arrêt |
| Élévation variée (plateformes, balcons) | cibles pour `AirKill` et tir en wall ride |

**Injuste (interdit)** : ennemi sur la ligne d'un couloir de vitesse sans échappatoire latérale · Shooter **derrière** le
joueur pendant la traversée · deux Tanks encadrant l'unique passage · activation à moins de `DistanceMin` · ennemi sur un mur
de wall ride ou dans le volume d'une trajectoire de wall ride · poche de combat collée à la sortie d'une section de mouvement
pur · **spawn dynamique en cours de run** : tout est pré-placé, `BP_LevelManager` ne fait qu'**activer**.

## 11. Checklist de validation manuelle

> R8 : l'agent ne peut pas juger du feeling. En main, dans `L_Sandbox_Movement` puis en niveau réel.

**Lisibilité** — [ ] j'identifie l'archétype à 3000 uu/s **avant** d'être à portée · [ ] je distingue les 3 à la
silhouette seule, sans la couleur · [ ] je vois le télégraphe du Shooter et j'ai le temps de changer de ligne · [ ] je
vois le tir arriver et je sais d'où il vient · [ ] le point faible du Tank est repérable en mouvement.

**Lisibilité sur fond clair (§2.1)** — [ ] l'ennemi se détache devant un **mur blanc** · [ ] il se détache découpé sur
le **ciel bleu** · [ ] il se détache **à contre-jour** · [ ] son **ombre portée** me signale sa présence avant de le voir
(§2.2) · [ ] le **projectile du Shooter** reste visible sur toute sa trajectoire, y compris devant une façade blanche en
plein soleil · [ ] aucun ennemi ne porte de blanc ni de magenta (couleur du joueur), aucun décor ne porte d'ambre.

**Contrat de vitesse (`§13`)** — [ ] Grunt < 0.3 s, Shooter < 0.4 s, Tank < 2 s · [ ] headshot Grunt = kill instantané à
toutes distances · [ ] aucun ennemi ne m'a **arrêté**, seulement ralenti · [ ] après un projectile encaissé je récupère ma
vitesse sans frustration (`SpeedLoss_RecoveryGrace`).

**Feedback & systèmes** — [ ] je sais que j'ai touché sans regarder l'ennemi · [ ] je sais que j'ai tué (son de mort ≠ son
de hit) · [ ] le dissolve est fini avant que je repasse au même endroit · [ ] un wall slam est **jouissif** (sinon
augmenter le VFX avant les dégâts) · [ ] rien ne bouge avant que j'entre dans la zone, et un ennemi dépassé cesse toute
activité · [ ] `stat game` sous le budget (§3) sur la poche la plus dense · [ ] aucun ennemi ne traverse le sol ni ne
reste coincé après un knockback · [ ] aucun projectile ne me traverse sans dégât (à 5000 uu/s, en fonçant dessus) · [ ]
laser + wall slam simultanés = **1 seul** kill · [ ] zéro warning de compilation sur les 5 BP d'ennemi.

## 12. Pièges connus UE5

1. **Navmesh & grandes arènes** — `RecastNavMesh` à cette échelle explose en mémoire et en build. `Runtime Generation =
   Static`, `Cell Size` augmenté, **`NavMeshBoundsVolume` limité aux poches de combat** (les couloirs de vitesse n'en ont
   pas besoin).
2. **`Get All Actors Of Class` / `Get Player Character` répétés** — interdits (`06_CONVENTIONS §4.5`) : `BP_LevelManager`
   pousse la position du joueur (§3).
3. **Projectiles rapides qui tunnellent** — *(a)* le projectile traverse un mur → sweep + **CCD** sur la sphère ; *(b)* **le
   joueur à 5000 uu/s traverse le projectile** → `Use CCD` aussi sur sa capsule, et `Projectile_Radius` généreux.
4. **Anim skeletal hors écran** — `Only Tick Pose When Rendered` + **URO** sur chaque mesh d'ennemi. **Cette spec fait
   foi sur ce point** et `SPEC_COMBAT §13.3` s'y aligne : la hitbox de tête étant une `Sphere Collision` large montée sur
   socket, et non un corps de physics asset épousant le crâne, un léger retard de pose ne compromet pas la validité du
   headshot. Les deux optimisations restent donc **activées**.
5. **MID créé à chaque hit** — `CreateDynamicMaterialInstance` dans `ApplyDamage` fuit un matériau par impact. Le créer
   **une seule fois au `BeginPlay`** (§2, §7).
6. **Soft ref chargée en plein jeu** — `Load Synchronous` pendant la course = hitch. Ennemis pré-placés → chargement au
   `BeginPlay`, pendant le loading. Jamais depuis un event de gameplay.
7. **StateTree qui tourne à vide** — il s'évalue même loin ; c'est l'`UnPossess` en `Dormant` (§3) qui l'arrête, pas la
   désactivation du Tick.
8. **`LaunchCharacter` mangé par le CharacterMovement** — en `Walking` le sol absorbe l'impulsion en une frame. Passer en
   `Falling` **avant** le launch (§9).
9. **`OnComponentHit` silencieux** — `Simulation Generates Hit Events` coché *et* collision en `Block` ; en `Overlap` seul
   aucun `Hit` n'est émis → pas de wall slam. Ne jamais `DestroyActor` depuis cet event : `Die()` + Timeline (§8).
10. **RVO / évitement entre ennemis** — **désactivé** : cher, et ça fait « glisser » les ennemis les uns autour des autres,
    ce qui casse la lisibilité de leur trajectoire.
11. **Hitbox tête trop petite** — cause n°1 de « le headshot ne marche pas » : `HeadHitbox` se règle au ressenti à
    3000 uu/s, pas à la taille du crâne du mesh.
