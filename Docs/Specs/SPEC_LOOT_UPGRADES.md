# SPEC — LOOT & UPGRADES

> Coffres de fin de niveau, tirage, catalogue, application des upgrades **temporaires**.
> **Blueprint only.** Aucune valeur numérique n'est écrite ici : tout renvoie à `Docs/07_TUNING.md §15`
> par nom de ligne. Structs/Enums : `Docs/08_DATA_SCHEMAS.md`. Architecture : `Docs/05_ARCHITECTURE.md`.
> Amont : `Docs/Specs/SPEC_SCORE_RANK.md`. Couleurs : `Docs/ArtDirection/PALETTE.md §5` (raretés) et `§7` (UI).
> Portée des données : `Docs/05_ARCHITECTURE.md §4` — **c'est lui qui fait autorité** sur ce qui survit à quoi.
> Intention d'origine : `Docs/02_GDD.md §43–§52`.
> Décisions tranchées : `Docs/11_ARBITRAGES.md` (**D1** portée d'une run, **D17** couleurs de rareté,
> **D26** nom de l'upgrade `MaxSpeed`, **D29** 7 upgrades max, **D31** vies).

---

## 1. Objectif du loot

Le coffre est la **récompense immédiate** du rank. Il répond à « j'ai bien joué → il se passe
quelque chose tout de suite », et il installe la boucle : mieux jouer → meilleur coffre → mieux jouer.

### Les trois règles qui gouvernent tout ce document

| # | Règle | Traduction technique |
|---|---|---|
| **1** | **Les upgrades aident, elles ne remplacent jamais le skill.** | Aucune upgrade ne supprime une exigence d'exécution. Elles élargissent une marge, elles n'automatisent rien. |
| **2** | **Le jeu demande « es-tu assez bon ? », pas « as-tu assez de stats ? »** | Cumul max **+100 % par stat** sur une run (`07_TUNING §15`, garde-fou GDD §49). Pas de scaling exponentiel, pas de Legendary. |
| **3** | **Tout meurt à la fin de la run.** | Pas de méta-progression au MVP. Rien n'est sauvegardé sur disque. |

**Anti-objectif** : le joueur ne doit jamais penser « je vais grinder des niveaux faciles pour
farmer des upgrades ». Le loot n'est pas une économie, c'est un **feedback**.

Raretés : `E_Rarity` = `Common` · `Rare` · `Epic` (GDD §45). **Pas de Legendary** — trois paliers suffisent à
faire ressentir la différence entre un coffre D et un coffre S.

**Couleurs de rareté** — source unique et exclusive : **`Docs/ArtDirection/PALETTE.md §5`**
(`11_ARBITRAGES D17`). Common = gris-bleu neutre, volontairement terne · Rare = bleu franc ·
Epic = violet saturé. **Aucun HEX n'est dupliqué ici** : la palette fait autorité, on y renvoie.

**Aucune rareté n'emploie une couleur de gameplay** (`11_ARBITRAGES D3`) : ni le magenta du joueur,
ni le rouge des surfaces de traversée, ni l'orange des ennemis. Le bleu de `Rare` et le violet d'`Epic`
sont choisis parce qu'ils sont **absents du décor** — et le violet de rareté est volontairement **plus
intense** que le `OD_Purple_Primary` de la signalétique, pour qu'on ne confonde pas une carte avec un
panneau directionnel. Aucun autre code couleur n'est autorisé pour la rareté, ni dans le coffre, ni sur
les cartes, ni au HUD.

> Le cyan de la v1 n'existe plus dans la palette : toute doc qui oppose encore `Rare` au cyan est caduque.
> Rappel de contexte v2 : les écrans de loot sont posés sur un panneau plein écran `OD_Navy_Deep`
> (`PALETTE.md §7`) — le monde est clair, une UI claire disparaîtrait.

---

## 2. Coffres

### 2.1 Un coffre par rank

| Rank obtenu | Table | Common / Rare / Epic | Nb de choix |
|---|---|---|---|
| D | `DT_LootTable_D` | cf. `07_TUNING §15` ligne `D` | cf. §15 |
| C | `DT_LootTable_C` | ligne `C` | §15 |
| B | `DT_LootTable_B` | ligne `B` | §15 |
| A | `DT_LootTable_A` | ligne `A` | §15 |
| S | `DT_LootTable_S` | ligne `S` | §15 |

Le joueur choisit **1 upgrade parmi N propositions**. N est défini par la colonne « Nb de choix »
de `07_TUNING §15` — il augmente avec le rank. C'est le vrai levier de récompense : un coffre S ne
donne pas *plus* d'upgrades, il donne **plus de choix** (donc plus de contrôle sur sa build).

> Décision : **une seule upgrade gagnée par niveau, quel que soit le rank.** Un coffre S qui
> donnerait 3 upgrades ferait exploser la courbe de puissance sur 6 niveaux. Le rank module la
> *qualité* et le *choix*, jamais la *quantité*.

### 2.2 Row Struct

`S_LootTableRow` (`08_DATA_SCHEMAS §4`) :
`UpgradeDefinition` (`PDA_UpgradeDefinition`, soft) · `Rarity` (`E_Rarity`) · `Weight` (Float) ·
`bUniquePerRun` (Bool).

Une même upgrade apparaît **une fois par rareté qu'elle propose** (une row `Common`, une row `Rare`,
une row `Epic`), pointant vers trois `PDA_UpgradeDefinition` distincts (`DA_Upg_MaxSpeed_Common`, …).

### 2.3 `BP_LootChest` — un objet logique, PAS un actor de niveau

> **Décision : le coffre est un écran UI plein écran (`WBP_LootChest`), enchaîné après `WBP_Results`.**
> Il n'existe **aucun actor de coffre dans les niveaux**, et donc **aucune « salle de fin »** à construire :
> `SPEC_LEVELDESIGN §4.6` termine chaque niveau par une Final Run et un `BP_LevelEndTrigger`, rien d'autre.

