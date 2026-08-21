# Journal — 2026-08-21 — J10bis — Hitmarker, hit-stop, son de headshot

**Branche** : `feat/j10-hitmarker-hitstop`
**Objectif** : solder le seul reliquat du J10 qui bloque le **Test 4** (`10_DEFINITION_OF_DONE §3`) —
« un headshot procure-t-il une vraie satisfaction ? ». Le headshot *fonctionnait* depuis le
2026-08-20, mais ses trois retours — **visuel, temporel, sonore** — n'existaient pas.

> ⚠️ **Rien n'est joué. Le Test 4 n'est pas coché** et ne le sera que sur le retour manche en main
> de Louis (R8 / R10). Ce qui est mesuré est listé plus bas ; ce qui ne l'est pas aussi.

---

## Ce qui a été construit

### `BPC_HitStop` — `Content/OVERDRIVE/Core/`, composant de `PC_Overdrive`

Propriétaire **unique** du `Set Global Time Dilation` (`11_ARBITRAGES D6`, `SPEC_COMBAT §5.4`).
5 variables, 2 fonctions, `EventGraph` de 4 nœuds. Compile en `warnings_as_errors`.

- `RequestHitStop(RealDuration, Dilation, Priority) → bAccepted` — **23 nœuds, 2 `return`,
  1 seule racine exec.** Garde d'empilement (priorité **strictement** supérieure) et garde de
  cadence (`HitStop_MinInterval`) fusionnées en un seul `or`, donc un seul `Branch`.
- `EndHitStop()` — restaure `1.0`, invalide le timer, réarme `LastHitStopTime`.
  Appelée au `BeginPlay` **et** à l'`EndPlay` : c'est la précaution 2 de la spec, et c'est ce qui
  empêche un rechargement de map de laisser le jeu figé.

**D59 — la « durée en temps réel » de la spec est un timer monde de `RealDuration × Dilation`.**
La spec prescrivait `ArmRealTimeTimer`. Ce nœud n'existe pas : **Blueprint n'expose aucun timer
insensible au time dilation.** Mais il n'en a pas besoin — sous dilatation `d`, le monde avance de
`d` seconde par seconde réelle, donc un timer monde armé à `RealDuration × d` expire après
exactement `RealDuration` secondes réelles. Algébriquement identique, zéro nœud custom.
À `d = 0.05` et `0.05 s` de hit-stop : timer monde de `0.0025 s`, soit **3 frames réelles à 60 fps**.

**D60 — la cadence se mesure en temps RÉEL, pas en `GameTime`.** Le pseudo-code de la spec compare
des `GameTime`. Or `GameTime` est dilaté, et la garde de cadence sert précisément **quand des
hit-stops s'enchaînent**, c'est-à-dire quand le temps est ralenti : elle se mesurerait elle-même
au ralenti. `GetRealTimeSeconds` des deux côtés. Identique à la spec quand `d = 1`.

### `WBP_Hitmarker` — `Content/OVERDRIVE/UI/HUD/`

X de 4 traits diagonaux bordés de blanc (8 `Image`), 3 paliers, 16 variables, 4 fonctions.

**Le choix qui a fait tout le reste : les paliers ne redessinent rien.** La spec demande trois
tailles (10 / 14 / 16 px) et une rotation de 45° sur le palier `Kill`. L'implémentation naïve
recalcule 8 slots à chaque hit. À la place, `ShowHitmarker` pose un **`RenderScale` et un
`RenderTransformAngle` sur le widget entier** : le pivot de rendu d'un `UserWidget` plein écran
est `(0.5, 0.5)`, donc **le centre de l'écran** — exactement là où le X est dessiné. Un palier
coûte alors 1 réglage au lieu de 8, et l'agrandissement se fait autour du réticule.
La géométrie, elle, est calculée **une fois** au `PreConstruct`.

