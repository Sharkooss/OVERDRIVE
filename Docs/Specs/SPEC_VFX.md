# SPEC — VFX

> Portée : tous les `NS_*`, les matériaux VFX, le post-process de vitesse, le hit-stop et le screen shake.
> Hors portée : matériaux d'environnement (`SPEC_ART_DIRECTION.md`), HUD (`SPEC_UI_HUD.md`), audio (`SPEC_AUDIO.md`).
> **Aucune valeur de gameplay ici** : tout renvoie à `Docs/07_TUNING.md §16` par nom de clé. Blueprint only (CLAUDE.md R1), UE 5.8.
> Le juice est un **pilier**, pas une finition : un VFX P0 se produit en même temps que la feature, pas après.

---

## 1. Principes

| Principe | Conséquence concrète |
|---|---|
| **Lisibilité > beauté** | À 3000 uu/s le joueur voit un effet pendant ~0.1 s. Si l'info n'est pas lue en 3 frames, l'effet est raté. |
| **Le fond est CLAIR — un VFX pâle n'existe pas** | Voir la règle détaillée ci-dessous. C'est **la** contrainte n°1 de cette révision. |
| **Une couleur = une signification** | Le joueur doit identifier la source d'un flash à la couleur seule, sans lire le HUD. |
| **Silhouette d'abord** | Forme géométrique nette (anneau, éclat, trait). Jamais un nuage flou informe. |
| **Court et sec** | Durée par défaut ≤ 0.35 s pour tout feedback de combat. Ce qui traîne pollue l'écran suivant. |
| **Centre d'écran = sacré** | Rien d'opaque dans la zone centrale sanctuarisée **40 % × 40 %** (D22). Le crosshair et la cible priment. |
| **Coût constant** | Un effet ne doit jamais scaler avec le nombre d'ennemis à l'écran sans budget (cf. §6). |

### 1.1 Lisibilité inversée — la règle qui commande tout le reste

Le jeu se déroule dans une **ville blanche en plein jour**, sous un ciel bleu clair (D2, `PALETTE.md §1`).
La contrainte de la v1 (monde sombre → VFX lumineux) est **inversée** :

> **Un VFX blanc, pâle, ou simplement « très lumineux » est invisible.**
> Il faut qu'il soit **saturé**, **foncé**, ou les deux.

Trois règles opérationnelles, appliquées à **tous** les systèmes du catalogue §2 :

| Règle | Application |
|---|---|
| **1. Saturation avant luminosité** | La lisibilité vient de l'écart de teinte et de saturation avec le décor (`OD_White_Structure`, `OD_Sky_Blue`), pas de la brillance. Monter `EmissiveIntensity` sur une couleur pâle ne fait que la rapprocher du fond : ça la *supprime*. |
| **2. Tout VFX porte du foncé** | Chaque effet a soit un **cœur sombre** (`OD_Navy_Ink`), soit un **contour sombre** de 1–2 px, soit les deux. C'est le contour qui garantit la lecture devant un mur blanc **et** devant le ciel. `M_VFX_Unlit` et `M_VFX_Beam` exposent tous deux un paramètre `OutlineColor` / `OutlineWidth` pour ça (§7). |
| **3. Le blanc n'est plus un pic d'intensité** | L'ancien `OD_Bone_White` en cœur de headshot / wall slam est **supprimé** : le pic d'intensité se rend désormais par un **cœur `OD_Navy_Ink`** entouré d'un anneau saturé, et par la **taille**, pas par la brillance. Un flash blanc plein écran sur une ville blanche ne produit **aucun** contraste. |

**Corollaire technique (matériaux)** : voir §7. Un matériau **additif** sur fond clair sature immédiatement
vers le blanc et disparaît. Tout ce qui doit se lire **contre le ciel ou un mur blanc** passe en
**Translucent (blend normal) ou Masked**, pas en Additive.

### Code couleur (tokens de palette)

**`Docs/ArtDirection/PALETTE.md` fait autorité sur toute couleur, sans exception** (D3, révisé le 2026-08-18).
Les anciens tokens `C_*` de cette spec sont **supprimés** : on n'utilise plus que les tokens `OD_*`.
**`OD_Cyan_Accent`, `OD_Red_Enemy`, `OD_Bone_White`, `OD_Violet_Deep`, `OD_Pink_Glow`, `OD_Red_Core`,
`OD_Magenta_Primary`, `OD_Amber_Warning` et `OD_Orange_Heat` n'existent plus.**

| Token | Teinte | Réservé à |
|---|---|---|
| `OD_Magenta_Player` (+ cœur `OD_Navy_Ink`) | magenta saturé | **tout ce qui émane du joueur** : laser (muzzle, beam, impacts), melee, dash, slide, traînée |
| `OD_Red_Traversal` | rouge corail | **la traversée** : wall ride, rails, surfaces de boost, bunny hop |
| `OD_Purple_Primary` / `OD_Purple_Light` | violet | signalétique directionnelle, chevrons, boss phase 1 |
| `OD_Amber_Enemy` | orange | **l'ennemi** : muzzle, projectile, réaction au dégât, mort |
| `OD_Red_Danger` | rouge sombre | danger, kill volume, **dégât subi par le joueur**, overheat |
| `OD_Amber_Heat` | ambre | chaleur, seuil de warning |
| `OD_Gold_Rank` | or | coffres, checkpoints, fin de niveau, **point faible de boss** |
| `OD_Navy_Ink` / `OD_Navy_Deep` | navy très foncé | **cœurs, contours, ombres, pics d'intensité, atterrissages, décals** |
| `OD_Rank_D` … `OD_Rank_S` | par rang | `NS_Rank_Reveal` uniquement |

> **Décisions prises ici** (aucune source ne les tranchait, signalées à Louis) : le **point faible de boss**
> passe en `OD_Gold_Rank` (c'est une opportunité de score, et l'or reste distinct du corps ennemi orange) ;
> les **pics d'intensité** passent en `OD_Navy_Ink` (§1.1 règle 3).

> Les HEX exacts sont dans `Docs/ArtDirection/PALETTE.md` (§2). **N'écris jamais une couleur en dur** dans un Niagara : passe par un `MI_` ou un User Parameter de couleur exposé.
> Rappel `PALETTE.md §3` : une couleur qui signifie quelque chose ne décore jamais. Le magenta part **toujours** du joueur, le rouge corail est **toujours** une surface qu'on parcourt, l'orange vient **toujours** d'un ennemi.

### Interdits absolus
Fumée opaque · particules réalistes (étincelles physiques, débris avec collision, fluides) · motion blur sur les VFX ·
effet plein écran opaque > 0.2 s · flash blanc pleine intensité (risque photosensible **et** invisible sur fond clair) ·
**VFX blanc, pâle ou désaturé** (§1.1) · **matériau additif pour un effet qui doit se lire contre le ciel** (§7) ·
VFX qui masque un ennemi ou un mur · particules qui persistent au sol > 1 s · lumière dynamique par particule ·
GPU sim pour < 50 particules · texture de fumée téléchargée · systèmes Cascade (legacy, interdit en 5.8).

---

## 2. Catalogue complet