Pourquoi : une salle de fin obligatoire sur 8 niveaux, c'est 8 espaces à construire, à éclairer et à tester,
un arrêt net après la Final Run (contraire au pilier « rien n'arrête le joueur ») et une interaction de plus
entre deux runs. Le coffre est un **moment d'UI**, pas un lieu.

`BP_LootChest` reste un **objet logique** (`BPC_UpgradeManager` le porte, aucun `Actor` placé) :

| Élément | Détail |
|---|---|
| Rôle | héberge `Roll()` (§3) et le cache par `LevelID` (§3.4). Zéro composant de rendu, zéro collision |
| Variables | `ChestRank : E_Rank` (défini au runtime) · `RollResult : S_LootRollResult` · `bOpened : Bool` |
| Dispatchers | `OnChestOpened(S_LootRollResult)` |

**Mise en scène** — entièrement dans `WBP_LootChest` (durées `Loot_*`, `07_TUNING §15`, aucune valeur ici) :
```
1. VERDICT      OnRankComputed → le tirage est fait, le bandeau de rank de l'écran de résultats
                porte déjà la couleur du rank obtenu (D..S : la couleur EST l'information)
2. OUVERTURE    déclenchée par le bouton CONTINUE de WBP_Results (pas par une interaction
                séparée : une action de moins entre deux runs)
                → Loot_ChestOpenDuration : flash plein écran + SFX + léger shake d'UI
3. RÉVÉLATION   les N cartes d'upgrade apparaissent en séquence (Loot_CardRevealStagger),
                le halo de fond prend la couleur de la RARETÉ la plus haute tirée (§1)
4. CHOIX        WBP_LootChest prend la main (§7)
5. FERMETURE    Loot_CardFlyToHUDDuration : la carte choisie s'envole vers le HUD → OpenLevel suivant
```

Le tirage (`Roll`) est effectué **dès `OnRankComputed`**, avant l'étape 2, pour que la mise en scène
puisse déjà refléter la rareté maximale obtenue.

**Cas boss / dernier niveau** : `PDA_LevelData.bIsBossLevel` → le coffre existe quand même
(le boss 01 est suivi du monde 2). Après le boss 02, `GI_Overdrive.EndRun(Success)` : pas de coffre.

---

## 3. Algorithme de tirage

Implémenté dans `BP_LootChest.Roll(Rank) → S_LootRollResult`.
Découpé en fonctions courtes (`06_CONVENTIONS §4.2`), zéro Tick.

### 3.1 Pseudo-code

```
FUNCTION Roll(ChestRank : E_Rank) → S_LootRollResult

    Table       = GetLootTableForRank(ChestRank)          // DT_LootTable_<Rank>
    RarityOdds  = GetRarityOddsForRank(ChestRank)         // 07_TUNING §15, table des drop rates
    NumChoices  = GetNumChoicesForRank(ChestRank)         // 07_TUNING §15, colonne "Nb de choix"
    Result.ChestRank = ChestRank
    Result.Offers.Empty()

    // Pré-filtrage : une seule passe, on construit le pool légal
    Pool = []
    FOR EACH Row IN Table.GetAllRows() :
        Def = Row.UpgradeDefinition.LoadSynchronous()
        IF IsUpgradeEligible(Def, Row) : Pool.Add(Row)

    FOR i = 0 TO NumChoices - 1 :

        // ---- Étape 1 : tirage de la RARETÉ ----
        Rarity = RollRarity(RarityOdds)                   // roue pondérée Common/Rare/Epic

        // ---- Étape 2 : tirage PONDÉRÉ dans cette rareté ----
        Candidates = Pool.Filter(Rarity == Rarity)
                         .Filter(NOT AlreadyOffered(Result.Offers))     // exclusion des doublons
        IF Candidates.IsEmpty() :
            Candidates = ApplyRarityFallback(Pool, Rarity, Result)      // Étape 4
            IF Candidates.IsEmpty() : BREAK                             // pool épuisé, on sort

        Chosen = WeightedPick(Candidates)                 // Σ Weight, random dans [0, Σ), cumul
        Result.Offers.Add(BuildInstance(Chosen))

    IF Result.Offers.IsEmpty() : Result.Offers.Add(GetSafetyFallbackUpgrade())   // §3.4
    RETURN Result
```

```
FUNCTION IsUpgradeEligible(Def, Row) → Bool
    // 1. déjà au max stack ?
    IF Def.MaxStacks > 0 AND UpgradeManager.GetStackCount(Def.UpgradeID) >= Def.MaxStacks
        RETURN false
    // 2. unique par run et déjà pris ? (modificateurs de gameplay)
    IF Row.bUniquePerRun AND UpgradeManager.HasUpgrade(Def.UpgradeID)
        RETURN false
    // 3. plafond de cumul par STAT atteint ? (garde-fou +100 %, §6)
    IF UpgradeManager.WouldExceedStatCap(Def.Stat, Def.Value, Def.bIsPercentage)
        RETURN false
    RETURN true
```

```
FUNCTION WeightedPick(Candidates) → Row
    Total = Σ Candidates[i].Weight
    R     = RandomFloatInRange(0, Total)      // stream §3.3
    Acc   = 0
    FOR EACH C IN Candidates :
        Acc += C.Weight
        IF R <= Acc : RETURN C
    RETURN Candidates.Last()                  // sécurité arrondi flottant
```

### 3.2 Exclusions — ordre exact

| Ordre | Exclusion | Raison |
|---|---|---|
| 1 | `MaxStacks` atteint | ne jamais proposer une upgrade qui ne ferait rien |
| 2 | `bUniquePerRun` déjà possédé | les modificateurs de gameplay ne se stackent pas |
| 3 | Plafond de cumul par stat (+100 %) | garde-fou d'équilibrage (§6) |
| 4 | Doublon **dans la même offre** | ne jamais afficher deux fois la même carte côte à côte |

Note : deux **raretés différentes** de la même stat (ex. `+MaxSpeed Common` et `+MaxSpeed Rare`) sont
considérées comme un doublon au sens de l'étape 4 — on compare l'**identité fonctionnelle**
(`Stat` + `Modifier`), pas l'`UpgradeID`. Proposer le même bonus en deux tailles est un faux choix.

### 3.3 Fallbacks

| Situation | Fallback |
|---|---|
| Aucune entrée dans la rareté tirée | **Descendre** d'un cran : `Epic → Rare → Common`. Ne jamais monter (on n'offre pas un Epic par accident dans un coffre D). |
| Aucune entrée dans **aucune** rareté | Réduire l'offre : proposer moins de N cartes. Une offre de 2 au lieu de 3 est acceptable. |
| Pool totalement vide (fin de run, tout maxé) | `GetSafetyFallbackUpgrade()` : une upgrade « soupape » à `MaxStacks = 0` (illimité) désignée dans la table — au MVP, `Upg_MaxHealth_Common`. Elle ne casse rien et évite un coffre vide. |
| `DT_LootTable_<Rank>` absente ou vide | Log d'erreur en éditeur + repli sur `DT_LootTable_C`. Ne jamais bloquer le flux de run. |

