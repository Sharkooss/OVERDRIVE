# SPEC — CAMÉRA & JUICE

> Tout ce qui fait *sentir* la vitesse : FOV, tilt, shakes, hit-stop, post-process, transitions.
> **Blueprint only, UE 5.8.** Toutes les valeurs numériques renvoient à `Docs/07_TUNING.md §16`
> (et §5/§8/§9/§10/§12) par nom de clé. Aucune valeur de gameplay n'est inventée ici.
> Couleurs : `Docs/ArtDirection/PALETTE.md`. Widgets : `Docs/Specs/SPEC_UI_HUD.md`.
>
> Propriétaire du système : **`BP_PlayerCameraManager`** (`Content/OVERDRIVE/Player/Blueprints/`).
> Assets référencés ici et déclarés dans `05_ARCHITECTURE §2` : `BP_PlayerCameraManager`, `BPC_HitStop`
> (sur `PC_Overdrive`), **`BP_DeathCam`** (§9), les `CS_*` de `Player/Blueprints/Shakes/`.
>
> **Rendu ÉCLAIRÉ, Lumen et VSM ACTIFS** (D2, révisé le 2026-08-18) : le jeu se déroule dans une **ville
> blanche en plein jour**, avec de vraies ombres portées. Le cel-shading vient d'un post-process de
> **posterisation** sur cette scène éclairée, plus les outlines Sobel (`SPEC_VFX §3.2`).
> **Conséquence directe pour cette spec** : le fond de l'écran est **clair**, presque partout, presque
> toujours. Tout effet de caméra qui ajoute de la lumière (flash blanc, speed lines blanches, éclaircissement)
> **n'a plus aucun contraste**. Les effets doivent **assombrir** ou **saturer**. Voir §7.

---

## 1. Principes

**La règle qui tranche tout : « subtil mais présent ».** À 5000 uu/s le monde bouge déjà énormément :
**la caméra n'a pas besoin d'en rajouter, elle a besoin de commenter.** Un effet est bien calibré quand
*le joueur ne le remarque pas quand il est là, mais trouve le jeu « mou » quand on le retire*.
Test pour Louis : jouer 2 min avec, 2 min sans. Si l'absence ne se sent pas → on coupe l'effet.
Si la présence gêne la lecture du niveau → ÷2.

| Priorité | Règle | Ce qu'elle interdit |
|---|---|---|
| **1. Lisibilité** | On doit toujours voir où on va et où sont les ennemis. | Shake qui déplace le crosshair de la cible. Motion blur en course. Speed lines opaques au centre. |
| **2. Confort** | Aucun effet ne doit provoquer de motion sickness. | Roll non désiré, oscillation continue, head bob, FOV qui pompe, shakes qui se cumulent. |
| **3. Sensation** | La vitesse doit se *sentir*, pas se lire au HUD. | Une caméra parfaitement rigide. |

**En cas de conflit : 1 > 2 > 3, toujours.**

| Les 5 interdits | Pourquoi |
|---|---|
| **Head bob** en marche/sprint | Oscillation continue = première cause de motion sickness en FPS rapide. Le mouvement du monde suffit. |
| **Shake périodique** (idle, marche) | Un shake doit être un **événement**, jamais un état. |
| **Roll > 15° cumulé** | Au-delà, le cerveau perd l'horizon et la nausée arrive vite. |
| **FOV qui pompe** (aller-retour rapide) | Interp lente et directionnelle seulement (§2). |
| **Reprise de contrôle caméra** au joueur | Aucune cinématique, aucun lock de vue en gameplay. Le joueur garde toujours la souris. |

| Où vit quoi | Propriétaire | Mécanisme |
|---|---|---|
| FOV dynamique, tilt, offsets | `BP_PlayerCameraManager` | Override de `BlueprintUpdateCamera` — **le seul Tick caméra autorisé du projet**, justifié en commentaire. |
| Screen shakes | `BP_PlayerCameraManager.StartCameraShake` | Assets `CS_*` (`LegacyCameraShake` en BP), dans `Content/OVERDRIVE/Player/Blueprints/Shakes/` (D7, `06_CONVENTIONS §2`). |
| Post-process (**posterisation**, outline, speed lines, aberration, vignette) | **Blendables portés par `BP_PlayerCameraManager`** + `MPC_Global` | Écriture de scalaires par `BPC_MovementState` / `BPC_Health`. Zéro logique de rendu en BP. **Budget (8 blendables) et ordre d'application : `SPEC_VFX §3.2` fait foi** — `PP_Posterize` en premier, avant tous les effets de vitesse. |
| Éclairage du niveau (`DirectionalLight`, `SkyLight`, `SkyAtmosphere`) | **`BP_LightingRig`** (D2, D33) | **Hors portée de cette spec.** Aucun effet de caméra ne pilote une lumière, jamais. |
| Hit-stop | **`BPC_HitStop` sur `PC_Overdrive`** (D6) | `Set Global Time Dilation` + timer, point unique (§6). |
| Caméra de mort | `BP_DeathCam` | Acteur statique posé à la position de mort, pris comme `View Target` (§9). |
| Fades / transitions | `PC_Overdrive` | `Camera Fade` du PlayerCameraManager. |

---

## 2. FOV dynamique

### 2.1 Le piège du FOV joueur — résolu explicitement

Le joueur choisit un FOV dans les settings (`PlayerFOV`, 80–120, `SPEC_UI_HUD §9`) et le FOV dynamique en
ajoute avec la vitesse. **Le piège** : `SetFOV(FOV_Base + Additive)` écrase le choix du joueur ;
`SetFOV(PlayerFOV)` ailleurs écrase l'effet de vitesse ; et si les deux systèmes écrivent, ils se battent
à chaque frame. **Règle unique et non négociable :**

```
FinalFOV = PlayerFOV  +  SpeedAdditive  +  DashAdditive
```

- `PlayerFOV` (`SG_Settings`) est la **BASE**, jamais `FOV_Base` de `07_TUNING §16`.
  `FOV_Base` n'est que la **valeur par défaut** de `PlayerFOV` à la première exécution.
- `SpeedAdditive` et `DashAdditive` sont **toujours additifs**, jamais absolus.
- **Un seul endroit** écrit le FOV de la caméra : `BP_PlayerCameraManager::BlueprintUpdateCamera`.
  Aucun autre BP n'appelle `SetFieldOfView`, `Camera->SetFieldOfView`, ni ne touche au FOV
  du `CameraComponent`. Le `CameraComponent` du pawn garde sa valeur par défaut, elle est ignorée.
- Changer le FOV dans les settings pendant le jeu met à jour `PlayerFOV` sur le camera manager
  (dispatcher `OnSettingsApplied`) — l'aperçu est immédiat et l'effet de vitesse continue de fonctionner.

**Conséquence assumée** : un joueur en FOV 120 avec `FOV_MaxAdditive` arrive à 145°. C'est voulu.
Si c'est trop en playtest, on n'ajoute pas de clamp absolu (qui recasserait le choix joueur) :
on **scale l'additif** par un facteur de confort optionnel (§11), ou on baisse `FOV_MaxAdditive`.

### 2.2 Calcul de `SpeedAdditive`

```
BP_PlayerCameraManager :: BlueprintUpdateCamera
  HorizontalSpeed = VSize2D( PlayerPawn.Velocity )          ← 2D : la chute ne compte pas
  RawAdditive     = CF_FOVBySpeed.GetFloatValue( HorizontalSpeed )
  TargetAdditive  = clamp( RawAdditive, 0, FOV_MaxAdditive )
  CurrentAdditive = FInterp To( CurrentAdditive, TargetAdditive, DeltaTime, InterpSpeed )
```

