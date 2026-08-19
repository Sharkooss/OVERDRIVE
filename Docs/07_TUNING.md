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
| `Accel_Air` | 2500 | uu/s² | À CALIBRER | pilote l'air strafe |
| `MomentumDecayRate` | 400 | uu/s² | À CALIBRER | perte au sol au-dessus du sprint cap |
| `MomentumDecay_GraceTime` | 0.35 | s | À CALIBRER | délai avant que la décroissance démarre |
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
| `Sprint_Mode` | Hold | Hold/Toggle | À CALIBRER (option dans Settings) |

---

## 5. Slide

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Slide_MinEntrySpeed` | 900 | uu/s | À CALIBRER | en dessous → crouch simple |
| `Slide_EntryBoost` | 400 | uu/s | À CALIBRER | boost additif à l'entrée |
| `Slide_MaxDuration` | 1.2 | s | À CALIBRER | |
| `Slide_Friction` | 0.4 | — | À CALIBRER | vs 3.0 debout |
| `Slide_ExitSpeedMin` | 1200 | uu/s | À CALIBRER | on ne sort jamais plus lent que ça |
| `Slide_SlopeAccelBonus` | 1800 | uu/s² | À CALIBRER | en descente, le slide accélère |
| `Slide_Cooldown` | 0.25 | s | À CALIBRER | anti-spam du boost d'entrée |
| `Slide_JumpWindow` | 0.20 | s | À CALIBRER | fenêtre post-slide où le saut garde le boost |
| `Slide_CameraDrop` | 40 | uu | À CALIBRER | descente caméra |
| `Slide_CameraTilt` | 6 | ° | À CALIBRER | |

---

## 6. Saut & bunny hop

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `Jump_ZVelocity` | 900 | uu/s | À CALIBRER | |
| `Jump_MaxCount` | 1 | — | À CALIBRER | pas de double jump (le dash le remplace) |
| `Jump_CoyoteTime` | 0.12 | s | À CALIBRER | |
| `Jump_BufferTime` | 0.15 | s | À CALIBRER | saut anticipé avant l'atterrissage |
| `BHop_PerfectWindow` | 0.10 | s | À CALIBRER | fenêtre après contact sol |
| `BHop_SpeedGain` | 120 | uu/s | À CALIBRER | gain par hop réussi |
| `BHop_MaxChainGain` | 1500 | uu/s | À CALIBRER | plafond du gain cumulé par chaîne |
| `BHop_FrictionSkip` | true | bool | À CALIBRER | pas de friction sol si hop dans la fenêtre |

---

## 7. Air strafe

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `AirStrafe_AirControl` | 0.55 | ratio | À CALIBRER | |
| `AirStrafe_MaxAccel` | 2500 | uu/s² | À CALIBRER | |
| `AirStrafe_GainAngleMax` | 45 | ° | À CALIBRER | angle max input/vélocité donnant du gain |
| `AirStrafe_SpeedGainPerSec` | 300 | uu/s² | À CALIBRER | gain si strafe correct (style Quake) |
| `AirStrafe_NoGainAboveSpeed` | 5000 | uu/s | À CALIBRER | plafond du gain aérien |
| `AirStrafe_WishSpeedCap` | 60 | uu/s | À CALIBRER | **clé du modèle Quake** : plafond de la vitesse désirée projetée. Bas = gain lent et maîtrisable, haut = gain explosif |

**Modèle retenu** : accélération vectorielle style Quake/Source (projection de la vélocité sur
la direction d'input, gain si l'angle est dans `GainAngleMax`). C'est ce qui rend le bunny hop
et le strafe *apprenables* plutôt qu'aléatoires.

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
| `Dash_GravityScale` | 0.0 | ×G | À CALIBRER | apesanteur pendant le dash |
| `Dash_ZLockOnGround` | true | bool | À CALIBRER | dash au sol = horizontal pur |
| `Dash_FOVKick` | +12 | ° | À CALIBRER | |
| `Dash_IFrames` | 0.0 | s | À CALIBRER | **par défaut : pas d'invincibilité** |

**Décision** : le dash **ne donne pas** de gros boost de vitesse (GDD §13). Il sert à réorienter,
franchir, atteindre un mur. Si en playtest il paraît mou, augmenter `Dash_Distance` avant `SpeedRetention`.

---

## 9. Wall ride

| Clé | Valeur | Unité | Statut | Note |
|---|---|---|---|---|
| `WallRide_MinEntrySpeed` | 1200 | uu/s | À CALIBRER | |
| `WallRide_MaxDuration` | 2.0 | s | À CALIBRER | |
| `WallRide_MaxWallAngle` | 20 | ° | À CALIBRER | écart max à la verticale |
| `WallRide_DetectDistance` | 70 | uu | À CALIBRER | trace latérale depuis la capsule |
| `WallRide_GravityScale` | 0.25 | ×G | À CALIBRER | glisse lente vers le bas |
| `WallRide_SpeedRetention` | 0.98 | ratio/s | À CALIBRER | quasi aucune perte |
| `WallRide_UpwardBoost` | 250 | uu/s | À CALIBRER | petite montée à l'accroche |
| `WallJump_ZVelocity` | 800 | uu/s | À CALIBRER | |
| `WallJump_AwayVelocity` | 700 | uu/s | À CALIBRER | poussée perpendiculaire au mur |
| `WallJump_ForwardBoost` | 300 | uu/s | À CALIBRER | gain dans l'axe du regard |
| `WallRide_SameWallCooldown` | 0.6 | s | À CALIBRER | empêche de camper un seul mur |
| `WallRide_CameraTilt` | 12 | ° | À CALIBRER | roulis vers l'extérieur |
| `WallRide_TraceInterval` | 0.03 | s | À CALIBRER | fréquence des traces de détection (~33 Hz), timer et non Tick |

Surfaces éligibles : object type **`WallRideSurface`** (cf. `Docs/06_CONVENTIONS.md §7`).
Pas de wall ride sur les props ni sur les ennemis.

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
| — | — | — | — | *(à remplir dès le premier playtest)* | — |
