# 07 — TUNING (source de vérité des valeurs)

> **Aucune valeur de gameplay ne doit exister ailleurs que dans ce fichier.**
> Les Blueprints lisent ces valeurs via DataAssets ou variables `Instance Editable`.
>
> - `[À CALIBRER]` = valeur de départ, à valider en jeu. **Attendue à changer.**
> - `[VALIDÉ]` = testé en jeu et approuvé par Louis. Ne pas modifier sans son accord.
>
> Statut global au 2026-08-18 : **tout est `[À CALIBRER]`**, rien n'a encore été joué.

---

## 1. Unités & conversions

UE : `1 uu = 1 cm`. Toute vitesse interne est en **`uu/s`**.

| Représentation | Formule | Exemple |
|---|---|---|
| Interne (moteur) | `uu/s` | `3000` |
| HUD « SPEED » | `uu/s ÷ 10` | `300` |
| km/h réel | `uu/s × 0.036` | `108 km/h` |
| km/h « arcade » (optionnel, cosmétique) | `uu/s × 0.036 × 3` | `324 km/h` |

**Décision** : le HUD affiche par défaut `SPEED` (unité interne ÷ 10), conforme au GDD §6.
La key art montre des km/h — si Louis veut ce style, on utilise le facteur arcade ×3 **purement cosmétique**,
sans jamais toucher aux valeurs internes. Le choix se fait au moment du HUD (`Docs/Specs/SPEC_UI_HUD.md`).

### Échelle de référence (GDD §6 → uu/s)

| GDD | uu/s | HUD | Signification |
|---|---|---|---|
| 0 | 0 | 0 | immobile |
| 100 | 1000 | 100 | déplacement normal |
| 150 | 1500 | 150 | sprint |
| 200 | 2000 | 200 | très rapide |
| 300 | 3000 | 300 | excellent |
| 400 | 4000 | 400 | expert |
| 500+ | 5000+ | 500+ | vitesse extrême |

Repère externe : Titanfall 2 tourne autour de 1000–2500 uu/s. On vise **plus haut**, donc
la lisibilité du niveau est une contrainte de design forte (`Docs/Specs/SPEC_LEVELDESIGN.md`).

---

## 2. Personnage

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `CapsuleHalfHeight` | 88 | uu | À CALIBRER | standard UE |
| `CapsuleRadius` | 34 | uu | À CALIBRER | standard UE |
| `CapsuleHalfHeight_Slide` | 44 | uu | À CALIBRER | permet de passer sous les obstacles |
| `EyeHeight` | 64 | uu | À CALIBRER | offset caméra depuis le centre capsule |
| `MaxHealth` | 100 | pv | À CALIBRER | |
| `Gravity` | 2.4 | ×G | À CALIBRER | gravité arcade, chutes rapides et lisibles |
| `MaxStepHeight` | 50 | uu | À CALIBRER | franchissement généreux, ne casse pas le flow |
| `WalkableFloorAngle` | 50 | ° | À CALIBRER | |
| `GroundFriction` | 3.0 | — | À CALIBRER | descend à ~0.5 en slide |
| `BrakingDecelerationWalking` | 1500 | uu/s² | À CALIBRER | assez bas pour garder le momentum |

---

