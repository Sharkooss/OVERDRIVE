# J8quater — Viser en wall ride

**Date :** 2026-08-20
**Durée :** ~2 h
**Statut :** ⏸ **implémenté, compilé, vérifié en PIE — EN ATTENTE DU PLAYTEST DE LOUIS (R10)**
**Rien n'est commité.**

---

## La demande

> « Il faudrait faire en sorte de pouvoir se décoller uniquement si on met la touche opposée au mur —
> mur à gauche, si on appuie sur D ou Z+D. Là on se décroche aussi si on regarde sur le côté.
> Il faudrait pas pouvoir se décrocher tant qu'on ne regarde pas à plus de 90 degrés. Au moins qu'on
> puisse regarder à droite si on est sur un mur, pour pouvoir tirer en étant en wall ride. »

C'est **le même conflit que `D53`** (le slide qui tournait quand on visait), sur une autre mécanique.
Le wall ride a été validé manche en main au J6 (« le game feel sur les murs est nickel ») ; l'arme est
arrivée au J8. Le J8quater **amende**, il ne refond pas.

---

## Le diagnostic — deux causes, pas une

L'hypothèse fournie était : *la trace de maintien part d'un vecteur de l'acteur, donc elle suit le
regard*. **Confirmée dans le graphe avant d'écrire** (piège 4.9) — et elle n'était que **la moitié**
du problème.

### Cause n°1 — la trace de maintien suivait le regard

`ConfirmWall` traçait `Start → Start + (ActorRightVector × WallSide) × (Capsule_Radius + DetectDistance)`.

`bUseControllerRotationYaw = true` : l'acteur tourne avec la caméra. Avec un standoff de ~40 uu et
104 uu de portée, la trace décroche du mur dès **arccos(40/104) ≈ 67°** de rotation de tête. Deux
évaluations ratées (à 33 Hz, soit **0.06 s**) et `EndWallRide("NoWall")` part.

### Cause n°2 — l'input de décrochage se jugeait dans la base caméra

C'est celle qu'on ne voyait pas, et **c'est la plus agressive**. `CheckDetachInput` construisait
`WishDir = normalize( CameraForward.XY × MoveInput.Y + CameraRight.XY × MoveInput.X )` — le vecteur
d'input **en espace monde**, celui-là même que l'air strafe utilise, et à juste titre pour lui.

En tenant `Z` (le réflexe pendant un ride), tourner la tête de θ vers l'extérieur donne
`Dot(WishDir, WallNormal) = sin θ`. Avec l'ancien seuil de 0.7 : décrochage dès **45°**. Avec le
nouveau seuil de 0.5 il aurait décroché dès **30°**.

**Corriger seulement la trace aurait donc laissé le bug en place** — et l'aurait même aggravé, en
donnant l'impression que le correctif n'avait rien fait. Les deux causes produisent le même symptôme
observable (« je me décroche quand je regarde sur le côté ») et se masquent l'une l'autre.
→ `12_PIEGES §6.21` et `§6.22`.

---

## Les décisions

### D54 — la trace de maintien suit la normale du mur

`ConfirmWall` trace désormais le long de **`-WallNormal`** (la normale mémorisée, rafraîchie à chaque
trace réussie). Portée, canal (`ObjectTypeQuery8`) et tolérance inchangés.

`WallSide` **n'est pas supprimée** : elle reste la donnée de `DetectWall` (l'accroche est
actor-relative par nature — « y a-t-il un mur à ma droite ? ») et du signe du roulis caméra (`D49`).
Elle n'est simplement plus consultée pendant le maintien.

Réutilisation de la variable existante `WallNormal`, aucune seconde variable de normale créée.

### D55 — l'input de décrochage se juge dans le repère du MUR

```
wallRight = Cross(WorldUp, WallDir)              // = ±WallNormal
wish      = normalize( WallDir × MoveInput.Y + wallRight × MoveInput.X )
detach    si Dot(wish, WallNormal) > WallRide_DetachDotThreshold  pendant DetachHoldTime
```

Mur à gauche ⇒ `wallRight = WallNormal` ⇒ `D` seul donne `dot = 1`, `Z+D` donne `0.707`, `Z` seul
donne `0`, `Q` donne `−1`. **Exactement la règle que Louis décrit, et totalement indépendante du
regard.**

⚠️ **Écart assumé avec la consigne.** Elle disait : *« WishDir est le vecteur d'input de déplacement
en espace monde (celui que `BPC_MovementState` utilise déjà pour l'air strafe — lis-le, ne le
recalcule pas) »*. Ce `WishDir`-là **est la cause n°2**. L'utiliser aurait rendu la demande
principale — viser en wall ride — impossible à satisfaire : à 30° de rotation de tête avec `Z` tenu,
on décroche. Le repère du mur est la seule formulation qui vérifie à la fois « `D` décroche »,
« `Z` ne décroche pas » et « le regard n'y change rien ». Décision écrite dans
`SPEC_MOVEMENT §9.4 D55`.