Un coffre **ne peut jamais être vide** : un coffre vide en fin de niveau est un bug de ressenti.

### 3.4 Seed — décision

> **Décision : le tirage est aléatoire NON déterministe (stream par défaut du moteur), et le
> résultat de chaque coffre est mémorisé pour la durée du niveau.**

Justification :

| Option | Pour | Contre | Verdict |
|---|---|---|---|
| Seed déterministe par run (`GI_Overdrive.Seed`) | reproductible pour le debug, runs comparables | **Le restart d'un niveau redonnerait exactement les mêmes offres** → le joueur peut re-rouler la même carte à l'infini, ou pire, savoir à l'avance ce qu'il aura. Tue l'effet de surprise du coffre, le seul moment « slot machine » du jeu. | ❌ |
| Aléatoire pur, re-tiré à chaque affichage | surprise maximale | le joueur peut **re-roll par restart** jusqu'à obtenir la carte voulue → farm dégénéré | ❌ |
| **Aléatoire, mais résultat mis en cache par `LevelID`** | surprise préservée, pas de re-roll abusif par restart | légèrement plus de state à gérer | ✅ **retenu** |

Implémentation : `BPC_UpgradeManager.CachedRolls : Map<Name(LevelID), S_LootRollResult>`.
`Roll()` consulte le cache d'abord. Le cache est vidé par `StartNewRun()`.
Conséquence : **redémarrer un niveau pour améliorer son rank change le coffre (meilleure table),
mais ne permet pas de re-roll la même table indéfiniment.**

Un `GI_Overdrive.DebugSeed` (Category `Debug`, `Instance Editable`) permet de forcer un stream
déterministe pour les tests — **jamais actif en build**.

---

## 4. Catalogue complet des upgrades

Toutes les valeurs sont dans **`07_TUNING §15`, tableau « Valeurs d'upgrade par rareté »**, ligne
indiquée en colonne « Ligne §15 ». Aucune valeur n'est dupliquée ici.
`UpgradeID` = `Upg_<Nom>_<Rareté>`. Asset = `DA_Upg_<Nom>_<Rareté>` (`PDA_UpgradeDefinition`).

> **Les noms affichés de ce tableau font foi.** En particulier, l'upgrade `MaxSpeed` s'appelle
> **`OVERDRIVE`** : c'est ce nom qui apparaît sur la carte, dans le bandeau `ACTIVE` et au HUD.
> `SPEC_UI_HUD` s'aligne sur ce catalogue, jamais l'inverse.

### 4.1 Upgrades de stats

| UpgradeID (base) | Nom affiché | Description joueur | Raretés | `E_UpgradeStat` | Ligne §15 | Max stacks | Risque de déséquilibre |
|---|---|---|---|---|---|---|---|
| `Upg_MaxHealth` | **VITALITY** | « +PV maximum. Tu encaisses une erreur de plus. » | C / R / E | `MaxHealth` | `+MaxHealth` | 0 (illimité) | Faible. Sert de fallback de sécurité (§3.3). |
| `Upg_LaserDamage` | **FOCUSED BEAM** | « Le laser fait plus mal. Moins de tirs par ennemi. » | C / R / E | `LaserDamage` | `+LaserDamage` | cap +100 % | ⚠️ **Moyen** — au-delà du one-shot Grunt, le combat perd son rythme. Surveiller le seuil de one-shot sur `DA_Enemy_Grunt`. |
| `Upg_MeleeDamage` | **HEAVY HANDS** | « Le poing frappe plus fort. » | C / R / E | `MeleeDamage` | `+MeleeDamage` | cap +100 % | ⚠️ **Moyen** — cumulé avec `Impact` et le wall slam, peut trivialiser le Tank. |
| `Upg_MaxSpeed` | **OVERDRIVE** | « Ta vitesse maximale monte. » | C / R / E | `MaxSpeed` | `+MaxSpeed (hard cap)` | cap +100 % | 🔴 **Élevé** — affecte le level design (gaps, largeurs de couloir). Voir §6. |
| `Upg_Acceleration` | **KICKSTART** | « Tu atteins ta vitesse de pointe plus vite. » | C / R / E | `Acceleration` | `+Acceleration` | cap +100 % | Faible. Améliore le confort, pas le plafond. |
| `Upg_SpeedRetention` | **FLOW** | « Tu perds moins de vitesse dans les virages et les impacts. » | C / R / E | `SpeedRetention` | `+SpeedRetention` | cap +100 % | ⚠️ **Moyen** — c'est la stat la plus forte du jeu ; d'où les valeurs volontairement petites en §15. Ne jamais autoriser une rétention effective de 100 %. |
| `Upg_DashRecharge` | **RECHARGE** | « Ton dash revient plus vite. » | C / R / E | `DashCooldown` | `+DashRecharge (cooldown)` | cap `StatCapDown` (§15) | 🔴 **Élevé** — un dash quasi permanent supprime la lecture de l'espace. Cap dur obligatoire. |
| `Upg_DashCharges` | **TWIN CORE** | « +1 charge de dash. » | **E uniquement** | `DashCharges` | `+DashCharges` | 1 | 🔴 **Élevé** — la plus grosse upgrade du jeu. Epic only, 1 stack, jamais plus. |
| `Upg_SlideBoost` | **GREASED** | « Le slide te propulse plus fort. » | C / R / E | `SlideBoost` | `+SlideBoost` | cap +100 % | ⚠️ **Moyen** — interagit avec le bunny hop ; vérifier qu'on ne dépasse pas `MaxSpeed` gratuitement. |
| `Upg_WallRideDuration` | **GECKO** | « Tu tiens plus longtemps sur un mur. » | C / R / E | `WallRideDuration` | `+WallRideDuration` | cap +100 % | 🔴 **Élevé** — peut rendre triviaux les gaps de wall ride conçus à la durée de base. Voir §6. |
| `Upg_HeatCapacity` | **COOLANT TANK** | « Tu tires plus longtemps avant la surchauffe. » | C / R / E | `HeatCapacity` | `+HeatCapacity` | cap +100 % | Faible à moyen. Cumulé avec `HeatRecovery` + `ThermalCore`, l'overheat peut disparaître. |
| `Upg_HeatRecovery` | **VENT** | « Ton arme refroidit plus vite. » | C / R / E | `HeatRecovery` | `+HeatRecovery` | cap +100 % | idem ci-dessus — voir la note « trio thermique » §6. |

