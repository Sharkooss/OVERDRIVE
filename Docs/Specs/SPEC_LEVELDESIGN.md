# SPEC — LEVEL DESIGN

> Document de travail du level designer. **À garder ouvert pendant la construction.**
> Toutes les valeurs de gameplay viennent de `Docs/07_TUNING.md` — ici elles sont **dérivées** (formules montrées).
> Mouvement : `Docs/Specs/SPEC_MOVEMENT.md`. Nommage : `Docs/06_CONVENTIONS.md`. Données : `Docs/08_DATA_SCHEMAS.md`.
> Grille de construction : **100 uu**. Snap éditeur : **50 uu / 15°** (`06_CONVENTIONS §6`).
> **DA v2 — ville blanche en plein jour, rendu ÉCLAIRÉ (Lumen + VSM actifs)** : `11_ARBITRAGES D2 / D3 / D33`.
> Couleurs : `ArtDirection/PALETTE.md`, par token, sans exception. Lisibilité sur fond clair : **§5.2**.
> Budget d'éclairage — **le risque perf n° 1 du projet** : **§12**.

---

## 1. Principes non négociables

| # | Règle | Pourquoi |
|---|---|---|
| P1 | **Le niveau est LINÉAIRE.** Un chemin principal lisible du début à la fin. Jamais un labyrinthe, jamais de backtracking, jamais de clé à chercher. | Le joueur va à 3000 uu/s : il n'a pas le temps de se demander où aller. |
| P2 | **Aucun couloir seul.** Chaque niveau alterne couloir ⇄ **grand espace**. Un couloir ne dure jamais plus de 3 s à vitesse de croisière (≈ 9000 uu à 3000 uu/s). | La vitesse a besoin de volume pour exister. |
| P3 | **Rien n'arrête le joueur.** Pas de porte à ouvrir, pas d'ascenseur, pas de zone verrouillée « tue tout pour continuer ». Le combat est *sur* le chemin, pas *en travers*. | GDD : erreur = perte de vitesse, jamais arrêt. |
| P4 | **Le raccourci est optionnel.** Le Speed Way ne doit **jamais** être requis pour finir. Il sert au score et au S Rank. | Un joueur bloqué par une exigence d'exécution abandonne. |
| P5 | **Tout obstacle est visible avant d'être atteint** (cf. §5, tableau de distances de visibilité). Aucun mur derrière un angle aveugle. | Mourir/ralentir sans avoir vu = injuste. |
| P6 | **La verticalité descend.** Le joueur n'a ni double saut ni grapple : la montée coûte du temps, la descente en donne. Ratio cible : **≥ 70 % du dénivelé d'un niveau est descendant.** | Apex de saut = 172 uu seulement (§2). |
| P7 | **Un niveau se relance en < 0.5 s.** Pas de World Partition streaming, pas de cinématique, pas d'écran intermédiaire (§9). | `Restart_FadeDuration = 0.15 s` (`07_TUNING §16`). |
| P8 | **Tout est sur la grille de 100 uu.** Un module hors grille est un bug. Les seules rotations autorisées sont des multiples de 15°. | Kit modulaire, joints propres, pas d'arêtes accrocheuses. |

### Ce qui tue le flow (liste noire)
Angle à 90° sans amorce · plafond bas non signalé · gap dont la longueur dépasse le tableau §2 ·
ennemi placé sur la ligne de course · couloir < 800 uu de large · escalier > `MaxStepHeight` (50 uu) en pleine course ·
zone où il faut s'arrêter pour viser · trigger scripté qui ralentit · sol non coplanaire entre 2 modules ·
mur de wall ride qu'on ne peut pas atteindre en `Falling` · descente qui se termine par un mur.

---

## 2. Métriques du joueur — TABLEAU DE RÉFÉRENCE

### 2.1 Constantes dérivées

```
g_effectif = 980 uu/s²  ×  Gravity (2.4)                 = 2352 uu/s²      [07_TUNING §2]
h_saut     = Jump_ZVelocity² / (2 × g_eff) = 900² / 4704 = 172 uu          [§6]
t_air_saut = 2 × Jump_ZVelocity / g_eff    = 1800 / 2352 = 0.765 s
h_walljump = WallJump_ZVelocity² / (2×g_eff) = 800²/4704  = 136 uu          [§9]
t_air_wj   = 2 × 800 / 2352                              = 0.680 s
v_dash     = Dash_Distance / Dash_Duration = 900 / 0.16   = 5625 uu/s       [§8]
t_chute(h) = √( 2h / g_eff ) = √( h / 1176 )
```

### 2.2 Distance parcourue (LE tableau)

| Vitesse (uu/s) | HUD | Par seconde | Par frame @60 fps | Modules 1600 uu / s | Saut à plat (`t=0.765 s`) | Saut + dash aérien | Wall ride 1.0 s | Wall ride 2.0 s (max) |
|---|---|---|---|---|---|---|---|---|
| 1000 `Speed_Walk` | 100 | 1000 uu | 17 uu | 0.6 | **765** | 1665 | 990 | 1960 |
| 1200 `WallRide_MinEntrySpeed` | 120 | 1200 | 20 | 0.75 | **918** | 1818 | 1188 | 2352 |
| 1500 `Speed_SprintCap` | 150 | 1500 | 25 | 0.94 | **1148** | 2048 | 1485 | 2940 |
| 2000 | 200 | 2000 | 33 | 1.25 | **1531** | 2431 | 1980 | 3920 |
| 2500 `SpeedLines_StartSpeed` | 250 | 2500 | 42 | 1.56 | **1913** | 2813 | 2475 | 4900 |
| 3000 | 300 | 3000 | 50 | 1.88 | **2296** | 3196 | 2970 | 5880 |
| 4000 `FOV_SpeedForMax` | 400 | 4000 | 67 | 2.50 | **3061** | 3961 | 3960 | 7840 |
| 5000 `SpeedLines_FullSpeed` | 500 | 5000 | 83 | 3.13 | **3827** | 4727 | 4950 | 9800 |
| 6000 `Speed_HardCap` | 600 | 6000 | **100** | 3.75 | **4592** | 5492 | 5940 | 11760 |

- **Saut à plat** = `Vitesse × 0.765`. **Saut + dash** = `Vitesse × 0.765 + 900` (le dash met `GravityScale = 0` pendant `Dash_Duration`, il **ajoute** 0.16 s de vol et 900 uu).
- **Wall ride** = `∫ V × WallRide_SpeedRetention^t dt` avec `0.98^t` → `V × 0.99` à 1 s, `V × 1.96` à 2 s.

### 2.3 Règle de dimensionnement des gaps

> **On dimensionne un gap à 70 % de la valeur théorique.** Le joueur n'entre jamais parfaitement à l'horizontale.

| Gap (Safe Way) | Vitesse requise (saut simple) | Gap (Speed Way, dash autorisé) | Vitesse requise |
|---|---|---|---|
| **600 uu** | 1100 uu/s — franchissable en marchant | 1200 uu | ~600 (dash seul suffit) |
| **800 uu** | 1500 uu/s (sprint) | 1600 uu | 1300 |
| **1200 uu** | 2250 uu/s | 2400 uu | 2800 |
| **1600 uu** | 3000 uu/s | 3200 uu | 4300 |
| **2400 uu** | 4500 uu/s — **réservé au Speed Way** | 3600 uu | 5000 |

**Formules employées** (les deux colonnes « Vitesse requise » se reproduisent exactement, arrondi à 50 uu/s près) :

```
marge   = 0.70                       // 30 % de sécurité sur la phase balistique
t_air   = 0.765 s                    // §2.1
d_dash  = 900 uu                     // Dash_Distance, 07_TUNING §8

Safe Way  (saut simple)   :  V = Gap / (marge × t_air)              = Gap / 0.5355
Speed Way (saut + dash)   :  V = (Gap − d_dash) / (marge × t_air)   = (Gap − 900) / 0.5355
```

**Pourquoi la marge ne s'applique pas au dash** : pendant `Dash_Duration`, `GravityScale = 0` et la vélocité
est écrite par la Timeline — les 900 uu sont **déterministes**, indépendants de l'angle d'entrée du joueur.
Seule la phase balistique, elle, dépend de la façon dont le joueur quitte le bord : c'est elle, et elle seule,
qu'on dérate de 30 %.

Vérification : `1600 uu Safe → 1600 / 0.5355 = 2988 → 3000` · `3200 uu Speed → (3200 − 900) / 0.5355 = 4295 → 4300`.

**Plafond dur** : aucun gap obligatoire > **1600 uu**. Au-delà, c'est un Speed Way.

### 2.4 Verticalité

| Manœuvre | Gain de hauteur | Contrainte |
|---|---|---|
| `MaxStepHeight` (marche) | **50 uu** | franchi sans saut, sans perte de vitesse → **taille max d'un décalage de sol** |
| Saut simple | **172 uu** | rebord confortable : **150 uu** |
| Wall jump | **136 uu** au-dessus du point d'accroche | chaîne murs opposés : +136 par saut |
| Dash aérien vertical | ≈ +900 uu si `DashDir.Z = 1` (hors sol, `Dash_ZLockOnGround`) | consomme la charge, cooldown 1.4 s |
| Wall ride 1.0 s | **−44 uu** (`+250×t − ½×588×t²`, `WallRide_GravityScale = 0.25`) | quasi horizontal |
| Wall ride 1.5 s | −287 uu | |
| Wall ride 2.0 s | **−676 uu** | le mur doit descendre avec le joueur |

| Chute depuis | Temps | Distance horizontale @3000 uu/s | Vitesse d'impact Z |
|---|---|---|---|
| 400 uu | 0.58 s | 1750 uu | 1372 uu/s |
| 800 uu | 0.83 s | 2475 uu | 1940 uu/s |
| 1600 uu | 1.17 s | 3500 uu | 2743 uu/s |
| 3200 uu | 1.65 s | 4950 uu | 3880 uu/s |

