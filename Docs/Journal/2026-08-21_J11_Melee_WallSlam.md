# Journal — 2026-08-21 — J11 — Melee & wall slam

**Branche** : `feat/j11-melee-wallslam`
**Demande de Louis** : *« ok c'est good j'ai testé ça me convient, aller go »* — validation du Test 4
puis feu vert sur le J11 de la roadmap.

> ⚠️ **Le coup n'a jamais été porté.** Tout ce qui suit est prouvé par **mesure sur les instances
> PIE** ou par audit de graphe. La sensation — et le fait même que le melee touche quelque chose —
> est le playtest de Louis (R8 / R10).

---

## Le Test 4 est soldé

`04_ROADMAP.md` portait une modification **non commitée** qui cochait le Test 4, sous un texte qui
disait encore « ⏳ EN ATTENTE DE PLAYTEST », et la ligne 4 du tableau de `10_DEFINITION_OF_DONE §3`
était vide. Louis a tranché manche en main. Les deux documents disent maintenant la même chose :

> **Test 4 ✅ OUI — 2026-08-21.** Hitmarker (visuel), hit-stop 0.06 s (temporel),
> `S_Laser_Hit_Head_01` (sonore). *« C'est good, j'ai testé, ça me convient. »*

Il reste **deux** tests pour la 🚦 **GATE SEMAINE 2** : le **3** (tuer en mouvement > à l'arrêt,
J17) et le **5** (un projectile évitable à 3000 uu/s, J13).

---

## Deux composants autonomes, zéro Blueprint validé réécrit

C'est le patron `BPC_Dash` / `BPC_WallRide` appliqué une fois de plus, et il tient : **aucun des
quatre `BPC_*` de mouvement n'a été ouvert**, `BP_EnemyBase.ApplyDamage` et son `BeginPlay` non plus.

| Blueprint | Ce qui a bougé |
|---|---|
| **`BPC_Melee`** *(neuf)* | `Weapons/Melee/` · 15 variables · 6 fonctions · `EventGraph` 2 nœuds |
| **`BPC_KnockbackReceiver`** *(neuf)* | `Enemies/Base/` · 17 variables · 5 fonctions · `EventGraph` 10 nœuds |
| `BP_PlayerCharacter` | **+3 nœuds** (`IA_Melee` → `Melee.TryMelee`), 62 → **65**. Aucun nœud existant touché |
| `BP_EnemyBase` | **+9 nœuds** (3 events → 3 appels), 10 → **19**. Aucun nœud existant touché |
| `PC_Overdrive` | `NotifyMeleeHit` (8 nœuds) + `HitStopMeleePriority` |

### `BPC_Melee` — le coup

`IA_Melee` était **déjà mappé** sur `RightMouseButton` avec un trigger `Pressed` dans
`IMC_Gameplay.DefaultKeyMappings` depuis le J1. Rien à créer côté input.

- **`MultiSphereTraceByChannel`**, pas d'overlap (`SPEC_COMBAT §6`) : départ **caméra**, direction
  `ControlRotation` **brute**, portée `Melee_Range`, rayon `Melee_Radius`, canal `Weapon`
  (`TraceTypeQuery3`).
- **Dédoublonnage par ACTEUR**, jamais par composant (`§13.5`) : `HitActorsThisSwing` est vidé au
  début du trace, et un ennemi touché à la fois sur sa capsule **et** sur sa `HeadHitbox` ne prend
  les dégâts qu'**une** fois. C'était le piège n°5 de la spec, et il est réel — la `HeadHitbox` du
  J10 bloque le même canal.
- **Un seul hit-stop par swing** (`bHitStopThisSwing`), même en frappant trois ennemis.
  Les dégâts et le knockback, eux, sont à **100 % pour chacun** : frapper un groupe est une
  récompense de positionnement, pas une dégressivité.
- **`AM_Melee_Punch` n'existe pas — et n'était pas nécessaire.** `SPEC_COMBAT §6` prévoit un
  **filet de sécurité** : un `Set Timer by Event(Melee_WindupTime)` armé *en parallèle* de
  l'`AN_MeleeHit`, le premier des deux résolvant le coup. Ici il n'y a que le timer, et
  `bSwingResolved` est déjà en place pour empêcher le double coup le jour où le montage arrivera.
  **Le gameplay ne dépend d'aucun asset d'animation** — c'est écrit dans la spec, ça se vérifie ici.

### `BPC_KnockbackReceiver` — le vol

- **`LaunchCharacter(XY+Z override)`**, jamais `Simulate Physics` (`§7.1`). Aucune simulation
  physique n'existe dans ce projet, à aucun moment.
- **Le Tick ne tourne que pendant le vol.** `SetComponentTickEnabled(false)` au `BeginPlay`,
  `true` au décollage, `false` dès que la fenêtre se ferme. C'est la parade `§13.6` :
  `Event Hit` ne donne pas la vitesse d'**avant** impact, il faut donc l'échantillonner soi-même —
  mais pas au prix d'un tick permanent sur chaque ennemi du niveau.
- **Trois sorties de fenêtre**, toutes câblées : impact mural · `Event Landed` ·
  `Knockback_MaxFlightTime`. Le timer est armé **systématiquement** (`§13.12`) : un ennemi projeté
  ne peut pas rester figé, quoi qu'il arrive.

### Deux choses que je n'ai **pas** faites, et pourquoi

> **`BPC_KnockbackReceiver` lit `EnemyData` lui-même** (cast de son owner vers `BP_EnemyBase` au
> `BeginPlay`) au lieu de se faire alimenter par un `InitFromData` appelé depuis l'hôte. La fonction
> `InitFromData` a été écrite, puis **supprimée**. Motif : l'appeler aurait exigé d'**insérer un
> nœud dans le `BeginPlay` validé de `BP_EnemyBase`**, c'est-à-dire de toucher une chaîne d'exec
> existante pour économiser un cast. Le cast est moins cher que le risque.

> **`bNotifyRigidBodyCollision` et `bUseCCD` sont posés DANS le graphe**, au `BeginPlay`, et pas en
> propriété sur la capsule. C'est `12_PIEGES §5.15`/`§5.56` : un défaut de composant hérité ne
> survit pas forcément à une recompilation, et il n'y a **aucun** signal quand il disparaît.
> Les deux ont été **relus sur l'instance PIE** : `true` / `true`. Sans le premier, `Event Hit` ne
> partirait jamais et le wall slam n'existerait pas (`§13.7`) ; sans le second, un knockback à
> 3500 uu/s traverserait un mur fin (`§13.8`).

---

## `D60` — deux clés disaient la même chose

`SPEC_COMBAT §7.2` gardait le décollage avec **`WallSlam_MinImpactSpeed`** (1500).
`07_TUNING §13` définit **`Knockback_MinImpulse`** (800) comme littéralement *« sous ce seuil,
l'ennemi est bousculé mais n'entre pas dans l'état en vol slammable »* — le même test, une autre
valeur, un autre nom.

