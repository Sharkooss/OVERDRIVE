# 2026-08-20 — J8ter — Faisceau laser : accroche/décrochage, glow, fondu doux

> Correctif de game feel demandé par Louis manche en main, sur le seul `BP_LaserWeapon`.
> Aucun autre système touché.

## Le retour de Louis, mot pour mot

> *« il faut que quand on tire ça parte exactement du muzzle du canon puis ensuite il se détache pour
> rester en l'air là où on a tiré, je ne veux pas de duplication »*
> *« un effet beaucoup plus glowy »*
> *« qu'il reste encore un peu plus longtemps et fade un peu plus doucement, car là c'est encore trop bref »*

## Le diagnostic

Le correctif du J8 avait fabriqué le bug suivant. `UpdateBeam` relisait `Muzzle.GetWorldLocation()`
**à chaque frame** pendant toute la vie du faisceau, et chaque segment vivait
`LaserDebug_DrawLifetime` = 0.05 s, soit ≈ 3 frames. À ~1900 uu/s le canon parcourt ~32 uu par frame :
**trois segments d'origines différentes coexistaient en permanence**, lus par le joueur comme deux
rayons qui divergent depuis le point d'impact.

Les deux réglages étaient individuellement corrects et incompatibles entre eux. Ni erreur, ni warning,
et le bug n'existe pas à l'arrêt. Consigné en `12_PIEGES §6.20` et `SPEC_COMBAT §13 piège 10bis`.

## Ce qui a été fait

### 1. Accroche puis décrochage — c'est ce qui tue la duplication

Nouvelle variable **`BeamStart`** (Vector, cat. `Debug`, **non** `Instance Editable`).

- `PlayFireFX` pose `BeamStart = Muzzle.GetWorldLocation()` en plus de `BeamEnd`.
- `UpdateBeam` calcule `Elapsed = DebugBeamDuration − BeamTimeRemaining` et fait
  `BeamStart = select(Elapsed < DebugAttachTime, Muzzle.GetWorldLocation(), BeamStart)` :
  tant qu'on est dans la fenêtre, l'origine suit le canon ; au-delà, **elle est figée en espace monde**.
- Les deux tracés partent **toujours** de `BeamStart`, jamais du muzzle.

Une fois l'origine figée, tous les redessins se superposent au pixel près. Le petit éventail résiduel
de la fenêtre d'accroche est **voulu** : c'est ce qui donne « ça part du canon ».

Le `select` est un nœud pur : il lit l'ancienne `BeamStart` **avant** que le `Set` n'écrive — ce n'est
pas le piège `2.3b`, qui concerne un `Set` précédant un getter tiré plus tard.

### 2. Plus long, fondu plus doux

`LaserDebug_BeamDuration` **0.12 → 0.35 s**, et l'alpha passe de linéaire à
**`sqrt(BeamTimeRemaining / DebugBeamDuration)`** (`Math|Float|Sqrt`). L'alpha reste haut sur les deux
premiers tiers puis s'effondre : ça se lit comme une dissipation, pas comme un fondu mécanique.
Noté explicitement dans `07_TUNING §16` — sans ça la clé de durée se lit de travers.

### 3. « Glowy » — deux traits concentriques

Un debug line n'émet pas. On l'imite en dessinant **le même segment deux fois dans la même frame**,
du plus large au plus fin :

| | Épaisseur | Alpha |
|---|---|---|
| **halo** (dessiné **en premier**) | `DebugLineThickness × DebugGlowWidthMult` | `alpha × DebugGlowAlphaMult` |
| **cœur** (dessiné **ensuite**) | `DebugLineThickness` | `alpha` |

Les deux lisent la **même** `BeamStart` et la **même** `BeamEnd` — deux origines différentes
recréeraient exactement la duplication qu'on corrige. R/G/B identiques et saturés
(`OD_Magenta_Player`) : le halo n'est **pas** éclairci vers le blanc, il se délaverait sur un monde
clair en plein jour (`SPEC_COMBAT §3.2`, `12_PIEGES §6.19`).

## Assets modifiés

| Asset | Ce qui change |
|---|---|
| `/Game/OVERDRIVE/Weapons/Laser/BP_LaserWeapon` | +4 variables (`BeamStart`, `DebugAttachTime`, `DebugGlowWidthMult`, `DebugGlowAlphaMult`), `UpdateBeam` réécrite, `PlayFireFX` complétée, `DebugBeamDuration` 0.12 → 0.35 |
| `/Game/OVERDRIVE/Player/Blueprints/BP_PlayerCharacter` | `ChildActorTemplate` de `ChildActor_Laser` : les 4 valeurs écrites dessus (`12_PIEGES §5.27`) |

## Comptes de nœuds

| Graphe | Avant | Après | Méthode |
|---|---|---|---|
| `UpdateBeam` | 18 | **1** (purge) → **34** | purge du corps puis `write_graph_dsl` — comptage absolu, plus de delta à interpréter (`12_PIEGES §5.29`) |
| `PlayFireFX` | 12 | **15** | insertion d'un maillon par `create_node` + `break_pins` + `connect_pins` (`12_PIEGES §2.34`) |

Audit d'accessibilité **exec** (racine = sortie Exec sans entrée Exec, `2.31`) : **un seul root par
graphe**, le `K2Node_FunctionEntry`. Aucun orphelin.

