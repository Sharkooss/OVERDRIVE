# J8quinquies — Un seul dash par contact de surface (D57)

**Date** : 2026-08-20
**Jour de roadmap** : J8 / 28 — correctif de mouvement demandé manche en main
**Statut** : ⏸ **implémenté, compilé, prouvé en PIE — NON JOUÉ.** Rien n'est commité (R10).

> « j'aimerais avoir le timer du dash oui, mais aussi faire que sur un long saut on ne puisse pas
> spam les dash. Donc avoir qu'un seul dash, et pour le récup il faut attendre le timer ET avoir
> touché une surface, donc sol ou wall ride. Car là on peut limite voler en spammant les dash. »
> — Louis

---

## La règle

La charge de dash est utilisable quand **les deux** conditions sont vraies :

1. `Dash_Cooldown` écoulé — **mécanisme existant, inchangé** ;
2. **une surface a été touchée depuis le dernier dash** — sol **ou** accroche de wall ride.

`Dash_Charges = 1` et `Dash_Cooldown = 1.4 s` ne bougent pas. La nouvelle règle est une **garde
d'entrée** posée à côté du cycle de charge, pas une refonte de ce cycle. C'est **D57**.

---

## Fait — `BPC_Dash` uniquement

Le J5 a coûté **7 playtests** parce qu'une coupure du slide qui n'avait pas lieu d'être a été
réparée cinq fois (**D42**). Consigne tenue ici : **amender, ne pas refondre.** Aucune écriture de
vélocité, aucune modification du déroulé du dash, aucune réécriture de graphe validé.

### 3 variables (catégorie `Dash`)

| Variable | Type | Rôle |
|---|---|---|
| `bSurfaceTouchedSinceDash` | bool, défaut **`true`** | le drapeau. Défaut `true` = on démarre une partie avec son dash |
| `TuneDashRequiresSurfaceTouch` | bool | cache de la clé de tuning, lue au `BeginPlay` comme les 12 autres |
| `CachedWallRide` | `BPC_WallRide` | résolu au `BeginPlay`, cible de l'abonnement au dispatcher |

### 5 graphes touchés, tous par **insertion** (recette 2.34), jamais par réécriture DSL

| Graphe | Avant | Après | Ce qui a été inséré |
|---|---|---|---|
| `CacheTuning` | 51 | **53** | `GetDash_RequiresSurfaceTouch(self = MovementData)` → `SetTuneDashRequiresSurfaceTouch`, spliqué entre `SetLastDashTime` et `SetbTuningCached` |
| `CanDash` | 10 | **15** | `NOT(TuneDashRequiresSurfaceTouch) OR bSurfaceTouchedSinceDash`, ajouté en `AND` **après** la chaîne existante. Les 3 gardes du J5 sont intactes et inchangées |
| `StartDash` | 36 | **37** | `SetbSurfaceTouchedSinceDash = false` **appendu** en queue de la branche `bAccepted`, après `CallOnDashPerformed`. Aucun nœud existant déplacé ni recâblé |
| `TickDash` | 5 | **6** | `UpdateSurfaceTouch()` en **tête** de chaîne |
| `EventGraph` | 8 | **15** | résolution de `CachedWallRide` + `BindEventtoOnWallRideStarted` en queue du `BeginPlay`, + custom event `HandleWallRideStarted` → `SetbSurfaceTouchedSinceDash = true` |

### 1 fonction nouvelle — `UpdateSurfaceTouch` (8 nœuds, écrite depuis un graphe vide)

```
si  CMC.IsMovingOnGround()  ET  NOT bIsDashing   →   bSurfaceTouchedSinceDash = true
```

Deux points non triviaux :

- **`BPC_Dash` tick en DERNIER (D32)** — il ne consomme donc que des **états moteur** :
  `IsMovingOnGround()` et son propre `bIsDashing`. Jamais `MovementState.CurrentState`, jamais un
  cache d'un autre composant (`12_PIEGES §6.12`, le bug des 5625 uu/s du J5).