*(Pas de dégâts de chute dans `07_TUNING` → une chute est gratuite, seule la perte de temps punit. Ne pas ajouter de dégâts de chute.)*

### 2.5 Capsule & gabarits

| Mesure | Valeur | Conséquence pour la géométrie |
|---|---|---|
| Hauteur debout | `2 × CapsuleHalfHeight` = **176 uu** | plafond d'un couloir traversable debout : **≥ 250 uu** |
| Hauteur slide | `2 × CapsuleHalfHeight_Slide` = **88 uu** | **ouverture de slide-gate : 150 uu** (marge 62 uu, < 176 donc slide obligatoire) |
| Rayon | 34 uu | passage mini entre 2 props : **150 uu** (jamais moins) |
| Hauteur des yeux | centre capsule + 64 uu → **152 uu** debout, **108 uu** en slide | placer les repères visuels autour de Z ≈ 150–400 uu |
| Portée de détection wall ride | `CapsuleRadius + WallRide_DetectDistance` = **104 uu** | le mur doit être à ≤ 104 uu du centre de la capsule |

### 2.6 Slide (estimations `[À CALIBRER]`)

Modèle : `v(t) = (V+400) × e^(−Slide_Friction × t)`, `Slide_MaxDuration = 1.2 s`, plancher `Slide_ExitSpeedMin = 1200`.

| Vitesse d'entrée | Vitesse après boost | Distance parcourue en 1.2 s | Vitesse de sortie |
|---|---|---|---|
| 1500 | 1900 | ≈ **1810 uu** | 1200 (plancher) |
| 2000 | 2400 | ≈ 2290 uu | 1486 |
| 3000 | 3400 | ≈ 3240 uu | 2105 |

→ **Longueur utile d'un tunnel de slide : 1600 à 3200 uu.** En descente (`Slide_SlopeAccelBonus`), le timer ne décompte pas : une rampe descendante peut faire 4800 uu.

---

## 3. Le kit modulaire

Emplacement : `Content/OVERDRIVE/Art/Meshes/Modules/`. Nommage `SM_Module_<Type>_<Taille>` (`06_CONVENTIONS §6`).
**Pivot** : coin **X− Y− Z−** (bas / arrière / gauche) pour tout module rectangulaire → snap 50 uu trivial.
Exception : `Pillar`, `Arch`, `Gate` → pivot **bas / centre** (symétriques, tournent sur place).
**Orientation canonique** : la longueur est sur **+X**, la largeur sur **+Y**, la hauteur sur **+Z**. `Rotation = 0` = orienté +X.
**Épaisseur minimale de toute géométrie bloquante : 100 uu** (anti-tunneling, cf. §12).
**Scale autorisé** : uniquement des entiers sur l'axe de longueur (×2, ×3, ×4) des modules marqués « scalable X ». Jamais de scale non uniforme sur un ramp ou un arch.

| # | Asset | Dim. X × Y × Z (uu) | Pivot | Collision preset | Scalable | Rôle |
|---|---|---|---|---|---|---|
| 1 | `SM_Module_Floor_400` | 400 × 400 × 100 | coin | `OD_LevelGeo` | non | remplissage, plateformes de movement section |
| 2 | `SM_Module_Floor_800` | 800 × 800 × 100 | coin | `OD_LevelGeo` | non | dalle standard des couloirs |
| 3 | `SM_Module_Floor_1600` | 1600 × 1600 × 100 | coin | `OD_LevelGeo` | X ×2/3/4 | **dalle des Speed Spaces et arènes** |
| 4 | `SM_Module_Wall_800` | 800 × 100 × 800 | coin | `OD_LevelGeo` | X ×2/3/4 | mur bas / garde-corps |
| 5 | `SM_Module_Wall_1600` | 1600 × 100 × 1600 | coin | `OD_LevelGeo` | X ×2/3/4 | mur de délimitation, fond d'arène |
| 6 | `SM_Module_WallRide_1600` | 1600 × 100 × 800 | coin | **`OD_WallRideSurface`** | X ×2/3/4 | **mur de wall ride court** — matériau dédié obligatoire |
| 7 | `SM_Module_WallRide_3200` | 3200 × 100 × 1600 | coin | **`OD_WallRideSurface`** | X ×2/3 | mur de wall ride long (corridors, boss) |
| 8 | `SM_Module_Ramp_1600x400` | 1600 × 800 × 400 | coin bas | `OD_LevelGeo` | Y ×2/3 | pente **14°** — rampe de lancement / slide descendant |
| 9 | `SM_Module_Ramp_800x400` | 800 × 800 × 400 | coin bas | `OD_LevelGeo` | Y ×2/3 | pente **26.6°** — montée courte, tremplin |
| 10 | `SM_Module_Ramp_800x800` | 800 × 800 × 800 | coin bas | `OD_LevelGeo` | Y ×2 | pente **45°** — sous `WalkableFloorAngle` (50°), franchissable mais coûteux |
| 11 | `SM_Module_Platform_400` | 400 × 400 × 100 | coin | `OD_LevelGeo` | non | plot de saut, jalonnage vertical |
| 12 | `SM_Module_Platform_800` | 800 × 800 × 100 | coin | `OD_LevelGeo` | X ×2 | plateforme d'atterrissage confortable |
| 13 | `SM_Module_Pillar_200` | 200 × 200 × 800 | bas centre | `OD_LevelGeo` | Z ×2/3/4 | colonne — obstacle de slalom en Speed Space |
| 14 | `SM_Module_Pillar_400` | 400 × 400 × 1600 | bas centre | `OD_LevelGeo` | Z ×2/3 | pilier structurel, couverture d'arène |
| 15 | `SM_Module_Arch_800` | 400 × 1000 × 1200 (ouverture 800 L × 800 H) | bas centre | `OD_LevelGeo` | non | **portail de transition** entre 2 zones |
| 16 | `SM_Module_Arch_1600` | 400 × 1800 × 2000 (ouverture 1600 × 1600) | bas centre | `OD_LevelGeo` | non | portail de Speed Space |
| 17 | `SM_Module_Gate_Slide` | 400 × 1000 × 800 (**ouverture 800 L × 150 H**) | bas centre | `OD_LevelGeo` | non | **slide obligatoire** — la seule pièce qui force le slide |
| 18 | `SM_Module_Tunnel_1600` | 1600 × 1000 × 800 (intérieur 800 L × 500 H) | coin | `OD_LevelGeo` | X ×2/3/4 | tunnel bas — tension, transition, compression avant un Speed Space |
| 19 | `SM_Module_Block_200` | 200 × 200 × 200 | coin | `OD_LevelGeo` | non | obstacle sautable / sur-slidable, remplissage d'arène |
| 20 | `SM_Module_Beam_1600` | 1600 × 200 × 200 | coin | `OD_LevelGeo` | X ×2/3 | poutre, garde-corps aérien, marquage de trajectoire |
| 21 | `SM_Module_Edge_800` | 800 × 100 × 50 | coin | `OD_LevelGeo` | X ×2/3/4 | **bordure de bord de gouffre** — lisibilité, jamais bloquant (50 uu = `MaxStepHeight`) |
| 22 | `SM_Module_Hazard_400` | 400 × 400 × 20 | coin | `OD_LevelGeo` | X/Y ×2/3/4 | plaque de danger — signalétique au sol, pas de logique |
| 23 | `SM_Module_TraversalStrip_400` | 400 × 20 × 20 | coin | **`NoCollision`** | Z ×2/3/4 | **liseré de traversée** — métronome de vitesse, posé tous les 800–1600 uu le long des couloirs (`SPEC_ART_DIRECTION §8.1`) |

**23 meshes.** Le kit était verrouillé à 22 ; le n° 23 est ajouté pour concorder avec `SPEC_ART_DIRECTION §8.1`,
qui en fait un élément **obligatoire** de lisibilité de la vitesse — ce n'est pas un mesh de décor optionnel.
Aucun autre mesh d'environnement n'est autorisé en v1 hors props de décor non collisionnables.

> **Renommage v2 — signalé** : `SM_Module_NeonStrip_400` devient **`SM_Module_TraversalStrip_400`**.
> Le « néon » appartenait à la ville nocturne v1 ; en v2 cette bande porte le rouge `OD_Red_Traversal`
> et **signifie « on passe par là »** (`11_ARBITRAGES D3`). Le nom décrit désormais la fonction, pas l'effet.
> Toute autre doc citant `SM_Module_NeonStrip_400` s'aligne sur ce nom.

**Aspect selon la nouvelle DA** (`ArtDirection/PALETTE.md`, `11_ARBITRAGES D2/D3`) :

| Famille de modules | Traitement |
|---|---|
| `Floor_*`, `Wall_*`, `Platform_*`, `Pillar_*`, `Block_*`, `Beam_*`, `Tunnel_*` | **blanc / gris clair**, mat, aucune couleur. Ce sont les faces qui portent la forme, via la lumière et l'ombre portée |
| `WallRide_*`, `Ramp_*` de lancement, `TraversalStrip_400` | liseré émissif **`OD_Red_Traversal`** sur l'arête ou en bande horizontale à Z ≈ 300 uu |
| `Arch_*`, `Gate_Slide` | panneau de **signalétique `OD_Purple_Primary`** (chevrons `»`) posé sur le linteau — un portail dit toujours où l'on va |
| `Hazard_400`, `Edge_800` | **`OD_Red_Danger`** + hachures diagonales foncées |

Règles de fabrication (Blender → FBX, cf. `06_CONVENTIONS §9`) : faces planes, **aucune concavité** (collision simple
box/convex), **normales sorties et lissage correct — la scène est éclairée, une normale retournée se voit maintenant
immédiatement** (`11_ARBITRAGES D2`), UV canal 0 uniquement (**pas de lightmap** : l'éclairage est entièrement
dynamique, Lumen, Static Lighting désactivé), 1 material slot, **Nanite désactivé** (trop peu de tris pour valoir le coût).

