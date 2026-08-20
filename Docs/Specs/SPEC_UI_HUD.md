# SPEC — UI & HUD

> HUD de course, résultats, coffre, menus, settings. **Blueprint only, UMG standard, PAS de Common UI** (`05_ARCHITECTURE §6`).
> Aucune valeur de gameplay ici : tout renvoie à `07_TUNING.md` par nom de clé. Couleurs : `Docs/ArtDirection/PALETTE.md`. Données : `08_DATA_SCHEMAS.md`.
> Les valeurs purement UI (px, s) sont proposées ici, marquées **`[À CALIBRER]`**.

---

## 1. Principes

À 5000 uu/s un mur arrive en 0.2 s. **Chaque pixel d'UI est un pixel de mur qu'on ne voit pas.**

| Règle | Conséquence technique |
|---|---|
| **Rien au centre** | Zone centrale 40 % × 40 % interdite, sauf crosshair et hitmarker (transitoire). |
| **L'UI est SOMBRE, le monde est CLAIR** | Règle **inversée** par rapport à la v1. Voir §1.1 — c'est la contrainte structurante de tout ce document. |
| **Le regard ne quitte pas le crosshair** | Toute info critique lisible en **vision périphérique** : forme + couleur, jamais texte seul. |
| **Reconnaissance, pas lecture** | Un chiffre ne se lit pas à 5000 uu/s. HP/Heat/Dash/Vies se lisent par silhouette et couleur. |
| **Seul l'urgent bouge** | Au repos tout est immobile, opacité ~0.85 (voir §1.1 : sur fond clair, l'opacité basse de la v1 rendait le HUD illisible). Mouvement/pulse = état critique uniquement. |

**Hiérarchie** — P0 survie : crosshair, HP, Heat, **Vies** (jamais masqués, priorité de réaction) · P1 ressource :
Dash, Speed, Style (permanents mais discrets) · P2 contexte : Timer, Kills, objectif (petits, coins hauts,
immobiles) · P3 transitoire : Hitmarker, DamageIndicator, popups de style (durée de vie < 1.2 s).

### 1.1 Contraste — le HUD est devant une ville blanche en plein jour

La DA v2 (D2, D3, `PALETTE.md`) place le HUD devant **deux fonds également lumineux** : un **ciel bleu clair**
(`OD_Sky_Blue` / `OD_Sky_Pale`) et des **murs blancs** (`OD_White_Structure`), avec en plus des **ombres
portées franches** (Lumen + VSM actifs) qui font varier la luminosité du fond d'une frame à l'autre en course.

> **Toute la règle en une phrase** : un élément d'UI clair, blanc ou semi-transparent **disparaît**.

`PALETTE.md §7` fait autorité et se décline ici sans exception :

| Élément | Traitement |
|---|---|
| **Panneau plein écran** (Results, RunFailed, Loot, menus, pause, settings) | Fond `OD_Navy_Deep` à **92 %** d'opacité · texte principal `OD_White_Pure` · texte secondaire `OD_Grey_Shadow` · bordures `OD_Magenta_Player` 1–2 px |
| **Élément de HUD sans panneau** (HP, Heat, Dash, Speed, Style, **Vies**, Timer, Kills) | Tracé en **`OD_Navy_Ink`**, avec un **halo blanc de 2 px** (`OD_White_Pure`, opacité 0.9). Pas de panneau, pas de liseré, pas de drop shadow noir |
| **Crosshair** | **Inversé à l'implémentation (J8)** : traits **blancs** bordés de `OD_Navy_Ink`, point central rouge `#FF1025` — le liseré sombre joue le rôle du halo, dans l'autre sens. Voir **§3.1** pour la justification et la tension de palette ouverte. **Jamais magenta** — il se confondrait avec le laser (`PALETTE.md §7`) |
| **Accents colorés** (états critiques, paliers) | Toujours des tokens **saturés ou foncés** de `PALETTE.md §2`. Jamais un pastel, jamais un blanc |

**Pourquoi un halo blanc et pas un drop shadow noir** : le drop shadow de la v1 supposait un fond sombre et
ne servait qu'aux rares murs clairs. Ici c'est l'inverse — le trait est foncé et c'est le **halo clair** qui
le décolle. Devant une **ombre portée** (le seul fond foncé du jeu), c'est le halo qui prend le relais et
maintient la lecture. Un contour, pas une ombre : il fonctionne dans les deux sens.

