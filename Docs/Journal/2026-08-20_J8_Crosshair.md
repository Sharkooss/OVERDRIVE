# Journal — 2026-08-20 — J8 (hors roadmap) — Réticule

**Temps effectif** : ~1 h agent
**Objectif du jour (roadmap)** : hors planning — `WBP_Crosshair` était prévu **J19**.
Demande directe de Louis : *« rajoute-moi un crosshair simple, assez fin, qui se voit sur n'importe
quelle surface. Au centre un point rouge néon et des traits blancs autour. Il faut évidemment que ça
ne se fonde pas dans le décor, donc adapte les couleurs en fonction de sur quoi c'est projeté. »*

---

## Fait

- **`Content/OVERDRIVE/UI/HUD/WBP_Crosshair`** — widget **autonome**, créé entièrement par outil.
  `CanvasPanel` racine + **10 `Image`** : 5 pour la couche sombre, 5 pour la couche claire.
  4 traits (haut / bas / gauche / droite) + 1 point central. Pas de cercle, pas de contour de visée.
- **8 variables `Instance Editable`** (`Feedback|Crosshair`) : longueur, épaisseur, gap, rayon du point,
  épaisseur du liseré, et les 3 couleurs. **Zéro valeur en dur dans le graphe** (R3).
- **6 variables `Computed_*`** (`Feedback|Crosshair|Computed`) recalculées par `ComputeCrosshairMetrics()`.
- 3 fonctions : `ComputeCrosshairMetrics`, `ApplyCrosshairElement`, `ApplyCrosshairLayout`.
  Appelées sur **`Event PreConstruct`** — le designer suit donc toute modification de tuning,
  sans `Event Tick` ni Property Binding (`SPEC_UI_HUD §3.0`).
- **`PC_Overdrive::BeginPlay`** : `Create Widget` → `Set CrosshairWidget` → `Add to Viewport (ZOrder 10)`.
- Doc : `SPEC_UI_HUD §3.1` réécrit (7 sous-sections), `04_ROADMAP` J19 annoté,
  `12_PIEGES` +4 entrées (**2.35**, 5.35, 5.36, 5.37).

## Pas fait / reporté

- **Les états du réticule (tir, heat, overheat)** — `SPEC_UI_HUD §3.1.7`. Ils demandent les dispatchers
  de `BPC_Heat` et de `BP_LaserWeapon`, qui sont en cours chez un autre agent aujourd'hui. Ils se
  câbleront au **J19** et ne feront que modifier les variables de tuning puis rappeler
  `ApplyCrosshairLayout` — l'architecture est déjà prête pour ça.
- **`WBP_HUD`** : pas créé, c'est le J19. En attendant c'est le PC qui affiche le réticule.
- **Aucun rendu vu.** PIE était interdit ce tour (un autre agent travaillait dessus). Voir plus bas.

---

## La demande de Louis, honnêtement : je n'ai pas fait ce qu'il a demandé, j'ai fait ce qu'il veut

Louis a demandé que le réticule **« adapte les couleurs en fonction de sur quoi c'est projeté »**.

**Ce n'est pas faisable en UMG, et je ne veux pas laisser croire que ça l'est.** Un widget est
composité **après** la scène : il n'a aucun accès au framebuffer qu'il recouvre, il ne peut donc rien
« lire » du décor. La vraie adaptation dynamique demanderait un **post-process en mode Difference /
inversion** — ce qui n'était pas dans le scope du jour, et qui casserait le cel-shading (D2).

**Le résultat demandé est obtenu autrement — par la forme, pas par la couleur.** C'est la solution de
tous les FPS shippés : le réticule **porte son propre contraste**. Chaque élément est dessiné deux fois,
une forme sombre 1 px plus grande sur chaque bord derrière, la forme claire par-dessus.

| Fond | Ce qui tient la lecture |
|---|---|
| Mur blanc en plein soleil | le liseré `OD_Navy_Ink` |
| Ombre portée | les traits blancs et le point rouge |
| Ciel `OD_Sky_Blue` | les deux |

**Aucun fond ne peut faire disparaître les deux couches à la fois.** C'est exactement ce que
`PALETTE.md §7` prescrit déjà pour un élément de HUD sans panneau (« tracé foncé + halo blanc »),
appliqué au réticule — sauf que le rapport est inversé : ici c'est le trait qui est clair et le halo
qui est sombre, parce que Louis veut des traits blancs.

**Ce que ça ne fait pas** : le réticule ne devient pas cyan devant un mur rouge. Il reste identique
partout, et il reste lisible partout. Si Louis veut réellement l'inversion dynamique, c'est un
post-process dédié et ça se décide séparément — ça ne se rattrape pas dans le widget.

---

## La tension de palette — je ne la tranche pas

