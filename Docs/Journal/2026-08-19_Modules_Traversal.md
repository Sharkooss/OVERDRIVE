# 2026-08-19 — Kit modulaire, lot 1 : les 7 modules de traversée

> Hors roadmap : produit en parallèle du J6, pendant que le wall ride attendait son playtest.
> Comble l'écart identifié le jour même — **six mécaniques de mouvement codées et validées,
> zéro vocabulaire de niveau pour le wall ride et le slide.**

## Livrables

| | |
|---|---|
| Fichier de travail | `Art_Source/OD_Modules_Traversal.blend` (neuf — `OD_EnvKit_City.blend` non touché) |
| Exports | `Art_Source/EnvKit_Modules/` — 7 FBX, `UCX_` inclus |
| Assets | `Content/OVERDRIVE/Art/Meshes/Modules/` — 7 `SM_Module_*` |
| Budget | **228 tris pour les 7** (12 à 48 par module ; le plafond de `SPEC_ART_DIRECTION §7.1` est 50–300 **par module**) |

Détail coté et partis pris : `SPEC_LEVELDESIGN §3`, tableau « État au 2026-08-19 ».

## Pourquoi ces 7 et pas d'autres

`SPEC_ART_DIRECTION §13` (semaine 2, lot 3) nomme les 8 modules qui portent la traversée.
Quatre d'entre eux n'avaient **aucun** équivalent, même approximatif, dans le kit de 40 props :

- **`WallRide_1600` / `_3200`** — rien dans le projet n'était ridable. Le J6 était terminé et
  n'avait de terrain que les zones E et F du sandbox.
- **`TraversalStrip_400`** — obligatoire au titre de `SPEC_LEVELDESIGN §10.1` règle 8. Sans lui,
  à 3000 uu/s, le joueur ne sent plus qu'il avance.
- **`Gate_Slide`** — la seule pièce du kit qui force le slide. Le J4 n'avait aucune expression en niveau.

Les trois autres (`Platform_400`, `Platform_800`, `Edge_800`) répondent à un manque de vocabulaire :
le kit de props est un kit de **toits**, mais il n'y avait rien **entre** les toits, alors que `P6`
impose que ≥ 70 % du dénivelé soit descendant.

`Edge_800` est en **`OD_Red_Danger`**, pas en `OD_Red_Traversal` : il borde un gouffre, il dit
« ça tombe », pas « cours dessus ». C'est le tableau d'aspect de §3. C'est aussi ce qui le distingue
du `SM_Roof_Edge` du kit de props, qui reste un parapet praticable — et qui fait **200 uu**, donc
bloque, là où `Edge_800` fait **50 uu = `MaxStepHeight`** et ne bloque jamais.

## La décision technique du lot — l'axe Y

La doc et le journal du kit de props se contredisaient sur l'orientation. Plutôt que d'arbitrer sur
papier, **import-témoin** : `TraversalStrip_400` (400 × 20 × 20, le plus asymétrique du lot) importé
seul dans `Dev/Debug` avant tout le reste.

Verdict : longueur sur `+X` **conforme à §3** — mais `min Y = −20`. Blender et UE sont Z-up tous les
deux et de **main opposée** : `Y` bascule à l'export, `X` et `Z` non. Le pivot tombait donc sur le
coin `Y+` au lieu du `Y−` imposé par §3.

Les 7 ont été **reconstruits en Y négatif** puis réexportés. Relecture après import : `min = (0,0,0)`
sur les 6 modules à pivot coin, `(−200,−500,0)` sur le portail à pivot bas/centre. Piège consigné
en `12_PIEGES §5.13`.

C'est exactement la règle n°1 du registre : *un outil qui ne renvoie pas d'erreur n'a pas forcément
fait ce que tu crois.* Ici rien n'aurait signalé le problème — dimensions justes, nom juste, mesh
juste, et un pivot du mauvais côté qui n'apparaît qu'en lisant les bornes.

## Vérifié

**Dans Blender** — volume signé positif sur les 15 objets (normales sorties) · transforms identité,
origine à (0,0,0) · UV0 présente et non chevauchante · faces planes, zéro chanfrein · ouverture du
portail contrôlée sur les sommets : `Y −400→400 = 800` de large, `Z 0→150` de haut.

**Dans UE, après import, relu asset par asset** — les 7 dimensions au uu près · pivots · 228 tris
au total, identiques au compte Blender · Nanite **off** sur les 7 · `bCustomizedCollision = true`
et `convexElems ≥ 1` (collision `UCX` bien reprise du FBX) · slots nommés par token de `PALETTE.md` ·
**presets de collision posés puis relus un par un** : `OD_WallRideSurface` ×2, `NoCollision` ×1,
`OD_LevelGeo` ×4.

## Incident sans conséquence

Le script d'import a **levé une exception** citant un `TextRenderActor` du sandbox, sans rapport avec
le script. Les 7 assets étaient pourtant tous créés. Relancer aurait produit des doublons `_1`.
Consigné en `12_PIEGES §5.14`.

## Dette ouverte

- **Aucun `MI_` n'existe encore.** Les 7 modules — comme les 40 props — portent des **noms de slots**,
  pas des matériaux. Ils sont gris dans l'éditeur tant que les 10 `MI_` de `PALETTE.md` n'existent pas.
- **L'intensité émissive du rouge n'est pas tranchée** (`SPEC_LEVELDESIGN §3.1` écart A) : 8.0 sur un
  mur de wall ride, mais 8.0 sur chaque arête de prop fait sauter le plafond de §10.1 règle 5.
- **16 modules restants**, dont 3 ont déjà un équivalent au uu près dans le kit de props.
- **`BP_LightingRig` toujours absent** — item de semaine 1 selon `SPEC_ART_DIRECTION §13`, et le
  premier `stat GPU` de référence n'a jamais été pris.
- **Destination des 8 bâtiments et toits** — dans `Props/`, alors que le journal du kit les envoyait
  dans `Modules/`. En attente d'arbitrage de Louis.

## Ce qui n'est PAS fait, volontairement

Aucun module n'a été **posé dans un niveau**. La zone K du J7 (le circuit qui enchaîne les
7 mécaniques) reste à construire — c'est du level design, pas de la production d'assets.