### 3.1 Kit de props de ville — `OD_EnvKit_City` (importé le 2026-08-19)

**Les 23 `SM_Module_*` de §3 n'existent toujours pas.** En revanche Louis a produit en amont un kit
de **40 props de ville blanche** (`Art_Source/OD_EnvKit_City.blend` + `Art_Source/EnvKit/*.fbx`),
importés dans **`Content/OVERDRIVE/Art/Meshes/Props/`**.

> **Décision (agent, 2026-08-19) — ils vont dans `Props/`, pas dans `Modules/`.**
> `Modules/` est réservé aux 23 `SM_Module_*` verrouillés ci-dessus ; la clause « aucun autre mesh
> d'environnement n'est autorisé en v1 **hors props de décor** » les couvre exactement.
> Renommer un prop en `SM_Module_*` reviendrait à ouvrir le kit verrouillé sans arbitrage.

Mesuré à l'import (bornes locales, LOD0) :

| Constat | Valeur |
|---|---|
| Meshes | 40 props + `SM_Weapon_LaserPistol` (→ `Player/Meshes/`, cf. `06_CONVENTIONS §9`) |
| Grille | **100 % sur la grille de 100 uu**, sur les 3 axes, sans exception |
| Pivots | coin `X− Y− Z−` ou bas/centre pour les pièces symétriques — conforme à §3 |
| Triangles | **20 à 228** par prop (budget §7.1 : 100–500). Kit complet ≈ **2 900 tris** |
| Collision | **UCX importée depuis le FBX** sur les 41 (`bCustomizedCollision = true`) |
| Nanite | désactivé sur les 41 — conforme `SPEC_ART_DIRECTION §5.5` |
| Material slots | **nommés par token de `PALETTE.md`** (`M_OD_White_Structure`, `M_OD_Red_Traversal`…), 2 à 5 slots par mesh |

**Le slot nommé par token est le bon choix** : la couleur n'est pas dans le mesh. Assigner 10 `MI_`
une fois colore les 40 props d'un coup, et un prop se recolore sans réexport.

#### Écarts à trancher

> **Correction du 2026-08-19.** Une première version de ce tableau accusait le kit de porter du
> « rouge décoratif » sur ~15 props. **C'était faux, et c'était de ma faute** : je n'avais pas lu
> `Docs/Journal/2026-08-18_EnvKit_RooftopCity.md §1`, qui définit explicitement le rouge du kit comme
> *« je peux atterrir / courir dessus »* — arête **haute** de tout prop praticable. Une clim de 300 uu
> se saute et se parcourt : son arête rouge **enseigne** quelque chose. La règle §10.1 est respectée.
> L'entrée A ci-dessous est réécrite en conséquence.

| # | Écart | Conséquence |
|---|---|---|
| A | **Intensité émissive du rouge, pas son emplacement.** 26 props sur 40 portent un slot `M_OD_Red_Traversal`. À `EmissiveIntensity = 8.0` (valeur « surface de traversée », `PALETTE §8`) sur chaque caisse et chaque clim, le plafond *« max 3 couleurs saturées visibles simultanément »* (§10.1 règle 5) saute dans une scène dense | **Déjà identifié par le journal du kit §6, non tranché.** Se règle par `MI_`, pas au modèle : prévoir sans doute deux instances — `MI_Red_Traversal_Wall` à 8.0 pour les vraies surfaces de wall ride, `MI_Red_Traversal_Edge` plus bas pour les arêtes de props. **À tester en jeu** |
| B | **La doc et le moteur se contredisent sur l'orientation.** Le journal du kit §3 affirme *« longueur sur +X UE »*. **Mesuré à l'import : X et Y sont échangés** sur tout le kit — `SM_Billboard_Large` est annoncé `100 × 2400 × 800` et arrive `2400 × 100 × 800` ; `SM_Roof_Edge` annoncé `800 × 100 × 200` arrive `100 × 800 × 200` ; idem pour les 40. Le canon du pistolet pointe `+Y` (bornes Y = −8 → +22) | **Le moteur a raison, la doc a tort** — c'est une mesure, pas une lecture. Soit on réexporte avec le bon mapping d'axes, soit on acte ici que le kit est orienté `+Y` et on aligne les futurs `SM_Module_*` dessus. **Ne pas mélanger les deux conventions** : c'est une source garantie de rotations fausses au blockout |
| C | `SM_Roof_Edge` et `SM_Safety_Rail` font **200 uu de haut** | `SM_Module_Edge_800` est plafonné à **50 uu = `MaxStepHeight`** précisément pour ne jamais bloquer. À 200 uu ces deux props **arrêtent le joueur** — parfait comme parapet infranchissable, inutilisable comme bordure de lisibilité. Le module `Edge_800` reste donc à produire |
| D | `lightMapCoordinateIndex = 1` sur les 41 | Le journal du kit §5 demandait `Generate Lightmap UVs ✘`, mais `StaticMeshTools.import_file` **n'expose pas** cette option (`12_PIEGES §5.11`) : un canal UV de lightmap a été généré alors que le Static Lighting est désactivé. Mémoire gaspillée, aucun effet visuel. Cosmétique |
| E | **Destination des 8 bâtiments et toits.** Le journal du kit §5 les envoie dans `Modules/` ; ils sont dans `Props/` | Choix de l'agent, motivé par le verrouillage de `Modules/` aux 23 `SM_Module_*`. **À trancher par Louis** — un `AssetTools.move` suffit dans les deux sens |

---

## 4. Grammaire des espaces

Les tags correspondent à `E_LevelSection` (`08_DATA_SCHEMAS §1`) et servent de `SectionTag` dans `S_EnemySpawnEntry`.

### 4.1 `SpeedSpace` — Espace de vitesse
| | |
|---|---|
| Dimensions | **min 4000 × 1600 × 800** · cible 8000–16000 × 2400–4000 × 1200–2400 · (mins durs `07_TUNING §17` : largeur 800, hauteur 600) |
| Durée de traversée | 2–5 s à 3000 uu/s |
| Ennemis | **0 à 3**, jamais sur la ligne de course, toujours latéraux ou surélevés |
| Enseigne | conserver et accumuler : bunny hop, air strafe, slide-jump |
| Obligatoire | sol continu ou gaps ≤ 800 uu · au moins 1 rampe descendante · ligne de fuite visible sur toute la longueur |
| Interdit | virage > 45° · plafond < 800 uu · obstacle non visible à 3000 uu (§5) |

```
   ┌───────────────────────────────────────────────────────────┐  ← plafond 1600+ ou ciel ouvert
   │   ▓         ▓                   ▓                          │
   │      ▓  (piliers 200, slalom optionnel)         ╲          │  ╲ = rampe descendante
   ▶  ════════════════════════════════════════════════ ╲════════▶
   │        ○(shooter surélevé, latéral)                 ╲      │
   └───────────────────────────────────────────────────────────┘
   |◄──────────────── 8000 – 16000 uu ─────────────────────────►|
   largeur 2400 uu min — le joueur choisit sa ligne
```

### 4.2 `Combat` — Combat Arena
| | |
|---|---|
| Dimensions | **min 2400 × 2400 × 800** · cible 3200–4800 × 3200–4800 × 1200 |
| Durée | 6–12 s |
| Ennemis | **4 à 6** — plafond dur **6, 8 en L6 uniquement** (`Heat_Max` = 9 tirs avant overheat, cf. §8.5) |
| Enseigne | tuer sans s'arrêter, headshot en mouvement, wall slam |
| Obligatoire | **2 entrées/sorties minimum** · **1 mur « slammable » à 400–1200 uu derrière un groupe** · 2 niveaux d'altitude · une ligne de traversée directe qui ne croise aucun ennemi |
| Interdit | cul-de-sac · arène fermée par un trigger · ennemi hors ligne de vue à l'entrée |

```
   entrée ▶                                       ▶ sortie A (rapide, haute)
   ═══════╗   ○       ○                    ┌────┐ ═══════
          ║      ▓▓▓        ○   ██◄ mur slammable
          ║   ○         ▓▓▓                └────┘
          ╚════════════════════════════════════════ ▶ sortie B (sol, safe)
             |◄──────── 3200 uu ────────►|
   ○ = ennemi   ▓ = couverture (Block_200 / Pillar)   ██ = mur d'impact
```

### 4.3 `MovementSection` — Section de mouvement
| | |
|---|---|
| Dimensions | 3200–8000 de long · largeur 1200–2400 · hauteur libre 1200+ |
| Durée | 5–10 s |
| Ennemis | **0 à 2**, statiques, jamais pendant une figure |
| Enseigne | une mécanique précise à la fois (gap / slide-gate / wall ride / dash) |
| Obligatoire | **3 à 6 obstacles maximum** · chaque obstacle a une solution Safe ET une Speed · bord de gouffre marqué par `SM_Module_Edge_800` |
| Interdit | plus de 2 mécaniques différentes exigées d'affilée avant que le joueur les maîtrise (voir §7) |

```
        ┌──┐        ┌──┐              ╔═══════════╗  ← SM_Module_Gate_Slide (150 uu)
   ═════┘  └════════┘  └══════════════╝           ╚════════▶
        gap 800     gap 1200            slide 1600 uu
        (sprint)    (sprint+dash)
```

