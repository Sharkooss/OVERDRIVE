# 2026-08-18 — Kit d'environnement « Rooftop City » — **40 assets**

> **v3.** Le kit entier a été refait sur `PALETTE.md v2`. Les 20 premiers assets ont été
> recolorés, 20 props ont été ajoutés. Les versions précédentes (palette violette, puis
> palette blanc/corail hors tokens) sont supprimées — elles n'existent plus sur disque.

## Livrables

| | |
|---|---|
| Fichier de travail | `Art_Source/OD_EnvKit_City.blend` |
| Exports | `Art_Source/EnvKit/` — **40 FBX**, un par asset, `UCX_` inclus |
| Planches | `kit_1_buildings.png` · `kit_2_machinery.png` · `kit_3_utility.png` · `kit_4_signage.png` · `kit_5_assembly.png` |
| Budget | **2932 tris pour les 40 assets** (20 à 228 par asset) |

---

## 1. Application de `PALETTE.md v2` — la décision structurante

`PALETTE.md v2 §3` pose une règle dure : *« Ces couleurs portent une information.
Les employer comme décoration est un bug de lisibilité. »* La demande initiale voulait du
rouge corail partout en décor, et des flèches rouges. **Les deux sont interdits par la palette.**

Plutôt que de retirer les accents, on leur a donné leur sens réel. Chaque couleur saturée
du kit **enseigne quelque chose** :

| Signal | Token | Où il apparaît dans le kit |
|---|---|---|
| **« je peux atterrir / courir dessus »** | `OD_Red_Traversal` `#F4453F` | arête haute de tout prop praticable, bord des toits, parapet `Roof_Edge`, main courante `Safety_Rail`, bande verticale du `Neon_Pillar` (mur wall-ridable), pilastres verticaux du `Building_Tall` |
| **« ça fait mal »** | `OD_Red_Danger` `#C81E2E` | `Warning_Barrier`, voyant de l'`Electrical_Cabinet` |
| **« va par là »** | `OD_Purple_Primary` `#7A4FC7` | **uniquement** `Rooftop_Sign` et `Arrow_Sign` |
| contraste mécanique neutre | `OD_Navy_Deep` `#2E2748` | grilles, panneaux encastrés, écran solaire, fonds de billboard |
| lampes | `OD_Sun_Warm` `#FFF6E0` | `Light_Pole`, `Street_Light_Small`, pointe de l'antenne |

### Deux écarts assumés par rapport au prompt de commande

1. **Les flèches directionnelles sont violettes, pas rouges.** `PALETTE §3` attribue
   « va par là » à `OD_Purple_Primary`. Une flèche rouge dirait « tu peux courir dessus ».
2. **Les billboards n'utilisent aucun violet.** Une publicité est du *décor sans fonction*,
   explicitement interdit à `OD_Purple_Primary` (`PALETTE §2`). Trois panneaux violets géants
   auraient dilué le signal directionnel. Ils sont en `OD_Navy_Deep` + blancs et gris —
   le navy ressort d'autant mieux que le monde est clair (`PALETTE §1` : *« un élément blanc
   lumineux disparaît »*).

**Aucun magenta, aucun ambre, aucun or dans le kit** : réservés au joueur, aux ennemis
et aux récompenses.

### Matériaux

10 matériaux, nommés 1:1 sur les tokens de `PALETTE.md` :

`M_OD_White_Structure` · `M_OD_White_Pure` · `M_OD_Grey_Shadow` · `M_OD_Grey_Deep` ·
`M_OD_Navy_Deep` · `M_OD_Purple_Primary` · `M_OD_Purple_Light` · `M_OD_Red_Traversal` ·
`M_OD_Red_Danger` · `M_OD_Sun_Warm`

**Émissifs dans Blender : tous à 1.0**, pour que les aperçus restent fidèles. Les vraies
intensités sont celles de `PALETTE §8` et sont à saisir **dans UE** :