- **`NOT bIsDashing` n'est pas décoratif.** Sans lui, un dash déclenché **depuis le sol** verrait
  son contact re-crédité au frame même où il part (le CMC est encore en `Walking` pendant la
  première frame d'un dash vers le ciel) — et le joueur repartirait en l'air avec un dash en poche.
  Avec lui, aucun réarmement pendant les 0.16 s ; à la sortie, si on est encore au sol, le
  réarmement a lieu au frame suivant.

### Le contact mural passe par le dispatcher, pas par une lecture

`BPC_WallRide` possède `OnWallRideStarted` depuis le J6, appelé en queue de `StartWallRide`
(dispatcher sans paramètre). `BPC_Dash` s'y **abonne** au `BeginPlay`, après avoir résolu le
composant. Zéro lecture de cache, zéro dépendance d'ordre de tick — la voie propre imposée par
`05_ARCHITECTURE` (dispatcher vers le haut, pas de `Cast` en Tick).

### Tuning (R3)

`Dash_RequiresSurfaceTouch` (**bool**, défaut **true**, `[À CALIBRER]`) ajoutée à
`PDA_MovementData` (catégorie `Dash`, `Instance Editable`), posée à `true` sur le CDO **et** sur
`DA_Movement_Default`, répercutée dans `07_TUNING §8` et `§19`.
**À `false`, le comportement d'avant est restauré à l'identique** — c'est le filet de sécurité si
le playtest rejette la règle, et ça ne demande aucune retouche de graphe.

---

## Ce qui n'a PAS été touché

`Dash_Charges` · `Dash_Cooldown` · `UpdateCharges` · la conservation de la norme (**D30**) ·
la direction au regard (**D37**) · la lecture de `CMC.Velocity` à l'entrée (**D38**) ·
le gel du slide (**D39** / **D42**) · le FOV kick · l'ordre de tick · `CanEnterState` ·
`BPC_Slide`, `BPC_WallRide`, `BPC_MovementState`, `BP_PlayerCharacter` (aucun graphe modifié).

---

## Vérifié

### Statique

- Comptes de nœuds relevés **avant et après chaque écriture** (2.2b) : 51→53, 10→15, 36→37, 5→6,
  8→15, 0→8. Tous conformes à l'attendu nœud par nœud.
- **Audit d'accessibilité exec par la topologie** (2.31 — racine = sortie `Exec` sans entrée `Exec`,
  jamais par nom) sur les 6 graphes : **0 nœud mort**, 1 seule racine par fonction, 3 racines dans
  l'`EventGraph` (`BeginPlay`, `Tick`, `HandleWallRideStarted`). Aucun `type_id` porteur d'exec en
  double (pas de chaîne empilée, 2.2c).
- **Chaque `self` relu et alimenté DIRECTEMENT par la variable voulue** (2.21) : le `self` de
  `IsMovingOnGround` vient de `GetCachedCMC`, celui de `GetDash_RequiresSurfaceTouch` de
  `GetMovementData`, celui du `BindEvent` de `GetCachedWallRide`. **Aucun nœud intercalé.**
- Valeurs de pins relues : `SetbSurfaceTouchedSinceDash` = `false` dans `StartDash`, `true` dans
  `HandleWallRideStarted` et dans `UpdateSurfaceTouch` ; `ComponentClass` = `BPC_WallRide_C`.
- **Ordre `Set` / getter pur vérifié** (2.3b/2.3c) : dans `UpdateSurfaceTouch`, aucun `Set` ne
  précède le `Branch` qui lit les mêmes variables. Dans l'`EventGraph`, `SetCachedWallRide`
  s'exécute **avant** le `BindEvent` qui tire le getter — l'ordre voulu.
- `compile_blueprint` en `warnings_as_errors` : vert sur `PDA_MovementData`, `BPC_Dash`,
  `BPC_MovementState`, `BPC_Slide`, `BPC_WallRide`, `BP_PlayerCharacter`.

### En PIE (relevés sur l'instance de jeu, pas sur le CDO)

Échafaudage : mapping temporaire `F4 → IA_Dash` dans `IMC_Debug` + `GameGetsMouseControl = true`
(recette `12_PIEGES §4.11`). **Retiré et revérifié clé par clé en fin de session** ; `IMC_Debug`
est byte-identique à sa version commitée (`git status` ne le voit pas).