### 4.4 `SpeedSpace` variante — Wall Ride Corridor
| | |
|---|---|
| Écartement des murs | **600 (min) à 1400 (max) uu** — `07_TUNING §17`, strict |
| Longueur des murs | 1600 à 4800 uu (`SM_Module_WallRide_1600/3200`) |
| Hauteur des murs | **≥ 800 uu**, 1600 si la traversée dépasse 1.2 s (le joueur descend, cf. §2.4) |
| Ennemis | 0 à 2, **au-dessus ou au bout**, jamais sur le mur |
| Enseigne | alternance de wall rides, wall jump, `SameWallCooldown` |
| **Règle critique** | `BPC_WallRide` ne trace **qu'en `MOVE_Falling`** (`SPEC_MOVEMENT §9.1`) → **le corridor doit être précédé d'un déclencheur d'envol** : gap ≥ 600 uu, ressaut de 100 uu, ou fin de rampe. Sans ça, le wall ride est impossible et le joueur ne comprend pas pourquoi. |
| Sol | absent (gouffre) ou 400 uu plus bas — sinon le joueur reste au sol et n'accroche jamais |

```
   vue de dessus                        coupe
   ║════════════════════║               ║      ║
   ║  ↗       ↘      ↗  ║  murs         ║  ↗↘  ║  hauteur 800-1600
   ║════════════════════║  écart 1000   ║______║
   ▲ gap d'entrée 800 uu                gouffre / sol -400
```

### 4.5 `MovementSection` variante — Vertical Section
| | |
|---|---|
| Dimensions | empreinte 1600–3200 × 1600–3200 · hauteur totale **≤ 1600 uu** |
| Durée | 4–8 s |
| Ennemis | **0** en montée. 1–2 en haut, visibles d'en bas. |
| Enseigne | wall jump enchaîné, dash vertical |
| Obligatoire | **écart vertical entre paliers ≤ 150 uu** (saut simple) ou **≤ 136 uu au-dessus d'un mur de wall ride** (wall jump) · toujours une descente rapide en sortie (rampe, chute libre) |
| Interdit | plus de 4 paliers · montée en spirale (désorientation) · palier atteignable uniquement au dash (cooldown 1.4 s = punition arbitraire) |

```
                       ┌────┐ ▶ sortie (chute + Speed Space)
                 ┌────┐│    │      +150
           ┌────┐│    │└────┘      +150
     ┌────┐│    │└────┘            +150
   ══┘    └┘    └                  +150   ← total 600 uu, 4 paliers max
```

### 4.6 `FinalRun` — Course finale
| | |
|---|---|
| Dimensions | **4000 à 10000 uu**, large 2400+, **descendante** (dénivelé −400 à −1600) |
| Durée | 3–6 s |
| Ennemis | **0 à 3 Grunts**, décoratifs, tués en passant |
| Enseigne | rien. C'est la récompense. Vitesse maximale de la run. |
| Obligatoire | ligne droite ou courbe ≤ 30° · `BP_LevelEndTrigger` visible depuis le début de la section · aucun gap · aucun plafond bas |
| Interdit | tout ce qui peut faire rater : gap, slide-gate, virage serré, ennemi dangereux |

```
   ▶ ══════╲
            ╲══════════╲
                        ╲═════════════════╗
                                          ║ ▓▓ END ▓▓  ← BP_LevelEndTrigger, 800×2400×800
   dénivelé -800 uu sur 8000 uu           ╚═══════════
```

### 4.7 `BossArena`
Cf. `Docs/Specs/SPEC_BOSS.md`. Dimensions imposées par `07_TUNING §13` : **Boss 01 → `Boss01_ArenaDiameter` = 4800 uu**
(arène circulaire/carrée 4800²) · **Boss 02 → `Boss02_ArenaLength` = 7000 uu**.
Contraintes de LD : **fermée mais large (min 4800 × 4800 × 1600)**,
2 murs `OD_WallRideSurface` opposés sur les côtés (écart 1400 uu max non applicable ici : ce sont des murs de contour),
couverture destructible **non** — uniquement des `Pillar_400` fixes, sol plat sans gap (pas de mort par chute pendant un boss).

---

## 5. Lisibilité à haute vitesse

### 5.1 Distance minimale de visibilité avant un élément

`D_visible = Vitesse × (T_perception + T_exécution)`
- `T_perception` = 0.25 s (voir + identifier)
- `T_exécution` : obstacle simple 0.35 s · choix de trajectoire 0.75 s · engagement de combat 1.15 s

| Vitesse | Obstacle simple (0.6 s) | **Bifurcation Safe/Speed (1.0 s)** | Ennemi à engager (1.4 s) |
|---|---|---|---|
| 1500 | 900 uu | 1500 uu | 2100 uu |
| 2000 | 1200 | 2000 | 2800 |
| 3000 | **1800** | **3000** | **4200** |
| 4000 | 2400 | 4000 | 5600 |
| 5000 | 3000 | 5000 | 7000 |

> **Règle de construction** : on dimensionne pour **3000 uu/s** en niveau 1–3 et **4000 uu/s** en niveau 4–6.
> Concrètement : *rien d'important ne doit apparaître à moins de 3000 uu (L1–L3) / 4000 uu (L4–L6) du joueur.*
> Corollaire : les murs de délimitation ne doivent jamais cacher le tronçon suivant → utiliser `SM_Module_Wall_800`
> (bas) plutôt que `Wall_1600` sur les bords intérieurs des virages.

### 5.2 Lisibilité sur fond CLAIR — la contrainte inversée