Deux vérités concurrentes sur la même question : exactement ce que **R3** existe pour empêcher, et
la même famille que le `Land_HeavySpeedThreshold` que j'avais failli inventer au J11-audio.
Tranché, écrit dans les deux documents :

> **Décollage → `Knockback_MinImpulse` (800). Dégâts muraux → `WallSlam_MinImpactSpeed` (1500).**
> Les deux clés sont désormais distinctes **et** lues par du code.

Conséquence de tuning à surveiller au playtest : avec `Melee_Knockback` = 3500 et un Grunt à
`KnockbackResistance = 0`, l'impulsion finale vaut ~3512 — très au-dessus des deux seuils. C'est le
**Tank** (J17) qui exercera vraiment `Knockback_MinImpulse`.

---

## Vérifié en PIE, sur les instances réelles

| Relevé | Valeur |
|---|---|
| `BP_PlayerCharacter_C_0.Melee` — les 8 clés | `60 · 220 · 60 · 0.55 · 0.06 · 3500 · 300 · 0.06` |
| `…Melee.bRefsCached` / `bCanMelee` | **`true`** / `true` |
| `…Melee.cachedPC` | **`PC_Overdrive_C_0`** (l'instance réelle, pas `None`) |
| `BP_Enemy_Grunt_C_0.KnockbackReceiver` — les 7 clés | `800 · 1500 · 200 · 0.08 · 0.4 · 1.2 · 0.8` |
| `…KnockbackReceiver.knockbackResistance` / `bCanbeWallSlammed` | **`0` / `true`** — **relus depuis `DA_Enemy_Grunt`** |
| `…KnockbackReceiver.bRefsCached` | **`true`** → le cast vers `BP_EnemyBase` a réussi |
| `…CollisionCylinder.bodyInstance.bNotifyRigidBodyCollision` | **`true`** |
| `…CollisionCylinder.bodyInstance.bUseCCD` | **`true`** |
| `PC_Overdrive.hitStopMeleePriority` / `hitStop_TimeDilation` | **`20`** / `0.05` |

`bRefsCached = true` des **deux** côtés est le relevé qui compte : il prouve que `CacheRefs` s'est
exécutée jusqu'au bout, donc que les deux casts ont abouti et que les valeurs affichées viennent
bien du DataAsset et pas d'un défaut.

**Audit de graphe — 13 graphes, `warnings_as_errors` vert partout, `orphans: []` partout :**

| Blueprint | Graphes (nœuds) |
|---|---|
| `BPC_Melee` | `CacheRefs` 9 · `TryMelee` 13 · `ResolveSwing` 6 · `DoMeleeTrace` 22 · `ApplyMeleeHit` 24 · `EndMeleeCooldown` 2 · `EventGraph` **2** |
| `BPC_KnockbackReceiver` | `CacheRefs` 18 · `ReceiveKnockbackImpulse` 22 · `OnOwnerHit` 32 · `OnOwnerLanded` 4 · `EndKnockbackWindow` 6 · `EventGraph` 10 |
| `PC_Overdrive` | `NotifyMeleeHit` 8 |

Racines d'exec, une par une : `BPC_Melee` → **1** (`BeginPlay`) · `BPC_KnockbackReceiver` → 2
(`BeginPlay` + `Tick`, les deux connectées et voulues) · `BP_EnemyBase` → 4 (`BeginPlay`,
`ApplyKnockback`, `Hit`, `OnLanded`, les quatre connectées) · `PC_Overdrive` → 1.

**Non-régression de l'input** — contrôlée **sur les pins**, pas au DSL relu : `BP_PlayerCharacter`
passe de **62 à exactement 65** nœuds, et les 3 sont ceux que j'ai créés. Aucun nœud existant n'a
été supprimé ni recâblé, parce que le graphe n'a **jamais** été réécrit : uniquement `create_node` +
`connect_pins`. Le nœud `TryMelee` a ses deux entrées connectées (`execute` ← `IA_Melee.Triggered`,
`self` ← `GetMelee`).

---

## Ce qui n'est PAS fait, et pourquoi

- **`StopLogic` / `ResumeLogic`** — **aucun `AIController` n'existe** avant le J13. La ligne reste
  dans `SPEC_COMBAT §7.2` parce qu'elle redeviendra vraie.
- **`PlayStagger()`, `PlayBounce()`, `A_Enemy_GetUp`** — les trois animations n'existent pas (le set
  du Grunt est `Idle` / `Walk` / `Run` + 3 clips de charge). **Les branches correspondantes sont en
  place et ferment proprement la fenêtre** ; il ne leur manque que l'habillage. J13.
  `Knockback_RecoverTime` passe donc **`INACTIVE`** dans `07_TUNING §12` — elle n'est lue par
  personne, et je préfère l'écrire que laisser croire qu'elle règle quelque chose (`§6.24`).
- **SFX de swing** — **aucun WAV de melee** parmi les 50 importés. Je n'ai **pas** créé de tableau
  `SoundBase[]` vide pour la forme : une clé que rien ne remplit est exactement le piège `§6.24`.
  Le coup a déjà un retour sonore, celui de l'ennemi (`EnemyData.HitSFX`, câblé au J10). J14.
- **`AM_Melee_Punch` + slot Upper Body**, VFX d'impact, son de wall slam → J14.
- **Un ennemi tué au melee est détruit, il ne vole pas.** `BP_EnemyBase.ApplyDamage` fait
  `DestroyActor` depuis le J10 ; le *dissolve en vol* de `§7.4` arrive avec le dissolve tout court
  (J13). Sans conséquence aujourd'hui : `Melee_Damage` = 60 contre 100 pv, **un coup ne tue pas**,
  donc le knockback part toujours. C'est le wall slam qui achève.

---

## Décisions prises

| Décision | Où |
|---|---|
| **`D60`** — `Knockback_MinImpulse` garde le décollage, `WallSlam_MinImpactSpeed` les dégâts muraux | `11_ARBITRAGES`, `SPEC_COMBAT §7.2`, `07_TUNING §12`/`§13` |
| Les clés melee vivent en `Instance Editable` sur les composants (pas de DataAsset melee) | `07_TUNING §12`, précédent `BPC_Heat` (J9) |
| Le receiver lit `EnemyData` lui-même plutôt que d'insérer un nœud dans le `BeginPlay` de `BP_EnemyBase` | ce journal, `SPEC_COMBAT §7.2` |
| Pas de `SetMovementMode(Falling)` : `CMC::HandlePendingLaunch` le fait déjà | `SPEC_COMBAT §7.2` |
| `HitStopMeleePriority` **sans underscore**, pour que le `type_id` du getter reste devinable | `07_TUNING §16`, `12_PIEGES §5.71` |