| Ce qui est prouvé | Relevé |
|---|---|
| La clé est lue sur l'instance de jeu | `tuneDashRequiresSurfaceTouch = true`, `bTuningCached = true` |
| Le composant wall ride est résolu | `cachedWallRide → …BP_PlayerCharacter_C_0.WallRide` (non nul) |
| Le drapeau vaut `true` au sol | `bSurfaceTouchedSinceDash = true`, `movementMode = MOVE_Walking` |
| Le dash consomme le contact et **ne le récupère pas en l'air** | joueur passé en `MOVE_Flying` (§4.18) + `F4` dans le **même** appel → dash parti (`lastDashTime = 46.62`, `dashExitSpeed = 1400`), et **`bSurfaceTouchedSinceDash = false`** de façon durable |
| **La garde bloque bien, et c'est le drapeau qui bloque** | toujours en l'air : `dashCharges = 1`, `chargeTimer = 0` — la charge est *rendue* — et **2 appuis `F4` supplémentaires laissent `lastDashTime` à 46.622448891401291, inchangé au dix-millième** |
| Le sol réarme le drapeau | retour `MOVE_Walking` → `F4` → `lastDashTime` 79.47 → **127.64** (le dash repart) **et** `bSurfaceTouchedSinceDash = true` alors qu'aucune écriture de propriété n'a eu lieu entre l'appui et la lecture — seul `UpdateSurfaceTouch` peut avoir écrit ce `true` |
| Coyote time / sortie de sol | **prouvé par le graphe, pas par la mesure** : les deux seuls écrivains de `false` sont le défaut du composant et le `Set` appendu à `StartDash`. Courir puis sauter ne peut donc pas coûter le dash |

### NON vérifié — c'est pour toi

- Le **wall ride** comme source de réarmement. L'abonnement est prouvé côté câblage
  (dispatcher sans paramètre, `self` = `CachedWallRide` non nul en jeu, custom event branché sur le
  pin `Delegate`), mais **aucun wall ride réel n'a pu être déclenché headless** dans cette session
  (il faut approcher un mur à la bonne vitesse, `12_PIEGES §4.16`). **C'est le point n°2 de ta
  checklist.**
- Tout le ressenti : est-ce que « un dash par saut » est *fun*, ou frustrant.

---

## Décisions

| # | Décision | Doc |
|---|---|---|
| **D57** | **Un seul dash par contact de surface.** Cooldown **ET** contact. Le drapeau tombe dans `StartDash`, se relève sur `IsMovingOnGround()` hors dash ou sur `OnWallRideStarted`. Implémenté comme **garde d'entrée** dans `CanDash` : `UpdateCharges` n'est pas touchée | `SPEC_MOVEMENT §8/§11`, `07_TUNING §8/§19` |

### Une conséquence à trancher par le playtest — je ne l'ai pas décidée seul

Comme la garde est séparée du cycle de charge, **l'overlay `DASH` peut afficher `charges 1/1` en
l'air alors que le dash est refusé.** C'est mécaniquement correct et strictement conforme à la
demande (« pour le récup il faut attendre le timer ET avoir touché une surface »), mais ça peut
se lire comme un bug en jeu. Deux réponses possibles, **aucune implémentée** :

1. ajouter `surf true/false` à la ligne `DASH` de l'overlay `F3` (2 nœuds dans `DrawDashDebug`) ;
2. conditionner la régénération de charge au drapeau, pour que `charges` affiche `0/1` tant qu'on
   n'a rien touché.

La consigne était de ne toucher que `StartDash`, la garde, `CacheTuning` et le Tick — je m'y suis
tenu et je te le signale au lieu d'improviser. **Dis-moi laquelle tu veux, si tu en veux une.**

---

## ⚙️ Checklist de test manuel (R8) — Louis

`L_Sandbox_Movement` en PIE. **`F3`** bascule l'overlay. Touche de dash : **`A`** ou **`Souris 4`**.
Le chiffre à surveiller reste **`DASH cd`** (le cooldown) — et **`SPEED`** pour les non-régressions.

### 0. Contrôle de vie (10 s, à faire en premier)
- [ ] À l'arrêt **au sol**, appuie sur `A` → tu dashes, `charges` passe à `0/1`, `cd` part de 1.40.
      Si rien ne part, arrête-toi et dis-le moi : c'est l'input, pas la règle du jour
- [ ] Attends que `cd` revienne à 0 **en restant au sol**, re-dashe → **ça doit repartir normalement**.
      Au sol, rien n'a changé par rapport à hier

### 1. Le test du jour — **un seul dash par saut**
- [ ] Prends de la vitesse, **saute le plus loin possible**, et **spamme `A` en l'air**
- [ ] Le **premier** dash part. **Aucun autre ne doit partir tant que tu n'as pas touché quelque chose**,
      même si `cd` est retombé à 0 et même si `charges` affiche `1/1`