### 4.2 Modificateurs de gameplay (`E_UpgradeModifier`)

**Rare / Epic uniquement. `bUniquePerRun = true`. `MaxStacks = 1`.**
Ils changent une *règle*, pas un *chiffre* : c'est ce qui donne une identité à une run.

| UpgradeID | Nom affiché | Description joueur | Raretés | `E_UpgradeModifier` | Valeur §15 | Risque |
|---|---|---|---|---|---|---|
| `Upg_DashRechargeOnKill` | **BLOODRUSH** | « Chaque kill recharge une partie de ton dash. » | R / E | `DashRechargeOnKill` | `Dash Recharge on Kill` | ⚠️ Combiné à `Upg_DashRecharge` + `Upg_DashCharges`, dash infini en zone de combat. Voir cap §6. |
| `Upg_OverchargedLaser` | **OVERCHARGE** | « Le premier tir après un temps d'arrêt fait double dégât. » | R / E | `OverchargedLaser` | `Overcharged Laser` | ⚠️ Encourage le tir intermittent — **contraire au design vitesse**. Fenêtre de recharge à garder courte. |
| `Upg_MomentumCore` | **MOMENTUM CORE** | « Tu conserves davantage ta vitesse en sautant. » | R / E | `MomentumCore` | `Momentum Core` | ⚠️ Additionne avec `Upg_SpeedRetention` — les deux tapent la même sensation, vérifier le cumul. |
| `Upg_Impact` | **IMPACT** | « Ton melee projette les ennemis bien plus loin. » | R / E | `Impact` | `Impact` | ⚠️ Augmente les kills par wall slam (donc score **et** style). Effet secondaire assumé, à surveiller en calibration. |
| `Upg_ThermalCore` | **THERMAL CORE** | « Ton arme dissipe la chaleur bien plus vite. » | R / E | `ThermalCore` | `Thermal Core` | ⚠️ Trio thermique, voir §6. |

**Non implémentés au MVP** : `E_UpgradeModifier.None` est la valeur par défaut de toute upgrade de
stat pure (`08_DATA_SCHEMAS §2 — S_UpgradeInstance.Modifier`).

---

## 5. Application des upgrades

### 5.1 Qui fait quoi

```
GI_Overdrive
   └── BPC_UpgradeManager        ← STOCKE  (ActiveUpgrades, survit au changement de map)
                │
                │  au BeginPlay du niveau (appelé par GM_Overdrive)
                ▼
BP_PlayerCharacter
   └── BPC_PlayerStats           ← APPLIQUE (calcule les valeurs finales)
                │
                ▼
   BPC_MovementState / BPC_Dash / BPC_Slide / BPC_WallRide / BPC_Health / BP_LaserWeapon+BPC_Heat
```

`BPC_UpgradeManager` **ne touche jamais** directement un composant de gameplay. Il pousse dans
`BPC_PlayerStats`, qui est le seul point d'application (`05_ARCHITECTURE §3`).

### 5.2 Surcharge sans écrasement — le principe

`PDA_MovementData` (`DA_Movement_Default`) est un **DataAsset partagé et immuable au runtime**.
Le modifier écraserait les valeurs de base pour toute la session éditeur : **interdit**.

`BPC_PlayerStats` maintient donc un **cache de valeurs effectives** :

```
STRUCTURE interne de BPC_PlayerStats
    BaseValues     : Map<E_UpgradeStat, Float>    // copié depuis PDA_MovementData / PDA_WeaponData au BeginPlay
    AdditiveBonus  : Map<E_UpgradeStat, Float>    // Σ des upgrades bIsPercentage = false
    MultiplierBonus: Map<E_UpgradeStat, Float>    // Σ des upgrades bIsPercentage = true (en %)
    FinalValues    : Map<E_UpgradeStat, Float>    // résultat, lu par tous les composants
```

```
FUNCTION RecalculateStats()
    FOR EACH Stat IN E_UpgradeStat :
        Base = BaseValues[Stat]                                  // jamais modifié
        Add  = AdditiveBonus[Stat]
        Mult = clamp(MultiplierBonus[Stat], -StatCapDown, StatCapUp)   // garde-fou §6
        FinalValues[Stat] = (Base + Add) * (1 + Mult)
    Dispatch OnStatsRecalculated()
```