| Élément | Spec |
|---|---|
| Courbe | `CF_FOVBySpeed` (`08_DATA_SCHEMAS §5`), domaine `uu/s` → image `°` additifs. |
| Points de la courbe | `(0 → 0)`, `(Speed_SprintCap → 0)`, `(FOV_SpeedForMax → FOV_MaxAdditive)`. Tangentes **ease-in** : le FOV ne bouge quasiment pas jusqu'au sprint cap, puis monte. Raison : le FOV doit récompenser le momentum gagné, pas le déplacement de base. |
| Au-delà de `FOV_SpeedForMax` | La courbe plafonne (dernière clé plate). Clamp de sécurité à `FOV_MaxAdditive`. |
| Interp | `FInterp To`, vitesse `FOV_InterpSpeed`. |
| **Interp asymétrique** | Montée : `FOV_InterpSpeed`. Descente : `FOV_InterpSpeed × 0.5` `[À CALIBRER]`. Gagner de la vitesse se voit vite, en perdre se sent longtemps — et surtout ça supprime le « pompage » quand la vitesse oscille. |
| Vitesse utilisée | **Horizontale uniquement** (`VSize2D`). Sinon une chute libre ouvre le FOV à fond sans que le joueur soit rapide. |
| Perte de vitesse (`07_TUNING §10`) | Aucun traitement spécial : le FOV se referme naturellement via l'interp lente, ce qui est déjà un excellent feedback de punition (§9). |

---

## 3. Camera tilt (roll)

Trois sources de roulis, calculées **séparément** puis **additionnées**, jamais en compétition.

```
FinalRoll = Roll_Strafe  +  Roll_Slide  +  Roll_WallRide
FinalRoll = clamp( FinalRoll, -RollClampMax, +RollClampMax )     RollClampMax = 15° [À CALIBRER]
CurrentRoll = FInterp To( CurrentRoll, FinalRoll, DeltaTime, CameraTilt_InterpSpeed )
```

