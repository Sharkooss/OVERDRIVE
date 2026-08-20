# Journal — 2026-08-20 — J8 (manche 7)

**Objectif** : deux correctifs de combat demandés par Louis manche en main.
1. *« ce n'est pas un line trace mais plus un sphere trace, pour avoir une hitbox beaucoup plus
   permissive, que le joueur ne se sente pas obligé d'être au pixel près… c'est trop dur surtout
   avec la speed accumulée »* → passe 2 de l'aide à la visée (`SPEC_COMBAT §11`).
2. *« dans la tête ça one shot »* → `IsHeadshot` réel + une vraie hitbox de tête sur la cible de test.

---

## Chantier 1 — passe 2 de l'aide à la visée

### `BP_LaserWeapon.ResolveShot` — 14 → **30** nœuds

Nouvelle sortie **`bAssisted : bool`**. Corps conforme **au mot près** au pseudo-code de `§11` :

| Étape | Nœuds | Détail |
|---|---|---|
| Origine / direction | inchangés | `OwnerController → PlayerCameraManager → GetCameraLocation`, direction = forward de `GetControlRotation` **brut** |
| Passe 1 | `Collision\|LineTraceByChannel` | `TraceTypeQuery3`, `bTraceComplex = false`, `bIgnoreSelf = true`, `ActorsToIgnore = [OwnerCharacter]` |
| Gate | `Branch(bBlockingHit1)` | `then → return (Hit1, true, false)` — **le headshot n'est possible que par ce chemin** |
| Gate 2 | `Branch(TraceRadius > 0)` | `else → return (Hit1, false, false)` |
| Passe 2 | `Collision\|SphereTraceByChannel` | **mêmes `Start`/`End` que la passe 1** (un seul `GetCameraLocation`, un seul `vector+`), `Radius ← WeaponData.TraceRadius`, mêmes réglages de canal |
| Filtre | `BreakHitResult.HitActor → DoesObjectImplementInterface(BPI_Damageable)` + `AND bBlockingHit2` | `then → return (Hit2, true, **true**)` · `else → return (Hit1, false, false)` |

### `BP_LaserWeapon:EventGraph` — 30 → **32** nœuds

`ProcessHit(Hit, IsHeadshot(Hit) **AND NOT** bAssisted)` : `+1 NOTBoolean`, `+1 ANDBoolean`,
et le nœud d'appel de `ResolveShot` **recréé** (2.37). **Aucune écriture DSL sur ce graphe** :
`delete_node` + `create_node` + `connect_pins`, 10 liens restaurés à l'identique + 3 neufs.

---

## Chantier 2 — le headshot existe

### `BP_LaserWeapon.IsHeadshot` — 2 → **4** nœuds

Ne renvoie plus `false` en dur : `Hit.Component.ComponentHasTag("Head")`.
`BreakHitResult.HitComponent` (**sortie 10**) alimente **directement** le `self` de `ComponentHasTag`.