**Ordre d'application : ADDITIF d'abord, MULTIPLICATIF ensuite.** Un `+15 PV` puis `+30 %` donne
`(100 + 15) × 1.30`, pas `100 × 1.30 + 15`. Règle unique, appliquée partout, sans exception —
c'est ce qui rend l'affichage « avant → après » de `WBP_LootChest` (§7) exact et prévisible.

Cas particuliers :
- `DashCooldown` : les valeurs de §15 sont **négatives** (`−10 %`, `−20 %`, `−33 %`). Elles vont dans
  `MultiplierBonus` et sont clampées par le bas (`StatCapDown`), pas par le haut.
- `DashCharges` : entier pur, additif uniquement, jamais de pourcentage.
- Les `E_UpgradeModifier` **n'entrent pas** dans ce calcul. Ils sont exposés en booléens lus par les
  composants concernés : `BPC_PlayerStats.HasModifier(E_UpgradeModifier) → Bool`.
  Ex. `BPC_Dash` interroge `HasModifier(DashRechargeOnKill)` sur `OnEnemyKilled`.

### 5.3 Séquence au chargement d'un niveau

```
OpenLevel(L_W1_02)
   │
   ├─ GM_Overdrive.BeginPlay
   │     ├─ SpawnPlayer
   │     └─ GI_Overdrive.BPC_UpgradeManager.ApplyAllTo(PlayerStats)
   │              ├─ PlayerStats.ResetToBase()                 // repart TOUJOURS des DataAssets
   │              ├─ FOR EACH U IN ActiveUpgrades : PlayerStats.AddUpgrade(U)
   │              └─ PlayerStats.RecalculateStats()
   │
   ├─ BPC_PlayerStats.OnStatsRecalculated
   │     └─ chaque composant relit ses valeurs (bind, pas de poll)
   │
   └─ BP_LevelManager.OnLevelStarted → le score commence à mesurer
```

`ResetToBase()` **avant** réapplication est obligatoire : sans lui, les bonus se ré-empileraient à
chaque map et la run deviendrait exponentielle. C'est le bug n°1 attendu sur ce système.

**PV au changement de niveau** : `MaxHealth` est recalculé, puis `CurrentHealth` est ajusté
proportionnellement (le joueur ne se fait pas soigner gratuitement par un `+MaxHealth`, et ne meurt
pas non plus d'un recalcul). **Politique de soin entre niveaux : aucun soin gratuit** — le ratio de PV
est reporté d'un niveau au suivant. Le seul moyen de remonter ses PV est `Upg_MaxHealth`, dont le
gain de `MaxHealth` s'applique au ratio courant. Cohérent avec GDD §50 : la mort et les dégâts coûtent,
rien ne se réinitialise gratuitement au milieu d'une run.

---

## 6. Garde-fous d'équilibrage

### 6.1 Caps

| Garde-fou | Valeur | Source |
|---|---|---|
| Cumul max d'une même stat | **+100 %** sur une run | `07_TUNING §15` (GDD §49) |
| Cumul max de réduction `DashCooldown` | `StatCapDown` | `07_TUNING §15` |
| `DashCharges` | +1 max, Epic only | §4.1 |
| Modificateurs | 1 exemplaire chacun, `bUniquePerRun` | §4.2 |
| Nombre total d'upgrades sur une run | **7 maximum** | structure de run (`CLAUDE.md §1`) |

**Le compte exact** : 6 niveaux + 2 boss = **8 fins de niveau**, mais le boss 02 termine la run
(`GI_Overdrive.EndRun(Success)`, §2.3) et **ne donne pas de coffre** → il reste **7 coffres**, donc
**7 upgrades maximum**, une par coffre (§2.1).

Ce plafond de 7 est le vrai garde-fou structurel : même en tirant les 7 meilleures cartes,
la puissance totale reste bornée. C'est pourquoi il n'y a **pas de Legendary** — il n'y a pas de
place dans une run pour une rareté de plus.

**Le système de vies ne change rien à ce compte** (`11_ARBITRAGES D1 / D29`) : un coffre s'obtient en
**terminant** un niveau, jamais en mourant dedans. Mourir ne donne pas de coffre, ne retire pas d'upgrade
(§8), et ne rouvre pas un coffre déjà pris. Une run qui échoue en cours de route en compte simplement
**moins de 7** — le plafond n'est jamais dépassé, dans aucun scénario.

### 6.1.1 Ce qui est explicitement HORS du catalogue

> **Une upgrade « +1 vie » a été explicitement REJETÉE du MVP.** Elle est datée et rangée au backlog
> post-v1 : `03_SCOPE_LOCK §4`, ligne « Vie supplémentaire comme loot Epic rare » (2026-08-18).
> **Ne pas l'implémenter, ne pas l'ajouter à une `DT_LootTable_*`, ne pas créer de `DA_Upg_ExtraLife_*`.**

Pourquoi ce refus est structurel, et pas un simple « pas le temps » :

| Raison | Détail |
|---|---|
| Elle casse la condition de défaite | `Run_MaxLives` (`07_TUNING §18`) **est** la condition de défaite de la run (`11_ARBITRAGES D1 / D31`). Une upgrade qui la remonte transforme la seule règle de fin de partie en variable de loot. |
| Elle contredit la règle n° 1 du loot | *« Les upgrades aident, elles ne remplacent jamais le skill »* (§1). Une vie ne rend pas le joueur meilleur : elle annule une erreur. C'est exactement l'inverse du contrat. |
| Elle inverse la boucle de risque | Le loot doit pousser à **prendre la ligne rapide**. Une upgrade défensive pousse à jouer sûr pour la conserver — le signal d'alarme identifié dans `07_TUNING §18`. |
| Le levier d'équilibrage existe déjà ailleurs | Si 3 vies s'avère trop sévère en playtest, on bouge `Run_MaxLives` ou on active `Run_LivesRefillOnBoss` (`07_TUNING §18`, `03_SCOPE_LOCK §4`). **On ajuste un chiffre, on n'ajoute pas du contenu.** |

Même règle pour toute variante déguisée : « +1 vie au boss vaincu », « seconde chance », « revive »,
« bouclier qui absorbe une mort ». Aucune ne rentre dans le MVP.

### 6.2 Ce qui ne doit JAMAIS devenir trivialisable

| Élément | Menace | Parade |
|---|---|---|
| **Les gaps de wall ride** | `Upg_WallRideDuration` maxé permet de tenir sur un mur bien au-delà de l'intention du level design | Le level design se calibre sur la **durée de base**, et les gaps critiques sont dimensionnés avec une marge testée à +100 % de durée. Aucun gap ne doit être *impossible* sans upgrade ni *gratuit* avec. |
| **Les sauts et écarts de plateforme** | `Upg_MaxSpeed` + `Upg_SlideBoost` transforment un saut exigeant en formalité | Aucun saut obligatoire ne doit exiger plus que la vitesse de base ; à l'inverse, la géométrie ne doit pas devenir « trop rapide pour être lisible » — d'où le hard cap sur `MaxSpeed`. |
| **Les boss** | `Upg_LaserDamage` + `Upg_OverchargedLaser` → phase 2 sautée | Les transitions de phase des boss sont pilotées par `PDA_BossData.Phase2HealthThreshold` (**ratio**, pas valeur absolue) : plus de dégâts = boss plus court, jamais de phase **sautée**. |
| **L'overheat (trio thermique)** | `HeatCapacity` + `HeatRecovery` + `ThermalCore` cumulés = plus jamais de surchauffe | Les trois sont **plafonnés séparément** et `ThermalCore` est `bUniquePerRun`. Critère de validation : même en full thermique, un tir continu doit **toujours** finir par surchauffer. |
| **Le combat rapproché** | `MeleeDamage` + `Impact` = un poing tue tout | Le melee reste un outil de **repositionnement et de knockback**, pas la meilleure DPS. Vérifier que le Tank survit à un melee full-upgrade. |
| **La lecture de l'espace** | dash quasi permanent (`DashRecharge` + `DashCharges` + `Bloodrush`) | Cap dur `StatCapDown` sur le cooldown. Le dash doit rester une **ressource**, jamais un mode de déplacement continu. |

### 6.3 Comment tester une run « full upgrades »

Procédure obligatoire avant de valider l'équilibrage (mode debug, `GI_Overdrive.DebugGrantUpgrades`,
Category `Debug`) :