### D56 — nouvelle sortie nommée `LookAway`, à 90°

```
detach si Dot( normalize(CameraForward.XY), WallDir ) < TuneDetachLookCos
```

`TuneDetachLookCos = cos(WallRide_DetachLookAngle)` **précalculé au `BeginPlay`**, patron
`Tune_AirStrafeGainAngleCos` du J3. Comparaison sur des **vecteurs aplatis XY normalisés**, jamais
sur des yaw bruts : le passage ±180° casse toute soustraction d'angle (leçon `D53`).

Immédiate, sans temps de maintien : `WallRide_DetachHoldTime` ne concerne que `InputAway`. Regarder
droit en haut ou droit en bas donne `CameraForward.XY ≈ 0` → `Normalize` renvoie `(0,0,0)` →
`dot = 0 > cos(90°)` → **pas de décrochage**, comportement voulu.

### La clé demandée existait déjà — signalé, pas contourné

La consigne demandait **deux** clés neuves : `WallRide_DetachInputDot` (0.5) et
`WallRide_DetachLookAngle` (90°).

**`WallRide_DetachInputDot` aurait fait doublon** avec `WallRide_DetachDotThreshold`, qui existe
depuis le J6, est câblée, est marquée **VALIDÉ**, et porte exactement la même sémantique
(`Dot(WishDir, Normal)` au-delà duquel l'input compte comme « je pousse loin du mur »). Créer la
seconde aurait laissé une clé morte dans le DataAsset et deux sources de vérité.

**Décision : réutiliser la clé existante et la retuner `0.7 → 0.5`**, avec la justification chiffrée
dans `07_TUNING §9`. La raison de la valeur : `Z+D` en diagonale exacte vaut `cos(45°) = 0.70710678`,
soit **1 % de marge** au-dessus de 0.7 — Louis demande explicitement que `Z+D` décroche, ça ne peut
pas tenir à 1 %. `0.5` donne **60° de tolérance**. Elle repasse **À CALIBRER** : elle était validée à
0.7 par un playtest, elle doit être revalidée à 0.5.

---

## Ce qui n'a pas bougé

`Grounded` (`D45`, piège 6.15) · `WallJump` (`D48`) · accroche illimitée à vitesse constante (`D47`) ·
roulis caméra (`D49`) · `WallRide_SameWallCooldown` · les 3 garde-fous anti-héritage de la vitesse de
dash · `DetectWall` · `IsValidWall` · `RefreshWallDir` · `WallRideStep` · `CheckGrounded` ·
`CheckDuration` · `EndWallRide` · `TryWallJump` · `BPC_MovementState` · `CanEnterState`.

---

## Comptes de nœuds — avant / après chaque écriture

| Graphe | Avant | Après | Attendu | Méthode |
|---|---|---|---|---|
| `CacheTuning` | 85 | **88** | +3 | insertion chirurgicale (recette 2.34), **pas de DSL** — le DSL relu de cette fonction contient des artefacts `Class\|CapsuleCollision\|…` sur un DataAsset (piège 2.34), le réinjecter aurait été destructeur |
| `ConfirmWall` | 24 | **22** | +1 créé, −3 supprimés | insertion chirurgicale — **pas de DSL possible** : le pin `ObjectTypes` du `LineTraceForObjects` ne s'alimente pas en DSL (piège 2.22) |
| `CheckDetachInput` | 32 | **43** | purge → 1 → écriture | purge complète avant réécriture (recette 5.29) : le comptage devient une **mesure absolue**, plus un delta à interpréter |

**Audit d'accessibilité exec** sur `CheckDetachInput` (racine = sortie Exec sans entrée Exec, piège
2.31, jamais par `type_id`) : **1 seule racine** (`K2Node_FunctionEntry_0`), **43 vivants, 0 mort**.
Aucun empilement (2.2b / 2.2c).

**Audit des doublons de `type_id`** : `BreakVector2D` ×1, `GetCachedMoveInput` ×1, `CrossProduct` ×1,
`GetForwardVector` ×1 — le writer a **dédupliqué** les `bind` (comportement 2.30, pas 2.25). Aucun
nœud à effet de bord n'existe en double.

**Audit des pins `self` (2.21)** : `GetCachedMoveInput.self ← GetCachedMovement`,
`GetForwardVector.self ← GetCachedCamera`, `GetWallRide_DetachLookAngle.self ← GetMovementData` —
les trois alimentés **directement** par la variable voulue, **aucun getter intermédiaire inventé**.