**Pas d'enum, pas d'animation UMG.** Le palier se choisit sur deux booléens dans l'ordre
`Kill > Headshot > Body` — ce qui évite `12_PIEGES §5.2` (aucun outil ne crée de variable enum) et
donne exactement la priorité de `SPEC_UI_HUD §3.9`. La disparition est un timer, pas un fondu :
aucun outil du projet ne crée d'animation UMG, et le fondu est du polish J14 (R4).

**Contradiction de doc tranchée** — `SPEC_COMBAT §5.3` met le headshot en `OD_Magenta_Player` à 45°,
`SPEC_UI_HUD §3.9` réserve ça au palier `Kill` et met le headshot en `OD_Amber_Heat`.
**Les deux disent la même chose en pratique** : le Grunt a `bHeadshotIsLethal = true`, donc tout
headshot est un kill. §3.9 est le sur-ensemble, c'est lui qui est implémenté. L'ambre ne se verra
que sur une cible au headshot non létal — le **Tank du J13**.

### Son de headshot — et une découverte

`PDA_WeaponData` possédait **déjà** `fireSFX`, `impactSFX`, `headshotSFX`, et `PlayFireFX` jouait
déjà les deux premiers depuis le J8. **Les trois slots de `DA_Weapon_Laser` étaient simplement
vides** (`None`) : le laser était muet non par absence de code, mais par absence de donnée.
Remplis avec `S_Laser_Fire_01`, `S_Laser_Impact_Surface_01`, `S_Laser_Hit_Head_01`.

`headshotSFX` n'était joué nulle part → ajouté dans `SendHitFeedback`, **avant** l'appel au
hit-stop (précaution 5 de `§5.4` : une attaque de son étirée par la dilatation ne vend rien).

**Le son de body shot n'a volontairement PAS été ajouté** : `BP_EnemyBase.ApplyDamage` joue déjà
`EnemyData.HitSFX` / `DeathSFX` depuis le J10, et `SPEC_AUDIO §8.4` dit que l'impact sur un ennemi
est l'affaire de l'ennemi, pas de l'arme. Le headshot, lui, est weapon-side parce qu'il doit être
**identique quelle que soit la cible** — « reconnaissable les yeux fermés ».

### Câblage

```
BP_LaserWeapon.ProcessHit
  └─ CallOnHitConfirmed  (dispatcher, inchangé — le StyleMeter du J18 s'y branchera)
  └─ SendHitFeedback(bHeadshot, bKilled)          ← 1 SEUL nœud inséré (16 → 17)
       ├─ if bHeadshot → PlaySound2D(WeaponData.HeadshotSFX)
       └─ Cast OwnerController → PC_Overdrive.NotifyHitConfirmed(bHeadshot, bKilled)
            ├─ if bHeadshot → HitStop.RequestHitStop(0.05, 0.05, 10)
            └─ IsValid(HitmarkerWidget) → ShowHitmarker(bHeadshot, bKilled)
```

`ProcessHit` **n'a pas été réécrite** : le DSL relu attribue `GetHeadshotMultiplier` à
`PDA_EnemyData` (piège 2.39), donc un aller-retour lecture → écriture y aurait posé un vrai appel
sur la mauvaise classe. Insertion de nœud, `self` revérifié `Self Object Reference` non connecté
(contrôle 2.21).

`PC_Overdrive.EventGraph` crée maintenant les deux widgets (crosshair `ZOrder 10`, hitmarker `20`).

---

## Vérifié en PIE, sur l'instance réelle