1. Accorder de force les **7 upgrades les plus fortes** — c'est le maximum atteignable sur une run (§6.1) :
   `MaxSpeed` E, `DashRecharge` E, `DashCharges` E, `WallRideDuration` E, `LaserDamage` E,
   `Bloodrush` E, `ThermalCore` E. Puis rejouer **le dernier niveau du monde 2 + le boss 02**.
2. Critères de réussite du test — la run doit **rester exigeante** :
   - [ ] Le joueur peut encore **mourir** en jouant mal.
   - [ ] Le laser **surchauffe encore** en tir soutenu.
   - [ ] Le dash a encore des moments d'indisponibilité en combat.
   - [ ] Le boss 02 dure encore **assez longtemps pour que ses deux phases soient jouées**.
   - [ ] Le rank **S n'est pas automatique** — parce que le S dépend du TEMPS et du STYLE
         (`SPEC_SCORE_RANK.md §2`), donc de l'exécution, pas des stats.
3. Si un seul critère échoue → **baisser la valeur en `07_TUNING §15`**, jamais retirer l'upgrade
   du catalogue (le nerf est un chiffre, pas une suppression de contenu).

> Le test ultime de la règle n°1 : **une run full upgrades doit être plus rapide et plus confortable,
> jamais plus facile à rater.**

---

## 7. Écran de choix — `WBP_LootChest`

### 7.1 Layout

Coffre A → **2 propositions** (`07_TUNING §15`, colonne « Nb de choix »).

```
┌──────────────────────────────────────────────────────────────┐
│                     ◆  A RANK CHEST  ◆                       │
│                     CHOOSE ONE UPGRADE                       │
│                                                              │
│   ┌────────────────┐  ┌────────────────┐                     │
│   │     [RARE]     │  │     [EPIC]     │   ← liseré coloré   │
│   │      ICON      │  │      ICON      │      par rareté (§1)│
│   │                │  │                │                     │
│   │   OVERDRIVE    │  │    GECKO       │                     │
│   │                │  │                │                     │
│   │ Ta vitesse max │  │ Tu tiens plus  │  ← Description      │
│   │ monte.         │  │ longtemps sur  │     joueur          │
│   │                │  │ un mur.        │                     │
│   │ ──────────────  │  │ ──────────────  │                     │
│   │ MAX SPEED      │  │ WALL RIDE      │  ← stat affectée    │
│   │ 6000 ▸ 6600    │  │ 2.0s ▸ 3.4s    │  ← AVANT ▸ APRÈS    │
│   │        (+10 %) │  │        (+70 %) │                     │
│   └────────────────┘  └────────────────┘                     │
│                                                              │
│   ACTIVE : FLOW ×2 · VENT ×1                                 │
└──────────────────────────────────────────────────────────────┘
```