## Valeurs modifiées

**Aucune valeur existante touchée.** Toutes les clés de `07_TUNING §12`/`§13` sont posées à leur
valeur documentée. **Ajout** : `HitStopMeleePriority` = 20 sur `PC_Overdrive` (`FIXE`, barème
`SPEC_COMBAT §5.4`). **Changement de statut** : `Knockback_RecoverTime` → `INACTIVE`,
`Melee_SelfPropulsion` annotée « lue par personne ».

## Bugs / pièges rencontrés

Quatre pièges neufs, tous de la même famille : **`read_graph_dsl` produit une vue, pas une source.**

| Piège | Gravité | Consigné |
|---|---|---|
| Les accesseurs de variable relus (`\|GetHitStop_TimeDilation`) **ne se réécrivent pas** — le vrai id supprime les underscores *et* minusculise les mots courts (`GetIsAirbornefromKnockback`, `GetCanbeWallSlammed`) | 💀 | **`5.71`** |
| Le lecteur affiche des id **de moteur** là où le graphe contient un nœud **de projet** : `Game\|Damage\|ApplyDamage` pour `Class\|BPIDamageable\|ApplyDamage`, `Game\|GetPlayerCameraManager` pour `Class\|PlayerController\|GetPlayerCameraManager` | 🔴 | **`5.72`** |
| `CallFunction\|X` n'est valable que **chez soi** ; ailleurs c'est `Class\|<ClasseSansUnderscores>\|X` | 🟠 | **`5.73`** |
| `get_node_type_pins` matérialise sa sonde **dans le graphe de contexte** | 🟠 | **`5.74`** |
| `write_graph_dsl` a réinstallé un `EventTick` **vide** sur `BPC_Melee` — purgé, le composant ne tick pas | 🔴 | `5.66`, déjà consigné |
| Le premier argument positionnel d'un appel de fonction se branche sur `self`, pas sur le 1ᵉʳ paramètre | 🔴 | `5.68`, déjà consigné |
| **Complément à `5.70`** : l'`UserConstructionScript` n'est **pas** un refuge fiable pour sonder — il peut avoir été empoisonné plus tôt. Seul un graphe créé exprès (puis supprimé) marche | 💀 | `5.70` amendé |

Le `5.66` mérite une note : l'`EventTick` fantôme posé sur `BPC_Melee` **compilait sans warning** et
n'aurait rien fait de visible — il aurait juste fait ticker un composant qui n'en a aucun besoin, sur
le pawn du joueur, pour toujours. C'est le contrôle « racines d'exec » qui l'a trouvé, pas la
compilation.

## Échafaudages

**Aucun posé de la journée.** Aucun `PrintString`, aucun mapping temporaire, aucune valeur gonflée.
Deux graphes de sonde jetables (`ZZ_ProbeTmp` sur `BP_PlayerCharacter`, `ZZ_Probe3` sur
`BPC_KnockbackReceiver`) ont été créés pour contourner `5.70` puis **supprimés** — `list_graphs`
relu après coup sur les deux Blueprints : ni l'un ni l'autre n'apparaît.

## Vérifications de fin de journée

- [x] Tous les BP recompilés en `warnings_as_errors` — zéro warning
- [x] Assets sauvegardés, puis relus **sur disque** (`git status`) et **en PIE** (instances)
- [x] Zéro nœud orphelin sur les 13 graphes, racines d'exec comptées une par une
- [x] Non-régression de l'input contrôlée sur les pins (62 → 65, +3 voulus)
- [x] Pièges consignés (4 neufs, 1 amendé)
- [ ] **3 minutes de jeu réel — PAS FAIT : c'est le playtest de Louis** (R8)
- [ ] **Commit — EN ATTENTE de son retour** (R10)

> ⚠️ **Le tir headless reste impossible dans cet éditeur.** `SlateInspector.Windows("list")` rend
> `[]`, comme au J10bis. Je n'ai donc **pas** pu déclencher un seul coup de melee : ni vol, ni impact
> mural, ni dégât de slam n'ont été mesurés. Tout ce qui précède prouve que **le câblage est en
> place et initialisé** ; rien ne prouve encore qu'il **frappe**.

---

# Addendum — 1ᵉʳ playtest de Louis

**Retour** : *« l'ennemi part bien quand on le tape, mais premier problème il va beaucoup trop loin
c'est abusé. J'aimerais aussi que sa vitesse ne soit pas constante, je veux un vrai impact quand je
tape : donc il prend très vite de la vitesse, mais l'ennemi est grand et lourd donc il réduit très
vite sa vitesse et freine. Genre avoir un game feel qu'on tape fort un truc lourd — là on a la
sensation de frapper doucement un truc d'un poids plume. Sinon à part ça tout fonctionne, on peut
kill quand il touche un mur et tout ça marche bien. »*

**Le diagnostic était dans le moteur, pas dans une valeur.** `LaunchCharacter` pose une vélocité et
`CMC.FallingLateralFriction` vaut **0** par défaut : en `MOVE_Falling`, sans input, rien ne freine
la composante horizontale. L'ennemi partait à 3500 uu/s et gardait **exactement** 3500 jusqu'au sol.
« Poids plume » est la description littérale du profil, pas une impression.

## `D61` — la traînée fait le poids

- Nouvelle clé **`Knockback_AirDrag`** = **2.5 /s**, poussée dans `CMC.FallingLateralFriction` au
  décollage et **restaurée** à sa valeur d'origine (mémorisée au `BeginPlay`) à la fermeture de la
  fenêtre. Le CMC applique alors `Velocity -= Friction × Velocity × dt` : décroissance
  **exponentielle**, donc **perte maximale juste après l'impact** — précisément la courbe demandée.
- **`Melee_Knockback` 3500 → 2800.**
- **`WallSlam_MinImpactSpeed` 1500 → 900** : avec la traînée, la vitesse tombe sous 1500 en 0.17 s.
  Laisser le seuil à 1500 aurait réduit la fenêtre de slam à ~330 uu et **cassé la seule chose que
  Louis a validée**. À 900, la fenêtre fait ~760 uu.

Profil résultant (calcul, **pas** mesure) : 2800 uu/s à l'impact → ~600 uu/s après 0.6 s,
**~875 uu de vol** au lieu de ~2100. Dégâts de slam à ~1500 uu/s : 120 pv sur un Grunt déjà à 40.

> **Aucun autre choix n'a été touché** : direction caméra, `bZOverride`, la fenêtre de vol, les trois
> sorties, le dédoublonnage, le hit-stop unique par swing, `D60`. Une seule cause, trois valeurs.

## `D62` — et là, le vrai piège de la journée

Les nouvelles valeurs étaient **écrites et relues correctes** sur le CDO du composant **et** sur le
template SCS de `BP_EnemyBase`. En PIE, les 6 Grunts lisaient encore **`AirDrag = 0`** et
**`MinImpactSpeed = 1500`**.