> **Ce catalogue fait foi pour tous les noms d'assets `NS_*` du projet** (D20). `SPEC_COMBAT`, `SPEC_ENEMIES`,
> `SPEC_BOSS` et `04_ROADMAP` renvoient ici et ne nomment aucun VFX de leur côté. Un `NS_` qui n'est pas dans
> ce tableau n'existe pas ; l'ajouter ici est la première étape pour le produire.
>
> Légende priorité : **P0** = obligatoire, existe en semaine 2 · **P1** = semaine 3 · **P2** = seulement si le temps le permet (R5).
> « Particules » = nombre cible **par burst**, pas par seconde. Tous les systèmes sont dans `Content/OVERDRIVE/VFX/Niagara/<Famille>/`.
>
> **Colonne « Couleur »** : toutes les couleurs viennent de `PALETTE.md`. Sauf mention contraire, **chaque
> entrée porte en plus un contour ou un cœur `OD_Navy_Ink`** (§1.1 règle 2) — ce n'est pas répété ligne à ligne.

### 2.1 Laser

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Laser_Muzzle` | `BP_LaserWeapon.PlayFireFX()` | 0.08 s | `OD_Magenta_Player` + cœur `OD_Navy_Ink` | 25 uu | 1 sprite + 4 shards | **P0** |
| `NS_Laser_Beam` | idem, User Params `BeamStart`/`BeamEnd` | 0.10 s fade | `OD_Magenta_Player` + cœur `OD_Navy_Ink` | épaisseur 4 uu | 2 (ribbon) | **P0** |
| `NS_Laser_Impact_Surface` | trace bloquante sur géo | 0.25 s | `OD_Magenta_Player` | anneau 60 uu | 1 anneau + 8 shards | **P0** |
| `NS_Laser_Impact_Enemy` | `BPI_Damageable` accepté, corps | 0.20 s | `OD_Magenta_Player` → `OD_Amber_Enemy` | 45 uu | 12 shards | **P0** |
| `NS_Laser_Impact_Headshot` | `IsHeadshot() == true` | 0.35 s | cœur `OD_Navy_Ink` → anneau `OD_Magenta_Player` | anneau 140 uu | 1 anneau + 16 shards + 1 cœur sombre | **P0** |
| `NS_Laser_Overcharge_Muzzle` | 1er tir à `Heat = 0` (upgrade) | 0.12 s | `OD_Amber_Heat` | 40 uu | 8 | P2 |
| `DEC_LaserScorch` | impact sur géo statique | 4 s fade | `OD_Navy_Ink` | 40 uu | décal, pas Niagara | P2 |

> `NS_Laser_Impact_Headshot` : l'ancien « flash blanc » est remplacé par un **cœur sombre qui s'ouvre**
> (`OD_Navy_Ink`, alpha 1 → 0 en 0.12 s) sous l'anneau magenta. Sur fond blanc c'est le **trou noir** qui
> claque, pas la lumière — c'est la traduction directe de §1.1 règle 3.

### 2.2 Kill / Mort

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Enemy_Death_Shatter` | `BPC_Health.OnDeath` (ennemi) | 0.6 s | `OD_Amber_Enemy` + shards `OD_Navy_Deep` | rayon 150 uu | 20 mesh shards | **P0** |
| `NS_Enemy_Death_Ring` | idem, en parallèle | 0.30 s | `OD_Amber_Enemy` | anneau 200 → 400 uu | 1 | **P0** |
| `NS_Kill_Confirm` | à la caméra, world-space devant le joueur | 0.15 s | `OD_Navy_Ink` | 30 uu | 1 sprite | P1 |
| `NS_Enemy_Death_Headshot` | mort par `E_DamageType.LaserHeadshot` | 0.7 s | `OD_Magenta_Player` → `OD_Navy_Ink` | rayon 200 uu | 24 shards + anneau | P1 |
| `NS_Enemy_Dissolve` | sur le `SK_` du cadavre, pilote `DissolveAmount` de `M_Toon_Enemy` (D5, §7) | `Death_DissolveDuration` | `OD_Amber_Enemy` bord | — | 0 (matériau) | P1 |
| `NS_Kill_Streak_Burst` | 3+ kills en < 2 s (`BPC_StyleMeter`) | 0.4 s | `OD_Magenta_Player` | 300 uu | 30 | P2 |

> Les shards de mort sont **`OD_Navy_Deep`** et non blancs : sur un mur clair, une silhouette de débris
> foncée se lit à 3000 uu/s, un éclat blanc ne se lit pas du tout.

### 2.3 Melee

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Melee_Windup` | début de `AM_Melee_Punch` (`Melee_WindupTime`) | 0.06 s | `OD_Magenta_Player` | 30 uu au poing | 6 | P1 |
| `NS_Melee_Impact` | `AN_MeleeHit` → touche confirmée | 0.25 s | `OD_Magenta_Player` + cœur `OD_Navy_Ink` | cône 250 uu | 1 cône + 14 shards | **P0** |
| `NS_Melee_Miss_Swoosh` | swing sans cible | 0.15 s | `OD_Magenta_Player` 30 % alpha | arc 200 uu | 1 ribbon | P2 |
| `NS_Knockback_Trail` | attaché à l'ennemi projeté, tant que `vitesse > seuil` | boucle, stop à l'impact | `OD_Amber_Enemy` → `OD_Magenta_Player` | épaisseur 25 uu | ribbon, 1 emitter | **P0** |
| `NS_WallSlam_Impact` | `BPC_KnockbackReceiver` détecte le mur (`WallSlam_MinImpactSpeed`) | 0.5 s | cœur `OD_Navy_Ink` → anneau `OD_Amber_Enemy` | anneau plaqué 350 uu | 1 anneau + 24 shards | **P0** |
| `NS_WallSlam_Splat` | idem, décal sur le mur | 3 s fade | `OD_Navy_Deep` bordé `OD_Amber_Enemy` | 200 uu | décal | P2 |

> `NS_WallSlam_Splat` est **le** cas d'école de la DA v2 : un impact clair sur un mur blanc ne se voit pas.
> Le décal est une **tache foncée** avec un liseré orange — c'est ce qui rend le slam spectaculaire.

### 2.4 Mouvement

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Dash_Burst` | `BPC_Dash.OnDashPerformed` | 0.20 s | `OD_Magenta_Player` | anneau 200 uu | 1 anneau + 10 shards | **P0** |
| `NS_Dash_Trail` | pendant `Dash_Duration` | 0.16 s + 0.2 s fade | `OD_Magenta_Player` | épaisseur 40 uu | 1 ribbon | **P0** |
| `NS_Slide_Sparks` | boucle pendant `E_MovementState.Sliding` | boucle | `OD_Magenta_Player` | 15 uu / particule | 8 spawn/s, GPU | **P0** |
| `NS_Slide_Start` | entrée de slide | 0.2 s | `OD_Magenta_Player` | 120 uu | 12 | P1 |
| `NS_WallRide_Contact` | boucle pendant `WallRiding`, au point de contact | boucle | `OD_Red_Traversal` | 20 uu | 12 spawn/s, GPU | **P0** |
| `NS_WallJump_Burst` | wall jump | 0.25 s | `OD_Red_Traversal` | anneau plaqué 250 uu | 1 anneau + 8 | P1 |
| `NS_Landing_Light` | atterrissage sous seuil de vitesse | 0.25 s | `OD_Navy_Deep` | anneau 150 uu | 1 anneau | P1 |
| `NS_Landing_Heavy` | atterrissage au-dessus du seuil | 0.4 s | `OD_Navy_Ink` + liseré `OD_Magenta_Player` | anneau 350 uu | 1 anneau + 12 | **P0** |
| `NS_BHop_Perfect` | hop dans `BHop_PerfectWindow` | 0.18 s | `OD_Red_Traversal` | anneau 180 uu | 1 anneau | **P0** |
| `NS_HighSpeed_Stream` | attaché caméra, actif > `SpeedLines_StartSpeed` | boucle | `OD_Navy_Ink` 30 % alpha | traits 300 uu | 20 max, GPU, local space | P1 |
| `NS_Speed_Threshold_Pop` | passage 3000 / 4000 / 5000 uu/s | 0.3 s | `OD_Red_Traversal` / `OD_Magenta_Player` / `OD_Navy_Ink` | bords d'écran | 1 | P2 |

