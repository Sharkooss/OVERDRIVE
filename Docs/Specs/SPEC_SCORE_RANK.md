# SPEC — SCORE & RANK

> Système de fin de niveau : mesure → score → rank → écran de résultats.
> **Blueprint only.** Aucune valeur numérique n'est écrite ici : tout renvoie à `Docs/07_TUNING.md §14`
> par nom de clé. Structs/Enums : `Docs/08_DATA_SCHEMAS.md`. Architecture : `Docs/05_ARCHITECTURE.md`.
> Intention d'origine : `Docs/02_GDD.md §39–§42`. Décisions tranchées : `Docs/11_ARBITRAGES.md` (D1, D13, D14, D16).

---

## 1. Objectif

Le score n'est pas une note scolaire, c'est un **bouton RESTART déguisé**.

L'écran de résultats doit produire, en moins de 4 secondes de lecture, exactement une pensée :
> « Ah OK. J'ai raté le S à cause de **ça**. Je le refais. »

Trois conséquences directes sur le design :

| Règle | Conséquence technique |
|---|---|
| Le joueur doit comprendre **instantanément** | 4 composantes, pas 9. Une ligne = une composante. |
| Le coupable doit être **désigné**, pas déduit | L'écran calcule et surligne LA statistique manquante (§7). |
| Relancer doit être **gratuit** | `Restart_FadeDuration` (§16). Aucun menu intermédiaire, une touche. |

Le score ne débloque **rien de permanent** (pas de méta-progression au MVP). Il ne sert qu'à :
1. donner un verdict lisible sur la performance,
2. ouvrir le coffre du rank correspondant (`SPEC_LOOT_UPGRADES.md`).

**Anti-objectif** : le score ne doit jamais récompenser la lenteur, la prudence ou l'exhaustivité
maniaque. Un joueur qui nettoie chaque recoin en 4 minutes doit finir en **C**, pas en **S**.

---

## 2. Les 4 composantes

| Composante | Ce qu'elle mesure | Ce qu'elle récompense | Pourquoi elle existe |
|---|---|---|---|
| **TIME** | temps écoulé du start trigger à l'end trigger | l'optimisation de trajectoire, la connaissance du niveau | c'est le pilier « vitesse » du jeu. La plus grosse contribution potentielle. |
| **KILLS** | ennemis tués (× bonus headshot / wall slam) | l'agressivité — tuer **en passant** | empêche le speedrun qui ignore tout le combat. |
| **SPEED** | vitesse **moyenne** sur tout le niveau | ne jamais s'arrêter | distingue « rapide au chrono » de « rapide en permanence ». Punit le stop-and-pop. |
| **STYLE** | multiplicateur global appliqué à la somme | l'enchaînement, le panache | c'est le seul terme **multiplicatif** : c'est lui qui crée l'écart entre A et S. |

**Pourquoi TIME et SPEED ne font pas doublon** : un joueur peut finir vite en sprintant en ligne
droite avec des arrêts (bon TIME, SPEED moyen), ou maintenir une vitesse élevée mais mal router
(bon SPEED, TIME moyen). Le S exige les deux.

**Pourquoi STYLE est multiplicatif** : additif, il serait une 5ᵉ ligne comptable ignorable.
Multiplicatif, il devient la question centrale — « est-ce que j'ai joué **proprement** du début à la fin ».

---

## 3. Formule complète

### 3.1 Formule de référence (`07_TUNING §14`)

```
Score = ( ScoreKills + ScoreSpeed + ScoreTime ) × StyleMultiplier

ScoreKills  = Σ ScoreBase(ennemi)  [+ 50 % si headshot, + 30 % si wall slam]
ScoreSpeed  = round( AvgSpeed / 10 ) × 5
ScoreTime   = max( 0, (ParTime - Time) × 100 )
```

### 3.2 Chaque terme, développé

#### `ScoreKills`
Accumulé **en direct**, pas recalculé à la fin. À chaque mort d'ennemi, `BP_EnemyBase` envoie
`NotifyScoreEvent` (`BPI_ScoreEvent`) au `GS_Overdrive` avec le `ScoreBase` lu dans son
`PDA_EnemyData` et le `E_DamageType` du coup fatal.

```
FUNCTION AddKill(EnemyData, KillingDamageType)
    Points = EnemyData.ScoreBase
    IF KillingDamageType == LaserHeadshot : Points *= (1 + Kill_HeadshotBonus)   // §14
    IF KillingDamageType == WallSlam      : Points *= (1 + Kill_WallSlamBonus)   // §14
    ScoreKills += round(Points)
    Kills      += 1
    IF KillingDamageType == LaserHeadshot : Headshots += 1
```
Les bonus **ne se cumulent pas** entre eux (un kill est headshot **ou** wall slam, jamais les deux —
le `E_DamageType` du coup fatal est unique). Un ennemi dont `S_EnemySpawnEntry.bCountsForScore = false`
(ennemi de décor, spawn scripté infini) n'incrémente ni `ScoreKills` ni `Kills`.

#### `ScoreSpeed`
`AvgSpeed` est en `uu/s`. La division par 10 correspond exactement à l'affichage HUD
(`CLAUDE.md §4 — Unités`) : le joueur voit à l'écran le nombre qui alimente son score. Voulu.

#### `ScoreTime`
`ParTime` = `PDA_LevelData.RankThresholds.ParTimeSeconds`.
Le terme est **clampé à 0** : dépasser le par time ne donne pas un score négatif, il donne **zéro**.
C'est délibéré — la punition du lent est de perdre la plus grosse source de points, pas de partir en
dette (un score négatif serait illisible et anti-motivant).

#### `StyleMultiplier`
Valeur de `BPC_StyleMeter.CurrentMultiplier` **au moment où le end trigger est franchi**
(= `S_LevelScore.FinalStyleMultiplier`). Bornée `[Style_Start … Style_Max]` (§14).
`PeakStyleMultiplier` est enregistré séparément **pour l'affichage uniquement** : il n'entre pas
dans la formule. Sinon le joueur optimiserait un pic à la seconde 12 puis se relâcherait.

### 3.3 Cas limites