| Relevé | Valeur | Ce que ça prouve |
|---|---|---|
| `PC_Overdrive_C_0.hitStop` | composant présent | le composant est bien sur le controller |
| `hitStop_Headshot` / `hitStop_TimeDilation` | `0.05` / `0.05` | les défauts survivent à la compilation |
| `hitmarkerWidget` | `WBP_Hitmarker_C_0` | le widget est créé au `BeginPlay` et référencé |
| `WBP_Hitmarker_C_0.visibility` | `Collapsed` | `PreConstruct` s'est exécuté |
| `Halo_A` slot | `pos (−6.364, −6.364)`, `14 × 6`, `45°` | |
| `Stroke_A` slot | `pos (−6.364, −6.364)`, `10 × 2`, `45°` | |
| `Stroke_B` / `Stroke_D` | `(+6.364, −6.364) −45°` / `(+6.364, +6.364) +45°` | les 4 diagonales sont correctes |
| `renderTransformPivot` | `(0.5, 0.5)` | le `RenderScale` par palier s'appliquera **autour du centre de l'écran** |

`off` attendu `= (Gap 4 + Length 10 / 2) × √2/2 = 9 × 0.70710678 = 6.36396`. **Relevé 6.364.**
Le halo fait bien `+2 px sur chaque bord` dans les deux dimensions.

Conversion sRGB → linéaire **validée contre la doc** : `OD_Navy_Ink` et `OD_White_Pure` retombent
au millionième sur les valeurs de `SPEC_UI_HUD §3.1.4`, ce qui valide au passage les deux couleurs
neuves (`OD_Amber_Heat`, `OD_Magenta_Player`).

Audit final — tous compilent en `warnings_as_errors`, **1 seule racine exec par graphe de fonction,
0 nœud mort** :

| Blueprint | Graphes |
|---|---|
| `BPC_HitStop` | `EventGraph` 4 · `RequestHitStop` 23 · `EndHitStop` 8 |
| `PC_Overdrive` | `EventGraph` 12 · `NotifyHitConfirmed` 10 |
| `WBP_Hitmarker` | `EventGraph` 2 · `ApplyStrokePair` 23 · `ApplyHitmarkerLayout` 24 · `ShowHitmarker` 36 · `HideHitmarker` 3 |
| `BP_LaserWeapon` | `ProcessHit` **17** (était 16) · `SendHitFeedback` 8 · `EventGraph` 34, `ResolveShot` 15, `PlayFireFX` 15, `IsHeadshot` 4 — **inchangés** |

---

## ❌ Ce qui n'a PAS pu être vérifié — et pourquoi c'est important

**Aucun tir n'a pu être déclenché en headless, et aucun pixel du hitmarker n'a été regardé.**

La recette `12_PIEGES §4.11` (mapper `IA_Fire` sur `F4` dans `IMC_Debug`, puis `PressKey`) a été
appliquée intégralement. `PressKey` a renvoyé `true` — **et le tir n'est jamais parti** :
`BeamEnd` relu à `(0,0,0)`, `BeamTimeRemaining = 0`, PV du Grunt à `100`. La sonde discrimine :
ce n'est pas le câblage du feedback qui est en cause, c'est l'**entrée**.