> **Répartition magenta / rouge, appliquée sans exception** (D3) : ce que **le joueur produit** (dash, slide,
> traînée) est `OD_Magenta_Player` ; ce qui naît du **contact avec une surface de traversée** (wall ride, wall
> jump, bunny hop) est `OD_Red_Traversal`, la même couleur que la bande émissive du mur — l'effet et la
> surface se répondent. L'atterrissage n'est ni l'un ni l'autre : c'est un **choc**, donc du foncé.
>
> `NS_HighSpeed_Stream` et `NS_Speed_Threshold_Pop` sont désormais **sombres**. Des traits blancs sur une
> ville blanche produisent zéro contraste — c'est le même arbitrage que les speed lines de
> `SPEC_CAMERA_JUICE §7`, et les deux doivent rester cohérents.

### 2.5 Ennemi

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Enemy_Projectile_Core` | attaché à `BP_EnemyProjectile` | vie du projectile | `OD_Amber_Enemy`, **cœur `OD_Navy_Ink`** | 50 uu (≥ `Projectile_Radius` ×2) | 1 mesh + halo | **P0** |
| `NS_Enemy_Projectile_Trail` | idem | boucle | `OD_Amber_Enemy` | épaisseur 20 uu | 1 ribbon | **P0** |
| `NS_Enemy_Muzzle` | tir ennemi | 0.12 s | `OD_Amber_Enemy` | 40 uu | 1 + 4 | **P0** |
| `NS_Enemy_Charge_Tell` | pendant l'`AttackCooldown` avant tir | ~0.4 s | `OD_Amber_Enemy` pulsant | 60 uu | 1 sprite | P1 |
| `NS_Enemy_Hit_Reaction` | dégât non létal reçu | 0.15 s | `OD_Navy_Ink` (flash **sombre**) | 40 uu | 6 | **P0** |
| `NS_Enemy_Projectile_Impact` | projectile détruit | 0.25 s | `OD_Amber_Enemy` | anneau 120 uu | 1 + 10 | **P0** |
| `NS_Tank_Step` | pas du Tank | 0.3 s | `OD_Navy_Deep` | anneau 150 uu | 1 | P2 |

> **Le projectile ennemi est le VFX le plus critique de la révision.** Il doit rester repérable devant le
> **ciel** (bleu clair) comme devant un **mur** (blanc) à 3000 uu/s. D'où : cœur `OD_Navy_Ink` opaque +
> halo `OD_Amber_Enemy` saturé, en matériau **translucide, pas additif** (§7). C'est le premier élément à
> tester en jeu contre le ciel, avant tout le reste (`07_TUNING §13` : « visible et évitable » est le critère).
>
> `NS_Enemy_Hit_Reaction` : l'ancien flash blanc devient un **flash sombre**. `HitFlash_Duration`
> (`07_TUNING §13`) est inchangée — seule la couleur du flash sur `M_Toon_Enemy` change.

### 2.6 Système / feedback joueur

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Heat_Warning` | `Heat_WarningThreshold` franchi, sur `Muzzle` | boucle pulsée | `OD_Amber_Heat` | 20 uu | 4 spawn/s | **P0** |
| `NS_Overheat_Vent` | `OnOverheatStarted` | 0.6 s | `OD_Amber_Heat` → `OD_Red_Danger` | jets 80 uu | 2 jets × 10 | **P0** |
| `NS_Overheat_Loop` | pendant `Heat_OverheatDuration` | boucle | `OD_Red_Danger` | 30 uu | 6 spawn/s | P1 |
| `NS_Cooldown_Ready` | sortie d'overheat / dash rechargé | 0.2 s | `OD_Magenta_Player` | 30 uu | 6 | P1 |
| `NS_TookDamage_Impact` | `BPC_Health` joueur, direction du hit | 0.3 s | `OD_Red_Danger` | bord d'écran | 8 | **P0** |
| `NS_Chest_Idle` | `BP_LootChest` non ouvert | boucle | `OD_Gold_Rank` | colonne 400 uu | 10 spawn/s, GPU | P1 |
| `NS_Chest_Open` | ouverture | 1.0 s | `OD_Gold_Rank` → `OD_Magenta_Player` | 500 uu | 40 | P1 |
| `NS_Rank_Reveal` | `WBP_Results`, 1 variante par `E_Rank` | 0.8 s | D `OD_Rank_D` · C `OD_Rank_C` · B `OD_Rank_B` · A `OD_Rank_A` · S `OD_Rank_S`, sur fond de panneau `OD_Navy_Deep` | plein widget | 20 → 60 (S) | P1 |
| `NS_Checkpoint_Activate` | `BP_Checkpoint` traversé | 0.5 s | `OD_Gold_Rank` | anneau 300 uu | 1 + 12 | P1 |
| `NS_LevelEnd_Portal` | `BP_LevelEndTrigger` visible | boucle | `OD_Gold_Rank` | 600 uu | 15 spawn/s | P2 |

> `NS_Chest_Idle` et `NS_LevelEnd_Portal` sont des **boucles dorées dans un monde blanc et ensoleillé** :
> l'or seul risque de se noyer. Les deux doivent porter un **contour `OD_Navy_Ink`** et jouer sur la
> **silhouette animée** (colonne de shards montants) plutôt que sur le glow. À revalider en jeu (§9).

### 2.7 Vies & fin de run

