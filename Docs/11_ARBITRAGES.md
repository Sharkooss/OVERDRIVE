# 11 — ARBITRAGES

> **Décisions tranchées définitivement.** Quand deux documents se contredisaient, c'est ici qu'on a choisi.
> Ce document a **autorité immédiatement après `CLAUDE.md`**. Une spec qui le contredit est en tort.
>
> Ne rouvre pas un arbitrage sans une raison de playtest. Écris alors la nouvelle décision ici, datée.

Établi le **2026-08-18** après audit de cohérence de la documentation de préproduction.

---

## D1 — Mort, vies et portée d'une run  🔄 *révisé le 2026-08-18*

**Décision** :

| Portée | Ce qui se passe |
|---|---|
| **Mort en cours de niveau** | Respawn au dernier checkpoint du **niveau courant**. Upgrades **conservés**. `Score_DeathPenalty` appliqué, style reset, chrono qui continue. `LivesRemaining -= 1` |
| **Passage au niveau suivant** | Upgrades **conservés**. Vies **non rechargées** |
| **`LivesRemaining` tombe à 0** | **RUN PERDUE.** Écran `Run Failed`, retour au menu |
| **Retour au menu / nouvelle run** | Reset total : niveau 1, **0 upgrade**, `Run_MaxLives` vies |

`Run_MaxLives = 3` (`07_TUNING §18`).

**Pourquoi** : le GDD se contredisait entre §1 (« à la mort la run est perdue ») et §50
(« les upgrades restent actifs »). Louis a tranché le 2026-08-18 : les upgrades se gardent
**au sein d'une run**, jamais entre deux runs — et un compteur de vies fournit la vraie
condition de défaite qui manquait.

**Conséquence** : le système de vies **entre au scope** (il en était explicitement exclu).
`S_RunState` gagne `LivesRemaining`. Le HUD affiche les vies. `E_GameState.RunFailed` est
désormais atteignable.

---

## D2 — Rendu : ÉCLAIRÉ, Lumen et VSM ACTIFS  🔄 *révisé le 2026-08-18*

**Décision** : le jeu est **éclairé**, en plein jour. **Lumen et Virtual Shadow Maps restent activés.**
Cel-shading obtenu par post-process de **posterisation** sur une scène éclairée normalement,
plus des outlines Sobel. Pas d'Unlit.

Réglages : `r.DynamicGlobalIlluminationMethod=1` · `r.ReflectionMethod=1` · `r.Shadow.Virtual.Enable=1`
— c'est-à-dire **on ne touche à rien**, le template est déjà correct.

Recommandé mais non bloquant : `r.Substrate=0` et Nanite off sur les meshes low-poly
(aucun gain sur de la géométrie à 500 tris, et Substrate complique les matériaux).

**Pourquoi** : la nouvelle DA (`KEYART_REF_02.png`) est une ville blanche en plein soleil avec
des ombres portées franches et un ciel bleu. Ces ombres **sont** le rendu — les simuler en Unlit
coûterait plus cher que de laisser Lumen les calculer, et le résultat serait plat.
La v1 (néon nocturne) justifiait l'Unlit ; la v2 ne le justifie plus.

**Conséquence** : `SPEC_ART_DIRECTION §4 et §9` sont à réécrire (éclairage réel, un `DirectionalLight`
+ `SkyLight` + `SkyAtmosphere` par niveau). Budget perf à surveiller : c'est le nouveau risque n°1.
`BP_LightingRig` pilote désormais de vraies lumières, pas seulement `MPC_Global`.

---

## D3 — Couleurs de gameplay  🔄 *révisé le 2026-08-18*

**Décision** : `Docs/ArtDirection/PALETTE.md` fait autorité sur toute couleur, sans exception.

| Information | Token |
|---|---|
| Laser, dash, melee, traînée — **le joueur** | `OD_Magenta_Player` |
| Surface de wall ride, rail, boost — **la traversée** | `OD_Red_Traversal` |
| Signalétique directionnelle, chevrons | `OD_Purple_Primary` |
| Ennemi (visière, émissif, projectile) | `OD_Amber_Enemy` |
| Heat / overheat / warning | `OD_Amber_Heat` |
| Danger, kill volume | `OD_Red_Danger` |