| Matériau | `EmissiveIntensity` UE |
|---|---|
| `M_OD_Red_Traversal` | **8.0** (surface de traversée) |
| `M_OD_Purple_Primary` | **3.0** (signalétique) |
| `M_OD_Sun_Warm` | **1.0** (décor) |
| tous les autres | non émissifs |

---

## 2. Les 40 assets

### Bâtiments & toits (01-08)
| Asset | UE X × Y × Z (uu) | Tris |
|---|---|---|
| `SM_Building_Low` | 1600 × 1200 × 600 | 36 |
| `SM_Building_Medium` | 800 × 800 × 1600 | 52 |
| `SM_Building_Tall` | 400 × 400 × 3200 | 84 |
| `SM_Building_Stepped` | 1600 × 1200 × 1800 | 60 |
| `SM_Rooftop_Large` | 3200 × 3200 × 100 | 20 |
| `SM_Rooftop_Slope` | 1600 × 1600 × 500 | 26 |
| `SM_Rooftop_Slope_Large` | 3200 × 2400 × 700 | 26 |
| `SM_Roof_Edge` | 800 × 100 × 200 | 28 |

Pentes : **14°** (`Rooftop_Slope`, identique à `SM_Module_Ramp_1600x400`) et **10.6°**
(`Rooftop_Slope_Large`, pensée pour tenir la vitesse). Toits architecturaux à un seul pan.

### Ventilation & machinerie (09-14, 21-22, 26-27, 38-39)
| Asset | UE X × Y × Z (uu) | Tris |
|---|---|---|
| `SM_AC_Unit_Large` | 400 × 300 × 300 | 44 |
| `SM_AC_Unit_Small` | 200 × 200 × 200 | 20 |
| `SM_Air_Duct` | 1600 × 200 × 200 | 56 |
| `SM_Water_Tank` | 400 × 400 × 600 | 100 |
| `SM_Ventilation_Round` | 400 × 400 × 400 | 78 |
| `SM_Ventilation_Stack` | 400 × 200 × 500 | 180 |
| `SM_Generator_Box` | 600 × 400 × 300 | 44 |
| `SM_Cooling_Tower_Small` | 400 × 400 × 600 | 112 |
| `SM_AC_Pipe_Box` | 300 × 200 × 200 | 74 |
| `SM_Rooftop_Chimney` | 200 × 200 × 600 | 28 |

### Tuyauterie & utilitaire (13, 19, 23-25, 28-30, 40)
| Asset | UE X × Y × Z (uu) | Tris |
|---|---|---|
| `SM_Pipe_Section` | 800 × 200 × 400 | 112 |
| `SM_Pipe_Vent` | 200 × 200 × 500 | 84 |
| `SM_Water_Pipe` | 1600 × 200 × 200 | 116 |
| `SM_Electrical_Cabinet` | 200 × 100 × 400 | 44 |
| `SM_Utility_Box` | 200 × 100 × 300 | 44 |
| `SM_Solar_Panel` | 800 × 600 × 200 | 36 |
| `SM_Satellite_Dish` | 300 × 300 × 400 | 48 |
| `SM_Crate` | 100 × 100 × 100 | 28 |
| `SM_Cargo_Pallet` | 800 × 600 × 400 | 72 |
| `SM_Rooftop_Tech_Structure` | 600 × 400 × 400 | 36 |

### Traversée & signalétique (15-18, 20, 31-37)
| Asset | UE X × Y × Z (uu) | Tris |
|---|---|---|
| `SM_Roof_Ladder` | 100 × 300 × 800 | 132 |
| `SM_Safety_Rail` | 800 × 100 × 200 | 36 |
| `SM_Warning_Barrier` | 800 × 200 × 300 | 116 |
| `SM_Neon_Pillar` | 200 × 200 × 1600 | 44 |
| `SM_Light_Pole` | 200 × 200 × 800 | 48 |
| `SM_Street_Light_Small` | 200 × 200 × 200 | 48 |
| `SM_Rooftop_Antenna` | 200 × 200 × 1600 | 48 |
| `SM_Rooftop_Sign` | 100 × 600 × 500 | 74 |
| `SM_Arrow_Sign` | 100 × 600 × 400 | 74 |
| `SM_Billboard_Small` | 100 × 500 × 800 | 168 |
| `SM_Billboard_Large` | 100 × 2400 × 800 | 228 |
| `SM_Billboard_Rooftop` | 100 × 2400 × 1400 | 228 |