> **Le monde est blanc et en plein soleil** (`11_ARBITRAGES D2`, `PALETTE.md §1`).
> La règle de la v1 (« le fond est noir, l'émissif fait tout ») est **caduque**.
> **Sur fond clair, une information de gameplay doit être foncée ou très saturée pour exister.**
> Un élément blanc lumineux posé sur un mur blanc lumineux n'est pas discret : il est **invisible**.

Trois conséquences directes pour le level designer :

1. **Le décor est le fond, pas le sujet.** Sol et murs neutres restent blanc/gris clair, **sans aucune couleur**.
   Tout ce qui est coloré est fonctionnel, sans exception dans les 6 niveaux.
2. **Un signal se lit par saturation, pas par luminosité.** On ne monte plus l'`EmissiveIntensity` pour
   « faire ressortir » : sur fond clair ça délave. On prend une teinte saturée de `PALETTE.md §3` et on
   la pose sur une surface **plus foncée que le mur qui la porte**.
3. **Les ombres portées sont une information.** Elles ne sont plus décoratives : c'est ce qui donne
   la profondeur, l'assise des objets et la lecture des arêtes (§5.2.2).

#### 5.2.1 Code couleur / matériau (rôles sémantiques)

À décliner en `MI_` sur `M_Toon_Base` (`06_CONVENTIONS §2`). Palette exacte : `Docs/ArtDirection/PALETTE.md`
— **ici on fixe les rôles, la palette fixe les teintes**. Un rôle = un `MI_` = une signification.

| Rôle | `MI_` | Token | Signal visuel | Où |
|---|---|---|---|---|
| Sol praticable | `MI_Env_Floor` | `OD_White_Structure` | valeur claire, mate, motif ≥ 400 uu, **aucune couleur** | tout sol |
| Mur neutre / bloquant | `MI_Env_Wall` | `OD_White_Structure` / `OD_Grey_Shadow` sur les faces latérales | clair et **désaturé** — c'est le fond | délimitation |
| **Wall ride / rail / boost** | `MI_Env_WallRide` | **`OD_Red_Traversal`** | **liseré émissif horizontal à Z ≈ 300 uu** sur toute la longueur du mur | uniquement `OD_WallRideSurface` |
| **Direction à suivre** | `MI_Env_Sign` | **`OD_Purple_Primary`** | chevrons `»` et panneaux, sur fond foncé (`OD_Navy_Deep`) | portails `Arch_*`, murs de virage, entrées de section |
| **Danger / mort** | `MI_Env_Hazard` | **`OD_Red_Danger`** | hachures diagonales foncées + liseré saturé | `SM_Module_Hazard_400`, bords de gouffre, kill volume |
| Franchissable / sautable | `MI_Env_Traversable` | `OD_Red_Traversal` (liseré fin) | arête supérieure soulignée | `Block_200`, `Beam`, rebords ≤ 150 uu |
| **Speed Way (raccourci)** | `MI_Env_SpeedWay` | **`OD_Red_Traversal`, pulsé** | même teinte que le wall ride, **animée** — c'est le pouls qui distingue le raccourci de la surface ordinaire | plateformes et murs du chemin rapide |
| Objectif / fin | `MI_Env_Goal` | `OD_Purple_Primary` + `OD_Gold_Rank` | grande surface foncée + chevrons, visible de loin | `BP_LevelEndTrigger`, checkpoints |

**Le cyan n'existe plus** (`11_ARBITRAGES D3`). Aucun `MI_` d'environnement n'emploie
`OD_Magenta_Player` (réservé au joueur) ni `OD_Amber_Enemy` (réservé aux ennemis) : si le décor porte
la couleur du joueur ou celle d'un ennemi, le joueur cesse de lire l'espace.

#### 5.2.2 Comment on voit une arête blanche devant un ciel bleu clair

C'est le problème n°1 de la nouvelle DA : `OD_White_Structure` (mur) et `OD_Sky_Pale` (horizon) sont
deux valeurs claires très proches. Une silhouette de bâtiment se découpe mal, un bord de toit disparaît,
et le joueur rate un gap qu'il n'a jamais vu. Quatre parades, **cumulatives, toutes obligatoires** :

| # | Parade | Mise en œuvre |
|---|---|---|
| 1 | **Ombres portées** | L'**inclinaison du soleil est donnée par monde dans `PALETTE.md §4`** (W1 zénith, W2 rasant, Boss 01 diffus, Boss 02 contre-jour) et ne se choisit pas au niveau. Une ombre projetée au sol *sous* une plateforme est ce qui dit sa hauteur et son bord : c'est le rendu, pas un ornement (`11_ARBITRAGES D2`). ⚠️ **World 1 est le cas difficile** — un soleil au zénith produit des ombres courtes, donc peu d'information de bord : c'est là que les parades 2, 3 et 4 doivent porter l'essentiel de la lecture. |
| 2 | **Valeur par orientation de face** | Faces vers le ciel = `OD_White_Structure`, faces latérales = `OD_Grey_Shadow`, faces en contre-jour = `OD_Grey_Deep`. Trois valeurs sur un même bloc blanc → le volume se lit même sans ombre. Réglé une fois dans `M_Toon_Base`, pas mesh par mesh. |
| 3 | **Occlusion de contact** | Un cerne foncé au raccord sol/mur et sous chaque plateforme. Sans lui, tout flotte. |
| 4 | **Outline** | Le post-process Sobel (`11_ARBITRAGES D2`) trace le contour en `OD_Navy_Ink`. **C'est le filet de sécurité, pas la solution** : si un volume n'est lisible *que* grâce à l'outline, la géométrie ou la lumière sont à refaire. |

> **Test obligatoire, à chaque fin de blockout** : se placer au sol, regarder l'horizon, capturer.
> Si une arête de bâtiment se confond avec le ciel, on baisse l'angle du soleil ou on assombrit
> les faces latérales — **on n'ajoute jamais une couleur pour compenser** : la couleur est réservée
> au gameplay (§5.2.1).

**Règle du contraste** : le contraste de **valeur** (clair/sombre) porte la lecture de la forme,
la **couleur** porte la lecture de la fonction. Un niveau doit rester lisible en niveaux de gris — teste-le
avec le viewmode `Lit` + saturation 0 dans le post-process. Si tu ne distingues plus le sol du mur ni le mur
du ciel, refais les **valeurs** et l'**angle du soleil**, pas les teintes.

### 5.3 Anti-motion-sickness

| Règle | Valeur | Source |
|---|---|---|
| Pas de motif haute fréquence sur les murs longeant la course | détail minimal **400 uu**, jamais de rayures < 100 uu | à 4000 uu/s, 100 uu = 25 ms → stroboscope |
| Pas de roulis caméra ajouté par le niveau | seuls `WallRide_CameraTilt` (12°) et `CameraTilt_Strafe` (2.5°) existent | `07_TUNING §16` |
| Sol jamais uniforme | repères tous les **1600 uu** (changement de `MI_` ou `Edge` module) pour donner la sensation de vitesse | |
| Pas de plafond bas prolongé | `Tunnel_1600` : max ×3 d'affilée (4800 uu) | compression = nausée |
| Horizon stable | pas de virage vertical > 15° enchaîné | |
| FOV | ne jamais compenser un couloir étroit par le FOV : élargir le couloir | `FOV_Base` = 100 fixe |

### 5.4 Signaler un raccourci sans tutoriel
1. **Le rendre visible depuis le Safe Way** — le joueur doit le voir *pendant* qu'il prend le chemin lent.
2. **`MI_Env_SpeedWay` émissif** : une seule signature dans tout le jeu, apprise en L1.
3. **Le point d'entrée est aligné avec la trajectoire naturelle** : une rampe qui pointe vers lui, jamais un saut à 90°.
4. **Aucun texte, aucun marqueur UI.** Si le raccourci a besoin d'être expliqué, il est mal placé.

---

## 6. Safe Way / Speed Way

### 6.1 Règles de conception
| Règle | Valeur |
|---|---|
| Gain de temps par raccourci | **1.5 à 4 s** sur un niveau de 120 s |
| Nombre de raccourcis par niveau | **3 à 5** (L1 : 2) |
| Gain cumulé cible | 8–18 s = **7 à 15 %** du temps du niveau — le reste du delta expert (`07_TUNING §17` : run expert = 55–65 % du temps débutant) vient du momentum, pas des raccourcis |
| Coût d'un échec de Speed Way | **retomber sur le Safe Way**, jamais la mort, jamais un checkpoint |
| Exigence d'exécution | 1 mécanique par raccourci en L1–L3, 2 max en L4–L6 |
| Lisibilité | le Speed Way est visible ≥ 1.0 s avant sa bifurcation (§5.1) |

### 6.2 Pattern A — « The High Line » (route parallèle surélevée)
Le Safe Way est au sol. Le Speed Way passe 400–800 uu au-dessus, plus court et plus droit.
Entrée par une rampe `Ramp_1600x400` qui existe **sur** la ligne de course : le joueur monte sans détour.
Retombée automatique sur le Safe Way en fin de section.

```
                    ╔═════════════════════════════╗        Speed Way (+800)
              ╱─────╝   (gap 1200)  ▓▓  (gap 1200) ╚────╲   ~2.5 s gagnées
   ═════════╱══════════════════════════════════════════════╲═════════▶
              Safe Way : contourne, 3 virages, sol
```

### 6.3 Pattern B — « The Gap » (la ligne droite au-dessus du vide)
Le Safe Way contourne un gouffre par un pont latéral. Le Speed Way le franchit tout droit :
gap de **2400 uu** (exige ≥ 4500 uu/s, ou 3000 uu/s + dash aérien). Bord marqué par `Edge_800` + `MI_Env_Hazard`.

```
   vue de dessus
        ┌──────────────┐
        │   pont safe  │  ← +2.0 s
   ▶════┤              ├════▶
        │░░░░ VIDE ░░░░│
   ▶ ─ ─ ─ ─ 2400 uu ─ ─ ─ ─▶   Speed Way : tout droit, plein régime
        └──────────────┘
```

### 6.4 Pattern C — « The Wall Cut » (couper un virage en wall ride)
Le Safe Way suit un virage à 90°. Le Speed Way part en `WallRide_3200` sur la corde extérieure et
recoupe la sortie du virage. L'entrée est un ressaut de 100 uu qui met le joueur en `Falling` (obligatoire, §4.4).

```
                     ║ mur WallRide (3200)
   ▶═══════╗  ↗ ─ ─ ─╫─ ─ ─ ↘
           ║ /       ║         ╲
           ║/  virage safe      ╲
           ╚══════════╗          ╲
                      ╚═══════════▶
   ressaut d'entrée : Block_200 posé au sol, 100 uu de haut
```

**Contrat de chaque pattern** : le Speed Way ne contient **aucun ennemi**. Vitesse et combat ne se cumulent
jamais dans le même choix — sinon le joueur perd sur les deux tableaux et le raccourci devient un piège.

---

## 7. Courbe d'apprentissage — les 6 niveaux + 2 boss

> **Ambiances : `ArtDirection/PALETTE.md §4` fait autorité** pour les 4 ambiances
> (World 1 *Ascension*, World 2 *Redline*, Boss 01, Boss 02) : ciel, structure, ombre, accent de
> signalétique, soleil et densité de fog. Le décor reste **blanc partout** — ce qui change d'un monde
> à l'autre, c'est la **lumière**, pas les murs. Un `PDA_WorldData` par ambiance, poussé par
> `BP_LightingRig` (`11_ARBITRAGES D33`). Les thèmes décrits ci-dessous sont des intentions de
> **structure et de densité**, jamais des consignes de couleur.

Légende : **N** = nouveau · **R** = renforcé · **A** = supposé acquis.

| | L1 Ignition | L2 Redline | L3 Crossfire | Boss 1 | L4 Freefall | L5 Slipstream | L6 Overdrive | Boss 2 |
|---|---|---|---|---|---|---|---|---|
| Sprint / slide | **N** | R | A | A | A | A | A | A |
| Saut / gap | **N** | R | A | A | A | A | A | A |
| Bunny hop | — | **N** | R | A | A | R | A | A |
| Air strafe | — | **N** | R | A | R | **R+** | A | A |
| Dash | **N** | R | R | R | A | A | A | A |
| Wall ride / wall jump | — | — | **N** | R | **R+** | A | A | R |
| Laser / headshot | **N** | R | R | R | A | A | A | A |
| Melee + wall slam | — | — | **N** | R | R | — | R | R |
| Slide-gate / tunnel | — | **N** | R | — | R | A | A | — |
| Verticalité | — | — | — | — | **N** | — | R | — |

### `L_W1_01_Ignition` — *Intro mouvement*
Thème : hangar de départ, blocs simples, éclairage neutre. **Durée 90–110 s. 12 ennemis** (Grunts uniquement).
Mécanique dominante : **sprint → slide → saut**. 2 raccourcis seulement.
1. START : couloir 1200 large, un Grunt statique à 2000 uu → le joueur tire en marchant.
2. INTRO : première rampe descendante + premier gap de **600 uu** (franchissable en marchant : personne ne rate).
3. SPEED SPACE #1 : 8000 × 2400, vide, 3 piliers. Le HUD monte au-dessus de 2000 pour la première fois.
4. COMBAT #1 : 4 Grunts, arène 2400², un mur slammable visible mais non nécessaire.
5. FINAL RUN : 5000 uu descendants, 2 Grunts, `BP_LevelEndTrigger`.

### `L_W1_02_Redline` — *Grandes sections de vitesse*
Thème : viaduc ouvert, ciel visible, longues lignes. **Durée 110–130 s. 16 ennemis** (Grunts + 3 Shooters).
Mécanique dominante : **conservation du momentum** (bunny hop, air strafe).
1. Rampe de lancement immédiate → SPEED SPACE de **16000 uu**, le plus long du jeu, sol continu.
2. Premier `Gate_Slide` : le tunnel est la seule ouverture, apprentissage par nécessité.
3. Enchaînement de 4 gaps 800/1200/800/1200 → le bunny hop devient rentable.
4. COMBAT : 6 ennemis dont 2 Shooters **latéraux** (§8), arène 3200².
5. FINAL RUN descendante de 8000 uu.

### `L_W1_03_Crossfire` — *Movement + combat*
Thème : complexe industriel, verticalité modérée, premiers murs d'accent. **Durée 130–150 s. 22 ennemis** (+ 2 Tanks).
Mécanique dominante : **wall ride** et **melee/wall slam**.
1. Premier Wall Ride Corridor : murs écartés de **1000 uu**, gap d'entrée 800, sol supprimé. Isolé, sans ennemi.
2. COMBAT #1 : 5 ennemis dont 1 Tank dos à un mur → le wall slam se découvre tout seul.
3. SPEED SPACE avec 2 Shooters surélevés : tirer **en** courant.
4. MOVEMENT SECTION : wall ride + gap combinés, Safe Way au sol.
5. COMBAT #2 (6 ennemis — plafond de poche §8.5, arène 4000²) → FINAL RUN.

### `L_W1_Boss` — *Boss 1*
Arène **4800²** fermée (`Boss01_ArenaDiameter`, `07_TUNING §13`), 2 murs de wall ride opposés, 4 `Pillar_400`.
**90–120 s.** 6 adds en phase 2.
Teste : garder de la vitesse dans un espace fermé. Cf. `SPEC_BOSS.md`.

### `L_W2_04_Freefall` — *Movement avancé*
Thème : structure suspendue, gouffres partout, verticalité descendante. **Durée 140–160 s. 18 ennemis.**
Mécanique dominante : **wall ride enchaîné + dash aérien + première Vertical Section**.
1. Chute d'entrée de 1600 uu dans un Speed Space (le niveau commence en l'air).
2. VERTICAL SECTION : 4 paliers à +150, sortie par chute libre.
3. Corridor de wall ride en **alternance** (murs opposés, 1400 uu, `SameWallCooldown` respecté par la longueur).
4. COMBAT sur plateformes séparées par des gaps de 1200 : impossible de camper.
5. FINAL RUN : chute contrôlée de 2400 uu sur 10000 uu de long.