**Une seule interpolation, sur la somme.** Interpoler chaque source séparément puis additionner
produit des transitions molles et des combinaisons imprévisibles (c'est le bug classique).

| Source | Entrée | Valeur cible | Note |
|---|---|---|---|
| **Strafe** | Input latéral normalisé `-1..1` (l'input, pas la vélocité — plus réactif et pas de roll parasite en glissade) | `CF_CameraTiltByStrafe` → `°`, amplitude `CameraTilt_Strafe` | Le roll est **opposé** au strafe : strafe droite → roll négatif (le monde penche vers la droite), comme dans un virage. |
| **Slide** | `bIsSliding` + signe du strafe | `Slide_CameraTilt` (`07_TUNING §5`), signé par la direction du strafe. `0` si pas de strafe. | Se cumule avec le strafe : slide + strafe = roll marqué, c'est l'effet le plus satisfaisant du jeu. |
| **Wall ride** | Normale du mur | `WallRide_CameraTilt` (`07_TUNING §9`), signe = côté du mur, roulis **vers l'extérieur** (comme un motard incliné) | Domine visuellement les deux autres. |

| Résolution des conflits | Comportement |
|---|---|
| Strafe + slide, même direction | S'additionnent. Somme max ≈ `CameraTilt_Strafe + Slide_CameraTilt`. Sous le clamp, OK. |
| Wall ride + strafe opposé | Le wall ride **écrase** le strafe : pendant `WallRiding`, `Roll_Strafe` est multiplié par `0.3` `[À CALIBRER]`. Sinon le joueur qui strafe contre le mur annule son propre tilt et l'effet disparaît au pire moment. |
| Sortie de wall ride | `Roll_WallRide` retombe à 0 et l'interp fait le reste. **Ne jamais forcer un retour instantané** : la transition douce est le signal de sortie. |
| Dash | Aucun roll ajouté. Le dash a son propre langage (§4). Le roll en cours continue normalement. |
| Mort / pause | `FinalRoll = 0`, interp normale. |

**Application** : le roll est écrit dans `BlueprintUpdateCamera` sur `POV.Rotation.Roll` **après** le
reste. Il n'affecte **jamais** la direction de tir : le laser trace depuis `GetPlayerViewPoint` sans roll,
ou depuis le `CameraComponent` dont le roll n'entre pas dans le forward vector. À vérifier en test (§12).

---

## 4. Feedback de dash

Le dash dure `Dash_Duration` (`07_TUNING §8`) — très court. Le feedback doit être **plus long que le dash
lui-même**, sinon on ne le perçoit pas.

| Phase | t | Effet |
|---|---|---|
| **Kick** | 0 → 0.06 s `[À CALIBRER]` | `DashAdditive` monte de 0 à `Dash_FOVKick` (`07_TUNING §8`). Montée quasi instantanée (courbe ease-out agressive). |
| **Hold** | 0.06 → `Dash_Duration` | Maintien à `Dash_FOVKick`. |
| **Recovery** | `Dash_Duration` → +0.25 s `[À CALIBRER]` | Retour à 0, courbe ease-in-out. |

**Implémentation** : une `Timeline` `TL_DashFOV` dans `BP_PlayerCameraManager`, longueur
`0.06 + Dash_Duration + 0.25`, courbe normalisée `0→1→1→0` multipliée par `Dash_FOVKick`, sortie écrite
dans `DashAdditive` (formule §2.1), déclenchée par `BPC_Dash.OnDashPerformed(Direction)`.
Un nouveau dash **redémarre** la timeline depuis 0 (pas de cumul).

**Décalage de caméra — décision : oui, mais minuscule.** Un léger recul positionnel à l'entrée du dash
amplifie énormément la sensation d'accélération pour un coût de confort quasi nul.

| Paramètre | Valeur |
|---|---|
| Offset | `-8 uu` sur l'axe de la direction du dash `[À CALIBRER]` |
| Timing | Appliqué en 0.04 s, résorbé en 0.20 s (même `Timeline`, courbe séparée) |
| Application | `POV.Location += DashOffsetVector` dans `BlueprintUpdateCamera`. **Additif, jamais un `SetActorLocation`.** |
| Sécurité | L'offset ne fait **jamais** sortir la caméra de la capsule (8 uu << `CapsuleRadius` = 34). Pas de risque de voir à travers un mur. |

| Reste du feedback de dash | Effet | Note |
|---|---|---|
| Post-process | `MPC_Global.DashFlash` monté à 1 puis résorbé en 0.2 s → pilote une aberration chromatique radiale ponctuelle. | Additif à l'aberration de vitesse (§7). |
| Shake | **Aucun.** Le dash est une action volontaire et précise ; un shake dessus dégrade la visée. | |
| HUD | `WBP_DashCharges` consomme un losange (`SPEC_UI_HUD §3.4`). | |
| Audio | Whoosh directionnel + sub-bass court. Le son porte 50 % de la sensation. | |

---

## 5. Screen shakes

Assets `CS_*` dans `Content/OVERDRIVE/Player/Blueprints/Shakes/`, classe parente **`LegacyCameraShake`**
(entièrement paramétrable dans le details panel, aucun code — le bon choix en BP-only).
Toutes les amplitudes sont **multipliées par le scale de `07_TUNING §16`** au moment du
`StartCameraShake(Class, Scale)`, jamais codées dans l'asset : l'asset définit la *forme*, le tuning
définit l'*intensité*. Toutes les valeurs du tableau sont **`[À CALIBRER]`** (formes de départ).

| Asset | Déclencheur | Durée | Rotation (Pitch/Yaw/Roll) amp ° | Freq | Loc | Oscillation | Scale (`§16`) |
|---|---|---|---|---|---|---|---|
| `CS_LaserFire` | Tir laser | 0.10 s | 0.35 / 0.20 / 0.10 | 25 / 20 / 15 Hz | 0 | Sinus, blend in 0.02 / out 0.06 | `Shake_LaserFire` |
| `CS_Headshot` | Headshot confirmé | 0.18 s | 0.6 / 0.4 / 0.3 | 30 / 25 / 20 Hz | Y 1.5 uu | Perlin (moins mécanique) | `Shake_Headshot` |
| `CS_MeleeHit` | Melee touche | 0.22 s | 1.2 / 0.8 / 0.6 | 18 / 15 / 12 Hz | X 3 / Y 2 uu | Perlin, blend out 0.12 | `Shake_MeleeHit` |
| `CS_TakeDamage` | Dégât subi | 0.30 s | 1.6 / 1.2 / 1.0 | 12 / 10 / 8 Hz | X 4 / Y 4 / Z 3 uu | Perlin, blend out 0.18 | `Shake_TakeDamage` |
| `CS_HardCollision` | Collision frontale > 2500 uu/s (`07_TUNING §10`) | 0.45 s | 2.5 / 1.8 / 2.0 | 8 / 7 / 6 Hz | X 8 / Z 6 uu | Perlin, blend in 0 / out 0.3 | `Shake_HardCollision` |

Les amplitudes de **location** ci-dessus (≤ 8 uu, ≤ 4 uu sur une action du joueur) sont la limite chiffrée
retenue par `SPEC_VFX §4.2` : une translation faible est autorisée, une translation ample ne l'est pas.

**Règles anti-cumul et priorité** — sans elles, un multikill melee pendant une collision produit une
bouillie injouable. Elles complètent le plafond de **2 shakes actifs maximum** (`SPEC_VFX §4.2`).

| Règle | Implémentation |
|---|---|
| **Un shake par catégorie** | 3 catégories : `Weapon` (LaserFire, Headshot), `Impact` (MeleeHit, HardCollision), `Damage` (TakeDamage). Une variable `ActiveShake_<Cat>` (`UCameraShakeBase` ref) par catégorie sur `BP_PlayerCameraManager`. |
| **Remplacement dans la catégorie** | Nouveau shake d'une catégorie → `StopCameraShake(ActiveShake, bImmediately = false)` sur l'ancien, puis démarrage du nouveau. Jamais deux shakes de la même catégorie en parallèle. |
| **Priorité inter-catégorie** | `Damage > Impact > Weapon`. Un shake de priorité **inférieure** démarré pendant qu'un shake supérieur est actif est joué à **50 %** de son scale `[À CALIBRER]`. Un shake supérieur coupe immédiatement les inférieurs. |
| **Cap global d'amplitude** | Somme des scales actifs clampée à `1.5` `[À CALIBRER]`. Vérifié avant chaque `StartCameraShake`. |
| **Cooldown du shake de tir** | `CS_LaserFire` a un cooldown égal à `Laser_FireCooldown` : en tir soutenu il **redémarre** au lieu de s'empiler. |
| **Multiplicateur d'accessibilité** | `ShakeScale` du `SG_Settings` (`SPEC_UI_HUD §9`) multiplie **tous** les scales. À 0, aucun `StartCameraShake` n'est appelé du tout (économie + garantie). |
| **Jamais pendant** | Pause, écran de résultats, coffre, fade de mort. Les shakes en cours sont stoppés (`StopAllCameraShakes`) à l'entrée de ces états. |

---

## 6. Hit-stop / time dilation

Valeurs : `Melee_HitStop` (`07_TUNING §12`), `HitStop_Headshot`, `HitStop_TimeDilation` et
`HitStop_MinInterval` (`§16`).

**Propriétaire unique : `BPC_HitStop`, sur `PC_Overdrive`** (D6). `BPFL_Overdrive::DoHitStop` **n'existe pas** :
une Function Library ne peut pas porter d'état, et `Set Global Time Dilation` est un état global qui ne peut
pas avoir trois propriétaires. Le PlayerController est le bon hôte parce qu'il **survit au respawn du pawn**.
Détail d'implémentation et pseudo-code de référence : `SPEC_VFX §4.1`.

```
BPC_HitStop  (sur PC_Overdrive)
  RequestHitStop( RealDuration: float, Dilation: float, Priority: int ) → bool bAccepted
   ├─ if bActive AND Priority <= CurrentPriority        → return false   (strictement supérieure, sinon ignoré)
   ├─ if TimeSinceLastHitStop < HitStop_MinInterval     → return false   (anti-spam)
   ├─ Set Global Time Dilation( Dilation )
   ├─ bActive = true ; CurrentPriority = Priority
   └─ Clear Timer + Set Timer by Event( RealDuration * Dilation , EndHitStop )     ⚠ voir §6.3
```

`EndHitStop` → `Set Global Time Dilation(1.0)` + `bActive = false` + `CurrentPriority = 0`.
`RealDuration` est exprimée en **temps réel** — d'où la multiplication par la dilatation à l'armement du timer.
Si `bHitStop` est à off dans `SG_Settings` (§11), `RequestHitStop` retourne `false` immédiatement.

| Événement | `Priority` | `RealDuration` | `Dilation` |
|---|---|---|---|
| Headshot | **10** | `HitStop_Headshot` | `HitStop_TimeDilation` |
| Melee hit | **10** | `Melee_HitStop` | `HitStop_TimeDilation` |
| Wall slam | **20** | `Melee_HitStop × 1.5` `[À CALIBRER]` | `HitStop_TimeDilation` |
| Boss phase / kill de boss | **30** | 0.25 s `[À CALIBRER]` | 0.15 |

**Pas de hit-stop sur le tir laser** : à `Laser_FireCooldown` ≈ 0.18 s, ça transformerait le jeu en
diaporama. Le laser a son shake et son hitmarker, ça suffit.

| Ce qui DOIT être exclu du ralenti | Comment l'exclure |
|---|---|
| **Audio** | `Sound Class` avec `bApplyEffects` / pitch non lié au time dilation. Concrètement : sur chaque `Audio Component` critique, `Set Pitch Multiplier` compensatoire, ou plus simplement mettre les SFX d'impact et la musique dans un `SCL_` dont le pitch n'est pas modulé. **Un hit-stop qui fait grave-buguer le son est immédiatement perçu comme un lag.** La musique en particulier ne doit JAMAIS ralentir. |
| **UI / widgets** | Toute animation UMG déclenchée pendant un hit-stop ralentit aussi. Solution : les widgets critiques (hitmarker, damage indicator) utilisent des `Set Timer` avec `Time Dilation` du widget forcé, ou plus simple : leurs durées sont si courtes (< 0.3 s) que le décalage est imperceptible. Pour `WBP_Results` et les menus : `Set Global Time Dilation(1.0)` est **garanti** avant leur ouverture. |
| **Input** | L'input n'est pas ralenti par le time dilation, mais le mouvement caméra du joueur l'est via les `Add Controller Input`. Compensation : diviser le delta de look par la dilation courante dans `PC_Overdrive` tant que `BPC_HitStop.bActive` `[À CALIBRER]`. **Sans ça, la souris devient pâteuse pendant le hit-stop et c'est le pire défaut possible dans un FPS rapide.** |
| **Post-process / MPC** | Non affecté (piloté par des scalaires, pas par du temps). OK. |

| Pièges de `Set Global Time Dilation` | Détail | Parade |
|---|---|---|
| **Les timers sont en temps dilaté** | Un `Set Timer(0.06)` posé pendant une dilation de 0.05 s'exécute en 0.06 / 0.05 = 1.2 s réelles. | Poser le timer **avec la durée déjà multipliée par la dilation** (`Duration × Dilation`), OU utiliser un `Timer Handle` sur un objet à `CustomTimeDilation = 1`. La première solution est plus simple en BP : voir le pseudo-code §6.1. |
| **Cumul de hit-stops** | Deux kills coup sur coup → deux `Set Global Time Dilation(0.05)` et un seul `EndHitStop` mal placé → le jeu reste au ralenti. | Flag `bActive` + `CurrentPriority` + `Clear and Invalidate Timer` avant de reposer, le tout dans `BPC_HitStop`. Jamais deux timers de hit-stop en vol. |
| **Dilation persistante après un changement de niveau** | `Global Time Dilation` **survit** à `OpenLevel` dans certains cas. | `GM_Overdrive::BeginPlay` → `Set Global Time Dilation(1.0)` inconditionnel. Idem à l'ouverture de `WBP_Results` et de la pause. |
| **Interaction avec la pause** | `Set Game Paused` pendant un hit-stop : le timer ne tourne plus, la dilation reste. | À la sortie de pause, si `bActive`, forcer `EndHitStop`. |
| **Valeur minimale** | `Global Time Dilation` a un plancher moteur (`t.MaxFPS` / `Min Global Time Dilation`, défaut 0.0001). `HitStop_TimeDilation` = 0.05 est confortable. Ne jamais utiliser 0 (freeze réel, physique cassée). | |
| **Physique et knockback** | Le knockback melee (`Melee_Knockback`) est appliqué pendant le hit-stop → l'ennemi part au ralenti puis accélère. **C'est l'effet recherché** (il souligne l'impact). Ne pas « corriger ». | |

---

## 7. Effets de vitesse (post-process)

Tous pilotés par **`MPC_Global`** (`08_DATA_SCHEMAS §6`) — **zéro logique de rendu dans un BP**.
`PlayerSpeed01` est écrit par **`BPC_MovementState`, et par personne d'autre** (D9), sur un **timer unique
20 Hz** (pas Tick) partagé avec le vent (`SPEC_AUDIO §5`) :

```
PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                       / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )
```

Ainsi `PlayerSpeed01 = 0` en dessous de `SpeedLines_StartSpeed` et `1` à `SpeedLines_FullSpeed`
(`07_TUNING §16`). Un seul scalaire pilote tous les effets → ils sont **cohérents par construction**.

> ⚠ **Le FOV n'utilise PAS `PlayerSpeed01`.** Ce scalaire n'existe que pour les **effets de vitesse**
> (speed lines, aberration, vignette) et vaut 0 sous 2500 uu/s. Le FOV, lui, lit la **vitesse brute**
> (`VSize2D(Velocity)`) via la courbe `CF_FOVBySpeed` (§2.2) : c'est la seule façon d'avoir une réponse
> continue sur tout le registre et une courbe de feeling réglable indépendamment des seuils de speed lines.
> Deux consommateurs, deux normalisations, **une seule lecture de la vitesse par frame**.

### 7.1 Le problème du fond clair — arbitrage des effets de vitesse

La v1 dessinait des **speed lines blanches** sur une ville nocturne : contraste maximal, effet gratuit.
La DA v2 (D2) est une **ville blanche en plein jour sous un ciel bleu clair**. Des traits blancs y sont
strictement **invisibles**, et un `pow()` plus agressif ne changera rien : ils convergent vers la couleur
du fond, pas vers un contraste.

**Décision : les speed lines passent en `OD_Navy_Ink`** (navy très foncé, `PALETTE.md §2`), **pas en magenta.**

| Option | Verdict | Raison |
|---|---|---|
| Blanc (v1) | **Rejetée** | Zéro contraste sur la structure blanche et sur le ciel. C'est le problème qu'on résout. |
| **`OD_Navy_Ink` (retenue)** | ✅ | (1) Le foncé est la **seule** valeur qui contraste à la fois avec `OD_White_Structure` et `OD_Sky_Blue` — le blanc n'en contraste avec aucun des deux. (2) C'est **neutre en teinte** : ça n'entre en concurrence avec aucune couleur réservée de `PALETTE.md §3`, donc l'effet ne « dit » rien de faux. (3) Ça lit comme un **flou de mouvement stylisé**, cohérent avec l'outline `OD_Navy_Ink` de la DA — les speed lines deviennent des outlines de vitesse. |
| Magenta | **Rejetée** | Le magenta est réservé au **joueur** (`OD_Magenta_Player`, D3) : laser, dash, melee, traînée. Des speed lines magenta permanentes à haute vitesse noieraient le muzzle flash et la traînée de dash dans un fond de la même couleur — exactement le signal qu'on ne peut pas se permettre de perdre. **Le magenta doit rester rare pour rester lisible.** |

**Sur une ombre portée**, le navy perd son contraste — c'est le seul cas de figure défavorable, et il est
acceptable : les ombres couvrent une fraction de l'écran, jamais sa totalité, et l'effet retrouve son
contraste dès la frame suivante. Le repli si le playtest l'infirme est le **magenta à faible opacité**
(≤ 15 %), à ne déclencher que sur constat de Louis.

**Règle générale, valable pour tous les effets de cette section** :

> Sur un fond clair, un effet d'écran doit **assombrir** ou **saturer**. Il ne doit **jamais éclaircir.**
> Concrètement : blend **`Multiply`** ou **`Alpha Blend` avec une couleur foncée**, jamais **`Add`**.

| Effet | Asset | Pilotage | Verdict |
|---|---|---|---|
| **Speed lines** | `PP_SpeedLines` (post process material, Blendable) | Intensité = `CF_SpeedLinesBySpeed(Speed)` écrit dans `MPC_Global` | **OUI, en `OD_Navy_Ink`** (§7.1). L'effet de vitesse le plus efficace. Traits radiaux depuis le centre, **transparents au centre** (rayon intérieur vide = 25 % de l'écran `[À CALIBRER]`) pour ne jamais masquer la cible. Densité et opacité montent avec le scalaire. Composition **`Multiply`** : les traits assombrissent l'image au lieu de l'éclaircir. Direction radiale fixe, pas alignée sur la vélocité (moins juste physiquement, beaucoup plus lisible). |
| **Aberration chromatique** | `PP_ChromaticAberration` (**blendable de `BP_PlayerCameraManager`**) | `PlayerSpeed01`, intensité max `ChromaticAberration_MaxAtFullSpeed` | **OUI, mais elle doit être plus forte qu'en v1.** L'aberration sépare les canaux RGB : sur du **blanc pur**, les trois canaux sont saturés, la séparation ne produit **rien** — l'effet ne se voit que sur les **arêtes** entre le décor et le ciel, ou le long des outlines. C'est heureusement là que l'œil regarde en course. `ChromaticAberration_MaxAtFullSpeed` (`07_TUNING §16`) est donc **la première valeur à remonter en playtest** ; on ne change pas la clé sans mettre à jour le doc (R3). Rayon de départ 0.4 `[À CALIBRER]` pour épargner le centre. Coupé par `bChromaticAberration` (§11). |
| **Vignette** | `PP_Vignette` (**blendable de `BP_PlayerCameraManager`**) | `PlayerSpeed01`, `DamageFlash01` | **OUI — et c'est l'effet qui gagne le plus au changement de DA.** Elle **assombrit** : sur un fond clair, elle est à la fois plus visible et plus confortable qu'en v1, où elle disparaissait dans un décor déjà sombre. Teinte de la vignette de vitesse : **`OD_Navy_Deep`** (neutre, cohérent avec les speed lines). Resserre le champ perçu quand on va vite — compense visuellement l'ouverture du FOV. Se combine avec la vignette de dégât (§9) en prenant le **max**, pas la somme, **dans le matériau**. **Conséquence assumée** : la vignette étant plus efficace, son intensité de base doit être **revue à la baisse** en playtest, sinon l'écran se referme trop. `[À CALIBRER]` |
| **Motion blur** | Réglage moteur (`r.MotionBlurQuality`) | `bMotionBlur` du `SG_Settings` | **NON par défaut. Tranché.** Raisons : (1) à 5000 uu/s le blur détruit la lisibilité de la géométrie, qui est déjà la contrainte n°1 (`07_TUNING §1`) ; (2) c'est un facteur majeur de motion sickness ; (3) le blur per-object rend les ennemis en mouvement flous — inacceptable dans un jeu où la fenêtre de tir est de quelques frames. Reste **disponible en option** (`r.MotionBlurQuality`), défaut **off**, avec un amount plafonné à 0.15 s'il est activé `[À CALIBRER]`. |
| **Radial blur** | — | — | **NON.** Même problème que le motion blur, sans le bénéfice. Les speed lines font le travail. |
| **Teinte du monde** | `MPC_Global.WorldTint` | `BP_LevelManager` | Hors juice caméra, mais partage le même MPC. Ne pas le piloter depuis la vitesse. |

