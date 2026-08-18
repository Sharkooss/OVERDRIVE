# SPEC — BOSS

> 2 boss, 2 phases maximum chacun (GDD §31). `BP_BossBase` hérite de `BP_EnemyBase`. Prérequis de lecture :
> **`Docs/Specs/SPEC_ENEMIES.md`** — tout ce qui n'est pas redit ici en vient. Valeurs : `Docs/07_TUNING.md`, **§13
> sous-section Boss** (et `§14` pour les clés `Boss_*Score*`) — toutes les clés citées ici y existent et sont
> `[À CALIBRER]`. Blueprint uniquement (R1). Priorité R5 : le boss passe après le score et le juice.

## 1. Philosophie

Un boss d'OVERDRIVE est un **niveau de mouvement déguisé en ennemi**. Il ne teste pas votre DPS, il teste si vous savez
encore bouger quand quelque chose vous vise.

1. **Le boss force le mouvement.** Chaque attaque a une parade qui est une **mécanique de mouvement** (slide, dash, wall
   ride, air strafe, saut) — jamais « reculer » ni « se cacher ».
2. **2 phases maximum.** Phase 2 = **nouvelles attaques + arène modifiée**, pas « les mêmes en plus rapide ».
3. **3–4 attaques maximum par boss**, toutes phases confondues, chacune lisible en une demi-seconde.
4. **Le boss est toujours vulnérable.** Aucune fenêtre où le joueur ne peut rien faire.
5. **Un combat dure ~90 s** (`Boss_TargetFightDuration`). Au-delà, on coupe des PV, pas du gameplay.

