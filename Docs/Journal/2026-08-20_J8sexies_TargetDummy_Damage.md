# Journal — 2026-08-20 — J8 sexies : les cibles encaissent le laser

**Temps effectif** : ~1 h 30 (agent)
**Objectif du jour (roadmap)** : dernière ligne ouverte du J8 — `BP_TargetDummy` doit implémenter
`BPI_Damageable` pour de vrai. Les graphes existaient et étaient **vides**.

---

## Fait

Un seul asset touché côté logique : **`/Game/OVERDRIVE/Dev/Sandbox/BP_TargetDummy`**.
Rien n'a été modifié côté arme — `BP_LaserWeapon.ProcessHit` appelait déjà `ApplyDamage` correctement.

### Graphes écrits (comptes de nœuds avant → après)

| Graphe | Avant | Après | Contenu |
|---|---|---|---|
| `EventGraph` | 3 | **5** | `EventBeginPlay → SetCurrentHealth(GetMaxHealth)`. Les 3 nœuds « avant » sont les events fantômes désactivés du template d'Actor (`BeginPlay`, `ActorBeginOverlap`, `Tick`) : le writer a **réutilisé** celui de `BeginPlay` au lieu d'en créer un second (`12_PIEGES §2.27`). `bCanEverTick` relu à **`false`** après compilation — le nœud `Tick` fantôme n'active rien. |
| `ApplyDamage` | 2 | **25** | voir ci-dessous |
| `IsAlive` | 2 | **5** | `return CurrentHealth > 0` |
| `GetHealthRatio` | 2 | **5** | `return SafeDivide(CurrentHealth, MaxHealth)` |

### `ApplyDamage` — la chaîne d'exec réelle, telle que relue

```
Entry
 └─ Branch  (CurrentHealth <= 0)                       ← garde anti double-kill, EN PREMIÈRE LIGNE
     ├ true  → Return (false, 0.0)
     └ false → Branch (Clamp(CurrentHealth - Amount, 0, MaxHealth) <= 0)
                ├ true  → SetCurrentHealth(0.0) → DestroyActor(self) → Return (true, Amount)
                └ false → SetCurrentHealth(NewHealth) → DrawDebugSphere(HitLocation…) → Return (false, Amount)
```

Trois `ReturnNode`, **tous atteints** : le piège `2.11` (« un `if` termine le flux ») est traité en
plaçant un `(return …)` en fin de chaque branche, pas en mettant l'`if` en dernier.

Audit d'accessibilité **exec** (racine = sortie `Exec` sans entrée `Exec`, `12_PIEGES §2.31`) :
**25 nœuds vivants, 0 mort, 1 seule racine** (`K2Node_FunctionEntry_0`). Idem sur les 3 autres graphes.

### Les deux points où ça aurait pu casser en silence

1. **Lecture après écriture (`2.3b` / `2.3c`).** `CurrentHealth` n'est lue qu'**une fois**, par un seul
   `K2Node_VariableGet_0` qui alimente à la fois la comparaison de la garde et la soustraction. Les deux
   `Set` sont en **fin** de leurs branches respectives et le second `Branch` les précède tous les deux
   dans la chaîne d'exec : aucune relecture ne traverse un `Set`. Le `Set` de la branche létale écrit un
   **littéral `0.0`**, pas une expression relue.
2. **Pins GUID du `Break S_DamageInfo` (`2.29`).** Sondés avant écriture, indices confirmés :
   `0 = Amount_16_211B3B…`, `1 = Type_17_…`, **`2 = HitLocation_18_E4F7FF…`**, 3 `HitNormal`,
   4 `HitBone`, 5 `Instigator`, 6 `KnockbackImpulse`, 7 `SpeedPenaltyPercent`. Relecture après écriture :
   `Break#0` alimente la soustraction **et** les deux `DamageApplied`, `Break#2` alimente le `Center`
   de la sphère. Aucun nœud intercalé nulle part, tous les `self` alimentés directement (`2.21`).

### Retour visuel (provisoire, remplacé au J14)

Sphère de debug au `DamageInfo.HitLocation` à chaque impact **non létal**, en `OD_Magenta_Player` —
la même teinte exacte que le faisceau. À la mort : `DestroyActor`, qui est déjà un signal fort.
Aucune valeur en dur : 5 variables `Instance Editable` catégorie `Debug`, reportées dans
`07_TUNING §16 > Debug du tir — côté cible`.

## Pas fait / reporté

- `ApplyKnockback` : ignorée volontairement, c'est le **J11**. Elle n'a pas de sortie, donc l'éditeur
  l'expose en event et pas en fonction — elle n'apparaît pas dans `list_graphs`, c'est normal.