### `L_W2_05_Slipstream` — *Vitesse optimisée*
Thème : tunnel/canyon, lecture pure, peu de décor. **Durée 100–120 s (le plus court). 15 ennemis.**
Mécanique dominante : **optimisation** — 5 raccourcis, le niveau est fait pour être rejoué.
1. Aucune section d'apprentissage : le niveau démarre à pleine vitesse (rampe immédiate).
2. 3 Speed Spaces enchaînés, séparés uniquement par des transitions de 1600 uu.
3. Les 5 Speed Ways sont tous du Pattern A ou B, aucun n'est obligatoire.
4. 2 poches de combat de 4 ennemis maximum, traversables sans s'arrêter.
5. FINAL RUN de 10000 uu, la plus rapide du jeu. Objectif : dépasser 5000 uu/s au moins une fois.

### `L_W2_06_Overdrive` — *Gauntlet final*
Thème : synthèse, tous les modules, densité maximale. **Durée 160–180 s. 30 ennemis** (tous types).
Mécanique dominante : **tout, enchaîné, sans temps mort**. 4 raccourcis, tous à 2 mécaniques.
1. INTRO courte (10 s) puis jamais de répit : la structure alterne combat/vitesse toutes les 8–12 s.
2. Combat #1 (8) → Wall ride corridor sous le feu de 2 Shooters surélevés.
3. Vertical Section suivie immédiatement d'un Speed Space (montée → récompense).
4. Combat #2 (8, dont 2 Tanks — plafond L6 §8.5) dans une arène à 3 niveaux.
5. FINAL RUN de 8000 uu avec 3 Grunts sur la ligne : dernier test de tir en pleine vitesse.

### `L_W2_Boss` — *Boss 2*
Arène allongée de **7000 uu** de long (`Boss02_ArenaLength`, `07_TUNING §13`), 2 étages, murs de wall ride
sur les 4 côtés. **120–150 s.** 10 adds répartis sur 2 phases.

---

## 8. Placement des ennemis

### 8.1 Temps de réaction disponible
`T = Distance / Vitesse`. Le joueur a besoin de **1.4 s** pour identifier + viser + tirer (§5.1).

| Vitesse | Distance mini d'apparition d'un ennemi | Distance mini d'un ennemi **qui attaque** |
|---|---|---|
| 2000 uu/s | 2800 uu | 4000 uu |
| 3000 uu/s | **4200 uu** | **6000 uu** |
| 4000 uu/s | 5600 uu | 8000 uu |

`Laser_Range` = 15000 uu → jamais limitant. C'est **la ligne de vue du niveau** qui limite : un ennemi doit être
visible depuis ≥ 4200 uu, donc une arène de combat ne doit pas être introduite par un virage aveugle.

### 8.2 Règles par archétype

| Archétype | `DetectionRange` | `AttackRange` | Placement |
|---|---|---|---|
| **Grunt** (550 uu/s, charge à 200) | 3000 | 200 | Par groupes de 2–4, **sur les côtés** de la ligne de course. Il ne rattrape jamais le joueur (550 < 1000) : il sert de cible mobile et de source de style, pas de menace. |
| **Shooter** (350 uu/s) | 5000 | 4500 | **Toujours latéral ou surélevé, à 30–90° de l'axe de course.** Jamais frontal (voir 8.3). Écart latéral cible : 1600–3200 uu. Élévation : +400 à +1200. |
| **Tank** (250 uu/s) | 3500 | 350 | **Bloqueur mou** : sur ou près de la ligne, adossé à un mur slammable. Il oblige à contourner ou à melee, jamais à s'arrêter. Max 2 par arène. |

### 8.3 Le Shooter frontal ne marche pas — démonstration
`Projectile_Speed = 2200 uu/s`. Un Shooter à `AttackRange` (4500 uu) face au joueur :
- temps de vol du projectile : `4500 / 2200 = 2.05 s`
- temps du joueur pour couvrir 4500 uu à 3000 uu/s : `1.5 s`

→ **le joueur arrive avant le projectile.** Un Shooter frontal ne menace jamais et donne un tir gratuit.
Placé à **90° de l'axe** à 2400 uu, le projectile croise la trajectoire en 1.1 s : c'est là que la mécanique existe.

### 8.4 Un ennemi crée un choix, pas un mur

| ✅ Crée un choix | ❌ Est un mur |
|---|---|
| Placé **à côté** de la ligne rapide : le tuer coûte 0.3 s mais donne du style | Placé **sur** la ligne, obligatoire à tuer |
| Groupe visible d'avance : le joueur choisit son ordre de kill | Groupe qui spawn derrière le joueur |
| Tank adossé à un mur : melee (rapide, stylé) ou contournement (safe) | Tank dans un couloir de 1200 uu |
| Shooter surélevé : headshot en l'air ou ignorer et encaisser | Shooter caché derrière une colonne |
| Ennemi qui garde un Speed Way (le raccourci a un prix) | Ennemi qui garde le Safe Way |

### 8.5 Budget par poche de combat
- **Maximum 6 ennemis par poche**, 8 en L6 uniquement.
  Justification : `Heat_Max`/`Heat_PerShot` = **9 tirs** avant overheat (`07_TUNING §11`). 6 Grunts en headshot = 6 tirs, marge pour 3 ratés.
- **≥ 3 s de mouvement pur entre deux poches** : `Heat_DecayDelay` (0.5) + `100/Heat_DecayRate` (2.2) = **2.7 s** pour refroidir complètement.
- Aucun spawn hors champ. Tous les ennemis d'une section sont posés dans le niveau et activés par `BP_LevelManager`
  via le `SectionTag` de `S_EnemySpawnEntry` (`08_DATA_SCHEMAS §2`).
- **Wall slam** : `WallSlam_MinImpactSpeed = 1500`, `Melee_Knockback = 3500` → un mur à **400–1200 uu** derrière un ennemi
  garantit le slam. Au-delà de ~1600 uu, l'impulsion est trop retombée : le slam ne déclenche pas et le joueur croit avoir raté.

---

## 9. Checkpoints, start et fin

### 9.1 Start
- `PlayerStart` orienté **dans l'axe de la première ligne de course**, jamais face à un mur.
- Devant lui : **2000 uu de ligne droite dégagée minimum** (0.7 s à pleine vitesse) avant le premier élément.
- `DA_Level_*.IntroHintText` (`PDA_LevelData`) affiche 1 ligne max, disparaît à 800 uu/s. Aucun tutoriel bloquant.

### 9.2 `BP_Checkpoint`

> **Un checkpoint ne rend pas une vie.** Il ne fait qu'une chose : **définir le point de respawn**
> dans le niveau courant. Mourir coûte **une vie sur `Run_MaxLives`** (`07_TUNING §18`) et
> `Score_DeathPenalty`, quel que soit le nombre de checkpoints franchis. Flux complet de la mort :
> `05_ARCHITECTURE §4` (`11_ARBITRAGES D1`). Un checkpoint ne restaure ni le style, ni les kills,
> ni le chrono (`SPEC_SCORE_RANK §5`).

- **0 à 2 par niveau** (`07_TUNING §17`). Répartition : L1–L2 = 1, L3–L4 = 2, L5 = 1, L6 = 2, boss = 0.
- **Viser le haut de la fourchette : 2 dès qu'un niveau contient plus d'une section à risque de mort.**
  C'est un vrai changement d'équilibre : avec `Run_MaxLives` vies pour `Run_LevelCount` niveaux
  (`07_TUNING §18`), un niveau avare en checkpoints devient doublement punitif — le joueur perd
  une vie **et** doit refaire du chemin déjà acquis. Le checkpoint ne réduit pas le coût de la mort,
  il empêche seulement de le payer deux fois.
- **Le nombre de checkpoints ne compense jamais un niveau trop dur.** Si un passage tue de façon
  répétée, c'est la géométrie qu'on corrige (§10.2 étape 4), pas le nombre de points de reprise.
  Les leviers d'équilibrage des vies sont `Run_MaxLives` et `Run_LivesRefillOnBoss` (`07_TUNING §18`),
  **jamais** le level design.
- **0 checkpoint** reste réservé aux **boss** (arène unique, mort = reprise du combat au début) et,
  à la rigueur, à un niveau court entièrement sans gouffre.
- **Où** : à l'**entrée** d'une section difficile, jamais à sa sortie. Idéalement juste avant une Combat Arena
  ou une Movement Section, **sur un sol plat en descente légère** pour que le respawn ne parte pas à 0.