**Audit des littéraux** : `EndWallRide` n°1 `Reason = "LookAway"`, n°2 `Reason = "InputAway"`, les
deux `bRestoreState = true` ; `MakeVector` du world-up = `(0,0,1)` ; le multiplicateur de `ConfirmWall`
= `(-1,-1,-1)`.

**Piège 2.3b / 2.3c désamorcé au passage.** L'ancienne `CheckDetachInput` faisait
`SetDetachHoldTimer(_new)` **puis** `if (_new >= hold)` : le `Branch` retirant le nœud pur `Add`
après l'écriture, il relisait `timer_neuf + dt`, soit **2 × dt** au lieu de `dt`. Le maintien tirait
donc à ~la moitié de `WallRide_DetachHoldTime`. La nouvelle structure compare **avant** d'écrire.

---

## Vérification PIE (`L_Sandbox_Movement`, zone E2, mur `Y = +500`)

Injection à `(−6500, 370, 500)`, vélocité `(2400, 250, 0)`, `MovementMode = MOVE_Falling`, le tout
dans **un seul** `execute_tool_script`.

| Vérification | Preuve |
|---|---|
| Les 2 clés sont lues sur l'instance de jeu | `TuneDetachLookCos = 6.123234e-17` — c'est `cos(90°)` **exact**, donc `WallRide_DetachLookAngle` a bien traversé DataAsset → `CacheTuning` → `Cos(Degrees)`. `TuneDetachDot = 0.5`. `bTuningCached = true` |
| La trace de maintien `-WallNormal` tient | `WallNormal = (0,−1,0)`, `WallDir = (1,0,0)`, **`MissedTraces = 0` sur 5500 uu** de couloir, sortie `NoWall` **en bout de mur** (X = −1000) |
| `D47` intact | `EntrySpeed = RideSpeed = 2412.9857024027306` — conservation exacte, la refonte n'a rien touché à la vitesse |
| La sortie `LookAway` existe et est atteignable | même injection vers `−X` (regard resté à yaw 0, soit **180°** de la direction de déplacement) → `LastEndReason = "LookAway"` dès la première évaluation |
| Le mapping des axes d'input | **prouvé topologiquement** : `MoveInput.Y → × WallDir`, `MoveInput.X → × Cross(WorldUp, WallDir)`. Le `bind` multi-sorties du DSL n'a pas inversé X et Y |
| Compilation | `warnings_as_errors = True` verte sur `PDA_MovementData`, `BPC_WallRide`, `BP_PlayerCharacter` |
| Assets sauvegardés | `PDA_MovementData`, `DA_Movement_Default`, `BPC_WallRide` — vérifié par `git status` |
| PIE | arrêté (`IsPIERunning = false`) |

### Ce que je n'ai PAS pu vérifier

**`InputAway`.** Deux impossibilités d'outillage, toutes deux consignées :

- `BPC_MovementState.CachedMoveInput` est **lisible mais pas inscriptible** (elle n'est pas
  `Instance Editable`, piège 4.8) — je ne peux pas simuler « D est enfoncé ».
- `AController::ControlRotation` n'est **ni lisible ni inscriptible** (piège 4.15, nouveau) — je ne
  peux pas tourner la tête pendant un ride. Le seul levier est le yaw de spawn, qui est aussi celui
  que `DetectWall` utilise pour l'accroche : au-delà de ~67° d'écart, **l'accroche elle-même** ne se
  fait plus. Il n'existe donc aucune configuration statique qui discrimine l'ancien code du nouveau.

C'est exactement la dette que le J6 avait laissée sur ces deux mêmes points. **Elle se solde manche
en main, pas autrement** (R8).

---

## Assets touchés

| Asset | Ce qui change |
|---|---|
| `Content/OVERDRIVE/Data/DataAssets/PDA_MovementData.uasset` | +1 variable `WallRide_DetachLookAngle` (float, `Instance Editable`, catégorie `Movement\|WallRide`) |
| `Content/OVERDRIVE/Data/DataAssets/DA_Movement_Default.uasset` | `WallRide_DetachLookAngle = 90` · `WallRide_DetachDotThreshold` 0.7 → **0.5** |
| `Content/OVERDRIVE/Player/Components/BPC_WallRide.uasset` | +1 variable `TuneDetachLookCos` (catégorie `WallRide`) · `CacheTuning` +3 nœuds · `ConfirmWall` retracée sur `-WallNormal` · `CheckDetachInput` réécrite |

---

## Dette ouverte

- **`InputAway` et le seuil de 90° ne sont validés par personne.** Premières lignes de la checklist.
- **`WallRide_DetachDotThreshold = 0.5` repasse À CALIBRER.** Si `Z+D` décroche trop facilement (par
  exemple en sortie de virage), c'est **cette clé** qu'on remonte, pas la logique.
