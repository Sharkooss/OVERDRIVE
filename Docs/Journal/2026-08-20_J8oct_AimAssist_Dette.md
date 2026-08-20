# Journal — 2026-08-20 — J8 (manche 8)

**Objectif** : solder la **dette J8** — `Laser_TraceRadius = 25` ne pilotait rien.
Louis a tranché la contradiction laissée ouverte au J8sept (`SPEC_COMBAT §11`).

---

## Fait

### `BP_LaserWeapon.ResolveShot` — 30 → **36** nœuds

Un seul graphe touché. **Aucune modification de signature** (`Hit` / `bBlockingHit` / `bAssisted`
existaient déjà) — donc aucun `add_function_param`, donc aucun nœud d'appel à recréer (2.37 évité).

| Étape | Avant (J8sept) | Après (J8oct) |
|---|---|---|
| Passe 1 | `LineTraceByChannel` | **inchangée** |
| Gate | `if (Hit1.bBlockingHit) return Hit1` | `if (Hit1.bBlockingHit AND Hit1.Actor implements BPI_Damageable) return (Hit1, true, false)` |
| Passe 2 | `SphereTraceByChannel` (simple) | **`Collision\|MultiSphereTraceByChannel`** |
| Sélection | 1 hit, filtré `BPI_Damageable` | **`ForEachLoopWithBreak`** sur `OutHits`, on retient le **premier** hit `BPI_Damageable` et on sort (§13 piège 5 : le multi renvoie un hit par composant) |
| Garde d'occlusion | ø | `(NOT Hit1.bBlockingHit) OR (h.Distance < Hit1.Distance)` — sinon **`break`** |
| Sortie finale | `return (Hit1, false, false)` | **`return (Hit1, Hit1.bBlockingHit, false)`** ← l'impact décor ressort par là |

**Le troisième point est le vrai risque du chantier et n'était dans aucune des deux corrections
proposées au J8sept.** La branche précoce `if (bBlockingHit) return Hit1` était **la seule sortie**
par laquelle un impact mural repartait avec `bBlockingHit = true`. En la conditionnant à
« c'est une cible », il fallait que la sortie finale reprenne le relais **avec le vrai booléen** —
sinon `PlayFireFX` retombe sur `Hit.TraceEnd` et le faisceau traverse les murs jusqu'à 15 000 uu.
Testé explicitement (mesures 5, 6 et 7).

**Ce qui n'a pas changé** : un hit assisté reste un body shot (`bAssisted` force `bHeadshot = false`
dans `TryFire`, câblage relu et intact) · `bTraceComplex = false` · canal `TraceTypeQuery3` ·
`ActorsToIgnore = [OwnerCharacter]` + `bIgnoreSelf = true` sur les deux traces.

---

## Preuves

### Comptages (`find_nodes`, avant → après)

| Graphe | Avant | Après | Attendu |
|---|---|---|---|
| `BP_LaserWeapon:ResolveShot` | 30 → **purge 2** → 36 | **36** | ✅ mesure absolue (5.29) |
| `BP_LaserWeapon:EventGraph` | 32 | **32** | ✅ intact, appelant recâblé sur ses 4 pins |
| `ProcessHit` / `IsHeadshot` / `PlayFireFX` / `UpdateBeam` / `EnsureOwnerRefs` | 16 / 4 / 15 / 34 / 3 | **inchangés** | ✅ |

Purge préalable (5.29) : liste des **28** nœuds imprimée et vérifiée (tous préfixés `:ResolveShot.`)
avant suppression, `FunctionEntry` **et un `FunctionResult`** conservés — les sorties d'une fonction
vivent sur le nœud Result (nouveau piège **5.38**). Compte après purge : **2**, donc les 36 nœuds
finaux sont une mesure absolue, pas un delta à interpréter.

### Audits

- **Accessibilité exec** (racine = ≥1 sortie Exec, **0** entrée Exec — 2.31) : **1 racine**
  (`K2Node_FunctionEntry_0`), **0 nœud mort**. Les `Branch ×4` et `ReturnNode ×4` sont la structure
  du `if` imbriqué, chacun avec un prédécesseur exec unique (2.2c).