## 3. Vitesse & momentum

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Speed_Walk` | 1000 | uu/s | À CALIBRER | vitesse de base |
| `Speed_SprintCap` | 1500 | uu/s | À CALIBRER | **plafond du sprint seul** |
| `Speed_HardCap` | 6000 | uu/s | À CALIBRER | plafond absolu, sécurité collision |
| `Accel_Ground` | 4000 | uu/s² | À CALIBRER | montée en vitesse progressive |
| `Accel_Air` | 4000 | uu/s² | À CALIBRER | `CMC.MaxAcceleration` en l'air. Avec `AirStrafe_AirControl`, donne l'accélération de contrôle aérien : `0.85 × 4000 = 3400 uu/s²`. **Ne pilote pas le gain de vitesse** (c'est `AirStrafe_SpeedGainPerSec`) |
| `MomentumDecayRate` | **800** | uu/s² | **RETUNÉ AU J7** (était 400) | perte au sol au-dessus du sprint cap. **Inopérante du J2 au J5** (`12_PIEGES §6.14`), réparée au J5. Repère : **1.9 s** pour ramener 3000 → 1500, soit ~4300 uu parcourus |
| `MomentumDecay_GraceTime` | **0.25** | s | **RETUNÉ AU J7** (était 0.35) | délai avant que la décroissance démarre. **Réarmée par `HandleLanded`, `EndDash` ET `EndWallRide`** |

> ### ⚠️ Le couple décroissance / grace est le chantier n°1 du J7
>
> **Constat de Louis au J6** : « c'est un peu trop simple d'accumuler de la vitesse sans la perdre ».
>
> `ApplyMomentumDecay` ne tourne **que si les 4 conditions sont réunies** :
> `bIsGrounded` **ET** état ∈ {`Idle`, `Walking`, `Sprinting`} **ET** `Grace ≤ 0` **ET** `vitesse > cap`.
> Donc **jamais en l'air, jamais en slide / dash / wall ride / saut / chute.** C'est voulu : la
> décroissance est le prix du *j'arrête d'enchaîner*, pas une punition d'erreur (`§10` s'en charge).
>
> **Le risque n'est pas le taux, c'est la grace.** `StartGrace(0.35 s)` est appelée par **trois**
> endroits — `HandleLanded`, `EndDash`, `EndWallRide`. Au J7 le bunny hop fait atterrir toutes les
> ~0.6 s : **chaque atterrissage réarme 0.35 s de grace**, donc la décroissance ne tourne qu'une
> fraction du temps, et pendant une chaîne wall ride → wall jump → atterrissage → dash elle peut
> **ne jamais tourner**. C'est la famille exacte de **D41** (fenêtre de slide réarmée par le dash),
> qui avait coûté un playtest à accuser le dash à tort.
>
> **Mesurer avant de tuner.** L'overlay `F3` affiche depuis le J6 une ligne `DECAY` (`OD_9_Decay`)
> qui donne `active`, **laquelle des 4 conditions bloque** (`atcap` / `air` / `state` / `grace`),
> l'excès au-dessus du cap, et le **temps cumulé passé au-dessus du cap**. Le chiffre à regarder est
> le **ratio de temps où `active = true`** pendant une chaîne. S'il est proche de zéro, c'est
> `MomentumDecay_GraceTime` qu'il faut baisser, **pas** `MomentumDecayRate` qu'il faut monter.
>
> Ordres de grandeur, sortie de wall ride à 2500 uu/s (retour au sprint cap 1500) :
>
> | `MomentumDecayRate` | temps pour retomber au cap | + grace | distance parcourue |
> |---|---|---|---|
> | **400** (actuel) | 2.5 s | ~2.85 s | ~5700 uu |
> | 600 | 1.7 s | ~2.0 s | ~4000 uu |
> | 800 | 1.25 s | ~1.6 s | ~3200 uu |
>
> Après une grosse chaîne à 4000 uu/s, l'actuel donne **6.25 s** au-dessus du cap, soit la quasi-
> totalité d'un niveau court. **Hypothèse de départ à tester, pas à croire : 600–800.**
>
> #### État au J7 (2026-08-19) — **les deux valeurs sont toujours à 400 et 0.35, volontairement**
>
> Le J7 a livré les deux prérequis de la mesure et **n'a touché à aucune des deux clés** :
> - **l'instrument** — ligne `DECAY` de l'overlay `F3` (posée au J6) ;
> - **le terrain** — la **zone K** du sandbox (`SPEC_MOVEMENT §13.2`), qui est le premier endroit du
>   projet où une chaîne complète est possible.
>
> **Le ratio ne se mesure pas sans jouer** (`CLAUDE.md` R8) : aucun outil ne sait enchaîner
> rampe → slide → gap → wall ride → wall jump → hops. La mesure est donc **à faire par Louis**,
> et le retune se décide après. Tuner à l'aveugle ici produirait exactement les deux valeurs
> fausses qui s'annulent contre lesquelles ce bloc met en garde.
>
> ### ✅ Retune fait — **`800` / `0.25`**, décidé par Louis le 2026-08-19 (fin de J7)
>
> Le bunny hop ayant été coupé le même soir (**D52**, §6), le risque annoncé plus haut — une grace
> réarmée toutes les 0.77 s qui aurait faussé la mesure — **n'existe plus**. Les réarmeurs
> redeviennent les trois d'origine : `HandleLanded`, `EndDash`, `EndWallRide`.
>
> Louis a tranché sur le **haut** de la fourchette proposée (600–800) et a resserré la grace :
> le taux **double** et le délai passe sous le quart de seconde. Effet combiné, sortie de wall ride
> à 2500 uu/s :
>
> | | avant (400 / 0.35) | **après (800 / 0.25)** |
> |---|---|---|
> | temps pour retomber au cap | 2.5 s + grace = **2.85 s** | 1.25 s + grace = **1.50 s** |
> | distance parcourue au-dessus du cap | ~5700 uu | **~3000 uu** |
>
> **La vitesse excédentaire ne dure plus qu'un tiers de ce qu'elle durait.** C'est ce que visait le
> constat du J6 — « c'est un peu trop simple d'accumuler de la vitesse sans la perdre ».
>
> ⚠️ **Statut : à confirmer manche en main.** Vérifié en PIE que le composant lit bien `800` / `0.25`
> au `BeginPlay`, mais la sensation n'a pas encore été jugée. Le signal le plus lisible est le
> **gap de 1200 uu de la zone K** (`SPEC_MOVEMENT §13.2`) : on sort de la rampe à ~2100 uu/s et on a
> 2716 uu de deck avant de sauter. À 800 uu/s², ces 2716 uu coûtent maintenant assez de vitesse pour
> que le saut devienne serré — **si le gap n'est plus franchissable sans dash, c'est trop fort.**
| `SpeedRetention_Landing` | 0.92 | ratio | À CALIBRER | vitesse conservée à l'atterrissage |
| `SpeedRetention_Jump` | 1.0 | ratio | À CALIBRER | saut = pas de perte horizontale |
| `Speed_IdleThreshold` | 50 | uu/s | À CALIBRER | en dessous et sans input → état `Idle` |
| `Input_MoveDeadZone` | 0.05 | ratio | À CALIBRER | norme mini de `IA_Move` pour compter comme un input (air strafe §7, dash §8) |

**Principe** : le sprint plafonne à `Speed_SprintCap`. Au-delà, la vitesse ne s'obtient
que par slide-boost, dash, wall ride et bunny hop, et **décroît** si le joueur ne fait plus rien.

---

## 4. Sprint

| Clé | Valeur | Unité | Statut |
|---|---|---|---|
| `Sprint_TimeToMax` | 0.6 | s | À CALIBRER |
| `Sprint_RequiresForwardInput` | true | bool | À CALIBRER |
| `Sprint_Mode` | **Hold to WALK** | — | À CALIBRER (option dans Settings) |

> **On court par défaut (J4, `D25`).** La course est l'essence du jeu : elle ne se mérite pas,
> elle se subit. `Speed_SprintCap` (1500) est la vitesse **par défaut** ; `Shift` **maintenu** fait
> retomber à `Speed_Walk` (1000).
>
> L'inversion est faite dans `BP_PlayerCharacter.SetWalkInput` — `SetSprintHeld(NOT bHeld)` —
> et **pas** dans `BPC_MovementState`, dont la sémantique interne (`bSprintHeld` = « le joueur veut
> courir ») reste correcte. `BeginPlay` appelle `SetWalkInput(false)` une fois, sinon on marcherait
> jusqu'au premier appui sur `Shift`.
>
> L'asset s'appelait `IA_Sprint` ; **renommé en `IA_Walk` au J4** (2026-08-19), avec la fonction
> `SetSprintInput` → **`SetWalkInput`**. Plus aucun nom ne ment sur ce qu'il fait.

---

## 5. Slide

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Slide_MinEntrySpeed` | 900 | uu/s | ⛔ **INACTIVE** | supprimée du code au J4 (`D30`) : maintenir `Ctrl` au sol déclenche **toujours** un slide, quelle que soit la vitesse |
| `Slide_EntryBoost` | **0** | uu/s | À CALIBRER | **passé de 400 à 0 au J4** — le slide ne crée plus de vitesse sur le plat (`D24`). Reste un bouton si un petit coup de pouce s'avère nécessaire |
| `Slide_HoldTime` | 1.0 | s | À CALIBRER | **durée pendant laquelle la vitesse est strictement conservée**, décroissance zéro. Se **réarme** dès qu'une pente fait ré-accélérer |
| `Slide_SlopeMinSin` | 0.1 | sin(θ) | À CALIBRER | pente minimale (≈ 5.7°) pour qu'un slide démarre **sans condition de vitesse** |
| `Slide_TurnRate` | 720 | °/s | À CALIBRER | **vitesse de virage du slide** : la vélocité pivote vers le regard à cette cadence. 720 = un **demi-tour en 0.25 s**. C'est *le* curseur de la mécanique |
| `Slide_MaxDuration` | 3.0 | s | ⛔ **INACTIVE** | ne met plus fin au slide (`D30`). Le compteur tourne encore et s'affiche dans l'overlay (`decay x / 3.00`), **à titre indicatif seulement** |
| `Slide_Friction` | **0.15** | —/s | À CALIBRER | coefficient de décroissance exponentielle, **appliqué seulement après `Slide_HoldTime`**. **Passé de 0.4 à 0.15 au J4** : ça tombait trop vite, un long tunnel devenait infranchissable |
| `Slide_ExitSpeedMin` | 1200 | uu/s | ⛔ **INACTIVE** | supprimée du code au J4 (`D30`) : on peut rester en slide **jusqu'à 0 uu/s** tant que la touche est tenue |
| `Slide_SlopeAccelBonus` | 1800 | uu/s² | À CALIBRER | accélération **vectorielle vers l'aval**, multipliée par `sin(pente)` : 466 / 900 / 1273 uu/s² à 15° / 30° / 45°. Repère : la gravité réelle donnerait `2.4 g × sin θ` = 1176 uu/s² à 30° |
| `Slide_Cooldown` | 0.25 | s | ⛔ **INACTIVE** | l'anti-spam protégeait le boost d'entrée, qui vaut désormais 0. Un cooldown créerait un état « je tiens `Ctrl` et je ne slide pas » — interdit (`D30`) |
| `Slide_JumpWindow` | 0.20 | s | ⛔ **jamais implémentée** | le saut conserve déjà 100 % du momentum (`SpeedRetention_Jump = 1.0`), la fenêtre n'a pas d'objet en l'état |
| `Slide_CameraDrop` | 40 | uu | À CALIBRER | descente caméra — **pas de code au J4** : le crouch du CMC fait déjà descendre la caméra de 44 uu (`D21`) |
| `Slide_CameraTilt` | 6 | ° | À CALIBRER | **reporté au J14** (juice) |

