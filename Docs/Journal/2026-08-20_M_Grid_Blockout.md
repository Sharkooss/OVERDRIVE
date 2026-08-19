# 2026-08-20 — `M_Grid_Blockout` : le matériau de grid du sandbox

> Hors roadmap, demandé par Louis avant d'attaquer le J8 : un matériau de grid « genre laboratoire »
> pour blockouter une zone de test contenant toutes les mécaniques.
> **Comble un trou ouvert au J4** : la suppression de `Content/LevelPrototyping/` (décision D1) a
> emporté les seuls matériaux de grid du projet. Depuis, tout le blockout est en gris uni.

## Livrables

| Asset | Rôle |
|---|---|
| `Content/OVERDRIVE/Dev/Debug/M_Grid_Blockout` | master, 22 expressions |
| `…/MI_Grid_Floor` | gris neutre froid, lignes bleu-gris — sol et murs |
| `…/MI_Grid_WallRide` | teinté rouge, lignes plus épaisses — **surfaces de wall ride** |

`Dev/Debug/` est **jetable et jamais référencé par du contenu final** (`06_CONVENTIONS §8`) : c'est
un outil de blockout, pas de l'art de production. La DA reste `SPEC_ART_DIRECTION`.

## La décision technique : grid en espace MONDE, pas en UV

**C'est tout l'enjeu du matériau.** Les volumes de blockout sont des cubes **mis à l'échelle de
façon non uniforme** — le deck de la zone K est en `27.16 × 9 × 4`. Un grid basé sur les UV serait
étiré dans un rapport de 1 à 7 sur le même objet, et illisible pour juger une distance.

Le grid est donc calculé sur `AbsoluteWorldPosition` : **les carreaux font 100 uu partout**, quelle
que soit l'échelle du mesh — et 100 uu, c'est exactement la grille du projet (`06_CONVENTIONS §6`).
On peut donc compter les carreaux pour mesurer une portée de saut ou un écartement de couloir.

### Suppression de l'axe parallèle à la surface

Un grid monde naïf a un défaut : sur un sol horizontal, les plans `z = n × 100` sont **parallèles à
la surface** — au ras d'un multiple de 100, le sol entier s'allume d'un coup.

Parade, sans triplanar complet : chaque masque d'axe est pondéré par `1 − |normale|`.

```
masque = saturate( Σ  lineMask(WP.axe) × (1 − |N.axe|) )
```

Sol (`N = 0,0,1`) → les plans X et Y dessinent, les plans Z sont annulés. Mur (`N = 1,0,0`) → l'axe X
est annulé, Y et Z dessinent. Aucun cas particulier, 3 nœuds de plus qu'un grid plat.

## Paramètres exposés

| Groupe | Paramètre | Défaut |
|---|---|---|
| Grid | `GridSize` | **100** (la grille du projet) |
| Grid | `LineThickness` | 4 uu |
| Surface | `BaseColor` / `LineColor` / `Roughness` | gris froid / bleu-gris / 0.85 |

## Vérifié

- Compilation du shader **OK**, `MP_BaseColor` et `MP_Roughness` branchées, 22 expressions.
- Les 2 instances relues paramètre par paramètre après écriture.
- **`WorldPosition` est bien en `WPT_Default` = position absolue.** Point critique : en
  *camera-relative*, le grid **dériverait avec la caméra** sans qu'aucune erreur ne le signale.
- **Rendu contrôlé** sur la vignette de `MI_Grid_Floor` : les plans de grille coupent bien la sphère.

## ⚠️ Le piège à ne pas confondre

`MI_Grid_WallRide` **ne rend rien ridable**. Il ne fait que *colorer*. Une surface n'est accrochable
que si son **object type** est `WallRideSurface` (`ECC_GameTraceChannel2`) — et
`12_PIEGES §5.15` a montré le même jour que **ce preset ne se pose pas par outil sur un composant** :
il doit vivre sur l'**asset StaticMesh**, sinon le mur est ridable en apparence et inerte en jeu.

Donc : pour un mur ridable, utiliser `SM_Module_WallRide_1600/3200` du kit modulaire, et se servir de
`MI_Grid_WallRide` uniquement pour que ça se **voie**. Un cube de blockout teinté en rouge n'est pas
un mur de wall ride.