- **Contrôle 2.21 sur chaque `self`**, relu par `get_node_infos`, tous **directs**, aucun nœud
  intercalé : `GetPlayerCameraManager.self = Player Controller` ← `OwnerController` ·
  `GetCameraLocation.self = Player Camera Manager` ← `GetPlayerCameraManager` ·
  **`Pawn|GetControlRotation.self = Controller Object Reference`** ← `OwnerController` (bonne
  surcharge `AController`) · `GetRange.self` et `GetTraceRadius.self = PDA Weapon Data` ← `WeaponData`.
- **Doublons de nœuds impurs** : `LineTraceByChannel ×1`, `MultiSphereTraceByChannel ×1` — un seul
  trace physique de chaque par tir malgré 4 et 1 références de bind (2.30 confirmé).
- **2.3b** : aucun `Set` dans la fonction, donc aucune lecture après écriture possible.
- **Pins du `ForEachLoopWithBreak`** relus un par un : `Break ← Branch(else)`, `LoopBody → Branch`,
  `Completed → ReturnNode`, `Array ← OutHits`. Nouveau piège **2.38**.
- **Compilation `warnings_as_errors = True`** verte, avant **et après** les 7 sessions PIE.
  `save_assets` sur `BP_LaserWeapon` et `IMC_Debug`.

### Mesures PIE

Joueur spawné à `(0, −3000, 300)`, caméra à **`(0, −3000, 153.65)`** — même point qu'au J8sept, donc
les chiffres sont directement comparables. Une session par test (4.15), tir par `F4` mappé
temporairement dans `IMC_Debug` (recette 4.11). `MaxHealth = 100`, `BodyDamage = 50`, `TraceRadius = 25`.

| # | Visée | Attendu | Mesuré | J8sept | Verdict |
|---|---|---|---|---|---|
| 1 | `(1000, −5000, 90)` corps | `−50` | `100 → 50`, `BeamEnd (985, −4970, 91)` à **2203.4 uu** | identique | ✅ tir précis inchangé |
| 2 | `(1000, −5000, 165)` tête | détruite en 1 coup | **acteur détruit**, `BeamEnd (977.6, −4955.3, 164.7)` = surface de la sphère | identique | ✅ **headshot non dégradé** |
| 3 | `(1040.25, −4979.88, 90)` — **11 uu à côté du corps, mur 442 uu derrière** | `−50` | `100 → 50`, `BeamEnd (1021.9, −4970, 91.1)` à **2220.2 uu** (flanc de la cible) | **`0 dégât`**, beam sur le mur à 2678 | ✅ **LA dette est soldée** |
| 4 | `(1000, −5000, 232)` — assisté sur la `HeadHitbox` | `−50`, pas `−150` | `100 → 50`, `BeamEnd (989.2, −4978.5, 208.8)` = surface de la sphère de tête | identique | ✅ l'assistance ne donne jamais de headshot |
| 5 | `(4200, −5350, 490)` — **mur, cible 1182 uu derrière** | `0` + beam sur le mur | **les 7 cibles restent à 100**, `BeamEnd (3171, −4774.2, 407.6)` à **3642.4 uu** = distance du mur mesurée hors jeu (3642.446) | non testé | ✅ garde d'occlusion **et** non-régression du retour final |
| 6 | `(1000, −3000, 150)` — mur en face | beam à 1000 uu | `BeamEnd (1000, −3000, 150)`, **1000.0 uu**, 0 dégât | identique | ✅ impact décor par la sortie finale |
| 7 | `(1000, −3000, 195)` — rase l'arête, passe 1 vers le ciel | beam à 15 000 uu | `BeamEnd (14987.2, −3000, 773.4)`, **15 000.0 uu**, 0 dégât | identique | ✅ le miss reste un miss |