> ### Le modèle de slide (refondu au J4 après playtest — `D24`)
>
> **Le slide ne crée jamais de vitesse sur le plat. Il la préserve.** C'est un outil de *virage*,
> pas un accélérateur. Le premier prototype donnait +400 uu/s gratuits à chaque appui : trop fort,
> aucune difficulté mécanique. Refondu.
>
> **Trois phases, par frame :**
>
> 1. **Pente** — accélération **vectorielle vers l'aval** :
>    `Velocity.XY += (FloorNormal.X, FloorNormal.Y) × Slide_SlopeAccelBonus × dt`.
>    Les composantes horizontales de la normale pointent déjà vers l'aval et ont pour norme `sin(θ)` :
>    la mise à l'échelle par l'inclinaison est **gratuite et exacte**. Comme c'est vectoriel et non
>    scalaire, ça fonctionne **à l'arrêt** — on se laisse glisser sans toucher à l'avant.
>    En montée, le même vecteur freine. Aucun cas particulier.
> 2. **Conservation** — tant que `Slide_HoldTime` n'est pas épuisée, la vitesse est **strictement
>    conservée**, décroissance nulle. C'est la fenêtre où l'on tourne à 180° sans rien perdre.
> 3. **Décroissance** — ensuite seulement : `Speed -= Slide_Friction × Speed × dt`.
>
> **Le compteur se réarme dès que la pente fait ré-accélérer** (`newSpeed > oldSpeed`). Rejoindre une
> descente en plein slide relance donc 1 s de conservation derrière. `Slide_MaxDuration` ne compte
> que le temps de décroissance : une pente ne consomme pas ce budget.
>
> **Le virage est piloté angulairement, pas par l'accélération du CMC** (`D26`). Compter sur
> `MaxAcceleration` pour tourner était l'erreur : à 2500 uu/s, inverser sa course demande 5000 uu/s
> de changement, soit **1.25 s** à 4000 uu/s² — d'où la sensation de « glisser sur le sol sans
> pouvoir tourner ». Désormais `BPC_Slide` fait **pivoter le vecteur vitesse vers le regard** à
> `Slide_TurnRate` °/s, norme conservée. `720 °/s` = demi-tour en **0.25 s**, ça accroche.
>
> **On ne peut pas accélérer accroupi.** `BPC_Slide` écrit `CMC.MaxWalkSpeedCrouched = vitesse
> courante` à chaque frame : à 0 uu/s on ne bouge pas, même en poussant l'avant. Cette clé prime
> sur `MaxWalkSpeed` dès que le personnage est accroupi (cf. `12_PIEGES_OUTILLAGE §6.6`).
>
> **Exception obligatoire — le dé-crouch bloqué** (`D27`). Accroupi **sous un plafond bas**, ce
> plafond de 0 uu/s est un **softlock** : on ne peut plus ni se lever ni bouger. Quand
> `bForcedSlide` est vrai, le plancher passe donc à **`Speed_Walk`** : on rampe pour sortir, et
> comme 1000 > `Slide_MinEntrySpeed` (900), un nouvel appui sur `Ctrl` relance un slide.
>
> **Chiffres du modèle** (entrée à 1500 uu/s sur du plat) : 1 s à vitesse constante, puis
> décroissance à 0.15 → `Slide_ExitSpeedMin` (1200) atteint après **1.5 s**, soit **~3500 uu**
> parcourus. Entrée à 2500 (après un air strafe) : `Slide_MaxDuration` (3 s) devient le
> déclencheur, pour **~8000 uu**. Le tunnel de la zone B fait 4000 uu.
>
> Pendant le slide, `CMC.GroundFriction` et `BrakingDecelerationWalking` sont mis à **0** : toute la
> dynamique est pilotée par `BPC_Slide`, sans double comptage.
>
> ### `D30` — maintenir la touche **est** l'état slide
>
> Règle unique, sans exception : **au sol, `IA_Slide` tenu ⇒ on est en `Sliding`.**
> Il ne doit exister **aucun** instant où le joueur tient la touche et n'est pas en slide.
> Toutes les gardes de sortie et d'entrée qui pouvaient créer cet écart ont été supprimées —
> d'où les 4 clés `INACTIVE` ci-dessus.
>
> - **Entrée** : aucune condition de vitesse, de pente ni de cooldown. Retentée **chaque frame**
>   tant que la touche est tenue, donc l'atterrissage touche-tenue déclenche le slide au contact,
>   sans fenêtre de buffer à respecter.
> - **Sortie** : **relâche de la touche** ou **perte du sol**. Rien d'autre.
> - On peut donc rester accroupi-slide **jusqu'à 0 uu/s**. C'est voulu : la vitesse se gère par
>   la décroissance, pas par un seuil qui éjecte le joueur de l'état.
>
> **Direction** : la cible du virage est `regard + strafe`, pas le regard seul —
> `ActorForward × Move.Y + ActorRight × Move.X`, et le regard seul si l'input est nul.
> `Q`/`D` infléchissent donc la trajectoire en plus de la souris (`D31`).
>
> La table d'états autorise `Idle → Sliding` et `Walking → Sliding` (`D23`) : le slide ne dépend
> ni du sprint, ni de la vitesse.

---

## 6. Saut & bunny hop

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Jump_ZVelocity` | 900 | uu/s | À CALIBRER | |
| `Jump_MaxCount` | 1 | — | À CALIBRER | pas de double jump (le dash le remplace) |
| `Jump_CoyoteTime` | 0.12 | s | À CALIBRER | |
| `Jump_BufferTime` | 0.15 | s | À CALIBRER | saut anticipé avant l'atterrissage |
| `BHop_PerfectWindow` | 0.10 | s | ⛔ **COUPÉ — D52** | |
| `BHop_SpeedGain` | 120 | uu/s | ⛔ **COUPÉ — D52** | |
| `BHop_MaxChainGain` | 1500 | uu/s | ⛔ **COUPÉ — D52** | |
| `BHop_FrictionSkip` | true | bool | ⛔ **COUPÉ — D52** | |

> ### ⛔ D52 — le bunny hop est coupé du scope (playtest J7, 2026-08-19)
>
> **Verdict de Louis, manche en main** : « le bunny hop rajoute trop de vitesse, je n'aime pas ;
> juste avant c'était vraiment bien ». **Le gain de vitesse reste l'affaire du seul air strafe.**
>
> Implémenté le 2026-08-19, **supprimé le même jour** après essai. `BPC_MovementState` est revenu
> exactement à son état du J6 : 15 nœuds dans `DoJump`, 37 dans le Tick, 33 fonctions,
> 61 variables — vérifié compteur par compteur.
>
> **Les 4 clés restent dans ce tableau, avec leurs valeurs**, pour que la décision soit lisible et
> réversible. Elles ne sont lues par aucun code. Le DataAsset `PDA_MovementData` les expose toujours.
>
> C'est la boucle `10_DEFINITION_OF_DONE §2` appliquée telle quelle : *prototype → test → pas fun →
> **supprimer***. La feature était fonctionnelle et mesurée (2000 → 2120 uu/s) ; ce n'est pas un bug
> qui l'a tuée, c'est le game feel. Une deuxième source de vitesse par-dessus l'air strafe rendait
> l'accumulation trop facile — même famille de constat que **D24** sur le slide (« trop grand boost
> sans aucun effort »).
>
> **Ne pas la réimplémenter sans un arbitrage explicite de Louis.** Si elle revient un jour, le
> chemin est documenté dans `Docs/Journal/2026-08-19_J7_BunnyHop.md`.

---

## 7. Air strafe

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `AirStrafe_AirControl` | 0.85 | ratio | À CALIBRER | passé de 0.55 au J3 : contrôle aérien jugé inexistant au playtest |
| `AirStrafe_MaxAccel` | 4000 | uu/s² | À CALIBRER | clamp #1 du modèle. Doit rester **au-dessus** de `SpeedGainPerSec`, sinon c'est lui qui borne le gain |
| `AirStrafe_GainAngleMax` | 60 | ° | À CALIBRER | angle max input/vélocité donnant du gain |
| `AirStrafe_SpeedGainPerSec` | 1200 | uu/s² | À CALIBRER | clamp #2, **c'est lui qui borne le gain en pratique** |
| `AirStrafe_NoGainAboveSpeed` | 5000 | uu/s | À CALIBRER | plafond du gain aérien |
| `AirStrafe_WishSpeedCap` | 1500 | uu/s | **VALIDÉ 2026-08-19** | **la clé du modèle.** Doit valoir `Speed_SprintCap` → modèle **Quake 3** : le strafe fonctionne en diagonale (`Z+Q` / `Z+D` + souris). Une valeur basse donne le modèle Quake 1/CPMA, où il faut lâcher `Z` |

**Modèle retenu** : accélération vectorielle style Quake/Source (projection de la vélocité sur
la direction d'input, gain si l'angle est dans `GainAngleMax`). C'est ce qui rend le bunny hop
et le strafe *apprenables* plutôt qu'aléatoires.

> **Quel modèle d'air strafe ? (tranché au J3, validé en playtest)**
> Il en existe deux, et ils **ne se jouent pas pareil** :
>
> | Modèle | `WishSpeedCap` | Comment on strafe |
> |---|---|---|
> | Quake 1 / CPMA | ~30 (bridé, bas) | touche latérale **seule** — il faut lâcher `Z` |
> | **Quake 3 ← retenu** | = vitesse de course | **`Z+Q` / `Z+D` + souris**, la diagonale naturelle |
>
> La garde du gain est `AddSpeed = WishSpeedCap − Dot(vitesse, direction_input)`. En diagonale
> l'input est à 45° de la vitesse, donc à 1500 uu/s la projection vaut `1500 × cos(45°) ≈ 1060` :
> avec un `WishSpeedCap` bas, `AddSpeed` est négatif et **aucun gain n'est possible**.
> C'est le modèle Quake 3 qu'attend un joueur de FPS arcade — validé manche en main.
>
> **Plafond atteignable = `WishSpeedCap / cos(angle)`** : 2121 uu/s en diagonale à 45°,
> davantage à mesure qu'on élargit l'angle à la souris. C'est là qu'est le skill.
>
> **`AirStrafe_WishSpeedCap` suit `Speed_SprintCap`.** Si le sprint cap bouge, cette clé bouge avec.
> Idem pour `_SpeedGainPerSec`, calé sur `sv_airaccelerate × wishspeed` de Quake rééchelonné
> (`300 u/s² × 1500/320 ≈ 1400`, arrondi prudent à 1200).

---

## 8. Dash

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Dash_Distance` | 900 | uu | À CALIBRER | |
| `Dash_Duration` | 0.16 | s | À CALIBRER | court et sec |
| `Dash_Cooldown` | 1.4 | s | À CALIBRER | |
| `Dash_MaxCharges` | 1 | — | À CALIBRER | upgrade peut monter à 2 |
| `Dash_SpeedRetention` | 1.0 | ratio | À CALIBRER | **conserve la vitesse horizontale (GDD §13)** |
| `Dash_MinExitSpeed` | 1400 | uu/s | À CALIBRER | plancher de sortie |
| `Dash_GravityScale` | 0.0 | ×G | **INACTIVE** | l'apesanteur est obtenue en réécrivant `Velocity` chaque frame, pas via `GravityScale` (**D31**) |
| `Dash_ZLockOnGround` | true | bool | **INACTIVE** | le dash suit le regard, pitch compris, au sol comme en l'air (**D37**, playtest J5) |
| `Dash_FOVKick` | +12 | ° | À CALIBRER | |
| `Dash_FOVReturnSpeed` | 8.0 | — | À CALIBRER | vitesse du `FInterpTo` qui ramène le FOV (≈ 0.3 s). Ajoutée au J5 |
| `Dash_IFrames` | 0.0 | s | À CALIBRER | **par défaut : pas d'invincibilité** |

