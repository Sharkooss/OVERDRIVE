# SPEC — AUDIO

> Portée : SFX, mix, MetaSounds, sensation de vitesse sonore, musique, sourcing, implémentation BP.
> Hors portée : VFX (`SPEC_VFX.md`), HUD (`SPEC_UI_HUD.md`), valeurs de gameplay (`Docs/07_TUNING.md`).
> **Le son est une feature de gameplay, pas une passe de finition.** Il se produit en même temps que le système qu'il sert (R4). Blueprint only (R1), UE 5.8.
> Les dB, durées et nombres de variations proposés ici sont `[À CALIBRER]` (ce n'est pas du gameplay) ; toute valeur de gameplay est citée **par nom de clé** de `Docs/07_TUNING.md`.

---

## 1. Principes

| Principe | Conséquence |
|---|---|
| **Le son informe avant d'illustrer** | Chaque SFX répond à une question précise du joueur. S'il n'en répond à aucune, il ne sert à rien. |
| **On joue au son** | Un joueur expérimenté doit pouvoir gérer sa chaleur, esquiver un projectile et confirmer ses kills **sans regarder le HUD**. |
| **Court, sec, transitoire** | À 4000 uu/s un son de 800 ms est déjà hors contexte. Cible : 80–350 ms pour tout feedback d'action. |
| **La vitesse s'entend** | Le vent est le HUD de vitesse le plus honnête. Il est continu, analogique, et lu périphériquement. |
| **Une famille = une bande de fréquences** | Le joueur occupe le médium-aigu, l'ennemi le bas-médium, l'UI l'aigu pur. Pas de bagarre spectrale. |
| **Le silence est un outil** | Le hit-stop headshot est aussi un trou audio de quelques ms. Ça vend l'impact mieux qu'un son plus fort. |

### Ce qu'un son doit dire sans le HUD

| Question du joueur | Son qui y répond |
|---|---|
| « J'ai touché ? à la tête ? tué ? » | `S_Laser_Hit_Body` / `S_Laser_Hit_Head` / `S_Enemy_Death` — **3 timbres nettement distincts** |
| « Je vais surchauffer ? » | `S_Heat_Warning` (ticks accélérants dès `Heat_WarningThreshold`) |
| « Je peux retirer ? » | `S_Heat_Ready` (montée courte à la sortie d'overheat) |
| « Je vais vite ? » | `MS_Wind_Speed` : volume + filtre + pitch continus |
| « Un projectile arrive sur moi » | `S_Enemy_Projectile_Whizz` spatialisé, + tell `S_Enemy_Shoot` avant |
| « Mon dash est rechargé » | `S_Dash_Ready` |
| « Je viens de perdre ma vitesse » | `S_Player_Hurt` + coupure brutale du vent (le plus fort signal du jeu) |
| « Ce mouvement était propre » | `S_BHop_Perfect` — récompense sonore, aucun équivalent visuel obligatoire |
| **« Je viens de perdre une vie »** | `S_LifeLost` — **timbre unique, jamais une variante de `S_Player_Hurt`** (§2.4) |
| **« Il ne me reste qu'une vie »** | `S_LastLife_Loop` — boucle de tension continue, pas un stinger (§2.4) |

> **Le son porte l'information de vies mieux que l'écran.** La DA v2 est une ville blanche et lumineuse
> (D2) : l'écran est déjà saturé d'informations claires et le budget de contraste y est rare. Le canal
> audio, lui, est **libre** — c'est là qu'on met la tension de dernière vie, pas dans un effet plein écran
> (`SPEC_CAMERA_JUICE §9.1` le dit explicitement : si Louis ne sent pas la tension, on monte **l'audio** en
> premier, jamais l'écran).

**Interdits** : sons réalistes d'armes à feu · dialogues / barks / voix off · SFX > 1 s pour une action · réverbération longue (le joueur a déjà quitté la pièce) · musique qui masque l'overheat · son répété en boucle sans variation (fatigue en 30 s) · footsteps réalistes (cf. §2.1).

---

## 2. Catalogue complet des SFX

> **Ce catalogue fait foi pour tous les noms de sons du projet** (D19). `SPEC_COMBAT`, `SPEC_ENEMIES`, `SPEC_BOSS`,
> `SPEC_UI_HUD` et `04_ROADMAP` renvoient ici et ne nomment aucun son de leur côté. Un `S_`/`SC_`/`MS_` absent de
> ce tableau n'existe pas ; l'y ajouter est la première étape pour le produire.
>
> **Var.** = samples à préparer pour la variation · **Sp.** = 2D (non spatialisé) / 3D · **dB** = volume relatif dans sa Sound Class, tous `[À CALIBRER]` · **P0** = S1–S2, **P1** = S3, **P2** = si le temps le permet. Dossier : `Content/OVERDRIVE/Audio/SFX/<Famille>/`.

### 2.1 Mouvement

**Décision : pas de footsteps.** À 1000–5000 uu/s une boucle de pas est soit inaudible, soit une mitraillette. Elle est remplacée par les événements discrets ci-dessous, qui portent tous une information de gameplay.

> ### 🔊 Retours de playtest — sons à refaire à la passe de sound design poussée
>
> Relevés par Louis **manche en main le 2026-08-21**, une fois les sons enfin joués en jeu. Le
> câblage n'est pas en cause : ce sont les **échantillons** qu'il faut resynthétiser
> (`Art_Source/Audio/synth/overdrive_sfx.py`, tout est calculé, rien n'est emprunté).
>
> | Son | Retour de Louis | Piste |
> |---|---|---|
> | **`S_WallRide_Enter`** ×2 | *« il sonne pas bien »* | La spec demande « claquement + résonance ». Le claquement est probablement trop sec / la résonance absente : on n'entend pas qu'on **s'accroche** à quelque chose. À reprendre en visant la matière du mur, pas l'impact. |
> | **`S_Jump`** ×3 | *« un peu trop trop fort / sec et aigu »* | La spec dit pourtant **« attaque douce, queue nulle », −8 dB** : l'échantillon actuel contredit sa propre fiche. Baisser le niveau, adoucir l'attaque, descendre le contenu spectral. C'est le son le plus fréquent du jeu après le tir — il doit se faire oublier. |
>
> Tout le reste a été validé à cette passe (tir, impacts, atterrissages, dash, slide, wall jump,
> chaleur, ennemis) : *« à part ça on est good »*. Les deux curseurs immédiats restent
> `Audio_PitchVariance` et `Audio_MovementVolume` (`07_TUNING §16`), mais ils ne corrigeront pas le
> timbre — il faut regénérer.

| Asset | Déclencheur | Description sonore | Durée | Var. | Sp. | dB | Prio |
|---|---|---|---|---|---|---|---|
| `S_Jump` | `Jump` | souffle court, attaque douce, corps bruité filtré, queue nulle | 120 ms | 3 | 2D | −8 | **P0** ⚠️ **à resynthétiser** — cf. encadré ci-dessus |
| `S_Land_Light` | atterrissage sous seuil | clic mat + basse courte, pas de queue | 150 ms | 3 | 2D | −10 | **P0** |
| `S_Land_Heavy` | atterrissage au-dessus du seuil | impact sub 60 Hz + noise burst, queue 200 ms | 400 ms | 3 | 2D | −4 | **P0** |
| `S_Dash` | `BPC_Dash.OnDashPerformed` | whoosh synthétique, sweep descendant 4 kHz → 400 Hz, attaque immédiate | 250 ms | 2 | 2D | −3 | **P0** |
| `S_Dash_Ready` | fin de `Dash_Cooldown` | double bip aigu, très court, **cristallin** | 90 ms | 1 | 2D | −14 | **P0** |
| `S_Slide_Start` | entrée de slide | scratch bruité + montée de résonance | 200 ms | 2 | 2D | −6 | **P0** |
| `S_Slide_Loop` | pendant `Sliding` | boucle de bruit filtré band-pass ~1.2 kHz, seamless | boucle | 1 | 2D | −9 | **P0** |
| `S_Slide_End` | sortie de slide | queue descendante, decay 250 ms | 250 ms | 2 | 2D | −10 | **P0** |
| `S_WallRide_Loop` | pendant `WallRiding` (via `MS_WallRide`) | frottement métallique tonal, résonance qui **monte** à l'approche de `WallRide_MaxDuration` | boucle | 1 | 2D | −7 | **P0** |
| `S_WallRide_Enter` | accroche au mur | claquement + résonance | 180 ms | 2 | 2D | −6 | **P0** ⚠️ **à resynthétiser** — cf. encadré §5 |
| `S_WallJump` | wall jump | impact + whoosh, plus aigu que `S_Jump` | 220 ms | 2 | 2D | −4 | **P0** |
| `S_BHop_Perfect` | hop dans `BHop_PerfectWindow` | **note musicale** courte, montante à chaque hop chaîné (jusqu'à 5 degrés) | 120 ms | 5 (pitchés) | 2D | −8 | **P0** |
| `S_Wind_Loop` | via `MS_Wind_Speed`, toujours actif | bruit rose filtré, stéréo large | boucle | 2 couches | 2D | variable | **P0** |
| `S_Speed_Threshold` | passage 3000 / 4000 / 5000 uu/s | souffle bref + note grave | 300 ms | 3 | 2D | −12 | P2 |

> **Nommage de `S_Wind_Loop` — décision 2026-08-20.** La colonne « Var. » vaut *2 couches*, pas 2 variantes.
> Les fichiers `S_Wind_Loop_01` (lit rose 120–2500 Hz) et `S_Wind_Loop_02` (bande 3–6 kHz, §4.2) sont donc
> des **couches à superposer**, jamais deux alternatives à tirer au sort. Un Sound Cue qui les mettrait dans
> un nœud `Random` serait un bug. Même logique pour toute future ligne dont « Var. » dit « couches ».
>
> **Les trois boucles sont des placeholders.** `MS_Wind_Speed` (§4.2) et `MS_WallRide` (§4.3) génèrent leur
> bruit dans le moteur (`Noise (Pink)` → `Ladder Filter`) : aucun Wave Player, donc aucun sample à terme.
> Les WAV existent pour que le mouvement se calibre **avant** que les MetaSounds soient montés (§9, S1).
> `S_Slide_Loop` n'a pas de MetaSound et reste, lui, un vrai sample définitif.

### 2.2 Combat

| Asset | Déclencheur | Description sonore | Durée | Var. | Sp. | dB | Prio |
|---|---|---|---|---|---|---|---|
| `MS_Laser_Fire` | `BP_LaserWeapon.PlayFireFX()` | attaque = transient claquant 3–8 kHz · corps = sweep saw descendant · queue = résonance 120 ms. **Pitch +0 à +4 demi-tons selon `HeatRatio`** | 250 ms | patch + 4 seeds | 2D | −2 | **P0** |
| `S_Laser_Impact_Surface` | trace bloquante sur géo | clic sec + petite queue métallique, distant | 180 ms | 4 | 3D | −12 | **P0** |
| `S_Laser_Hit_Body` | ennemi touché, corps | thud sourd + « fizz » électrique, bas-médium | 150 ms | 4 | 2D | −6 | **P0** |
| `S_Laser_Hit_Head` | headshot | **timbre nettement distinct** : crack aigu + sub court + micro-silence avant | 300 ms | 3 | 2D | **0** | **P0** |
| `S_Enemy_Death` | `BPC_Health.OnDeath` (ennemi) | shatter cristallin descendant, queue 400 ms | 500 ms | 4 | 3D | −5 | **P0** |
| `S_Kill_Confirm` | kill validé (superposé) | note courte, montante avec le style multiplier | 120 ms | 5 (pitchés) | 2D | −10 | P1 |
| `S_Heat_Warning` | `Heat_WarningThreshold` franchi | ticks courts, **intervalle qui se resserre** avec `HeatRatio` | 40 ms/tick | 2 | 2D | −9 | **P0** |
| `S_Overheat` | `OnOverheatStarted` | vapeur + clunk mécanique + coupure nette (« l'arme se ferme ») | 600 ms | 1 | 2D | −2 | **P0** |
| `S_Overheat_Deny` | tir tenté pendant l'overheat | clic sec négatif, très court, jamais fatigant | 70 ms | 2 | 2D | −14 | **P0** |
| `S_Heat_Ready` | `OnOverheatEnded` | montée courte 2 notes, timbre **cristallin** (même famille que `S_Dash_Ready`) | 250 ms | 1 | 2D | −8 | **P0** |
| `S_Melee_Swing` | `AM_Melee_Punch`, notify de départ | whoosh grave, plus lourd que `S_Dash` | 200 ms | 3 | 2D | −7 | **P0** |
| `S_Melee_Hit` | `AN_MeleeHit`, cible touchée | **le plus gros son du jeu après le wall slam** : sub 50 Hz + crunch + saturation | 350 ms | 3 | 2D | **0** | **P0** |
| `S_WallSlam` | `BPC_KnockbackReceiver` détecte le mur (`WallSlam_MinImpactSpeed`) | impact béton massif + shatter + queue 600 ms. **Le son le plus fort du jeu.** | 700 ms | 3 | 3D | **+1** | **P0** |
| `S_Overcharge_Fire` | 1er tir à `Heat = 0` (upgrade) | `MS_Laser_Fire` + couche sub et harmoniques | 350 ms | 1 | 2D | 0 | P2 |

### 2.3 Ennemi

| Asset | Déclencheur | Description sonore | Durée | Var. | Sp. | dB | Prio |
|---|---|---|---|---|---|---|---|
| `S_Enemy_Alert` | perception → cible acquise | grognement synthétique court, bas-médium 200–500 Hz | 400 ms | 4 | 3D | −8 | **P0** |
| `S_Enemy_Shoot` | tir du Shooter | **tell** : charge 150 ms puis départ sec. Le tell est obligatoire. | 400 ms | 3 | 3D | −5 | **P0** |
| `S_Enemy_Projectile_Loop` | attaché à `BP_EnemyProjectile` | bourdonnement grave, doppler activé | boucle | 1 | 3D | −8 | **P0** |
| `S_Enemy_Projectile_Whizz` | projectile passant à < 300 uu du joueur | whoosh bref panoramique, **info critique** | 250 ms | 3 | 3D | −4 | **P0** |
| `S_Enemy_Hit` | dégât non létal reçu | grunt court + fizz | 180 ms | 5 | 3D | −9 | **P0** |
| `S_Enemy_Death_Grunt` / `_Shooter` / `_Tank` | mort (surcouche de `S_Enemy_Death`) | timbre par archétype : Grunt aigu, Shooter médium, Tank grave + effondrement | 500–900 ms | 3 chacun | 3D | −5 | P1 |
| `S_Tank_Step` | pas du Tank | impact sub + métal, **doit s'entendre à 40 m** (avertissement) | 400 ms | 4 | 3D | −6 | **P0** |
| `S_Tank_Charge` | attaque du Tank | montée grave menaçante | 700 ms | 2 | 3D | −4 | P1 |
| `S_Player_Hurt` | dégât subi (`BPC_Health` joueur) | impact + inspiration coupée + **filtrage instantané du vent** | 500 ms | 3 | 2D | **0** | **P0** |
| `S_Player_Death` | mort du joueur | coupure sèche + descente de pitch générale | 900 ms | 1 | 2D | 0 | **P0** |

### 2.4 UI / Système

| Asset | Déclencheur | Description sonore | Durée | Var. | Sp. | dB | Prio |
|---|---|---|---|---|---|---|---|
| **`S_LifeLost`** | **`GI_Overdrive.OnLifeLost(LivesRemaining)`**, joué **au respawn** après le fade-in (`SPEC_CAMERA_JUICE §9.1`) | **Timbre unique, jamais une variante de `S_Player_Hurt`.** Un **retrait** : impact grave et mat, suivi d'une **descente d'un ton entier** sur une note tenue courte, puis un **trou de 150 ms** avant que le vent revienne. Le silence porte l'information. Aucune saturation, aucun crunch : ce n'est pas un impact, c'est une soustraction. | 800 ms | 1 | 2D | **0** | **P0** |
| **`S_LastLife_Loop`** | `LivesRemaining == 1`, **boucle** jusqu'à la fin de la run ou `RunFailed` | **Boucle de tension, pas un stinger.** Drone très grave (55–80 Hz) + une **pulsation lente à ~0.25 Hz** (une respiration toutes les 4 s, calée sur la vignette de `SPEC_CAMERA_JUICE §9.1`). Aucune mélodie, aucun rythme : ça ne doit **jamais** entrer en conflit avec la musique ni avec le vent. Sub uniquement — on la **sent** plus qu'on ne l'entend. | boucle | 1 | 2D | **−20** | **P0** |
| **`S_RunFailed`** | `E_GameState.RunFailed`, ouverture de `WBP_RunFailed` | Coupure nette de tout (musique incluse), **1 s de quasi-silence**, puis accord grave descendant non résolu, longue queue. Le seul endroit du jeu où l'on a le droit de laisser respirer. | 3.0 s | 1 | 2D | **0** | P1 |
| `S_UI_Hover` | survol d'un bouton | tick aigu très court | 50 ms | 2 | 2D | −16 | P1 |
| `S_UI_Click` | validation | clic + petite queue tonale | 90 ms | 1 | 2D | −12 | P1 |
| `S_UI_ScoreTick` | défilement du score dans `WBP_Results` | tick, **pitch qui monte** avec le total, rate-limité à 20/s | 30 ms | 1 | 2D | −18 | P1 |
| `S_Stinger_Rank_D` / `_C` / `_B` / `_A` / `_S` | `OnRankComputed` | D = descente morne · C/B = accord neutre puis majeur · A = fanfare · **S = stinger complet, le plus gratifiant du jeu** | 0.8 → 2.5 s | 1 chacun | 2D | −2 | **P0** |
| `S_Chest_Appear` | apparition de `BP_LootChest` | montée + shimmer ambre | 800 ms | 1 | 2D | −8 | P1 |
| `S_Chest_Open` | ouverture | claquement + éclat + accord | 1.2 s | 1 | 2D | −4 | P1 |
| `S_Upgrade_Select` | choix d'une upgrade | confirmation ; **timbre par `E_Rarity`** (Common mat → Epic brillant) | 500 ms | 3 | 2D | −5 | P1 |
| `S_Checkpoint` | `BP_Checkpoint` traversé | double note claire et cristalline, discret mais net | 400 ms | 1 | 2D | −10 | **P0** |
| `S_LevelComplete` | `BP_LevelEndTrigger` | stinger ascendant, enchaîne sur le rank | 1.5 s | 1 | 2D | −2 | **P0** |

> **Les trois sons de vies sont la priorité audio n°1 du système de run.** `S_LifeLost` est **P0** :
> c'est une **information de gameplay critique** — sans lui, le joueur ne sait pas qu'il vient de
> consommer une vie sans regarder le HUD, ce qui contredit frontalement le principe « on joue au son »
> (§1). Il vit dans **`SCL_SFX_Critical`** (§3.1), au même titre que `S_Player_Hurt` et `S_Overheat` :
> **rien ne le ducke, jamais.**
>
> **`S_LastLife_Loop` est le canal principal de la tension de dernière vie** (`SPEC_CAMERA_JUICE §9.1`).
> Contraintes dures, parce qu'elle peut tourner **plusieurs niveaux d'affilée** (D1 : les vies ne se
> rechargent pas) : −20 dB, sub uniquement, **aucun contenu au-dessus de 200 Hz** (sinon elle masque le
> tell du Shooter et le whizz des projectiles, qui sont du gameplay pur), et **`SCL_Ambience`**, pas
> `SCL_SFX_Critical` — elle doit pouvoir être duckée par un overheat ou un dégât.
> C'est une boucle : **`AudioComponent` persistant** porté par `GI_Overdrive` (comme la musique, §6), pas
> un `Play Sound 2D` répété (§8.3 règle 4). Elle survit aux `OpenLevel`, exactement comme la donnée
> `LivesRemaining` qu'elle représente.
>
> **Test d'accessibilité** : à `SCL_Music` −60 dB, `S_LifeLost` et `S_LastLife_Loop` doivent rester
> parfaitement audibles (§10).

### 2.5 Boss

| Asset | Déclencheur | Description sonore | Durée | Var. | Sp. | dB | Prio |
|---|---|---|---|---|---|---|---|
| `S_Boss_Intro` | `IntroDuration` | drone grave montant + impact final | ≤ intro | 1 | 2D | −2 | P1 |
| `S_Boss_AttackTell` | début d'un `AttackPatterns` | **1 timbre distinct par pattern** — c'est le tell principal du combat | 400–700 ms | 1/pattern | 3D | −3 | **P0 (boss)** |
| `S_Boss_Hit` | dégât reçu | métal résonnant, plus « dur » que `S_Enemy_Hit` | 250 ms | 4 | 3D | −8 | P1 |
| `S_Boss_PhaseChange` | `Phase2HealthThreshold` | rupture : coupure musique + rugissement + reprise plus rapide | 2.0 s | 1 | 2D | 0 | P1 |
| `S_Boss_Death` | mort | effondrement long + silence + stinger de victoire | 3.0 s | 1 | 2D | 0 | P1 |
| `S_Boss_Weakpoint_Hit` | point faible touché | crack cristallin très identifiable | 300 ms | 3 | 3D | −4 | P2 |

---

## 3. Mix

### 3.1 Hiérarchie des Sound Classes (`Content/OVERDRIVE/Audio/Mix/`)

```
SCL_Master                     0 dB
├─ SCL_Music                  −8 dB
├─ SCL_Ambience              −16 dB   ← ambiance urbaine diurne (§6), S_LastLife_Loop
├─ SCL_UI                     −6 dB   ← + S_RunFailed
└─ SCL_SFX                     0 dB
   ├─ SCL_SFX_Critical        +2 dB   ← S_Player_Hurt, S_Overheat, S_Heat_Warning,
   │                                    S_Enemy_Projectile_Whizz, S_LifeLost
   ├─ SCL_SFX_Weapon          −1 dB   ← laser, melee, wall slam
   ├─ SCL_SFX_Player          −4 dB   ← mouvement, vent, dash
   └─ SCL_SFX_Enemy           −5 dB   ← alerte, tir, mort, pas
```

Toutes valeurs `[À CALIBRER]`. **Règle** : le volume vit dans la Sound Class et dans le `SC_`/`MS_`, jamais en dur dans un Blueprint. `SCL_SFX_Critical` existe pour une seule raison : **garantir que l'information vitale passe toujours**. Rien ne la ducke, jamais.

### 3.2 Sound Mixes et ducking

| Mix | Poussé par | Effet | Fade in / out |
|---|---|---|---|
| `SMX_Default` | `GM_Overdrive.BeginPlay` | mix de base ci-dessus | — |
| `SMX_Overheat` | `OnOverheatStarted` | `SCL_Music` −8 dB, `SCL_SFX_Player` −6 dB, `SCL_SFX_Critical` inchangé | 0.05 / 0.4 s |
| `SMX_TookDamage` | `BPC_Health` joueur | tout −6 dB **sauf** `SCL_SFX_Critical` ; 250 ms | 0.02 / 0.3 s |
| `SMX_Results` | `WBP_Results` | `SCL_SFX_*` −20 dB, `SCL_Music` −4 dB, `SCL_UI` +2 dB | 0.2 / 0.3 s |
| `SMX_Pause` | `PC_Overdrive` pause | tout −24 dB sauf `SCL_UI` | 0.1 / 0.1 s |
| `SMX_BossPhase` | `OnPhaseChanged` | `SCL_SFX_*` −10 dB pendant 1.5 s | 0.1 / 0.6 s |
| **`SMX_RunFailed`** | `E_GameState.RunFailed` | **tout −40 dB sauf `SCL_UI`** — la coupure est le son. `SCL_Ambience` inclus : `S_LastLife_Loop` s'arrête ici | 0.05 / 0.5 s |

Implémentation : `Push` / `Pop Sound Mix Modifier`. **Toujours dépiler** (un mix oublié = mix cassé pour toute la run). Un seul point d'entrée : `SetAudioMix(E_AudioMix)` dans `BPFL_Overdrive`.
`SMX_RunFailed` est le seul mix qu'on ne dépile pas explicitement : il est purgé par le `OpenLevel(L_Menu)`
qui suit. **`GM_Overdrive::BeginPlay` repousse `SMX_Default` inconditionnellement**, ce qui garantit qu'il
ne survit pas — même règle que `Set Global Time Dilation(1.0)` (`SPEC_CAMERA_JUICE §6`).

### 3.3 Concurrency (`SCC_*`)

| Asset | Familles | Max | Résolution | Volume Scale (dupes) |
|---|---|---|---|---|
| `SCC_Laser` | `MS_Laser_Fire`, `S_Overheat_Deny` | 4 | Stop Oldest | 0.8 |
| `SCC_Impacts` | impacts laser, hits ennemis | 8 | Stop Lowest Priority | 0.7 |
| `SCC_EnemyDeath` | morts d'ennemis | 4 | Stop Oldest | 0.75 |
| `SCC_EnemyVoice` | alerte, grunts, tells | 5 | Prevent New | 1.0 |
| `SCC_Projectiles` | boucles + whizz | 6 | Stop Farthest | 1.0 |
| `SCC_Movement` | jump, land, wall jump | 4 | Stop Oldest | 0.9 |
| `SCC_UI` | tous les UI | 6 | Stop Oldest | 1.0 |
| `SCC_Loops` | slide loop, wall ride loop, vent, **`S_LastLife_Loop`** | 1 **par type** | Prevent New | 1.0 |

**Total voix simultanées cible : ≤ 32.** Au-delà, la lisibilité s'effondre bien avant les fps.

---

## 4. MetaSounds

`Content/OVERDRIVE/Audio/MetaSounds/`. On les utilise **là où un paramètre de gameplay module le son en continu** — ailleurs, un `SC_` (Sound Cue) suffit et coûte moins de temps de dev.

| Patch | Remplace | Justification |
|---|---|---|
| `MS_Laser_Fire` | 8 variantes de samples | pitch piloté par la chaleur = feedback gratuit et impossible en Cue |
| `MS_Wind_Speed` | boucle statique | le vent EST le HUD de vitesse (§5) |
| `MS_WallRide` | boucle statique | la résonance doit annoncer la fin de `WallRide_MaxDuration` |

### 4.1 `MS_Laser_Fire`

| Entrée | Type | Source |
|---|---|---|
| `HeatRatio` | Float 0–1 | `BPC_Heat` au moment du tir |
| `bOvercharged` | Bool | upgrade `OverchargedLaser` |
| `Seed` | Int | `Random Integer` côté BP |

Chaîne : `Trigger` → 3 couches parallèles. **Attaque** = Wave Player sur 4 `S_Laser_Click_0x` choisis par `Seed`, enveloppe 1 ms / 30 ms. **Corps** = `Saw Osc`, `Frequency = Lerp(900, 1400, HeatRatio)`, enveloppe de pitch descendante (Decay 120 ms) → `Ladder Filter` cutoff `Lerp(6000, 3000, HeatRatio)`. **Queue** = noise band-passé, decay 150 ms, gain −12 dB.
Pitch global : `Lerp(0, +4, HeatRatio)` demi-tons + jitter ±1.5 demi-ton (anti-fatigue). Si `bOvercharged` : + couche sub sine 55 Hz, decay 250 ms.

### 4.2 `MS_Wind_Speed` (boucle unique, jamais rejouée)

| Entrée | Type | Source |
|---|---|---|
| `Speed01` | Float 0–1 | `BPC_MovementState` — **normalisation propre au vent, sur `Speed_HardCap`** (cf. §5) |
| `bIsWallRiding` | Bool | `BPC_WallRide` |
| `HurtDuck` | Float 0–1 | `BPC_Health` (§5) |

Chaîne : `Noise (Pink)` → `Ladder Filter` (LPF cutoff `Lerp(400, 9000, Speed01^0.7)`) → `Biquad HPF` (`Lerp(60, 300, Speed01)`, évite la boue) → gain `Lerp(-40, -6 dB, Speed01)` → décorrélation stéréo. Seconde couche : `Noise (White)` band-passé 3–6 kHz, active seulement au-dessus de `SpeedLines_StartSpeed` normalisé.
`bIsWallRiding` → cutoff ×0.6 (le mur bouche l'oreille). `HurtDuck` → LPF fermé brutalement (0.02 s) puis réouverture 0.6 s.

### 4.3 `MS_WallRide`

| Entrée | Type | Source |
|---|---|---|
| `Speed01` | Float 0–1 | `BPC_MovementState` |
| `DurationRemaining01` | Float 1→0 | `BPC_WallRide` / `WallRide_MaxDuration` |

Chaîne : `Noise` → `Biquad Band Pass` (`Q = Lerp(1, 12, 1 - DurationRemaining01)` → devient tonal et urgent à la fin ; fréquence centrale `Lerp(800, 1800, Speed01)`) + `Sine Osc` de renfort dont le gain suit `1 - DurationRemaining01`. **Le joueur doit entendre qu'il va décrocher, avant de décrocher.**

---

## 5. Sensation de vitesse par le son

Le système, dans l'ordre de priorité de lecture par le joueur : **vent > pitch des sons de mouvement > doppler**.

| Couche | Comportement |
|---|---|
| Volume | `Lerp(-40, -6 dB, Speed01)` — quasi inaudible à l'arrêt, envahissant à 5000 uu/s |
| Filtre passe-bas | s'ouvre avec la vitesse : la sensation d'aigu = sensation de danger |
| Filtre passe-haut | monte aussi : évite que le vent masque le sub des impacts |
| Pitch | +0 à +3 demi-tons sur la couche haute uniquement |
| Coupure | `HurtDuck` : fermeture instantanée du LPF à chaque hit → **on entend la perte de vitesse avant de la voir** |
| Doppler | activé **uniquement** sur `ATT_Projectile` (les projectiles ennemis). Jamais sur le joueur : illisible à 5000 uu/s |

### Alimentation depuis `BPC_MovementState` — sans Tick

Le timer 20 Hz vit dans **`BPC_MovementState`** (D9), **pas** dans `BP_PlayerCharacter` : c'est le composant qui
possède la vitesse, et c'est le même timer qui écrit `MPC_Global.PlayerSpeed01` (`SPEC_VFX §3.1`).

```
BeginPlay (BPC_MovementState):
    WindComponent = SpawnSound2D(MS_Wind_Speed, bAutoDestroy = false)   // 1 seule instance, vit toute la run
    SetTimerByFunctionName("PushJuice", 0.05, Looping = true)           // 20 Hz, pas de Tick

PushJuice():
    // (a) scalaire des EFFETS DE VITESSE — formule D9, écrite dans MPC_Global (SPEC_VFX §3.1)
    PlayerSpeed01 = Clamp( (HorizontalSpeed - SpeedLines_StartSpeed)
                         / (SpeedLines_FullSpeed - SpeedLines_StartSpeed), 0, 1 )
    SetScalarParameterValue(MPC_Global, "PlayerSpeed01", PlayerSpeed01)

    // (b) scalaire du VENT — normalisation PROPRE au vent, sur Speed_HardCap (07_TUNING §3)
    Target   = Clamp(HorizontalSpeed / Speed_HardCap, 0, 1)
    Smoothed = FInterpTo(Smoothed, Target, 0.05, 4.0)                   // lissage BP, pas dans le MetaSound
    if (Abs(Smoothed - LastPushed) >= 0.01):                            // ne pousse que si ça change
        WindComponent.SetFloatParameter("Speed01", Smoothed)
        LastPushed = Smoothed
```

**Décision : le vent n'utilise PAS `PlayerSpeed01`, il a sa propre normalisation sur `Speed_HardCap`.**
Justification : `PlayerSpeed01` vaut **0 en dessous de `SpeedLines_StartSpeed`** (2500 uu/s) par construction
(D9) — le brancher sur le vent rendrait le vent totalement muet sur toute la moitié basse du registre de
vitesse, alors que c'est précisément là que le joueur a besoin d'entendre son accélération. Le vent est un
indicateur **analogique et continu de 0 à `Speed_HardCap`** ; les speed lines sont un effet de **seuil**. Deux
usages différents, deux normalisations différentes, **un seul timer et une seule lecture de la vitesse** —
c'est ça, le point de maintenance unique.

- **20 Hz suffit** : l'oreille n'entend pas la quantification derrière un `InterpTo` sur le cutoff côté MetaSound.
- Le même timer pousse `bIsWallRiding` → **un seul timer pour tout le juice continu.** `HurtDuck` est poussé **par événement** depuis `BPC_Health`, jamais par le timer.
- Interdit : `Spawn Sound 2D` du vent à répétition · `Set Float Parameter` dans Tick · `AudioComponent` du vent non détruit entre deux maps (il est recréé à chaque `BeginPlay`).

---

## 6. Ambiance & musique

### 6.0 Ambiance — **ville diurne, aérienne, en hauteur**

> **Révision 2026-08-18 (D2).** Le jeu se déroule dans une **ville blanche en plein jour**, sous un ciel
> bleu et un soleil franc — plus dans une ville néon nocturne. Toute description d'ambiance nocturne
> (bourdonnement de néon, ville qui dort, grondement urbain sourd, pluie, nappe froide) est **caduque**.

L'ambiance est portée par une boucle unique par monde, dans **`SCL_Ambience`** (−16 dB, §3.1),
référencée depuis `PDA_WorldData` (D33) au même titre que le ciel et la lumière.

| Asset | Usage | Description | Prio |
|---|---|---|---|
| `S_Ambience_City_Day` | World 1 — *Ascension* | **Air, pas ville.** Souffle de vent d'altitude large et stable, très peu de basses, quelques réflexions lointaines et **très réverbérées** (on est en hauteur, au-dessus de tout). Aucun trafic, aucune foule, aucun bruit d'activité : la ville est **vide**, c'est ce qui rend la vitesse possible. | P1 |
| `S_Ambience_City_Warm` | World 2 — *Redline* | Même base, plus **chaude** et légèrement plus dense : soleil rasant (`PALETTE.md §4`), donc un souffle plus grave et un peu de résonance métallique lointaine. | P2 |

**Règles** — boucle 2D unique par niveau, jamais spatialisée · **aucun contenu au-dessus de 4 kHz** (cette
bande appartient au vent `MS_Wind_Speed`, qui est du gameplay, §5) · **aucun événement ponctuel** (un son
d'ambiance qui « arrive » se lit comme une information et ment au joueur) · si le temps manque, **on coupe
l'ambiance entière** : le vent porte déjà 90 % de la sensation d'espace (R5).

**Interdit** : néon qui bourdonne · pluie · nappe froide ou inquiétante · trafic · foule · sirène ·
tout ce qui appartient à une ville nocturne.

### 6.1 Musique

`Content/OVERDRIVE/Audio/Music/`. Style : **synthwave solaire / électro rétro énergique**, saturé mais
**lumineux**, sans voix. Tonalités **majeures ou modales claires** (lydien, mixolydien) plutôt que mineures ;
leads brillants, arpèges rapides, basse ronde et présente, batterie sèche et en avant.
Références de ton : **Kavinsky période *Nightcall* en version diurne, Lifelike, Anoraak, la BO de
*Hotline Miami* pour l'énergie mais sans sa noirceur**, `The Midnight` pour la brillance des leads.

> **Révision 2026-08-18** : les références **Carpenter Brut / Perturbator / Dan Terminus** (darksynth,
> horreur, saturation agressive) sont **abandonnées**. Elles servaient la ville nocturne de la v1 et
> contrediraient frontalement une ville blanche en plein soleil : la musique et l'image raconteraient
> deux jeux différents. **Ce qui ne change pas** : le tempo, l'énergie, la sécheresse rythmique et
> l'absence de voix. On garde la vitesse, on perd la noirceur.

Mix : basse et kick présents mais **sous** `SCL_SFX`. La brillance de la musique vit dans les **médiums-aigus
mélodiques**, une bande que ni le vent (aigus bruités) ni les ennemis (bas-médium) n'occupent (§1).

### MVP (obligatoire) — 4 pistes + 5 stingers

| Asset | Usage | Tempo | Structure | Durée |
|---|---|---|---|---|
| `MU_Menu` | `L_Menu` | 100–110 BPM | boucle atmosphérique **lumineuse et suspendue**, peu d'événements | 1:30 loop |
| `MU_Gameplay_W1` | niveaux World 1 | 150–160 BPM | intro 4 mes. + boucle 1:30 seamless, **tonalité claire, lead brillant** | 1:30 loop |
| `MU_Gameplay_W2` | niveaux World 2 | 160–172 BPM | idem, plus dense et plus **chaude** (pas plus sombre — cf. le ciel de coucher de soleil de `PALETTE.md §4`) | 1:30 loop |
| `MU_Boss` | les 2 boss | 170–180 BPM | intro + boucle, break au phase change. **Le seul morceau du jeu qui a le droit d'être sombre** : c'est le contraste avec le reste qui le rend menaçant | 2:00 loop |
| `S_Stinger_LevelComplete` | fin de niveau | — | résolution majeure, enchaîne sur le rank | 1.5 s |
| `S_Stinger_Rank_D` … `_S` | 5 variantes (`E_Rank`) | — | cf. §2.4 — **nom unique et définitif : `S_Stinger_Rank_<D..S>`** | 0.8–2.5 s |
| `S_Stinger_Death` | mort du joueur | — | descente dissonante courte | 1.0 s |
| `S_Stinger_Chest` | ouverture de coffre | — | accord ascendant ambre | 1.2 s |
| `S_Stinger_RunComplete` | fin de run **réussie** | — | thème principal en version résolue | 4.0 s |

> **`S_Stinger_Death` et `S_LifeLost` sont deux choses différentes** : le premier est **musical** (il
> ponctue la mort dans le tissu de la piste), le second est un **SFX critique** (§2.4) qui dit combien il
> reste de vies. Les deux se jouent ensemble, dans deux Sound Classes différentes, avec deux timbres qui ne
> doivent pas se ressembler.
> De même, **`S_Stinger_RunComplete` (run terminée) et `S_RunFailed` (run perdue) sont symétriques et
> mutuellement exclusifs** : une run se termine par exactement l'un des deux.

> Les 5 stingers de rank sont **les mêmes assets** que ceux de §2.4 — un seul jeu de sons, un seul nom :
> `S_Stinger_Rank_D`, `_C`, `_B`, `_A`, `_S`. Toute autre écriture (`S_Rank_*`, `S_Stinger_Rank_*` générique)
> est obsolète.

**Règles MVP** : une **boucle unique par contexte**, jouée en 2D via un `AudioComponent` porté par `GI_Overdrive` (survit aux `OpenLevel`) ; crossfade 1.0 s entre deux pistes ; **stop net + stinger** en fin de niveau. La piste vient de `PDA_LevelData.MusicTrack` (`08_DATA_SCHEMAS §3`) — aucune sélection en dur.

### Optionnel (P2, seulement si S1–S3 sont validés)

Musique **dynamique en couches** : `MU_Gameplay_W1` en 3 stems (drums / bass+lead / arpège+pads) joués en parallèle et synchrones, gains pilotés par `CF_MusicIntensityBySpeed` (`08_DATA_SCHEMAS §5`) depuis le même timer 20 Hz que le vent ; couche 3 au-dessus de `SpeedLines_StartSpeed`. **Si le temps manque, on coupe cette section entière** — une bonne boucle statique bat une musique dynamique bâclée.

---

## 7. Où trouver les sons

### Registre des sources — **ce tableau est le registre officiel du projet**

Il n'y a **pas** de fichier `Docs/Audio_Sources.md` : le registre vit ici, dans la spec qui décrit les sons.
Pré-rempli avec les banques recommandées ; **Louis le complète au fur et à mesure** — une ligne par banque
réellement utilisée, et la colonne « Utilisé pour » se précise avec les noms d'assets du catalogue §2 dès
qu'un son en est tiré. **Sans ce tableau à jour, la publication est bloquée.**

| Source | Licence | URL | Utilisé pour |
|---|---|---|---|
| **Sonniss — GDC Game Audio Bundle** | royalty-free, usage commercial illimité, **pas d'attribution** | `sonniss.com/gameaudiogdc` | Impacts, whooshes, matières. La meilleure ressource gratuite (~30 Go/an) → base de `S_Melee_Hit`, `S_WallSlam`, `S_Land_Heavy` |
| **Freesound.org** — filtre **CC0 1.0 uniquement** | domaine public | `freesound.org` | Briques brutes à retravailler. **Filtre CC0 obligatoire** : CC-BY impose l'attribution, CC-NC interdit le commercial |
| **Kenney.nl — Audio packs** | CC0 | `kenney.nl/assets?q=audio` | UI et bips arcade prêts à l'emploi → `S_UI_Hover`, `S_UI_Click`, `S_UI_ScoreTick` |
| **99Sounds** | royalty-free, commercial OK | `99sounds.org` | Packs thématiques propres (impacts, sci-fi) → impacts laser, morts d'ennemis |
| **Pixabay Audio** | Pixabay Content License, commercial OK, sans attribution | `pixabay.com/sound-effects` | Musique de placeholder, ambiances |
| **Epic Games — packs audio du Fab / contenu UE** | Epic Content License (usage dans un projet Unreal) | `fab.com` | Ambiances, UI |
| **MusicRadar — Free Sample Packs** | royalty-free | `musicradar.com/news/tech/free-music-samples` | Synthés et drums pour fabriquer ses propres SFX (§ recette ci-dessous) |
| **Zapsplat** | gratuit **avec attribution** (ou Gold sans) | `zapsplat.com` | Large catalogue de dépannage — l'attribution est une contrainte réelle, à n'utiliser qu'en dernier recours |
| **OpenGameArt** (filtre CC0) · **Incompetech** (CC-BY) | variable — **vérifier par asset** | `opengameart.org` · `incompetech.com` | Dépannage, musique de secours |
| **Synthèse procédurale du projet** — `Art_Source/Audio/synth/` | **aucune licence tierce** : les échantillons sont calculés, rien n'est emprunté | *(interne)* | `S_Laser_Fire` · `S_Laser_Hit_Body` / `_Head` · `S_Laser_Impact_Surface` · `S_Heat_Warning` · `S_Enemy_Hit` · `S_Enemy_Death` · `S_Jump` · `S_Land_Light` / `_Heavy` · `S_Dash` · `S_Dash_Ready` · `S_Slide_Start` / `_Loop` / `_End` · `S_WallRide_Enter` / `_Loop` · `S_WallJump` · `S_Wind_Loop` |
| *(à compléter)* | | | |

> **Sur la synthèse procédurale.** Les WAV ne sont pas la source : ce sont les **paramètres** du dict `P` de
> `overdrive_sfx.py` qui le sont. `Art_Source/Audio/out/` est gitignoré et se régénère par
> `python overdrive_sfx.py`. Conséquence pratique : réécouter et corriger un son coûte une minute, pas une
> session Audacity — c'est ce qui rend l'itération de R4 (« prototype → test → c'est fun ? ») réellement
> praticable sur l'audio. `analyze.py` mesure durée, niveau, centroïde et **qualité du raccord des boucles** ;
> `audition.py` fabrique les montages d'écoute en contexte, avec les dB relatifs de §2 déjà appliqués.
> Aucune de ces mesures ne dit si un son est bon (R8) — elles disent seulement s'il est conforme à §2.

⚠ **À éviter** : BBC Sound Effects (licence RemArc = **non commercial**) · YouTube Audio Library sans vérifier la
ligne de licence · tout sample « free » sans page de licence explicite.
**Règle de tenue** : dès qu'un fichier téléchargé entre dans `Content/OVERDRIVE/Audio/`, sa banque d'origine
doit figurer ci-dessus, et le nom de l'asset `S_*` produit doit apparaître dans « Utilisé pour ».

### Fabriquer un SFX arcade en 10 minutes
Outils gratuits : **Audacity** · **Bfxr / jsfxr / ChipTone** (générateurs 8-bit, sortie libre de droits) · **Surge XT** ou **Vital** (synthés) · **Cakewalk** ou **Reaper** (éval illimitée) · et **MetaSounds dans l'éditeur** (souvent le plus rapide ici). Recette valable pour 90 % du catalogue :
1. **Attaque (0–30 ms)** — un transient : clic, claquement, noise burst très court. C'est ce qui donne la punchiness.
2. **Corps (30–200 ms)** — oscillateur avec **enveloppe de pitch descendante** (sweep vers le bas = impact, vers le haut = charge/récompense). La règle la plus rentable de tout le sound design arcade.
3. **Queue (0–400 ms)** — noise filtré ou courte réverbe. Coupe-la impitoyablement : à 4000 uu/s elle ne sert à rien.
4. **Traitement** — saturation légère, **passe-haut à 120 Hz** sauf impacts lourds, compression rapide.
5. **Finition** — normaliser à −3 dBFS, trim des silences, 3–4 variantes (pitch ±2 demi-tons, gain ±2 dB), export **WAV 44.1 kHz 16-bit** mono (3D) ou stéréo (2D). Import UE : compression `ADPCM` pour les SFX courts.

---

## 8. Implémentation technique

### 8.1 Attenuation (`Content/OVERDRIVE/Audio/Mix/`)

| Asset | Inner / Falloff | Courbe | Options |
|---|---|---|---|
| `ATT_Enemy3D` | 800 / 4000 uu | Logarithmic | Spatialization Panning, Air Absorption on, Occlusion **off** (coûteux) |
| `ATT_Impact3D` | 400 / 3500 uu | Inverse | Focus off |
| `ATT_Projectile` | 300 / 3000 uu | Natural Sound | **Doppler on** (Intensity 0.6 `[À CALIBRER]`) |
| `ATT_TankFootstep` | 1500 / 8000 uu | Logarithmic | doit porter loin : c'est un avertissement |

**Non-Spatialized Radius** ≥ 200 uu partout : à haute vitesse un son qui saute d'une oreille à l'autre est désagréable. Les sons du joueur ne sont **jamais** 3D (§2.1) : il bouge trop vite pour que la spatialisation ait un sens.

### 8.2 Où déclencher

| Son | Point de déclenchement | Pourquoi |
|---|---|---|
| Laser, overheat, deny | `BP_LaserWeapon.PlayFireFX()` | déjà le point unique des FX (`SPEC_COMBAT §2`) |
| Melee swing, melee hit | **Anim Notify** sur `AM_Melee_Punch` (`AN_MeleeHit` pour le hit) | le son doit coller à l'anim, pas à l'input |
| Dash, slide, wall ride, saut | Event Dispatchers des `BPC_*` correspondants | jamais depuis l'input : un input refusé ne doit pas sonner |
| Impacts, morts d'ennemis | `BP_EnemyBase`, via les soft refs `HitSFX`/`DeathSFX` de `PDA_EnemyData` | data-driven, pas de branche par type |
| UI | `WBP_*` directement | — |
| Vent, boucles | `AudioComponent` persistant créé au `BeginPlay` | jamais spawné à répétition |

> **§8.2a — état réel au 2026-08-21 (J11), ce paragraphe fait foi.**
>
> **Aucun `SC_*` n'existe et aucun toolset MCP ne sait créer un `SoundCue`.** La « variation
> obligatoire » de `§8.3 r3` est donc obtenue par **tableaux `SoundBase[]` + index aléatoire +
> pitch aléatoire ±`Audio_PitchVariance`**, ce qui rend exactement ce qu'un `Random` + `Modulator`
> de Cue rendrait. **Remplaçable par un `SC_*` sans toucher un seul graphe** : il suffira de mettre
> le Cue seul dans le tableau.
>
> | Famille | Où vivent les variantes | Qui joue |
> |---|---|---|
> | Saut, wall jump, atterrissage, dash, slide, wall ride | `BPC_PlayerAudio`, 9 tableaux | `BP_PlayerCharacter` route les dispatchers → `BPC_PlayerAudio.Play*()` |
> | Tir, impact décor, headshot, chaleur | `PDA_WeaponData`, 4 tableaux → `DA_Weapon_Laser` | `BP_LaserWeapon.PlayFireFX` / `SendHitFeedback` / event lié `OnWarningEntered` |
> | Hit et mort d'ennemi | `PDA_EnemyData.HitSFX` / `DeathSFX` | `BP_EnemyBase.ApplyDamage` (J10, inchangé) |
>
> **Les 4 composants de mouvement ne jouent aucun son eux-mêmes.** C'est la règle « déclencher sur
> les dispatchers » prise au pied de la lettre, et elle a une vertu qui n'était pas annoncée : tout
> l'audio de mouvement s'est câblé **sans modifier une ligne** de `BPC_MovementState`, `BPC_Slide`,
> `BPC_Dash` ni `BPC_WallRide` — les 4 composants validés manche en main entre le J4 et le J8.
>
> **Pas encore câblé** : les 4 **boucles** (`S_Slide_Loop`, `S_WallRide_Loop`, `S_Wind_Loop` ×2),
> qui exigent un `AudioComponent` persistant avec fondus (`§8.3 r4`) → J14 ; et `S_Dash_Ready`,
> faute de dispatcher de rechargement de charge sur `BPC_Dash`.

### 8.3 Anti-spam et pooling

1. **Concurrency d'abord** (§3.3) : garde-fou moteur, il fonctionne même si un BP se trompe.
2. **Gate temporel côté BP** pour les sons à haute cadence : `S_Laser_Impact_Surface` et `S_Enemy_Hit` ne rejouent pas dans les 60 ms **[À CALIBRER]** ; un `LastPlayTime` par famille comparé à `Get Game Time in Seconds`.
3. **Variation obligatoire** : tout son joué > 1×/s a ≥ 3 variantes + pitch aléatoire ±5 % (`Random` + `Modulator` dans le Cue, ou `Seed` dans le MetaSound).
4. **Pooling** : `05_ARCHITECTURE §6` interdit le pooling générique. Seule règle audio : **les boucles sont des composants persistants** (vent, slide, wall ride, projectile), **les one-shots passent par `Play Sound at Location` / `Play Sound 2D`** — le moteur gère déjà son pool de voix. Aucun `AudioComponent` spawné pour un one-shot.
5. **Fuites** : `au.Debug.SoundWaves 1` / `stat SoundWaves` en fin de niveau — aucune boucle orpheline.
6. **Priority** : `S_Player_Hurt`, `S_Overheat`, `S_Enemy_Projectile_Whizz` à 1.0 ; mouvement 0.5 ; UI 0.4.

---

## 9. Ordre de production (4 semaines)

Le son **n'est pas repoussé à la fin**. Chaque système livré arrive avec ses P0 audio.

> **Cette spec planifie en semaines** (D23). Le découpage en jours est l'affaire exclusive de
> `04_ROADMAP.md` : si les deux divergent, c'est la roadmap qui a raison sur le calendrier.

| Semaine | Livraison audio | Pourquoi maintenant |
|---|---|---|
| **S1 — infra + mouvement** | Sound Classes + `SMX_Default` + `SCC_*` de base · `MS_Wind_Speed` + timer 20 Hz · `S_Dash`, `S_Jump`, `S_Land_*`, `S_Slide_*`, `S_WallRide_Enter` (placeholders Sonniss acceptés) | Le mouvement se calibre **avec** son son. Sans vent, on ne peut pas juger si le jeu est rapide. |
| **S2 — combat** | `MS_Laser_Fire` · `S_Laser_Hit_Body` / `_Head` · `S_Enemy_Death` · `S_Melee_Swing` / `_Hit` · `S_WallSlam` · `S_Heat_Warning`, `S_Overheat`, `S_Overheat_Deny`, `S_Heat_Ready` · `S_Player_Hurt` | Le TTK et le tuning de chaleur se jugent à l'oreille. `S_WallSlam` est le son signature du jeu. |
| **S2 fin** | `SMX_Overheat`, `SMX_TookDamage` · `SCC_*` complets · `ATT_*` | Le mix arrive **avant** l'ajout de contenu, sinon il faut tout remixer. |
| **S3 — ennemis, UI, systèmes** | `S_Enemy_Alert`, `S_Enemy_Shoot` (+tell), `S_Enemy_Projectile_*`, `S_Tank_Step` · `S_Stinger_Rank_D..S`, `S_LevelComplete`, `S_Chest_*`, `S_Upgrade_Select`, `S_Checkpoint`, UI · **`S_LifeLost` + `S_LastLife_Loop`** · `MS_WallRide` · `MU_Gameplay_W1` | Le tell du Shooter est du gameplay pur : sans lui, les projectiles sont injustes. Les vies arrivent avec le système de run — `S_LifeLost` est **P0**, il ne se repousse pas en S4. |
| **S3 fin** | `MU_Menu`, `MU_Gameplay_W2` · `SMX_Results`, `SMX_Pause`, **`SMX_RunFailed`** · **`S_RunFailed`** · passe de variations (3–5 samples par son P0) | La fatigue auditive apparaît seulement après une session longue : il faut du temps pour la détecter. |
| **S4 — boss & mix final** | `MU_Boss`, `S_Boss_*` · `S_Stinger_RunComplete` · **`S_Ambience_City_*`** (§6.0) · **passe de mix complète au casque ET aux enceintes** · réglage des concurrency sous charge réelle · slider volumes dans `WBP_Settings` (Master / Music / SFX) · P2 restants | Le mix final se fait sur le jeu complet, pas sur des systèmes isolés. L'ambiance arrive en dernier : c'est la couche la plus facile à couper et la moins informative. |

**Règle de coupe (R5)** : couper dans l'ordre `S_Speed_Threshold` → **ambiance (§6.0)** → variations de mort par archétype → musique dynamique en couches → `S_RunFailed` → stingers non-rank → `S_Boss_Weakpoint_Hit`. **On ne coupe aucun P0**, et surtout rien de `SCL_SFX_Critical` : ce sont des informations de gameplay, pas de la décoration. `S_LifeLost` et `S_LastLife_Loop` en font partie.

---

## 10. Checklist de validation

**Par son**
- [ ] Nom conforme (`S_` / `SC_` / `MS_`), rangé dans `Content/OVERDRIVE/Audio/SFX/<Famille>/`
- [ ] Sound Class assignée (jamais de volume en dur dans un BP) et Concurrency assignée si joué plus d'1×/s
- [ ] ≥ 3 variantes + pitch aléatoire pour tout son à cadence élevée
- [ ] Normalisé à −3 dBFS, silences trimés, mono pour le 3D / stéréo pour le 2D
- [ ] Attenuation assignée si 3D ; `Non-Spatialized Radius` ≥ 200 uu
- [ ] Source et licence inscrites dans le **registre des sources de §7**
- [ ] Écouté **en jeu à 3000+ uu/s**, pas dans le Content Browser

**Par système**
- [ ] Aucun Tick BP pour l'audio ; un seul timer 20 Hz partagé avec le juice visuel (§5)
- [ ] Aucune boucle orpheline après un changement de niveau (`au.Debug.SoundWaves 1`)
- [ ] Tout `Push Sound Mix Modifier` a son `Pop` garanti, y compris en cas de mort ou de pause pendant l'effet
- [ ] ≤ 32 voix simultanées dans le pire cas (combat dense + boss)
- [ ] Volume Master / Music / SFX exposés dans `WBP_Settings` et persistés
- [ ] Le jeu reste **jouable et lisible** avec `SCL_Music` à −60 dB (test d'accessibilité)
- [ ] **Vies** : `S_LifeLost` ne ressemble à aucun autre son du jeu · `S_LastLife_Loop` est un
  `AudioComponent` persistant porté par `GI_Overdrive`, survit aux `OpenLevel`, et s'arrête à
  `RunFailed` comme à `StartNewRun()` · aucune boucle orpheline après une run perdue
  (`au.Debug.SoundWaves 1`) · `S_LastLife_Loop` ne masque **ni** `S_Enemy_Shoot` **ni**
  `S_Enemy_Projectile_Whizz` (rien au-dessus de 200 Hz)
- [ ] **Ambiance** : aucune boucle d'ambiance nocturne (néon, pluie, trafic) · rien au-dessus de 4 kHz ·
  aucun événement ponctuel dans une boucle d'ambiance
- [ ] **Musique** : aucune piste de gameplay en tonalité mineure sombre — `MU_Boss` est la seule exception

**Test manuel pour Louis (R8)**
1. Jouer un niveau complet **sans regarder le HUD**. Sais-tu quand tu vas surchauffer ? quand tu vas vite ? quand un projectile arrive ? Si non → c'est le son qui a échoué, pas le HUD.
2. Enchaîner 10 tirs jusqu'à l'overheat. **Le pitch monte-t-il assez pour anticiper ?** L'overheat est-il une punition *sonore* claire (coupure nette) ou juste un son de plus ?
3. Faire un wall slam. **Est-ce le son le plus satisfaisant du jeu ?** Sinon, remonter son gain et sa couche sub avant tout le reste.
4. Enchaîner 5 bunny hops parfaits. **La montée de notes donne-t-elle envie de recommencer ?**
5. Jouer 15 min d'affilée. **Quel son te fatigue en premier ?** → variations en plus, ou baisser sa classe.
6. Couper la musique. **Le jeu reste-t-il bon ?** Il doit l'être : la musique est un renfort, pas une béquille.
7. **Mourir, les yeux fermés au respawn. Sais-tu que tu viens de perdre une vie, et non de prendre un coup ?**
   Si les deux sons se ressemblent, c'est `S_LifeLost` qu'on refait — pas le HUD.
8. **Jouer un niveau entier à 1 vie restante.** La tension s'entend-elle ? Et au bout de 5 minutes,
   est-elle devenue **agaçante** ? Si oui, baisser `S_LastLife_Loop` avant de la supprimer : à −20 dB elle
   doit se sentir sans s'écouter.
9. **Écouter `MU_Gameplay_W1` en regardant le jeu.** La musique et l'image racontent-elles le même jeu ?
   Une ville blanche en plein soleil sur du darksynth sonne comme un bug de build (§6.1).