La sonde qui a tranché : lire la propriété sur les acteurs du **monde éditeur** (`find_actors`,
filtrés *hors* `UEDPIE`). Les six portaient `0` / `1500` **chacun**. Un acteur déjà posé **fige sa
propre copie** des défauts d'un composant au moment où on le lui ajoute, et **PIE clone le monde
éditeur, pas le CDO**. `save_assets` sur la map puis `load_level` n'ont rien changé — la sauvegarde a
même *persisté* les valeurs périmées. C'est `12_PIEGES §5.42` **un cran plus profond** : quatre
copies possibles du même défaut, et c'est la plus profonde qui gagne.

Ce qui rendait le symptôme traître : **`BPC_Melee` sur le joueur prenait bien sa nouvelle valeur.**
Un composant sur deux obéissait.

**La parade était déjà écrite dans la doc, et je ne l'avais pas appliquée.**
`10_DEFINITION_OF_DONE §5` : *« un ennemi est fini si ses stats sont dans son `DA_Enemy_*`, pas dans
le BP »*. Les clés de knockback **sont** des stats d'ennemi. Corrigé :

- **6 propriétés ajoutées à `PDA_EnemyData`** (`08_DATA_SCHEMAS §3`) : `KnockbackAirDrag`,
  `KnockbackMinImpulse`, `KnockbackMaxFlightTime`, `WallSlamMinImpactSpeed`, `WallSlamDamage`,
  `WallSlamDamagePerSpeed`. Renseignées dans `DA_Enemy_Grunt`.
- `CacheRefs` les lit au `BeginPlay` (20 → **32** nœuds, 0 doublon).
- Les variables du composant deviennent des **caches non `Instance Editable`**, catégorie
  `Knockback|Data` : plus personne ne peut croire qu'on les règle dans l'inspecteur.
- `WallSlam_MaxNormalZ` **reste** sur le composant : c'est de la géométrie, pas une stat.

**Effet de bord, et il est bon** : la traînée est désormais **per-ennemi**. Le Tank (J17) freinera
plus fort que le Grunt sans une ligne de code — c'est littéralement « grand et lourd ».

**Prouvé en PIE après correction** — `BP_Enemy_Grunt_C_0` et `_C_1` :
`airDrag 2.5 · minImpulse 800 · maxFlightTime 1.2 · minImpactSpeed 900 · slamDamage 200 ·
damagePerSpeed 0.08 · bRefsCached true`. Les valeurs viennent de `DA_Enemy_Grunt`.

## Second piège : un graphe empilé qui compilait vert

`ReceiveKnockbackImpulse` est monté à **46 nœuds** après une réécriture — **chaque nœud en double**
(`LaunchCharacter: 2`, `Branch: 2`, …), seuls les 3 nœuds neufs en un exemplaire. C'est `2.2c` :
une écriture qui a échoué en cours de route n'a pas purgé, la suivante a empilé.
**L'ennemi aurait été lancé deux fois par coup, et le Blueprint compilait sans un warning.**

Le contrôle d'orphelins ne le voit **pas** (la chaîne empilée est reliée à elle-même). Ce qui l'a vu :
un **comptage par `type_id`**. Purge à 1 nœud (`FunctionEntry`) puis réécriture → **25 nœuds,
0 doublon**. Contrôle ajouté au réflexe de fin d'écriture : *après tout `write_graph_dsl`, tallier
les `type_id` — tout compte > 1 sur un nœud censé être unique est un empilement.*

## Valeurs modifiées