**Explicitement interdit** : plus de 2 phases · plus de 4 attaques · barres de vie multiples · **cinématiques** (interdit
absolu, `CLAUDE.md §6` — l'intro est un plan fixe de `Boss_IntroDuration`, `PDA_BossData`, **skippable**) · invulnérabilité
scriptée · murs invisibles surgissants · phase d'« add clear » obligatoire · attaque non esquivable ou qui suit le joueur
(pas de homing, `SPEC_ENEMIES §5`) · attaque qui **immobilise** (la punition reste la perte de vitesse, `07_TUNING §10`) ·
boss qui vole hors de portée, qui régénère, ou timer d'enrage.

## 2. `BP_BossBase`

`Content/OVERDRIVE/Bosses/Base/BP_BossBase`, **hérite de `BP_EnemyBase`**. Il récupère gratuitement `BPI_Damageable`, les
hitboxes, le flash de hit, le dissolve, `BPI_ScoreEvent` et `BPC_Health`. Il **désactive** ce qui n'a pas de sens :
`BPC_KnockbackReceiver` (`KnockbackResistance = 1`, `bCanBeWallSlammed = false`) et l'activation par distance — le boss est
réveillé par `BP_LevelManager`.

**Mort : dissolve, jamais de ragdoll — la règle vaut aussi pour les boss.** Aucune simulation physique, à aucun moment.
`Die()` hérité de `BP_EnemyBase` (`SPEC_ENEMIES §8`) : `DissolveAmount` sur `M_Toon_Enemy` pendant
`Death_DissolveDuration`, puis `DestroyActor`. Pas de `PHYS_Boss_*`, pas de délai de cadavre.

| Ajout | Détail |
|---|---|
| `BossData` | `PDA_BossData` (`08_DATA_SCHEMAS §3`) : `PhaseCount`, `Phase2HealthThreshold`, `AttackPatterns`, `ArenaBoundsTag`, `IntroDuration` |
| `CurrentPhase` | Int (1–2) |
| `E_BossState` | `Idle · Intro · Telegraph · Attacking · Recover · PhaseTransition · Dead` — enum défini dans **`08_DATA_SCHEMAS §1`**, qui fait foi |
| `WBP_BossHealthBar` | Créé au début du combat, détruit à la mort. **2 segments = 2 phases** |
| `ArenaActors` | Refs des `BP_BossArenaElement` (plateformes, murs mobiles, dangers) taggés `ArenaBoundsTag` |
| Dispatchers | `OnBossFightStarted` · `OnPhaseChanged(NewPhase)` · `OnBossAttackTelegraph(Name)` · `OnBossDefeated` |
| `AttackPatterns` | Array de `Name` → un **Event custom par nom d'attaque** dans l'enfant |

```
      LevelManager.StartBossFight()
Idle ─────────────────────────────▶ Intro ─▶ ┌──── COMBAT LOOP ────┐
                                             │ Telegraph ─▶ Attacking│
                                             │     ▲          │      │
                                             │     └ Recover ◀┘      │
                                             └───────────┬───────────┘
                                        HP% <= Phase2HealthThreshold │
                                                         ▼
                                   PhaseTransition (Boss_PhaseTransitionPause)
                                                         ▼
                                   COMBAT LOOP (set d'attaques 2) ── HP=0 ──▶ Dead
```
**Implémentation** : machine à états **dans le BP**, pas de StateTree — 7 états mais un seul flux linéaire piloté par timers
et Timelines ; un StateTree n'apporterait que de l'indirection. On le réserve aux archétypes navigants (`SPEC_ENEMIES §5–6`).

**Transition de phase — pas d'invulnérabilité.** Elle dure `Boss_PhaseTransitionPause` = **0.6 s [À CALIBRER]** pendant
lesquelles le boss **n'attaque pas** mais **reste vulnérable**. Raison : une fenêtre d'invulnérabilité dans un jeu de vitesse
est un temps mort, le joueur y perd son momentum. Ici la transition est au contraire la **meilleure fenêtre de DPS** du
combat. Ce qui se passe pendant : flash + changement de couleur émissive, modification de l'arène, un son unique.

```
SelectNextAttack()
  Pool = BossData.AttackPatterns filtré par CurrentPhase
  Exclure la dernière attaque jouée        ← jamais deux fois la même d'affilée
  Pondérer par distance joueur/boss        ← attaque de proximité vs attaque de zone
  CallFunctionByName(AttackName)
     EnterState(Telegraph) → OnBossAttackTelegraph.Broadcast → VFX + SFX + décalque au sol
     wait TelegraphTime                    ← config par attaque
     EnterState(Attacking) → Timeline / spawn de projectiles / trace
     EnterState(Recover)   → wait RecoverTime      ← FENÊTRE DE RIPOSTE
```
**Règle du télégraphe** : `TelegraphTime` d'une attaque de boss ≥ `Shooter_TelegraphTime` (`07_TUNING §13`). Le boss est
gros et lu de plus loin : il a besoin de plus, pas de moins.

## 3. Structure d'un combat de boss

```
0s        3s                    35s                40s                    90s
│ INTRO   │ PHASE 1             │ TRANSITION       │ PHASE 2              │ MORT
│ plan    │ 2 attaques          │ 0.6 s            │ 3 attaques           │ dissolve
│ fixe    │ arène simple        │ arène change     │ arène hostile        │ + résultats
│ skip    │ apprentissage       │ fenêtre de DPS   │ exécution            │
```

| Segment | Durée cible **[À CALIBRER]** | Ce que fait le joueur |
|---|---|---|
| `Telegraph` | 0.7–1.2 s | lit, décide, oriente son mouvement |
| `Attacking` | 0.4–1.5 s | **esquive en mouvement**, ne tire pas |
| `Recover` | 1.2–2.0 s | tire, se replace, gagne du style (wall ride, dash) |

**Ratio cible : ~40 % du temps en esquive, ~60 % en riposte.** Si le joueur passe plus de la moitié du combat à ne pas
pouvoir tirer, le combat est raté. **Contrainte de vitesse** : sa vitesse moyenne pendant un combat de boss doit rester
comparable à celle d'un niveau normal — c'est mesurable (`S_LevelScore.AverageSpeed`), et si elle s'effondre, le boss
immobilise et doit être retravaillé.

## 4. Boss 01 — `BP_Boss_01` « OVERSEER » (fin World 1)

**Concept** : un **noyau blindé suspendu au centre d'une arène cylindrique**. Il ne se déplace pas, il **tourne**. Le joueur
doit tourner autour, plus vite que lui. Boss « circulaire » qui valide exactement ce que W1 a enseigné : **wall ride, slide,
dash directionnel**.

```
       vue de dessus                       vue de côté
  ┌──────────────────────┐            ┌─────────────────────┐
  │ ░░░ mur wall-ride ░░ │            │   ╱‾‾‾╲             │   ◉ = noyau (boss)
  │ ░ ┌───┐  ◉  ┌───┐  ░ │            │  │ ◉ │  à ~600 uu   │   P = plateforme (dash only)
  │ ░ │ P │     │ P │  ░ │            │   ╲___╱             │   ░ = WallRideSurface
  │ ░░░░░░░░░░░░░░░░░░░░ │            │ ══════════════════  │
  └──────────────────────┘            └─────────────────────┘
```
Arène `L_W1_Boss` : cylindre de `Boss01_ArenaDiameter` = **4800 uu** (`07_TUNING §13`) · mur périphérique **entièrement
`WallRideSurface`** (`07_TUNING §9`), hauteur ≥ 1200 uu · 2 plateformes surélevées atteignables **au dash uniquement** ·
anneau au sol qui s'électrifie en phase 2 (attaque C) · ligne de vue dégagée à 360°, aucun angle mort. La distance maxi
entre deux murs de wall ride opposés (`07_TUNING §17`) est une règle de **couloir de traversée** : elle **ne contraint
pas** le diamètre d'une arène de boss, où l'on tourne autour d'un mur unique au lieu de rebondir entre deux murs.

**A — `SweepBeam` (phases 1 et 2).** Télégraphe **0.9 s [À CALIBRER]** : le noyau s'oriente, un rayon fin trace le plan de
balayage. Exécution : rayon horizontal à hauteur de torse, balayage 360° en `Boss01_SweepDuration` = **1.4 s [À CALIBRER]**.
**Parade : slide dessous** (le rayon passe au-dessus de `CapsuleHalfHeight_Slide`, `07_TUNING §2`) **ou wall ride au-dessus**.
Punition : dégâts + −45 % de vitesse (`§10`), jamais de stun. C'est l'attaque signature : elle rend le slide et le wall ride
obligatoires, pas optionnels.

**B — `MortarVolley` (phases 1 et 2).** Télégraphe : `Boss01_MortarCount` = **4 [À CALIBRER]** décalques au sol, **0.7 s**
avant impact. Exécution : projectiles en cloche visant les **positions successives du joueur au moment du tir**, jamais
anticipées (`SPEC_ENEMIES §5`). **Parade : ne jamais s'arrêter**, dash latéral si acculé. Réutilise `BP_EnemyProjectile` avec
`ProjectileGravityScale > 0`, mesh scalé, MI différent. Punit l'immobilité — le seul comportement qu'on veut interdire.

**C — `GroundPulse` (phase 2 uniquement).** Télégraphe **1.1 s [À CALIBRER]** : tout le sol pulse en émissif. Exécution :
onde depuis le centre, sol pénalisant pendant `Boss01_PulseDuration` = **2.0 s [À CALIBRER]**. **Parade : quitter le sol** —
wall ride sur le mur périphérique, ou plateforme au dash. Vérifie que le joueur sait **rester en l'air**, compétence
terminale de W1.

**Transition** : `Phase2HealthThreshold` = **0.5 [À CALIBRER]**. Le blindage se détache (mesh caché + VFX), le noyau passe en
couleur chaude, `GroundPulse` entre dans le pool, et `SweepBeam` gagne un **second rayon plus bas** : il faut désormais
choisir entre passer dessous et passer au-dessus, on ne peut plus faire les deux au hasard. Pas d'invulnérabilité (§2).

**Mort** : PV du noyau à 0. Pas de phase 3, pas de dernier souffle. `Die()` hérité (`SPEC_ENEMIES §8`) : dissolve +
`BPI_ScoreEvent`, puis `OnBossDefeated` → `BP_LevelManager` → écran de résultats.

## 5. Boss 02 — `BP_Boss_02` « REDLINE » (final)

**Concept** : **un rival qui bouge comme vous**. Il dash, il wall ride, il garde son momentum. Là où OVERSEER était un
terrain à négocier, REDLINE est une **poursuite en arène** : il ne reste pas en place, il faut le rattraper. Il teste **tout
le kit**, gestion de la chaleur comprise (`BPC_Heat`) — il n'est jamais immobile assez longtemps pour être arrosé.

```
┌────────────────────────────────────┐
│ ░│      │░      │      │░        ░ │   ░ = WallRideSurface (périmètre + piliers)
│ ░│  ▮   │░  ▮   │  ▮   │░  ▮     ░ │   ▮ = pilier wall-ride (4)
│ ░└──────┘░      └──────┘░        ░ │   ═ = rail surélevé (phase 2)
│ ░   ════════════════════          ░│
│ ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└────────────────────────────────────┘
```
Arène `L_W2_Boss` : rectangle long, `Boss02_ArenaLength` = **7000 uu** (`07_TUNING §13`, il faut de la place pour prendre
de la vitesse) · 4 piliers `WallRideSurface` espacés selon `07_TUNING §17` (600–1400 uu entre murs opposés) · passerelle surélevée
traversant l'arène, atteignable en wall ride + wall jump · en phase 2, le **sol devient hostile** (attaque D) : le combat
monte d'un étage.

**A — `DashSlash` (phases 1 et 2).** Télégraphe **0.6 s [À CALIBRER]** : il se fige, s'oriente, traînée de charge visible sur
sa trajectoire. Exécution : dash rectiligne à `Boss02_DashSpeed` = **5000 uu/s [À CALIBRER]** vers la position mémorisée du
joueur. **Parade : dash latéral ou air strafe hors de la ligne**, jamais un recul. S'il finit sa course dans un mur, il subit
`Boss02_SelfStunDuration` = **1.5 s [À CALIBRER]** → grosse fenêtre de DPS pour qui esquive au dernier moment.

**B — `SpreadVolley` (phases 1 et 2).** Télégraphe **0.8 s [À CALIBRER]** : 3 orbes se chargent autour de lui. Exécution :
3 `BP_EnemyProjectile` en éventail, vitesse ≥ `Projectile_Speed` (`07_TUNING §13`). **Parade : passer entre deux
projectiles** — récompense la précision de trajectoire, pas la fuite. L'écart angulaire doit laisser un couloir franchissable
à 3000 uu/s : c'est un critère de validation, pas un chiffre.

**C — `SummonPair` (phase 1 uniquement).** Télégraphe **1.0 s** : 2 marqueurs au sol. Exécution : active **2
`BP_Enemy_Shooter` pré-placés et dormants** (`SPEC_ENEMIES §3`) — **aucun spawn runtime**. **Parade : une décision** — les
tuer (perte de temps) ou les ignorer (tir croisé permanent). Réutilise 100 % de l'archétype Shooter, zéro asset nouveau.

**D — `FloorBurn` (phase 2 uniquement).** Télégraphe **1.2 s [À CALIBRER]** : le sol s'illumine progressivement. Exécution :
le sol inflige dégâts + pénalité de vitesse au contact pendant `Boss02_FloorBurnDuration` = **6.0 s [À CALIBRER]**.
**Parade : wall ride + wall jump + air strafe en chaîne** — survivre 6 s sans toucher le sol, avec `WallRide_MaxDuration` et
`WallRide_SameWallCooldown` (`07_TUNING §9`) qui interdisent de camper un mur. C'est l'examen final : le boss est
imbattable pour qui n'a pas maîtrisé le wall ride.

**Transition** : `Phase2HealthThreshold` = **0.55 [À CALIBRER]**. Il monte sur le rail, `SummonPair` sort du pool, `FloorBurn`
entre, `DashSlash` gagne une seconde charge enchaînée. Toujours pas d'invulnérabilité.
**Mort** : PV à 0 → `OnBossDefeated` → fin de run (`GI_Overdrive.EndRun(Success)`, `05_ARCHITECTURE §4`).

## 6. Scoring d'un boss

> Source de vérité de la formule : **`Docs/Specs/SPEC_SCORE_RANK.md`**. Cette section ne décrit que les **écarts**
> par rapport à un niveau normal.

Un niveau de boss n'a pas 15–30 ennemis : `ScoreKills` (`07_TUNING §14`) serait quasi nul. Substitution, clés définies
dans `07_TUNING §14` :
```
ScoreBoss = Boss_ScoreBase + Boss_PhaseClearBonus × PhasesCleared
          + Boss_NoHitBonus (si DamageTaken == 0) − Boss_DamagePenaltyPerHit × NbHitsReçus

Score = ( ScoreBoss + ScoreSpeed + ScoreTime ) × StyleMultiplier        ← même forme qu'un niveau
```
`Boss_ScoreBase` (équivalent d'un niveau plein d'ennemis) · `Boss_PhaseClearBonus` (récompense la progression même en cas de
mort) · `Boss_NoHitBonus` (le vrai objectif du speedrunner) · `Boss_DamagePenaltyPerHit` (rend `S_LevelScore.DamageTaken`
signifiant). Toutes **[À CALIBRER]** dans `07_TUNING §14`.

**Ce qui ne change pas.** `ScoreSpeed` (`AverageSpeed`) est inchangé et c'est **le garde-fou du design** : un boss qui fait
chuter la vitesse moyenne fait chuter le rank, donc le système sanctionne mécaniquement un boss statique · `ScoreTime`
utilise le `ParTimeSeconds` du combat, dans `DA_Level_W1_Boss.RankThresholds` (`S_RankThresholds`) — source unique
`PDA_LevelData` (`08_DATA_SCHEMAS §4`) · `StyleMultiplier` fonctionne normalement (`Style_Gain_WallRide`, `_Dash`,
`_HighSpeedSustain`, `_AirKill`…), donc un boss combattu en wall ride rapporte structurellement plus · seuils de rank
`S/A/B/C = ParScore × 1.00 / 0.80 / 0.60 / 0.40` (`07_TUNING §14`) dans `DA_Level_W1_Boss` et `DA_Level_W2_Boss` · mort :
pénalité standard, respawn au début du combat, upgrades conservés (`05_ARCHITECTURE §4`) · coffre `BP_LootChest` classique
en fin de combat selon le rank (`07_TUNING §15`).

## 7. Production — un boss en 1 journée

Ordre imposé (R5 : le boss est l'avant-dernier maillon, `05_ARCHITECTURE §5`). Si le budget déborde, **on coupe la phase 2
avant de couper une attaque de phase 1.**

| ⏱ | Étape | Réutilisé | Fabriqué |
|---|---|---|---|
| 1 h | `BP_BossBase` | `BP_EnemyBase` (santé, dégâts, hitbox, dissolve, score), `E_BossState` (`08_DATA_SCHEMAS §1`) | phases, dispatchers, boucle d'attaque |
| 1 h | Arène blockout | `SM_Module_*` (grille 100 uu, `06_CONVENTIONS §6`), preset `OD_WallRideSurface` | layout, placement des piliers |
| 2 h | Attaques phase 1 | `BP_EnemyProjectile`, `BPC_Health`, traces existantes | 2 events custom + Timelines |
| 1 h | Télégraphes | `M_Toon_Enemy` (émissif, `DissolveAmount`), décalques `DEC_` | 2 VFX Niagara simples + 2 sons |
| 1 h | `WBP_BossHealthBar` | style du `WBP_HUD` existant | widget 2 segments, bind sur `OnPhaseChanged` |
| 1 h | Phase 2 | tout ce qui précède | 1 attaque + 1 modification d'arène |
| 1 h | Playtest + tuning | — | remplissage de `07_TUNING §13/§14` |

**Réutilisé systématiquement** : mesh = **Tank scalé + `MI_` propre** (aucun nouveau `SK_`) · **aucune nouvelle animation** —
le mouvement du boss est piloté par Timelines (rotation, scale, translation) et `LaunchCharacter` · projectiles, VFX de hit,
dissolve et sons identiques aux ennemis. **Fabriqué** : l'arène, les télégraphes, la boucle d'attaque. C'est tout. Un boss,
c'est 80 % de level design et 20 % de Blueprint : si vous passez la journée dans l'Event Graph, vous fabriquez le mauvais boss.

## 8. Checklist de validation manuelle

> R8 : manette/clavier en main, sur `L_W1_Boss` puis `L_W2_Boss`.

**Mouvement** — [ ] ma vitesse moyenne pendant le combat est comparable à celle d'un niveau normal (`AverageSpeed`) ·
[ ] je n'ai jamais eu envie de m'arrêter pour tirer tranquillement · [ ] chaque attaque m'a fait utiliser une mécanique
**différente** · [ ] Boss 01 est infaisable sans slide **et** sans wall ride · [ ] Boss 02 est infaisable sans wall ride
**et** sans dash.

**Lisibilité** — [ ] je lis chaque télégraphe **en mouvement**, sans regarder le boss en face · [ ] je distingue les attaques
à l'oreille · [ ] après avoir encaissé, je sais **pourquoi** · [ ] aucune attaque ne me touche hors de mon champ de vision.

**Rythme** — [ ] le combat dure ~90 s à ma 3e tentative · [ ] j'ai une vraie fenêtre de tir après chaque attaque (`Recover`) ·
[ ] la transition de phase se voit et s'entend en moins d'une seconde · [ ] **aucune** perte de contrôle > 0.2 s, transition
comprise · [ ] le boss n'a jamais enchaîné deux fois la même attaque.

**Système** — [ ] `WBP_BossHealthBar` reflète phase + PV en temps réel · [ ] l'intro est skippable dès le premier essai ·
[ ] mort → respawn au début du combat, upgrades conservés, en < 1 s · [ ] `SummonPair` active des Shooters **pré-placés**
(aucun spawn runtime, aucun hitch) · [ ] score et rank corrects dans `WBP_Results`, `Boss_NoHitBonus` vérifié à 0 dégât ·
[ ] `stat game` stable pendant `MortarVolley` / `SpreadVolley` · [ ] aucun endroit de l'arène ne met hors d'atteinte du boss ·
[ ] zéro warning de compilation sur `BP_BossBase`, `BP_Boss_01`, `BP_Boss_02`.

## 9. Valeurs

Toutes les clés `Boss_*`, `Boss01_*` et `Boss02_*` citées dans cette spec vivent dans **`07_TUNING §13`, sous-section
« Boss »** (et `§14` pour les `Boss_*Score*`). C'est le seul endroit où on les modifie.

`MaxHealth`, `AttackDamage`, `PlayerSpeedPenaltyPercent` et `ScoreBase` des boss vivent dans `DA_Boss_01` / `DA_Boss_02`
(`PDA_BossData`, `08_DATA_SCHEMAS §3`), comme pour les autres ennemis.