| Cas | Comportement | Justification |
|---|---|---|
| `Time > ParTime` | `ScoreTime = 0`, jamais négatif | lisibilité, pas de dette |
| `Time` très inférieur au par | pas de cap explicite ; le cap réel vient du level design (le niveau a une longueur minimale) | un skip de géométrie légitime doit payer |
| **0 kill** | `ScoreKills = 0`. Le rank reste calculable, mais `TargetKills` rend le S mathématiquement inatteignable sur un niveau de combat | on ne bloque pas, on rend juste le S hors de portée |
| **Mort** | `Deaths += 1` ; `Style` → `Style_Loss_Death` (reset) ; malus fixe `Score_DeathPenalty` (§14) ; **`LivesRemaining -= 1`** (`Run_MaxLives`, `07_TUNING §18`) ; le chrono **continue de tourner** pendant le fade + respawn ; **les upgrades sont conservés** | la mort coûte du temps, du style **et une vie sur trois** — mais jamais les upgrades (`11_ARBITRAGES D1`, GDD §50) |
| **Dernière vie perdue** | même traitement au niveau du **score du niveau** (rien de spécial), puis `E_GameState.RunFailed` : le niveau n'est **jamais** terminé, donc `ComputeScore()` **n'est pas appelé** et aucun `S_LevelScore` n'est ajouté | le score d'un niveau se gagne en **franchissant l'end trigger**, jamais en mourant dedans (§7.5) |
| **Joueur qui camp** | triple punition automatique : `ScoreTime` fond, `AvgSpeed` s'effondre (échantillonnage continu), `Style_Loss_Idle` déclenche | aucune règle anti-camp spécifique n'est nécessaire, la formule s'en charge |
| **Score final ≤ 0** | clamp à 0 avant le calcul de rank | |
| `ParTime = 0` (level data non renseigné) | `ScoreTime = 0` + warning `Print String` en éditeur uniquement | détection d'un `DA_Level_*` non calibré |
| **Boss** | même formule ; `TargetKills = 1`, `ParTime` = durée de combat cible | pas de formule spéciale au MVP |

### 3.4 Échantillonnage de `AverageSpeed`

Pas de `Tick`. Un **Timer** sur `BPC_ScoreManager` (`GS_Overdrive`), cadence `Score_SpeedSampleRate` (§14).

```
EVENT SampleSpeed  (timer, looping)
    IF GS.CurrentGameState != Gameplay : RETURN      // écran de fin, loot, pause → pas d'échantillon
    IF bIsRespawning                   : RETURN
    Speed = BPC_MovementState.GetHorizontalSpeed()   // uu/s, composante Z ignorée
    SpeedSum   += Speed
    SpeedCount += 1
    MaxSpeed    = max(MaxSpeed, Speed)               // celui-ci utilise la vitesse 3D complète
    AverageSpeed = SpeedSum / SpeedCount
```

Règles précises :
- **Ce qui compte** : tous les états de `E_MovementState`, y compris `Falling`, `WallRiding`, `Dashing`.
  Être en l'air n'est pas une pause.