- [ ] **Tu ne dois plus pouvoir « voler »** en enchaînant les dashs. C'est exactement le symptôme que
      tu as remonté : s'il subsiste, dis-le moi
- [ ] Retombe au sol → **le dash redevient disponible** (dès que `cd` est écoulé)

### 2. Le wall ride rend le dash — **le point que je n'ai PAS pu vérifier**
- [ ] Saute, **dashe en l'air**, puis **accroche un mur** en wall ride
- [ ] Pendant/après l'accroche, une fois `cd` à 0 → **`A` doit repartir**. Le mur doit compter comme
      un contact au même titre que le sol
- [ ] Enchaîne : dash → mur → dash → mur. La chaîne doit tenir tant qu'il y a des murs
- [ ] **Si le mur ne rend pas le dash, dis-le moi tout de suite** — c'est la seule partie du
      correctif qui n'a aucune preuve en jeu

### 3. Ce qui ne doit rien avoir perdu (non-régressions du J5)
- [ ] **Courir puis sauter sans dasher** → tu gardes ton dash. Il ne doit **jamais** disparaître
      parce que tu as quitté le sol
- [ ] **Slide → dash → slide** : `SLIDE hold` doit avoir **la même valeur** juste avant et juste
      après le dash (le dash gèle le slide, **D42**)
- [ ] `SPEED` juste avant et juste après un dash : **identique**. `DASH entry` = `exit` = cette
      valeur (**D30**/**D38**)
- [ ] **Reste accroupi et spamme le dash** : `SPEED` doit retomber à ta vitesse d'avant chaque
      dash. **Tu ne dois jamais rester perché à 5625** (**D39**)
- [ ] **Dash pendant un wall ride** → tu décroches et tu pars au regard, comme avant
- [ ] `Espace` pendant un dash au sol → le saut part **juste après**, jamais avalé

### 4. Ce qu'il faut sentir
- [ ] Est-ce que « un dash par saut » **rend les sauts plus intentionnels**, ou est-ce que ça
      **casse le flow** ? C'est la seule question qui compte
- [ ] Si c'est trop punitif : la clé est **`Dash_RequiresSurfaceTouch`** → `false` dans
      `DA_Movement_Default` et **tout revient exactement comme avant**, sans toucher au code
- [ ] Si c'est bon mais que l'affichage `charges 1/1` en l'air te gêne, dis-moi laquelle des deux
      réponses ci-dessus tu veux

**Ne change aucune valeur sans me le dire** — je répercute dans `07_TUNING` (R3).

---

## Pièges consignés

- **4.17** 🔴 — `ObjectTools.set_properties` sur un composant **en PIE relance le `BeginPlay`** de
  tous les composants de l'acteur, **même en réécrivant une valeur identique**. Mesuré :
  `lastDashTime` 127.64 → **−999** (la valeur de `CacheTuning`) après un `set_properties` neutre.
  Conséquence de méthode : **aucune comparaison « avant / après » n'est valable si un
  `set_properties` la traverse.** Ça a failli me faire conclure à tort que le réarmement au sol
  venait d'une réinitialisation ; le test a été refait sans écriture entre l'appui et la lecture.
- **4.18** ✅ — `CMC.movementMode = "MOVE_Flying"` est **la** façon de maintenir le joueur en l'air
  pendant plusieurs allers-retours MCP : ni gravité ni atterrissage (§6.15), `IsMovingOnGround()`
  reste faux, et **le tuning n'est pas modifié** — donc la physique testée non plus (contrairement
  à la parade de 4.12).

## Vérifications de fin de session

- [x] Tous les BP recompilés, **zéro warning** (`warnings_as_errors`)
- [x] Assets sauvegardés (`save_assets`, piège 5.6)
- [x] Échafaudage retiré et **revérifié clé par clé** : `IMC_Debug` revenu à son unique mapping
      `F3 → IA_DebugToggle` (et non modifié vs git), `GameGetsMouseControl = false`, `StopPIE`
- [x] `07_TUNING §8` + `§19`, `SPEC_MOVEMENT §8` + `§11`, `04_ROADMAP`, `12_PIEGES` à jour
- [ ] **Commit : NON. En attente de ton playtest (R10).**