---

## 3. Règles de fabrication respectées

- **Grille 100 uu** : les 120 dimensions sont des multiples de 100. Vérifié par script.
- **Pivot** : coin UE **X− Y− Z−** pour le rectangulaire ; **bas / centre** pour les pièces
  symétriques qui tournent sur place (`Water_Tank`, `Ventilation_Round`, `Pipe_Vent`,
  `Cooling_Tower_Small`, `Satellite_Dish`, `Light_Pole`, `Rooftop_Antenna`,
  `Billboard_*`, `Rooftop_Sign`, `Arrow_Sign`). Z minimum = 0 partout.
- **Orientation** : longueur sur **+X** UE, largeur +Y, hauteur +Z.
- **Épaisseur bloquante ≥ 100 uu** sur toutes les boîtes de collision. Le `Roof_Ladder`
  a un mesh visuel fin mais un `UCX` de 100 uu — c'est le contournement anti-tunneling documenté.
- **Zéro chanfrein**, faces planes, aucune concavité, cylindres à **8 segments**.
- **Collisions `UCX_<nom>_01…`** convexes dans le même FBX, 1 à 4 par asset.
- **Transforms identité**, **UV0** valide et non chevauchante sur les 40.
- Export : `apply_scale_options=FBX_SCALE_NONE`, `bake_space_transform=False`,
  `mesh_smooth_type=FACE`, `use_triangles=True`, `use_tspace=True`,
  `axis_forward=-Z`, `axis_up=Y`.

## 4. Vérifications

- Volume signé positif sur les 40 meshes → **normales sorties partout**.
- Aller-retour export → réimport sur `Cargo_Pallet`, `Pipe_Section`, `Arrow_Sign`,
  `Neon_Pillar` : **0 polygone non triangulé**, scale (1,1,1), UV présentes,
  nombre de `UCX` correct, Z min = 0, dimensions conformes.
- Contrôle palette : les 10 matériaux utilisés sont **exactement** des tokens `PALETTE.md`.
  Vérification scriptée que le violet n'apparaît que sur `SM_Rooftop_Sign` et `SM_Arrow_Sign`.

## 5. Réglages d'import UE

Destination : `Content/OVERDRIVE/Art/Meshes/Modules/` (bâtiments, toits, `Roof_Edge`) ·
`Content/OVERDRIVE/Art/Meshes/Props/` (les 33 autres).

| Réglage | Valeur |
|---|---|
| Normal Import Method | **Import Normals** |
| Generate Lightmap UVs | ✘ |
| Auto Generate Collision | ✘ — `UCX_` fournis |
| Combine Meshes | ✘ |
| Build Nanite | ✘ |
| Import Materials / Textures | ✘ / ✘ |
| Import Uniform Scale | 1.0 |

Snap éditeur : **50 uu** / **15°**.

## 6. Reste à faire

- Créer les 10 `MI_` toon dans UE à partir des tokens, et brancher `EmissiveIntensity`
  selon le tableau du §1. Les matériaux Blender ne traversent pas le FBX : ce sont les
  **noms de slots** qui font le travail.
- Décider si `OD_Red_Traversal` sur les arêtes de props doit être **émissif 8.0** comme les
  vrais murs de wall ride, ou plus bas. À 8.0 sur chaque caisse, le budget « max 3 couleurs
  émissives visibles » risque de sauter dans une scène dense. **À tester en jeu.**
- Le kit ne contient aucune surface `OD_WallRideSurface` : le preset de collision se pose
  dans UE, pas dans le FBX. `SM_Neon_Pillar` et `SM_Building_Tall` sont les deux candidats
  (ils portent déjà la bande verticale rouge).
- Aucun asset au-delà de 3200 uu : pour plus grand, **scaler en entier** plutôt que créer un mesh.