> **Nouveau** (D1 / D31). Valeurs : `Run_MaxLives` et `RunFailed_ScreenDuration` (`07_TUNING §18`).
> Aucune durée de gameplay n'est inventée ici.

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_LifeLost` | `GI_Overdrive.OnLifeLost(LivesRemaining)` — joué **au respawn**, pas à la mort | 0.5 s | `OD_Red_Danger`, cœur `OD_Navy_Ink` | anneau plein écran 1 → 0 | 1 anneau + 12 | **P0** |
| `NS_LastLife_Aura` | `LivesRemaining == 1`, **boucle permanente** jusqu'au niveau suivant ou à la mort | boucle | `OD_Red_Danger` 20 % alpha, bords d'écran uniquement | bordure d'écran | 6 spawn/s, GPU, local space | **P0** |
| `NS_RunFailed` | `E_GameState.RunFailed` | `RunFailed_ScreenDuration` | `OD_Navy_Ink` → `OD_Red_Danger` | plein écran | 30, en 2 vagues | P1 |

- **`NS_LifeLost`** est **distinct** de `NS_TookDamage_Impact` : il est **centripète** (l'anneau se referme
  vers le centre au lieu de partir des bords), il ne se déclenche qu'une fois par mort, et il est **rouge
  danger foncé**, pas orange. Le joueur doit lire « j'ai perdu une vie », pas « j'ai pris un coup ».
  Il est joué **après** le fade-in du respawn (`SPEC_CAMERA_JUICE §10`) pour ne pas être mangé par le fondu.
- **`NS_LastLife_Aura`** est un **état, pas un événement** : une vignette de particules très lentes en
  bordure d'écran, sous la zone sanctuarisée 40 % × 40 %, qui ne bouge pas avec la vitesse. Elle
  **n'a pas le droit de pulser rapidement** (fatigue sur un niveau entier) ni de dépasser 20 % d'alpha.
  Compte dans le budget « boucles attachées au joueur » de §6 — à 1 vie, on tombe donc à **2** autres boucles.
- **`NS_RunFailed`** : le seul effet du jeu qui **assombrit** l'écran entier. Sur une DA blanche, la fin de
  run est le moment où le monde s'éteint — c'est le contraste le plus fort dont on dispose.

**Coupe (R5)** : `NS_RunFailed` avant `NS_LastLife_Aura`, jamais `NS_LifeLost` (c'est une information de
gameplay P0 : sans elle, le joueur ne sait pas combien de vies il lui reste sans lire le HUD).

### 2.8 Boss

| Asset | Déclencheur | Durée | Couleur | Taille | Particules | Prio |
|---|---|---|---|---|---|---|
| `NS_Boss_Intro` | `IntroDuration` de `PDA_BossData` | ≤ intro | `OD_Purple_Primary` → `OD_Amber_Enemy` | arène | 60 | P1 |
| `NS_Boss_PhaseChange` | `Phase2HealthThreshold` franchi | 1.2 s | `OD_Amber_Enemy` → `OD_Red_Danger` | onde 1500 uu | 1 anneau + 40 | P1 |
| `NS_Boss_Attack_Tell` | début d'un `AttackPatterns` | variable | `OD_Red_Danger` | 200 uu | 12 | P1 |
| `NS_Boss_Hit` | dégât reçu | 0.15 s | `OD_Navy_Ink` | 100 uu | 10 | P1 |
| `NS_Boss_Death` | mort | 2.5 s | `OD_Red_Danger` → `OD_Navy_Ink` | arène | 80, en 3 vagues | P1 |
| `NS_Boss_Weakpoint` | point faible exposé | boucle | `OD_Gold_Rank` | 80 uu | 6 spawn/s | P2 |

> `NS_Boss_Attack_Tell` passe en **`OD_Red_Danger`** et non `OD_Amber_Enemy` : le télégraphe dit « ça va me
> tuer », pas « c'est hostile ». C'est exactement la distinction que `PALETTE.md §3` établit entre les deux
> tokens, et c'est la seule information du combat de boss qui doit être lue en moins de 3 frames.

---

## 3. Effets d'écran / post-process

### 3.1 Règle d'or

**Aucune logique Blueprint par frame.** Les matériaux de post-process lisent directement `MPC_Global`
(`Docs/08_DATA_SCHEMAS §6`) via un nœud **Collection Parameter**. Le seul coût BP est l'écriture de 3–5 scalaires.

```
BPC_MovementState ──(Timer 20 Hz)───▶ FInterpTo ──▶ SetScalarParameterValue(MPC_Global, "PlayerSpeed01")
BPC_Heat          ──(événement)─────▶              SetScalarParameterValue(MPC_Global, "HeatRatio" / "OverheatActive")
BPC_StyleMeter    ──(événement)─────▶              SetScalarParameterValue(MPC_Global, "StyleMultiplier01")
BPC_Health        ──(événement)─────▶              SetScalarParameterValue(MPC_Global, "DamageFlash01")
```

**`PlayerSpeed01` — formule unique (D9)**, écrite par **`BPC_MovementState` et par personne d'autre** :

```
PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                       / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )
```

- **Cadence** : un timer unique **20 Hz** dans `BPC_MovementState`, qui alimente aussi le vent (`MS_Wind_Speed`,
  `SPEC_AUDIO §5`). Un seul écrivain, une seule cadence, un seul point de maintenance.
- **Ne sert PAS au FOV** : le FOV lit la vitesse brute via `CF_FOVBySpeed` (`SPEC_CAMERA_JUICE §2`).
- `BPC_PlayerStats` n'écrit **rien** dans `MPC_Global`. Liste complète des paramètres : `08_DATA_SCHEMAS §6`
  (`PlayerSpeed01`, `StyleMultiplier01`, `HeatRatio`, `OverheatActive`, `DamageFlash01`, `WorldTint`).
- **Interdit** : Tick, `Get Player Character` dans un matériau-driver, ou un timer < 0.05 s.
- Le lissage se fait **une fois** en BP (`FInterpTo` avec `FOV_InterpSpeed` comme référence de feeling), jamais dans le matériau.

### 3.2 Les matériaux de post-process

| Asset | Effet | Entrée `MPC_Global` | Approche matériau | Prio |
|---|---|---|---|---|
| `PP_SpeedLines` | traits radiaux depuis le centre | `PlayerSpeed01` | `ScreenPosition` − 0.5 → coords polaires (`atan2` + `length`) → `frac(angle × 64 + Time × 2)` → `pow()` pour affiner les traits → masqué par `1 - length` (centre vide) → multiplié par `CF_SpeedLinesBySpeed`. Blendable **After Tonemapping**. | **P0** |
| `PP_ChromaticAberration` | séparation RGB en bord d'écran | `PlayerSpeed01` | `SceneTexture:PostProcessInput0` échantillonné 3× avec un offset UV radial ±`Intensity × radius²`. Intensité max = `ChromaticAberration_MaxAtFullSpeed`. | **P0** |
| `PP_Vignette` | assombrissement des bords | `PlayerSpeed01`, `DamageFlash01` | `1 - saturate(length(ScreenPos - 0.5) × k)`, teinte lerp `OD_Navy_Deep` → `OD_Red_Danger` par `DamageFlash01`. Sur fond clair, la vignette est l'un des rares effets **naturellement lisibles** : elle assombrit. | **P0** |
| `PP_SpeedWarp` | distorsion barillet à très haute vitesse | `PlayerSpeed01` | Offset UV = `radialDir × radius³ × Intensity`. Ne s'active qu'au-dessus de `SpeedLines_StartSpeed`, plafonné à `SpeedLines_FullSpeed`. Reste **subtil** : au-delà on perd la lecture du niveau. | P1 |
| `PP_HeatOverlay` | teinte ambre + ondulation | `HeatRatio`, `OverheatActive` | Grain de chaleur = `sin(ScreenPos.y × 300 + Time × 20)` × `HeatRatio²`, offset UV vertical ≤ 2 px. Sur front montant d'`OverheatActive`, **assombrissement** plein écran teinté `OD_Red_Danger` à 35 % alpha en **multiply**, jamais un flash additif (invisible sur une ville blanche), décroissance via `OverheatActive` lissé côté BP. | **P0** |
| `PP_DamageFlash` | pulsation rouge directionnelle | `DamageFlash01` | Vignette `OD_Red_Danger` asymétrique en **multiply** ; la direction du hit passe par un **Material Instance Dynamic** sur le blendable (paramètre `HitDirection2D`), pas par le MPC (valeur non partagée). | **P0** |
| `PP_Posterize` | **cel-shading de la scène éclairée** | — (statique) | **Nouveau (D2).** Le monde est **éclairé** : la posterisation quantifie la luminance en `N` bandes (`N = 4` `[À CALIBRER]`) après le tonemapping du lighting, ce qui transforme les ombres portées de Lumen/VSM en aplats toon. `floor(luminance × N) / N`, appliqué en préservant la teinte (quantifier `L` dans un espace `HSL`, pas les 3 canaux RGB séparément — sinon les couleurs de la palette dérivent). | **P0** |

**Implémentation** : **tous** les blendables permanents du jeu sont portés par `BP_PlayerCameraManager` (un seul endroit
à maintenir), pas par un volume par niveau — **y compris `PP_ToonOutline`** (outline Sobel) **et `PP_Posterize`**,
les deux moitiés du rendu cel-shaded de la DA (`SPEC_ART_DIRECTION`, D2). Ils comptent dans le budget comme les autres.

**Ordre d'application — la posterisation vient AVANT tous les effets de vitesse :**

```
1. PP_Posterize            (Before Tonemapping)   ← le rendu de base : on quantifie la scène éclairée
2. PP_ToonOutline          (Before Tonemapping)   ← l'outline se trace sur des aplats déjà propres
3. PP_SpeedWarp            (Before Tonemapping)
4. PP_ChromaticAberration
5. PP_SpeedLines
6. PP_HeatOverlay
7. PP_DamageFlash
8. PP_Vignette
```

**Pourquoi cet ordre** : posteriser **après** les speed lines quantifierait les traits eux-mêmes et les
ferait clignoter d'une frame à l'autre. La posterisation décrit **le monde** ; les effets de vitesse sont
une **surcouche** sur l'image finale. Même raison pour l'outline : elle doit lire des aplats stables.

**Budget : 8 blendables max** (posterisation + outline + 6 de vitesse/feedback — le budget passe de 7 à 8
avec l'arrivée de `PP_Posterize`), ≤ 1 sample de `SceneTexture` chacun sauf `PP_ChromaticAberration` (3),
`PP_ToonOutline` (SceneDepth + CustomDepth) et `PP_Posterize` (1 `PostProcessInput0`).
Au-delà de 8, on fusionne — les candidats, dans l'ordre : `PP_Vignette` dans `PP_DamageFlash`, puis
`PP_Posterize` dans `PP_ToonOutline` (les deux lisent la même image et sont voisins dans la chaîne).
**On ne coupe jamais `PP_Posterize`** : sans lui, la scène éclairée n'est plus toon, c'est un rendu réaliste
low-poly. C'est le rendu, pas du juice.

> ⚠ **Nouveau risque perf (D2)** : Lumen + VSM sont **actifs**. Le budget VFX de §6 (2.0 ms GPU) est
> **inchangé**, mais il se prend sur une frame désormais plus chargée. Si le budget global explose, on
> coupe dans les VFX P2 **avant** de toucher aux réglages d'éclairage — les ombres portées **sont** la DA.

---

## 4. Hit-stop et screen shake

### 4.1 Hit-stop — `BPC_HitStop` (sur `PC_Overdrive`)

**Un seul propriétaire, le PlayerController** (D6). `Set Global Time Dilation` est un état global : il ne peut pas
avoir trois propriétaires. Et le PlayerController survit au respawn du pawn, contrairement à `BP_PlayerCharacter`.
`BPFL_Overdrive::DoHitStop` **n'existe pas** : une Function Library ne peut pas porter d'état.

Valeurs : `HitStop_Headshot`, `HitStop_TimeDilation`, `HitStop_MinInterval` (`07_TUNING §16`) et `Melee_HitStop`
(`§12`). **Ne rien inventer.**

```
BPC_HitStop  (sur PC_Overdrive)
  RequestHitStop(RealDuration: float, Dilation: float, Priority: int) → bool bAccepted