**Où vivent ces effets — décision alignée sur `SPEC_VFX §3.2`** : **tous** les effets d'écran sont des
**Post Process Materials déclarés en blendables sur `BP_PlayerCameraManager`**, un seul endroit à maintenir.
Aucun d'entre eux n'est un réglage de `PostProcessVolume` : ni `Scene Fringe Intensity`, ni
`Vignette Intensity`, ni un volume par niveau. Raisons : (1) un blendable pilote son intensité par `MPC_Global`
sans qu'aucun BP ne touche au volume ; (2) on garde le contrôle exact de l'ordre d'application ; (3) une
option de confort (§11) se traduit par **retirer le blendable**, ce qui économise aussi le coût GPU.
Le budget global est de **8 blendables**, **`PP_Posterize`** (le cel-shading de la scène éclairée, D2) et
`PP_ToonOutline` (l'outline Sobel) inclus — **l'ordre complet et le décompte font foi dans `SPEC_VFX §3.2`**.
Point clé de cet ordre : **la posterisation s'applique AVANT tous les effets de vitesse**. Posteriser après
les speed lines quantifierait les traits eux-mêmes et les ferait clignoter d'une frame à l'autre.

**Matériaux d'environnement** : `PlayerSpeed01`, `StyleMultiplier01`, `HeatRatio` et `OverheatActive` sont
lisibles par **tous** les matériaux du niveau (`SPEC_ART_DIRECTION`) — pulsation des bandes
`OD_Red_Traversal` des surfaces de wall ride sur la vitesse, intensité de la signalétique
`OD_Purple_Primary` sur le style. **Aucun BP additionnel** : le levier de juice le moins cher du projet.
Attention toutefois : le monde étant **éclairé** (D2), un émissif qui monte se **délave** au lieu de briller.
Piloter la **saturation** et l'**épaisseur** des bandes donne bien plus qu'une montée d'`EmissiveIntensity`.

---

## 8. Caméra en slide et wall ride

| Slide | Comportement |
|---|---|
| Descente | La caméra descend de `Slide_CameraDrop` (`07_TUNING §5`). La capsule passe de `CapsuleHalfHeight` à `CapsuleHalfHeight_Slide` — **la caméra ne doit PAS suivre la capsule instantanément**, sinon le drop est un saut d'une frame. |
| Implémentation | Un offset `SlideCameraOffset` interpolé (`FInterp To`, vitesse 10/s `[À CALIBRER]`) vers `-Slide_CameraDrop`, appliqué sur `POV.Location.Z` dans `BlueprintUpdateCamera`. Le resize de capsule reste instantané côté gameplay. |
| Entrée | Descente en ~0.12 s `[À CALIBRER]` — assez rapide pour être ressentie, assez lente pour ne pas être un cut. |
| Sortie | Remontée avec la **même** vitesse d'interp. Une remontée plus lente donne une sensation de lourdeur agréable : vitesse × 0.7 en sortie `[À CALIBRER]`. |
| Tilt | `Slide_CameraTilt`, cf. §3. |
| **Ce qui doit rester stable** | Le **pitch** et le **yaw** : le joueur vise pendant le slide, souvent le moment le plus meurtrier. Aucun shake, aucun bob, aucun mouvement horizontal parasite. Seuls Z et Roll bougent. |

| Wall ride | Comportement |
|---|---|
| Tilt | `WallRide_CameraTilt` vers l'extérieur, cf. §3. C'est **le** signal d'accroche : le joueur sait qu'il est collé sans regarder le HUD. |
| Entrée | Transition sur `CameraTilt_InterpSpeed`. Ne pas raccourcir : une accroche brutale est désorientante. |
| Offset latéral | `+6 uu` en direction du mur `[À CALIBRER]`, pour donner l'impression de raser la surface. Clampé pour ne jamais traverser (6 uu << `WallRide_DetectDistance` = 70). |
| FOV | Aucun traitement spécial : la vitesse est conservée (`WallRide_SpeedRetention` ≈ 0.98), donc le FOV reste élevé naturellement. |
| **Ce qui doit rester stable** | Le **yaw**. La caméra ne s'aligne JAMAIS automatiquement sur le mur. Le joueur peut regarder où il veut pendant le wall ride, c'est ce qui permet de tirer en le faisant. Aucune correction de vue, jamais. |
| Wall jump | Le tilt retombe à 0 via l'interp normale + un `DashAdditive`-like ? **Non** : pas de FOV kick sur le wall jump, ça deviendrait épileptique en enchaînement mur-à-mur. Seul le tilt qui bascule d'un côté à l'autre porte le feedback. |
| Enchaînement mur gauche → mur droit | Le tilt traverse 0 en `2 × WallRide_CameraTilt / CameraTilt_InterpSpeed`. Si en playtest c'est trop lent pour un enchaînement serré, augmenter `CameraTilt_InterpSpeed` — **pas** réduire `WallRide_CameraTilt`. |

---

## 9. Feedback de dégât

Le dégât en PV n'est **pas** la vraie punition du jeu : la vraie punition est la **perte de vitesse**
(`07_TUNING §10`, principe GDD §15 : *erreur = perte de vitesse, jamais mort immédiate*). Le feedback est
hiérarchisé en conséquence.

| Dégât (PV) | Effet |
|---|---|
| Shake | `CS_TakeDamage` × `Shake_TakeDamage` (§5). |
| Flash écran | **Assombrissement** teinté **`OD_Red_Danger`** plein écran, blend **`Multiply`**, alpha 0.25 `[À CALIBRER]`, 0.08 s, fondu 0.15 s. Court : un flash long masque le danger suivant. **Ce n'est plus un flash additif** : sur une ville blanche, ajouter du rouge donne du rose pâle, c'est-à-dire rien. On retire de la lumière, on n'en ajoute pas (§7.1). |
| Vignette de dégât | Teinte **`OD_Red_Danger`**. `MPC_Global.DamageVignette` monte à `1 - HealthRatio`, donc **permanente et proportionnelle** en dessous de 50 % de PV. Combinée à la vignette de vitesse (`OD_Navy_Deep`, §7) par `max()`, jamais par addition (sinon écran noir à haute vitesse et bas HP). Les deux teintes sont lerpées par `DamageFlash01` **dans le matériau** (`SPEC_VFX §3.2`). |
| Directionnel | `WBP_DamageIndicator` (`SPEC_UI_HUD §3.10`) — la caméra ne fait **aucun** kick directionnel : déplacer la vue vers/contre l'attaquant casserait la visée du joueur. Le feedback directionnel est 100 % UI. |
| Audio | Impact + acouphène court proportionnel au dégât. |

**PERTE DE VITESSE — le feedback le plus important.** Déclenché par
**`BPC_MovementState.OnSpeedPenaltyApplied(OldSpeed, NewSpeed, Percent, Reason)`** (D12 — signature
définitive, `Reason` permet de différencier collision, dégât et hazard sans multiplier les dispatchers ;
la fonction appelante est `ApplySpeedPenaltyPercent(Percent, Reason)`, D11). Doit être **immédiatement
identifiable et différent** du feedback de PV : le joueur peut perdre 45 % de sa vitesse en n'ayant
quasiment pas perdu de PV.

| Canal | Effet |
|---|---|
| **FOV** | Le FOV se referme brutalement — mais via l'interp de descente lente (§2.2). **Décision** : sur `OnSpeedPenaltyApplied`, on **accélère temporairement** l'interp de descente (× 3 pendant 0.3 s `[À CALIBRER]`). La fermeture rapide du FOV est le signal viscéral « tu viens de perdre ton momentum ». |
| **Speed lines** | Disparaissent en même temps (piloté par `PlayerSpeed01`, automatique). Le contraste avant/après est énorme et gratuit. |
| **HUD** | `WBP_SpeedMeter` : flash **`OD_Red_Danger`** 0.25 s + le nombre chute avec l'interp de descente (visible). Le franchissement de palier vers le bas change la couleur (`SPEC_UI_HUD §3.5`). |
| **Style** | `Style_Loss_TakeDamage` s'applique en parallèle : le `WBP_StyleMeter` shake et flashe (`SPEC_UI_HUD §5.3`). Double punition visible. |
| **Audio** | **Le canal décisif.** Un son descendant (pitch down) distinct des sons de dégât, + un ducking bref de la musique 0.2 s `[À CALIBRER]`. Le silence relatif fait plus d'effet que n'importe quel VFX. |
| **Aucun shake supplémentaire** | Le `CS_TakeDamage` couvre déjà le moment. |

**Collision frontale** (`07_TUNING §10`, −50 % + camera shake) : `CS_HardCollision` + tout le feedback de
perte de vitesse ci-dessus, sans le flash rouge (ce n'est pas un dégât PV).

| Mort, t | Effet |
|---|---|
| 0 | `StopAllCameraShakes`. `Set Global Time Dilation(0.35)` `[À CALIBRER]` pendant 0.4 s — le seul ralenti « dramatique » du jeu. |
| 0 | La caméra se détache du pawn : `Set View Target with Blend` (blend 0) sur un **`BP_DeathCam`** — acteur minimal (`SceneComponent` + `CameraComponent`) spawné à la position et à la rotation de la caméra à l'instant de la mort, puis **totalement immobile**. Il est détruit au respawn. Aucune chute de caméra, aucun ragdoll POV : nauséeux. Déclaré dans `05_ARCHITECTURE §2`. |
| 0.05 | Assombrissement `OD_Red_Danger` en `Multiply`, alpha 0.4, vignette `OD_Red_Danger` à fond. **Le monde s'éteint** — sur une ville blanche c'est le contraste le plus violent dont on dispose, et il est gratuit. |
| 0.4 | `Set Global Time Dilation(1.0)`, puis fade selon §10. |

### 9.1 Perte de vie — **nouveau** (D1 / D31)

`Run_MaxLives` et `RunFailed_ScreenDuration` : `07_TUNING §18`. **Aucune valeur de gameplay n'est écrite ici.**

Une mort coûte **une vie** en plus du score et du style. Le joueur doit distinguer **trois** événements
qui se ressemblent dangereusement : *j'ai pris un coup* → *je suis mort et j'ai perdu une vie* →
*je suis sur ma dernière vie*. La troisième est un **état**, pas un événement — c'est ce qui la rend
difficile et importante.

**Perte de vie — un événement, distinct du dégât ordinaire**

Déclenché par **`GI_Overdrive.OnLifeLost(LivesRemaining)`**, joué **au respawn, après le fade-in**
(§10) — pas à l'instant de la mort, où l'écran est noir et où le feedback serait perdu.

| Canal | Effet | Ce qui le distingue du dégât (§9) |
|---|---|---|
| **Vignette** | `MPC_Global.LifeLostPulse` : la vignette `OD_Red_Danger` monte à **1.0** puis redescend à 0 en **0.9 s** `[À CALIBRER]`, courbe ease-out. | Le dégât ordinaire est **court et sec** (0.08 s + 0.15 s). Celui-ci est **long et lent**. Une durée, pas une intensité : c'est ce qui se lit comme « quelque chose de plus grave vient de se passer ». |
| **Shake** | **Aucun.** | Le dégât a `CS_TakeDamage`. Le silence de la caméra ici est délibéré : le joueur vient de reprendre le contrôle, un shake au respawn dégraderait sa première seconde de course. |
| **Écran** | `NS_LifeLost` (`SPEC_VFX §2.7`) — anneau **centripète**, qui se referme vers le centre. | `NS_TookDamage_Impact` est **centrifuge** (part des bords). Direction opposée = lecture opposée, sans avoir à lire une couleur. |
| **HUD** | `Anim_LifeLost` sur `WBP_LivesCounter` (`SPEC_UI_HUD §3.11`). | Le seul canal qui donne le **nombre** restant. |
| **Audio** | `S_LifeLost` (`SPEC_AUDIO §2.4`, **P0**). | Timbre propre, jamais une variante de `S_Player_Hurt`. |
| **FOV / tilt** | Inchangés. | On ne touche jamais au FOV au respawn : le joueur repart à vitesse nulle, l'interp fait déjà le travail. |

**Interdit** : ajouter un hit-stop, un ralenti ou un fade supplémentaire à la perte de vie. Le budget de
temps « mort → jouable » reste **< 0.5 s** (D16) et il est intouchable — tout le feedback de perte de vie
se joue **par-dessus** le jeu redevenu jouable, jamais en le retardant.

**Dernière vie — un état continu, pas un flash**

À `LivesRemaining == 1`, et **jusqu'à la fin de la run** (les vies ne se rechargent pas entre niveaux, D1) :

| Canal | Effet |
|---|---|
| **Vignette de tension** | `MPC_Global.LastLifeTension` = **1.0** (bool poussé une fois par `GI_Overdrive`, jamais par timer). Ajoute au `PP_Vignette` existant une **teinte `OD_Red_Danger` permanente à faible intensité** : opacité **0.12** `[À CALIBRER]`, uniquement dans les **15 % extérieurs** de l'écran, **sous** la vignette de vitesse (combinaison par `max()`, comme le reste de §9). |
| **Respiration** | Cette teinte **respire** : `0.09 ↔ 0.15` d'opacité sur une période de **4.0 s** `[À CALIBRER]`, `sin(Time × π / 2)` **dans le matériau**, zéro logique BP. Quatre secondes, c'est plus lent qu'un rythme cardiaque au repos : le joueur le perçoit sans jamais pouvoir le fixer du regard. |
| **Ce que ça ne fait PAS** | Aucun clignotement · aucun pulse rapide · aucun shake · aucune modification du FOV, du tilt ou de la vitesse d'interp · aucune couleur au centre de l'écran (la zone sanctuarisée 40 % × 40 % reste vierge, D22) · aucun son répété. |

**Pourquoi si discret** : cet état peut durer **plusieurs niveaux entiers** — potentiellement 5 des 8 d'une
run. Tout ce qui serait perceptible en 10 secondes devient insupportable en 10 minutes, et surtout **masque
le vrai danger** : sur une DA claire, une teinte rouge trop forte en bord d'écran entre en concurrence
directe avec la vignette de dégât et avec les projectiles `OD_Amber_Enemy`. La tension doit **teinter la
perception**, pas occuper un canal.

**L'aveu de conception** : si Louis ne sent pas la tension en playtest, la bonne réaction est de renforcer
**l'audio** (`S_LastLife_Loop`, `SPEC_AUDIO §2.4`) et le **widget** (`SPEC_UI_HUD §3.11` : taille + couleur du
chevron), **pas** l'effet écran. L'écran est le canal le plus coûteux en confort et le moins précis en
information — c'est le dernier qu'on monte, jamais le premier.

**Sortie de l'état** : `LastLifeTension` retombe à 0 uniquement à `GI_Overdrive.StartNewRun()`.
Il est **remis à 0 explicitement** à l'ouverture de `WBP_RunFailed`, de `WBP_Results`, du coffre et de la
pause — même règle que les shakes et la dilatation (§10).

---

## 10. Transitions

Toutes gérées par `PC_Overdrive` via `Camera Fade` (`StartCameraFade`) — pas de widget de fondu
(un widget de fondu est soumis au DPI, au z-order et aux animations UMG ; le camera fade non).

| Transition | Durée | Séquence |
|---|---|---|
| **Mort → restart** (`LivesRemaining > 0`) | `Restart_FadeDuration` (`07_TUNING §16`) **out**, puis `Restart_FadeDuration` **in** | Fade to black `Restart_FadeDuration` → destruction du `BP_DeathCam` et respawn au checkpoint (pas de `OpenLevel`, donc pas de chargement) → `Set Global Time Dilation(1.0)` → fade from black → **puis seulement** le feedback de perte de vie (§9.1) : `NS_LifeLost`, `S_LifeLost`, `Anim_LifeLost`. **Cible technique : < 0.5 s entre la mort et le moment où le joueur est jouable** (D16), **inchangée** — le feedback de vie se joue par-dessus le jeu jouable, il n'allonge pas la transition. Le joueur doit pouvoir spammer la mort sans frustration. Aucun écran intermédiaire, aucun bouton à presser. |
| **Mort → `RunFailed`** (`LivesRemaining == 0`) | 0.5 s out `[À CALIBRER]`, pas de fade in | **Le seul chemin de mort qui ne respawn pas.** Enchaînement : `BPFL_Overdrive.ResetCameraState()` (dilatation 1.0 + `StopAllCameraShakes`) → `MPC_Global.LastLifeTension = 0` → fade to black **0.5 s**, soit plus lent que `Restart_FadeDuration` : c'est le seul moment du jeu où on a le droit de ralentir, la run est finie → `E_GameState.RunFailed` → `WBP_RunFailed` (`SPEC_UI_HUD §6.1`) en overlay, **sans fade from black** (l'écran apparaît sur le noir, le monde figé et assombri derrière). Le `BP_DeathCam` **n'est pas détruit** : il reste le View Target pendant tout l'écran, puis est détruit avec le niveau. |
| **`RunFailed` → menu** | `RunFailed_ScreenDuration` (`07_TUNING §18`) puis 0.3 s | Attente de `RunFailed_ScreenDuration`, **skippable** (`SPEC_UI_HUD §6.1`) → fade to black 0.3 s → `OpenLevel(L_Menu)`. `GI_Overdrive` reset son `S_RunState` **à l'arrivée dans le menu**, pas avant : l'écran doit pouvoir afficher les données de la run jusqu'à sa dernière frame. |
| **Restart manuel (`R`)** | `Hold 0.4 s` (D16) | Depuis `WBP_Results`, la pause ou le gameplay. Maintien de 0.4 s pour éviter le restart accidentel en plein combat, puis même chemin que ci-dessus. |
| **Fin de niveau** | 0.3 s `[À CALIBRER]` | Le pawn est figé (`DisableInput`, pas `SetGamePaused` — la musique continue), la caméra reste en place, blur léger, `WBP_Results` en overlay (`SPEC_UI_HUD §6`). Le monde reste visible : c'est le trophée. |
| **Résultats → coffre** | 0.15 s | Cross-fade entre les deux widgets, pas de fade caméra. |
| **Coffre → niveau suivant** | 0.25 s out + chargement + 0.25 s in | Fade to black → `OpenLevel(NextLevel)` → `GM_Overdrive::BeginPlay` force `Global Time Dilation = 1.0` et lance le fade in. Prévoir un `Level Streaming` / écran de chargement minimal si le temps dépasse 1 s `[À CALIBRER]`. |
| **Entrée de boss** | `IntroDuration` (`PDA_BossData`, `08_DATA_SCHEMAS §3`) | **Le joueur garde le contrôle de la caméra pendant toute l'intro.** Pas de cinématique, pas de lock. Ce qui change : `WBP_BossHealthBar` apparaît (slide depuis le haut 0.3 s), la musique change, un `CS_` très lent et très ample (`CS_BossIntro`, amp 1.0°, freq 2 Hz, durée `IntroDuration`) donne un tremblement de sol. Les portes de l'arène se ferment dans le monde, pas à l'écran. |
| **Menu → jeu** | 0.4 s | Fade from black au `BeginPlay` du joueur. |
| **Jeu → menu (quit run)** | 0.3 s | Fade to black → `OpenLevel(L_Menu)`. |