- **Composante utilisée** : vitesse **horizontale** (X,Y) pour la moyenne — une chute verticale ne
  doit pas gonfler le score. `MaxSpeed` utilise la vitesse 3D (c'est une stat de vantardise).
- **Pauses** : timer **arrêté** (`Pause Timer`, pas `Clear`) quand `E_GameState` vaut `Paused`,
  `LevelComplete`, `Loot`, `Transitioning`. L'écran de résultats ne dilue jamais la moyenne.
- **Mort/respawn** : échantillonnage suspendu du `OnDeath` jusqu'à la fin du fade de respawn.
  Le joueur ne gagne pas une moyenne artificiellement haute ni basse en mourant.
- **Départ** : le timer démarre sur `BP_LevelManager.OnLevelStarted`, pas sur `BeginPlay`
  (sinon l'intro/fade-in compte comme de la vitesse nulle).
- Ce timer **n'écrit pas** `MPC_Global.PlayerSpeed01` : ce scalaire a un seul écrivain,
  `BPC_MovementState`, via son propre timer 20 Hz (`11_ARBITRAGES D9`, `SPEC_MOVEMENT §2.5`).

---

## 4. Style multiplier — `BPC_StyleMeter`

Composant sur `BP_PlayerCharacter`. **Il ne connaît pas le score** : il expose un float et des
dispatchers, `BPC_ScoreManager` et `WBP_StyleMeter` s'y abonnent.

### 4.1 Variables

| Variable | Type | Category | Rôle |
|---|---|---|---|
| `CurrentMultiplier` | Float | Score | valeur courante, init `Style_Start` |
| `PeakMultiplier` | Float | Score | max atteint sur le niveau (affichage) |
| `TimeSinceLastGain` | Float | Score | remis à 0 à chaque gain |
| `bDecayActive` | Bool | Score | vrai après `Style_DecayDelay` sans gain |
| `StyleEventTable` | DataTable | Score | `DT_StyleEvents`, Instance Editable |
| `LastEventOfType` | Map\<`E_StyleEvent`, Float\> | Score | timestamp du dernier gain par type (anti-spam) |
| `SameSourceCount` | Map\<`E_StyleEvent`, Int\> | Score | gains consécutifs du même type (dégressivité) |
| `LastWallRideSurface` | Object (soft) | Score | mur du dernier `WallRideTick` crédité |
| `bIsIdleTicking` | Bool | Score | anti double-application du malus d'immobilité |

Dispatchers : `OnStyleChanged(NewValue, Delta, Event)` · `OnStyleTierChanged(NewTier)` ·
`OnStyleMaxed()`.

### 4.2 Arrivée des événements

Un seul point d'entrée, appelé par les composants via le `BP_PlayerCharacter` (dispatch vers le
haut, cf. `05_ARCHITECTURE §3`) :

```
FUNCTION AddStyleEvent(Event : E_StyleEvent)
    Row = DT_StyleEvents.GetRow(Event)              // S_StyleEventDef : Delta, bIsPerSecond, DisplayText
    IF NOT IsEventAllowed(Event) : RETURN           // §4.4 anti-farm
    Delta = Row.Delta * GetDiminishFactor(Event)
    CurrentMultiplier = clamp(CurrentMultiplier + Delta, Style_Start, Style_Max)
    PeakMultiplier    = max(PeakMultiplier, CurrentMultiplier)
    TimeSinceLastGain = 0 ; bDecayActive = false
    Dispatch OnStyleChanged(CurrentMultiplier, Delta, Event)
```

| Émetteur | Événement `E_StyleEvent` | Clé de gain (§14) |
|---|---|---|
| `BP_EnemyBase.OnDeath` | `Kill` / `Headshot` / `MeleeKill` / `WallSlamKill` | `Style_Gain_Kill` / `_Headshot` / `_MeleeKill` / `_WallSlamKill` |
| `BPC_ScoreManager` (contexte du kill) | `SlideKill` / `AirKill` | `Style_Gain_SlideKill` / `_AirKill` |
| `BPC_WallRide` (timer 1 s) | `WallRideTick` | `Style_Gain_WallRide` (`bIsPerSecond = true`) |
| `BPC_Dash.OnDashPerformed` | `Dash` | `Style_Gain_Dash` |
| `BPC_ScoreManager` (timer 1 s) | `HighSpeedTick` | `Style_Gain_HighSpeedSustain` |
| `BPC_Health.OnDamageTaken` | `TookDamage` | `Style_Loss_TakeDamage` |
| timer d'immobilité | `Idle` | `Style_Loss_Idle` |
| `BPC_Health.OnDeath` | `Death` | `Style_Loss_Death` → reset à `Style_Start` |
| **`BPC_Heat` (timer `Heat_TickInterval`)** | **— aucun `E_StyleEvent`, cf. §4.2b** | **`Style_Loss_Heat`** |

Le contexte d'un kill est résolu **une seule fois**, dans l'ordre de priorité :
`WallSlamKill > Headshot > MeleeKill > AirKill > SlideKill > Kill`. **Un kill = un seul événement de
style.** Pas d'empilement, pas de combo à mémoriser : c'est la règle qui garde le système intuitif.

### 4.2b Perte continue liée à la chaleur — `Style_Loss_Heat` (`11_ARBITRAGES D58`)

**La chaleur de l'arme est la seule entrée du Style Meter qui n'est pas un `E_StyleEvent`.** C'est
délibéré : la chaleur est un **état** qui dure, pas un accident qui arrive.

```
EVENT HeatTick   (timer de BPC_Heat, cadence Heat_TickInterval — 07_TUNING §11)
    IF BPC_Heat.CurrentHeat >= Heat_WarningThreshold :
        CurrentMultiplier = max(Style_Start, CurrentMultiplier + Style_Loss_Heat * DeltaTime)
        Dispatch OnStyleChanged(...)
```

| Règle | Détail |
|---|---|
| Condition | `CurrentHeat >= Heat_WarningThreshold` (`07_TUNING §11`). En dessous : **aucune perte**. |
| Nature | Perte **continue**, par seconde, exprimée par `Style_Loss_Heat` (`07_TUNING §14`). Elle **n'appelle pas `AddStyleEvent`**. |
| Anti-farm | **Hors périmètre** de `IsEventAllowed` / `GetDiminishFactor` (§4.4) : une pénalité ne se farme pas, et la dégressivité l'affaiblirait à mesure qu'elle dure — exactement l'inverse de l'intention. |
| Cumul | Se **cumule** avec `Style_DecayPerSec` (§4.3). Un joueur chaud **et** inactif paie les deux. |
| Plancher | `Style_Start`, comme toute perte. Jamais en dessous. |
| Canal de score | **Aucun.** La chaleur n'a **pas** de ligne dédiée dans le score : elle passe entièrement par le style (`11_ARBITRAGES D58`, options écartées). L'écran de résultats reste à **4 composantes** (§2). |

**Comment le joueur éteint cette perte** — les deux puits de `SPEC_COMBAT §4.1` : un **headshot**
(retrait fixe, `Heat_CoolPerHeadshot`) ou **rouler au-dessus de `Heat_CoolSpeedThreshold`**
(retrait continu, `Heat_CoolRateAtSpeed`). Il n'y a **aucune décroissance passive** : attendre ne
refroidit rien.

> ⚠️ **`Heat_CoolSpeedThreshold` est la même valeur que le seuil de `Style_Gain_HighSpeedSustain`,
> volontairement** (`07_TUNING §11`/`§14`). Au-dessus de ce seuil, le joueur **gagne du style et
> refroidit son arme en même temps** : une seule règle, deux récompenses. C'est la clé de voûte du
> design de D58 — **les deux valeurs se déplacent ensemble, jamais l'une sans l'autre.**

> ### ⏳ Dette datée au J18
>
> `BPC_StyleMeter` **n'existe qu'au J18**, `BPC_Heat` arrive au **J9**. Entre les deux, `BPC_Heat`
> calcule la perte (`GetCurrentStylePenalty()`) et la **fait afficher** telle quelle par le HUD
> (`SPEC_UI_HUD §3.3`) **sans que personne ne la consomme**. Le câblage réel vers
> `BPC_StyleMeter` est à faire au J18 (`04_ROADMAP`) — l'affichage provisoire existe pour que la
> mécanique reste **jugeable** dès le J9 (parade au piège `12_PIEGES §6.24`).

### 4.3 Décroissance

```
EVENT StyleTick (timer, cadence = Score_StyleTickRate, §14)
    TimeSinceLastGain += DeltaTime
    IF TimeSinceLastGain >= Style_DecayDelay :
        bDecayActive = true
        CurrentMultiplier = max(Style_Start, CurrentMultiplier - Style_DecayPerSec * DeltaTime)
        Dispatch OnStyleChanged(...)
```
- Plancher : `Style_Start` (jamais en dessous de x1.00, jamais négatif). Vaut aussi pour
  `Style_Loss_Heat` (§4.2b), qui **se cumule** avec cette décroissance sans jamais franchir le plancher.
- Plafond : `Style_Max`. Au plafond, `OnStyleMaxed` déclenche un feedback HUD dédié et les gains
  supplémentaires sont **silencieusement absorbés** (pas de banque de style en réserve).
- Reset complet à `Style_Start` : mort du joueur, et chargement d'un nouveau niveau.
  **Le style ne traverse pas les niveaux** — chaque niveau est une performance indépendante.
- Le checkpoint **ne restaure pas** le style d'avant la mort.

### 4.4 Anti-farm dégénéré

Le style doit dire « je joue bien », pas « je connais l'exploit ». Trois garde-fous, tous dans
`IsEventAllowed()` / `GetDiminishFactor()` :

| Exploit | Parade |
|---|---|
| **Spam de dash** sur place pour empiler `Style_Gain_Dash` | `Dash` n'est crédité que si le dash a produit un déplacement réel : vitesse horizontale après dash ≥ `Style_MinSpeedForDashGain` (§14). De plus le nombre de charges et `DashCooldown` bornent naturellement la fréquence. |
| **Wall ride en boucle sur le même mur** | `WallRideTick` n'est crédité que si `HitSurface != LastWallRideSurface`, **ou** si le joueur a touché le sol / un autre mur entre-temps. Le cooldown same-wall existant de `BPC_WallRide` (`SPEC_MOVEMENT`) fait le reste. |
| **Répétition du même événement** en général | dégressivité : `GetDiminishFactor(Event)` renvoie `1.0` puis décroît selon `Style_DiminishPerRepeat` (§14) tant que le **même** `E_StyleEvent` se répète d'affilée. Le compteur `SameSourceCount` se remet à 0 dès qu'un événement d'un autre type arrive, **ou** après `Style_ResetDiminishAfter` sans répétition (cf. ci-dessous). **Varier rapporte plus que répéter.** |
| **Farm de kills sur spawner infini** | aucun spawner infini au MVP (`03_SCOPE_LOCK`). Les ennemis scriptés portent `bCountsForScore = false` → pas de style non plus. |
| **Attendre au plafond** avant l'end trigger | inutile : le style est plafonné, et attendre coûte `ScoreTime` + `AvgSpeed` + déclenche `Idle`. |

**Dégressivité — implémentation exacte** (`GetDiminishFactor`, clés `07_TUNING §14`) :

```
FUNCTION GetDiminishFactor(Event : E_StyleEvent) → Float
    Now = World Time Seconds
    IF Now - LastEventOfType[Event] >= Style_ResetDiminishAfter :
        SameSourceCount[Event] = 0                       // retour au gain plein
    Factor = pow( Style_DiminishPerRepeat , SameSourceCount[Event] )
    SameSourceCount[Event] += 1
    LastEventOfType[Event]  = Now
    RETURN Factor
```

- `Style_DiminishPerRepeat` s'applique **en cascade** sur le **même** `E_StyleEvent` : ×1.0, ×0.7, ×0.49…
- `Style_ResetDiminishAfter` est le **délai sans répétition** au bout duquel le gain de cet event
  redevient plein. C'est le pendant de la dégressivité : sans lui, un event serait puni jusqu'à la fin du niveau.
- Le compteur est **par event**, jamais global : enchaîner headshot → wall slam → slide kill ne diminue rien.
  D'où les deux Maps `LastEventOfType` et `SameSourceCount` de §4.1.

> Décision : **pas de fenêtre de combo, pas de chaîne, pas de timer de combo affiché.**
> Un compteur de combo transformerait le style en système à mémoriser. Ici il n'y a qu'une jauge
> qui monte quand on fait des choses et qui descend quand on ne fait rien.

### 4.5 Feedback temps réel attendu (`WBP_StyleMeter`)

- Valeur numérique `x1.00` → `x5.00` (2 décimales), + barre de remplissage `CurrentMultiplier / Style_Max`.
- **Bind sur `OnStyleChanged`, jamais de Tick widget** (`06_CONVENTIONS §4.6`).
- Sur gain : punch scale + flash + `DisplayText` de la row `DT_StyleEvents` en texte flottant
  au-dessus de la jauge (ex. « WALL SLAM »).
- Sur perte / décroissance active : la barre passe en couleur d'alerte et « fuit » visiblement.
  Le joueur doit **voir** son style partir, c'est ce qui le pousse à relancer une action.
- Paliers visuels (couleur/intensité) sur `OnStyleTierChanged` — bornes de tier
  `Style_Tier_Thresholds` (§14).
- `BPC_StyleMeter` écrit `MPC_Global.StyleMultiplier01` : l'environnement et le post-process
  réagissent sans logique BP supplémentaire (`08_DATA_SCHEMAS §6`).

---

## 5. Collecte des données pendant le niveau

**Qui mesure quoi** (aucune logique de score dans `BP_PlayerCharacter` — interdit par `05_ARCHITECTURE §3`) :

| Donnée `S_LevelScore` | Source | Chemin |
|---|---|---|
| `LevelID` | `PDA_LevelData.LevelID` | `BP_LevelManager` → `GS_` |
| `TimeSeconds` | `GS_Overdrive` | horodatage start/end trigger |
| `Kills`, `Headshots`, `ScoreKills` | `BP_EnemyBase` → `BPI_ScoreEvent` → `BPC_ScoreManager` | |
| `TotalEnemies` | `PDA_LevelData.TotalEnemies` | lu au `BeginPlay` |
| `MaxSpeed`, `AverageSpeed` | `BPC_ScoreManager` (timer §3.4) | lit `BPC_MovementState` |
| `PeakStyleMultiplier`, `FinalStyleMultiplier` | `BPC_StyleMeter` → dispatcher | |
| `Deaths` | `BPC_Health.OnDeath` → `GS_.RegisterDeath()` | **inchangé** : compte les morts **du niveau courant** |
| `DamageTaken` | `BPC_Health.OnDamageTaken` | cumul brut |
| `ScoreSpeed`, `ScoreTime`, `TotalScore`, `Rank` | `BPC_ScoreManager.ComputeScore()` | calculés à la fin uniquement |

**Donnée de RUN, pas de niveau** — la nouveauté de la v2 :

| Donnée `S_RunState` | Source | Portée |
|---|---|---|
| **`LivesRemaining`** | `GI_Overdrive.ConsumeLife()`, appelé par `BPC_Health.OnDeath` | **toute la run**. Initialisée à `Run_MaxLives` (`07_TUNING §18`) par `StartNewRun()`, **jamais rechargée** entre deux niveaux, remise à `Run_MaxLives` uniquement à la run suivante |
| `TotalRunScore`, `LevelScores` | `BPC_ScoreManager.ComputeScore()` en fin de niveau | toute la run |

**Ne pas confondre `Deaths` et `LivesRemaining`** : `S_LevelScore.Deaths` est une statistique **de niveau**
(elle repart à 0 au niveau suivant et alimente `Score_DeathPenalty`) ; `S_RunState.LivesRemaining` est
l'**état de la run** et la seule condition de défaite. Tableau de portée complet : `05_ARCHITECTURE §4`.

**Stockage** : toutes les données vivantes sont sur le **`GS_Overdrive`** (composant `BPC_ScoreManager`),
pas sur le joueur — le joueur peut mourir et être respawné, le GameState non.
`LivesRemaining` fait exception : elle survit au changement de map, donc elle vit dans **`GI_Overdrive`**
(`05_ARCHITECTURE §4` : *tout ce qui survit vit dans `GI_Overdrive`*).
`PS_Overdrive` ne sert qu'au miroir d'affichage HUD.

**À la mort** (le flux complet fait autorité dans `05_ARCHITECTURE §4`, `11_ARBITRAGES D1` — on ne le duplique pas) :
```
BPC_Health.OnDeath (joueur)
  ├─ GI_Overdrive.ConsumeLife()  → S_RunState.LivesRemaining -= 1      ← donnée de RUN
  ├─ GS_.RegisterDeath()         → Deaths++, ScorePenalty += Score_DeathPenalty
  ├─ BPC_StyleMeter.Reset()      → Style_Loss_Death
  ├─ pause de l'échantillonnage de vitesse (§3.4)
  └─ le chrono continue           ← la mort coûte du temps

  puis, selon LivesRemaining :  > 0 → respawn au checkpoint     |     == 0 → RunFailed (§7.5)
```
Le branchement appartient à `GI_Overdrive`, jamais à `BPC_ScoreManager` : **le score ne décide de rien**,
il enregistre. Le score du niveau est collecté de la même façon dans les deux cas — c'est seulement
`ComputeScore()` qui ne sera jamais appelé si le niveau n'est pas terminé (§7.5).
**Au checkpoint** : `BP_Checkpoint` sauvegarde uniquement la **position de respawn** et l'index
de checkpoint. Il **ne fige ni ne restaure** kills, temps, vitesse moyenne ou style. Un checkpoint
n'est pas une sauvegarde de score — sinon mourir volontairement deviendrait une stratégie.

**À la fin du niveau** : `BPC_ScoreManager.ComputeScore()` remplit un `S_LevelScore` complet, l'ajoute
à `GI_Overdrive.RunState.LevelScores`, et incrémente `TotalRunScore`.

---

## 6. Calcul du rank

### 6.1 Source des seuils
`PDA_LevelData.RankThresholds` (`S_RankThresholds`). **Une seule source de vérité** :
`DT_RankThresholds` n'est pas créée (`08_DATA_SCHEMAS §4`).

```
FUNCTION ComputeRank(TotalScore, T : S_RankThresholds) → E_Rank
    IF TotalScore >= T.ScoreS : RETURN S
    IF TotalScore >= T.ScoreA : RETURN A
    IF TotalScore >= T.ScoreB : RETURN B
    IF TotalScore >= T.ScoreC : RETURN C
    RETURN D
```
Fonction pure dans `BPFL_Overdrive` (testable hors contexte, réutilisable par l'écran de résultats).
`E_Rank` est ordonné `D=0 … S=4` : comparer avec `>=` est légal (`08_DATA_SCHEMAS §1`).

**Couleurs des rangs** : `ArtDirection/PALETTE.md §6` fait autorité — tokens `OD_Rank_D` … `OD_Rank_S`,
**une couleur par rang**, jamais du magenta systématique (`11_ARBITRAGES D18`). Le `S` reprend la couleur
du joueur : c'est le rang « tu as joué comme le jeu le voulait ». Aucun HEX n'est dupliqué dans cette spec.
La lettre est tracée sur le panneau plein écran d'`OD_Navy_Deep` de `PALETTE.md §7` — sur le monde clair
de la v2, un écran de résultats clair serait illisible.

### 6.2 Méthode de calibration (par niveau, jamais globale)

1. Louis termine le niveau en **run propre mais pas parfait** : trajectoire correcte, quasi tous les
   ennemis, pas de mort, style honnête sans optimisation.
2. Le score obtenu = **seuil A**. On en déduit `ParScore = ScoreA / 0.80`.
3. On applique la grille de `07_TUNING §14` :
   `S = ParScore × 1.00` · `A = × 0.80` · `B = × 0.60` · `C = × 0.40` · `D` = en dessous.
4. `ParTimeSeconds` = temps de ce même run propre (pas le record).
5. `TargetKills` = nombre d'ennemis tuables du niveau ; `TargetStyle` et **`TargetAverageSpeed`** = valeurs
   d'un run S visé — elles ne servent **pas** au calcul du rank, uniquement à l'écran de comparaison (§7).
   `TargetMaxSpeed` est un simple repère d'affichage : il n'est comparé à rien (`11_ARBITRAGES D14`).
6. Test de contrôle obligatoire : un run **volontairement médiocre** doit sortir en D ou C,
   un run **excellent** en S. Si le S tombe au premier essai, `ParScore` est trop bas.

Un mode debug (`BPC_ScoreManager.bDebugPrintScoreBreakdown`, Category `Debug`) imprime les 4 termes
séparément en fin de niveau pour accélérer cette calibration.

---

## 7. Écran de résultats — `WBP_Results`

> Structure reprise de **GDD §42** (`LEVEL COMPLETE` / `S RANK` / `YOUR RUN`, et le principe
> « le joueur doit immédiatement comprendre pourquoi il n'a pas obtenu S »).
> Les champs affichés viennent de `S_LevelScore` et `S_RankThresholds` (`08_DATA_SCHEMAS §2`).

### 7.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│                        LEVEL COMPLETE                        │
│                      W1-01 · IGNITION                        │
│                                                              │
│                            ┌───┐                             │
│                            │ A │   ← lettre géante, 1 seule  │
│                            └───┘                             │
│                                                              │
│   TIME       01:58.6                            +     0      │
│   KILLS      10 / 12                            + 1 200      │
│   AVG SPEED  3 060                              + 1 530      │
│   ───────────────────────────────────────────────────────    │
│   STYLE                                          × 3.30      │
│   ═══════════════════════════════════════════════════════    │
│   TOTAL                                            9 009     │
│                                                              │
│   MAX SPEED  4 180                              (statistique)│
│                                                              │
│   ┌── S RANK vs YOUR RUN ────────────────────────────────┐   │
│   │              S RANK        YOU          DIFF         │   │
│   │  TIME        01:35.0     01:58.6      +23.6 s   ◀◀◀  │   │
│   │  KILLS         12          10          -2            │   │
│   │  AVG SPEED    3 400       3 060       -340           │   │
│   │  STYLE         4.00        3.30       -0.70          │   │
│   └──────────────────────────────────────────────────────┘   │
│                                                              │
│   ▶  23.6 s AU-DESSUS DU PAR TIME : TIME T'A RAPPORTÉ 0.     │
│      C'EST LÀ QUE TU AS PERDU TON RANG.                      │
│                                                              │
│              [ CONTINUE ]        [ RESTART ]                 │
└──────────────────────────────────────────────────────────────┘
```

**Vérification de la maquette** — tous les chiffres se recalculent avec §3.1 et `07_TUNING §13 / §14` :

```
Niveau      W1-01 IGNITION : 12 ennemis, tous Grunts → ScoreBase = 100 (07_TUNING §13)
Seuils      ParScore = 11 000 → S 11 000 · A 8 800 · B 6 600 · C 4 400   (grille §6.2)
            ParTimeSeconds 95.0 s · TargetKills 12 · TargetAverageSpeed 3 400 · TargetStyle 4.00

ScoreTime   Time 118.6 s > ParTime 95.0 s        → max(0, (95.0 - 118.6) × 100) =     0   (§3.3)
ScoreKills  6 kills simples  6 × 100                                        =   600
            4 headshots      4 × 100 × (1 + Kill_HeadshotBonus 50 %)        =   600
                                                                    total   = 1 200
ScoreSpeed  round(3 060 / 10) × 5 = 306 × 5                                 = 1 530
Base        1 200 + 1 530 + 0                                               = 2 730
TOTAL       2 730 × 3.30                                                    = 9 009
Rank        9 009 ≥ ScoreA (8 800) et < ScoreS (11 000)                     =     A
```

**Ce que la maquette démontre volontairement** : au-dessus du par time, `TIME` rapporte **zéro**, pas des
points négatifs (§3.3). C'est le cas le plus fréquent d'un run raté, et c'est celui qui doit être le plus
lisible. `MAX SPEED` est affichée comme **statistique de vantardise uniquement** : elle n'entre ni dans le
score ni dans la comparaison au S Rank (`11_ARBITRAGES D14`).

Contraintes de lisibilité : **une seule lettre de rank**, très grande, très haut. Le total n'est pas
la star — la lettre l'est. Le tableau de comparaison est le **second** point de fixation du regard.

### 7.2 Ordre d'apparition animé

Séquence pilotée par un `Timeline`/`Sequence` de widget, cadence `Results_StepDelay` (§14).
Chaque étape est **skippable** : appuyer sur n'importe quelle
touche saute directement à l'état final (règle non négociable pour un jeu de restart rapide).

```
1. Fond + titre du niveau                         (fade)
2. Ligne TIME       — valeur puis points qui comptent (count-up)
3. Ligne KILLS      — idem
4. Ligne AVG SPEED  — idem
5. Ligne STYLE      — le × s'anime en scale, punch
6. TOTAL            — count-up rapide de 0 au total
7. LETTRE DE RANK   — impact, shake, SFX dédié            ← le pic émotionnel
8. Tableau S RANK vs YOUR RUN — apparition des 4 lignes
9. Surlignage de la ligne coupable + phrase verdict        ← le message à retenir
10. Boutons CONTINUE / RESTART
```
La lettre arrive **après** les chiffres : le joueur additionne mentalement, puis reçoit le verdict.
Le surlignage arrive en **dernier** : c'est la dernière chose lue avant de décider de relancer.

### 7.3 Désignation de la statistique coupable — **le cœur de l'écran**

Objectif : ne pas laisser le joueur faire la soustraction. On lui dit **quelle composante**, et
**combien il lui manquait**.

Fonction pure de `BPFL_Overdrive`. `E_ScoreComponent` est déclaré dans **`08_DATA_SCHEMAS §1`**
(`Kills` · `Speed` · `Time` · `Style`) — il n'est pas redéclaré ici.

```
FUNCTION GetLimitingStat(S : S_LevelScore, T : S_RankThresholds) → (E_ScoreComponent, Text)

    IF S.Rank == E_Rank::S : RETURN (None, "PERFECT RUN")

    // Écart RELATIF à la cible du S Rank, composante par composante.
    // On compare des écarts relatifs et non des points : c'est le seul moyen de mettre
    // une seconde, un kill, un uu/s et un « × » sur la même échelle, et ça reste valable
    // quel que soit le niveau et quel que soit ParScore.
    Deficit_Time  = max(0, S.TimeSeconds          - T.ParTimeSeconds)      / T.ParTimeSeconds
    Deficit_Kills = max(0, T.TargetKills          - S.Kills)               / T.TargetKills
    Deficit_Style = max(0, T.TargetStyle          - S.FinalStyleMultiplier)/ T.TargetStyle
    Deficit_Speed = max(0, T.TargetAverageSpeed   - S.AverageSpeed)        / T.TargetAverageSpeed

    Winner = argmax( Deficit[] )
             // égalité à moins de Results_TieTolerance près (§14) →
             // ordre de départage TIME > KILLS > STYLE > SPEED   (11_ARBITRAGES D13)

    // Verdict formulé en unité JOUEUR (secondes, kills, ×, uu/s) — jamais en points
    RETURN (Winner, FormatVerdict(Winner, DeltaEnUnitéJoueur))
```

Application à la maquette §7.1 :
`TIME 23.6 / 95.0 = 24.8 %` · `KILLS 2 / 12 = 16.7 %` · `STYLE 0.70 / 4.00 = 17.5 %` ·
`SPEED 340 / 3 400 = 10.0 %` → **TIME**, avec plus de 7 points d'écart sur le second : aucun départage
nécessaire.

Règles de présentation :
- La **vitesse comparée au S Rank est `AverageSpeed` vs `T.TargetAverageSpeed`** (`11_ARBITRAGES D14`) :
  c'est elle qui alimente `ScoreSpeed`. `MaxSpeed` / `TargetMaxSpeed` sont affichées comme statistiques,
  jamais comparées au score.
- Le verdict est exprimé dans l'**unité que le joueur contrôle** (« 23.6 s au-dessus du par time »,
  « 2 ennemis en moins », « vitesse moyenne 340 sous la cible »), **jamais** en points bruts.
- La ligne correspondante du tableau est surlignée (`◀◀◀` + couleur d'accent + léger scale).
- **Une seule** ligne est surlignée. Si deux composantes sont à moins de `Results_TieTolerance` (§14)
  l'une de l'autre, on prend celle de plus haute priorité : **`TIME > KILLS > STYLE > SPEED`**
  (`11_ARBITRAGES D13`).
- Rank S : pas de surlignage, message `PERFECT RUN`, le tableau affiche des `=`.
- Rank D avec 0 kill et temps > par : le verdict pointe TIME et le tableau reste affiché entier
  (pas de cas dégénéré masqué).

### 7.4 Entrées
`CONTINUE` → ouvre `WBP_LootChest`. `RESTART` → relance le niveau, run et upgrades conservés.
`RESTART` doit être atteignable en une touche sans navigation.

### 7.5 Que devient le score quand la run échoue — `WBP_RunFailed`

Quand `LivesRemaining` tombe à 0, `E_GameState` passe à **`RunFailed`** (`11_ARBITRAGES D1`) et
`WBP_RunFailed` remplace la boucle habituelle. Ce que devient le score :

| Question | Réponse |
|---|---|
| Le score total de la run est-il conservé ? | **Oui — pour l'affichage de fin, et uniquement pour lui.** `GI_Overdrive.RunState.TotalRunScore` et le tableau `LevelScores` sont **intacts** au moment où l'écran s'ouvre : ils ont été remplis niveau après niveau. `WBP_RunFailed` les lit et affiche le récap (niveau atteint, score total, upgrades collectés — `05_ARCHITECTURE §2`). |
| Le niveau où le joueur est mort compte-t-il ? | **Non.** `ComputeScore()` n'est appelé que par `BP_LevelEndTrigger` (§8). Un niveau non terminé n'a **ni `S_LevelScore`, ni rank, ni coffre**. Le récap affiche donc *N−1* niveaux marqués et le niveau courant comme « atteint ». |
| Y a-t-il un rank de run ? | **Non.** Le rank est une notion **de niveau** (§6). Aucun rank global, aucune lettre agrégée : ce serait une 5ᵉ statistique à comprendre, et une porte ouverte à la méta-progression. |
| Le score est-il sauvegardé ? | **Non. Rien n'est écrit sur disque.** Aucune méta-progression au MVP (§1, `SPEC_LOOT_UPGRADES §8`). Pas de `SaveGame`, pas de meilleur score, pas de leaderboard (rangés au backlog, `03_SCOPE_LOCK §4`). |
| Que reste-t-il après l'écran ? | **Rien.** Retour au menu, puis `GI_Overdrive.StartNewRun()` au prochain *PLAY* : `TotalRunScore` = 0, `LevelScores` vide, `ActiveUpgrades` vide, `LivesRemaining` = `Run_MaxLives`. Le score affiché n'est qu'un **au revoir**, jamais une monnaie. |

Durée d'affichage : `RunFailed_ScreenDuration` (`07_TUNING §18`), **skippable** — même exigence que
l'écran de résultats (§7.2) : rien ne doit retarder la relance.

> **Ton de l'écran.** `WBP_RunFailed` dit *« voilà jusqu'où tu es allé »*, pas *« tu as perdu »*.
> Le chiffre qui compte pour le joueur est **le niveau atteint**, pas le total de points : c'est lui
> qu'il voudra battre à la run suivante. Le score total est affiché en second.

---

## 8. Flux technique

```
BP_LevelEndTrigger  (overlap joueur, une seule fois — bTriggered garde)
   │
   ├─▶ BP_LevelManager.EndLevel()
   │        ├─ GS_.SetGameState(LevelComplete)        // stoppe timers de score et de style
   │        └─ désactive l'input gameplay (PC_)
   │
   ├─▶ GS_.BPC_ScoreManager.ComputeScore()
   │        ├─ TimeSeconds = Now - LevelStartTime
   │        ├─ lit BPC_StyleMeter (Final + Peak)
   │        ├─ applique la formule §3
   │        ├─ BPFL_Overdrive.ComputeRank(TotalScore, PDA_LevelData.RankThresholds)
   │        ├─ remplit S_LevelScore
   │        ├─ GI_Overdrive.RunState.LevelScores.Add(...)  + TotalRunScore += ...
   │        └─ Dispatch OnRankComputed(S_LevelScore)
   │
   ├─▶ PC_Overdrive  (bind OnRankComputed)
   │        ├─ Create Widget WBP_Results
   │        ├─ WBP_Results.Setup(S_LevelScore, S_RankThresholds)
   │        └─ SetInputModeUIOnly + curseur
   │
   ▼
WBP_Results  ── OnContinueClicked ──▶  BP_LootChest.Roll(S_LevelScore.Rank)
                                              └─▶ WBP_LootChest   (SPEC_LOOT_UPGRADES.md §7)
```

- `BPC_ScoreManager` **ne crée aucun widget** : il dispatch. Le `PC_` possède l'UI (`05_ARCHITECTURE §2`).
- `WBP_Results` **ne calcule aucun score** : il reçoit un `S_LevelScore` figé et un `S_RankThresholds`,
  et ne fait que de la mise en forme + `GetLimitingStat()` (fonction pure de `BPFL_Overdrive`).
- Aucun `Cast To BP_PlayerCharacter` dans cette chaîne.

---

## 9. Anti-exploits

| # | Exploit possible | Parade | Où |
|---|---|---|---|
| 1 | Farmer le style puis traîner pour finir avec un multiplicateur max | Le style **décroît** (`Style_DecayDelay` + `Style_DecayPerSec`) et seul `FinalStyleMultiplier` compte | §3.2, §4.3 |
| 2 | Spam de dash sur place | Gain conditionné à un déplacement réel + charges/cooldown | §4.4 |
| 3 | Wall ride en boucle sur le même mur | Contrôle `LastWallRideSurface` + cooldown same-wall | §4.4 |
| 4 | Répéter à l'infini le même type d'événement | Dégressivité `Style_DiminishPerRepeat` | §4.4 |
| 5 | Tuer les ennemis d'un spawn scripté/décoratif | `S_EnemySpawnEntry.bCountsForScore = false` → ni score ni style | §3.2 |
| 6 | Mourir volontairement pour restaurer HP/position sans coût | `Deaths++`, `Score_DeathPenalty`, reset du style, chrono qui tourne — **et `LivesRemaining -= 1`** : la mort volontaire coûte désormais une vie sur `Run_MaxLives`, c'est la parade la plus dissuasive du tableau | §3.3, §5 |
| 7 | Camper une zone sûre pour laisser tomber la difficulté | `ScoreTime` → 0, `AvgSpeed` chute, `Style_Loss_Idle` | §3.3 |
| 8 | Tomber en boucle pour gonfler `AvgSpeed` (vitesse verticale) | La moyenne n'utilise que la vitesse **horizontale** | §3.4 |
| 9 | Rester sur l'écran de fin pour diluer/gonfler la moyenne | Timer d'échantillonnage mis en pause hors `Gameplay` | §3.4 |
| 10 | Franchir plusieurs fois l'end trigger | Garde `bTriggered` + désarmement du trigger | §8 |
| 11 | Se faire toucher volontairement pour un i-frame gratuit | `Style_Loss_TakeDamage` est le malus le plus lourd des événements ponctuels | §4.2 |
| 12 | Pause-abuse (mettre en pause pour lire l'arène) | Le chrono de niveau **et** l'échantillonnage sont suspendus en `Paused` → aucun gain de score, seulement du confort | §3.4 |
| 13 | Score négatif exploité par overflow | Clamps explicites : `ScoreTime ≥ 0`, `TotalScore ≥ 0`, style borné | §3.3 |
| 14 | Skip de géométrie hors-map | **Autorisé et récompensé** si le end trigger est atteint — c'est un jeu de vitesse. Les sorties de map non voulues sont bloquées par des blocking volumes, pas par le score | level design |

---

## 10. Checklist de validation manuelle (Louis)

**Score & formule**
- [ ] Finir un niveau lentement, sans tuer : rank **D**, `ScoreTime = 0`, aucun crash.
- [ ] Finir un niveau au-dessus du par time : `ScoreTime` affiché **0**, pas de valeur négative.
- [ ] Tuer un ennemi en headshot puis un au wall slam : vérifier le bonus dans le debug breakdown.
- [ ] Vérifier que `Kills` n'augmente pas sur un ennemi `bCountsForScore = false`.

**Vitesse**
- [ ] Rester immobile 10 s : la moyenne affichée **baisse** visiblement.
- [ ] Chuter d'une grande hauteur : `AverageSpeed` **n'augmente pas** (composante horizontale).
- [ ] Laisser l'écran de résultats ouvert 30 s puis relire `AverageSpeed` : **inchangée**.

**Style**
- [ ] Ne rien faire pendant `Style_DecayDelay` : la jauge se met à fuir, visiblement, sur le HUD.
- [ ] Spammer le dash sur place : le multiplicateur **ne monte pas** de façon significative.
- [ ] Faire 5 wall rides d'affilée sur le **même** mur : gain nul ou fortement dégressif.
- [ ] Alterner kill / wall ride / dash : le multiplicateur monte **plus vite** que la répétition.
- [ ] Se faire toucher au style max : chute nette et lisible à l'écran.
- [ ] Mourir : le style revient à `Style_Start`, pas à autre chose.
- [ ] **Chaleur (§4.2b)** — vider des tirs dans un mur jusqu'à dépasser `Heat_WarningThreshold` :
      le style se met à **fuir en continu**, et le HUD affiche le coût exact. *(Au J9 la perte est
      **affichée mais pas appliquée** : le câblage arrive au J18 — vérifier alors que le
      multiplicateur baisse vraiment.)*
- [ ] **Chaleur** — reprendre de la vitesse au-dessus de `Heat_CoolSpeedThreshold` : la fuite
      s'arrête **et** `Style_Gain_HighSpeedSustain` se met à créditer. **Les deux au même seuil.**
- [ ] **Chaleur** — un headshot fait redescendre la chaleur assez pour couper la perte.
- [ ] **Chaleur** — chaud **et** immobile : les deux pertes se cumulent, sans jamais passer sous
      `Style_Start`.

**Rank & résultats**
- [ ] Run propre = **A**. Si c'est S du premier coup, `ParScore` est mal calibré.
- [ ] Les 4 lignes apparaissent dans l'ordre §7.2, la lettre **après** les chiffres.
- [ ] Appuyer sur une touche pendant l'animation : tout apparaît instantanément.
- [ ] Le tableau S RANK vs YOUR RUN affiche 4 diffs cohérentes avec le run.
- [ ] La ligne surlignée correspond bien à la composante la plus déficitaire — vérifier sur
      3 runs volontairement biaisés (un lent, un sans kill, un sans style).
- [ ] Rank S : message `PERFECT RUN`, aucune ligne surlignée.
- [ ] `RESTART` relance en moins d'une seconde perçue, upgrades conservés.
- [ ] La lettre de rank porte bien la couleur `OD_Rank_*` de son rang (`PALETTE.md §6`), lisible sur le
      panneau foncé.

**Vies & fin de run**
- [ ] Mourir : `Deaths++`, `Score_DeathPenalty` appliqué **et** le compteur de vies décrémente.
- [ ] Passer au niveau suivant : `Deaths` repart à 0, `LivesRemaining` **ne remonte pas**.
- [ ] Épuiser les vies : `WBP_RunFailed` affiche le **niveau atteint**, le **score total de la run**
      et les upgrades collectés — le niveau où l'on est mort n'a **ni score ni rank** (§7.5).
- [ ] Relancer une run après un échec : score total à 0, aucune upgrade, vies à `Run_MaxLives`.
- [ ] Fermer et rouvrir le jeu : **aucun score conservé** (pas de save).

**Ressenti (R8)**
- [ ] En lisant l'écran, la phrase « je sais quoi améliorer » vient **avant** 4 secondes.
- [ ] L'envie de relancer est présente **avant** d'avoir cliqué sur CONTINUE.
- [ ] Aucun moment où le joueur se demande d'où sort un chiffre.

---

## 11. Où vivent les valeurs

Toutes les clés citées dans ce document (`Score_DeathPenalty`, `Score_SpeedSampleRate`, `Score_StyleTickRate`,
`Kill_HeadshotBonus`, `Kill_WallSlamBonus`, `Style_*` — **`Style_Loss_Heat` compris** —,
`Results_StepDelay`, `Results_TieTolerance`…) sont définies dans **`Docs/07_TUNING.md §14`**.
Les clés de **chaleur** citées en §4.2b (`Heat_WarningThreshold`, `Heat_CoolSpeedThreshold`,
`Heat_CoolPerHeadshot`, `Heat_CoolRateAtSpeed`, `Heat_TickInterval`) sont dans **`§11`**.
Les clés de **run et de vies** (`Run_MaxLives`,
`Run_LevelCount`, `Run_LivesRefillOnBoss`, `RunFailed_ScreenDuration`) sont dans **`§18`**.
Aucune n'est orpheline, aucune n'est à créer.

> Règle R3 : la valeur vit dans `07_TUNING.md`, jamais dans une spec. On y renvoie par nom de clé.
> Décisions d'arbitrage applicables à ce système : **`Docs/11_ARBITRAGES.md` D1, D13, D14, D16, D18, D31, D58**.
> Couleurs (rangs, panneaux) : **`Docs/ArtDirection/PALETTE.md §6 et §7`**, sans exception.