```

```
RequestHitStop(RealDuration, Dilation, Priority):
    if (bActive AND Priority <= CurrentPriority): return false     // strictement supérieure, sinon ignoré
    if (TimeSinceLastHitStop < HitStop_MinInterval): return false   // anti-spam
    CurrentPriority = Priority ; bActive = true
    SetGlobalTimeDilation(Dilation)
    ClearAndInvalidateTimer(HitStopTimer)
    SetTimerByEvent(EndHitStop, RealDuration * Dilation)            // ⚠ compensation
    return true
```

> ⚠ **Piège UE** : les timers du monde subissent la dilatation. Un timer de `T` secondes dure `T / D` en temps réel.
> `RealDuration` est exprimée en **temps réel** : on arme donc le timer à `RealDuration × Dilation`. À vérifier au chrono.
> `EndHitStop` remet `SetGlobalTimeDilation(1.0)`, `bActive = false`, `CurrentPriority = 0`.

| Règle | Valeur |
|---|---|
| Priorités | `Boss phase = 30` > `WallSlam = 20` > `Headshot = 10`. Kill simple : pas de hit-stop. |
| Cumul | **Interdit.** Une seule requête active ; accepté **uniquement** si `Priority` est **strictement supérieure**, sinon ignoré (`bAccepted = false`). |
| Intervalle minimum entre deux hit-stops | `HitStop_MinInterval` (`07_TUNING §16`) |
| Exclus du ralenti | l'**audio** (`Sound Class` dont le pitch n'est pas lié au time dilation) et l'**UI** |
| Jamais de hit-stop sur | tir dans le vide, dégât subi, kill de masse, boss (hors phase change) |
| Pendant un hit-stop | l'input reste lu ; **on ne bloque jamais la caméra** |

### 4.2 Screen shake

Classes Blueprint dérivées de `CameraShakeBase` / `LegacyCameraShake`, dans
`Content/OVERDRIVE/Player/Blueprints/Shakes/`.
**Nommage : préfixe `CS_`** (D7). `06_CONVENTIONS §2` fait autorité sur les préfixes, sans exception —
la décision `BP_Shake_*` de cette spec est **annulée**, et le dossier `Player/Camera/` n'existe pas.
Formes et amplitudes détaillées : `SPEC_CAMERA_JUICE §5`, qui fait foi sur le paramétrage des assets.

| Asset | Pattern | Scale (`07_TUNING §16`) | Déclencheur |
|---|---|---|---|
| `CS_LaserFire` | Wave Oscillator, 0.10 s, pitch/yaw only | `Shake_LaserFire` | chaque tir |
| `CS_Headshot` | Wave Oscillator + roll léger, 0.15 s | `Shake_Headshot` | headshot confirmé |
| `CS_MeleeHit` | Perlin Noise, 0.20 s | `Shake_MeleeHit` | melee touché |
| `CS_TakeDamage` | Perlin Noise + FOV kick négatif, 0.25 s | `Shake_TakeDamage` | dégât subi |
| `CS_HardCollision` | Perlin Noise, 0.30 s | `Shake_HardCollision` | collision frontale > 60° |
| `CS_WallSlam` | Perlin Noise, 0.25 s | `Shake_WallSlam` | wall slam confirmé |

**Règles anti-abus** — un shake mal géré à 5000 uu/s rend le jeu injouable :

1. **Translation de caméra : autorisée, mais faible.** `SPEC_CAMERA_JUICE §5` en spécifie et ses valeurs sont
   modestes ; l'interdiction totale de cette spec est **levée**. Limite chiffrée qui remplace l'interdit :
   **amplitude de location ≤ 8 uu sur chaque axe**, et **≤ 4 uu pour tout shake déclenché par une action du
   joueur** (tir, headshot, melee) — au-delà, la visée décroche. Aucune translation ne fait sortir la caméra
   de la capsule.
2. **Amplitude de roll ≤ 30 %** de l'amplitude pitch/yaw : le roll est le plus nauséeux.
3. **Cooldown par asset** : un même shake ne peut être rejoué avant 60 % de sa durée. Géré par
   `StartCameraShake` (UE remplace l'instance existante si `bSingleInstance = true` → **cocher `bSingleInstance` partout**).
4. **Plafond global** : max **2** shakes actifs. `BP_PlayerCameraManager` maintient une pile ; au-delà, le plus faible est stoppé.
5. **Le shake décroît avec la vitesse** : au-dessus de `SpeedLines_StartSpeed`, multiplier le scale par 0.6.
   Le mouvement de caméra propre au déplacement fait déjà le travail.
6. **Option accessibilité obligatoire** : `WBP_Settings` expose `ShakeScale` (0–1, `SG_Settings`,
   `SPEC_UI_HUD §9`), appliqué comme multiplicateur global au moment du `StartCameraShake`. À 0, aucun
   `StartCameraShake` n'est appelé et le jeu doit rester lisible et fun.
7. Jamais de shake pendant un fondu, un écran de résultat ou une pause.

---

## 5. Techniques Niagara à privilégier (dev solo)

### 5.1 Arbitrages

| Question | Réponse par défaut |
|---|---|
| CPU ou GPU ? | **CPU Sim** partout sauf boucles > 50 particules simultanées (`NS_Slide_Sparks`, `NS_HighSpeed_Stream`, `NS_Chest_Idle`). Le CPU permet les events, les bounds auto et le debug ; le GPU impose des bounds fixes. |
| Sprite, mesh ou ribbon ? | **Mesh** pour tout ce qui doit lire comme une forme (shards, éclats) · **Sprite** pour les flashs et anneaux (matériau radial) · **Ribbon** pour les trails (dash, knockback, projectile, beam). |
| Texture ? | **Aucune.** Tout est procédural dans `M_VFX_Unlit` (§7). Zéro fichier à produire, zéro coût mémoire, style cohérent garanti. |
| Blend mode ? | **Translucent (blend normal) ou Masked par défaut. Additive uniquement pour ce qui se joue devant du foncé.** Le monde est clair (D2) : un additif se sature vers le blanc du décor et **disparaît**. Voir §7. |
| Lumière ? | **Aucune light par particule, aucun `Light Renderer`** — c'est une contrainte de perf, pas de rendu. Le monde **est** éclairé (Lumen + VSM actifs, D2), mais les VFX restent en shading `Unlit` : ils ne reçoivent ni ombre ni GI, et leur lisibilité vient de la **saturation et du contour sombre** (§1.1), pas de l'`EmissiveIntensity`. |
| Modules ? | Le strict minimum : `Spawn Burst Instantaneous`, `Initialize Particle`, `Add Velocity`, `Drag`, `Scale Sprite/Mesh Size by Life`, `Color by Life`, `Solve Forces and Velocity`. |
| Collision ? | **Non**, sauf `NS_WallSlam_Impact` (et encore : préférer l'orientation par la normale du hit). |

**Toujours** : `Local Space = true` pour tout ce qui est attaché au joueur ou à une arme (le muzzle à 4000 uu/s
laisse une traînée absurde en world space). `Local Space = false` pour les impacts, morts et knockback trails.

### 5.2 Trois recettes réutilisables

**Recette A — « Shard Burst » (le socle : impacts, morts, dash, wall slam)**
```
Emitter : CPU, Mesh Renderer, SM_VFX_Shard_Tri (triangle 3 tris, pivot au centre)
  Emitter Update  : aucun (one-shot)
  Emitter Spawn   : Spawn Burst Instantaneous  → SpawnCount = User.BurstCount
  Particle Spawn  : Initialize Particle (Lifetime 0.15–0.35 random, Uniform Sprite Size)
                    Add Velocity in Cone  → Cone Axis = User.Normal, Angle 45°, Speed 400–1200 random
                    Initialize Mesh Reproduction / random rotation + Rotational Velocity
  Particle Update : Solve Forces (Drag 3.0, Gravity 0 ou -980 selon la famille)
                    Scale Mesh Size by Life  → courbe 1.0 → 0.0 (ease-out, pas linéaire)
                    Color by Life            → User.ColorStart → User.ColorEnd, Alpha 1 → 0