**Règle transverse** : chaque transition **remet explicitement** `Global Time Dilation` à 1.0,
appelle `StopAllCameraShakes` et **remet `MPC_Global.LastLifeTension` à 0** (§9.1). Une seule fonction
`BPFL_Overdrive.ResetCameraState()` fait les trois, appelée systématiquement.
`LastLifeTension` est **repoussée à 1.0 par `GI_Overdrive` au `BeginPlay` du niveau** si
`LivesRemaining == 1` — sinon l'état de tension disparaîtrait silencieusement à chaque changement de
niveau, alors que les vies, elles, ne se rechargent pas (D1).

---

## 11. Accessibilité / confort

Options exposées dans `WBP_Settings`, stockées dans `SG_Settings`.
Chacune est lue par `BP_PlayerCameraManager` au `BeginPlay` et sur `OnSettingsApplied`.

> **Le tableau de référence de `SG_Settings` est celui de `SPEC_UI_HUD §9`** — il est unique et exhaustif
> (types, plages, défauts, mode d'application, y compris les réglages audio, vidéo et l'inversion Y).
> Ce qui suit décrit **l'effet caméra** de chaque option, pas son stockage. Si les deux divergent sur une
> plage ou un défaut, `SPEC_UI_HUD §9` fait foi.

| Option | Variable | Effet caméra |
|---|---|---|
| **Camera shake** | `ShakeScale` | Multiplie tous les scales de §5. À **0**, aucun `StartCameraShake` n'est appelé du tout (économie + garantie). |
| **FOV** | `PlayerFOV` | Base du FOV (§2.1). Un FOV élevé réduit la motion sickness chez beaucoup de joueurs. |
| **Motion blur** | `bMotionBlur` | §7 — off par défaut. |
| **Speed lines** | `bSpeedLines` | À off, `PP_SpeedLines` est **retiré des blendables** de `BP_PlayerCameraManager` (pas juste mis à 0 : on économise aussi le coût GPU). |
| **Effet de vitesse sur le FOV** | `FOVSpeedEffectScale` | Multiplie `SpeedAdditive` et `DashAdditive`. À 0, le FOV est constant. **C'est l'option de confort la plus importante** : c'est le FOV qui bouge, pas le shake, qui provoque le plus de nausée dans ce genre de jeu. |
| **Camera tilt** | `TiltScale` | Multiplie `FinalRoll` (§3). À 0, l'horizon ne bouge jamais. |
| **Aberration chromatique** | `bChromaticAberration` | À off, `PP_ChromaticAberration` est retiré des blendables (§7). Certains joueurs la lisent comme un défaut de vue. |
| **Hit-stop** | `bHitStop` | À off, `BPC_HitStop.RequestHitStop()` retourne `false` immédiatement (§6). Utile pour les joueurs sensibles aux saccades. |