- **Jamais** dans un Speed Space, jamais sur un Speed Way, jamais en l'air.
- Volume : `Box` de **2400 × largeur du couloir × 800**, traversant tout le passage → impossible à manquer.
- Enregistre : transform du joueur, rotation, `E_LevelSection` courante, snapshot des ennemis morts, temps écoulé.
  Marqué `MI_Env_Goal`, sonore et visuel bref (< 0.3 s), **ne ralentit pas le joueur**.
- **Franchir un checkpoint doit être vu** : c'est la seule bonne nouvelle d'un système à 3 vies.
  Panneau `OD_Purple_Primary` traversant le couloir + son court. Aucun arrêt, aucun texte à lire.

### 9.3 `BP_LevelEndTrigger`
- Box de **1600 × largeur totale × 1200**, placé en fin de Final Run, **visible depuis ≥ 4000 uu**.
- Traverse tout le couloir : aucune trajectoire ne peut le contourner (tester le Speed Way le plus extrême).
- Déclenche la chaîne `05_ARCHITECTURE §4` : `ComputeScore` → `WBP_Results` → `WBP_LootChest`.
- **Ne stoppe pas le joueur** : le fondu part pendant qu'il court encore.
- **Aucune salle de fin à construire** : le coffre est un écran UI plein écran, pas un actor de niveau
  (`SPEC_LOOT_UPGRADES §2.3`). Le niveau se termine sur la Final Run, point.

### 9.4 Comment le restart reste instantané
| Règle | Détail |
|---|---|
| **Pas de World Partition** | Niveaux de 1–3 min → level persistant unique, non streamé. Un WP + streaming coûte 200–800 ms de hitch au respawn. |
| **Pas de `OpenLevel` au respawn** | Respawn = `SetActorLocation` + reset de la vélocité + reset des ennemis de la section courante uniquement. `OpenLevel` est réservé au passage au niveau suivant. |
| **Reset par section** | `BP_LevelManager` ne réinitialise que les ennemis dont le `SectionTag` ≥ celui du checkpoint. |
| **Fondu court** | `Restart_FadeDuration = 0.15 s` (`07_TUNING §16`), fondu **sortant seulement** : le joueur est déjà jouable pendant le fondu entrant. |
| **Pas de rechargement d'assets** | Aucune soft reference chargée au respawn : tout est résident (les niveaux tiennent en mémoire). |
| **Touche dédiée** | `R` en **Hold 0.4 s** (`IA_Restart`, `11_ARBITRAGES D16`) = restart complet du niveau, depuis n'importe où, sans menu (`PC_Overdrive`). Cible technique : **< 0.5 s** entre la validation du hold et un joueur jouable. |

> **[À TRANCHER — hors périmètre LD]** Le restart volontaire (`R`) ne passe pas par `BPC_Health.OnDeath` :
> il **ne consomme donc aucune vie** en l'état. À confirmer par Louis — sinon `R` devient le moyen gratuit
> d'annuler une section ratée, ce que le système de vies (`11_ARBITRAGES D1`) cherche précisément à rendre coûteux.
> La décision appartient à `11_ARBITRAGES` / `SPEC_UI_HUD`, pas à cette spec.

---

## 10. Workflow de construction dans UE5.8

### 10.1 Réglages d'éditeur (à faire une fois)
| Réglage | Valeur | Où |
|---|---|---|
| Grid Snap (translation) | **50 uu** (activé) | barre d'outils viewport, menu déroulant de la grille |
| Rotation Snap | **15°** (activé) | idem |
| Scale Snap | **0.25** (activé) | idem |
| Grid unités affichées | 100 / 500 / 1000 | Editor Preferences → Viewports → Grid Snapping |
| Camera Speed | 6–8 | viewport |
| Far Clip Plane | ≥ 100000 uu | Project Settings → Rendering (les Speed Spaces sont longs) |
| World Partition | **désactivé** sur les maps de gameplay | World Settings |
| Static Lighting | **désactivé** — l'éclairage est **100 % dynamique** (Lumen), aucun lightmap, aucun build de lumière (`11_ARBITRAGES D2`) | Project Settings → Rendering |
| Dynamic GI / Reflection Method | **Lumen / Lumen** · Virtual Shadow Maps **ON** — *on ne touche à rien, le template est déjà correct* (`11_ARBITRAGES D2`) | Project Settings → Rendering |
| Substrate / Nanite | **off** (recommandé, non bloquant) — aucun gain sur des meshes à 500 tris | Project Settings → Rendering |
| Auto-save | 5 min | Editor Preferences |

### 10.2 Étapes
```
1. PAPIER (10 min)          Plan de masse : la suite de sections, leurs longueurs en uu.
                            START → INTRO → SPEED → COMBAT → MOVEMENT → SPEED → COMBAT → FINAL RUN.
                            Somme des longueurs / 3000 uu/s ≈ durée cible (90–180 s).

2. BLOCKOUT GRIS (2–4 h)    Modeling Mode → Create → Box (pas de BSP, pas de Geometry Script).
                            Un seul matériau `MI_Env_Blockout`. Tout snappé à 50 uu.
                            Objectif : le niveau est TRAVERSABLE de bout en bout. Rien d'autre.

3. PREMIER RUN              PIE, sprint continu, chrono. Note où tu ralentis SANS le vouloir.
                            → chaque ralentissement involontaire = un défaut de LD, pas du joueur.

4. ITÉRATION GÉOMÉTRIE      Élargir, allonger, supprimer. On coupe toujours plutôt qu'on ajoute.
   (boucle 3↔4, 3–5 fois)   Règle : si tu hésites entre 2 tailles, prends la plus GRANDE.

5. COLLISIONS & CANAUX      Passer les murs de wall ride en `OD_WallRideSurface`.
                            Tester le corridor : accroche + wall jump + `SameWallCooldown`.

6. ENNEMIS                  Poser les `BP_Enemy_*` avec leur `SectionTag`. Re-run. Ajuster les distances (§8).

7. CHECKPOINTS + END        `BP_Checkpoint` (0–2) + `BP_LevelEndTrigger`. Tester le respawn.

8. SAFE / SPEED WAY         Ajouter 3–5 raccourcis (§6). Chronométrer les deux lignes. Ajuster à 1.5–4 s de gain.

9. MODULES FINAUX           SEULEMENT quand les temps sont bons et que le run est fun.
                            Remplacer les boxes par les `SM_Module_*` un par un (Replace References / copier le transform).
                            Le blockout et le module final ont EXACTEMENT les mêmes dimensions → aucun retiming.

10. MATÉRIAUX & AMBIANCE    Scène ÉCLAIRÉE (11_ARBITRAGES D2) : appliquer les `MI_` de §5.2.1, poser les
                            `SM_Module_TraversalStrip_400` (tous les 800–1600 uu), puis 1 `BP_LightingRig`
                            qui porte **DirectionalLight (ombres ON, angle imposé par le monde) + SkyLight +
                            SkyAtmosphere + Exponential Height Fog**, réglé depuis le `PDA_WorldData`
                            du monde (`11_ARBITRAGES D33`, `PALETTE.md §4`).
                            Vérifier §5.2.2 (arêtes contre le ciel) AVANT de poser la moindre lumière
                            d'appoint. Budget de lumières et d'ombres : §12. Cf. `SPEC_ART_DIRECTION §9`.

11. TUNING DU RANK          Louis fait un run « propre mais pas parfait » → seuil A (`07_TUNING §14`).
                            Renseigner `S_RankThresholds` dans `DA_Level_*`.

12. CHECKLIST §11
```

### 10.3 Tester vite
- `L_Sandbox_Movement` (`SPEC_MOVEMENT §13.2`) est la référence de calibration : **tout gap, tout écartement de mur
  de wall ride, toute hauteur de slide-gate doit d'abord exister en sandbox** avant d'entrer dans un niveau.
- `BP_SpeedGate` (`Dev/Debug`) posé à l'entrée et à la sortie de chaque section → `Print` de la vitesse.
  Objectif : **la vitesse de sortie d'une section ≥ vitesse d'entrée**, sauf en Combat Arena.
- `bDebugEnabled` sur `BPC_MovementState` pendant toute la construction (overlay `SPEC_MOVEMENT §13.1`).
- Raccourci « Play From Here » (clic droit dans le viewport) pour tester une section isolée.
- Un chrono par section noté dans `Docs/Journal/` : si une section dérive de plus de 20 % de sa cible, c'est la géométrie qui change, pas le tuning.

---

## 11. Checklist de validation d'un niveau

**Structure**
- [ ] La suite de sections respecte START → INTRO → SPEED → COMBAT → MOVEMENT → SPEED → COMBAT → FINAL RUN
- [ ] Durée première completion mesurée : **90–180 s** (`07_TUNING §17`)
- [ ] Run expert mesurée : **55–65 %** du temps débutant
- [ ] Aucun couloir de plus de 3 s à 3000 uu/s sans grand espace
- [ ] Nombre d'ennemis dans la cible du niveau (§7), aucune poche > 6 (8 en L6)

**Métriques**
- [ ] Tout est snappé à 50 uu, toutes les rotations sont multiples de 15°
- [ ] Aucun gap obligatoire > 1600 uu · aucun écart vertical obligatoire > 150 uu
- [ ] Écartement de tous les murs de wall ride entre 600 et 1400 uu
- [ ] Chaque corridor de wall ride est précédé d'un déclencheur d'envol (le joueur est en `Falling`)
- [ ] Toute ouverture de slide a 150 uu de haut, jamais moins de 110 ni plus de 170
- [ ] Aucun couloir < 800 uu de large · aucun plafond < 250 uu hors slide-gate

**Flow**
- [ ] Un run complet est possible **sans jamais retomber sous `Speed_SprintCap` (1500)** hors Combat Arena
- [ ] La vitesse de sortie de chaque Speed Space > vitesse d'entrée (`BP_SpeedGate`)
- [ ] Aucun ralentissement involontaire pendant 3 runs consécutifs
- [ ] Aucune arête qui accroche (tester en longeant chaque mur à 4000 uu/s)
- [ ] Le niveau est finissable **sans aucun Speed Way** et **sans aucun dash**