**Écart d'architecture assumé et documenté** (`SPEC_COMBAT §5.1`, encadré) : la spec prescrivait
`Hit.Component == Hit.Actor.HeadHitbox`, ce qui impose un `Cast<BP_EnemyBase>` **dans l'arme** —
classe qui n'existe pas avant le J12, et couplage que `05_ARCHITECTURE` interdit. Le tag est
générique (dummy aujourd'hui, `BP_EnemyBase` demain, points faibles du Tank ensuite) et respecte
l'interdit **réel** de la spec, qui est `Hit.BoneName`.

### `BP_TargetDummy` — `HeadHitbox`

`SphereCollision` enfant de `TargetMesh`, **Component Tag `Head`**.
`EventGraph` 5 → **9** nœuds : trois appels insérés **en tête** du `BeginPlay` (recette 2.34),
avant `SetCurrentHealth` —
`SetCollisionResponseToAllChannels(Ignore)` → `SetCollisionResponseToChannel(ECC_GameTraceChannel3, Block)`
→ `SetCollisionEnabled(QueryOnly)`. **Aucun preset de collision par outil** (`12_PIEGES §5.15`) :
relu en PIE, le composant est en `QueryOnly / profil Custom`, toutes les réponses à `Ignore`
**sauf `GameTraceChannel3`**. C'est la parade `§5.26`, et elle tient.

**Dimensionnement — la valeur que j'avais posée d'abord était fausse.** Rayon monde 40 uu :
correct de face (corps 60 × 60, demi-largeur 30) et **négatif à 45°** (demi-diagonale 42.4).
Le headshot aurait marché de face et disparu en approche oblique — soit exactement en course.
Corrigé à **50 uu** monde, centre **+75 uu** au-dessus du pivot. Nouveau piège `12_PIEGES §6.23`.

⚠️ `TargetMesh` est la **racine** et porte l'échelle `0.6/0.6/1.8`, dont la sphère hérite.
`GetShapeScale() = GetMinimumAxisScale() = 0.6` (source moteur lue). Valeurs saisies sur le
composant : `Sphere Radius = 83.333333`, `Relative Location Z = 41.666667`. Le **viewport**, lui,
dessine la sphère à sa taille monde — c'est lui qui fait foi pour un réglage à l'œil.

---

## Preuves

### Comptages (avant → après, `find_nodes`)

| Graphe | Avant | Après | Attendu |
|---|---|---|---|
| `BP_LaserWeapon:ResolveShot` | 14 | **30** | ✅ |
| `BP_LaserWeapon:EventGraph` | 30 | **32** | ✅ (`−1` appel périmé, `+1` neuf, `+2` NOT/AND) |
| `BP_LaserWeapon:IsHeadshot` | 2 | **4** | ✅ |
| `BP_TargetDummy:EventGraph` | 5 | **9** | ✅ |
| `ProcessHit` / `PlayFireFX` / `UpdateBeam` / `EnsureOwnerRefs` | 16 / 15 / 34 / 3 | **inchangés** | ✅ |

### Audits

- **Accessibilité exec** (racine = ≥1 sortie Exec et **0** entrée Exec — `2.31`) :
  `ResolveShot` **1 racine, 0 nœud mort** · `EventGraph` **4 racines** (`BeginPlay`, `TryFire`,
  `EndFireCooldown`, `Tick`), **0 mort** · `BP_TargetDummy:EventGraph` 3 racines, 0 mort.
  Les `Branch ×3` et `ReturnNode ×4` de `ResolveShot` sont la structure du `if/elif`, pas des
  chaînes empilées (chacun a un prédécesseur exec unique).
- **Contrôle 2.21 sur chaque `self`** : `Pawn|GetControlRotation.self` est de type
  **`Controller Object Reference`** et vient **directement** de `OwnerController` → c'est bien la
  surcharge `AController`, aucun nœud intercalé. Idem `GetPlayerCameraManager`, `GetCameraLocation`,
  `GetTraceRadius`, et les 3 `self` du dummy alimentés par un **unique** `GetHeadHitbox`.
- **Valeurs de pins relues** : `TraceChannel = TraceTypeQuery3` sur **les deux** traces,
  `bTraceComplex = false`, `bIgnoreSelf = true`, `Interface = /Game/OVERDRIVE/Core/BPI_Damageable.BPI_Damageable_C`,
  `Channel = ECC_GameTraceChannel3`, `NewResponse = ECR_Block`, `NewType = QueryOnly`, `Tag = Head`.
- **Compilations `warnings_as_errors = True`** vertes sur `BP_LaserWeapon`, `BP_TargetDummy`,
  `BP_PlayerCharacter`. `save_assets` sur les 3 BP + `IMC_Debug` + `DA_Weapon_Laser` + **le niveau**.

### Mesures PIE

Joueur spawné à `(0, −3000, 300)`, retombé à `(0, −3000, 89.65)`, caméra à **`(0, −3000, 153.65)`**.
Tir déclenché par `F4` mappé temporairement dans `IMC_Debug` (recette `§4.11`).
Une session PIE par test : la `ControlRotation` ne se change pas en cours de jeu (`§4.15`).

| # | Visée | Résultat mesuré | Verdict |
|---|---|---|---|
| 1 | `(1000, −5000, 90)` — corps | `BeamEnd (985, −4970, 91)` = face du cube. Vie **100 → 50 → acteur détruit** | ✅ 2 tirs au corps tuent |
| 2 | `(1000, −5000, 165)` — centre de la sphère de tête | `BeamEnd (977.6, −4955.3, 164.7)` = **surface de la sphère** (49.96 uu du centre), **pas** la face du cube qui serait à `(985, −4970)`. **Détruite en 1 tir** | ✅ headshot = 150 pv, one-shot |
| 3 | `(1000, −5000, 232)` — **52 uu au-dessus du crâne**, passe 1 vers le ciel | `BeamEnd (989.2, −4978.5, 208.8)` = surface de la sphère de **tête**. Vie **100 → 50** | ✅ la passe 2 touche **et** ne donne **pas** de headshot (`−50`, pas `−150`) |
| 4a | `(1000, −3000, 150)` — mur en face | `BeamEnd (1000, −3000, 150)`, dist **1000 uu**. **Les 7 cibles restent à 100** | ✅ aucun dégât |
| 4b | `(1000, −3000, 195)` — **rase l'arête haute du mur à 13 uu**, passe 1 vers le ciel | `BeamEnd` à **15 000 uu** (= `TraceEnd`). Sans le filtre `BPI_Damageable`, l'impact serait à 1000 uu sur le mur | ✅ l'assistance **jette** le décor |
| 4c | `(1040.25, −4979.88, 90)` — 45 uu à côté de la cible, **11 uu à côté du corps** | passe 1 a touché le **mur 442 uu derrière la cible** (`BeamEnd` à 2678 uu, cible à 2236) → **0 dégât** | ⚠️ voir ci-dessous |

Les trois branches de `bHeadshot = IsHeadshot AND NOT bAssisted` sont donc prouvées séparément :
`false AND …` (test 1), `true AND true` (test 2), `true AND NOT true` (test 3).

### Échafaudage restauré et revérifié clé par clé

`IMC_Debug.defaultKeyMappings` : **1 mapping**, `key = F3`, `action = IA_DebugToggle`, 1 trigger.
`LevelEditorPlaySettings.GameGetsMouseControl` : **`false`**.
`DA_Weapon_Laser` : `Range 15000 · TraceRadius 25 · BodyDamage 50 · HeadshotMultiplier 3 · FireCooldown 0.18`
— inchangé, aucune valeur de tuning n'a servi d'échafaudage.

---

## ⚠️ Contradiction mesurée — arbitrage de Louis attendu

Le test **4c** n'est pas un succès, c'est un **constat**. Le pseudo-code de `§11` conditionne la
passe 2 à `!Hit1.bBlockingHit`, soit *« la passe 1 n'a touché **rien du tout** sur 15 000 uu »*.
Or le canal `Weapon` est `Block` sur le décor : **derrière chaque ennemi il y a un mur.**

Un tir manqué de 11 uu à côté d'une cible — exactement le cas que l'aide à la visée doit
rattraper — n'a donc produit **aucun** dégât. Le seul tir assisté reproductible visait **le ciel**.

**Tel qu'écrit, `Laser_TraceRadius` n'aidera presque jamais en jeu réel.** Le symptôme sera
« je monte le rayon et ça ne change rien », pas une erreur.

Je n'ai **pas** corrigé de moi-même : la consigne était d'implémenter le pseudo-code au mot près,
et changer le gate change le comportement. Les deux options sont écrites dans `SPEC_COMBAT §11` :
1. gate sur *« pas touché de `BPI_Damageable` »* + rejet d'un hit de passe 2 **plus lointain** que
   celui de la passe 1 (sinon on tire à travers les murs) ;
2. une seule passe `SphereTraceMulti` triée par distance.

---

## Décisions prises

| Décision | Pourquoi | Où c'est écrit |
|---|---|---|
| `IsHeadshot` = `ComponentHasTag("Head")` au lieu d'une comparaison de composant | Pas de cast, pas de couplage arme→ennemi, extensible aux points faibles du Tank | `SPEC_COMBAT §5.1`, encadré « écart d'implémentation » |
| Rayon de tête = **50 uu** (> demi-diagonale 42.4), pas 40 | À 40 la tête disparaît dès 45° d'incidence | `07_TUNING §16` + `12_PIEGES §6.23` |
| Collision de la sphère posée **dans le graphe**, pas par preset | `12_PIEGES §5.15`/`§5.26` ; vérifié en PIE, pas par relecture de propriété | `07_TUNING §16` |
| Les 7 cibles du sandbox **supprimées et re-posées** (labels, transforms, dossier restaurés) | Seul moyen de propager un composant neuf sur des acteurs déjà placés | `12_PIEGES §5.35` |
| La contradiction du gate de `§11` est **signalée, pas contournée** | `CLAUDE.md` §5 | `SPEC_COMBAT §11` + `12_PIEGES §6.24` |

## Valeurs ajoutées à `07_TUNING.md`

| Clé | Valeur monde | Valeur saisie | Statut |
|---|---|---|---|
| `TargetHead_Radius` | **50 uu** | `Sphere Radius = 83.333333` | À CALIBRER |
| `TargetHead_LocalZ` | **+75 uu** (Z monde 165) | `Relative Location Z = 41.666667` | À CALIBRER |

Aucune valeur existante n'a été modifiée. `Laser_TraceRadius` a reçu un avertissement, pas une
nouvelle valeur.

## Bugs / pièges rencontrés

| Piège | Gravité | Entrée |
|---|---|---|
| Le `bind` multi-sorties du DSL est **positionnel**, alors que le lecteur nomme par pin | 🔴 | `12_PIEGES 2.36` |
| `add_function_param` casse les nœuds d'appel comme `remove_function_param` | 🔴 | `12_PIEGES 2.37` |
| Composant neuf → valeurs figées sur les instances placées, `relativeLocation` inécrivable | 💀 | `12_PIEGES 5.35` |
| Hitbox sphérique dimensionnée sur la demi-largeur au lieu de la demi-diagonale | 🔴 | `12_PIEGES 6.23` |
| Aide à la visée gatée sur « n'a rien touché » = morte en niveau fermé | 🔴 | `12_PIEGES 6.24` |

## Ressenti de playtest

> **Non joué.** R8/R10 : rien n'est validé tant que Louis n'a pas tiré en courant.
> Checklist dans la réponse d'accompagnement. **Aucun commit.**

## Vérifications de fin de manche

- [x] BP recompilés, zéro warning (`warnings_as_errors = True`)
- [x] Assets **et niveau** sauvegardés
- [x] Échafaudage de test restauré et revérifié clé par clé
- [x] Roadmap cochée, tuning à jour, pièges consignés
- [ ] 3 minutes de jeu réel — **en attente de Louis**
- [ ] Commit — **volontairement pas fait (R10)**
