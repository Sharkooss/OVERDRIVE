# 00 — INDEX

> **Point d'entrée de la documentation OVERDRIVE.**
> Si tu es un agent : lis `CLAUDE.md` à la racine d'abord, puis reviens ici.

---

## Par où commencer

| Tu veux… | Lis, dans cet ordre |
|---|---|
| Comprendre le projet | `01_VISION.md` → `02_GDD.md` |
| Coder une feature | `CLAUDE.md` → la `Specs/SPEC_*.md` concernée → `07_TUNING.md` |
| Créer un asset | `06_CONVENTIONS.md` → `Specs/SPEC_ART_DIRECTION.md` |
| Construire un niveau | `Specs/SPEC_LEVELDESIGN.md` → `Specs/SPEC_MOVEMENT.md §2` |
| Régler une valeur | `07_TUNING.md` uniquement |
| Savoir quoi faire aujourd'hui | `04_ROADMAP.md` |
| Savoir si une idée entre | `03_SCOPE_LOCK.md` |
| Trancher une contradiction | `11_ARBITRAGES.md` (elle y est peut-être déjà) |
| Savoir si c'est fini | `10_DEFINITION_OF_DONE.md` |

---

## Documents fondateurs

| # | Fichier | Contenu | Autorité |
|---|---|---|---|
| 00 | `00_INDEX.md` | Ce fichier | — |
| 01 | [`01_VISION.md`](01_VISION.md) | Pitch, 5 piliers, contrat joueur, ton | **Vision** |
| 02 | [`02_GDD.md`](02_GDD.md) | GDD d'origine, 85 sections. *Archive d'intention* | Historique |
| 03 | [`03_SCOPE_LOCK.md`](03_SCOPE_LOCK.md) | Dans / hors scope, backlog, ordre de sacrifice | **Scope** |
| 04 | [`04_ROADMAP.md`](04_ROADMAP.md) | 28 jours, gates hebdo, risques | **Planning** |
| 05 | [`05_ARCHITECTURE.md`](05_ARCHITECTURE.md) | Arbre BP, composants, communication, cycle de run | **Architecture** |
| 06 | [`06_CONVENTIONS.md`](06_CONVENTIONS.md) | Nommage, dossiers, hygiène BP, collision, sources d'art | **Conventions** |
| 07 | [`07_TUNING.md`](07_TUNING.md) | **Toutes** les valeurs numériques | **Valeurs** |
| 08 | [`08_DATA_SCHEMAS.md`](08_DATA_SCHEMAS.md) | Enums, Structs, DataAssets, DataTables, Curves, MPC | **Données** |
| 09 | [`09_INPUT.md`](09_INPUT.md) | Enhanced Input, mapping, buffering | **Input** |
| 10 | [`10_DEFINITION_OF_DONE.md`](10_DEFINITION_OF_DONE.md) | DoD, 8 tests de validation, gates | **Qualité** |
| 11 | [`11_ARBITRAGES.md`](11_ARBITRAGES.md) | **33 décisions tranchées** là où deux docs se contredisaient | **Arbitrages** |

## Specs système

| Fichier | Couvre |
|---|---|
| [`Specs/SPEC_MOVEMENT.md`](Specs/SPEC_MOVEMENT.md) | Machine à états, sprint, slide, jump, bunny hop, air strafe, dash, wall ride, collisions, sandbox |
| [`Specs/SPEC_COMBAT.md`](Specs/SPEC_COMBAT.md) | Laser, trace, heat, overheat, headshots, hit-stop, melee, knockback, wall slam, `BPI_Damageable` |
| [`Specs/SPEC_ENEMIES.md`](Specs/SPEC_ENEMIES.md) | `BP_EnemyBase`, activation, Grunt, Shooter, Tank, projectile, mort, placement |
| [`Specs/SPEC_BOSS.md`](Specs/SPEC_BOSS.md) | `BP_BossBase`, phases, Boss 01 « OVERSEER », Boss 02 « REDLINE », scoring boss |
| [`Specs/SPEC_SCORE_RANK.md`](Specs/SPEC_SCORE_RANK.md) | Formule de score, style multiplier, collecte, rank, écran de résultats, anti-exploit |
| [`Specs/SPEC_LOOT_UPGRADES.md`](Specs/SPEC_LOOT_UPGRADES.md) | Coffres, tirage, catalogue d'upgrades, application, garde-fous |
| [`Specs/SPEC_LEVELDESIGN.md`](Specs/SPEC_LEVELDESIGN.md) | **Métriques joueur**, kit modulaire, grammaire des espaces, lisibilité, courbe des 6 niveaux |
| [`Specs/SPEC_ART_DIRECTION.md`](Specs/SPEC_ART_DIRECTION.md) | Toon shader, outlines, matériaux, budgets, pipeline Blender→UE, ambiances |
| [`Specs/SPEC_VFX.md`](Specs/SPEC_VFX.md) | Catalogue Niagara, post-process, hit-stop, shake, budget perf |
| [`Specs/SPEC_AUDIO.md`](Specs/SPEC_AUDIO.md) | Catalogue SFX, mix, MetaSounds, sensation de vitesse, musique, sources |
| [`Specs/SPEC_UI_HUD.md`](Specs/SPEC_UI_HUD.md) | HUD, widgets, écran de résultats, coffre, menus, settings, design system |
| [`Specs/SPEC_CAMERA_JUICE.md`](Specs/SPEC_CAMERA_JUICE.md) | FOV dynamique, tilt, shakes, hit-stop, effets de vitesse, transitions, confort |

