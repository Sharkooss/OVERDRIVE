# 2026-08-18 — Kit d'environnement « Rooftop City » (20 assets)

> **Ce kit a été produit sur décision explicite de Louis, contre l'état de la doc au moment
> de la production.** Louis a annoncé qu'il change la DA et met la doc à jour lui-même.
> Voir §« Ce que la doc dit encore » en bas — c'est la liste de ce qui reste à réécrire.

## Livrables

| | |
|---|---|
| Fichier de travail | `Art_Source/OD_EnvKit_City.blend` |
| Exports | `Art_Source/EnvKit/` — **20 FBX**, un par asset |
| Planches | `kit_1_buildings.png`, `kit_2_props.png`, `kit_3_signage.png`, `kit_4_assembly.png` |
| Budget | **1384 tris pour tout le kit** (18 à 228 par asset) |

## Direction artistique appliquée

Ville de toits blanche, lumière du jour, style toon plat. **Pas de cyberpunk violet.**

| Rôle | Cible | Matériaux |
|---|---|---|
| Architecture (~70 %) | blanc dominant | `M_City_White_Warm` `#F4F3EE` · `M_City_White_Pure` `#FFFFFF` · `M_City_Grey_Cool` `#E6E8EE` · `M_City_Lavender_Pale` `#D9D8E8` |
| Accents (~15 %) | corail / rouge | `M_City_Coral` `#FF4056` (émissif 1.0) · `M_City_Red_Vivid` `#F52F4A` (mat) · `M_City_PinkRed` `#FF5368` (émissif 1.0) |
| Violet (~5 %) | fonds de panneaux, petits accents | `M_City_Violet_Deep` `#4D3A91` · `M_City_Violet_Med` `#684FC1` (mats) |
| Neutre (~10 %) | ombres douces | `M_City_Grey_Neutral` `#B9BCC6` |

Les base colors sont stockées en **linéaire** dans Blender (converties depuis les hex sRGB).
Le violet n'apparaît que sur `Billboard_Small` (fond d'écran), `Billboard_Large`,
`Billboard_Rooftop` et `Rooftop_Sign` — jamais comme matériau de bâtiment.

## Les 20 assets

| Asset | UE X × Y × Z (uu) | Tris | Slots | UCX |
|---|---|---|---|---|
| `SM_Building_Low` | 1600 × 1200 × 600 | 28 | 4 | 1 |
| `SM_Building_Medium` | 800 × 800 × 1600 | 52 | 5 | 1 |
| `SM_Building_Tall` | 400 × 400 × 3200 | 84 | 5 | 1 |
| `SM_Building_Stepped` | 1600 × 1200 × 1800 | 84 | 4 | 3 |
| `SM_Rooftop_Large` | 3200 × 3200 × 100 | 20 | 2 | 1 |
| `SM_Rooftop_Slope` | 1600 × 1600 × 500 | 18 | 2 | 2 |
| `SM_Rooftop_Slope_Large` | 3200 × 2400 × 700 | 18 | 2 | 2 |
| `SM_Roof_Edge` | 800 × 100 × 200 | 28 | 3 | 1 |
| `SM_AC_Unit_Large` | 400 × 300 × 300 | 44 | 4 | 1 |
| `SM_AC_Unit_Small` | 200 × 200 × 200 | 20 | 3 | 1 |
| `SM_Air_Duct` | 1600 × 200 × 200 | 48 | 2 | 1 |
| `SM_Water_Tank` | 400 × 400 × 600 | 78 | 2 | 2 |
| `SM_Utility_Box` | 200 × 100 × 300 | 44 | 4 | 1 |
| `SM_Crate` | 100 × 100 × 100 | 28 | 3 | 1 |
| `SM_Billboard_Small` | 100 × 500 × 800 | 168 | 5 | 1 |
| `SM_Billboard_Large` | 100 × 2400 × 800 | 228 | 6 | 1 |
| `SM_Billboard_Rooftop` | 100 × 2400 × 1400 | 228 | 5 | 3 |
| `SM_Rooftop_Antenna` | 200 × 200 × 1600 | 48 | 3 | 1 |
| `SM_Rooftop_Tech_Structure` | 600 × 400 × 400 | 44 | 4 | 1 |
| `SM_Rooftop_Sign` | 100 × 600 × 500 | 74 | 4 | 1 |

**Pentes** : `Rooftop_Slope` = 400 uu de montée sur 1600 → **14°** (même pente que
`SM_Module_Ramp_1600x400`). `Rooftop_Slope_Large` = 600 sur 3200 → **10.6°**, pensée pour
tenir la vitesse. Ce sont des toits architecturaux à un seul pan, pas des rampes de skate.

## Règles de fabrication respectées

Ces règles viennent du pipeline (`06_CONVENTIONS §9`, `SPEC_LEVELDESIGN §3`) et ne dépendent
pas de la DA — elles ont donc été tenues malgré le changement de direction artistique.