User Params exposés : BurstCount (int), Normal (vector), ColorStart, ColorEnd, SizeScale
```
Un seul émetteur, réglé par User Params → 8 systèmes du catalogue en dérivent. **C'est le premier asset à produire.**

**Recette B — « Flash Ring » (anneau de choc, sans texture)**
```
Emitter : CPU, Sprite Renderer, matériau M_VFX_Unlit en mode Ring
  Spawn Burst = 1
  Particle Spawn : Lifetime 0.20–0.35, Sprite Size = User.StartSize
                   Sprite Facing = Custom Facing Vector (= normale du mur) OU Camera Facing
  Particle Update: Scale Sprite Size by Life → 0.1 → 1.0 (ease-out fort : 80 % de la taille en 30 % du temps)
                   Color by Life → alpha 1 → 0 sur la même courbe inversée
Matériau : radial = abs(distance(UV, 0.5) - RingRadius) → 1 - smoothstep(0, Thickness, x)
```
Zéro texture, épaisseur et rayon animables par paramètre → un seul matériau pour tous les anneaux du jeu.

**Recette C — « Speed Ribbon » (dash, knockback, projectile, beam laser)**
```
Emitter : CPU, Ribbon Renderer, M_VFX_Beam
  Emitter Update : Spawn Rate = 60/s (attaché) OU Spawn Burst 2 (beam point à point)
  Particle Spawn : Lifetime 0.15 s, Ribbon Width = User.Width
  Particle Update: Scale Ribbon Width by Life → 1.0 → 0.0
                   Color by Life → User.Color, alpha 1 → 0
  Ribbon Settings : Tessellation Mode = Automatic, Curve Tension 0.5 (indispensable à haute vitesse,
                    sinon le ruban devient une ligne brisée)