**Valeur dérivée** (calculée au `BeginPlay`, pas une clé) :
`DashSpeed = Dash_Distance / Dash_Duration` = **5625 uu/s**. C'est la vitesse *pendant* les 0.16 s,
pas la vitesse de sortie.

**Décision** : le dash **ne donne pas** de gros boost de vitesse (GDD §13). Il sert à réorienter,
franchir, atteindre un mur. Si en playtest il paraît mou, augmenter `Dash_Distance` avant `SpeedRetention`.

> **D30 — la vitesse de sortie n'est pas la vitesse de dash.** À la sortie, la norme repart à
> `max(VitesseEntrée × Dash_SpeedRetention, Dash_MinExitSpeed)` — **pas** à 5625.
> Le dash est donc une **réorientation à norme conservée** : on garde sa vitesse, on change sa
> direction à 360°. Sans ça, `TargetSpeed = max(EntrySpeed, DashSpeed)` de `SPEC_MOVEMENT §8 [3]`
> offrirait 5625 uu/s gratuits à chaque appui et le dash deviendrait *la* mécanique de vitesse,
> ce que le GDD §13 interdit explicitement.

> **D38 — la vitesse d'entrée se lit sur la vélocité réelle du CMC, pas sur `HorizontalSpeed`.**
> `BPC_MovementState.HorizontalSpeed` est calculée au tick de `BPC_MovementState`, qui s'exécute
> **avant** `BPC_Dash` (D32) : au moment où `StartDash` la lisait, elle avait **une frame de retard**.
> En enchaînant slide et dash, la valeur mémorisée pouvait donc être celle du dash précédent —
> et le joueur ressortait à 5625 uu/s au lieu de sa vraie vitesse, en boucle.
> `StartDash` lit désormais `CMC.Velocity` directement. **Signalé par Louis au playtest J5** :
> « en slidant et dashant tout le temps je suis constamment à 5625 uu/s ».

---

## 9. Wall ride

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `WallRide_MinEntrySpeed` | 1200 | uu/s | À CALIBRER | |
| `WallRide_MaxDuration` | **0** | s | **INACTIVE — VALIDÉ 2026-08-19** | **Playtest J6** : accroche **illimitée** (**D47**). `0` = pas de sortie par durée. Une valeur > 0 la réactive |
| `WallRide_MaxWallAngle` | 20 | ° | À CALIBRER | écart max à la verticale |
| `WallRide_DetectDistance` | 70 | uu | À CALIBRER | trace latérale depuis la capsule |
| `WallRide_GravityScale` | **0** | ×G | **INACTIVE — VALIDÉ 2026-08-19** | **Playtest J6** : plus de glisse vers le bas, **l'altitude est verrouillée** pendant le ride (**D47**) |
| `WallRide_SpeedRetention` | **1.0** | ratio/s | **VALIDÉ 2026-08-19** | **Playtest J6** : la vitesse est conservée **exactement**, ni gain ni perte (**D47**) |
| `WallRide_UpwardBoost` | **0** | uu/s | **INACTIVE — VALIDÉ 2026-08-19** | **Playtest J6** : on s'accroche **à l'horizontale**, sans pop vertical (**D47**) |
| `WallJump_ZVelocity` | **1200** | uu/s | **VALIDÉ 2026-08-19** | **Playtest J6** : 800 était **sous** `Jump_ZVelocity` (900) — le wall jump sautait moins haut qu'un saut normal (**D48**) |
| `WallJump_AwayVelocity` | **1000** | uu/s | **VALIDÉ 2026-08-19** | poussée perpendiculaire au mur (**D48**) |
| `WallJump_ForwardBoost` | 300 | uu/s | **VALIDÉ 2026-08-19** | gain dans l'axe du regard — inchangé depuis le J1, validé tel quel |
| `WallRide_SameWallCooldown` | 0.6 | s | À CALIBRER | empêche de camper un seul mur |
| `WallRide_CameraTilt` | 12 | ° | **VALIDÉ 2026-08-19** | roulis **vers l'extérieur** — câblé au J6 (**D49**). Signe : `Roll = −WallSide × CameraTilt`. Une valeur **négative** inverse le sens |
| `WallRide_CameraTiltSpeed` | 10 | /s | **VALIDÉ 2026-08-19** | **J6** — vitesse du `FInterpTo` du roulis, aller **et** retour |
| `WallRide_TraceInterval` | 0.03 | s | À CALIBRER | fréquence des traces de détection (~33 Hz), **accumulateur dans le Tick** et non timer (**D43**) |
| `WallRide_DetachDotThreshold` | 0.7 | — | **VALIDÉ 2026-08-19** | **J6** — `Dot(WishDir, Normal)` au-delà duquel l'input compte comme « je pousse loin du mur » (`SPEC_MOVEMENT §9.2`) |
| `WallRide_DetachHoldTime` | 0.1 | s | **VALIDÉ 2026-08-19** | **J6** — durée de maintien avant décrochage volontaire |
| `WallRide_MissedTraceTolerance` | 2 | — | À CALIBRER | **J6** — évaluations négatives consécutives avant de lâcher le mur (anti-flicker sur les joints de modules) |