- **Grille 100 uu** : toutes les dimensions sont des multiples de 100. Vérifié par script.
- **Pivot** : coin UE **X− Y− Z−** pour tout ce qui est rectangulaire ; **bas / centre** pour
  les pièces symétriques qui tournent sur place (`Water_Tank`, `Billboard_*`, `Rooftop_Antenna`,
  `Rooftop_Sign`). Z minimum = 0 sur tous les assets.
- **Orientation** : longueur sur **+X** UE, largeur +Y, hauteur +Z (construit vers −Y dans Blender).
- **Épaisseur bloquante ≥ 100 uu** partout (anti-tunneling à 6000 uu/s = 100 uu/frame). Vérifié.
- **Zéro chanfrein**, faces planes, aucune concavité.
- **Collisions fournies** : `UCX_<nom>_01…` convexes dans le même FBX. 1 à 3 par asset.
- **Transforms identité** (scale 1, rotation 0) avant export. Vérifié par script.
- **UV0** valide et non chevauchante sur chaque asset (les matériaux toon sont plats, mais UE
  émet un warning sans UV).
- Export : `apply_scale_options=FBX_SCALE_NONE`, `bake_space_transform=False`,
  `mesh_smooth_type=FACE`, `use_triangles=True`, `use_tspace=True`, `axis_forward=-Z`, `axis_up=Y`.

## Vérifications effectuées

Aller-retour export → réimport FBX sur `Building_Stepped`, `Billboard_Rooftop`,
`Rooftop_Slope_Large` et `Water_Tank` : **0 polygone non triangulé**, scale (1,1,1),
UV présentes, nombre de UCX correct, Z min = 0, dimensions conformes.
Volume signé positif sur les 20 meshes → **normales sorties partout**.

## Réglages d'import UE

Dossier cible : `Content/OVERDRIVE/Art/Meshes/Modules/` (bâtiments, toits, edge) et
`Content/OVERDRIVE/Art/Meshes/Props/` (le reste).

| Réglage | Valeur |
|---|---|
| Normal Import Method | **Import Normals** |
| Generate Lightmap UVs | ✘ |
| Auto Generate Collision | ✘ — les `UCX_` sont fournis |
| Combine Meshes | ✘ |
| Build Nanite | ✘ |
| Import Materials / Textures | ✘ / ✘ — créer les `MI_` toon dans UE |
| Import Uniform Scale | 1.0 |

Snap éditeur : **50 uu** en translation, **15°** en rotation.

## Ce que la doc dit encore (à réécrire par Louis)

Au moment de la production, la doc contredit ce kit sur cinq points. Aucun n'a été modifié ici.

1. **`SPEC_LEVELDESIGN §3`** verrouille le kit d'environnement à **23 meshes nommés**, et écrit
   « Aucun autre mesh d'environnement n'est autorisé en v1 hors props de décor non collisionnables ».
   Ces 20 assets ne sont pas dans la table. Le `§12` ajoute « 23 modules max ».
2. **`SPEC_LEVELDESIGN §3`** impose **1 material slot** par module ; ce kit en utilise 2 à 6
   (color blocking). À trancher : soit la règle change, soit les accents corail passent en
   vertex color / masque.
3. **`PALETTE.md §1-§2` et `SPEC_ART_DIRECTION §3.2`** : le corail `#FF4056` et le rouge
   `#F52F4A` sont très proches de `OD_Red_Enemy` `#FF1F3D`, réservé aux ennemis avec la mention
   « Toute décoration. Aucune exception ». **Si le rouge devient la couleur d'accent de
   l'architecture, il faut déplacer la couleur ennemi** — sinon le joueur ne distingue plus un
   ennemi d'une bande de toit à 4000 uu/s. C'est le point le plus important de la mise à jour.
4. **`PALETTE.md §3`** : World 1 est violet `#2A0F45`, World 2 bleu nuit `#0B1C3D`. Un kit blanc
   ne correspond à aucune des 4 ambiances, qui vivent dans `DA_World_01…Boss02` → `MPC_Global`.
5. **`SPEC_LEVELDESIGN §7`** : aucun des 6 niveaux n'est un niveau de toits (hangar, viaduc,
   complexe industriel, structure suspendue, tunnel/canyon). `P6` impose ≥ 70 % de dénivelé
   descendant avec un apex de saut de **172 uu** — à revoir si le rooftop-hopping devient
   la mécanique de traversée.

## Reste à faire

- Import UE + création des `MI_` toon (le rendu est **Unlit**, les couleurs plates sont finales).
- Les matériaux Blender sont des Principled ; ils ne traversent pas le FBX de façon utile.
  Ce sont les **noms de slots** qui comptent : ils permettent d'assigner les bons `MI_` en un clic.
- Aucun `Rooftop_Large` de plus de 3200 uu : pour une surface plus grande, **scaler en entier**
  sur X plutôt que créer un mesh.