**Règle de conception** : chacune de ces options doit pouvoir être **toutes désactivées
simultanément** et le jeu doit rester jouable et lisible. Le juice est un ajout, jamais une
béquille de lisibilité. Test explicite en §12.

**Note MVP** : si le temps manque (`CLAUDE.md R5` — Juice avant Menus), livrer au minimum
`ShakeScale`, `PlayerFOV` et `FOVSpeedEffectScale`. Les autres sont du bonus.

---

## 12. Checklist de validation

**FOV** — [ ] changer `PlayerFOV` en jeu : l'effet de vitesse continue de fonctionner par-dessus ·
[ ] un seul BP écrit le FOV (recherche `SetFieldOfView` → 1 résultat) · [ ] une chute libre verticale
n'ouvre pas le FOV · [ ] osciller autour de `Speed_SprintCap` ne fait pas pomper le FOV ·
[ ] `FOVSpeedEffectScale = 0` → FOV constant, jeu toujours agréable.

**Tilt** — [ ] le roll cumulé ne dépasse jamais `RollClampMax` · [ ] slide + strafe : tilt marqué mais
horizon lisible · [ ] en wall ride, strafer contre le mur n'annule pas le tilt · [ ] **le roll n'affecte
PAS la direction du tir laser** (tirer sur une cible en plein tilt de wall ride) · [ ] enchaînement mur
gauche → mur droit sans latence perçue.