Surfaces éligibles : object type **`WallRideSurface`** (cf. `Docs/06_CONVENTIONS.md §7`).
Pas de wall ride sur les props ni sur les ennemis.

> Le wall ride réutilise aussi `Capsule_Radius`, `Capsule_HalfHeight`, `MaxStepHeight` (§2),
> `Speed_HardCap` (§3), `MomentumDecay_GraceTime` (§3), `Input_MoveDeadZone` (§3) et `Gravity` (§2).
> `Capsule_HalfHeight + MaxStepHeight` = **138 uu** sert de portée à la trace de sol qui met fin au
> ride (**D45**) — même calibrage que la trace de pente du slide (`12_PIEGES_OUTILLAGE §6.8`).

---

## 10. Perte de vitesse (punition)

| Événement | Perte | Statut | Note |
|---|---|---|---|
| Projectile ennemi encaissé | **−45 %** de la vitesse actuelle | À CALIBRER | GDD §15 : ça doit faire mal |
| Melee ennemi encaissé | −60 % | À CALIBRER | |
| Collision frontale (angle > 60°) à > 2500 uu/s | −50 % + camera shake | À CALIBRER | |
| Collision rasante (angle < 30°) | 0 % (on glisse le long) | À CALIBRER | GDD §16 |
| `SpeedLoss_Collision_MidAngle` (30°–60°) | `Lerp(0, 0.50, InverseLerp(30, 60, Angle))` | À CALIBRER | zone intermédiaire, transition continue |
| Arrêt volontaire (relâcher input) | `MomentumDecayRate` | À CALIBRER | |
| Chute hors niveau | reset checkpoint | — | |
| `SpeedLoss_RecoveryGrace` | 0.5 s sans décroissance après un hit | À CALIBRER | permet de rebondir |

**Principe GDD §15** : *erreur = perte de vitesse*, jamais *erreur = mort immédiate*.

---

## 11. Laser

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Laser_Damage_Body` | 34 | pv | À CALIBRER | 3 tirs sur un Grunt |
| `Laser_Damage_Head` | 100 | pv | À CALIBRER | **one-shot Grunt** (GDD §23) |
| `Laser_HeadshotMultiplier` | 3.0 | × | À CALIBRER | alternative au chiffre absolu |
| `Laser_Range` | 15000 | uu | À CALIBRER | 150 m |
| `Laser_FireCooldown` | 0.18 | s | À CALIBRER | ~5.5 tirs/s max, semi-auto |
| `Laser_TraceRadius` | 0 | uu | À CALIBRER | 0 = line trace pur ; >0 = aide à la visée |
| `Laser_Spread` | 0 | ° | À CALIBRER | **précision parfaite, c'est un laser** |
| `Laser_RecoilPitch` | 1.2 | ° | À CALIBRER | remonte, retour auto |
| `Recoil_ReturnInterpSpeed` | 12 | /s | À CALIBRER | vitesse de retour du kick caméra |

### Heat

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Heat_Max` | 100 | — | À CALIBRER | |
| `Heat_PerShot` | 11 | — | À CALIBRER | ≈ 9 tirs avant overheat |
| `Heat_DecayRate` | 45 | /s | À CALIBRER | |
| `Heat_DecayDelay` | 0.5 | s | À CALIBRER | délai après le dernier tir |
| `Heat_OverheatDuration` | 1.5 | s | À CALIBRER | verrou dur |
| `Heat_OverheatExitThreshold` | 25 | — | À CALIBRER | on peut retirer sous ce seuil |
| `Heat_OverheatDecayMultiplier` | 1.5 | × | À CALIBRER | refroidit plus vite en overheat |
| `Heat_WarningThreshold` | 75 | — | À CALIBRER | déclenche le feedback UI/son |
| `Heat_TickInterval` | 0.05 | s | À CALIBRER | fréquence du timer de décroissance (20 Hz) |

**Overcharge (upgrade)** : premier tir après refroidissement complet (`Heat = 0`) → `×2.0` dégâts. [À CALIBRER]

> **Précision** : `Laser_Damage_Head` est **dérivé** de `Laser_Damage_Body × Laser_HeadshotMultiplier`.
> La source de vérité est le **multiplicateur** ; la valeur absolue n'est là que comme repère de lecture.

---

## 12. Melee

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Melee_Damage` | 60 | pv | À CALIBRER | |
| `Melee_Range` | 220 | uu | À CALIBRER | |
| `Melee_Radius` | 60 | uu | À CALIBRER | sphere trace |
| `Melee_Cooldown` | 0.55 | s | À CALIBRER | |
| `Melee_WindupTime` | 0.06 | s | À CALIBRER | quasi instantané |
| `Melee_Knockback` | 3500 | uu/s | À CALIBRER | **très fort (GDD §24)** |
| `Melee_KnockbackUp` | 300 | uu/s | À CALIBRER | légère composante verticale |
| `Melee_HitStop` | 0.06 | s | À CALIBRER | time dilation 0.05 |
| `WallSlam_MinImpactSpeed` | 1500 | uu/s | À CALIBRER | seuil de dégâts muraux |
| `WallSlam_Damage` | 200 | pv | À CALIBRER | **tue tout sauf le Tank** |
| `WallSlam_DamagePerSpeed` | 0.08 | pv / (uu/s) | À CALIBRER | **pente** : dégâts = `Speed × cette valeur` |
| `Knockback_MaxFlightTime` | 1.2 | s | À CALIBRER | durée max de l'état « en vol » vulnérable au slam |
| `Knockback_RecoverTime` | 0.8 | s | À CALIBRER | relevé après atterrissage sans impact mural |
| `Melee_SelfPropulsion` | 0 | uu/s | EXPÉRIMENTAL | hors MVP (GDD §26) |

> **Précision** : `WallSlam_Damage` est le **plafond**, `WallSlam_DamagePerSpeed` la **pente**.
> Formule : `Damage = Min(WallSlam_Damage, ImpactSpeed × WallSlam_DamagePerSpeed)`.

> **`Corpse_LifeSpan` a été supprimée** (`11_ARBITRAGES D24`). Il n'y a pas de cadavre :
> à la mort, l'ennemi joue un dissolve puis est détruit. Le **seul** délai est
> **`Death_DissolveDuration`** (§13, *Comportement & budget IA*). Aucun ragdoll, jamais (D5).

---

## 13. Ennemis

| | Grunt | Shooter | Tank |
|---|---|---|---|
| `MaxHealth` | 100 | 80 | 400 |
| Headshot = kill | **oui** | oui | non (×3 dmg) |
| `MoveSpeed` | 550 | 350 | 250 |
| `DetectionRange` | 3000 | 5000 | 3500 |
| `AttackRange` | 200 (charge) | 4500 | 350 |
| `AttackCooldown` | 1.5 s | 2.2 s | 2.5 s |
| `Damage` | 12 | 15 | 30 |
| Perte de vitesse infligée | −45 % | −45 % | −60 % |
| `ScoreBase` | 100 | 150 | 400 |
| `TimeToKill` cible | < 0.3 s | < 0.4 s | < 2 s |

Toutes ces valeurs : **À CALIBRER**. Elles vivent dans `DA_Enemy_*` (cf. `Docs/08_DATA_SCHEMAS.md`).

### Projectile Shooter

| Clé | Valeur | Statut |
|---|---|---|
| `Projectile_Speed` | 2200 uu/s | À CALIBRER |
| `Projectile_Radius` | 25 uu | À CALIBRER |
| `Projectile_LifeTime` | 5 s | À CALIBRER |
| `Projectile_Homing` | 0 | À CALIBRER — **pas de homing dans le MVP** |

| `Projectile_LeadFactor` | 0 | À CALIBRER — **pas d'anticipation de tir au MVP** |

Le projectile doit être **visible et évitable** à 3000 uu/s de vitesse joueur. C'est le critère
de validation, pas le chiffre.

### Comportement & budget IA

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `EnemyScan_Rate` | 0.2 | s | À CALIBRER | scan de distance centralisé dans `BP_LevelManager` |
| `EnemyScan_Hysteresis` | 400 | uu | À CALIBRER | marge ajoutée au seuil de désactivation pour éviter le clignotement actif/inactif en bordure |
| `MaxLOSTracesPerScan` | 6 | — | À CALIBRER | budget de traces de ligne de vue par passe de scan, réparti en round-robin |
| `DeactivateBehindDistance` | 6000 | uu | À CALIBRER | au-delà et **derrière** le joueur, l'ennemi est désactivé (`BP_EnemyActivationVolume`) |
| `Enemy_MaxEngagedSimultaneous` | 8 | — | À CALIBRER | budget CPU IA |
| `Grunt_ChargeWindup` | 0.4 | s | À CALIBRER | télégraphe de la charge |
| `Grunt_RepathRate` | 0.4 | s | À CALIBRER | fréquence de recalcul du chemin (timer, jamais Tick) |
| `Shooter_TelegraphTime` | 0.5 | s | À CALIBRER | pré-tir visible |
| `Shooter_TurnRate` | 180 | °/s | À CALIBRER | vitesse de rotation vers le joueur — assez lente pour qu'un strafe rapide la prenne à défaut |
| `Tank_WindupTime` | 0.8 | s | À CALIBRER | télégraphe de l'attaque lourde, le plus long des 3 archétypes |
| `HitFlash_Duration` | 0.08 | s | À CALIBRER | flash blanc sur `M_Toon_Enemy` à l'encaissement (distinct du dissolve) |
| `Death_DissolveDuration` | 0.5 | s | À CALIBRER | **seul délai de mort** — remplace l'ex-`Corpse_LifeSpan` (`11_ARBITRAGES D24`) |
| `Placement_MinReactionTime` | 0.6 | s | À CALIBRER | temps de réaction mini garanti au joueur (règle de LD) |

### Knockback reçu & wall slam (côté ennemi — `BPC_KnockbackReceiver`)

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Knockback_MinImpulse` | 800 | uu/s | À CALIBRER | sous ce seuil, l'ennemi est bousculé mais n'entre pas dans l'état « en vol » slammable |
| `WallSlam_MaxNormalZ` | 0.4 | — | À CALIBRER | `abs(Hit.Normal.Z)` au-dessus de cette valeur = sol ou plafond → aucun dégât de slam |