## Direction artistique

| Fichier | Contenu |
|---|---|
| [`ArtDirection/PALETTE.md`](ArtDirection/PALETTE.md) | Palette HEX, tokens, couleurs réservées gameplay, ambiances, raretés |
| `ArtDirection/KEYART_REF_02.png` | ⚠️ **À déposer** — key art de référence (cf. `ArtDirection/README.md`) |

## Journal

`Journal/TEMPLATE.md` — modèle d'entrée quotidienne. Une entrée par jour de travail.

---

## Hiérarchie d'autorité

En cas de contradiction entre deux documents :

```
1. CLAUDE.md            (règles agents)
2. 11_ARBITRAGES.md     (les décisions déjà tranchées — ne se rouvrent pas)
3. 03_SCOPE_LOCK.md     (ce qui existe)
4. 07_TUNING.md         (les valeurs)
5. 06_CONVENTIONS.md    (les noms)
6. 05_ARCHITECTURE.md   (la structure)
7. 08_DATA_SCHEMAS.md   (les données)
8. Specs/SPEC_*.md      (le comportement détaillé)
9. 02_GDD.md            (l'intention d'origine — ne prime jamais sur les autres)
```

**Exception** : sur les couleurs, `ArtDirection/PALETTE.md` prime sur tout, y compris les specs.
Sur l'apparence visuelle, `Specs/SPEC_ART_DIRECTION.md` prime sur `Specs/SPEC_UI_HUD.md`.

**Une contradiction est un bug de documentation.** Elle se signale et se corrige, elle ne se contourne pas.

---

## État de la documentation

| | |
|---|---|
| Version | **2.0** — refonte DA + système de vies |
| Date | 2026-08-18 |
| Statut | Préproduction terminée, prête pour la Semaine 1 |
| Valeurs `[VALIDÉ]` | **0** — aucun playtest encore |
| Valeurs `[À CALIBRER]` | Toutes |

### Ce qui a changé en v2 (2026-08-18)

| Changement | Impact |
|---|---|
| **Nouvelle DA** : ville blanche en plein jour au lieu du néon nocturne | `PALETTE.md` refaite, `SPEC_ART_DIRECTION` réécrit, tous les tokens de couleur remappés |
| **Rendu éclairé** : Lumen et VSM restent actifs (`D2` inversé) | Cel-shading par posterisation. Nouveau risque perf n°1 |
| **Le cyan n'existe plus** | Rouge = traversée · violet = direction · magenta = joueur · orange = ennemi |
| **Fond clair** : l'info de gameplay doit être foncée ou saturée | Inverse de la v1. Impacte VFX, UI, ennemis, projectiles |
| **Système de 3 vies** (`D1`, `D31`) | Entre au scope. `S_RunState.LivesRemaining`, `WBP_LivesCounter`, `WBP_RunFailed` |

### Points ouverts en attente d'arbitrage de Louis

| Sujet | Où | Statut |
|---|---|---|
| **Le restart volontaire (`R`) coûte-t-il une vie ?** | `SPEC_LEVELDESIGN §9.4` | 🔴 **Bloquant pour le design** — sans réponse, on peut contourner le système de vies |
| **Charte visuelle des ennemis** | `SPEC_ART_DIRECTION §9` | Proposée (silhouette navy + visière orange), la key art n'en montre aucun |
| `Run_MaxLives = 3` sur 8 niveaux | `07_TUNING §18` | Volontairement sévère. Leviers de repli documentés |
| Affichage `SPEED` vs km/h au HUD | `07_TUNING §1`, `SPEC_UI_HUD §4` | Recommandation : `SPEED`. À confirmer |
| Orange ennemi vs rouge traversée | `PALETTE.md §3` | Repli turquoise `#00D9C0` documenté, à valider en playtest |
| Melee propulsif | `03_SCOPE_LOCK §3` | Expérimental, hors MVP |
| Key art de référence | `ArtDirection/` | **`KEYART_REF_02.png` à déposer** |