- **`WallRide_DetachLookAngle = 90°` est un premier jet.** S'il faut viser plus loin derrière soi pour
  tuer un ennemi qu'on double, monter à 110–120°. S'il faut au contraire un moyen rapide de lâcher le
  mur au regard, descendre à 70°.
- **Le décrochage au regard n'a aucun feedback.** Aujourd'hui le joueur ne peut pas savoir qu'il est
  près du seuil. Si Louis le trouve surprenant, la réponse n'est **pas** de changer le seuil : c'est du
  feedback (`WallRide_CameraTilt` qui se relâche progressivement, par exemple) — et c'est du J14.
- Dettes J6 non soldées reprises telles quelles : sons de wall ride, marches de la zone F à 150 uu.

---

## Checklist de test manuel — Louis

**Terrain : `L_Sandbox_Movement`, couloir E2 (`Y = 0`, écartement 1000, murs de 6000 uu).**
Overlay `F3` : regarder la ligne du wall ride et **la raison de sortie**.

### 1. Le cœur de la demande — viser en wall ride

- [ ] Accroche un mur à gauche, **lâche toutes les touches de déplacement**, tourne la tête à droite
      jusqu'à ~90°. **Tu ne dois PAS décrocher.** Reste accroché, regarde le couloir, reviens.
- [ ] Même chose en tenant `Z`. **Tu ne dois toujours pas décrocher** — c'est le cas qui échouait
      avant (30° suffisaient).
- [ ] Accroche un mur et **tire** sur une cible pendant que tu roules dessus, en visant sur le côté.
      Le mur doit te garder pendant tout le tir.
- [ ] Tourne la tête franchement **vers l'arrière** (plus de 90° de ta direction de course) :
      là, tu dois décrocher. Overlay → raison **`LookAway`**.

### 2. Le décrochage volontaire

- [ ] Mur à gauche, appuie **`D`** : tu décroches. Raison **`InputAway`**.
- [ ] Mur à gauche, appuie **`Z+D`** : tu décroches aussi. **C'est le cas qui tenait à 1 % de marge
      avant** — s'il ne marche pas, c'est `WallRide_DetachDotThreshold` qu'il faut baisser encore.
- [ ] Mur à gauche, appuie **`Z` seul** : tu **restes** sur le mur.
- [ ] Mur à gauche, appuie **`Q`** (vers le mur) : tu **restes** sur le mur.
- [ ] Refais les 4 avec un mur **à droite** (l'autre paroi du couloir), touches inversées.
- [ ] Est-ce que ça sort **au bon moment** ? `WallRide_DetachHoldTime` vaut 0.1 s. Si le décrochage
      te semble mou, dis-le : la fenêtre tirait en réalité à ~0.05 s avant aujourd'hui (bug 2.3b
      corrigé), donc **elle est maintenant deux fois plus longue qu'hier**. C'est le seul endroit où
      le feeling a pu changer sans qu'on le veuille.

### 3. Non-régression — rien d'autre ne doit avoir bougé

- [ ] La vitesse est **strictement constante** sur le mur (`D47`) — overlay, `SPEED` ne bouge pas.
- [ ] L'altitude est **verrouillée**, tu ne descends pas.
- [ ] Le **wall jump** part dans la direction du regard et monte plus haut qu'un saut normal (`D48`).
- [ ] Le **roulis caméra** penche toujours du bon côté (`D49`).
- [ ] Descendre jusqu'au sol en wall ride te repose bien au sol (`D45`) — raison **`Grounded`**,
      pas `Duration`.
- [ ] **Dash pendant un wall ride** : tu décroches, et tu **ne gardes pas** 5625 uu/s.
- [ ] Enchaîner deux murs opposés (E2) marche comme au J6.
- [ ] Tu n'arrives **jamais** à obtenir une sortie `NoWall` en tournant simplement la tête au milieu
      d'un mur. Si tu y arrives, note à quel angle : la trace a une portée de 104 uu et ça voudrait
      dire que tu roules loin de la paroi.

### 4. Chiffres à regarder dans l'overlay

| Ce que tu lis | Ce que ça doit valoir |
|---|---|
| Raison de sortie en tournant la tête à 90° | **rien** — tu es toujours accroché |
| Raison de sortie en regardant derrière | `LookAway` |
| Raison de sortie sur touche opposée | `InputAway` |
| Raison de sortie en bout de mur | `NoWall` |
| Raison de sortie en touchant le sol | `Grounded` |
| `SPEED` pendant le ride | constant au chiffre près |

**Si un seul point de la section 1 échoue, ne tune rien : dis-le.** C'est un bug de logique, pas de
valeur.
