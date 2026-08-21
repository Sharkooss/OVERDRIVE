# Journal — 2026-08-20 — J10 (partiel) — Câblage du Grunt

**Branche** : `feat/j10-grunt-wiring`
**Objectif (demande de Louis)** : importer et câbler `SK_Enemy_Grunt` avec ses animations de base
(idle + réaction aux dégâts), **sans IA**, pour disposer d'un **vrai ennemi sur qui tirer** et
pouvoir trancher la frontière tête/corps (`12_PIEGES §6.23`) sur une vraie silhouette plutôt que
sur `BP_TargetDummy`.

> ⚠️ **Journée incomplète, arrêtée volontairement.** Le socle d'assets est posé et vérifié ;
> le graphe de gameplay ne l'est pas. Détail exact ci-dessous — rien n'est annoncé comme fait
> qui ne l'est pas.

---

## Fait, et vérifié

- **`SK_Enemy_Grunt` importé** → `Enemies/Grunt/`. Relu : **180.00 × 70.00 uu** de haut/large
  (`boxExtent` 90 / 35 / 14.2), 3968 vertices, 3 slots matériau nommés par token de `PALETTE.md`.
  Le modèle regarde bien **+X**, donc l'orientation UE d'un Character est correcte sans rotation.
- **Squelette** déplacé et renommé → `Enemies/Shared/SKEL_Enemy_Humanoid`, et le mesh pointe
  toujours dessus après le déplacement (revérifié par `get_skeleton`, pas sur la foi de `move`).
  → **34 os, pas 33** : l'objet Armature de Blender est devenu un os racine (`12_PIEGES §5.51`).
- **3 instances de matériau** créées et **assignées aux 3 slots**, valeurs relues :
  `MI_Enemy_Body` (`OD_Navy_Deep`), `MI_Enemy_Panel` (`OD_Navy_Ink`),
  `MI_Enemy_Emissive` (`OD_Amber_Enemy`, `EmissiveIntensity` 6.0).
  → Parent = **`M_Weapon_Base`**, faute de `M_Toon_Enemy`. Voir la dette ci-dessous.
- **`PDA_EnemyData`** (`Data/DataAssets/`) : **18 propriétés**, `Instance Editable`, catégorisées.
  Conforme à `08_DATA_SCHEMAS §3` moins `EnemyType` (enum, `12_PIEGES §5.2`).
- **`BPC_Health`** (`Systems/Health/`) — **compile propre en `warnings_as_errors`** :
  3 variables, 2 dispatchers (`OnDeath`, `OnHealthChanged`), 4 fonctions —
  `InitializeHealth` (5 nœuds), `ApplyHealthDamage` (17), `IsAlive` (4), `GetHealthRatio` (5).
  Garde anti-double-kill en première ligne d'`ApplyHealthDamage`, `SafeDivide` sur le ratio.
- **`BP_EnemyBase`** (`Enemies/Base/`, parent `Character`) — compile propre. Composants
  `HeadHitbox` (Sphere, enfant du mesh) et `Health` ajoutés ; variable `EnemyData`.
- **`BP_Enemy_Grunt`** (`Enemies/Grunt/`) — créé, enfant de `BP_EnemyBase`, compile propre.

## Seconde passe — après les gestes manuels de Louis

Louis a importé les 6 FBX d'animation, coché `BPI_Damageable` sur `BP_EnemyBase`, vérifié
`E_EnemyType`, et produit **58 WAV** dans `Art_Source/Audio/out/`. Vérifié de mon côté :
les 6 assets sont bien de classe `AnimSequence`, l'interface expose bien `ApplyDamage` /
`IsAlive` / `GetHealthRatio`, et l'enum contient `Grunt / Shooter / Tank`.

**Graphes écrits, tous compilés en `warnings_as_errors`, 1 seule racine d'exec par graphe
(zéro nœud orphelin), vérifié par `entry_points_only`** :