**Vérification des deux cartes** (aucune valeur n'est inventée) :

| Carte | Stat pilotée | Valeur de base | Rareté | Valeur §15 | Après |
|---|---|---|---|---|---|
| `OVERDRIVE` | `Speed_HardCap` (`07_TUNING §3`) | **6000 uu/s** | Rare | `+MaxSpeed` +10 % | `6000 × 1.10` = **6600 uu/s** |
| `GECKO` | `WallRide_MaxDuration` (`07_TUNING §9`) | **2.0 s** | Epic | `+WallRideDuration` +70 % | `2.0 × 1.70` = **3.4 s** |

Le bandeau `ACTIVE` ne liste que des upgrades **déjà prises** : `OVERDRIVE` ne peut donc pas y figurer
en même temps qu'elle est proposée (§3.2, exclusion n° 4).

### 7.2 Information montrée — non négociable

| Élément | Règle |
|---|---|
| **Avant ▸ Après** | Valeur **effective actuelle** du joueur → valeur si la carte est prise, calculée par **`BPC_PlayerStats.PreviewUpgrade(Upgrade) → (Before, After)`** (fonction **pure**, n'applique rien, ne touche jamais `FinalValues`). C'est l'information la plus importante de l'écran : le joueur choisit sur un chiffre réel, pas sur un pourcentage abstrait. |
| **Rareté** | Liseré + libellé. Common / Rare / Epic. Jamais un simple pourcentage de couleur. |
| **Description joueur** | Une phrase, en langage de sensation (« tu tiens plus longtemps »), jamais en jargon (« +40 % WallRideDuration »). Le jargon est sur la ligne stat. |
| **Upgrades déjà actives** | Bandeau bas, compact, avec le nombre de stacks. Permet de construire une build sans ouvrir de menu. |
| **Modificateurs** | Carte visuellement distincte (pas de ligne « avant ▸ après » — ils ne modifient pas une stat) : le texte de règle occupe toute la carte. |

### 7.3 Timing et input

- Ouverture : enchaînée depuis `WBP_Results` → `CONTINUE`, avec le stagger de révélation (§2.3).
- **Aucun timer de décision.** Le joueur n'est pas sous pression : c'est le seul moment calme du jeu.
- Sélection au clic **ou** aux touches `1..N` (choix immédiat, pas de confirmation à deux temps).
- Hover : la carte s'agrandit, la ligne « avant ▸ après » s'anime.
- Après le choix : les cartes non prises se dissolvent, la carte choisie s'envole vers le HUD,
  puis `OpenLevel(NextLevel)` (`PDA_LevelData.NextLevel`).
- Bind sur dispatchers, **aucun Tick de widget** (`06_CONVENTIONS §4.6`).

---

## 8. Persistance — la portée d'une upgrade

> **La règle, en une phrase** : une upgrade est acquise **pour toute la run**. Elle survit aux
> changements de niveau **et** aux morts. Elle n'est remise à zéro qu'au **démarrage d'une nouvelle run**
> — c'est-à-dire au retour au menu, après `RunFailed`, ou après le boss 02.
> **Il n'existe aucun autre événement qui retire une upgrade au joueur.**

C'est la règle définitive de `11_ARBITRAGES D1`. Elle tranche la contradiction du GDD (§1 « à la mort
la run est perdue » vs §50 « les upgrades restent actifs ») : ce qui coûte, c'est une **vie**
(`Run_MaxLives`, `07_TUNING §18`), du temps, du score et le style — **jamais la build**.

### 8.1 Ce qui conserve, ce qui remet à zéro

| Événement | `ActiveUpgrades` | Pourquoi |
|---|---|---|
| **Mort avec `LivesRemaining > 0`** (respawn au checkpoint) | ✅ **conservées** | Le message doit être « tu as raté ce passage », pas « recommence ta build ». Perdre ses upgrades en mourant transformerait une mort en abandon de run de fait. |
| **Passage au niveau suivant** (`OpenLevel`) | ✅ **conservées** | Elles vivent dans `GI_Overdrive`, qui survit au changement de map (`05_ARCHITECTURE §4`). |
| **Restart volontaire d'un niveau** (`R`, `11_ARBITRAGES D16`) | ✅ **conservées** | Sinon relancer un niveau pour améliorer son rank coûterait la run entière. |
| **`RunFailed`** (0 vie) | ❌ **remises à zéro** | Fin de run : `EndRun(Failed)` → `StartNewRun()` au prochain *PLAY*. |
| **Fin de run réussie** (boss 02) | ❌ **remises à zéro** | Idem. Pas de méta-progression (règle n° 3, §1). |
| **Retour au menu / nouvelle run** | ❌ **remises à zéro** | C'est le **seul** moment où le reset a lieu. |

**Le tableau de portée qui fait autorité est `05_ARCHITECTURE §4`** (« Portée des données »).
Il couvre `ActiveUpgrades`, `LivesRemaining`, `LevelScores`, `CurrentLevelIndex`, le style et le chrono.
Cette spec ne le duplique pas ; elle en détaille seulement la colonne « upgrades ».

### 8.2 Où vit quoi

| Donnée | Vit dans | Survit à une **mort** | Survit à un **restart de niveau** | Survit à la **fin de run** |
|---|---|---|---|---|
| `ActiveUpgrades` (`Array<S_UpgradeInstance>`) | `GI_Overdrive.RunState` | ✅ oui | ✅ oui | ❌ non |
| `CurrentLevelIndex` | `GI_Overdrive.RunState` | ✅ | ✅ | ❌ |
| `LivesRemaining` | `GI_Overdrive.RunState` | **décrémenté** (`ConsumeLife()`) | ✅ inchangé | ❌ reset à `Run_MaxLives` |
| `LevelScores`, `TotalRunScore` | `GI_Overdrive.RunState` | ✅ | l'entrée du niveau est **remplacée** | ❌ (affiché une dernière fois par `WBP_RunFailed`, `SPEC_SCORE_RANK §7.5`) |
| `CachedRolls` (offres par `LevelID`) | `BPC_UpgradeManager` | ✅ | ✅ (pas de re-roll, §3.4) | ❌ |
| `TotalDeaths` | `GI_Overdrive.RunState` | ✅ (incrémenté) | ✅ | ❌ |
| Style, kills, temps, vitesse du niveau | `GS_Overdrive` | partiellement (cf. `SPEC_SCORE_RANK §5`) | ❌ remis à zéro | ❌ |
| Stats effectives | `BPC_PlayerStats` | **recalculées** au respawn | recalculées | ❌ |
| **Quoi que ce soit sur disque** | — | — | — | **rien. Pas de save.** |

```
GI_Overdrive.StartNewRun()
    RunState = default (ActiveUpgrades vide, LevelScores vide, index 0,
                        LivesRemaining = Run_MaxLives)        // 07_TUNING §18
    CachedRolls.Empty()
    DebugSeed ignoré en build

GI_Overdrive.ConsumeLife()                                    // appelé par BPC_Health.OnDeath
    LivesRemaining -= 1
    → ActiveUpgrades INTACTES, dans tous les cas
    → si 0 : EndRun(Failed)

GI_Overdrive.EndRun(Success | Failed)
    → affichage du récap de run (WBP_RunFailed / écran de fin)
    → StartNewRun() au prochain "PLAY"     ← le SEUL point de reset des upgrades
```

### 8.3 Le respawn recalcule, il ne ré-empile pas

Au respawn comme au chargement d'un niveau, `BPC_UpgradeManager.ApplyAllTo(PlayerStats)` passe
**obligatoirement** par `ResetToBase()` avant de réappliquer les `ActiveUpgrades` (§5.3).
Sans lui, chaque mort ajouterait une couche de bonus et une run à 3 vies deviendrait exponentielle :
c'est le **bug n° 1 attendu** de ce système, et le système de vies en multiplie les occasions.
Critère de test : mourir 3 fois d'affilée doit laisser des stats **strictement identiques**
à celles d'avant la première mort (§9).

---

## 9. Checklist de validation manuelle (Louis)

**Tirage**
- [ ] Finir un niveau en rank D : coffre D, **1** seule proposition, aucune Rare/Epic.
- [ ] Finir un niveau en rank S : coffre S, nombre de propositions conforme à `07_TUNING §15`.
- [ ] Sur 20 ouvertures de coffre A : la distribution Common/Rare/Epic ressemble à la table §15.
- [ ] Aucune offre n'affiche **deux fois la même stat** (même en raretés différentes).
- [ ] Prendre `Upg_DashCharges` puis rouvrir un coffre S : elle **ne réapparaît plus**.
- [ ] Prendre un modificateur (ex. `Impact`) : il **ne réapparaît plus** de la run.
- [ ] Maxer une stat au cap +100 % : elle disparaît des offres, l'offre reste pleine (fallback OK).
- [ ] Vider artificiellement la table : le coffre propose moins de cartes mais **n'est jamais vide**.

**Seed / re-roll**
- [ ] Restart du même niveau, même rank : **mêmes offres** (cache par `LevelID`).
- [ ] Restart du même niveau avec un **meilleur rank** : offres différentes (autre table).
- [ ] Nouvelle run : les offres du niveau 1 sont différentes de la run précédente.

**Application**
- [ ] Prendre `+MaxSpeed Rare` : la vitesse max en jeu correspond exactement au « après » affiché.
- [ ] Prendre 2 upgrades de la même stat : l'ordre additif→multiplicatif est respecté (vérifier au debug).
- [ ] Passer 3 niveaux avec les mêmes upgrades : **les bonus ne se ré-empilent pas** (bug n°1 attendu).
- [ ] Ouvrir `DA_Movement_Default` après une run : **aucune valeur modifiée**.
- [ ] Mourir puis respawn : les upgrades sont toujours actives, les stats correctes.
- [ ] Prendre `+MaxHealth` : les PV courants ne sont pas soignés gratuitement.

**Portée de la run (§8)**
- [ ] Mourir 3 fois d'affilée : stats effectives **strictement identiques** à avant la première mort
      (pas de ré-empilement — §8.3).
- [ ] Mourir ne retire **aucune** upgrade et n'en ajoute aucune.
- [ ] Enchaîner 3 niveaux : les upgrades s'accumulent, une par coffre, **jamais plus de 7** sur la run.
- [ ] Épuiser ses vies (`RunFailed`) puis relancer : `ActiveUpgrades` **vide**, `CachedRolls` vidé,
      `LivesRemaining` = `Run_MaxLives`.
- [ ] Aucune table de loot ne contient d'upgrade « +1 vie » ni aucune variante (§6.1.1).

**Équilibrage**
- [ ] Run full upgrades (§6.3) : les 5 critères de « reste exigeante » passent.
- [ ] Full thermique : le laser **surchauffe encore** en tir continu.
- [ ] Full dash : il existe encore des moments sans dash en combat.
- [ ] Boss 02 full upgrades : les **deux phases** sont jouées.
- [ ] Un gap de wall ride conçu pour la durée de base reste franchissable **sans** upgrade.

**Écran de choix (ressenti, R8)**
- [ ] Le joueur comprend en 2 secondes ce que chaque carte change **concrètement**.
- [ ] La ligne « avant ▸ après » est exacte pour les 3 raretés d'une même upgrade.
- [ ] Choisir prend moins de 5 secondes sans se sentir pressé.
- [ ] L'ouverture du coffre procure une sensation de récompense — sinon revoir §2.3, pas les chiffres.

---

## 10. Où vivent les valeurs

Toutes les clés citées dans ce document — `Loot_ChestOpenDuration`, `Loot_CardRevealStagger`,
`Loot_CardFlyToHUDDuration`, `StatCapUp`, `StatCapDown`, `Modifier_OverchargedLaser_RechargeWindow`,
les drop rates, la colonne « Nb de choix » et les valeurs d'upgrade par rareté — sont définies dans
**`Docs/07_TUNING.md §15`**. Les clés de **run et de vies** citées en §6.1.1 et §8 (`Run_MaxLives`,
`Run_LivesRefillOnBoss`, `Run_LevelCount`) sont dans **`§18`**. Aucune n'est orpheline, aucune n'est à créer.

> Règle R3 : la valeur vit dans `07_TUNING.md`, jamais dans une spec. On y renvoie par nom de ligne.
> Décisions d'arbitrage applicables : **`Docs/11_ARBITRAGES.md` D1** (les upgrades survivent à la mort,
> pas à la run), **D17** (couleurs de rareté), **D29** (7 upgrades max) et **D31** (vies).
> Couleurs : **`Docs/ArtDirection/PALETTE.md §5`** pour les raretés, **`§7`** pour les panneaux d'UI.
> Aucun HEX n'est écrit dans cette spec.