```
Pour le beam hitscan : 2 particules positionnées par les User Params `BeamStart` / `BeamEnd` via
`Set Niagara Variable (Vector)` depuis `BP_LaserWeapon`, puis `Activate`. **Pas de spawn continu.**

### 5.3 Stylisation sans texture

Dégradés = `smoothstep` sur une distance UV · formes = analytiques (cercle, anneau, étoile via `atan2`) · « flicker » =
`frac(Time × 20)` quantifié (le stepping renforce le toon, ne pas lisser) · courbes de scale **jamais linéaires**
(ease-out à l'apparition, ease-in à la disparition) · la couleur fade vers une teinte **plus saturée** puis alpha 0,
**jamais vers le blanc** (sur fond clair, fader vers le blanc = fader vers l'invisible deux fois).

**Le contour, en une ligne de matériau** : `Outline = smoothstep(Shape - OutlineWidth, Shape, x) - Shape`,
multiplié par `OutlineColor` (`OD_Navy_Ink`) et composé **sous** la couleur principale. Un seul nœud
réutilisé par toutes les formes de `M_VFX_Unlit` — c'est ce qui rend §1.1 règle 2 gratuite.

---

## 6. Budget performance

| Contrainte | Valeur cible | Note |
|---|---|---|
| Systèmes Niagara actifs simultanés | **≤ 16** | au-delà, le `NS_` le plus ancien de priorité P2 est stoppé |
| Particules totales à l'écran | ≤ 800 | ≤ 300 en combat dense |
| Particules par burst d'impact | ≤ 24 | un headshot spectaculaire = 16 shards bien réglés, pas 200 |
| Overdraw | **le tueur n°1** | additif plein écran interdit ; taille de sprite ≤ 15 % de la hauteur d'écran |
| Boucles attachées au joueur | ≤ 3 | slide + wall ride + high speed ne coexistent jamais tous les trois |
| `Local Space` | joueur / arme / caméra = **true** | impacts et morts = false |
| Culling | `Effect Type` Niagara + **Significance Culling** par distance | ennemi : 4000 uu · props : 2500 uu · impacts : 6000 uu |
| Fixed Bounds | **obligatoire** sur tout emitter GPU | sinon le système disparaît à l'écran ou coûte un readback |
| Lifetime max | 1.0 s (combat) / 4 s (ambiance) | rien ne persiste |
| Instancing | `NS_Laser_Impact_Surface` et `NS_Enemy_Hit_Reaction` doivent supporter 10 spawns/s | testés au `stat GPU` |

**Ce qui tue les fps** : GPU sim sans bounds fixes · `Light Renderer` · translucide plein écran · `Collision` Scene Depth
sur > 50 particules · Ribbon Tessellation `High` · matériau translucide multi-`SceneTexture` · un système jamais désactivé
(toujours `Auto Destroy` + `Kill On Complete`). **Mesure** : `stat GPU`, `stat Niagara`, `fx.Niagara.Debug.Hud 1`.
Budget : **VFX ≤ 2.0 ms GPU**.

---

## 7. Bibliothèque de matériaux VFX

`Content/OVERDRIVE/VFX/Materials/` — **4 masters, tout le reste est un `MI_`.**

| Master | Blend / Shading | Paramètres exposés | Utilisé par |
|---|---|---|---|
| `M_VFX_Unlit` | **Translucent (blend normal)**, Unlit, **Disable Depth Test = off**, switch statique `bAdditive` | `Color` (V), `Intensity` (S), `Shape` (switch : Disc / Ring / Star / Streak), `RingRadius`, `RingThickness`, `SoftEdge`, `Flicker`, **`OutlineColor`**, **`OutlineWidth`** | 80 % des systèmes : flashs, anneaux, shards, sparks |
| `M_VFX_Beam` | **Translucent (blend normal)**, Unlit, Two Sided | `Color`, `CoreWidth`, `GlowFalloff`, `ScrollSpeed`, `Fade`, **`OutlineColor`**, **`OutlineWidth`** | `NS_Laser_Beam`, tous les ribbons |
| `M_VFX_Distortion` | Translucent, Unlit, **Refraction** | `DistortionStrength`, `Falloff`, `Speed` | onde de choc du wall slam, boss phase change. **P2** — coûte cher, à couper en premier |
| `M_VFX_Mesh_Unlit` | **Masked**, Unlit | `Color`, `EmissiveBoost`, `FresnelPower`, **`OutlineColor`** | mesh particles (shards), projectile ennemi |

> **`M_VFX_Additive` est renommé `M_VFX_Unlit`** et son blend mode par défaut passe de **Additive** à
> **Translucent**. L'ancien nom promettait le mauvais comportement, ce qui est le pire défaut possible pour
> un master : n'importe quel `MI_` créé dessus héritait d'un blend invisible sur fond clair.

### 7.1 Additif ou translucide ? — la décision technique de la révision

| Le VFX se joue devant… | Blend | Pourquoi |
|---|---|---|
| **Le ciel, un mur blanc, le sol** (99 % des cas) | **Translucent (blend normal)** ou **Masked** | Un additif ajoute de la lumière à une image **déjà proche du blanc** : le résultat sature à `1.0` et devient **exactement la couleur du fond**. L'effet ne disparaît pas « un peu », il disparaît **complètement**. |
| **Une surface foncée** : silhouette d'ennemi, ombre portée, `NS_RunFailed`, intérieur de tunnel | **Additive** autorisé | C'est le seul contexte où l'additif garde son punch. Se règle par un `MI_`, jamais en dupliquant le master. |

**Conséquence assumée** : les VFX ont **moins de « glow »** qu'en v1. C'est le prix de la lisibilité, et le
`OutlineWidth` le compense largement. Si un effet paraît fade en jeu, la bonne réaction est **d'augmenter la
saturation et l'épaisseur du contour**, pas de repasser en additif ni de monter `Intensity` — les deux
ramènent le problème.

**`Masked` plutôt que `Translucent` dès que possible** : pas de tri de transparence, pas d'overdraw
(le tueur n°1 de §6), et un bord dur qui sert le style toon. `Translucent` est réservé aux effets qui ont
réellement besoin d'un fondu d'alpha (ribbons, vignettes de bord, `NS_LastLife_Aura`).

**Pas de master `M_VFX_Dissolve`** (D5). Le dissolve est un **paramètre du matériau d'ennemi** :
`DissolveAmount` (0–1) sur **`M_Toon_Enemy`** (`SPEC_ART_DIRECTION`), piloté par Dynamic Material Instance
pendant `Death_DissolveDuration`. Aucune simulation physique, jamais de ragdoll. Les autres dissolves
(apparition du coffre, boss phase change) réutilisent le même paramètre sur leur propre `M_Toon_*` —
on ne duplique pas un master pour ça.

**Règles** : shading `Unlit` sur tous les masters VFX — les particules ne reçoivent ni ombre ni GI, alors que
**le monde, lui, est éclairé** (Lumen + VSM actifs, D2) · aucun `Sample Texture2D` sauf exception validée ·
`Two Sided` seulement si nécessaire · **jamais de `Custom Depth`** (réservé à l'outline des ennemis) ·
toute couleur passe par le paramètre `Color`, jamais par une constante · **`OutlineColor` par défaut à
`OD_Navy_Ink`, `OutlineWidth` jamais à 0 sans raison écrite** (§1.1 règle 2).

---

## 8. Ordre de production (4 semaines)

> **Cette spec planifie en semaines** (D23). Le découpage en jours est l'affaire exclusive de
> `04_ROADMAP.md` : si les deux divergent, c'est la roadmap qui a raison sur le calendrier.

| Semaine | Ce qu'on produit | Pourquoi |
|---|---|---|
| **S1** — fondations | `M_VFX_Unlit`, `M_VFX_Beam`, `M_VFX_Mesh_Unlit` (avec **le nœud de contour** de §5.3), `SM_VFX_Shard_Tri`, **Recette A + B + C** en émetteurs réutilisables (`NE_ShardBurst`, `NE_FlashRing`, `NE_SpeedRibbon`) | Sans le socle, chaque VFX coûte 1 h au lieu de 10 min. Le contour est dans le socle : rétrofiter la lisibilité sur 40 systèmes coûterait une semaine. |
| **S1 fin** | `NS_Dash_Burst`, `NS_Dash_Trail`, `NS_Slide_Sparks`, `NS_WallRide_Contact`, `NS_Landing_Heavy`, `NS_BHop_Perfect` | Le mouvement est la feature n°1 (R5) : il doit être juteux **pendant** son tuning, pas après. |
| **S2** — combat | `NS_Laser_Muzzle`, `NS_Laser_Beam`, les 3 impacts laser, `NS_Enemy_Hit_Reaction`, `NS_Enemy_Death_Shatter` + `_Ring`, `NS_Melee_Impact`, `NS_Knockback_Trail`, `NS_WallSlam_Impact` | **Tous les P0 combat sont finis en fin de S2.** |
| **S2 fin** | `BPC_HitStop` (sur `PC_Overdrive`) + les 6 `CS_*` + `ShakeScale` | Le hit-stop change le tuning du combat : le faire tard invalide le playtest. |
| **S1 fin (bis)** | **`PP_Posterize` + `PP_ToonOutline`** | D2 : le rendu cel-shaded n'est **pas** du polish, c'est la DA. Tant qu'ils ne sont pas là, on juge la lisibilité des VFX sur une image qui n'est pas celle du jeu. |
| **S3** — écran & système | `PP_SpeedLines`, `PP_ChromaticAberration`, `PP_Vignette`, `PP_HeatOverlay`, `PP_DamageFlash` + câblage `MPC_Global` ; `NS_Heat_Warning`, `NS_Overheat_Vent`, `NS_TookDamage_Impact`, VFX projectile ennemi | La sensation de vitesse plein écran arrive quand le mouvement est calibré. |
| **S3 fin** | `DissolveAmount` sur `M_Toon_Enemy`, `NS_Enemy_Dissolve`, `NS_Chest_Open`, `NS_Rank_Reveal`, `NS_Checkpoint_Activate`, **`NS_LifeLost` + `NS_LastLife_Aura`** (§2.7) | Boucle de progression rendue lisible. Les vies arrivent avec le reste du système de run. |
| **S4** — boss & polish | VFX boss (§2.8), **`NS_RunFailed`**, `PP_SpeedWarp`, passe de **cohérence colorimétrique**, passe de **budget perf** (§6), P2 restants | Les P2 ne se produisent que si S1–S3 sont validés. |

**Règle de coupe (CLAUDE.md R5)** : si S3 déborde, on coupe dans l'ordre `M_VFX_Distortion` → tous les P2 →
`NS_RunFailed` → `PP_SpeedWarp` → variantes de mort. On ne coupe **jamais** un P0, ni `PP_Posterize`
(c'est le rendu, pas un effet).

---

## 9. Checklist de validation

**Par effet**
- [ ] Nom conforme (`NS_` / `M_` / `PP_` / `CS_`, `06_CONVENTIONS §2`), rangé dans le bon dossier (`Content/OVERDRIVE/VFX/…`, shakes dans `Player/Blueprints/Shakes/`)
- [ ] Aucune couleur en dur : tout passe par un User Parameter ou un `MI_`, aligné sur un token `OD_*` de `PALETTE.md`
- [ ] **Aucun `OD_Cyan_Accent`, `OD_Red_Enemy`, `OD_Bone_White`, `OD_Violet_Deep`, `OD_Pink_Glow`, `OD_Red_Core`, `OD_Magenta_Primary`, `OD_Amber_Warning` ni `OD_Orange_Heat`** — ces tokens n'existent plus (§1)
- [ ] **Blend mode** : `Translucent`/`Masked` sauf si l'effet se joue devant du foncé (§7.1). Aucun additif devant le ciel
- [ ] **Contour ou cœur `OD_Navy_Ink` présent**, `OutlineWidth ≠ 0` (§1.1 règle 2)
- [ ] **Testé devant les 3 fonds : ciel bleu, mur blanc en pleine lumière, mur blanc à l'ombre.** Si l'effet disparaît sur l'un des trois, il est raté
- [ ] `Local Space` réglé consciemment (§6), `Fixed Bounds` renseigné si GPU
- [ ] `Auto Destroy` + `Kill On Complete` sur tout one-shot ; aucune boucle sans condition d'arrêt explicite
- [ ] Durée ≤ 0.35 s pour un feedback de combat, ≤ 1.0 s pour une mort
- [ ] Testé **en mouvement à 3000+ uu/s**, pas à l'arrêt dans le viewport Niagara
- [ ] Ne masque ni un ennemi, ni un mur, ni la zone centrale sanctuarisée 40 % × 40 % (D22)
- [ ] `Effect Type` + distance de culling assignés

**Par système**
- [ ] `stat GPU` : ligne Niagara ≤ 2.0 ms dans le pire cas (combat dense + haute vitesse)
- [ ] `fx.Niagara.Debug.Hud 1` : ≤ 16 systèmes actifs, ≤ 800 particules
- [ ] Aucun Tick BP ajouté pour piloter un VFX ; `MPC_Global` écrit par timer ≥ 0.05 s uniquement
- [ ] Les **8** blendables post-process (`PP_Posterize` et `PP_ToonOutline` inclus) se cumulent sans saturer l'écran à 5000 uu/s, **dans l'ordre de §3.2** (posterisation en premier)
- [ ] Vies : `NS_LifeLost` ne se confond pas avec `NS_TookDamage_Impact` · `NS_LastLife_Aura` s'arrête bien au changement de niveau et à la mort · `NS_LastLife_Aura` ne pulse pas et ne dépasse pas 20 % d'alpha
- [ ] Hit-stop : `BPC_HitStop` bien sur `PC_Overdrive`, pas de cumul, respect de `HitStop_MinInterval`, retour garanti à `TimeDilation = 1.0` (tester une mort pendant un hit-stop)
- [ ] Screen shake : `bSingleInstance` coché partout, ≤ 2 actifs, translation ≤ 8 uu (≤ 4 uu sur une action du joueur), `ShakeScale = 0` reste jouable
- [ ] Aucune valeur de `07_TUNING §16` dupliquée dans un Blueprint

**Test manuel pour Louis (R8)** — dans `L_Sandbox_Movement` :
1. Enchaîner slide → dash → wall ride → wall jump à > 3000 uu/s. **Question : sais-tu à tout moment ce que tu viens de faire, sans regarder le HUD ?**
2. Headshot un Grunt en pleine course. **Le hit-stop se sent-il, ou casse-t-il la course ?**
3. Melee un Grunt contre un mur. **Le wall slam est-il l'effet le plus spectaculaire du jeu ?** (il doit l'être)
4. Faire monter la chaleur jusqu'à l'overheat en courant. **As-tu vu venir l'overheat avant qu'il arrive ?**
5. Prendre un projectile à pleine vitesse. **Sais-tu d'où il venait ?**
6. Jouer 3 min d'affilée. **Mal aux yeux ? Nausée ? → réduire shakes et chromatic aberration avant tout le reste.**

**Tests spécifiques à la DA v2** — le fond est clair, c'est la seule chose qui compte :
7. Se placer face au **ciel** (regarder vers le haut, en bord de toit) et tirer. **Vois-tu le beam ? le muzzle ?**
   Refaire face à un **mur blanc en plein soleil**, puis face à un **mur blanc à l'ombre**.
   → Si un effet ne passe pas les trois, c'est le **contour** qu'on épaissit, pas l'`Intensity`.
8. Faire tirer un Shooter sur toi **depuis un fond de ciel**. **Vois-tu le projectile arriver ?**
   C'est le test le plus important de tous : `07_TUNING §13` dit « visible et évitable », pas un chiffre.
9. Enchaîner wall ride → dash → slide. **Distingues-tu le rouge de la surface du magenta de ton dash ?**
   Si les deux se confondent en mouvement, c'est le repli turquoise de `PALETTE.md §3` qui se déclenche —
   remonte-le à Louis, ne change pas la palette de ton côté.
10. Perdre une vie, puis rejouer avec **1 vie restante** pendant 2 min complètes.
    **Sais-tu en permanence que tu es sur ta dernière vie ? Et est-ce que ça te fatigue les yeux au bout de 2 min ?**
    Si oui → baisser l'alpha de `NS_LastLife_Aura` avant de la supprimer.