**Pourquoi la refonte** : la v1 se lisait sur un monde sombre et neutre. La v2 se lit sur un monde
**blanc**, et le décor lui-même emploie du rouge et du violet. On a donc rendu ces deux couleurs
**fonctionnelles** au lieu de les interdire : le rouge marque ce qu'on parcourt, le violet indique
la direction. Le cyan disparaît de la palette ; l'ennemi passe à l'orange, seule teinte chaude
libre qui ressort sur du blanc.

**Conséquence** : toute mention de `OD_Cyan_Accent` ou `OD_Red_Enemy` est caduque.
Sur un fond clair, **une information de gameplay doit être foncée ou très saturée** — l'inverse de la v1.

---

## D4 — Hitboxes ennemis : Sphere Collision, PAS de Physics Asset

**Décision** :
- `SkeletalMeshComponent` en **`NoCollision`**
- **Capsule** = hitbox corps
- **`SphereCollision` nommée `Head`**, attachée au socket de tête = hitbox headshot
- Aucun `PHYS_Enemy_*` à produire

`IsHeadshot()` teste `Hit.Component == HeadSphere`, **jamais** `Hit.BoneName`.

**Pourquoi** : per-bone tracing sur un skeletal mesh en mouvement à 3000 uu/s relatif est coûteux
et imprécis. Une sphère est gratuite, déterministe, et se règle visuellement en 30 secondes.

**Conséquence** : le préfixe `PHYS_` de `06_CONVENTIONS §2` ne sert plus qu'aux boss, s'ils en ont besoin.
`SPEC_COMBAT §3.3 / §5.1 / §13` doivent être réécrits sur ce modèle.

---

## D5 — Mort des ennemis : DISSOLVE, jamais de ragdoll

**Décision** : à la mort, l'ennemi joue un dissolve piloté par `DissolveAmount` sur `M_Toon_Enemy`,
durée `Death_DissolveDuration`, puis est détruit. Aucune simulation physique, à aucun moment,
y compris pour un ennemi tué en vol après un knockback.

**Pourquoi** : `03_SCOPE_LOCK §3` l'avait déjà tranché. Le ragdoll coûte un Physics Asset (que D4 supprime),
du CPU, et produit des poses grotesques en low-poly. Le dissolve est plus stylé et gratuit.

**Conséquence** : `Corpse_LifeSpan` devient **obsolète** — le seul délai est `Death_DissolveDuration`.
Purger toutes les mentions de ragdoll de `SPEC_COMBAT §7 / §8 / §10`.

---

## D6 — Hit-stop : `BPC_HitStop` sur `PC_Overdrive`, point unique

**Décision** : un seul propriétaire, le PlayerController.

```
BPC_HitStop  (sur PC_Overdrive)
  RequestHitStop(RealDuration: float, Dilation: float, Priority: int) → bool bAccepted
```

Règles :
- Si un hit-stop est actif : accepté **uniquement** si `Priority` est strictement supérieure. Sinon ignoré.
- Refusé si moins de `HitStop_MinInterval` s'est écoulé depuis le dernier.
- La durée est en **temps réel** : le timer de sortie utilise un timer non affecté par la dilatation.
- **Exclus du ralenti** : l'audio (`Sound Class` avec pitch non lié au time dilation) et l'UI.

Priorités : `MeleeHit = 5` · `Headshot = 10` · `WallSlam = 20` · `Boss phase = 30`.

**Pourquoi** : `Set Global Time Dilation` est un état global — il ne peut pas avoir trois propriétaires.
Le PlayerController survit au respawn du pawn, contrairement au `BP_PlayerCharacter`.

**Conséquence** : `BPFL_Overdrive::DoHitStop` n'existe pas (une Function Library ne peut pas porter d'état).
À ajouter à `05_ARCHITECTURE §2`. Corriger `SPEC_VFX §4.1` et `SPEC_CAMERA_JUICE §6`.

---

## D7 — Camera shakes : préfixe `CS_`, dossier `Player/Blueprints/Shakes/`