**Lisibilité**
- [ ] Rien d'important n'apparaît à moins de 3000 uu (L1–L3) / 4000 uu (L4–L6)
- [ ] Le niveau reste lisible en niveaux de gris
- [ ] Chaque `MI_` respecte son rôle sémantique (§5.2.1), zéro exception
- [ ] **Aucune arête de bâtiment ne se confond avec le ciel** — test horizon de §5.2.2
- [ ] **Aucune information de gameplay n'est claire sur fond clair** : rouge de traversée, violet de
      signalétique et hachures de danger sont tous **plus foncés ou plus saturés** que le mur qui les porte
- [ ] Le décor n'emploie **ni `OD_Magenta_Player` ni `OD_Amber_Enemy`** (couleurs du joueur et des ennemis)
- [ ] Aucun motif de moins de 400 uu sur les surfaces longées à haute vitesse
- [ ] `BP_LevelEndTrigger` visible depuis ≥ 4000 uu et incontournable

**Rendu & perf** (`11_ARBITRAGES D2`, §12)
- [ ] 1 seule `DirectionalLight` avec ombres, 1 `SkyLight`, 1 `SkyAtmosphere`, portés par `BP_LightingRig`
- [ ] Toutes les lumières d'appoint ont `Cast Shadows` = OFF, ≤ 8 par niveau, ≤ 3 visibles à la fois
- [ ] `Dynamic Shadow Distance` ≈ 10 000 uu, `Cast Far Shadow` coupé
- [ ] **Tous les modules du kit sont en `Static`** — aucun `Movable` parasite dans l'Outliner
- [ ] Frame time mesuré dans le Speed Space le plus ouvert **et** dans l'arène la plus dense (`stat gpu`)

**Systèmes**
- [ ] `BP_LevelManager` présent, `DA_Level_*` assigné, `TotalEnemies` correct
- [ ] Tous les ennemis ont un `SectionTag`
- [ ] Checkpoints (0–2) testés : respawn < 0.5 s, vélocité remise à zéro proprement, ennemis de la section reset
- [ ] Mourir au checkpoint : **une vie est consommée**, le compteur HUD décrémente, les upgrades sont conservés
      (`11_ARBITRAGES D1`, `05_ARCHITECTURE §4`) — le checkpoint ne rend **aucune** vie
- [ ] `S_RankThresholds` renseignés (S/A/B/C + `ParTimeSeconds`)
- [ ] Kill volume sous tout le niveau (Z = plus bas point − 2000 uu)
- [ ] `R` maintenu = restart instantané depuis n'importe quel point

---

## 12. Pièges connus

| Piège | Symptôme | Correctif |
|---|---|---|
| **Tunneling à haute vitesse** | Le joueur traverse un mur à 5000+ uu/s | À 6000 uu/s = **100 uu par frame @60fps**. Épaisseur minimale de toute géométrie bloquante : **100 uu**. `bUseCCD = true` sur la capsule. `Speed_HardCap` respecté. Pour un mur mince voulu visuellement : mesh fin + collision box de 100 uu. |
| **Arêtes qui accrochent** | Blocage net sur un joint entre 2 modules | Sols strictement coplanaires (même Z, snap 50). `bUseFlatBaseForFloorChecks = true`. Aucun mesh concave. Décalage de sol toléré : **≤ 50 uu** (`MaxStepHeight`). `Perch Radius Threshold > 0`. |
| **Mur de wall ride qui n'accroche pas** | Le joueur longe le mur, rien ne se passe | 3 causes, dans l'ordre : (1) il est au sol → la détection ne tourne qu'en `Falling` ; (2) le preset n'est pas `OD_WallRideSurface` ; (3) l'écart est > 1400 uu ou la vitesse < 1200. |
| **`OD_WallRideSurface` n'est plus `WorldStatic`** | `CanUncrouch()` traverse le mur, le joueur se relève dans la géométrie | `SPEC_MOVEMENT §12` : inclure **toujours** `WallRideSurface` dans les object types des traces de sol et de dé-crouch. |
| **Niveau trop vertical** | Le joueur passe son temps à remonter, la vitesse ne dépasse jamais 2000 | Apex de saut = 172 uu. **≥ 70 % du dénivelé descendant** (P6). Une Vertical Section max par niveau, ≤ 1600 uu de haut, toujours suivie d'une descente. |
| **Couloir trop étroit** | Impression de tunnel, collisions rasantes permanentes, nausée | Minimum absolu 800 uu (`07_TUNING §17`), **cible 1200–2400**. À 4000 uu/s, un couloir de 800 se lit comme un boyau. Si tu es tenté d'augmenter le FOV, c'est que le couloir est trop étroit. |
| **Angle mort avant un obstacle** | Perte de 50 % de vitesse « injuste » (collision > 60°, `07_TUNING §10`) | Tableau §5.1. Baisser les murs intérieurs des virages (`Wall_800` au lieu de `Wall_1600`). |
| **Speed Way qui tue** | Le joueur rate et meurt → il ne le retente jamais | Un échec de Speed Way retombe **toujours** sur le Safe Way. Jamais de kill volume sous un raccourci. |
| 🔴 **Coût de l'éclairage dynamique — LE risque perf n°1 de la v2** | Frame time qui s'effondre dans un Speed Space ouvert ou une arène ; micro-freezes quand la caméra tourne | Le rendu est **ÉCLAIRÉ, Lumen + Virtual Shadow Maps actifs** (`11_ARBITRAGES D2`). Voir la ligne suivante pour le détail du budget. C'est ce poste, et plus l'overdraw d'émissifs, qui décide de la tenue du frame time. |
| **Trop de lumières / d'ombres dynamiques** | GPU time qui monte avec le nombre de lumières visibles, pas avec le nombre de meshes | **Budget par niveau** : **1 seule `DirectionalLight` projetant des ombres** (celle du `BP_LightingRig`, `11_ARBITRAGES D33`) · 1 `SkyLight` · **8 Point/Spot dynamiques max**, **`Cast Shadows` = OFF sur toutes**, rayon < 800 uu, jamais plus de **3 visibles simultanément** dans un cadre · aucune lumière d'appoint pour « corriger » une lecture de forme (c'est §5.2.2 qui la corrige). Une lumière avec ombres est **un ordre de grandeur** plus chère qu'une lumière sans. |
| **Ombres projetées trop loin** | Les VSM pagent sur tout le Speed Space alors que le joueur ne verra jamais ces ombres | Limiter la distance de projection à la **distance de réaction utile**, pas au Far Clip Plane (100 000 uu, §10.1). Formule : `DistanceOmbre = D_visible_max (§5.1) × 1.5 = 7000 × 1.5 ≈ 10 000 uu`. Au-delà, la silhouette lointaine est portée par le fog et la valeur des faces (§5.2.2), pas par une ombre. Régler `Dynamic Shadow Distance` sur la `DirectionalLight` et couper `Cast Far Shadow`. |
| **Modules en `Movable` au lieu de `Static`** | Chute de perf inexpliquée dans un niveau pourtant simple | **Tout module du kit §3 est posé en `Static`.** Un `Static Mesh` en `Movable` invalide le **cache d'ombre des VSM à chaque frame** et sort de la représentation Lumen accélérée : c'est l'erreur la plus chère et la plus discrète du projet. `Movable` est réservé aux ennemis, au joueur et aux `BP_BossArenaElement` qui bougent réellement. **À vérifier avant chaque commit de niveau** (filtrer par Mobility dans l'Outliner). |
| **Surcharge d'émissifs / d'overdraw** | Image qui « blanchit » et devient illisible dans les arènes | Sur fond clair, monter l'émissif **délave** au lieu de faire ressortir (§5.2). Contraintes : **max 3 couleurs de gameplay visibles simultanément** dans un cadre · `EmissiveIntensity` par usage donné par `PALETTE.md §8.3`, jamais improvisé · translucides jamais empilés à plus de 3 couches. Cf. `SPEC_ART_DIRECTION §9.3 / §9.4`. |
| **Trop de meshes visibles d'un coup** | Draw calls qui explosent dans un Speed Space de 16000 uu | **HISM obligatoire pour tout module répété plus de 20 fois** dans un niveau. Budget scène visible < 1,5 M tris (`SPEC_ART_DIRECTION §6.1`) — jamais atteint avec le kit §3, mais le nombre d'**instances** distinctes, lui, se surveille. Un Speed Space se remplit avec du `Floor_1600` scalé, pas avec 40 `Floor_400`. |
| **Streaming / hitch au respawn** | Micro-freeze de 0.3–1 s au checkpoint | Pas de World Partition, pas de Level Streaming, pas de soft reference chargée en jeu. Tout le niveau est résident (§9.4). |
| **Trop de meshes uniques** | Temps de build et de chargement qui explose | 23 modules max (§3). Un besoin nouveau se résout par du scale entier ou de la rotation, pas par un mesh de plus. |
| **Ennemi qui spawn hors champ** | Dégât « venu de nulle part », perte de 45 % de vitesse | Zéro spawn dynamique. Tous les ennemis sont posés et activés par `SectionTag` (§8.5). |
| **Sol infini sans repère** | Le joueur ne sent plus la vitesse malgré le HUD à 4000 | Repère visuel tous les 1600 uu (§5.3). La sensation de vitesse est un problème de level design avant d'être un problème de post-process. |
| **Plafond bas oublié au-dessus d'un slide** | Le joueur reste bloqué en `bForcedSlide` (`SPEC_MOVEMENT §4.2`) | Après tout `Gate_Slide` ou `Tunnel_1600` : **800 uu de dégagement vertical** dans les 400 uu qui suivent la sortie. |