Les dégâts eux-mêmes restent en §12 (`WallSlam_Damage`, `WallSlam_DamagePerSpeed`, `WallSlam_MinImpactSpeed`).

### Boss

| Clé | Valeur | Clé | Valeur |
|---|---|---|---|
| `Boss_TargetFightDuration` | 90 s | `Boss02_ArenaLength` | 7000 uu |
| `Boss_PhaseTransitionPause` | 0.6 s | `Boss02_DashTelegraph` / `_DashSpeed` | 0.6 s / 5000 uu/s |
| `Boss01_ArenaDiameter` | 4800 uu | `Boss02_SelfStunDuration` | 1.5 s |
| `Boss01_SweepTelegraph` / `_SweepDuration` | 0.9 s / 1.4 s | `Boss02_VolleyTelegraph` | 0.8 s |
| `Boss01_MortarCount` / `_MortarTelegraph` | 4 / 0.7 s | `Boss02_FloorBurnTelegraph` / `_Duration` | 1.2 s / 6.0 s |
| `Boss01_PulseTelegraph` / `_PulseDuration` | 1.1 s / 2.0 s | | |

Toutes `[À CALIBRER]`. `MaxHealth`, `AttackDamage`, `ScoreBase` des boss vivent dans `DA_Boss_01/02`.

> **Dimensions d'arène** : `Boss01_ArenaDiameter` = **4800 uu**, `Boss02_ArenaLength` = **7000 uu**.
> Ces deux valeurs font foi — `Docs/Specs/SPEC_LEVELDESIGN.md` doit s'y aligner, pas l'inverse.
> Justification : à 4800 uu de diamètre, traverser l'arène du Boss 01 à `Speed_SprintCap` prend ~3,2 s,
> soit plus que `Boss01_SweepTelegraph + _SweepDuration` — l'esquive reste possible sans être gratuite.
> Le couloir du Boss 02 (7000 uu) laisse ~1,4 s de réaction face au dash à 5000 uu/s.

---

## 14. Score & Rank

### Formule (v1, à calibrer)

```
Score = ( ScoreKills + ScoreSpeed + ScoreTime ) × StyleMultiplier

ScoreKills  = Σ ScoreBase(ennemi)  [+ 50 % si headshot, + 30 % si wall slam]
ScoreSpeed  = round( AvgSpeed / 10 ) × 5
ScoreTime   = max( 0, (ParTime - Time) × 100 )
```

| Clé | Valeur | Statut |
|---|---|---|
| `Style_Max` | 5.0 | À CALIBRER |
| `Style_Start` | 1.0 | À CALIBRER |
| `Style_DecayPerSec` | 0.25 | À CALIBRER |
| `Style_DecayDelay` | 2.0 s | À CALIBRER |
| `Style_Gain_Kill` | +0.15 | À CALIBRER |
| `Style_Gain_Headshot` | +0.35 | À CALIBRER |
| `Style_Gain_MeleeKill` | +0.30 | À CALIBRER |
| `Style_Gain_WallSlamKill` | +0.50 | À CALIBRER |
| `Style_Gain_WallRide` (par seconde) | +0.20 | À CALIBRER |
| `Style_Gain_Dash` | +0.05 | À CALIBRER |
| `Style_Gain_SlideKill` | +0.25 | À CALIBRER |
| `Style_Gain_AirKill` | +0.30 | À CALIBRER |
| `Style_Gain_HighSpeedSustain` (>3000 uu/s, /s) | +0.10 | À CALIBRER |
| `Style_Loss_TakeDamage` | −0.75 | À CALIBRER |
| `Style_Loss_Idle` (<500 uu/s pendant 1 s) | −0.50 | À CALIBRER |
| `Style_Loss_Death` | reset à 1.0 | À CALIBRER |
| `Style_MinSpeedForDashGain` | 1500 uu/s | À CALIBRER — anti-spam de dash à l'arrêt |
| `Style_DiminishPerRepeat` | 0.7 × | À CALIBRER — même event répété = gain × 0.7 cumulatif |
| `Style_Tier_Thresholds` | 1.5 / 2.5 / 3.5 / 4.5 | À CALIBRER — paliers visuels du HUD |
| `Style_ResetDiminishAfter` | 4.0 s | À CALIBRER — retour au gain plein |

> **`Style_ResetDiminishAfter`** : délai sans répétition d'un event avant que son gain redevienne plein.
> `Style_DiminishPerRepeat` (0.7 ×) s'applique en cascade tant que le **même** `E_StyleEvent` se répète
> (kill → ×1.0, kill → ×0.7, kill → ×0.49…). Si ce même event n'est pas rejoué pendant
> `Style_ResetDiminishAfter`, son compteur de répétitions repart à zéro et le gain revient à ×1.0.
> Le compteur est **par event**, pas global : enchaîner headshot / wall slam / slide kill ne diminue rien.

### Score — annexes