**En une phrase** : `PALETTE.md §7` dit que le crosshair est `OD_Navy_Ink` bordé de blanc, et
`11_ARBITRAGES D3` réserve le rouge au **danger** et aux **surfaces de traversée** — or Louis demande
un **point rouge**, donc j'ai fait le point rouge et je laisse Louis arbitrer.

**Ce que j'ai choisi pour limiter les dégâts** : le rouge du point est `#FF1025`, **celui de l'émissif
de l'arme** (`SPEC_ART_DIRECTION §6.4.1` — divergence déjà ouverte, déjà voulue par Louis aujourd'hui),
et **pas** `OD_Red_Danger` ni `OD_Red_Traversal`. Résultat : aucune couleur réservée n'est détournée,
et le réticule est de la couleur du canon qu'il prolonge.

**L'alternative, si Louis veut garder le rouge strictement exclusif au danger** : mettre
`Crosshair_DotColor` à `OD_White_Pure` ou à `OD_Navy_Ink`. **Une seule variable à changer**, aucun
autre impact, aucun asset à retoucher. C'est réversible en 5 secondes dans le Content Browser.

---

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| Le contraste du réticule vient du **doublage concentrique** (forme), pas d'une adaptation dynamique impossible en UMG | `SPEC_UI_HUD §3.1.1` |
| Écart assumé avec `SPEC_UI_HUD §1.1` : le doublage y est interdit **pour les textes** (4 draw calls, casse à l'animation) ; ici il est concentrique, coûte +1 draw call par élément et ne casse pas | `SPEC_UI_HUD §3.1.1` |
| Point central rouge `#FF1025` (rouge de l'arme) plutôt qu'`OD_Red_Danger` / `OD_Red_Traversal` | `SPEC_UI_HUD §3.1.4` — **tension signalée, à trancher par Louis** |
| Le réticule est porté par **`PC_Overdrive`** et non par `BP_PlayerCharacter` : il survit au respawn du pawn (raisonnement de `SPEC_COMBAT §5.4` pour `BPC_HitStop`) | `SPEC_UI_HUD §3.1.6`, `04_ROADMAP` J19 |
| `Event PreConstruct` plutôt que `Construct` : le layout se recalcule aussi **dans le designer** | `SPEC_UI_HUD §3.1.5` |
| Les valeurs de géométrie restent dans `SPEC_UI_HUD` et non dans `07_TUNING` — ce sont des px d'UI, pas du gameplay (règle posée en tête de `SPEC_UI_HUD`) | — |

## Valeurs modifiées

> Valeurs d'UI : elles vivent dans `SPEC_UI_HUD §3.1.2`, pas dans `07_TUNING` (cf. en-tête de la spec).

| Clé | Ancien | Nouveau | Raison |
|---|---|---|---|
| `Crosshair_Gap` | 5 px | **8 px** | À 5, le liseré du point (3 px de rayon) et celui des traits (qui empiète de 1 px vers le centre) ne laissaient plus qu'**1 px de vide** : le réticule se serait lu comme une croix pleine. À 8, le vide fait 4 px. |
| `Crosshair_DotRadius` | (« point 2 px ») | **2.0 → point de 4 px** | Un point de 2 px n'existe pas à 4000 uu/s, et Louis demande explicitement qu'on le voie. |
| `Crosshair_OutlineWidth` | *(n'existait pas)* | **1.0 px** | Nouvelle clé : c'est elle qui porte tout le contraste. |
| `Crosshair_LineLength` / `_LineThickness` | 6 / 2 | **inchangées** | Les valeurs de la spec tenaient. |

## Ressenti de playtest

**Aucun — et c'est la limite honnête de ce livrable.** PIE m'était interdit ce tour (un autre agent
travaillait sur `BP_LaserWeapon` / `BP_TargetDummy`), donc **je n'ai vu aucun pixel**. J'ai vérifié la
géométrie, les couleurs, la visibilité, la topologie des graphes et la compilation — pas le rendu.

Ce que je ne peux pas garantir et qui se voit en 10 secondes de jeu :

1. **Que le réticule apparaisse.** Les `Image` n'ont **aucune texture** : je compte sur Slate pour
   rendre un quad plein quand `resourceObject = None`. C'est le comportement standard d'un widget
   `Image` fraîchement posé, mais je ne l'ai pas **observé** sur ce projet. Si rien ne s'affiche,
   c'est ça — et le correctif est de poser une texture blanche 4×4 ou `drawAs = RoundedBox`.
2. **Que la taille soit la bonne.** 30 × 30 px sur un écran 1080p, c'est **petit**. C'est voulu
   (« assez fin »), mais c'est le premier réglage à toucher.
3. **Que le liseré de 1 px suffise** devant un mur blanc en plein soleil. 1 px est le minimum
   théorique ; 2 px est peut-être le bon.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| `write_graph_dsl` sur `PC_Overdrive:EventGraph` a **détruit 2 nœuds que je n'avais pas écrits** (deux `PrintString` orphelins de diagnostic d'input). 2 → 7 au lieu de 2 → 9. Aucune erreur. Sans conséquence ici (nœuds morts), **mais c'est la destruction 3.2 à un event d'input près** | 💀 | Consigné en `12_PIEGES 2.35`. Les 2 nœuds détruits étaient du debug mort, rien à restaurer. |
| Mon propre script de création a planté sur une erreur de **formatage Python** (`slot` valant la chaîne `"None"`), après que l'appel MCP eut réussi. Relancer aveuglément aurait créé un doublon | 🟠 | Relecture de l'arbre avant de retenter → `CrosshairRoot` existait déjà. Rappel de la règle n°1 : l'échec du script n'est pas l'échec de l'écriture. |
| `Appearance\|SetColorandOpacity` listé **3 fois** par `find_node_types`, avec un `self` de type `UserWidget` | 🔴 | Évité avant écriture par le contrôle de 2.21 (type du pin `self`). Consigné en `12_PIEGES 5.36`. |

---

## Checklist de test manuel pour Louis (R8)

**Ouvrir `L_Sandbox_Movement`, jouer, regarder le centre de l'écran.**

| # | À vérifier | Attendu | Si ça rate |
|---|---|---|---|
| 1 | Le réticule est là | 4 traits blancs + 1 point rouge au centre exact | Rien ne s'affiche → les `Image` sans texture ne rendent pas ; me le dire, correctif à 1 appel |
| 2 | Il est **centré** | Le point rouge est pile au milieu, même en 21:9 / fenêtré | — |
| 3 | Il est lisible **devant un mur blanc en plein soleil** | Le liseré sombre détache chaque trait | Monter `Crosshair_OutlineWidth` de 1 à 2 |
| 4 | Il est lisible **dans une ombre portée** | Les traits blancs ressortent | — |
| 5 | Il est lisible **devant le ciel** | — | — |
| 6 | **À 4000 uu/s**, il reste un point de fixation stable | Il ne bouge pas, ne grossit pas, ne clignote pas | C'est voulu : aucun crosshair dynamique (interdit §3.1) |
| 7 | Il ne mange **aucun clic** | Le tir part normalement | `Visibility` mal posée — mais elle est relue `HitTestInvisible` sur les 11 widgets |
| 8 | Le point rouge te plaît **ou** tu veux le rouge exclusif au danger | choix de couleur | Cf. « tension de palette » ci-dessus |

**Les 5 curseurs à tourner** — ouvrir `WBP_Crosshair`, panneau *Details*, catégorie `Feedback|Crosshair`.
Le designer se met à jour tout seul (`PreConstruct`), **pas besoin de lancer le jeu pour juger** :

| Si tu trouves que… | Tourne |
|---|---|
| c'est trop petit / trop gros | `Crosshair_LineLength` (6) et `Crosshair_DotRadius` (2) |
| les traits sont trop épais / trop fins | `Crosshair_LineThickness` (2) |
| le vide central est trop serré / trop large | `Crosshair_Gap` (8) |
| ça se noie sur les murs blancs | `Crosshair_OutlineWidth` (1 → 2) |
| le rouge est trop agressif / pas assez | `Crosshair_DotColor` — **coller le HEX dans l'onglet *Hex sRGB* du color picker**, jamais taper les composantes à la main (`PALETTE.md §8`, `12_PIEGES 5.31`) |

## Demain

- Câbler les états du réticule quand `BPC_Heat` et `BP_LaserWeapon` exposeront leurs dispatchers (J19).
- Décider de la couleur du point (Louis).

---

## Vérifications de fin de journée

- [x] `WBP_Crosshair` et `PC_Overdrive` compilent, **zéro warning** (`warnings_as_errors = true` sur les deux)
- [x] Les 10 slots relus **après compilation** avec `get_properties` (pas avec l'outil qui a écrit) : position, taille, ZOrder, couleur, visibilité — 10/10 conformes
- [x] Topologie des 4 graphes auditée : **un seul nœud racine** par graphe (critère topologique de `12_PIEGES 2.31`), longueurs de chaîne exec = attendu, aucun nœud inséré en douce (2.21)
- [x] `PC_Overdrive:EventGraph` : **2 nœuds avant → 7 après**, chaîne `BeginPlay → CreateWidget → SetCrosshairWidget → AddToViewport`, **un seul** `CreateWidget`
- [x] `save_assets` sur les deux assets, présence confirmée sur disque via `git status`
- [ ] **3 minutes de jeu réel** — PIE interdit ce tour, à faire par Louis
- [x] Roadmap annotée (J19)
- [x] Tuning à jour (`SPEC_UI_HUD §3.1.2`)
- [ ] **Commit : NON fait**, conformément à R10 — j'attends que Louis ait vu le réticule