**Dash** — [ ] le FOV kick est perceptible malgré `Dash_Duration` très court · [ ] deux dashes de suite
ne cumulent pas le kick · [ ] l'offset caméra ne fait jamais voir à travers un mur · [ ] aucun shake sur
le dash (visée stable pour dash-tirer).

**Shakes** — [ ] tir en rafale : pas d'empilement, le crosshair reste sur la cible · [ ] multikill melee
pendant une prise de dégât : un seul shake dominant · [ ] `ShakeScale = 0` → aucun shake, jeu toujours
satisfaisant · [ ] aucun shake pendant pause, résultats, coffre, mort.

**Hit-stop** — [ ] `BPC_HitStop` est bien sur `PC_Overdrive` et survit au respawn du pawn · [ ] durée
**réelle** correcte (chronométrer : `Melee_HitStop` = 0.06 s réelles, pas 1.2 s) ·
[ ] la musique ne ralentit pas · [ ] la souris ne devient pas pâteuse · [ ] deux kills coup sur coup ne
bloquent pas le jeu au ralenti · [ ] changer de niveau pendant un hit-stop → niveau suivant à vitesse
normale · [ ] pause pendant un hit-stop puis reprise → vitesse normale.

**Effets de vitesse (DA v2)** — [ ] les speed lines sont bien **`OD_Navy_Ink`**, composées en `Multiply`,
et **visibles devant le ciel bleu comme devant un mur blanc** · [ ] elles ne masquent jamais le centre ni
une cible · [ ] elles restent perceptibles en traversant une **ombre portée** (le cas défavorable, §7.1) ·
[ ] à `SpeedLines_FullSpeed` la géométrie et les ennemis restent distincts · [ ] l'aberration chromatique
est perceptible sur les arêtes décor/ciel (sinon remonter `ChromaticAberration_MaxAtFullSpeed` **et mettre
à jour `07_TUNING §16`**) · [ ] vignette vitesse (`OD_Navy_Deep`) + vignette dégât (`OD_Red_Danger`) ne
s'additionnent pas en écran noir · [ ] **aucun effet d'écran n'éclaircit l'image** (§7.1) · [ ] motion blur
off par défaut · [ ] `PlayerSpeed01` écrit sur Timer, pas en Tick (profiler : coût BP négligeable) ·
[ ] `PP_Posterize` est bien **avant** les effets de vitesse dans la pile de blendables (`SPEC_VFX §3.2`) —
sinon les speed lines clignotent d'une frame à l'autre.