**Implémentation** : le halo est un `MI_UI_Halo` (outline procédural sur l'alpha du brush), paramètre
`HaloWidth` = 2 px `[À CALIBRER]`, appliqué via le `Brush` du widget — **jamais** en dupliquant le widget
en blanc derrière lui décalé de 2 px (4 draw calls au lieu d'1, et ça casse à l'animation).

**Test obligatoire de chaque élément** (repris en §12) : lisible devant le **ciel**, devant un **mur blanc
en plein soleil**, et devant une **ombre portée**. Trois fonds, pas deux.

**Interdit au HUD (MVP)** : minimap · munitions (le laser n'en a pas) · liste d'upgrades · barres de vie
ennemies (sauf `WBP_BossHealthBar`) · marqueurs 3D permanents · tutoriel persistant · killfeed · barre d'XP ·
portrait · notifications · tout ce qui couvre la moitié inférieure centrale.
**Anti-objectif** : si une info manque en playtest, passer par **l'audio ou le VFX écran**
(`SPEC_CAMERA_JUICE §7/§9`) avant d'ajouter un widget.

---

## 2. Layout du HUD (`WBP_HUD`)

Canvas racine plein écran, **anchors + offsets uniquement**. Référence 1920×1080, 16:9.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [A] OBJECTIVE / 00:47.32       (haut-centre)                [B] KILLS 12/24  │
│                          ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐                             │
│                          │  ZONE INTERDITE     │                             │
│                          │  40% x 40%     ✛[C] │  ← crosshair + hitmarker    │
│                          └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘                             │
│                             [D] ◤ damage indicators (radiaux)                │
│ [J] ❯❯❯  LIVES                                                               │
│ [E] ▮▮▮▮▮▮▮▮▯▯  HP                                        [F]    2 4 7      │
│ [G] ▬▬▬▬▬▯▯▯  HEAT (8 blocs)                                  SPEED          │
│ [H] ◆ ◆                                                   [I]  x2.4 STYLE    │
└──────────────────────────────────────────────────────────────────────────────┘
```

| Id | Widget | Anchor | Offset px | Taille | Justification |
|---|---|---|---|---|---|
| A | `WBP_Timer` + objectif | `0.5,0` | `Y +24` | 320×64 | Haut-centre : zone la moins traversée par la géométrie en course, consultable sans quitter l'axe vertical du crosshair. |
| B | `WBP_KillCounter` | `1,0` | `X -40, Y +28` | 200×44 | P2 pur, coin le plus « mort » de l'écran en FPS rapide. |
| C | `WBP_Crosshair` + `WBP_Hitmarker` | `0.5,0.5` | `0,0` | 32×32 | Point de fixation oculaire, référence de tout le reste. |
| D | `WBP_DamageIndicator` | plein écran | `0` | full | Radial : la direction se lit sans mouvement oculaire. |
| **J** | **`WBP_LivesCounter`** | `0,1` | `X +48, Y -140` | **120×24** | **Juste au-dessus de HP, même colonne, même largeur d'ancrage.** Les vies sont la ressource **la plus lente** du jeu (3 pour toute la run) : elles coiffent la pile « ce que je subis » et n'entrent jamais dans le champ du crosshair. Petit par défaut — c'est une info qu'on consulte une fois par mort, pas en continu. |
| E | `WBP_HealthBar` | `0,1` | `X +48, Y -110` | 320×22 | Bas-gauche = main gauche (WASD/Shift/Ctrl) = « ce que je subis ». |
| G | `WBP_HeatBar` | `0,1` | `X +48, Y -76` | 320×14 | Sous HP, même largeur : les deux se lisent comme un bloc unique. Plus fine car moins létale. |
| H | `WBP_DashCharges` | `0,1` | `X +48, Y -44` | 120×28 | Même colonne : le dash est une ressource, donc même famille visuelle. |
| F | `WBP_SpeedMeter` | `1,1` | `X -48, Y -104` | 260×86 | Bas-droite = main droite (tir/dash). Stat héroïque → plus grosse typo. Éloignée de HP pour éviter la confusion périphérique. |
| I | `WBP_StyleMeter` | `1,1` | `X -48, Y -48` | 260×40 | Collé sous SPEED : les deux montent ensemble, lus comme un « score en direct ». |

**Pourquoi les vies ne surchargent pas le HUD** : la colonne bas-gauche passe de 3 à 4 éléments, mais
`WBP_LivesCounter` est le **plus petit** de tous (120×24, 3 chevrons de 16 px) et le seul **totalement
immobile** hors événement. Il n'ajoute ni chiffre à lire, ni barre à interpréter : 3 formes, présentes ou
absentes. Aucun autre widget n'est déplacé, aucun n'est agrandi. L'alternative haut-droite (à côté de
`WBP_KillCounter`) a été **écartée** : les vies sont une information de survie, elles appartiennent à la
pile de survie, pas à la pile de contexte.

Marges écran 40–48 px `[À CALIBRER]`, jamais < 3 % de la largeur (§11).
**Z-Order** : `0` barres → `10` crosshair → `20` hitmarker → `30` damage → `50` popups style → `100` overlays.

---

## 3. Les widgets du HUD

### 3.0a Règle transverse — **apparence : `PALETTE.md` puis la DA font autorité**

Ordre d'autorité sur l'**apparence** : `Docs/ArtDirection/PALETTE.md` (couleurs, sans exception, D3) →
`SPEC_ART_DIRECTION §10.5` (formes, densité) → cette spec (structure, sources de données, comportement).
Trois conséquences directes, appliquées dans tout ce §3 :

| Règle | Conséquence ici |
|---|---|
| **Aucune bordure, aucun fond sur les éléments du HUD de jeu** | Ni `WBP_LivesCounter`, ni `WBP_HealthBar`, ni `WBP_HeatBar`, ni `WBP_DashCharges`, ni `WBP_SpeedMeter`, ni `WBP_StyleMeter` n'a de panneau ni de liseré. Uniquement du texte et des barres pleines. Les panneaux `OD_Navy_Deep` bordés `OD_Magenta_Player` sont réservés aux **écrans plein écran** : `WBP_Results` (§6), **`WBP_RunFailed` (§6.1)**, `WBP_LootChest` (§7), menus et settings (§8, §9). `WBP_Panel` n'est donc **jamais** utilisé dans `WBP_HUD`. |
| **Tracé foncé + halo blanc, jamais de drop shadow** | Le **drop shadow noir 2 px** de la v1 est **supprimé** : il supposait un monde sombre. Tout élément de HUD sans panneau est tracé en **`OD_Navy_Ink`** avec un **halo blanc 2 px** (`MI_UI_Halo`, §1.1). C'est ce qui le rend lisible devant le ciel, devant un mur blanc **et** devant une ombre portée. |
| **Barre de heat segmentée en 8 blocs** | `WBP_HeatBar` n'est pas une barre continue (§3.3). |

**Table de conversion des anciennes couleurs** — les libellés `WHITE` / `CYAN` / `MAGENTA` / `AMBER` / `RED`
de la v1 de cette spec sont **abolis**. Ce qui suit s'applique partout dans ce document :

| Ancien libellé v1 | Token v2 (`PALETTE.md §2`) | Note |
|---|---|---|
| `WHITE` (élément de HUD au repos) | **`OD_Navy_Ink` + halo blanc** | Un trait blanc sur une ville blanche n'existe pas |
| `WHITE` (texte sur panneau) | `OD_White_Pure` | Reste blanc : le panneau est foncé |
| `CYAN` (gain, valeur améliorée, palier) | **`OD_Purple_Primary`** | Le cyan est **mort** (D3). Le violet est la seule teinte froide de la palette, et il n'est pas réservé au joueur |
| `MAGENTA` | `OD_Magenta_Player` | Bordures de panneau, titres, accents joueur |
| `AMBER` | `OD_Amber_Heat` | Chaleur, warning, cible S RANK |
| `RED` (danger, dégât, delta négatif) | `OD_Red_Danger` | |
| `DANGER_RED` | `OD_Red_Danger` | Même token |

### 3.0 Règle transverse — **Dispatchers, jamais Property Binding, jamais Tick**

**Interdit** : le `Property Binding` UMG (bouton « Bind » d'un champ) et `Event Tick` sur widget.
**Pourquoi** : un binding est **évalué à chaque frame de rendu, pour chaque champ**, avec un cast implicite
derrière — 10 bindings = 10 casts/frame pour des valeurs qui changent 3 fois par seconde. Surtout, il
s'évalue **même quand la valeur n'a pas bougé**, ce qui interdit toute animation « au changement ».

```
WBP_HUD :: Event Construct
   ├─ Get Owning Player Pawn → Cast To BP_PlayerCharacter → CachedPlayer     (UNE fois)
   ├─ Bind CachedPlayer.OnHealthChanged / OnHeatChanged / OnDashChargesChanged
   │                    / OnSpeedChanged / OnStyleChanged      → Handle_*
   ├─ Get Game State → Cast To GS_Overdrive → CachedGS
   ├─ Bind CachedGS.OnKillCountChanged / OnLevelTimerTick      → Handle_*   (1 event / 0.1 s)
   ├─ Get Game Instance → Cast To GI_Overdrive → CachedGI                   (UNE fois)
   └─ Bind CachedGI.OnLifeLost                                 → Handle_LifeLost
```
**`GI_Overdrive` est la 3ᵉ et dernière source de données du HUD** : les vies sont la seule donnée qui
**survit au changement de niveau** (D1), donc ni le pawn ni le GameState ne peuvent la porter.
`WBP_HUD::Construct` lit aussi `CachedGI.LivesRemaining` **une fois** pour initialiser l'affichage —
sans ça, le compteur repart à `Run_MaxLives` à chaque niveau.
Chaque `Handle_*` **pousse** la valeur dans le sous-widget via une fonction publique
(`SetHealth(Current,Max)`, `SetHeat(Ratio,bOverheated)`…) et déclenche l'animation si besoin.

| Cas | Solution autorisée |
|---|---|
| Valeur événementielle (HP, kills, dash, overheat, **vies**) | Dispatcher direct. |
| Valeur continue (vitesse, style, heat) | Le composant émet au changement significatif ou sur le **timer unique 20 Hz** de `BPC_MovementState` (D9, `SPEC_VFX §3.1`). Jamais de Tick widget, jamais un second timer. |
| Lissage visuel | **Animation UMG** ou `Timeline` dans le sous-widget, déclenchée par le setter. |
| Pulse / glow | **Material** (`Time`, `MPC_Global`), zéro logique BP. |

**Le `WBP_HUD` est le SEUL widget qui connaît le joueur, le GameState et le GameInstance.** Les sous-widgets
ne castent jamais et ne cherchent jamais le pawn : ils reçoivent des données par fonction publique, donc
restent testables seuls dans le designer. Nommage des dispatchers : `On` + fait passé (`06_CONVENTIONS §3`).

### 3.1 `WBP_Crosshair` — **implémenté au J8** (`Content/OVERDRIVE/UI/HUD/WBP_Crosshair`)

Source (à câbler au J19) `BPC_Heat.OnHeatStateChanged` + `BP_LaserWeapon.OnShotFired(Hit, bHit)`
(`SPEC_COMBAT §3` fait foi sur les noms de dispatchers du laser).
**4 traits fins + 1 point central, pas de cercle** (un cercle masque la cible), pas de contour de visée.

#### 3.1.1 Pourquoi le contraste vient de la FORME et pas d'une adaptation dynamique

Louis a demandé un réticule *« qui ne se fonde pas dans le décor, donc adapte les couleurs en fonction
de sur quoi c'est projeté »*. **Cette adaptation est impossible en UMG** : un widget est composité
**après** la scène et n'a aucun accès au framebuffer qu'il recouvre. La faire vraiment demanderait un
post-process en mode *Difference* / inversion — hors scope du jour, et il casserait le cel-shading (D2).

**Le résultat demandé est obtenu autrement, et c'est ce que font tous les FPS shippés : le réticule
porte son propre contraste.** Chaque élément est dessiné **deux fois** :

1. une **couche sombre** `OD_Navy_Ink`, plus large et plus longue de `OutlineWidth` **sur chaque bord** ;
2. la **couche claire** par-dessus, exactement centrée dessus.

Il en résulte un liseré sombre de 1 px tout autour de chaque trait et du point. Sur un mur blanc en
plein soleil c'est le liseré qui tient la lecture ; devant une ombre portée c'est la couche claire.
**Aucun fond ne peut faire disparaître les deux à la fois** — c'est exactement ce que `PALETTE.md §7`
prescrit pour un élément de HUD sans panneau, appliqué au réticule.

> **Écart assumé avec §1.1** : §1.1 interdit de « dupliquer le widget en blanc derrière lui décalé de
> 2 px (4 draw calls au lieu d'1) ». Ici le doublage est **concentrique**, pas décalé : il coûte
> **1 draw call de plus par élément** (10 au total, pas 4 par élément) et ne casse pas à l'animation,
> puisque les deux couches sont repositionnées par la même fonction. `MI_UI_Halo` reste la solution
> prévue pour les **textes** du HUD, où un doublage concentrique ne marcherait pas.

#### 3.1.2 Géométrie et valeurs

Toutes exposées en variables `Instance Editable`, catégorie `Feedback|Crosshair`.
**Aucune n'est en dur dans le graphe** (R3). Elles sont appliquées par `ApplyCrosshairLayout` sur
`Event PreConstruct` — donc le rendu du designer suit toute modification.

| Clé (variable) | Valeur | Unité | Rôle |
|---|---|---|---|
| `Crosshair_LineLength` | **6.0** `[À CALIBRER]` | px | Longueur d'un trait clair |
| `Crosshair_LineThickness` | **2.0** `[À CALIBRER]` | px | Épaisseur d'un trait clair |
| `Crosshair_Gap` | **8.0** `[À CALIBRER]` | px | Distance centre → extrémité **intérieure** du trait clair |
| `Crosshair_DotRadius` | **2.0** `[À CALIBRER]` | px | Demi-côté du point central (→ point de 4 px) |
| `Crosshair_OutlineWidth` | **1.0** `[À CALIBRER]` | px | Épaisseur du liseré sombre, **sur chaque bord** |

> `Crosshair_Gap` est passé de 5 à **8** : à 5, le liseré du point (rayon 2 + 1) et celui des traits
> (qui empiète de 1 px vers le centre) ne laissaient plus qu'**1 px de vide** — le réticule se serait lu
> comme une croix pleine. À 8, le vide fait 4 px et le point se détache. Le « point 2 px » de la v1
> passe à **4 px** (`DotRadius = 2`) : à 2 px et à 4000 uu/s, il n'existe pas.

Géométrie dérivée (variables `Computed_*`, catégorie `Feedback|Crosshair|Computed`, non éditables) :

```
LineOffset       = Gap + LineLength / 2                 = 11.0   <- centre du trait, en px du centre ecran
LineOffsetNeg    = -LineOffset                          = -11.0
OutlineLength    = LineLength    + 2 x OutlineWidth     =   8.0
OutlineThickness = LineThickness + 2 x OutlineWidth     =   4.0
DotSize          = 2 x DotRadius                        =   4.0
OutlineDotSize   = 2 x DotRadius + 2 x OutlineWidth     =   6.0
```

Encombrement total **30 × 30 px** (`LineOffset + OutlineLength/2` = 15 px de demi-diagonale),
compatible avec la case 32×32 de la ligne **C** du tableau §2.

#### 3.1.3 Arbre de widgets

`CanvasPanel CrosshairRoot` — tous les enfants ancrés `(0.5, 0.5)`, alignment `(0.5, 0.5)`,
`bAutoSize = false`. **La couche sombre est déclarée en premier** (`ZOrder 0`), la couche claire
ensuite (`ZOrder 1`) : l'ordre du Canvas *et* le `ZOrder` disent la même chose, volontairement.

| Widget | ZOrder | Position (x, y) | Taille (w × h) | Couleur |
|---|---|---|---|---|
| `Outline_Top` | 0 | `0, LineOffsetNeg` | `OutlineThickness × OutlineLength` | `Crosshair_OutlineColor` |
| `Outline_Bottom` | 0 | `0, LineOffset` | `OutlineThickness × OutlineLength` | `Crosshair_OutlineColor` |
| `Outline_Left` | 0 | `LineOffsetNeg, 0` | `OutlineLength × OutlineThickness` | `Crosshair_OutlineColor` |
| `Outline_Right` | 0 | `LineOffset, 0` | `OutlineLength × OutlineThickness` | `Crosshair_OutlineColor` |
| `Outline_Dot` | 0 | `0, 0` | `OutlineDotSize × OutlineDotSize` | `Crosshair_OutlineColor` |
| `Line_Top` | 1 | `0, LineOffsetNeg` | `LineThickness × LineLength` | `Crosshair_LineColor` |
| `Line_Bottom` | 1 | `0, LineOffset` | `LineThickness × LineLength` | `Crosshair_LineColor` |
| `Line_Left` | 1 | `LineOffsetNeg, 0` | `LineLength × LineThickness` | `Crosshair_LineColor` |
| `Line_Right` | 1 | `LineOffset, 0` | `LineLength × LineThickness` | `Crosshair_LineColor` |
| `Dot_Center` | 1 | `0, 0` | `DotSize × DotSize` | `Crosshair_DotColor` |

Les 11 widgets (racine comprise) sont en **`Visibility = HitTestInvisible`** : le réticule ne doit
jamais intercepter un clic. Les `Image` n'ont **aucune texture** (`resourceObject = None`,
`drawAs = Image`) — Slate rend un quad plein, teinté par `ColorAndOpacity`. Zéro asset de texture.

#### 3.1.4 Couleurs — **HEX sRGB et valeur linéaire**

⚠️ `12_PIEGES §5.31` : aucun setter MCP ne convertit le sRGB. **La colonne « linéaire » est celle qui
est réellement écrite dans l'asset.** Ne jamais recopier le HEX dans un outil.

| Variable | Token | HEX sRGB | Linéaire (R / G / B / A) |
|---|---|---|---|
| `Crosshair_OutlineColor` | `OD_Navy_Ink` | `#1B1730` | `0.010960 / 0.008568 / 0.029557 / 1.0` |
| `Crosshair_LineColor` | `OD_White_Pure` | `#FBFCFE` | `0.964686 / 0.973445 / 0.991102 / 1.0` |
| `Crosshair_DotColor` | rouge de l'arme | `#FF1025` | `1.000000 / 0.005182 / 0.018500 / 1.0` |

> **Tension de palette ouverte, à trancher par Louis.** `PALETTE.md §7` dit que le crosshair est
> `OD_Navy_Ink` bordé de blanc, et `11_ARBITRAGES D3` réserve le rouge au **danger** et aux **surfaces
> de traversée**. Louis a demandé un **point central rouge néon** : c'est fait. Le rouge choisi est
> `#FF1025`, **celui de l'émissif de l'arme** (`SPEC_ART_DIRECTION §6.4.1`, divergence déjà ouverte et
> déjà voulue par Louis) — donc ni `OD_Red_Danger` ni `OD_Red_Traversal` ne sont détournés de leur
> rôle, et le réticule est de la couleur du canon qu'il prolonge.
> **Alternative si Louis veut garder le rouge strictement exclusif** : `Crosshair_DotColor` =
> `OD_White_Pure` ou `OD_Navy_Ink` — une seule variable à changer, aucun autre impact.

**Jamais magenta** : le magenta est la couleur du faisceau, un réticule magenta se noierait dans son
propre muzzle flash au moment exact où le joueur en a besoin.

#### 3.1.5 Graphe

| Fonction | Rôle |
|---|---|
| `ComputeCrosshairMetrics()` | Recalcule les 6 `Computed_*` depuis les 5 clés de tuning. N'en **relit** aucune (piège `12_PIEGES 2.3b`). |
| `ApplyCrosshairElement(Target, PosX, PosY, SizeX, SizeY, Tint)` | `SlotAsCanvasSlot` → `SetPosition` → `SetSize` → `SetColorAndOpacity`. Le seul endroit qui touche un slot. |
| `ApplyCrosshairLayout()` | `ComputeCrosshairMetrics` puis 10 × `ApplyCrosshairElement`. |

`Event PreConstruct → ApplyCrosshairLayout`. **Aucun `Event Tick`, aucun Property Binding** (§3.0).

#### 3.1.6 Affichage

Créé et affiché par **`PC_Overdrive::BeginPlay`** (`Create Widget` → `Set CrosshairWidget` →
`Add to Viewport`, `ZOrder = Crosshair_ZOrder` = **10**, cf. §2). Le propriétaire est le
**PlayerController** et non le pawn : il survit au respawn, même raisonnement que `BPC_HitStop`
(`SPEC_COMBAT §5.4`). **Au J19, `WBP_HUD` reprend cette responsabilité et l'`AddToViewport` du PC
disparaît** — le handle est déjà là (`PC_Overdrive.CrosshairWidget`, type `UserWidget`).

#### 3.1.7 États (J19, non implémentés)

Idle : couche claire à 1.0 · Tir : `Crosshair_Gap` +3 px pendant 0.06 s (`Anim_Fire`) ·
Heat > `Heat_WarningThreshold` : lerp de `Crosshair_LineColor` vers `OD_Amber_Heat`
(**le liseré sombre ne change jamais** — c'est lui qui garantit la lecture) ·
Heat == `Heat_Max` : traits `OD_Red_Danger`, écart +4 px, **immobiles** (le clignotement est illisible
en course) · retour sous le seuil : retour animé 0.2 s. Tous ces états ne touchent que les variables de
tuning et rappellent `ApplyCrosshairLayout` — aucune valeur n'est écrite dans un slot ailleurs.

> **`D58`** : ces états signalent un **coût de style**, jamais une indisponibilité. Le crosshair
> **n'est jamais barré** et le tir part toujours (`SPEC_COMBAT §4`).

**Interdit** : crosshair dynamique lié à la vitesse (perte du point de fixation) · crosshair
magenta · crosshair entièrement blanc · cercle · contour de visée · `Event Tick` ·
**crosshair barré ou tout signe de tir refusé** (`D58`).

### 3.2 `WBP_HealthBar`
Source `BPC_Health.OnHealthChanged(New,Max,Delta)`. Barre **segmentée en 10 tranches** — on compte des blocs
en périphérie, on ne lit ni un remplissage continu ni un chiffre. **Ni panneau, ni bordure** (§3.0a) :
les blocs seuls, tracés en `OD_Navy_Ink` avec halo blanc 2 px.
**États** — > 60 % : `OD_Navy_Ink` 0.85 · 30–60 % : `OD_Amber_Heat` 0.9 · < 30 % : `OD_Red_Danger` + pulse
1.0 s `[À CALIBRER]` + vignette `OD_Red_Danger` écran (`SPEC_CAMERA_JUICE §9`) · **perte : chase bar**,
fantôme `OD_Grey_Deep` 40 % qui rattrape en 0.35 s `[À CALIBRER]` (rend le dégât lisible même si le joueur
regardait ailleurs) · gain : flash `OD_Purple_Primary` 0.15 s · mort : masqué.
PV chiffrés 14 px opacité 0.8 (relevée depuis 0.5 : sur fond clair, 0.5 disparaît) : utiles en debug,
ignorables en course.

### 3.3 `WBP_HeatBar`

> **Réécrit le 2026-08-20 — `11_ARBITRAGES D58`.** Ce que la jauge **signifie** a changé.
> Sa forme (8 blocs, sans panneau) et sa couleur (`OD_Amber_Heat`) ne changent pas.

**Ce que la barre dit au joueur** : **une discipline de tir**, pas une réserve de munitions.
Elle ne répond **plus** à *« combien de tirs me reste-t-il avant d'être bloqué ? »* — plus rien n'est
bloqué (`SPEC_COMBAT §4`). Elle répond à *« est-ce que j'arrose ? »*, et son coût est du **style**.
Elle monte sur les **tirs ratés**, descend sur les **headshots** et **au-dessus de
`Heat_CoolSpeedThreshold`**, et ne redescend **jamais toute seule**.

Source `BPC_Heat.OnHeatChanged(Ratio, State)` + `OnWarningEntered` + `OnOverheatStarted/Ended`
(ces deux derniers marquent le **maximum de pénalité de style**, et **non plus** un verrou de tir). Le composant est **sur l'arme**, il
remonte au Character par dispatcher (`05_ARCHITECTURE §3`). Barre **segmentée en 8 blocs**
(`SPEC_ART_DIRECTION §10.5`, §3.0a) : c'est la forme la plus lisible en vision périphérique, et 8 blocs
donnent une granularité de 12.5 % — assez fine pour sentir la marge, assez grossière pour se compter d'un
coup d'œil. Le dernier bloc partiel se remplit en continu, ce qui conserve la lecture de *timing*.
Ni panneau ni bordure.

**États** (couleurs de `PALETTE.md §2`) — sous `Heat_WarningThreshold` : `OD_Navy_Ink` (état neutre,
pas encore une info) · de `Heat_WarningThreshold` à `Heat_Max` : `OD_Amber_Heat` + pulse ·
à `Heat_Max` : `OD_Red_Danger` + clignotement 6 Hz. Le franchissement de `Heat_WarningThreshold` ajoute
un SFX (`S_Heat_Warning`) · **refroidissement** : les blocs se vident **franchement et visiblement** —
c'est une récompense, elle doit se voir autant que la montée.

**Interdits, depuis `D58`** : ⛔ icône de **verrou** ou de cadenas · ⛔ crosshair **barré**
(§3.1.7 corrigé) · ⛔ blocs **inversés** signifiant « attends » · ⛔ tout repère de « seuil de
déblocage » — `Heat_OverheatExitThreshold` est `INACTIVE` (`07_TUNING §11`) et **le trait vertical qui
le marquait est supprimé**. Aucun élément de l'UI ne doit suggérer que le tir est indisponible :
**il ne l'est jamais.**

#### 3.3a Affichage provisoire du coût de style — J9, dette J18

À partir de `Heat_WarningThreshold`, la barre affiche **le coût réel qui s'applique**, sous la forme
d'une ligne courte accolée à la jauge, en `OD_Amber_Heat` :

```
HEAT 82 · STYLE −0.20/s        ← exemple d'affichage. Les deux nombres sont LUS :
                                 CurrentHeat, et Style_Loss_Heat (07_TUNING §14)
```

| Règle | Détail |
|---|---|
| Source | `BPC_Heat.GetCurrentStylePenalty()` (`SPEC_COMBAT §4.4`) — **jamais** une valeur recopiée dans le widget. |
| Apparition | **exactement** au franchissement de `Heat_WarningThreshold`. Disparaît au retour sous le seuil. |
| Format | La **grandeur réelle**, telle qu'elle sera appliquée au J18 : `Style_Loss_Heat` en unités de style par seconde. |
| ⛔ Interdit | **Aucun pourcentage de score inventé**, aucune approximation « tu perds ~8 % de ton score ». On affiche ce qui existe, pas ce qu'on imagine — sinon il faudra le défaire au J18. |
| Bind | `OnHeatChanged`, comme le reste du widget. **Pas de Tick** (`06_CONVENTIONS §4.6`). |

> **Pourquoi cet affichage existe.** `BPC_StyleMeter` n'arrive qu'au **J18** : sans lui, la chaleur
> livrée au J9 serait une jauge qui bouge et **ne coûte rien**, donc impossible à juger et à calibrer.
> C'est exactement le piège `Laser_TraceRadius` qui a coûté deux chantiers au J8
> (`04_ROADMAP` J8, `12_PIEGES §6.24`). Cette ligne rend la mécanique **jugeable dès le J9**.
> **Elle n'est pas provisoire par paresse** : au J18 la valeur affichée devient la valeur appliquée,
> et il n'y a rien à réécrire.

### 3.4 `WBP_DashCharges`
Source `BPC_Dash.OnDashChargesChanged(Current,Max)` + `OnDashCooldownProgress(Ratio)` (Timer 20 Hz).
N losanges 24 px espacés de 10 px `[À CALIBRER]`, N = `Dash_MaxCharges` (rebuild du `HorizontalBox` seulement
quand `MaxCharges` change, donc à l'application d'un upgrade).
**États** — disponible : losange plein `OD_Magenta_Player` + halo blanc (le dash est une action du joueur,
donc magenta — c'est le seul élément de HUD qui porte une couleur réservée, et c'est justifié par D3) ·
consommé : contour `OD_Navy_Ink` seul, opacité 0.5 · en recharge : remplissage **radial** via
`MI_UI_RadialFill` (param `Progress` poussé par dispatcher, zéro Tick) ·
**charge rendue : flash `OD_Purple_Primary` 0.12 s + pop 1.0→1.25→1.0 en 0.18 s** `[À CALIBRER]` — feedback
clé, savoir qu'on peut redasher sans regarder · dash sans charge : shake ±4 px 0.15 s + flash `OD_Red_Danger`.

### 3.5 `WBP_SpeedMeter`
Source `BPC_MovementState.OnSpeedChanged(SpeedUUs)`, émis par le **timer unique 20 Hz** de `BPC_MovementState`
(D9 — le même qui écrit `MPC_Global.PlayerSpeed01` et alimente le vent ; aucun timer propre au widget),
vitesse **horizontale uniquement**. Nombre 64 px aligné à droite en `OD_Navy_Ink` + halo blanc 2 px, label
`SPEED` 14 px `OD_Magenta_Player` majuscules letter-spacing +0.1 em, barre fine 4 px de 0 à `Speed_HardCap`.
Ni panneau ni bordure (§3.0a).
**Lissage** : `FInterp To` **dans le handler de dispatcher** (jamais en Tick), **asymétrique** — montée 25/s,
descente 8/s `[À CALIBRER]`. Gagner de la vitesse doit se voir immédiatement, en perdre doit être doux sinon
le HUD devient stroboscopique en combat. Sans lissage, les chiffres papillonnent.

| Vitesse (uu/s) | Couleur | Sens |
|---|---|---|
| < `Speed_Walk` | `OD_Navy_Ink` 60 % | normal |
| → `Speed_SprintCap` | `OD_Navy_Ink` | sprint |
| → `SpeedLines_StartSpeed` | `OD_Purple_Primary` | momentum capitalisé |
| → `SpeedLines_FullSpeed` | `OD_Magenta_Player` | haute vitesse |
| ≥ `SpeedLines_FullSpeed` | `OD_Red_Traversal` | vitesse extrême |

> L'échelle va du **foncé neutre** au **saturé chaud** : elle monte en saturation, pas en luminosité —
> c'est la seule progression lisible sur fond clair (§1.1 règle 1). Le halo blanc est **conservé à tous les
> paliers**, y compris quand le nombre est coloré : sans lui, le magenta sur un mur clair perd son bord.
> Pas de `glow` au dernier palier (il ajouterait du clair sur du clair) : c'est la **taille** du halo qui
> passe de 2 à 3 px `[À CALIBRER]`.

**Franchissement de palier vers le haut** : `Anim_ThresholdPop` scale 1.0→1.12→1.0 en 0.2 s + flash de la
couleur cible + tick SFX `[À CALIBRER]`. **Vers le bas : aucune animation** — on ne célèbre pas la perte, la
couleur suffit. Anti-spam : 1 pop / 0.4 s max, **hystérésis ±100 uu/s** autour du seuil pour éviter le
clignotement quand on oscille sur une borne.

### 3.6 `WBP_StyleMeter`
Source `BPC_StyleMeter.OnStyleChanged(Value,Delta)` + `OnStyleEventScored(E_StyleEvent,Delta)`. Voir §5.

### 3.7 `WBP_Timer`
Source `GS_Overdrive.OnLevelTimerTick(Seconds)`, Timer 0.1 s sur le GameState — **le HUD n'a pas de
chronomètre à lui**. Formatage par `BPFL_Overdrive.FormatTime()`, réutilisé par `WBP_Results`. 28 px,
**chiffres tabulaires obligatoires** (sinon la largeur danse à chaque dixième), `OD_Navy_Ink` + halo blanc,
opacité 0.85. Si `ParTimeSeconds` (`PDA_LevelData`) est dépassé → timer `OD_Red_Danger` : le joueur sait
qu'il a perdu le S sur le temps **pendant** la run, pas à l'écran de résultats. Objectif : ligne 16 px
au-dessus (`IntroHintText` puis objectif courant), disparaît après 4 s `[À CALIBRER]`.

### 3.8 `WBP_KillCounter`
Source `GS_Overdrive.OnKillCountChanged(Kills,Total)`. `12 / 24` aligné à droite, 22 px, `OD_Navy_Ink` +
halo blanc, opacité 0.8. Chaque kill : pop 1.0→1.15→1.0 en 0.15 s. À `Kills == Total` : `OD_Amber_Heat` +
`ALL CLEAR` 14 px pendant 2 s.

### 3.9 `WBP_Hitmarker`
Source `BP_LaserWeapon.OnHitConfirmed(Target, bHeadshot, bKilled)` (`SPEC_COMBAT §3`) / `BPC_Melee.OnMeleeHit`.
4 traits diagonaux, apparition **à 0 frame de délai**, tous avec halo blanc 2 px.
Body : `OD_Navy_Ink` 10 px 0.12 s · Headshot : `OD_Amber_Heat` 14 px 0.18 s · Kill :
`OD_Magenta_Player` pivoté 45°, 16 px 0.25 s · Melee/WallSlam : `OD_Red_Danger` traits 3 px, 20 px 0.30 s.
**Le hitmarker de body passe du blanc au foncé** : c'est l'élément le plus fréquent du jeu et le plus petit,
donc celui qui souffrait le plus du fond clair.
**Une seule instance réutilisée** : un nouveau hit **redémarre** l'animation (`Stop` + `Play`), jamais de
superposition. Priorité si simultanés : `WallSlam > Kill > Headshot > Body`.

### 3.10 `WBP_DamageIndicator`
Source `BPC_Health.OnDamageTaken(S_DamageInfo)`, angle via `BPFL_Overdrive.GetScreenAngleTo()`. Arc radial
60° à un rayon de 180 px `[À CALIBRER]`, rotation par `Set Render Transform Angle` — un seul Image widget.
**Pool de 4 instances** créées au `Construct`, round-robin, zéro `Create Widget` en combat. Apparition
0.05 s / maintien 0.6 s / fondu 0.4 s `[À CALIBRER]`, `OD_Red_Danger` opacité pic 0.9, **bordé de blanc
1 px** sur son arête extérieure (sans quoi l'arc rouge se perd sur un mur en plein soleil). Le vrai feedback
de dégât reste la **perte de vitesse** (`SPEC_CAMERA_JUICE §9`).

### 3.11 `WBP_LivesCounter` — **nouveau** (D1 / D31)

> Le seul widget de HUD dont la donnée **survit au changement de niveau**. `Run_MaxLives` et
> `RunFailed_ScreenDuration` : `07_TUNING §18`. Aucune valeur de gameplay n'est écrite dans le widget.

**Source de données**

| | |
|---|---|
| Propriétaire de la donnée | **`GI_Overdrive`** — `LivesRemaining` (dans `S_RunState`, `08_DATA_SCHEMAS`). Ni le pawn ni le GameState : ils meurent avec le niveau (D1). |
| Dispatcher | **`GI_Overdrive.OnLifeLost(LivesRemaining: int)`** — nommage `On` + fait passé (`06_CONVENTIONS §3`). Émis **une fois** par mort, après l'application de `Score_DeathPenalty`. |
| Initialisation | `WBP_HUD::Construct` lit `CachedGI.LivesRemaining` et appelle `SetLives(Current, Run_MaxLives)`. **Obligatoire** : sans lecture initiale, le compteur repart plein à chaque `OpenLevel`. |
| Fonction publique | `SetLives(Current: int, Max: int)` — pousse l'état · `PlayLifeLost()` — joue l'animation. Le widget ne caste **jamais** vers `GI_Overdrive`. |
| Cas `Max == 0` | Si `Run_MaxLives` passait à 0 en tuning, le widget se masque entièrement (`Collapsed`). Pas de cas particulier ailleurs. |

**Affichage — décision : 3 chevrons `❯`, pas des pips ni des cœurs**

```
   ❯ ❯ ❯      3 vies          ❯ ❯ ·      2 vies
   ❯ · ·      1 vie (état critique, cf. ci-dessous)
```

| | |
|---|---|
| Forme | **Chevron `❯`** dessiné comme un `Image` (`MI_UI_Chevron`), 16×16 px, espacement 8 px `[À CALIBRER]`, alignés à gauche dans un `HorizontalBox`. |
| Nombre d'éléments | `Run_MaxLives` — le `HorizontalBox` est reconstruit **uniquement** si `Max` change (donc jamais en jeu). |
| Vie disponible | Chevron **plein** `OD_Navy_Ink` + halo blanc 2 px (§1.1). |
| Vie perdue | Chevron réduit à son **contour** `OD_Navy_Ink` à 0.3 d'opacité. **La case reste occupée** : on doit voir qu'il *manque* quelque chose, pas seulement qu'il en reste moins. Un `HorizontalBox` qui rétrécit ne se remarque pas en périphérie. |
| Label | `LIVES` 11 px `OD_Navy_Ink` 0.7, à droite des chevrons. Purement mnémotechnique les premières parties, ignorable ensuite. |
| Au repos | **Totalement immobile.** Aucun pulse, aucun glow, aucune animation d'idle — sauf à 1 vie. |

**Pourquoi le chevron** : il reprend la signalétique directionnelle du décor (`OD_Purple_Primary`,
`PALETTE.md §3` — même glyphe `»`), donc il est déjà dans le vocabulaire visuel du joueur. Il est
**asymétrique**, donc reconnaissable en vision périphérique sans être compté, contrairement à un pip rond
que l'œil confond avec les losanges de `WBP_DashCharges` deux lignes plus bas. Les cœurs sont exclus : ce
ne sont pas des PV, c'est un nombre de tentatives.

**État à 1 vie restante — le plus important du widget**

C'est le seul moment où l'UI a le droit de bouger en permanence. À `LivesRemaining == 1` :

| Canal | Effet |
|---|---|
| Chevron restant | Passe en **`OD_Red_Danger`** (halo blanc conservé) et **grossit de 16 à 22 px** `[À CALIBRER]`. Le changement de **taille** est ce qui se lit en périphérie ; la couleur seule ne suffirait pas. |
| Label | `LIVES` devient **`LAST LIFE`** en `OD_Red_Danger` 12 px. |
| Pulse | Respiration lente d'opacité 0.75 ↔ 1.0 sur **1.6 s** `[À CALIBRER]`, courbe sinusoïdale. **Lente et continue, jamais un clignotement** : c'est un état de tension qui dure un niveau entier, pas une alarme. |
| Écran | `NS_LastLife_Aura` (`SPEC_VFX §2.7`) + la teinte continue de `SPEC_CAMERA_JUICE §9`. Le widget n'est **pas** seul à porter l'information. |
| Audio | Boucle de tension `S_LastLife_Loop` (`SPEC_AUDIO §2.4`). |

**Sortie de l'état** : le passage au niveau suivant **ne recharge pas** les vies (D1) — l'état à 1 vie
**persiste** jusqu'à la fin de la run ou jusqu'à `RunFailed`. Le widget ne repasse à 3 chevrons pleins
qu'au démarrage d'une **nouvelle run** (`GI_Overdrive.StartNewRun()`).

**Animation de perte de vie (`Anim_LifeLost`)** — jouée par `PlayLifeLost()`, **au respawn**, pas à l'instant
de la mort (pendant la mort, l'écran est en fondu, `SPEC_CAMERA_JUICE §10` : l'animation serait invisible).

| t | Effet |
|---|---|
| 0.00 | Le chevron perdu **flashe `OD_Red_Danger`** à pleine opacité et scale 1.0 → 1.4. |
| 0.12 | Scale 1.4 → 0.0 en 0.18 s, courbe ease-in, opacité → 0. Le chevron **s'effondre**. |
| 0.30 | Le contour vide apparaît en fondu 0.2 s à opacité 0.3. La case est désormais visiblement trouée. |
| 0.50 | Si `LivesRemaining == 1` : enchaîne sur l'entrée de l'état critique (grossissement + `LAST LIFE`, 0.3 s). |

Durée totale **0.8 s** `[À CALIBRER]`, **non skippable** (elle se joue pendant que le joueur reprend le
contrôle, elle ne le retient pas). Une seule animation, jamais deux en parallèle : deux morts ne peuvent pas
se produire à 0.8 s d'intervalle (`Restart_FadeDuration` + respawn ≥ 0.5 s, D16).

**Interdit** : afficher `LIVES 2/3` en chiffres (on ne lit pas un chiffre à 5000 uu/s) · faire disparaître
le widget quand il reste 3 vies · un panneau ou une bordure (§3.0a) · un clignotement rapide à 1 vie.

---

## 4. Affichage de la vitesse — SPEED ou km/h ?

`07_TUNING §1` définit les deux ; le choix se fait **ici**.

| Option | Formule | À 3000 uu/s | Pour | Contre |
|---|---|---|---|---|
| **A — `SPEED`** (GDD §6) | `round(uu/s ÷ 10)` | `300` | Aligné sur toute la doc, le tuning et les seuils de rank. Debug trivial. 3 chiffres → typo stable. | Unité abstraite, aucune référence réelle. |
| **B — km/h arcade** | `round(uu/s × 0.036 × 3)` | `324 km/h` | Conforme à la key art, lisible « racing HUD », vend la vitesse au premier regard. | Second système d'unités = classe entière de bugs de calibration. Le km/h réel (`108`) serait trop bas, donc le ×3 reste arbitraire. |

**Recommandation : option A, avec la présentation visuelle de l'option B.** Le doc, le tuning, les seuils de
rank et les logs parlent tous en `uu/s ÷ 10` ; introduire une seconde unité pour du cosmétique est un risque
disproportionné en solo sur 4 semaines. On garde **le nombre de A** et **l'habillage racing de la key art**
(gros nombre condensé, label magenta, barre de progression, glow aux hautes valeurs).
Implémentation : `BPFL_Overdrive.SpeedToDisplay(SpeedUUs) → Int`, **fonction pure unique** partagée par
`WBP_SpeedMeter` et `WBP_Results` : si Louis tranche pour les km/h, une ligne change et l'unité change
partout. Booléen `bUseArcadeKmh` dans le `SaveGame` de settings (§9).

---

## 5. Style multiplier

Seul terme **multiplicatif** du score (`SPEC_SCORE_RANK §2`) : la stat à comprendre le plus vite et à
regarder le moins souvent.

```
┌──────────────────────────────┐
│  ▰▰▰▰▰▰▰▱▱▱          x2.4   │
│  STYLE                       │
└──────────────────────────────┘
```
Valeur `x2.4` (1 décimale) 32 px alignée à droite, `OD_Navy_Ink` + halo blanc. Barre 5 px, remplissage
`(Value - Style_Start) / (Style_Max - Style_Start)` : **elle rend visible la marge restante**, ce que le
nombre seul ne fait pas. Paliers `[À CALIBRER]` : `OD_Navy_Ink` x1 → `OD_Purple_Primary` x2 →
`OD_Magenta_Player` x3 → `OD_Red_Traversal` x4+ ; le changement de couleur est un événement plus fort que
le changement de chiffre. **Même progression que `WBP_SpeedMeter` (§3.5)** : les deux stats montent
ensemble et doivent se lire comme un seul mouvement de couleur, du neutre foncé vers le saturé chaud.

**Gain — décision : texte flottant transitoire, pas de liste persistante.** Une liste empilée (style DMC)
oblige à lire du texte en périphérie, donc coûte une fixation oculaire : inacceptable à 5000 uu/s. Un texte
unique **toujours au même endroit** est reconnu par sa forme et sa couleur, sans lecture.

| Élément | Spec |
|---|---|
| Position | Au-dessus de `WBP_StyleMeter`, ancré bas-droite, `Y -96` `[À CALIBRER]`. |
| Contenu | `DisplayText` de `DT_StyleEvents` (`08_DATA_SCHEMAS §4`) + delta. Ex. `HEADSHOT +0.35`. |
| Animation | Scale 1.3→1.0 + slide `+12 px → 0` en 0.12 s, maintien 0.5 s, fondu 0.3 s `[À CALIBRER]`. |
| Empilement | **Max 3 lignes**, pool de 3 widgets, la plus ancienne recyclée. Zéro `Create Widget` en combat. |
| Combo rapide | Même `E_StyleEvent` pendant que sa ligne est visible → **pas de nouvelle ligne**, incrément `x2`, `x3` sur l'existante + rejoue son pop. Évite le mur de texte en multikill. |
| Meter | `Anim_Gain` : pop 1.0→1.15→1.0 en 0.15 s + flash de la couleur du palier. |

**Perte — plus lisible que le gain, c'est elle qui enseigne** (`07_TUNING §14`) : décroissance passive → la
barre descend, aucune animation, silencieux (le joueur voit fondre sa marge) · `Style_Loss_TakeDamage` →
ligne `OD_Red_Danger` `-0.75` au même emplacement + shake ±6 px 0.2 s + barre flash `OD_Red_Danger` ·
`Style_Loss_Idle` → le label `STYLE` clignote 2× `[À CALIBRER]` **avant** que la perte s'applique
(avertissement, pas punition surprise) · chute de palier → flash `OD_Red_Danger` 0.2 s, son sourd et court,
jamais triomphal · `Style_Loss_Death` → le meter se vide en 0.4 s de droite à gauche, **en même temps que
`Anim_LifeLost`** (§3.11) : les deux punitions de la mort se lisent d'un seul coup d'œil, aux deux coins
bas de l'écran.

---

## 6. Écran de résultats (`WBP_Results`)

Objectif (`SPEC_SCORE_RANK §1`) : **une seule pensée en moins de 4 s** — « j'ai raté le S à cause de **ça**, je le refais ».

```
┌────────────────────────────────────────────────────────────────────┐
│                      L E V E L   C O M P L E T E                   │ 48px OD_Magenta_Player
│                          W1-01  IGNITION                           │ 18px OD_Grey_Shadow
│  ┌──────────────────────────────────────┐   ┌───────────────────┐  │
│  │ TIME                        01:12.44 │   │                   │  │
│  │ KILLS                          18/24 │   │        A          │  │ 180px OD_Rank_A
│  │ AVG SPEED                        318 │   │      RANK         │  │ 16px OD_Amber_Heat
│  │ MAX SPEED                        412 │   │                   │  │
│  │ STYLE                          x 3.2 │   │                   │  │
│  ├──────────────────────────────────────┤   └───────────────────┘  │
│  │ SCORE                         48 720 │                          │
│  └──────────────────────────────────────┘                          │
│  ── S RANK  vs  YOUR RUN ────────────────────────────────────────  │ 16px OD_Magenta_Player
│  ┌──────────────┬───────────────┬───────────────┬──────────────┐   │
│  │              │   S RANK      │   YOUR RUN    │    DELTA     │   │
│  │ TIME         │   01:05.00    │   01:12.44    │   +7.44 s    │   │
│  │ KILLS        │      24       │      18       │      -6      │   │ ◀ surligné
│  │ AVG SPEED    │     350       │     318       │     -32      │   │
│  │ STYLE        │    x 4.0      │    x 3.2      │    -0.8      │   │
│  │ SCORE        │   61 000      │   48 720      │  -12 280     │   │
│  └──────────────┴───────────────┴───────────────┴──────────────┘   │
│   ▸ YOU LOST S ON: KILLS  —  6 ENEMIES LEFT ALIVE                  │ 22px OD_Amber_Heat
│        [ R ]  RETRY            [ SPACE ]  CONTINUE ▸               │ 18px
└────────────────────────────────────────────────────────────────────┘
```

Panneaux **`OD_Navy_Deep` à 0.92** (`PALETTE.md §7`), bordure 1 px `OD_Magenta_Player`, en-têtes
`OD_Magenta_Player` majuscules, valeurs `OD_White_Pure`, texte secondaire `OD_Grey_Shadow`, colonne
`S RANK` en `OD_Amber_Heat`. Le gameplay reste visible et figé derrière (blur léger `[À CALIBRER]`) :
le joueur voit où il s'est arrêté.

> **Le panneau foncé sur un monde blanc est un avantage, pas un problème** : le contraste est maximal
> sans qu'on ait à assombrir le fond. **L'opacité 0.92 ne descend pas** — à 0.7 devant une ville en plein
> soleil, le texte devient illisible.

**Couleur de la grosse lettre de rank : une couleur par rang** (D18, `PALETTE.md §6`) — les HEX vivent dans
`PALETTE.md`, jamais ici : `OD_Rank_D` · `OD_Rank_C` · `OD_Rank_B` · `OD_Rank_A` · `OD_Rank_S`.
**Pas de magenta systématique** : `OD_Rank_S` *est* le magenta du joueur (« tu as joué comme le jeu le
voulait »), l'utiliser pour un D détruirait le signal. Les notes de détail (bonus, sous-scores) restent en
`OD_Gold_Rank`. La variante de `NS_Rank_Reveal` jouée derrière la lettre suit la même couleur
(`SPEC_VFX §2.6`) — sur le panneau `OD_Navy_Deep`, donc les VFX de rank sont les **seuls** du jeu qui ont
le droit d'être additifs (`SPEC_VFX §7.1`).

**Vitesse comparée : `AverageSpeed`, pas `MaxSpeed`** (D14). C'est `AverageSpeed` qui alimente `ScoreSpeed`
(`SPEC_SCORE_RANK §2`) : comparer un pic ponctuel à une cible de rang récompenserait un unique dash contre
un mur. `MaxSpeed` **reste affichée** dans le bloc de statistiques (c'est un trophée lisible), mais elle
n'entre ni dans la comparaison de rang, ni dans le calcul du coupable.

**Séquence** — une `Widget Animation` maîtresse `Anim_ResultsSequence`, **skippable dès la frame 1** par
n'importe quelle touche (`Set Animation Current Time` = fin). On ne retient jamais le joueur.

La cadence d'apparition des lignes est **`Results_StepDelay`** (`07_TUNING §14`) — aucune durée d'étape n'est
écrite en dur dans le widget. Le tableau ci-dessous exprime les étapes en multiples de cette clé (`n × Step`),
pas en secondes absolues : régler `Results_StepDelay` doit suffire à accélérer ou ralentir tout l'écran.

| t | Événement |
|---|---|
| `0 × Step` | Fond + panneaux, fondu, blur, SFX whoosh. |
| `1 × Step` | `LEVEL COMPLETE` : slide depuis la gauche, letter-spacing qui se resserre. |
| `2` / `3` / `4` / `5` / `6 × Step` | `TIME` / `KILLS` / `AVG SPEED` / `MAX SPEED` / `STYLE` : count-up + tick SFX. |
| `7 × Step` | `SCORE` : count-up **long** (≈ 2 × `Step`), tick SFX qui accélère. |
| `9 × Step` | `RANK` : scale 3.0→1.0, shake UI, flash `OD_White_Pure` (autorisé ici : on est **sur le panneau foncé**), `S_Stinger_Rank_<D..S>` (`SPEC_AUDIO §2.4`). |
| `10 × Step` | Séparateur `S RANK vs YOUR RUN` : trait tracé de gauche à droite. |
| `11 × Step` | Lignes de comparaison en cascade, `Results_StepDelay ÷ 6` d'écart. |
| `13 × Step` | **Surlignage du coupable** : bordure `OD_Amber_Heat` 2 px + fond `OD_Amber_Heat` 12 % + pop 1.0→1.05→1.0. |
| `14 × Step` | `YOU LOST S ON: …` + SFX grave. |
| `15 × Step` | Prompts d'input (pulse lent). **Les inputs sont acceptés dès t = 0.** |

Si `Rank == S` : les deux dernières étapes (`13`/`14 × Step`) sont remplacées par `PERFECT RUN` en
`OD_Amber_Heat`, aucune comparaison (rien à comparer), le tableau se réduit à la colonne `YOUR RUN`.

**Tableau** — cibles : `PDA_LevelData.RankThresholds` (`S_RankThresholds` : `ParTimeSeconds`, `TargetKills`,
`TargetStyle`, **`TargetAverageSpeed`** (D14), `ScoreS`) ; run : `S_LevelScore` de `BPC_ScoreManager`. Libellés
`OD_Magenta_Player` 16 px · `S RANK` en `OD_Amber_Heat` · `YOUR RUN` en `OD_White_Pure` · `DELTA` signé avec
unité, **`OD_Purple_Primary` si ≥ cible** (le cyan de la v1 n'existe plus, D3), `OD_Red_Danger` sinon.
Tous les chiffres en font tabulaire (`F_Overdrive_Data`, §10).

**Désigner LE coupable** — `BPFL_Overdrive.GetLimitingStat()` (fonction pure, D13) :
1. Écart normalisé `Gap01 = clamp((Target - Actual) / Target, 0, 1)` — pour `TIME`, inverser.
2. Ignorer les composantes où `Gap01 <= 0` (cible atteinte).
3. Prendre le max ; égalité à moins de 5 % `[À CALIBRER]` → départager par **`TIME > KILLS > STYLE > SPEED`**
   (ordre d'impact réel sur le score). `SPEED` désigne ici `AverageSpeed` vs `TargetAverageSpeed`, jamais `MaxSpeed`.
4. Message concret : `TIME — 7.4 S TOO SLOW` · `KILLS — 6 ENEMIES LEFT ALIVE` ·
   `SPEED — AVERAGE 318, NEEDED 350` · `STYLE — CHAIN WITHOUT TAKING HITS`.

**Un seul coupable** : deux surlignages = aucune conclusion. La ligne est surlignée dans le tableau **et**
reprise en toutes lettres en dessous — redondance volontaire, c'est le message central de l'écran.

**Navigation** : toute touche = skip · `R` = `IA_Restart`, **hold 0.4 s** (`09_INPUT §3`, D16) → restart
direct (`Restart_FadeDuration`, aucun menu intermédiaire) · `Space`/`Enter`/clic `CONTINUE` = `WBP_LootChest` · `Esc` = pause. Focus initial sur
`CONTINUE`, `SetInputModeUIOnly` + curseur visible.

---

## 6.1 Écran de run perdue (`WBP_RunFailed`) — **nouveau** (D1 / D31)

Déclenché par **`E_GameState.RunFailed`**, atteint quand `LivesRemaining` tombe à 0 (`07_TUNING §18`).
Il **remplace** `WBP_Results` : la run est finie, il n'y a ni rank de niveau à donner, ni coffre à ouvrir.

> **Objectif, en une phrase** : *« voilà jusqu'où tu es allé, et voilà ce que tu vas retenter. »*
> Pas une punition, un **bilan de run**. C'est le seul écran du jeu qui résume une run entière —
> `WBP_Results` ne résume qu'un niveau.

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                       R U N   F A I L E D                          │ 64px OD_Red_Danger
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ REACHED              W2-02   OVERPASS      ( 5 / 8 )         │  │ 22px
│  │ RUN SCORE                                    182 940         │  │ 32px OD_Gold_Rank
│  │ TOTAL TIME                                  07:41.12         │  │ 22px
│  │ UPGRADES                                         4           │  │ 22px
│  ├──────────────────────────────────────────────────────────────┤  │
│  │  ▸ MOMENTUM CORE   ▸ VENT   ▸ OVERDRIVE   ▸ GECKO            │  │ 16px, par rareté
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│              [ SPACE ]  BACK TO MENU ▸                             │ 18px
└────────────────────────────────────────────────────────────────────┘
```

**Contenu** — source unique : `S_RunState` de `GI_Overdrive` (`08_DATA_SCHEMAS`).

| Ligne | Donnée | Format |
|---|---|---|
| `REACHED` | Nom du dernier niveau atteint + index / `Run_LevelCount` (`07_TUNING §18` = 8) | `DisplayName` de `PDA_LevelData` + `( n / 8 )`. Le compteur est **l'information principale** : c'est le record que le joueur cherchera à battre. |
| `RUN SCORE` | **Somme** des `S_LevelScore.Total` de tous les niveaux terminés, pénalités de mort incluses (`Score_DeathPenalty`, `07_TUNING §14`) | Count-up, `OD_Gold_Rank`, `F_Overdrive_Display` 32 px. La seule valeur en or de l'écran. |
| `TOTAL TIME` | Cumul des chronos de niveau, `BPFL_Overdrive.FormatTime()` | Font tabulaire. |
| `UPGRADES` | `Num` du tableau d'upgrades actifs (max **7**, D29) | Chiffre seul. |
| Liste d'upgrades | `DisplayName` de chaque `S_UpgradeInstance` collecté, dans l'ordre d'acquisition | Chips 16 px, **texte à la couleur de la rareté** (`PALETTE.md §5` : `Common` / `Rare` / `Epic`). Wrap sur 2 lignes max ; au-delà de 7 il n'y a rien à gérer (D29). |

**Ce qui n'est PAS sur cet écran** : aucun rank (il est par niveau, pas par run) · aucune comparaison au
S rank · aucun coupable désigné (`GetLimitingStat()` n'a pas de sens sur une run) · **aucun bouton
`RETRY`** — une run perdue se rejoue depuis le début, ce qui est exactement `PLAY` au menu (D1 : « retour
au menu / nouvelle run → reset total »). Proposer un retry ici laisserait croire qu'on reprend la run.

**Apparence** — `PALETTE.md §7` : panneau `OD_Navy_Deep` **0.92**, bordure 1 px `OD_Magenta_Player`,
titre `RUN FAILED` en **`OD_Red_Danger`** `F_Overdrive_Display` 64 px, libellés `OD_Magenta_Player` 16 px,
valeurs `OD_White_Pure`. Le monde reste visible et figé derrière, **assombri** par `NS_RunFailed`
(`SPEC_VFX §2.7`) : c'est le seul moment du jeu où la ville blanche s'éteint.

**Durée et sortie**

| | |
|---|---|
| Durée | **`RunFailed_ScreenDuration`** (`07_TUNING §18`) avant retour automatique au menu. Aucune durée en dur dans le widget. |
| Skippable | **Oui, dès la frame 1** — même règle que `WBP_Results` : on ne retient jamais le joueur. Toute touche accélère `Anim_RunFailedSequence` à sa fin ; une seconde pression (ou `Space`/`Enter`/clic) déclenche le retour au menu immédiatement. |
| Retour | `OpenLevel(L_Menu)` via la transition **Jeu → menu** de `SPEC_CAMERA_JUICE §10`. `GI_Overdrive` reset son `S_RunState` **à l'entrée du menu**, pas ici — sinon l'écran afficherait des zéros. |
| Audio | `S_RunFailed` (`SPEC_AUDIO §2.4`), et `SMX_Results` est réutilisé tel quel pour le mix. |

**Séquence** (`Anim_RunFailedSequence`, cadencée par `Results_StepDelay`, `07_TUNING §14` — on ne crée pas
une seconde clé de cadence pour un seul écran) :

| t | Événement |
|---|---|
| `0 × Step` | Assombrissement + panneau en fondu, `S_RunFailed`. |
| `1 × Step` | `RUN FAILED` : apparition en scale 1.3 → 1.0, letter-spacing qui se resserre. |
| `2` / `3` / `4 × Step` | `REACHED` / `RUN SCORE` (count-up) / `TOTAL TIME`. |
| `5 × Step` | `UPGRADES` + les chips en cascade (`Results_StepDelay ÷ 6` d'écart). |
| `6 × Step` | Prompt `BACK TO MENU` (pulse lent). **Les inputs sont acceptés dès t = 0.** |

**Interdit** : un `Game Over` plein écran opaque et immobile · un bouton `RETRY` · retenir le joueur
au-delà de `RunFailed_ScreenDuration` · afficher un rank.

---

## 7. Écran de coffre (`WBP_LootChest`)

Après `WBP_Results` → `BP_LootChest.Roll(Rank)` → `S_LootRollResult` (drop rates `07_TUNING §15`).

```
┌────────────────────────────────────────────────────────────────────┐
│                      S   R A N K   C A C H E                       │ 40px OD_Rank_S
│                       CHOOSE ONE UPGRADE                           │ 16px OD_Magenta_Player
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐          │
│  │    [icon]    │    │    [icon]    │    │    [icon]    │          │
│  │ MOMENTUM     │    │ VENT         │    │ OVERDRIVE    │          │
│  │ CORE         │    │              │    │              │          │
│  │ ── EPIC ──   │    │ ── RARE ──   │    │ ── COMMON ── │          │
│  │ Speed kept   │    │ Weapon cools │    │ Raises max   │          │
│  │ on jump      │    │ down faster  │    │ speed cap    │          │
│  │              │    │ HEAT RECOV.  │    │ MAX SPEED    │          │
│  │              │    │   20 ▸ 26    │    │ 6000 ▸ 6300  │          │ avant ▸ après
│  └──────────────┘    └──────────────┘    └──────────────┘          │
│   [ 1 ] [ 2 ] [ 3 ]  or  ← →  + ENTER                              │
└────────────────────────────────────────────────────────────────────┘
```

> **Vérification arithmétique des exemples ci-dessus** (`07_TUNING §15` fait foi, aucune valeur n'est inventée) :
> `VENT` Rare = `+HeatRecovery +30 %` sur **`Heat_CoolRateAtSpeed`** = 20 → **26** (et non +50 %, qui est la
> valeur Epic). ⚠️ **Changé par `11_ARBITRAGES D58`** : `+HeatRecovery` portait sur `Heat_DecayRate` (45 → 58.5),
> qui est désormais **`INACTIVE`** — il n'y a plus de décroissance passive. L'upgrade surcharge maintenant les
> deux **puits** de chaleur, `Heat_CoolRateAtSpeed` et `Heat_CoolPerHeadshot` (`SPEC_COMBAT §4.2`) ; la carte
> n'affiche que le premier, c'est celui que le joueur voit fondre.
> `OVERDRIVE` Common = `+MaxSpeed +5 %` sur `Speed_HardCap` = 6000 → **6300**.
> Un `GECKO` Rare afficherait `WALL RIDE 2.0 s ▸ 2.8 s` (`+WallRideDuration +40 %` sur `WallRide_MaxDuration` = 2.0 s).
> **`MOMENTUM CORE` n'affiche aucune ligne « avant ▸ après »** : c'est un **modificateur de gameplay**
> (`SPEC_LOOT_UPGRADES §5`), pas un pourcentage sur une stat — il n'y a rien à comparer, et forcer un chiffre
> ici induirait le joueur en erreur. Même règle pour `THERMAL CORE`, `IMPACT`, `OVERCHARGED LASER`,
> `DASH RECHARGE ON KILL`.

Cartes 280×400 px `[À CALIBRER]`, fond **`OD_Navy_Deep` 0.92**, bordure 1 px **par rareté**, couleurs de
`PALETTE.md §5` (D17) : `Common` · `Rare` · `Epic`. Les HEX vivent dans `PALETTE.md`, jamais ici.
**Ni magenta, ni rouge, ni orange** : ces trois familles sont réservées au gameplay (joueur, traversée,
ennemi) — c'est la règle explicite de `PALETTE.md §5`. Titre du coffre à la couleur du rank
(`OD_Rank_D..S`, §6).
**Ouverture** : 0.00 fondu 0.15 s · 0.15 titre impact scale 1.4→1.0 + SFX · 0.40 cartes en cascade (0.08 s
d'écart, slide `+30 px → 0`), les `Epic` **en dernier** avec un flash · 0.80 prompts + focus sur la carte du milieu.
**Contenu** (`S_UpgradeInstance`) : icône (soft ref chargée à l'ouverture), `DisplayName` (celui de
`SPEC_LOOT_UPGRADES §5` — `OVERDRIVE`, `VENT`, `GECKO`, `FLOW`… ; le nom `HARD CAP` n'existe pas), `Rarity`
(couleur + libellé), `Description` (une ligne, **jamais de chiffre**), et — **pour les upgrades de stat
uniquement** — **Avant ▸ Après** via `BPC_PlayerStats.PreviewUpgrade() → (Before, After)`,
`Before` `OD_Grey_Shadow` / `After` **`OD_Purple_Primary`** (le vert-cyan de la v1 n'existe plus, D3 ;
le violet est la teinte « valeur améliorée » de tout le document, cf. §3.0a). Un modificateur de gameplay
laisse cette zone **vide**.
**C'est le point le plus important de l'écran** : le joueur ne doit jamais choisir entre « +18 % » et « +30 »
sans savoir sur quoi. La preview tient compte des upgrades **déjà actifs**. Si le garde-fou de cumul
(+100 %, `07_TUNING §15`) est atteint : `CAPPED` en `OD_Red_Danger` et `After` clampé, visible **avant** le choix.
**Navigation** : `1`/`2`/`3` sélection directe (le plus rapide) · `←`/`→` focus (scale 1.05, bordure 2 px,
glow) · `Enter`/`Space`/clic valide (`Anim_Confirm` 0.3 s → `GI_Overdrive.AddUpgrade()` → `OpenLevel(NextLevel)`)
· survol souris = focus (état **partagé** souris/clavier).
**Pas d'option « skip »** : renoncer à une upgrade n'est pas au scope (`03_SCOPE_LOCK`). Le joueur choisit
toujours une carte — l'écran ne se ferme pas autrement.

---

## 8. Menus

```
L_Menu → WBP_MainMenu ─┬─ PLAY      → GI_Overdrive.StartNewRun() → OpenLevel(L_W1_01_Ignition)
                       ├─ SETTINGS  → WBP_Settings (overlay)
                       └─ QUIT      → Quit Game
Esc    → WBP_Pause    ─┬─ RESUME    → unpause
                       ├─ RESTART   → RestartLevel (Restart_FadeDuration)
                       ├─ SETTINGS  → WBP_Settings (overlay)
                       └─ QUIT RUN  → confirmation inline → OpenLevel(L_Menu)

LivesRemaining == 0   → E_GameState.RunFailed → WBP_RunFailed (§6.1) → OpenLevel(L_Menu)
```
`StartNewRun()` remet `LivesRemaining = Run_MaxLives` et vide les upgrades (D1) : c'est le **seul** endroit
du jeu où les vies se rechargent.

**`WBP_Settings` est le MÊME asset** dans les deux contextes : variable `ReturnTarget` (`MainMenu`/`Pause`)
+ dispatcher `OnSettingsClosed`. Aucune duplication.

**`WBP_MainMenu`** : fond = rendu du niveau `L_Menu` avec caméra en travelling lent (pas une image fixe).
**Ce fond est désormais une ville blanche en plein jour** : les textes du menu sont donc tracés en
`OD_Navy_Ink` avec halo blanc (§1.1), pas en blanc.
Titre `OVERDRIVE` 120 px `OD_Magenta_Player` letter-spacing large, ancré haut-gauche 96/96 px `[À CALIBRER]`.
Boutons verticaux alignés à gauche 240×56 px, espacement 12 px, ancrés bas-gauche, majuscules 24 px.
`v0.1 — BUILD {n}` bas-droite 12 px `OD_Navy_Ink` 60 %. États : Normal (`OD_Navy_Ink` 75 %, **pas de fond**) ·
Hover/Focus (`OD_Navy_Ink` 100 %, barre `OD_Magenta_Player` 3 px à gauche déployée en 0.1 s, décalage
`+8 px` X) · Pressed (fond `OD_Magenta_Player` 15 %). Aucun bouton n'a de fond au repos : la key art est
faite de bordures, pas de blocs.

**`WBP_Pause`** : `Set Game Paused`, HUD conservé à opacité × 0.3. Panneau centré 420×360 px,
**`OD_Navy_Deep` 0.92**, bordure `OD_Magenta_Player`, titre `PAUSED`, stats de la run en cours en 14 px
`OD_Grey_Shadow` sous les boutons — **`LIVES` y figure** (le seul endroit où les vies apparaissent en
chiffres, §3.11). `QUIT RUN` → confirmation **inline** (le bouton devient `SURE? [Y/N]`), pas de modale.

**Navigation (tous menus)** : `↑↓`/`W S` focus avec wrap-around · `←→`/`A D` modifie la valeur du réglage
focus · `Enter`/`Space` valide · `Esc` recule d'un cran · le survol souris **définit** le focus
(`SetKeyboardFocus` sur `OnMouseEnter`) — un seul état de focus, jamais deux surbrillances. À l'ouverture, un
élément a **toujours** le focus (`Set Keyboard Focus` au `Construct`), sinon la première frappe est perdue.
Input mode `UI Only` en menu, `Game and UI` pour le HUD.

---

## 9. Settings

Sauvegarde : **`SG_Settings`**, slot `"OverdriveSettings"`, user index 0. **Seule sauvegarde du MVP**
(`05_ARCHITECTURE §6` : pas de save/load de progression).

> **Ce tableau est la liste exhaustive et unique du contenu de `SG_Settings`.** Les options de confort de
> `SPEC_CAMERA_JUICE §11` et l'inversion Y de `09_INPUT §3` y sont **fusionnées** : elles sont décrites en
> détail dans leur spec d'origine, mais c'est ici qu'on lit *ce qui existe*. Un réglage absent de ce tableau
> n'existe pas.

| Section | Option | Variable | Type | Plage | Défaut | Application |
|---|---|---|---|---|---|---|
| AUDIO | Master volume | `MasterVolume` | Float | 0–1, pas 0.05 | 0.8 | `Set Sound Mix Class Override` sur `SCL_Master` via `SMX_Default`. |
| AUDIO | Music volume | `MusicVolume` | Float | 0–1 | 0.7 | idem `SCL_Music`. |
| AUDIO | SFX volume | `SFXVolume` | Float | 0–1 | 1.0 | idem `SCL_SFX`. |
| CONTROLS | Sensibilité souris | `MouseSensitivity` | Float | 0.1–3.0, pas 0.05 | 1.0 | Scalar de `IA_Look` via `InputModifier_Scalar`, piloté par `PC_Overdrive`. |
| CONTROLS | **Inversion Y** | `bInvertY` | Bool | on/off | **off** | Modificateur `Negate` sur l'axe Y de `IA_Look`, appliqué par `PC_Overdrive` (`09_INPUT §3`). |
| CONTROLS | Sprint mode | `SprintMode` | Enum | Hold / Toggle | `Sprint_Mode` (`§4`) | Lu par `BPC_MovementState`. |
| CONTROLS | Unité de vitesse | `bUseArcadeKmh` | Bool | SPEED / KM/H | SPEED (§4) | `BPFL_Overdrive.SpeedToDisplay`. |
| VIDEO | Window mode | `WindowMode` | Enum | Fullscreen / Borderless / Windowed | Borderless | `r.SetRes {W}x{H}{f\|wf\|w}`. |
| VIDEO | Résolution | `Resolution` | IntPoint | `GetSupportedFullscreenResolutions` | Natif desktop | idem, appliqué avec `WindowMode`. |
| VIDEO | FOV | `PlayerFOV` | Float | 80–120 | `FOV_Base` | `BP_PlayerCameraManager`. **Base du FOV dynamique : `SPEC_CAMERA_JUICE §2.1`.** |
| VIDEO | Motion blur | `bMotionBlur` | Bool | on/off | **off** (`SPEC_CAMERA_JUICE §7`) | `r.MotionBlurQuality 0/4`. |
| VIDEO | Speed lines | `bSpeedLines` | Bool | on/off | on | `MPC_Global` ; à off, `PP_SpeedLines` est retiré des blendables de `BP_PlayerCameraManager`. |
| CONFORT | **Camera shake** | `ShakeScale` | Float | 0–1 | 1.0 | Multiplie tous les scales des `CS_*`. À 0, aucun `StartCameraShake` n'est appelé (`SPEC_CAMERA_JUICE §5`). |
| CONFORT | **Effet de vitesse sur le FOV** | `FOVSpeedEffectScale` | Float | 0–1 | 1.0 | Multiplie `SpeedAdditive` et `DashAdditive`. À 0, le FOV est constant (`SPEC_CAMERA_JUICE §2`). |
| CONFORT | **Camera tilt** | `TiltScale` | Float | 0–1 | 1.0 | Multiplie `FinalRoll` (`SPEC_CAMERA_JUICE §3`). À 0, l'horizon ne bouge jamais. |
| CONFORT | **Aberration chromatique** | `bChromaticAberration` | Bool | on/off | on | Blendable `PP_ChromaticAberration` de `BP_PlayerCameraManager` (`SPEC_CAMERA_JUICE §7`). |
| CONFORT | **Hit-stop** | `bHitStop` | Bool | on/off | on | À off, `BPC_HitStop.RequestHitStop()` retourne immédiatement `false` (`SPEC_CAMERA_JUICE §6`). |

**Ordre de livraison si le temps manque** (`CLAUDE.md R5`) : `ShakeScale`, `PlayerFOV` et
`FOVSpeedEffectScale` d'abord — les autres options de confort sont du bonus.

```
GI_Overdrive :: Init
   ├─ Does Save Game Exist("OverdriveSettings") ?
   │     oui → Load Game From Slot → Cast SG_Settings
   │     non → Create Save Game Object(SG_Settings) → Save Game To Slot
   └─ ApplyAllSettings()          ← fonction UNIQUE, rappelée après chaque changement
```
`ApplyAllSettings()` vit sur `GI_Overdrive` : **un seul endroit** applique les réglages. Un changement est
appliqué **immédiatement** (aperçu direct, indispensable pour FOV et sensibilité) et **sauvegardé à la
fermeture** du menu. `RESET TO DEFAULTS` recrée un `SG_Settings` neuf + `ApplyAllSettings()`.
Résolution/fullscreen : retour arrière automatique après 10 s sans confirmation `[À CALIBRER]` (protection
contre un mode d'affichage invalide).
**Layout** : panneau `OD_Navy_Deep` 0.92, deux colonnes (libellé `OD_Magenta_Player` majuscules 16 px,
largeur fixe 280 px / contrôle, valeurs `OD_White_Pure`). Quatre sections séparées par un trait
`OD_Magenta_Player` : `AUDIO` · `CONTROLS` · `VIDEO` · `COMFORT`. Sliders rail 4 px `OD_Grey_Shadow` +
poignée losange 14 px `OD_Magenta_Player` + valeur à droite. Toggles `[ ON ][OFF]`, actif en
`OD_Magenta_Player` plein. **Pas d'onglets** : une page scrollable = moins de widgets, moins de navigation.

---

## 10. Système de design UI

Tokens dans **`DA_UITokens`** (Data Asset, `06_CONVENTIONS §2` : le préfixe `SL_` est réservé aux
**Slate Widget Styles / Brushes**, pas à un conteneur de tokens — l'ancien nom `SL_Overdrive` est annulé)
+ `MI_UI_*` pour les brushes. **Aucune couleur, aucune taille en dur dans un widget.**
Les valeurs des tokens couleur viennent **toutes** de `PALETTE.md` : `DA_UITokens` ne fait que les nommer.

| Token couleur (→ `PALETTE.md`) | Usage | | Token typo | Taille | Usage |
|---|---|---|---|---|---|
| `Color_Magenta` → `OD_Magenta_Player` | Bordures de panneau, titres, libellés, accents joueur | | `Text_Hero` | 120 px (rank 180) | `OVERDRIVE`, lettre de rank |
| `Color_Purple` → `OD_Purple_Primary` | Gains, valeurs améliorées, deltas + | | `Text_Display` | 64 px (48 en titre) | SPEED, `LEVEL COMPLETE`, `RUN FAILED` |
| `Color_Amber` → `OD_Amber_Heat` | Chaleur, grades, cible S RANK | | `Text_Large` | 32 px | Style multiplier, scores |
| `Color_Red` → `OD_Red_Danger` | Danger, dégâts, deltas −, **dernière vie** | | `Text_Body` | 22 px | Tableaux, kills, boutons |
| `Color_Gold` → `OD_Gold_Rank` | Récompense, score de run | | `Text_Label` | 16 px | Libellés, en-têtes |
| `Color_TextOnPanel` → `OD_White_Pure` | Valeurs **sur panneau foncé** | | `Text_Micro` | 12–14 px | Version, PV chiffrés |
| `Color_TextDim` → `OD_Grey_Shadow` | Texte secondaire sur panneau | | | | |
| **`Color_HUDInk` → `OD_Navy_Ink`** | **Tout élément de HUD sans panneau** (§1.1) | | | | |
| **`Color_HUDHalo` → `OD_White_Pure`** | **Halo 2 px des éléments sans panneau** | | | | |
| `Color_PanelBG` → `OD_Navy_Deep` | Fond de panneau, **alpha 0.92** | | | | |

> **`Color_Cyan` est supprimé de `DA_UITokens`** (D3) et **`Color_White` est scindé en deux** :
> `Color_TextOnPanel` (texte sur fond foncé, reste blanc) et `Color_HUDHalo` (le halo). Les confondre
> ramènerait du texte blanc dans le HUD de jeu, c'est-à-dire du texte invisible.
> **`Color_PanelBG_HUD` (noir 0.55) est supprimé** : plus aucun élément de HUD n'a de fond (§3.0a).

Layout `[À CALIBRER]` : `Border_Thin` 1 px (défaut partout) · `Border_Focus` 2 px · **`Halo_Width` 2 px** ·
`Space_XS…XL` 4/8/16/24/48 px · **`Radius` = 0** (aucun arrondi, esthétique technique et anguleuse) ·
`Anim_Instant/Fast/Normal/Slow` = 0.08/0.15/0.25/0.4 s.

**Deux polices, deux assets — pas de troisième** (D8, `SPEC_ART_DIRECTION §10.1`).

| Asset | Font | Licence | Usage |
|---|---|---|---|
| `F_Overdrive_Display` | **Chakra Petch** | **SIL OFL 1.1** — commercial libre, embarquable | Titres, lettre de rank, gros chiffres (`OVERDRIVE`, `LEVEL COMPLETE`, `SPEED`). Porte l'identité « racing HUD ». |
| `F_Overdrive_Data` | **Rajdhani** | **SIL OFL 1.1** — commercial libre | Valeurs, HUD, tableaux : **toutes les valeurs numériques** (timer, tableau de comparaison, deltas). Chiffres tabulaires : indispensable pour que les colonnes ne dansent pas. |

**`F_Overdrive_Mono` n'existe pas** — c'est `F_Overdrive_Data` qui porte les chiffres tabulaires. Toute
mention de « font mono » dans cette spec désigne `F_Overdrive_Data`.

Import dans `UI/Fonts/` avec le `OFL.txt` de chaque police à côté. **Font Cache = `Offline`** (D8) : build
reproductible, et pas de hitch de cache au premier affichage. Hinting `Auto`.
**Un Font Asset par famille** (typefaces Regular/Medium/Bold) : un widget ne référence jamais un `.ttf`
directement. Fallback si une police manque : **Saira Condensed** ou **Orbitron**, toutes deux OFL 1.1.

**Widgets réutilisables (`UI/Common/`)** : `WBP_Panel` (panneau `OD_Navy_Deep` 0.92 + bordure, `BorderColor`,
`BGOpacity`, `TitleText`, `Named Slot` — **tout panneau du jeu passe par lui**) · `WBP_Button` (les 4 états
de §8) · `WBP_StatRow` (`LIBELLÉ …… VALEUR`, utilisé par Results/**RunFailed**/Pause/LootChest) · `WBP_CompareRow` (4 colonnes +
état surligné ; le tableau §6 = **5 instances** dans un `VerticalBox`) · `WBP_Slider` / `WBP_Toggle`
(contrôles navigables clavier de §9) · `WBP_ValueBar` (segmentée ou continue selon un bool : base de
HealthBar, HeatBar, barres de style et de vitesse).
**Règle anti-duplication** : un motif visuel qui apparaît **deux fois** devient un widget commun avant la
troisième. `Named Slot` + variables `Instance Editable` / `Expose on Spawn`, jamais de copier-coller de
hiérarchie. Un widget commun ne connaît **jamais** le gameplay.

---

## 11. Résolutions & DPI

| Règle | Détail |
|---|---|
| **Anchors, jamais de position absolue** | Un élément bas-gauche a l'anchor `(0,1)`, pas `(0.5,0.5)` + gros offset. |
| **Size To Content par défaut** | Pas de taille figée qui déborde en 16:10. |
| **Aucun élément traversant** | Rien ne s'étend d'un bord à l'autre dans le HUD : en 21:9 un élément étiré devient illisible. |
| **Overlays centrés + largeur max** | Results/Loot/Settings dans un `SizeBox` `Max Desired Width = 1600 px` `[À CALIBRER]`. En 21:9 les bords restent vides — voulu, on ne remplit pas l'ultrawide. |
| **Marge de sécurité** | 3 % de la plus petite dimension. Le 16:10 est le plus contraignant en hauteur. |

**DPI Scaling Rule : `Shortest Side`.** Avec `Horizontal`, le HUD grossit en 21:9 (écran plus large, pas plus
haut) et déborde verticalement ; avec `Shortest Side`, 1920×1080 et 2560×1080 donnent la même échelle —
exactement ce qu'on veut. Courbe : `0.75` à 720 px, `1.0` à 1080, `1.33` à 1440, linéaire `[À CALIBRER]` ;
ne jamais descendre sous 0.6 (le 12 px devient illisible).
**Exception** : `WBP_Crosshair` est **exclu du DPI scaling** (`Apply DPI Scaling = false` sur son slot) — il
doit faire la même taille en pixels réels partout, sinon la visée change de ressenti selon la résolution.
**Matrice de test** : 1920×1080 (référence exacte) · 2560×1440 / 3840×2160 (scaling propre, texte net) ·
1680×1050 et 1920×1200 en 16:10 (blocs bas gauche/droite sans chevauchement, timer non tronqué) ·
2560×1080 et 3440×1440 en 21:9 (offsets fixes → OK par construction, overlays centrés) · 1280×720
(texte 12 px encore lisible ? sinon relever le plancher de la courbe DPI).

---

## 12. Checklist de validation

**HUD** — [ ] aucun `Property Binding` (vérifier chaque champ Text/Progress dans le designer) · [ ] aucun
widget avec Tick (`Tick Frequency = Never`) · [ ] un seul `Cast To BP_PlayerCharacter` dans toute l'UI, dans
`WBP_HUD::Construct` · [ ] **un seul `Cast To GI_Overdrive`**, au même endroit · [ ] zéro `Create Widget`
pendant le gameplay (hitmarker, damage, style : pools) ·
[ ] à 5000 uu/s la zone centrale 40 % × 40 % est vide hors crosshair
(D22) · [ ] aucun élément de HUD n'a de panneau ni de bordure (`SPEC_ART_DIRECTION §10.5`) · [ ] la barre de
heat est bien segmentée en 8 blocs ·
[ ] HP < 30 % perceptible **sans regarder la barre** · [ ] chaleur au-dessus de `Heat_WarningThreshold`
identifiable en < 0.3 s en périphérie, **et lue comme un coût, pas comme un blocage** (§3.3, `D58`) ·
[ ] aucun élément du HUD ne suggère que le tir est indisponible : **ni verrou, ni crosshair barré** ·
[ ] le retour d'une charge de dash se perçoit sans regarder le widget · [ ] SPEED ne papillonne pas en combat ·
[ ] pas de clignotement de palier (hystérésis) · [ ] jamais plus de 3 lignes de style simultanées.

**Contraste (DA v2, §1.1)** — le HUD est devant une ville blanche en plein jour, ces tests passent **avant**
tout jugement esthétique :
[ ] **chaque** élément de HUD testé devant les **trois** fonds : ciel bleu, mur blanc en plein soleil, ombre
portée · [ ] aucun élément de HUD n'est blanc, pâle ou sous 0.7 d'opacité · [ ] le halo blanc 2 px est
présent sur **tous** les éléments sans panneau, y compris quand ils sont colorés · [ ] le crosshair est
`OD_Navy_Ink` bordé de blanc et **n'est jamais magenta** · [ ] tirer face à un mur blanc : le crosshair reste
visible **pendant** le muzzle flash · [ ] traverser une ombre portée à 4000 uu/s : aucun élément ne
« clignote » par perte de contraste · [ ] aucune occurrence de `CYAN`, `WHITE`, `AMBER`, `RED`,
`DANGER_RED` en dur — uniquement des tokens `OD_*` (§3.0a) · [ ] tous les panneaux sont à
**`OD_Navy_Deep` 0.92**, aucun à 0.7.

**Vies (§3.11)** — [ ] `LivesRemaining` survit à `OpenLevel` (finir un niveau après une mort : le compteur
ne se recharge pas, D1) · [ ] `WBP_LivesCounter` s'initialise correctement au `Construct` du niveau suivant ·
[ ] la case perdue reste **visiblement trouée**, le `HorizontalBox` ne rétrécit pas ·
[ ] `Anim_LifeLost` se joue **après** le fade-in du respawn, pas pendant le fondu ·
[ ] à 1 vie : l'état est identifiable **sans regarder le widget** (taille + couleur + aura écran + audio) ·
[ ] à 1 vie, jouer un niveau entier **sans fatigue oculaire** (pulse ≥ 1.6 s, jamais un clignotement) ·
[ ] l'état 1 vie **persiste** au niveau suivant · [ ] `LIVES` apparaît dans les stats de `WBP_Pause`.

**Run Failed (§6.1)** — [ ] `WBP_RunFailed` s'ouvre bien à `LivesRemaining == 0` et **remplace**
`WBP_Results` (pas de coffre après) · [ ] `RUN SCORE` = somme des scores de niveau, pénalités incluses ·
[ ] `REACHED n / 8` correspond au niveau réellement atteint · [ ] la liste d'upgrades affiche les bonnes
raretés et tient sur 2 lignes à 7 upgrades (D29) · [ ] durée pilotée par `RunFailed_ScreenDuration`,
**aucune durée en dur** · [ ] skippable dès la frame 1 · [ ] retour au menu automatique · [ ] `S_RunState`
est reset **à l'entrée du menu**, pas avant l'affichage · [ ] **aucun bouton `RETRY`**, aucun rank affiché.

**Résultats / Coffre** — [ ] séquence entièrement cadencée par `Results_StepDelay` (aucune durée en dur),
skippable dès la frame 1 · [ ] `R` relance sans menu intermédiaire · [ ] un seul coupable surligné, cohérent
avec `YOU LOST S ON:` · [ ] la comparaison de vitesse porte sur `AverageSpeed`, pas `MaxSpeed` · [ ] la lettre
de rank prend la couleur de son rang (`OD_Rank_D..S`) · [ ] un run S n'affiche pas de tableau de comparaison ·
[ ] chiffres alignés (`F_Overdrive_Data`) · [ ] la preview `avant ▸ après` tient compte des upgrades actifs et
n'apparaît **pas** sur un modificateur de gameplay · [ ] les valeurs `avant ▸ après` recalculées à la main
correspondent à `07_TUNING §15` · [ ] `CAPPED` visible avant le choix · [ ] nombre de cartes conforme à
`07_TUNING §15` · [ ] aucune option de skip dans le coffre.

**Menus & settings** — [ ] focus clavier dès l'ouverture de chaque menu · [ ] jamais deux surbrillances
simultanées · [ ] chaque réglage s'applique immédiatement et survit à un redémarrage · [ ] un mode
d'affichage invalide se rétablit automatiquement · [ ] `WBP_Settings` est bien un asset unique partagé ·
[ ] `Esc` recule d'un seul cran.

**Résolutions & conventions** — [ ] testé en 1920×1080, 1920×1200, 2560×1080, 1280×720 sans chevauchement,
marges ≥ 3 % · [ ] le crosshair fait la même taille en pixels dans toutes les résolutions · [ ] tous les
widgets dans `Content/OVERDRIVE/UI/{HUD,Menus,Results,Loot,Common,Fonts}` (`WBP_RunFailed` va dans
`Results/`) · [ ] zéro warning de compilation ·
[ ] aucune couleur ni valeur de gameplay en dur.