Chaîne d'exec de `UpdateBeam` : `Entry → Branch(rem>0) → SetBeamStart → DrawDebugLine (halo) →
DrawDebugLine (cœur) → SetBeamTimeRemaining`.
Chaîne de `PlayFireFX` : `Entry → PlaySound2D → SetBeamEnd → **SetBeamStart** → SetBeamTimeRemaining
→ Branch → PlaySoundAtLocation`.

Contrôle `2.21` : le seul pin `self` du graphe est celui de `Transformation|GetWorldLocation`, alimenté
**directement** par `GetMuzzle`. Aucun nœud intercalé.

## Preuve PIE — sur l'instance de jeu, pas sur le CDO

`ChildActor_Laser_GEN_VARIABLE_BP_LaserWeapon_C_CAT_0` :

```
debugAttachTime    = 0.05
debugGlowWidthMult = 5.0
debugGlowAlphaMult = 0.3
debugBeamDuration  = 0.35
```

Le `ChildActorTemplate` était bien **périmé** avant écriture (`0 / 0 / 0` et `0.12`), exactement la
signature de `12_PIEGES §5.27`. Écrit → 2 recompilations → relu sur le template → relu **en PIE**.

Tir déclenché en headless par la parade `4.11` (mapping temporaire `F4 → IA_Fire` dans `IMC_Debug`,
`GameGetsMouseControl = true`), puis relecture :

```
beamStart = (68.5, −2986.0, 145.65)     <- muzzle en espace monde, non nul
beamEnd   = (1000.0, −3000.0, 153.65)
```

`BeamStart` non nul prouve que `PlayFireFX` l'écrit et que la chaîne complète tourne sur l'instance
de jeu. Échafaudage **restauré et revérifié** : `IMC_Debug` remis à son unique mapping `F3`,
`gameGetsMouseControl` remis à `false`, `StopPIE`.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| Origine relue chaque frame + segments persistants = éventail de rayons | 🔴 | Oui — accroche bornée puis décrochage. `12_PIEGES §6.20` |
| `write_graph_dsl` veut `code`, pas `dsl` — appel avorté | 🟠 | Oui. `12_PIEGES §5.28` |
| `AssetTools.find_assets` veut `folder_path` **et** `name` | 🟠 | Oui. `12_PIEGES §5.28` |
| `StartPIE` introuvable sous `editor_toolset.*` (c'est `EditorToolset.EditorAppToolset`) | 🟠 | Oui. `12_PIEGES §5.30` |
| `12_PIEGES §6.18` recommandait `Duration = DeltaSeconds`, ce qui ne dessine **rien** | 🔴 | Oui — entrée corrigée, la bonne valeur est `LaserDebug_DrawLifetime` |
| `get_node_type_pins` a laissé un `Math\|Float\|Sqrt` orphelin dans `UpdateBeam` | ⚪ | Oui — supprimé avant écriture. `12_PIEGES §2.12` |

## Décisions non triviales

- **`BeamStart` n'est pas `Instance Editable`** : c'est un état runtime, pas du tuning — même statut
  que `BeamEnd`. Écrit dans `SPEC_COMBAT §2`.
- **Le `select` plutôt qu'un second `Branch`** : un `if` termine le flux d'exec (`12_PIEGES §2.11`),
  il aurait fallu extraire une fonction. Le `select` garde la chaîne linéaire et lisible.
- **Halo avant cœur** : le line batcher dessine dans l'ordre de soumission ; le cœur doit rester par
  dessus. Écrit dans `07_TUNING §16` et `SPEC_COMBAT §2`.
- **Purge du corps de `UpdateBeam` avant réécriture** : rend le comptage `2.2b` absolu au lieu
  d'ambigu. Généralisé en `12_PIEGES §5.29`, avec la limite explicite « graphes de fonction seulement ».

## À faire à la manche suivante

- **Louis** : playtest (checklist dans la réponse d'accompagnement), puis retuner
  `LaserDebug_AttachTime` / `GlowWidthMult` / `GlowAlphaMult` / `BeamDuration` directement dans le
  panneau `Debug` de `ChildActor_Laser` en PIE. ⚠️ Toute valeur retenue doit être reportée
  **dans `07_TUNING §16`** *et* sur le CDO + le `ChildActorTemplate`.
- ~~Reste ouvert du J8~~ → **soldé le 2026-08-20** : `Pure` coché sur `IsHeadshot` (vérifié : plus de
  pin d'exec sur le nœud d'appel), et `BPI_Damageable` implémentée sur `BP_TargetDummy`.
- *(ligne d'origine)* Reste ouvert du J8 : cocher `Pure` sur `IsHeadshot`, et `BPI_Damageable` sur `BP_TargetDummy`.

---

## Vérifications de fin de journée

- [x] `BP_LaserWeapon` et `BP_PlayerCharacter` recompilés, `warnings_as_errors = True`, zéro warning
- [x] Assets sauvegardés (`save_assets`)
- [x] Défauts vérifiés **sur l'instance PIE**, pas seulement sur le CDO
- [x] Échafaudage de test restauré et revérifié
- [ ] 3 minutes de jeu réel — **en attente de Louis**
- [x] Roadmap cochée, tuning et specs à jour
- [ ] Commit fait — **volontairement pas fait (R10)**