**Dégâts & perte de vitesse** — [ ] la perte de vitesse est **plus perceptible** que la perte de PV ·
[ ] on identifie sans regarder le HUD qu'on vient d'être ralenti · [ ] projectile encaissé à 4000 uu/s :
le FOV se referme visiblement, les speed lines coupent, le son descend · [ ] aucun kick directionnel qui
déplace la visée · [ ] la mort ne produit aucun mouvement de caméra nauséeux.

**Vies (§9.1)** — [ ] le feedback de perte de vie est **immédiatement distinguable** d'un dégât ordinaire
(long vs court, centripète vs centrifuge, sans shake) · [ ] il se joue **après** le fade-in, jamais pendant
le noir · [ ] il **n'allonge pas** le délai mort → jouable (toujours < 0.5 s, D16) · [ ] à 1 vie, jouer un
niveau entier : la tension se perçoit **sans jamais fatiguer** · [ ] la teinte de dernière vie n'entre pas
dans la zone centrale 40 % × 40 % · [ ] elle ne se confond pas avec la vignette de dégât ni avec un
projectile ennemi · [ ] `LastLifeTension` **persiste** au niveau suivant · [ ] elle est **à 0** en pause,
aux résultats, au coffre et sur `WBP_RunFailed`.

**Transitions** — [ ] mort → rejouable en **< 0.5 s** au checkpoint sans presser de touche (D16) ·
[ ] `IA_Restart` ne se déclenche pas sous 0.4 s de maintien · [ ] le `BP_DeathCam` est bien détruit au
respawn (aucun acteur orphelin après 10 morts) · [ ] mourir à `LivesRemaining == 1` mène bien à
`WBP_RunFailed` et **jamais** à un respawn · [ ] le retour au menu après `RunFailed_ScreenDuration` est
automatique et skippable · [ ] `Global Time
Dilation` = 1.0 au début de chaque niveau (vérifié au debugger) · [ ] l'intro de boss ne retire jamais le
contrôle de la caméra · [ ] aucune transition ne laisse un shake, une dilation ou une tension résiduels.

**Confort global (test dédié, 15 min)** — [ ] 15 min sans inconfort, tous effets à fond · [ ] 15 min avec
toutes les options de confort à 0 : le jeu reste jouable, lisible et **fun à contrôler** · [ ] aucun effet
en `Event Tick` non justifié · [ ] zéro warning de compilation sur `BP_PlayerCameraManager` et les `CS_*`.