| Clé | Valeur | Statut |
|---|---|---|
| `Score_DeathPenalty` | −1500 pts | À CALIBRER |
| `Score_SpeedSampleRate` | 10 Hz | À CALIBRER |
| `Score_StyleTickRate` | 10 Hz | À CALIBRER |
| `Kill_HeadshotBonus` | +50 % | À CALIBRER |
| `Kill_WallSlamBonus` | +30 % | À CALIBRER |
| `Results_StepDelay` | 0.35 s | À CALIBRER — cadence d'apparition des lignes |
| `Results_TieTolerance` | 2 % | À CALIBRER — marge sous laquelle une stat n'est pas « la coupable » |
| `Boss_ScoreBase` | 2000 pts | À CALIBRER |
| `Boss_PhaseClearBonus` | +500 pts | À CALIBRER |
| `Boss_NoHitBonus` | +2000 pts | À CALIBRER |
| `Boss_DamagePenaltyPerHit` | −150 pts | À CALIBRER |

### Seuils de rank
Définis **par niveau** dans `DA_Level_*` (cf. `Docs/08_DATA_SCHEMAS.md`), pas globalement.
Méthode : Louis fait un run « propre mais pas parfait » → c'est le seuil **A**.
```
S = ParScore × 1.00     (temps expert, ~100 % kills, style ≥ 4.0)
A = ParScore × 0.80
B = ParScore × 0.60
C = ParScore × 0.40
D = en dessous
```

---

## 15. Loot & upgrades

### Drop rates par coffre

| Coffre | Common | Rare | Epic | Nb de choix |
|---|---|---|---|---|
| D | 100 % | 0 % | 0 % | 1 |
| C | 85 % | 15 % | 0 % | 1 |
| B | 65 % | 35 % | 0 % | 2 |
| A | 40 % | 50 % | 10 % | 2 |
| S | 15 % | 55 % | 30 % | 3 |

Toutes `[À CALIBRER]`. Le joueur choisit **1 upgrade parmi N** propositions.

### Valeurs d'upgrade par rareté

| Upgrade | Common | Rare | Epic |
|---|---|---|---|
| `+MaxHealth` | +15 | +30 | +50 |
| `+LaserDamage` | +8 % | +18 % | +30 % |
| `+MeleeDamage` | +12 % | +25 % | +45 % |
| `+MaxSpeed` (hard cap) | +5 % | +10 % | +18 % |
| `+Acceleration` | +10 % | +20 % | +35 % |
| `+SpeedRetention` | +2 % | +4 % | +7 % |
| `+DashRecharge` (cooldown) | −10 % | −20 % | −33 % |
| `+SlideBoost` | +15 % | +30 % | +50 % |
| `+WallRideDuration` | +20 % | +40 % | +70 % |
| `+HeatCapacity` | +15 % | +30 % | +50 % |
| `+HeatRecovery` | +15 % | +30 % | +55 % |
| `+DashCharges` | — | — | +1 |

Modificateurs de gameplay (Rare/Epic uniquement) : `Dash Recharge on Kill` (−0.25 s/kill),
`Overcharged Laser` (×2 premier tir), `Momentum Core` (+SpeedRetention saut), `Impact` (+50 % knockback),
`Thermal Core` (heat decay ×1.5). Toutes `[À CALIBRER]`.

**Garde-fou (GDD §49)** : cumul maximum d'une même stat = **+100 %** sur une run.

| Clé | Valeur | Statut |
|---|---|---|
| `StatCapUp` | +100 % | À CALIBRER — plafond de cumul à la hausse |
| `StatCapDown` | −60 % | À CALIBRER — plafond de réduction (`DashCooldown`) |
| `Modifier_OverchargedLaser_RechargeWindow` | 0.5 s | À CALIBRER |
| `Loot_ChestOpenDuration` | 1.2 s | À CALIBRER |
| `Loot_CardRevealStagger` | 0.15 s | À CALIBRER |
| `Loot_CardFlyToHUDDuration` | 0.4 s | À CALIBRER |

---

## 16. Caméra & juice

| Clé | Valeur | Unité | Statut |
|---|---|---|---|
| `FOV_Base` | 100 | ° | À CALIBRER (réglable dans Settings 80–120) |
| `FOV_MaxAdditive` | +25 | ° | À CALIBRER |
| `FOV_SpeedForMax` | 4000 | uu/s | À CALIBRER |
| `FOV_InterpSpeed` | 6 | /s | À CALIBRER |
| `CameraTilt_Strafe` | 2.5 | ° | À CALIBRER |
| `CameraTilt_InterpSpeed` | 8 | /s | À CALIBRER |
| `CameraRoll_ClampMax` | 15 | ° | À CALIBRER — plafond dur du roulis caméra, toutes sources cumulées (strafe + wall ride) |
| `Shake_LaserFire` | 0.15 | scale | À CALIBRER |
| `Shake_Headshot` | 0.35 | scale | À CALIBRER |
| `Shake_MeleeHit` | 0.5 | scale | À CALIBRER |
| `Shake_TakeDamage` | 0.8 | scale | À CALIBRER |
| `Shake_HardCollision` | 1.0 | scale | À CALIBRER |
| `Shake_WallSlam` | 0.7 | scale | À CALIBRER |
| `HitStop_MinInterval` | 0.25 | s | À CALIBRER — anti-empilement |
| `DamageIndicator_FadeTime` | 1.0 | s | À CALIBRER |
| `SpeedLines_StartSpeed` | 2500 | uu/s | À CALIBRER |
| `SpeedLines_FullSpeed` | 5000 | uu/s | À CALIBRER |
| `ChromaticAberration_MaxAtFullSpeed` | 1.5 | — | À CALIBRER |
| `HitStop_Headshot` | 0.05 | s | À CALIBRER |
| `HitStop_TimeDilation` | 0.05 | — | À CALIBRER |
| `Restart_FadeDuration` | 0.15 | s | À CALIBRER — **le restart doit être quasi instantané** |

### Échelles de confort (Settings joueur)

Trois multiplicateurs exposés dans les Settings. **Défaut `1.0`, plage `0.0 – 1.0`** : le joueur ne peut
qu'**atténuer**, jamais amplifier au-delà du réglage d'auteur. À `0.0`, l'effet est totalement désactivé.

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `FOVSpeedEffectScale` | 1.0 | ratio 0–1 | À CALIBRER | multiplie `FOV_MaxAdditive` et `Dash_FOVKick` |
| `TiltScale` | 1.0 | ratio 0–1 | À CALIBRER | multiplie `CameraTilt_Strafe`, `WallRide_CameraTilt`, `Slide_CameraTilt` |
| `ShakeScale` | 1.0 | ratio 0–1 | À CALIBRER | multiplie tous les `Shake_*` de cette section |

Ces échelles sont appliquées dans `BP_PlayerCameraManager`, **jamais** dans les assets `CS_*` eux-mêmes.

---

## 17. Niveaux

| Clé | Valeur | Statut |
|---|---|---|
| Durée cible première completion | 90–180 s | À CALIBRER |
| Durée cible run expert | 55–65 % du temps débutant | À CALIBRER |
| Ennemis par niveau | 15–30 | À CALIBRER |
| Checkpoints par niveau | 0–2 | À CALIBRER |
| Largeur mini d'un couloir de vitesse | 800 uu | À CALIBRER |
| Hauteur mini d'un espace de vitesse | 600 uu | À CALIBRER |
| Distance mini entre 2 murs de wall ride opposés | 600 uu | À CALIBRER |
| Distance maxi entre 2 murs de wall ride opposés | 1400 uu | À CALIBRER |
| **Distance de référence entre 2 murs opposés** | **1000 uu** | **VALIDÉ 2026-08-19** |

> **`1000 uu` est l'écartement de référence pour tout couloir de wall ride** (playtest J6).
> Les 3 écartements ont été construits et joués côte à côte dans le sandbox (zone E, `SPEC_MOVEMENT §13.2`) :
> avec `WallJump_AwayVelocity = 700`, **600 uu** était le meilleur ; passé à **1000**, c'est **1000 uu**
> qui gagne. Les deux bornes restent valables — 600 pour un couloir serré et nerveux, 1400 pour un
> espace ouvert — mais **c'est 1000 qui sert de défaut** dans `L_W1_*`.

