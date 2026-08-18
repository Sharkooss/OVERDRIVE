# 2026-08-18 — Mesh du pistolet laser (`SM_Weapon_LaserPistol`)

> **v2 — reconstruction complète.** La v1 était trop « pistolet » : corps trop haut,
> poignée trop longue et trop reculée. Reconstruit sur des ratios mesurés sur la
> planche de référence. Voir §« Reconstruction v2 » en bas.

## Ce qui a été fait

Modélisation Blender du pistolet laser du joueur, d'après une planche de référence
fournie par Louis (pistolet sci-fi low-poly gris anthracite, bandes émissives rouges,
bouche de canon octogonale).

| | |
|---|---|
| Fichier source | `Art_Source/OD_LaserPistol.blend` |
| Export | `Art_Source/SM_Weapon_LaserPistol.fbx` |
| Destination UE | `Content/OVERDRIVE/Player/Meshes/` (cf. `06_CONVENTIONS.md` §5) |
| Triangles | **1220** (654 verts) — 100 % triangulé à l'export |
| Dimensions | **28,8 × 6,9 × 19,6 uu** (long × large × haut) |
| Pivot | creux de la main sur la poignée |
| Orientation | canon vers **−Y** Blender → **+X** dans UE, up **+Z** |
| UV | 1 seul set (`UVMap`), îlots non chevauchants, bornés 0,01–0,99 |
| Matériaux | slot 0 `M_LaserPistol_Body`, slot 1 `M_LaserPistol_Emissive` |
| Socket | `SOCKET_Muzzle` → socket UE **`Muzzle`** à (0, −24,4, 6,2) uu, +X dans l'axe du tir |

Construction : volumes prismatiques extrudés le long de X à partir de silhouettes YZ,
chanfreins 1 segment (aspect facetté hard-surface), bandes émissives en incrustations
séparées plutôt qu'en inset — même rendu, script plus robuste, coût identique.

## Décisions prises

1. **Les sources d'art vivent dans `Art_Source/` à la racine du projet**, pas dans
   `Content/`. Le `CLAUDE.md` §4 disait « Export FBX vers `Content/OVERDRIVE/Art/Meshes/` » :
   ça mettrait des `.fbx`/`.blend` bruts dans le Content Browser, où UE ne les utilise pas
   et où ils partiraient au cook. Décision reportée dans `06_CONVENTIONS.md` §10.
2. **Pivot sur la poignée** plutôt que sur l'origine d'un rig de bras. Choix validé par
   Louis : OVERDRIVE n'a pas encore de bras FP, un pivot poignée est portable.
3. **Pas de textures bitmap** — 2 matériaux à plat. Choix validé par Louis. Les UV sont
   quand même dépliées proprement, donc un bake AO/color reste possible plus tard sans
   retoucher le mesh.
4. **Pas de collision** exportée (UCX). Une arme FP n'en a pas besoin.

## Incident à noter

Blender avait ouvert `L:\Unreal Engine\Projects\RunLuck 5.8\ArtSource\RunLuck_Arms.blend`
(**un autre projet**), pas un fichier OVERDRIVE. Deux conséquences :

- Un script de ma part a récupéré les empties existants `SOCKET_Muzzle` et
  `SOCKET_GripAttach` (qui appartenaient au shotgun RunLuck) au lieu d'en créer de
  nouveaux, et les a reparentés/déplacés. Restauré ensuite à l'identique
  (`SOCKET_Muzzle` → parent `SM_Shotgun_BarrelAssembly`, local (0, −0,492, 0,190) ;
  `SOCKET_GripAttach` → parent `EMPTY_Shotgun_Root`, local (0, 0,121, 0,126)).
  **Le fichier `RunLuck_Arms.blend` sur disque n'a jamais été écrit** (mtime vérifié
  inchangé avant/après). Le travail a été sauvegardé via *Save As* dans
  `OVERDRIVE/Art_Source/OD_LaserPistol.blend`, puis les collections `ARMS` et `SHOTGUN`
  ont été supprimées **de la copie OVERDRIVE uniquement**.
- Le parent d'origine de `SOCKET_Muzzle` a été *déduit* du pattern du fichier
  (tout ce qui suit le canon est parenté à `SM_Shotgun_BarrelAssembly`), pas lu.
  Si RunLuck est repris un jour, vérifier ce point.