| Clé | Avant | Après |
|---|---|---|
| `Melee_Knockback` | 3500 | **2800** |
| `WallSlam_MinImpactSpeed` | 1500 | **900** |
| `Knockback_AirDrag` | *(n'existait pas)* | **2.5** |

## Pièges consignés

| Piège | Gravité | Consigné |
|---|---|---|
| Un acteur posé fige sa copie des défauts d'un composant ; PIE clone le monde éditeur | 💀 | **`5.75`** |
| `Class\|X\|Set<Prop>` : le `self` doit être passé en **keyword**, sinon le 1ᵉʳ positionnel va sur la valeur | 🔴 | `5.68`, famille déjà consignée |
| Graphe empilé après une écriture avortée — invisible au contrôle d'orphelins | 💀 | `2.2c`, complété du contrôle par tally de `type_id` |

---

# Addendum 2 — 2ᵉ playtest

**Retour** : *« non là il ne prend pas assez de recul, j'aimerais qu'il aille quand même plus loin,
là c'est trop peu. Par contre j'ai un bug : quand je l'envoie à la verticale, genre je regarde le
ciel, il part méga super haut !! C'est un gros souci. »*

## `D63` — le bug et le manque de portée avaient la même cause

`ApplyMeleeHit` construisait `Impulse = Camera.ForwardVector × Melee_Knockback + Up × KnockbackUp`,
exactement comme `SPEC_COMBAT §7.2` le prescrivait. **Nez au zénith, `Camera.ForwardVector = (0,0,1)` :
toute l'impulsion devient verticale**, soit `2800 + 300 = 3100 uu/s` vers le haut. Et `D61` ne freine
que le **latéral** (`FallingLateralFriction`) — la verticale n'a que la gravité pour la retenir :

```
apex = v² / (2g) = 3100² / (2 × 980) ≈ 4900 uu  ≈ 49 mètres
```

Ce n'était pas un cas limite, c'était **la formule de la spec appliquée littéralement**. Et c'est la
même cause qui rendait le recul court : à chaque fois qu'on regardait un peu vers le haut, une part
de l'impulsion partait en altitude au lieu d'aller loin.

**Correctif : le pitch sort de la direction.**
`Dir = MakeRotator(Pitch = 0, Yaw = ControlRotation.Yaw, Roll = 0).ForwardVector`.
`Melee_KnockbackUp` (300) devient **la seule source de vertical**, donc le temps de vol est constant
(~0.61 s, apex ~46 uu) **quel que soit le regard**.

J'ai écarté le clamp de pitch (borner à ±15/25°) : il déplace le problème au lieu de le supprimer —
à 4500 uu/s, même 25° donnent encore ~2 000 uu de vertical, et il aurait fallu recalibrer l'angle à
chaque changement de `Melee_Knockback`. **Le yaw seul règle le cas par construction, pas par dosage.**

> **Pourquoi c'est gratuit en gameplay** : viser en l'air n'apportait rien. `SPEC_COMBAT §7.3` exclut
> déjà sols et plafonds du wall slam via `WallSlam_MaxNormalZ` — **un mur se vise au yaw**.
> Et le **trace** reste sur la caméra complète, pitch compris : on frappe toujours un ennemi en
> contrebas ou en surplomb. C'est la **direction de projection** qui devient horizontale, pas la
> portée du coup.

## La portée

Toute l'impulsion allant désormais dans l'horizontale, **`Melee_Knockback` passe à 4500**.

| | 1ᵉʳ playtest | 2ᵉ playtest | Maintenant |
|---|---|---|---|
| `Melee_Knockback` | 3500 | 2800 | **4500** |
| Direction | caméra complète | caméra complète | **yaw seul** |
| Vitesse au décollage | 3500 | 2800 | 4500 |
| Vitesse à l'atterrissage | **3500** (aucun freinage) | ~600 | **~980** |
| Portée horizontale | ~2100 uu | ~875 uu | **~1400 uu** |
| Apex en regardant le ciel | ~7 400 uu | **~4 900 uu** | **46 uu** |

L'aller-retour 3500 → 2800 → 4500 n'est pas une hésitation : entre les deux, `D63` a changé ce que
la valeur *signifie*. À 2800 avec le pitch, une part variable partait vers le haut ; à 4500 sans le
pitch, les 4500 vont **entièrement** dans la distance, et le freinage reste très lisible
(4500 → 980, soit −78 % sur le vol).

Wall slam : la vitesse ne passe sous `WallSlam_MinImpactSpeed` (900) qu'à t ≈ 0.64 s, c'est-à-dire
**après l'atterrissage**. Toute la trajectoire est donc slammable — la mécanique que Louis a validée
devient plus facile, pas plus dure.

## Vérifié en PIE, sur les instances

`BP_PlayerCharacter_C_0.Melee` → `meleeKnockback 4500 · meleeKnockbackUp 300 · meleeRange 220 ·
bRefsCached true`
`BP_Enemy_Grunt_C_0.KnockbackReceiver` → `airDrag 2.5 · minImpactSpeed 900 · maxFlightTime 1.2`

`ApplyMeleeHit` : purgé à 1 nœud puis réécrit → **26 nœuds**, tally par `type_id` propre (seul
doublon : les 2 multiplications vectorielles, qui sont les deux termes de l'impulsion), 0 orphelin,
compilation `warnings_as_errors` verte.

> ⚠️ **Toujours aucun coup porté par un outil.** Les chiffres de portée et d'apex ci-dessus sont des
> **calculs** à partir des valeurs relues en PIE, pas des mesures en jeu. C'est la manche de Louis
> qui tranche.

---

# Addendum 3 — 3ᵉ playtest

**Retour** : *« ok c'est mieux, il faudrait encore un poil plus de force quand même, là c'est trop
peu. Et aussi un peu plus de verticalité, il rase un peu trop le sol quand on vise haut. »*

## `D64` — le pitch revient, mais sur Z seulement

La seconde demande rouvre `D63`, et il fallait le dire au lieu de l'appliquer en silence : j'avais
supprimé **toute** influence du regard vertical, et c'était trop absolu. Ce que `D63` devait tuer,
ce n'est pas la verticalité — c'est le fait que **le pitch pilotait la direction**, donc une
impulsion non bornée sur un axe sans traînée.

Le pitch alimente désormais un **terme additif sur Z**, jamais la direction :

```
Lift    = Melee_KnockbackPitchBoost × sin(Clamp(NormalizeAxis(Pitch), 0°, 90°))
Impulse = MakeVector(Dir.X × Melee_Knockback, Dir.Y × Melee_Knockback, Melee_KnockbackUp + Lift)
```

**Les deux axes sont indépendants**, et c'est toute la différence avec la formule d'origine :

- viser haut **ajoute** de la hauteur sans jamais **retirer** de l'horizontale ;
- le vertical est **borné par une clé**, pas par un angle à recalibrer — monter `Melee_Knockback`
  ne peut plus faire décoller personne, ce qui était le vrai défaut de la formule d'origine ;
- viser **vers le bas** n'ajoute rien (`Clamp` à 0) : on n'enterre pas un ennemi dans un sol qui,
  de toute façon, ne slamme pas (`WallSlam_MaxNormalZ`).

| Visée | `Z` | Apex | Temps de vol |
|---|---|---|---|
| à plat | 300 | 46 uu | 0.61 s |
| 45° | 654 | 218 uu | 1.33 s |
| zénith | **800** | **326 uu** | 1.63 s |
| *zénith, formule d'origine* | *3100* | ***4900 uu*** | *6.3 s* |

## La force

**`Melee_Knockback` 4500 → 5500** → portée ≈ **1720 uu** à visée horizontale (contre 1400).
Vitesse à l'atterrissage ≈ 1200 uu/s : le freinage reste très lisible (−78 %).

Historique complet de la clé, et ce n'est pas de l'hésitation :
`3500` (trop loin) → `2800` (pas assez) → `4500` → `5500`. Entre le 2ᵉ et le 3ᵉ, **`D63` a changé
ce que la valeur signifie** — avec le pitch dans la direction, une part variable partait vers le
ciel ; sans lui, la clé va entièrement dans la distance.

## Un piège d'écriture attrapé au contrôle, pas en jeu

Première version : `Impulse = Dir × K + Up × (KnockbackUp + Lift)`. Le contrôle par tally a montré
**deux** `Math|Vector|vector+vector` alors que je n'attends qu'une addition vectorielle. En ouvrant
les pins : le second avait `A: Float (double)` et `B: Float (double)` — un `type_id` **vectoriel**
avec des pins **scalaires**, alimentant un `vector*vector` dont le pin `B` est déclaré `Vector`.
Une promotion `float → (f,f,f)` traînait quelque part.

Comme `Up = (0,0,1)`, le résultat était **peut-être** juste. Ça compilait, et personne ne l'aurait
vu en jeu. « Peut-être » n'est pas un diagnostic (**R12**) : réécrit avec un **`MakeVector`
explicite** — 3 entrées scalaires, une sortie Vector, plus aucune promotion à interpréter.
Vérifié après coup : 3 `float*float`, 1 `float+float`, 1 `MakeVector`, **zéro nœud vectoriel à pins
flottants**. Consigné en **`12_PIEGES §5.76`**.

## Vérifié en PIE

`BP_PlayerCharacter_C_0.Melee` → `meleeKnockback 5500 · meleeKnockbackUp 300 ·
meleeKnockbackPitchBoost 500 · meleeDamage 60 · meleeRange 220 · bRefsCached true`.
`ApplyMeleeHit` : purgé à 1 nœud puis réécrit → **34 nœuds**, compilation `warnings_as_errors` verte.

> ⚠️ Apex, portées et temps de vol du tableau sont des **calculs** à partir des valeurs relues en
> PIE. Toujours aucun coup porté par un outil.

---

# Addendum 4 — 4ᵉ playtest : la forme de la courbe

**Retour**, croquis à l'appui : *« la courbe que l'éjection fait n'est pas bonne. À gauche c'est ce
que tu m'as fait : il part fort à l'horizontale puis ralentit et monte, ensuite redescend d'un coup.
Moi je voudrais vraiment plus dans le style de [droite], en mode une parabole. Et en terme de vitesse
il part fort et ralentit progressivement. »*

## Le croquis était un diagnostic, pas une préférence

La bosse tardive suivie d'une **chute verticale** est la signature exacte d'un seul défaut :
**la traînée horizontale est trop forte par rapport au temps de vol.**

```
constante de temps horizontale = 1 / Knockback_AirDrag = 1 / 2.5 = 0.40 s
temps de vol (visée haute)     = 1.63 s
```

L'horizontale perdait **87 %** de sa vitesse au premier quart du vol. Concrètement : l'ennemi part
vite, s'arrête en X, **finit de monter sur place**, puis retombe à la verticale. Tracé en `y(x)`,
ça donne une montée qui s'accélère puis un trait vertical — le dessin de gauche, trait pour trait.

**`D61` n'était pas faux, il était mal dosé.** La traînée est bien ce qui donne le poids ; c'est son
rapport au temps de vol qui décidait de la *forme*. Règle posée dans `07_TUNING §13` :

> **`1 / Knockback_AirDrag ≥ t_air`** — sinon la trajectoire cesse d'être une parabole.

## `D65` — cinq valeurs, une seule idée

| Clé | Avant | Après | Pourquoi |
|---|---|---|---|
| `Knockback_AirDrag` | 2.5 | **0.6** | `1/k = 1.67 s ≥ 1.22 s` de vol → l'horizontale survit à tout le vol |
| `Melee_KnockbackUp` | 300 | **600** | à 300, apex 46 uu : **l'arc était invisible**, ça rasait le sol |
| `Melee_Knockback` | 5500 | **2700** | avec 4× moins de traînée, il en faut 2× moins pour aller **plus loin** |
| `Knockback_MaxFlightTime` | 1.2 | **2.5** | anti-blocage, pas un curseur : il doit dépasser le vol le plus long (2.24 s) |
| `WallSlam_MinImpactSpeed` | 900 | **700** | doit rester sous la vitesse de fin de vol la plus basse (702) |

> ⚠️ **`Melee_Knockback` qui tombe de 5500 à 2700 n'est PAS une perte de force.** La portée dépend
> de la clé **et** de la traînée : à `k = 2.5` il fallait 5500 pour 1720 uu ; à `k = 0.6`, **2700
> suffisent pour 2342 uu**. C'est le piège de lecture de cette clé, noté dans `07_TUNING §12`.

**Profil calculé à partir des valeurs relues en PIE :**

| Visée | Temps de vol | Apex | Portée | Vitesse à l'atterrissage |
|---|---|---|---|---|
| à plat | 1.22 s | 184 uu | **2342 uu** | 1295 uu/s (**48 %** restants) |
| 45° | 1.95 s | 464 uu | 3100 uu | 840 uu/s (31 %) |
| zénith | 2.24 s | 617 uu | 3330 uu | 702 uu/s (26 %) |

C'est **48 % de vitesse horizontale restante à l'atterrissage** contre 13 % avant : la trajectoire
avance jusqu'au bout, donc l'arc est une vraie parabole, et le ralentissement reste très lisible
(−52 %) — *« il part fort et ralentit progressivement »*.

**Aucun graphe modifié** : `D65` est entièrement du tuning. Les cinq valeurs sont dans
`DA_Enemy_Grunt` (traînée, fenêtre, seuil de slam) et sur `BPC_Melee` (norme, plancher vertical).

## Vérifié en PIE

`BP_PlayerCharacter_C_0.Melee` → `meleeKnockback 2700 · meleeKnockbackUp 600 ·
meleeKnockbackPitchBoost 500`
`BP_Enemy_Grunt_C_0.KnockbackReceiver` → `airDrag 0.6 · maxFlightTime 2.5 · minImpactSpeed 700 ·
slamDamage 200 · damagePerSpeed 0.08 · bRefsCached true`

> ⚠️ Le tableau de profil est **calculé**, pas mesuré : je ne peux toujours pas porter un coup.
> C'est la manche de Louis qui dit si la parabole est la bonne.

---

# Addendum 5 — 5ᵉ playtest : portée du melee + polish HUD

**Retour** : *« ok très bien, là le recul et tout est good. Maintenant le sphere trace, donc le coup
de melee, il faudrait qu'il ait plus de range et une hitbox plus grosse, car là il faut vraiment
être collé — avec la vitesse ça casse un peu le rythme. Ensuite rajoute juste un fade in / fade out
sur les hit markers et kill markers. Et dans la progression de la barre de heat en bas à gauche,
anime un peu la progression pour ne pas monter ou descendre d'une barre d'un coup : qu'elle se
charge avec des petites animations de remplissage, que ce soit plus sympa visuellement. »*

> ✅ **Le knockback est validé** (`D61` → `D65`). Cette passe n'y touche pas d'une virgule.

## 1. Portée du melee — du tuning pur

| Clé | Avant | Après |
|---|---|---|
| `Melee_Range` | 220 | **400** |
| `Melee_Radius` | 60 | **120** |

La portée réellement utile n'est pas `Range` seule mais **`Range + Radius + rayon de la cible`** :
elle passe de **~350 uu à ~590 uu**. À 2000 uu/s, 350 uu se franchissent en 0.17 s — d'où le
*« il faut être collé »*. **Aucun graphe modifié.**

> ⚠️ **Ce que grossir le rayon coûte** : `DoMeleeTrace` ne teste **aucune occlusion** — c'est le même
> choix qu'au J8nonies pour le laser, et il est assumé. À très grand rayon on finirait par frapper
> à travers une cloison fine. **120 est le plafond raisonnable** sur un module de grille ; au-delà
> il faudrait une garde d'occlusion, donc de la complexité que `D53`/J8nonies ont justement retirée.

## 2. `D66` — fondus du hitmarker, remplissage continu de la jauge

**Aucun toolset MCP ne crée de `WidgetAnimation`** — même famille que le `SoundCue` du J11 et
l'`AnimBlueprint` du J10. Les deux effets sont donc pilotés par le **`Tick` du widget**, ce qui rend
la même chose, se règle par une clé de tuning, et se remplacera par une animation timeline le jour
venu **sans toucher aux appelants**. `ShowHitmarker(bHeadshot, bKilled)` et
`SetHeat(Ratio, HeatValue, bWarning, bOverheat, StylePenalty)` gardent leur signature exacte.

### `WBP_Hitmarker` — fondu d'entrée et de sortie

- 4 variables neuves : `MarkerElapsed`, `MarkerDuration`, `bMarkerActive` (état) et
  **`HitmarkerFadeInTime`** = 0.03 s (`Instance Editable`).
- `ShowHitmarker` (36 nœuds) : arme l'état et pose `RenderOpacity = 0` au lieu d'armer un timer de
  masquage. Couleurs, échelles et angle des 3 paliers **inchangés**.
- `EventTick` (24 nœuds) : `alpha = e/FadeIn` en montée, `(d−e)/(d−FadeIn)` en descente, clampé
  `[0,1]`, `SafeDivide` des deux côtés (aucune division par zéro possible même si la clé passe à 0).
  À la fin : `RenderOpacity = 0`, `HideHitmarker()`, `bMarkerActive = false`.
- Le `HideTimer` n'est plus armé — le Tick est le seul pilote, il n'y a donc pas deux horloges
  concurrentes sur le même effet.

> ⚠️ **Si le fondu ne se voit pas, le curseur n'est pas `HitmarkerFadeInTime`** : à
> `Hitmarker_BodyDuration = 0.12 s`, il ne reste que **0.09 s** de sortie, soit ~5 images.
> Je n'ai **pas** touché aux durées : ce sont elles que Louis a validées au J10bis.

### `WBP_HeatBar` — la jauge se remplit au lieu de sauter

- 2 variables neuves : `DisplayRatio` (état) et **`HeatBarFillSpeed`** = 9.0 (`Instance Editable`).
- **`SetHeat` n'a pas été touchée.** Elle continue d'écrire `CurrentRatio`, qui devient la **cible**.
- `EventTick` (7 nœuds) : `DisplayRatio = FInterpTo(DisplayRatio, CurrentRatio, dt, FillSpeed)`
  puis `RefreshBlocks()`.
- `ApplyBlock` (10 nœuds) passe du binaire à un **remplissage continu** :
  `alpha = Clamp(DisplayRatio × 8 − Index, 0, 1)`, couleur =
  `Lerp(Color_Empty → ActiveColor, alpha)`. Chaque bloc se teinte progressivement, et les blocs
  s'allument l'un après l'autre au rythme de l'interpolation.
- Nouvelle fonction `RefreshBlocks` (17 nœuds) — les 8 appels sont sortis de `SetHeat` vers là.

> **Pourquoi ne pas avoir réécrit `SetHeat`** : elle contient la construction de la ligne de texte
> (`BuildString(Float)` imbriqués, `SetText`), et le DSL relu affiche ce nœud sous un `type_id`
> `Class|Factory|SetText` dont je sais depuis `5.72` qu'il peut mentir. La réécrire pour déplacer
> 8 appels aurait mis en jeu du code qui marche. Ses 8 `ApplyBlock` restent en place et sont
> désormais **inoffensifs** : ils lisent `DisplayRatio` comme le Tick.

## Audit

**Zéro orphelin, zéro empilement, compilation `warnings_as_errors` verte sur les deux widgets.**

| Graphe | Nœuds |
|---|---|
| `WBP_Hitmarker` : `ShowHitmarker` · `EventGraph` · `HideHitmarker` | 36 · 24 (2 racines) · 3 |
| `WBP_HeatBar` : `ApplyBlock` · `RefreshBlocks` · `EventGraph` · `SetHeat` | 10 · 17 · 7 · 34 *(inchangée)* |

`ApplyHitmarkerLayout` (24) et `ApplyStrokePair` (23) : **intouchés**, recomptés.

**Piège rencontré** : le premier `write_graph_dsl` sur l'`EventGraph` du hitmarker l'a **empilé**
(45 nœuds, tout en double). Même famille que `2.2c`, et pour un `EventGraph` la purge n'est pas
« tout sauf le `FunctionEntry` » mais **tout, sans exception** — il n'y a pas de nœud d'entrée à
préserver. Purgé à 0 puis réécrit : 24 nœuds. Trouvé par tally, pas par le contrôle d'orphelins.

## Valeurs modifiées

`Melee_Range` 220 → **400** · `Melee_Radius` 60 → **120** ·
**ajouts** `HitmarkerFadeInTime` = 0.03 et `HeatBarFillSpeed` = 9.0, tous deux `[À CALIBRER]`.

> ⚠️ **Aucun pixel regardé.** `12_PIEGES §5.43` est formel : une feature d'UI n'est pas vérifiée
> tant qu'on n'a pas vu une image, et le pipeline de capture ne répond toujours pas dans cet éditeur
> (`Windows("list")` → `[]`). Les deux effets sont prouvés **structurellement** (graphes, valeurs sur
> le CDO), pas **visuellement**.

---

# Clôture du J11 — rituel de fin de journée (`10_DEFINITION_OF_DONE §7`)

## ✅ Validé par Louis, 6ᵉ playtest

*« On est vraiment good là, c'est parfait, le tuning ça me convient. »*

La ligne **Test J11** de `04_ROADMAP.md` est cochée. Le fond était acquis dès la 1ʳᵉ manche
(*« on peut kill quand il touche un mur et tout ça marche bien »*) ; les cinq passes suivantes n'ont
porté que sur la **courbe d'éjection** et la **portée du coup**.

> **Ce que la journée a coûté, et ce qu'elle n'a pas coûté.** Six manches — mais **aucun bug de
> logique**. Les six retours portaient sur le *modèle* ou le *dosage*, jamais sur du code cassé :
> `D61` le poids · `D63` le bug du zénith · `D64` la verticalité au regard · `D65` la parabole ·
> `D66` la portée. Même profil que le J6 (wall ride), à l'opposé du J5 (dash), où cinq passes sur
> six réparaient les dégâts d'une erreur d'architecture.
>
> Les deux vrais défauts trouvés aujourd'hui l'ont été **par des contrôles, pas en jeu** :
> le graphe empilé de `ReceiveKnockbackImpulse` (l'ennemi aurait été lancé **deux fois par coup**,
> compilation verte) et les défauts figés sur les 6 Grunts posés (`D62`). Ni l'un ni l'autre
> n'aurait été visible manche en main.

## Contrôle de fin de journée

**Recompilation — 18 Blueprints en `warnings_as_errors`, zéro warning, zéro échec :**
`BPC_Melee` · `BPC_KnockbackReceiver` · `BP_EnemyBase` · `BP_Enemy_Grunt` · `BP_PlayerCharacter` ·
`PC_Overdrive` · `BPC_HitStop` · `WBP_Hitmarker` · `WBP_HeatBar` · `PDA_EnemyData` ·
`BP_LaserWeapon` · `BPC_Heat` · `BPC_MovementState` · `BPC_Slide` · `BPC_Dash` · `BPC_WallRide` ·
`BPC_PlayerAudio` · `BPC_Health`.

**Graphes de sonde jetables : aucun résidu.** Les 7 `ZZ_*` créés pour contourner `5.70` ont été
recherchés sur les 18 Blueprints — **zéro trouvé**.

### Valeurs en dur repérées dans un Blueprint aujourd'hui

| Littéral | Où | Verdict |
|---|---|---|
| `8.0` | `WBP_HeatBar.ApplyBlock` — nombre de blocs | **Toléré.** Constante **structurelle** : il y a 8 `Image` dans l'arbre du widget, la changer exigerait de toucher la hiérarchie. Elle était déjà là au J9. À promouvoir en clé le jour où `WBP_HUD` génère les blocs (J19) |
| `90.0` | `BPC_Melee.ApplyMeleeHit` — borne du `Clamp` de pitch | ⚠️ **Le plus discutable de la journée.** C'est la borne physique du pitch caméra, pas un curseur — au-delà de 90° `sin` redescend et l'effet s'inverserait. Mais R3 n'aime pas les littéraux. **Signalé à Louis, laissé en l'état** : en faire une clé inviterait à la régler, or toute valeur ≠ 90 est un bug |
| `0.0` / `1.0` | bornes de `Clamp`, `1 − KnockbackResistance` | Non concerné : normalisation, pas du tuning |
| `"TraceTypeQuery3"` | `BPC_Melee.DoMeleeTrace` | Non concerné : identifiant de canal, comme dans `BP_LaserWeapon` depuis le J8 |
| indices `0..7` | `WBP_HeatBar.RefreshBlocks` | Non concerné : câblage vers 8 widgets nommés |

**Aucune valeur de gameplay en dur.** Les 15 clés du melee et du knockback sont toutes dans
`07_TUNING`, et lues depuis `PDA_EnemyData` ou une variable `Instance Editable`.

### Contradictions entre documents — 5 trouvées, 5 résolues

| Contradiction | Résolution |
|---|---|
| `SPEC_COMBAT §7.2` gardait le décollage avec `WallSlam_MinImpactSpeed`, `07_TUNING §13` définit `Knockback_MinImpulse` comme ce même seuil | **`D60`** — les deux clés séparées et **toutes deux lues** par du code |
| `SPEC_UI_HUD §2` : *« jamais de Tick widget »* vs les deux Ticks de `D66` | Règle **précisée** : interdit pour **lire** l'état du jeu, autorisé pour **animer une variable déjà poussée**. Les deux widgets ne castent rien |
| `SPEC_UI_HUD §3.3` : remplissage continu *« reporté au J19 »* | Fait au **J11**, tableau corrigé |
| `SPEC_UI_HUD §3.9a` : *« pas de fondu »* | Fait au **J11**, encadré réécrit |
| `04_ROADMAP` J19 : remplissage continu **et** `S_Heat_Warning` sans abonné | Les deux sont faits (J11 et J11-audio), ligne corrigée |

> ⚠️ **Écart resté ouvert, volontairement** : le rituel demande de reporter les calibrations dans
> `07_TUNING §18`, or l'historique est en **`§19`** (`§18` = *Run & vies*). Les 12 lignes du jour
> sont en **§19**. C'est la consigne du rituel qui est périmée, pas le doc.

### Assets créés hors convention

**Aucun.** `BPC_Melee` → `Content/OVERDRIVE/Weapons/Melee/` et `BPC_KnockbackReceiver` →
`Content/OVERDRIVE/Enemies/Base/`, tous deux à l'emplacement exact prescrit par
`05_ARCHITECTURE §4`, préfixe `BPC_` conforme à `06_CONVENTIONS §2`, sous `Content/OVERDRIVE/` (R6).

## Ce qui reste ouvert après le J11

- ⏳ **Le polish HUD de `D66` n'a pas de validation explicite** — fondus et jauge animée ont été
  livrés dans la même passe que la portée du melee, et le retour de Louis parle du *tuning*.
  **Aucun pixel regardé par un outil** (`12_PIEGES §5.43`, `Windows("list")` → `[]`).
- **J13** : `StopLogic`/`ResumeLogic`, `PlayStagger`, `PlayBounce`, `A_Enemy_GetUp`,
  dissolve en vol. Les branches existent et ferment la fenêtre ; il leur manque l'habillage.
  `Knockback_RecoverTime` reste **INACTIVE** jusque-là.
- **J14** : `AM_Melee_Punch` + slot Upper Body, SFX de swing (aucun WAV de melee dans les 50),
  VFX d'impact et son de wall slam, scale-punch du hitmarker.
- **J19** : pulse et clignotement de la jauge de chaleur.

## Pièges consignés aujourd'hui — 6 neufs, 2 amendés

`5.71` (accesseurs de variable relus non réécrivables) · `5.72` (type_id moteur affiché pour un
nœud de projet) · `5.73` (`CallFunction|X` vs `Class|X|Y`) · `5.74` (`get_node_type_pins`
matérialise sa sonde) · **`5.75`** (un acteur posé fige les défauts d'un composant — 💀) ·
`5.76` (opérateurs wildcard et promotion float→vecteur).
Amendés : `5.70` (l'`UserConstructionScript` n'est pas un refuge fiable) et `2.2c` (contrôle par
**tally de `type_id`** — c'est lui qui a trouvé les deux graphes empilés, le contrôle d'orphelins
étant aveugle à un empilement).

## Incident de fin de journée — `git switch` sous éditeur ouvert (`12_PIEGES §3.5`)

Le merge vers `main` a échoué à mi-parcours : l'éditeur Unreal était **encore ouvert** et verrouillait
`BP_EnemyBase.uasset` et `L_Sandbox_Movement.umap`.

```
error: unable to unlink old 'Content/OVERDRIVE/Enemies/Base/BP_EnemyBase.uasset': Invalid argument
```

`git switch main` a **changé la branche** puis renoncé à remplacer les deux fichiers : `HEAD` sur
`main`, deux `.uasset` portant le contenu de la branche. **La copie de travail était à cheval sur
deux branches**, et `git status` les affichait comme de simples « modifications locales » — une
invitation à les écraser sans réfléchir, c'est-à-dire à refaire `3.4`.

**R11 vaut dans les deux sens** : *éditeur fermé avant de basculer*, pas seulement avant d'ouvrir.
Je n'ai pas appliqué la règle que le projet s'est donnée précisément pour ça.

**Sortie, sans perte, dans cet ordre :**
1. `git push` de la branche **immédiatement** — ça ne touche pas la copie de travail et met le
   commit `d59a352` à l'abri sur le remote avant toute manipulation ;
2. fermeture de l'éditeur par Louis ;
3. **preuve avant d'écraser** : `git diff feat/j11-melee-wallslam -- <les 2 fichiers>` → **vide**,
   donc le disque portait bien les octets de la branche ;
4. `git checkout --` puis `merge --no-ff` → réinstallation d'octets identiques.

L'étape 3 est celle qui distingue cet incident de `3.4` : là-bas, un `git checkout --` lancé sur
une supposition avait écrasé des `.uasset` dont personne ne savait plus d'où ils venaient.

**Merge : `884dc73`. `main` poussé. Copie de travail propre.**