---

## 18. Run & vies

Cf. `Docs/11_ARBITRAGES.md D1` pour la règle complète de portée des données.

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Run_MaxLives` | 3 | — | À CALIBRER | vies pour **toute la run** (8 niveaux), jamais rechargées |
| `Run_LivesRefillOnBoss` | false | bool | À CALIBRER | levier de secours si 3 vies s'avère trop sévère |
| `Run_LevelCount` | 8 | — | — | 6 niveaux + 2 boss |
| `Score_DeathPenalty` | voir §14 | pts | À CALIBRER | s'applique **en plus** de la perte de vie |
| `RunFailed_ScreenDuration` | 4.0 | s | À CALIBRER | avant retour au menu, skippable |

> ⚠️ **`Run_MaxLives = 3` sur 8 niveaux est agressif.** C'est le choix de Louis et il donne au jeu
> une vraie condition de défaite. Points de bascule à surveiller en playtest :
> - taux d'échec de run > 70 % chez un joueur qui connaît les niveaux → passer à 5,
>   ou activer `Run_LivesRefillOnBoss`
> - joueur qui n'ose plus prendre la ligne rapide → le système punit le risque,
>   ce qui contredit le pilier MOMENTUM. C'est le signal d'alarme le plus important.

---

## 19. Historique des calibrations

| Date | Clé | Ancien | Nouveau | Raison | Statut |
|---|---|---|---|---|---|
| 2026-08-18 | *(section §18)* | — | `Run_MaxLives = 3` | Arbitrage de Louis : ajout d'une condition de défaite | À CALIBRER |
| 2026-08-18 | `Speed_IdleThreshold` (§3) | — | `50` uu/s | J2 : la résolution d'état a besoin d'un seuil `Idle`, absent de la doc | À CALIBRER |
| 2026-08-18 | `Input_MoveDeadZone` (§3) | — | `0.05` | J2 : `SPEC_MOVEMENT §7/§8` utilisait `0.05` en dur, la clé n'existait nulle part | À CALIBRER |
| 2026-08-19 | `AirStrafe_WishSpeedCap` (§7) | `60` | `150` | **Playtest J3 de Louis** : « ça demande de trop bouger la souris ». Valeur de Quake non rééchelonnée — fenêtre de gain 2,5× trop étroite pour notre vitesse | *(remplacé, cf. ligne suivante)* |
| 2026-08-19 | `AirStrafe_WishSpeedCap` (§7) | `150` | **`1500`** | **Playtest J3 n°3** : « en Z+Q avec la caméra dans le bon côté, ça ne compte pas comme un strafe ». Mauvais **modèle** : Quake 1/CPMA (touche latérale seule) au lieu de Quake 3 (diagonale + souris). `WishSpeedCap = Speed_SprintCap` | **VALIDÉ** |
| 2026-08-19 | `AirStrafe_SpeedGainPerSec` (§7) | `300` | `1200` | Idem : c'est le clamp qui bornait le gain, à l'échelle de Quake (320 u/s) et non de la nôtre (1500 uu/s) | À CALIBRER |
| 2026-08-19 | `AirStrafe_MaxAccel` (§7) | `2500` | `4000` | Doit rester au-dessus de `SpeedGainPerSec`, sinon il redevient le clamp actif | À CALIBRER |
| 2026-08-19 | `AirStrafe_GainAngleMax` (§7) | `45` | `60` | Élargit la fenêtre angulaire de gain : seuil `cos(150°) = −0.866` au lieu de `cos(135°) = −0.707` | À CALIBRER |
| 2026-08-19 | `AirStrafe_AirControl` (§7) | `0.55` | `0.85` | **Playtest J3** : « aucune sensation de contrôle aérien » | À CALIBRER |
| 2026-08-19 | `Accel_Air` (§3) | `2500` | `4000` | Idem — c'est le multiplicande de `AirControl` : `0.85 × 4000 = 3400 uu/s²` de contrôle aérien | À CALIBRER |
| 2026-08-19 | `Dash_FOVReturnSpeed` (§8) | — | `8.0` | J5 : le retour du FOV après le kick avait besoin d'une vitesse d'interpolation, la clé n'existait nulle part | À CALIBRER |
| 2026-08-19 | `Dash_GravityScale` (§8) | `0.0` | *(inchangé)* | J5 : passée **INACTIVE**. `DriveCMC` réécrit `GravityScale` chaque frame ; l'apesanteur vient de la réécriture de `Velocity` (**D31**) | INACTIVE |
| 2026-08-19 | `Dash_ZLockOnGround` (§8) | `true` | *(inchangé)* | **Playtest J5 de Louis** : « j'aimerais un dash qui me propulse dans la direction de mon regard, pas que à l'horizontale ». Le dash suit le regard partout → clé passée **INACTIVE** (**D37**) | INACTIVE |
| 2026-08-19 | `WallRide_DetachDotThreshold` (§9) | — | `0.7` | J6 : `SPEC_MOVEMENT §9.2` utilisait `0.7` en dur, la clé n'existait nulle part (R3) | À CALIBRER |
| 2026-08-19 | `WallRide_DetachHoldTime` (§9) | — | `0.1` | J6 : idem, `0.1 s` en dur dans la spec | À CALIBRER |
| 2026-08-19 | `WallRide_MissedTraceTolerance` (§9) | — | `2` | J6 : « 2 évaluations consécutives » de `§9.2` était une constante de spec, pas une clé (R3) | À CALIBRER |
| 2026-08-19 | `WallRide_CameraTilt` (§9) | `12` | *(inchangé)* | J6 : passée EN ATTENTE (D46)… puis **câblée le jour même** sur retour de Louis (**D49**). `12°` conservé | À CALIBRER |
| 2026-08-19 | `WallRide_MaxDuration` (§9) | `2.0` | **`0`** | **Playtest J6 de Louis** : « j'aimerais vraiment avoir un temps d'accroche sur le mur infini ». `0` désactive la sortie par durée (**D47**) | INACTIVE |
| 2026-08-19 | `WallRide_GravityScale` (§9) | `0.25` | **`0`** | **Playtest J6** : « on perd de la verticalité trop vite… on ne descend pas petit à petit du mur ». Altitude verrouillée (**D47**) | INACTIVE |
| 2026-08-19 | `WallRide_UpwardBoost` (§9) | `250` | **`0`** | **Playtest J6** : « quand on touche le mur on s'y attache **à l'horizontale** ». Plus de pop vertical à l'accroche (**D47**) | INACTIVE |
| 2026-08-19 | `WallRide_SpeedRetention` (§9) | `0.98` | **`1.0`** | **Playtest J6** : « on ne gagne ni en speed ni on en perd quand on court sur le mur, on conserve exactement la même ». Vérifié : `entrySpeed == rideSpeed` au dix-millième (**D47**) | À CALIBRER |
| 2026-08-19 | `WallJump_ZVelocity` (§9) | `800` | **`1200`** | **Playtest J6** : « le saut du mur est trop faible, il faudrait un peu plus de verticalité ». **Cause trouvée** : 800 était **sous** `Jump_ZVelocity` (900) — le wall jump sautait moins haut qu'un saut normal (**D48**) | À CALIBRER |
| 2026-08-19 | `WallJump_AwayVelocity` (§9) | `700` | **`1000`** | **Playtest J6** : « se décoller un peu plus du mur » (**D48**) | À CALIBRER |
| 2026-08-19 | `WallRide_CameraTiltSpeed` (§9) | — | `10` | J6 : le roulis a besoin d'une vitesse d'interpolation, la clé n'existait nulle part (**D49**) | À CALIBRER |
| — | — | — | — | *(à remplir au prochain playtest)* | — |