**À faire avant toute prochaine session Blender sur OVERDRIVE :** ouvrir
`Art_Source/OD_LaserPistol.blend`, pas le fichier RunLuck.

## Vérifications effectuées

- Aller-retour export → réimport FBX : 1220 tris, **0 polygone non triangulé**,
  scale (1,1,1), rotation nulle, `UVMap` présente, 2 slots matériaux dans l'ordre,
  `SOCKET_Muzzle` correctement parenté à (0, −0,244, 0,062) m.
- Aperçus : `Art_Source/prev_side.png`, `prev_persp.png`, `prev_top.png`, `uv_layout.png`.

## Reconstruction v2

La v1 ne correspondait pas à la silhouette de la référence. Ratios mesurés sur la
vue de côté de la planche, puis modèle refait :

| Ratio | Référence | v1 | v2 |
|---|---|---|---|
| Longueur / hauteur du corps | 3,95 | 3,2 | **3,95** |
| Longueur / hauteur totale | 2,03 | 1,47 | **2,02** |
| Surplomb arrière derrière la poignée | ~20 % | 3 % | **16 %** |

Corrections apportées :
- Corps allongé à 30 uu et aminci (hauteur de la caisse 7,6 uu au lieu de 9,0).
- Poignée **avancée** et raccourcie (chute de 6,7 uu au lieu de 10,6) — c'était l'écart
  de silhouette le plus visible : la référence garde un long bloc arrière derrière la main.
- Émetteur octogonal évasé (Ø 6,0 uu contre 5,0 pour la section avant), relié au corps
  par un collier, avec une vraie cavité : **housing sombre → alésage sombre en retrait →
  noyau rouge plus petit, enfoncé de 11 mm**.
- Hausse arrière et rail supprimés (la consigne interdit les organes de visée) ;
  il ne reste qu'un rail, un petit bloc, un panneau sombre encastré et un logement avant.

### Panneaux rouges — vraie géométrie en retrait
Les bandes ne sont **pas** des polygones rouges posés en surface. Chaque plaque
latérale est un bandeau en relief dans lequel des poches sont **découpées au boolean
(solveur EXACT)** de part en part ; le panneau émissif est ensuite posé au fond de la
poche, 1 mm sous la surface du bandeau. Lecture finale : bandeau sombre → paroi de
poche sombre → panneau rouge en creux.

### Palette (4 sections matériaux)
| Slot | Matériau | sRGB | Rough / Metal |
|---|---|---|---|
| 0 | `M_LaserPistol_Body` | `#24282E` | 0,65 / 0,55 |
| 1 | `M_LaserPistol_Panel` | `#1A1D22` | 0,72 / 0,45 |
| 2 | `M_LaserPistol_Accent` | `#3A3F47` | 0,55 / 0,65 |
| 3 | `M_LaserPistol_Emissive` | `#FF1025` | émission 12 |

Répartition : Body 424 tris · Panel 456 · Accent 176 · **Emissive 108**.
Les valeurs de base color sont stockées en **linéaire** dans Blender (converties depuis
les hex sRGB demandés).

### Chiffres v2
**1164 tris / 614 verts** · **30,0 × 6,1 × 14,9 uu** · pivot creux de la main ·
`SOCKET_Muzzle` à (0 ; −22,5 ; 5,0) uu.

Aller-retour FBX revérifié : 1164 tris, 0 polygone non triangulé, scale 1.0,
4 slots dans l'ordre, UV 0,01–0,99, socket parenté.

### Note rendu
Le view transform par défaut de Blender (**AgX**) désature fortement : le rouge #FF1025
y sort saumon et le corps anthracite y sort gris moyen. Les aperçus sont rendus en
**Standard, exposition −1,3**. Ça n'affecte que les PNG, pas l'asset.
Le nœud Glare du compositeur a changé d'API en Blender 5.2 (plus de
`scene.node_tree`, plus de `CompositorNodeComposite`) — pas de bloom configuré,
et ce n'est pas nécessaire : l'émissif est visiblement rouge sans bloom, ce qui était
la contrainte posée.

## Reste à faire

- Import dans UE + création des `MI_` (voir checklist dans la réponse d'agent).
- Le matériau émissif doit être **réécrit dans UE** : l'intensité d'émission du
  Principled BSDF de Blender ne traverse pas le FBX de façon fiable.
- Pas de bras FP dans OVERDRIVE pour l'instant → la position en main reste à caler.