**Décision** : `CS_LaserFire`, `CS_Headshot`, `CS_MeleeHit`, `CS_TakeDamage`, `CS_HardCollision`, `CS_WallSlam`.
`06_CONVENTIONS §2` fait autorité sur les préfixes, sans exception.

**Conséquence** : `BP_Shake_*` et le dossier `Player/Camera/` n'existent pas. Corriger `SPEC_VFX §4.2`.
`Shake_WallSlam` (`07_TUNING §16`) est bien câblé sur `CS_WallSlam` — la clé n'est pas orpheline.

---

## D8 — Polices : Chakra Petch + Rajdhani

**Décision** :

| Asset | Police | Usage | Licence |
|---|---|---|---|
| `F_Overdrive_Display` | **Chakra Petch** | titres, rank, gros chiffres | SIL OFL 1.1 |
| `F_Overdrive_Data` | **Rajdhani** | valeurs, HUD, tableaux | SIL OFL 1.1 |

Font Cache : **Offline** (build reproductible, pas de hitch de cache au premier affichage).

**Pourquoi** : `SPEC_ART_DIRECTION` a autorité sur la DA, et ces deux polices correspondent à
l'esthétique technique/condensée du key art. Les deux sont libres d'usage commercial.

**Conséquence** : `F_Overdrive_Mono` n'existe pas. Corriger `SPEC_UI_HUD §10`.

---

## D9 — `MPC_Global.PlayerSpeed01` : une seule formule

**Décision** :

```
PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                       / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )
```

- **Écrit par** `BPC_MovementState`, et par personne d'autre.
- **Cadence** : timer unique **20 Hz** dans `BPC_MovementState`, qui alimente aussi le vent (`MS_Wind_Speed`).
- **Ne sert PAS au FOV.** Le FOV lit la vitesse brute via `CF_FOVBySpeed` (`SPEC_CAMERA_JUICE §2`).

**Pourquoi** : ce scalaire n'existe que pour les **effets de vitesse** (speed lines, aberration, vignette).
Le normaliser sur `Speed_HardCap` rendrait les effets invisibles avant 5000 uu/s.
Un seul écrivain, une seule cadence, un seul point de maintenance.

**Conséquence** : `BPC_PlayerStats` n'écrit rien dans `MPC_Global`. `WBP_SpeedMeter` passe à 20 Hz.

---

## D10 — `BPI_Damageable` : 4 fonctions, signature définitive

**Décision** :

```
ApplyDamage    (DamageInfo: S_DamageInfo)  → (bKilled: bool, DamageApplied: float)
ApplyKnockback (Impulse: Vector, Instigator: Actor)
IsAlive        ()                          → bool
GetHealthRatio ()                          → float          [pure]
```

`ApplyKnockback` est appelée **après** `ApplyDamage`, par l'appelant, jamais depuis `ApplyDamage`.
Raison : le knockback doit s'appliquer même si la cible est morte (un cadavre projeté reste satisfaisant),
et l'appelant sait s'il veut projeter ou non.

**Conséquence** : supprimer les encarts « divergence de signature » de `SPEC_COMBAT §8` et `SPEC_ENEMIES §2`.
Mettre à jour `05_ARCHITECTURE §2`.

---

## Décisions mineures dérivées