Cause : le toolset Slate ne voit **aucune fenêtre** dans cette session d'éditeur —
`Windows("list")` rend `[]`, `Snapshot` rend une chaîne vide, et `CaptureEditorImage` répond
*« Failed to capture any editor windows »*. Ni `GameGetsMouseControl = true` ni
`bThrottleCPUWhenNotForeground = false` n'y changent quoi que ce soit. **Hypothèse non vérifiée**
(fenêtre d'éditeur minimisée / non enregistrée auprès de Slate) — elle n'a pas été testée, donc
elle s'annonce comme telle.

Conséquence directe : **`12_PIEGES §5.43` n'est pas satisfait** — « une feature d'UI n'est pas
vérifiée tant qu'on n'a pas regardé un pixel ». Les deux causes documentées d'un widget invisible
sont écartées *structurellement* (brush `RoundedBox` sans texture ; `CanvasPanel` à ancres
ponctuelles, donc pas de famine de `Fill`), mais **écarté n'est pas vu**. C'est le premier point de
la checklist de Louis.

---

## Trois entrées 💀 du registre étaient fausses

C'est le vrai enseignement de la journée. **Deux pièges classés « mortels » et « non résolus »
n'étaient pas des limites d'outillage, c'étaient des erreurs d'appel de notre côté.**

- **`5.58` — « aucun chemin d'écriture vers un DataAsset » → RÉSOLU.** Le paramètre `values` de
  `set_properties` est déclaré `"type": "string"` : il attend une **chaîne JSON**. Un dict passe la
  validation, le serveur renvoie `returnValue: False` **sans un mot**, et rien n'est écrit.
  Avec `json.dumps(...)`, `DA_Weapon_Laser` s'écrit du premier coup. **Les `DA_*` sont écrivables
  par outil** — la consigne « Louis les remplit à la main » tombe. Nouveau piège **`5.65`**.
- **`5.54` — « le DSL ne sait écrire aucune fonction à valeur de retour » → INFIRMÉ.**
  `RequestHitStop`, 23 nœuds et **deux** `(return)`, est passée du premier coup. L'échec du J10
  était réel mais sa cause n'a jamais été isolée. L'entrée est conservée, barrée et datée : elle
  aurait coûté une reconstruction à `create_node` pour rien.

> **La leçon de méthode, à ajouter à R12 :** un outil qui « ne fait rien » sans erreur ne prouve
> pas que la capacité n'existe pas. Avant de classer une limite d'outillage — surtout en 💀 —
> **relire le schéma d'entrée de l'outil**. Et `returnValue: False` n'est pas « rien à faire »,
> c'est un **échec** : il se teste.

---

## Décisions prises

| Décision | Où c'est écrit |
|---|---|
| **D59** — durée réelle du hit-stop = timer monde de `RealDuration × Dilation` | `SPEC_COMBAT §5.4a` |
| **D60** — cadence du hit-stop mesurée en temps réel, pas en `GameTime` | `SPEC_COMBAT §5.4a` |
| Paliers du hitmarker par `RenderScale`/`Angle` sur le widget entier, pas par re-layout | `SPEC_UI_HUD §3.9a` |
| Palier choisi sur 2 booléens (`Kill > Headshot > Body`), pas sur un enum | `SPEC_UI_HUD §3.9a` |
| Contradiction §5.3 / §3.9 sur la couleur de headshot : §3.9 fait foi, sans divergence observable | `SPEC_UI_HUD §3.9a` |
| Le son d'impact au **corps** reste data-driven côté ennemi ; seul le **headshot** est weapon-side | ce journal + `SPEC_AUDIO §8.4` |
| Les 3 clés `HitStop_*` de tir vivent sur `PC_Overdrive`, pas sur le composant (c'est un service) | `07_TUNING §16` |

## Valeurs modifiées

Aucune valeur existante de `07_TUNING` touchée. **Ajouts** : `HitStop_HeadshotPriority` (10, fixe)
et les **15 clés `Hitmarker_*`** (11 numériques + 4 couleurs), toutes `[À CALIBRER]`, §16.

## Ressenti de playtest

**Néant — rien n'a été joué.** Aucune affirmation de feeling n'est possible (R8).

## Bugs / pièges rencontrés

| Piège | Gravité | Consigné |
|---|---|---|
| `set_properties` veut `values` en **chaîne JSON** — cause unique de `5.58` | 💀 | `5.65` |
| Le DSL réinstalle des events `Tick`/`Construct` **vides et actifs** | 🔴 | `5.66` |
| Continuations multi-exec au niveau du `bind` ; un multi-exec termine le flux | 🟠 | `5.67` |
| `self` est le 1ᵉʳ argument positionnel d'un appel membre en DSL | 🔴 | `5.68` |
| **J'ai détruit le mapping `F3 → IA_DebugToggle` d'`IMC_Debug`** (voir ci-dessous) | 💀 | `5.69` |
| `5.58` requalifié ✅ RÉSOLU · `5.54` requalifié ⚠️ INFIRMÉ | — | en place |

### L'erreur que j'ai commise, et comment elle a été rattrapée

En posant l'échafaudage de tir headless, j'ai écrit `IMC_Debug.defaultKeyMappings` **sans avoir lu
sa valeur d'origine** — j'avais lu son *schéma* (`list_properties`), qui ressemble à une valeur.
`set_properties` n'est pas un merge : mon `{mappings: [F4 → IA_Fire]}` a remplacé le contenu, et le
« nettoyage » à `{mappings: []}` a **détruit le `F3 → IA_DebugToggle`** qui s'y trouvait depuis
le J2. Zéro erreur, zéro warning, et l'overlay de debug aurait cessé de répondre au prochain
playtest sans que rien ne l'explique.

**Ce qui l'a rattrapé** : le `git status` de fin de session. Le pointeur LFS était passé de
**2546 à 1208 octets** — un `.uasset` ne maigrit pas tout seul.
**Ce qui l'a réparé sans toucher au disque** (l'éditeur tenait l'asset en mémoire et l'aurait
réécrit) : lire l'objet LFS d'origine dans `.git/lfs/objects/`, en extraire les chaînes ASCII —
`F3`, `IA_DebugToggle`, `InputTriggerPressed` y étaient **en clair** — et reposer la valeur par
`set_properties`. `git status` ne voit plus le fichier : restauration **à l'octet près**.

La parade est en `12_PIEGES §5.69`, et elle tient en une phrase : **la sauvegarde d'un échafaudage
se prend au moment où on le pose, pas au moment où on le retire.**

> 🧹 **Dette de doc repérée, non corrigée** : `12_PIEGES_OUTILLAGE.md` contient **deux entrées
> `5.59` et deux entrées `5.60`** avec des contenus différents. Une insertion automatique s'est
> donc dupliquée avant d'être rattrapée. À renuméroter — ça n'a pas été fait aujourd'hui pour ne
> pas mélanger une renumérotation globale avec le travail du jour.

---

## Échafaudages — retirés et revérifiés

- `IMC_Debug` → **`git status` ne le voit plus** : restauré à l'octet près (2546 o), `F3 → IA_DebugToggle`
  et son trigger `InputTriggerPressed` en place. ⚠️ Il avait été **détruit** en cours de session — voir `5.69`
- ⚠️ `GameGetsMouseControl` et `bThrottleCPUWhenNotForeground` remis à `false` / `true` — **valeurs
  supposées**, leur valeur d'origine n'avait pas été relevée. Ce sont des préférences d'éditeur, pas
  du contenu ; à corriger si Louis constate un changement de comportement du bouton Play
- `WBP_Hitmarker.hitmarker_KillDuration` → **relu `0.25`** (était monté à 30 s pour photographier)
- `LevelEditor/PlayIn.GameGetsMouseControl` → `false` · `EditorPerformanceSettings.bThrottleCPUWhenNotForeground` → `true`
- PIE arrêté · les 3 Grunts du sandbox **relus à `(1000, −4300)`, `(2200, −4000)`, `(3300, −4500)`, `Z = 150`** — le déplacement de test était en PIE, il n'a pas fui dans le niveau
- Aucun `PrintString` posé de la journée

## Vérifications de fin de journée

- [x] Tous les BP recompilés en `warnings_as_errors` — **zéro warning**
- [x] 1 racine exec par graphe de fonction, **0 nœud mort**, `self` contrôlé (2.21)
- [x] Assets sauvegardés et relus après sauvegarde
- [ ] 3 minutes de jeu réel — **pas fait : c'est le playtest de Louis**
- [x] Roadmap mise à jour **sans cocher le Test 4**
- [x] Pièges consignés — 4 neufs, 2 requalifiés
- [ ] Commit — **interdit tant que Louis n'a pas joué (R10)**