- **`BP_EnemyBase.EventGraph` — 28 nœuds.** `BeginPlay` → `IsValid(EnemyData)` :
  branche invalide → `PrintString "EnemyData MANQUANT"` ; branche valide → capsule 35/90 +
  blocage du canal `Weapon` · mesh depuis `EnemyData.SkeletalMesh`, `RelativeLocation Z −90`,
  collision `NoCollision` (§2 : le mesh n'est jamais tracé) · `HeadHitbox` rayon **43**,
  `Z +158`, `QueryOnly`, **tous canaux `Ignore` sauf `Weapon` = `Block`**, et
  **`ComponentTags = ["Head"]`** — c'est ce tag que lit `BP_LaserWeapon.IsHeadshot` depuis le J8 ·
  `Health.InitializeHealth(EnemyData.MaxHealth)` · `MaxWalkSpeed = EnemyData.MoveSpeed`.
- **`ApplyDamage` — 8 nœuds.** `BreakS_DamageInfo` → `Health.ApplyHealthDamage(Amount)` →
  `Branch(bKilled)` → mort : `DestroyActor` ; les deux sorties renvoient `bKilled` et
  `DamageApplied`.
- **`IsAlive` / `GetHealthRatio` — 4 nœuds chacun**, délégués à `BPC_Health`.

> **Décision assumée : `ApplyDamage` ne rejoue PAS le multiplicateur de headshot.**
> `BP_LaserWeapon` applique déjà `HeadshotMultiplier` depuis le J8nonies (un headshot vaut
> 150 pv pleins). Le remultiplier ici donnerait 450. Conséquence : `bHeadshotIsLethal` et
> `HeadshotMultiplier` de `PDA_EnemyData` **ne pilotent encore rien** — c'est acceptable pour le
> Grunt (150 > 100 pv, le headshot tue de fait), et ça devra être câblé au **J13** pour le Tank,
> dont le headshot doit être **non létal**. Signalé ici pour ne pas devenir un `12_PIEGES §6.24`.
> `DestroyActor` est un **placeholder** : la vraie mort est le dissolve de `SPEC_ENEMIES §8` (J12).

## Troisième passe — données, sons, placement, vérification PIE

- **50 WAV importés** (`SoundWave`) dans `Audio/SFX/{Combat 17, Enemy 9, Movement 24}`.
  Copiés depuis `Art_Source/Audio/out/` **dans `Content/`, où ils RESTENT** : le `.gitignore`
  ignore `Art_Source/Audio/out/` (regénérable par `overdrive_sfx.py`) et déclare que *« seuls les
  WAV validés et importés dans `Content/OVERDRIVE/Audio/` sont suivis »*. Les effacer aurait
  supprimé **la seule copie versionnée** des sons. Les 3 `_AUDITION_*.wav` sont exclus.
- **`DA_Enemy_Grunt` rempli par Louis** et relu : `100 pv / 550 / ×3 / bHeadshotIsLethal ✓ /
  SkeletalMesh lié`. **`BP_Enemy_Grunt.EnemyData`** pointe dessus.
- **3 Grunts placés** dans `L_Sandbox_Movement`, dossier `Sandbox/L_Enemies`, sur la ligne
  d'approche à plat : `(1000, −4300)`, `(2200, −4000)`, `(3300, −4500)`, à côté des `TargetDummy`
  existants pour comparaison directe.

### Vérifié en PIE, sur l'instance réelle

| Relevé | Valeur |
|---|---|
| `CharacterMesh0.skeletalMeshAsset` | `SK_Enemy_Grunt` |
| `CharacterMesh0.relativeLocation` | `Z −90` (pieds au bas de la capsule) |
| `CollisionCylinder` | `radius 35 / halfHeight 90` |
| `HeadHitbox.sphereRadius` | `43` |
| `HeadHitbox.componentTags` | **`["Head"]`** — le tag que lit `BP_LaserWeapon.IsHeadshot` |
| `Health` | `100 / 100`, `bIsDead false` |
| `CharacterMesh0` | `bVisible true`, `bHiddenInGame false`, scale 1 |

**Zone de headshot effective** : centre à `Z 158`, demi-hauteur `sqrt(43² − 35²) = 25.0`
→ **Z 133 à 183** sur un modèle de 180 uu, soit la tête et le haut des épaules.

> ⚠️ **Non confirmé visuellement** : les captures de viewport à 300–500 uu sont trop basse
> définition pour que j'affirme que le mesh se dessine correctement. Toutes les propriétés qui
> commandent l'affichage sont bonnes, mais **je ne l'ai pas vu**. C'est le premier point de la
> checklist de Louis.

## Quatrième passe — retour de playtest de Louis, 4 corrections

> *« peu importe où je tire, je les one shoot »* · *« ils sont trop petits, met les en scale 2 »* ·
> *« dans le BP la sphère head est au milieu »* · *« fait en sorte que je les voie dans l'éditeur,
> ça me sera utile pour le mapping »*.

**Le one-shot n'était pas un bug de hitbox.** L'œil du joueur est à `Z ≈ 152` ; la zone de tête à
l'échelle 1 allait de `Z 133` à `183`. Tirer à l'horizontale tombait donc **toujours** dedans.
L'ennemi faisait la taille du joueur : sa tête était à hauteur des yeux. **Passer à l'échelle 2
règle le one-shot et la taille d'un seul geste** — la zone de tête monte à `Z 266 → 366`, hors de
la ligne de visée horizontale. Reporté dans `07_TUNING §13`.

- **`ApplyEnemyVisuals` — nouvelle fonction, 24 nœuds, 0 nœud exec inaccessible.** Elle contient
  tout le montage (capsule **70/180**, mesh `RelativeScale3D = 2` et `Z −180`, `HeadHitbox` 43 @ 158
  **local** — donc 86 @ 316 en monde par héritage d'échelle —, collisions, tag `Head`).
- **Appelée depuis `UserConstructionScript` ET `EventBeginPlay`.** C'est ce qui rend l'ennemi
  **visible et correctement dimensionné dans l'éditeur**, sans PIE. Vérifié : `get_actor_bounds`
  rend `Z 0 → 402` **hors PIE**, et la capture d'écran montre la silhouette navy avec la sphère de
  tête en haut. L'`EventGraph` retombe à 10 nœuds (appel + vie + vitesse).
- **`ApplyDamage` — 14 nœuds** : `S_Enemy_Death` sur la branche létale (avant `DestroyActor`),
  `S_Enemy_Hit` sinon, lus depuis `EnemyData.DeathSFX` / `HitSFX` (`SPEC_AUDIO §8.2`, data-driven).
- **Les 3 acteurs replacés à `Z = 180`** (demi-hauteur de capsule doublée), pieds au sol vérifiés.

> **Piège d'outillage payé cash** : deux tentatives ratées d'écriture du tag avaient laissé
> **4 nœuds orphelins** (`SetComponentTags` + `MakeArray` ×2), et ma détection de « fin de chaîne »
> s'est branchée sur l'orphelin au lieu de la vraie queue. Détecté par **audit d'accessibilité
> exec** depuis le `FunctionEntry`, purgé, recâblé. C'est exactement `12_PIEGES §2.2b/2.2c` :
> le graphe compilait proprement dans les deux cas.

## Cinquième passe — le vrai bug du one-shot

Louis, après la passe scale 2 : *« même quand je tire vraiment dans le bas des pieds je le one shot »*.
**Mon diagnostic « hauteur d'yeux » était donc faux aussi** — il expliquait pourquoi tout tir était
classé headshot, pas pourquoi un tir au corps tuait.

**Méthode qui a tranché** : arrêt des hypothèses, pose d'une sonde `PrintString` sur le montant reçu
par `ApplyDamage`. Retour de Louis en un tir : **« 50, une seule fois »**. Donc l'arme est innocente,
la double application est écartée, et le bug est dans `BPC_Health.ApplyHealthDamage`.

**Cause racine** : le pin `B` du nœud `float<=float` (`newHP <= 0`) portait une **chaîne vide** au
lieu de `"0.0"`. Mon `set_pin_value` avait été fait **avant** que le wildcard du
`K2Node_PromotableOperator` ne se résolve : le pin a été régénéré derrière et la valeur perdue.
Écriture acceptée, aucune erreur, **compilation verte** — et la comparaison partait en vrai, donc
**tout ennemi mourait au premier coup quel que soit le montant des dégâts**.
Le témoin est visible à la relecture : le `Clamp` voisin affiche bien `"0.0"` sur son `Min` non
connecté, le pin cassé affichait `""`. Consigné en **`12_PIEGES §5.62`**.

Correctif : `B = 0.0`, **relu après compilation**. Sonde retirée et recomptée
(`ApplyDamage` 16 → **14 nœuds**, aucun `PrintString`/`ToString` résiduel), **0 nœud exec
inaccessible** dans les deux graphes, les deux Blueprints compilent en `warnings_as_errors`.

> **Trois diagnostics faux avant le bon** (hitbox de tête, échelle, arme). Le symptôme
> « je one-shot partout » oriente naturellement vers le headshot ; la cause était un littéral
> manquant à deux nœuds de là. La leçon de méthode est dans le registre : quand les hypothèses
> plausibles tombent, on instrumente au lieu de raisonner.

## Sixième passe — la hitbox de tête, et le problème était structurel

Retour de Louis après validation du headshot : *« beaucoup trop permissive, ça dépasse beaucoup
trop ; la taille en 0.5 était bonne mais elle ne ressortait pas assez »*.

**Les deux réglages qu'il avait essayés étaient les deux extrêmes d'un curseur cassé.** Une sphère
centrée sur l'axe de la capsule n'est touchable que là où elle **déborde latéralement** :
`zone = h ± sqrt(R² − r²)`. Avec `r = 70` (la capsule couvrait la tête) :

- `R = 43` → `43 < 70` : la sphère est **entièrement noyée dans le corps**, aucun headshot possible ;
- `R = 86` → ça marche, mais la tête fait **172 uu de large** contre 140 pour le corps entier.

**Aucune valeur intermédiaire n'existait.** Le correctif n'est pas un nombre, c'est de sortir la
tête de la capsule : `Enemy_CapsuleHalfHeight` 180 → **150**, la capsule s'arrête au cou (`Z 0→300`),
et la sphère vit au-dessus, où elle ne concurrence plus rien — **sa taille redevient libre**.

Mesuré en PIE après coup : rayon effectif **45**, centre `Z 331.6`, sommet de capsule `Z 301.6`,
zone de headshot **`Z 296.6 → 375.6`** (79 uu de haut, 90 de large). Acteurs repositionnés à
`Z = 150`, pieds au sol vérifiés (`bounds Z 1.6 → 376.6`).

**Contrepartie assumée et signalée à Louis** : au-dessus de `Z 300`, un tir qui rate la sphère ne
touche plus rien — il n'est plus absorbé par la capsule et compté en body shot. Rater la tête est
un miss.

## Pas fait — reporté explicitement

- **Hitmarker et hit-stop** : `BPC_HitStop` (`SPEC_COMBAT §5.4`) et `WBP_Hitmarker` (`§5.3`) n'ont
  pas été commencés. **Le Test 4 reste donc NON validé** : le headshot fonctionne, mais sa
  *satisfaction* dépend de ces trois retours (visuel, temporel, sonore).
- **~40 SFX d'arme et de mouvement non câblés.** Ils touchent 5 Blueprints validés manche en main ;
  les insérer en fin de session aurait laissé du code validé à moitié modifié (R10). Passe dédiée,
  avec des Sound Cues `SC_*` pour la randomisation des variantes (`SPEC_AUDIO §8.3` règle 3).
- **`ABP_Enemy`** : les 6 animations sont importées, rien ne les joue. Le Grunt est en pose de
  référence — suffisant pour calibrer les hitbox, pas pour juger le feeling.
- **`12_PIEGES §5.58` non résolu** : aucun chemin d'écriture par outil vers un DataAsset. Les
  `DA_*` se remplissent à la main.

## La décision de fond : la frontière tête/corps (`12_PIEGES §6.23`)

Le piège disait que la règle « rayon de tête > demi-diagonale du corps » fait que **tout tir est un
headshot**. C'est vrai, mais le registre n'avait pas posé l'équation. La voici.

Corps = capsule de rayon `r`, tête = sphère de rayon `R` centrée `h` au-dessus du sol.
Un rayon horizontal à la hauteur `z` touche le corps à la distance `r` de l'axe, et la tête à
`sqrt(R² − (z−h)²)`. **La tête gagne si et seulement si** :

```
(z − h)²  <  R² − r²        →  zone de tête = h ± sqrt(R² − r²)
```

**La hauteur de la zone de tête n'est donc pas un réglage libre : elle est imposée par `R` et `r`.**

- `BP_TargetDummy` : `r = 30`, `R = 83.33` → zone de tête **± 77.8 uu** sur un corps de 180.
  D'où « tout est un headshot ». Ce n'était pas un bug, c'était l'équation.
- **Grunt retenu** : `r = 35` (capsule), `R = 43` → zone de tête **± 25.0 uu**, soit **50 uu**
  de haut sur 180. Généreux à 3000 uu/s, et le torse reste du torse.

`HeadHitbox` est donc posé à **rayon 43**, à attacher à l'os `head` au `BeginPlay`.
**Ces deux chiffres sont `[À CALIBRER]` et n'ont jamais été joués** — c'est le curseur du prochain
playtest : monter `R` élargit la zone de tête, la descendre vers 36 la réduit à ±8 uu.

## Décisions prises

| Décision | Fichier |
|---|---|
| Zone de tête dimensionnée par `h ± sqrt(R² − r²)` ; Grunt à `R = 43` / `r = 35` → ± 25 uu | à porter dans `07_TUNING §13` et `12_PIEGES §6.23` |
| Matériaux d'ennemi instanciés depuis `M_Weapon_Base` faute de `M_Toon_Enemy` | dette datée au J14 |
| Les défauts de composant se posent dans le graphe au `BeginPlay`, pas par propriété | `12_PIEGES §5.56` |
| `E_EnemyType` volontairement absent de `PDA_EnemyData` (aucun outil ne crée une variable enum) | `12_PIEGES §5.2` |

## Valeurs modifiées

Aucune valeur de `07_TUNING` existante touchée. **Deux clés à y ajouter** :
`Enemy_HeadHitboxRadius` = 43 `[À CALIBRER]` et `Enemy_CapsuleRadius` = 35 `[À CALIBRER]`.

## Ressenti de playtest

**Néant — rien n'est jouable.** Aucune affirmation de feeling n'est possible aujourd'hui (R8).

## Bugs / pièges rencontrés

| Piège | Gravité | Consigné |
|---|---|---|
| Aucun outil n'importe une AnimSequence | 🔴 | `5.52` |
| `write_graph_dsl` ne sait écrire aucune fonction à valeur de retour (`\|\|AddReturnNode...`) | 💀 | `5.54` |
| Défauts de composant effacés par `compile_blueprint` | 🔴 | `5.56` |
| Propriétés Blueprint en camelCase, nom faux ignoré en silence ET relu à `0` | 🔴 | `5.57` |
| `set_properties` sans effet sur un DataAsset Blueprint — **non résolu** | 💀 | `5.58` |
| UE retire le `b` des accesseurs (`bIsDead` → `GetIsDead`) | 🟠 | `5.53` |
| Signatures `ObjectTools` : `(instance, values)` / `(instance, properties)` | 🟠 | `5.55` |
| L'objet Armature Blender devient un 34ᵉ os | 🟠 | `5.51` |

## Demain — dans cet ordre

1. Louis importe les 6 FBX d'animation et coche `BPI_Damageable` sur `BP_EnemyBase`.
2. `BP_EnemyBase.BeginPlay` : `ApplyEnemyData` (mesh, capsule 35/90, `HeadHitbox` R=43 attaché à
   l'os `head` + tag `Head` + blocage du canal `Weapon`), `Health.InitializeHealth`.
3. Implémenter `BPI_Damageable` (`ApplyDamage` / `IsAlive` / `GetHealthRatio`) — **à `create_node`,
   pas au DSL** (`5.54`).
4. Résoudre ou contourner `5.58`, sinon `DA_Enemy_Grunt` reste à remplir à la main.
5. `ABP_Enemy` (idle), placement dans le sandbox, mesure en PIE, **puis** playtest de Louis.

---

## Vérifications de fin de journée

- [x] Tous les BP recompilés en `warnings_as_errors` — `BPC_Health`, `BP_EnemyBase`,
      `BP_Enemy_Grunt` : **zéro warning**
- [x] Assets sauvegardés (`save_assets`) et relus après sauvegarde
- [ ] 3 minutes de jeu réel — **impossible, rien n'est jouable**
- [ ] Roadmap cochée — **rien à cocher : aucune ligne du J10 n'est terminée**
- [x] Pièges consignés — **14 entrées, `5.51` à `5.64`**
- [x] **Échafaudages retirés et recomptés** : `BP_EnemyBase.ApplyDamage` **14 nœuds**,
      `BPC_Health.ApplyHealthDamage` **19**, `BP_LaserWeapon.IsHeadshot` revenu à ses **4** nœuds
      d'origine. Zéro `PrintString` / `ToString` résiduel, **0 nœud exec inaccessible** partout.
- [x] **Jeu réel par Louis** : deux tirs au corps, un tir à la tête létal, taille et lisibilité
      validées, sons d'ennemi validés — *« ok c'est good »*
- [x] `CLAUDE.md` **R12** ajoutée
- [x] Roadmap J10 mise à jour, **sans cocher ce qui n'est pas fait** (hitmarker, hit-stop, Test 4)
- [x] Commit + merge sur `main` — **autorisé par Louis après playtest (R10)**