| # | Sujet | Décision |
|---|---|---|
| D11 | `ApplySpeedPenalty` | Nom retenu : **`ApplySpeedPenaltyPercent(Percent, Reason)`** |
| D12 | Dispatcher de pénalité | **`OnSpeedPenaltyApplied(OldSpeed, NewSpeed, Percent, Reason)`** |
| D13 | Stat limitante (écran de résultats) | Fonction **`GetLimitingStat()`**, ordre de départage **TIME > KILLS > STYLE > SPEED** |
| D14 | Vitesse comparée au S Rank | **`AverageSpeed`** (c'est elle qui alimente `ScoreSpeed`). Ajouter `TargetAverageSpeed` à `S_RankThresholds` |
| D15 | Toggle debug | **`IA_DebugToggle`** sur **`F3`** — *révisé au J2 : `F1` est le raccourci Wireframe du viewport éditeur (codé en dur, pas dans un `.ini`), il basculait le rendu en fil de fer à chaque appui. `F3` choisi par Louis, atteinte du jeu vérifiée en PIE. Repli si le viewport réagit aussi : `F5` ou `F6`, tous deux testés libres.* |
| D16 | Restart | **`Hold 0.4 s`**, cible technique **< 0.5 s** entre mort et jouable |
| D17 | Raretés au coffre | Couleurs de `PALETTE.md §5` (Common gris, Rare bleu `#3AA8FF`, Epic violet `#B14BFF`) — **pas** de couleur réservée au gameplay |
| D18 | Lettre de rank | Une couleur par rang (`OD_Rank_D..S`), pas magenta systématique |
| D19 | Catalogue SFX | **`SPEC_AUDIO §2` fait foi.** `SPEC_COMBAT` renvoie vers lui, ne nomme plus de sons |
| D20 | Catalogue VFX | **`SPEC_VFX §2` fait foi.** `SPEC_COMBAT` et `04_ROADMAP` renvoient vers lui |
| D21 | Nom du mesh d'arme | **`SM_Weapon_LaserPistol`** (l'asset existe déjà dans `Art_Source/`) |
| D22 | Zone centrale sanctuarisée (HUD) | **40 %** de la largeur, **40 %** de la hauteur |
| D23 | Plannings dans les specs | Les specs planifient **en semaines**. `04_ROADMAP.md` est seul à planifier en jours |
| D24 | `Corpse_LifeSpan` | **Supprimée** — remplacée par `Death_DissolveDuration` (D5) |
| D25 | Préfixes manquants | Ajouter à `06_CONVENTIONS §2` : `SG_` (SaveGame), `MU_` (Music) |
| D26 | Nom de l'upgrade `MaxSpeed` | **« OVERDRIVE »** (pas « HARD CAP »). `SPEC_LOOT_UPGRADES` fait foi sur les noms d'upgrades |
| D27 | Post-process | **Deux porteurs distincts, pas de doublon.** Les blendables **réactifs** (speed lines, aberration, vignette de dégât, flash de dash, outline) sont sur `BP_PlayerCameraManager` — ils suivent le joueur et lisent `MPC_Global`. Le `PostProcessVolume` du niveau (Unbound, Priority 0) ne porte que les **réglages statiques** d'ambiance : exposure, bloom, fog, color grading. Aucun matériau blendable sur le volume |
| D28 | Coffre de loot | **Écran UI plein écran** (`WBP_LootChest`) après `WBP_Results`. `BP_LootChest` est un objet logique, pas un actor placé. Aucune « salle de fin » à construire dans les 8 niveaux |
| D29 | Upgrades max par run | **7** (6 niveaux + Boss 01 ; pas de coffre après le Boss 02, qui termine la run) |
| D30 | Composant hitbox tête | Nom retenu : **`HeadHitbox`**, attaché au socket `head` |
| D31 | Vies | **3 par run** (`Run_MaxLives`), non rechargeables. Compteur au HUD. 0 vie = `RunFailed` |
| D32 | Personnage visible | **Le jeu reste en vue FPS.** Le personnage complet de la key art sert à l'identité visuelle, aux VFX de traversée et à une éventuelle vue 3ᵉ personne post-v1 — **on ne modélise que les bras + l'arme au MVP** (`03_SCOPE_LOCK §3`) |
| D33 | Ciel & atmosphère | `SkyAtmosphere` + `DirectionalLight` + `SkyLight` par niveau, pilotés par `BP_LightingRig` depuis `PDA_WorldData`. Pas de HDRI, pas de Sky Sphere texturée |

---

## Journal des arbitrages

| Date | # | Décision | Raison |
|---|---|---|---|
| 2026-08-18 | D1–D25 | Établissement initial | Audit de cohérence de préproduction |
| 2026-08-18 | D26–D30 | Complément | Conflits résiduels remontés pendant la propagation |
| 2026-08-18 | **D1, D2, D3 révisés** | **Changement de DA** (`KEYART_REF_02.png`) : ville blanche en plein jour au lieu du néon nocturne → rendu éclairé, palette refondue. Et arbitrage de Louis sur les vies |
| 2026-08-18 | D31–D33 | Ajouts | Conséquences du changement de DA et du système de vies |