- Aucun VFX/SFX d'impact : c'est le J14. La sphère de debug est un échafaudage assumé.

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| Garde `bIsDead` de `SPEC_COMBAT §13-9` transposée en `if (CurrentHealth <= 0) return (false, 0)` — le dummy n'a pas de `BPC_Health` | `SPEC_COMBAT §8` (note « Écarts constatés ») |
| `GetHealthRatio` protégée par `Math\|Float\|SafeDivide` plutôt qu'un `Branch` : pur, sans warning « divide by zero », et compatible si Louis coche `Pure` un jour | `SPEC_COMBAT §8` |
| `GetHealthRatio` est déclarée **impure** dans l'asset `BPI_Damageable` alors que la spec l'annote `[pure]` — signalé, **pas corrigé** (flag non outillable, `12_PIEGES §5.3`) | `SPEC_COMBAT §8` |
| `TargetDebug_HitSphereSegments` exposée en variable alors que 12 est le défaut du pin — pour ne laisser **aucune** valeur sur un défaut de pin (R3, et souvenir de `6.18`) | `07_TUNING §16` |

## Valeurs modifiées

Aucune valeur existante de `07_TUNING` n'a été touchée. **5 clés neuves**, toutes `[À CALIBRER]` :

| Clé | Valeur | Unité |
|---|---|---|
| `TargetDebug_HitSphereRadius` | 25 | uu |
| `TargetDebug_HitSphereDuration` | 0.25 | s |
| `TargetDebug_HitSphereThickness` | 2.0 | px |
| `TargetDebug_HitSphereSegments` | 12 | — |
| `TargetDebug_HitSphereColor` | `(0.910, 0.200, 0.431, 1.0)` | LinearColor |

## Vérification en PIE (relevé brut)

Échafaudage : `IMC_Debug` + touche **F4 → `IA_Fire`** (recette `12_PIEGES §4.11`),
`GameGetsMouseControl = true`. Spawn `(0, −3000, 300)`, `yaw = −63.435°`, `pitch = −1.588°` —
angle calculé pour viser `TargetDummy_Flat_01` à `(1000, −5000, 90)`, soit 2236 uu de distance.
Le regard ne se pilote pas par outil (`12_PIEGES §4.15`), seul le yaw de spawn est un levier.

| Étape | Mesure |
|---|---|
| `BeginPlay` | `CurrentHealth = 100` sur les **7** instances du monde `UEDPIE_` |
| Tir 1 | `TargetDummy_Flat_01` : **100 → 66** |
| Tir 2 | **66 → 32** |
| Tir 3 | **cible détruite** — `find_actors` renvoie 6 au lieu de 7 |
| Les 6 autres | `CurrentHealth = 100`, intactes |

`100 − 66 = 34` et `66 − 32 = 34` : exactement `Laser_Damage_Body`, **une fois** par tir — donc pas de
multi-hit et la garde anti double-kill n'a pas été sollicitée à tort.
Sphère d'impact confirmée **à l'image** (capture de la fenêtre PIE, `TargetDebug_HitSphereDuration`
montée à 30 s le temps de la capture puis remise à 0.25 et revérifiée).

Échafaudage **restauré et revérifié clé par clé** : `IMC_Debug` byte-identique à la sauvegarde
(1 seul mapping, `F3 → IA_DebugToggle`), `gameGetsMouseControl = false`, durée de sphère à 0.25 sur
les 7 instances. `IMC_Debug` n'apparaît pas dans `git status` : le scaffold n'a jamais touché le disque.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| **Les 5 variables neuves valaient `0` sur les 7 instances placées** alors que le CDO était parfait — soit rayon nul et durée 0 (donc 1 s de traînée, `6.18`) | 🔴 | Oui — écriture sur chaque instance + sauvegarde du niveau. Nouvelle entrée **`12_PIEGES §5.34`** |

Rien d'autre. Aucun empilement DSL (`2.2b`) : les comptes avant/après collent nœud pour nœud sur les
4 graphes, et les sondes `get_node_type_pins` n'ont laissé **aucun** nœud orphelin (2/2/2 avant, 2/2/2
après 5 sondes — confirme la nuance de `2.12`).

## Demain

- **Playtest de Louis** — la feature n'est pas finie tant qu'il n'a pas tiré en courant (R8/R10).
  **Rien n'est commité.**
- Puis J9 — `BPC_Heat`, et `BPC_Health` côté ennemi (qui reprendra cette logique proprement).

---

## Vérifications de fin de journée

- [x] `BP_TargetDummy` recompilé, zéro warning (`warnings_as_errors = True`)
- [x] `BP_TargetDummy` + `L_Sandbox_Movement` sauvegardés (`save_assets`)
- [ ] 3 minutes de jeu réel — **en attente de Louis**
- [x] Roadmap cochée
- [x] Tuning à jour (`§16`)
- [x] Nouveau piège consigné (`§5.34`)
- [ ] Commit fait — **volontairement pas fait (R10)**