Le cas 5 a été construit **hors jeu** avec `SceneTools.trace_world` : distance au premier bloquant
`3642` vs distance au centre de la cible `4824`, puis re-traces depuis `h+20 / +60 / +120` décroissant
de 40 en 40 avec un décalage constant de 34 uu → la cible est bien pile dans l'axe, derrière le mur
(nouveau piège **4.19**).

### Échafaudage restauré et revérifié clé par clé

`IMC_Debug.defaultKeyMappings` : **1 mapping**, `F3 → IA_DebugToggle`, 1 trigger, **identique à la
sauvegarde** (comparaison de dict, pas à l'œil). `LevelEditorPlaySettings.GameGetsMouseControl` :
**`false`**. Les 7 `BP_TargetDummy` : `MaxHealth 100`, `DebugHitSphere* = 25 / 0.25 / 2 / 12 / magenta`.
`DA_Weapon_Laser` : `Range 15000 · TraceRadius 25 · BodyDamage 50 · HeadshotMultiplier 3 ·
FireCooldown 0.18` — **aucune valeur de tuning n'a servi d'échafaudage**, `StopPIE` fait.

---

## Pas fait / reporté

- Rien d'autre. Chantier volontairement limité à `ResolveShot` : aucun refactor, aucune feature.
- **Le calibrage de `Laser_TraceRadius` n'est pas fait** — la clé pilote enfin quelque chose, mais
  sa valeur (25) n'a jamais été jugée manche en main puisqu'elle était inopérante. C'est le playtest
  de Louis qui l'ouvre.

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| Le pseudo-code de `§11` est **remplacé**, pas amendé ; l'encadré « contradiction mesurée » devient une note historique explicite | `SPEC_COMBAT §11` |
| La sortie finale renvoie `Hit1` **avec son vrai `bBlockingHit`** — point absent des deux corrections proposées au J8sept, ajouté comme 3ᵉ contrainte non négociable | `SPEC_COMBAT §11` + `12_PIEGES §6.24` |
| Purge d'un graphe de fonction : conserver **un** `FunctionResult`, sinon la signature de sortie est effacée | `12_PIEGES §5.38` (extension de 5.29) |

## Valeurs modifiées

| Clé | Ancien | Nouveau | Raison |
|---|---|---|---|
| `Laser_TraceRadius` — **statut** | ⚠️ `SANS EFFET AUJOURD'HUI` | **`À CALIBRER`** | La clé pilote réellement l'aide à la visée depuis le J8oct ; l'avertissement long est remplacé par une note courte |

**Aucune valeur numérique n'a bougé.** `TraceRadius` reste à `25`.

## Ressenti de playtest

> **Non joué.** R8 / R10 : je peux prouver `−50` au lieu de `0`, je ne peux pas dire si l'assistance
> se sent juste ou trop généreuse en pleine course. **Aucun commit.**

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| `Collision\|SphereTraceMultiByChannel` n'existe pas — le `Multi` est en préfixe | 🟠 | `12_PIEGES §5.39` |
| Purger un graphe de fonction en gardant seulement le `FunctionEntry` efface les sorties | 💀 | anticipé, `12_PIEGES §5.38` |
| `trace_world` ne renvoie qu'une distance, pas un `HitResult` | ✅ | `12_PIEGES §4.19` |
| `(for … (break))` en DSL : quel macro, et le pin `Break` est-il câblé ? | ✅ | `12_PIEGES §2.38` |

## Demain

- Playtest de Louis sur les 5 points de la checklist, puis calibrage de `Laser_TraceRadius`.
- Commit **seulement après** son retour (R10).

---

## Vérifications de fin de manche

- [x] BP recompilé, zéro warning (`warnings_as_errors = True`), avant **et après** les sessions PIE
- [x] Assets sauvegardés (`BP_LaserWeapon`, `IMC_Debug`)
- [x] Échafaudage de test restauré et revérifié clé par clé, `StopPIE` fait
- [x] Roadmap cochée (`DETTE J8` → `[x]`), tuning à jour, spec réécrite, pièges consignés
- [ ] 3 minutes de jeu réel — **en attente de Louis**
- [ ] Commit — **volontairement pas fait (R10)**
