# 09 — INPUT

> Enhanced Input (déjà actif dans le projet). Clavier / souris uniquement.
> Assets dans `Content/OVERDRIVE/Player/Input/`.

---

## 1. Mapping de référence

| Touche | Action | Input Action | Type de valeur | Trigger |
|---|---|---|---|---|
| `W A S D` | Déplacement | `IA_Move` | Axis2D | Down |
| `Souris` | Visée | `IA_Look` | Axis2D | Down |
| `LMB` | Laser | `IA_Fire` | Digital | **Pressed** (semi-auto, jamais Hold) |
| `RMB` | Melee | `IA_Melee` | Digital | Pressed |
| `Espace` | Saut | `IA_Jump` | Digital | Pressed + Released |
| `Maj gauche` | Sprint | `IA_Sprint` | Digital | Hold (option Toggle dans Settings) |
| `Ctrl gauche` | Slide | `IA_Slide` | Digital | Hold |
| `Souris 4` / `Q` | Dash | `IA_Dash` | Digital | Pressed |
| `R` | Restart rapide | `IA_Restart` | Digital | Hold 0.4 s |
| `Échap` | Pause | `IA_Pause` | Digital | Pressed |
| `F1` | Debug overlay | `IA_DebugToggle` | Digital | Pressed |

**Décision** : `Souris 4` **et** `Q` sont mappés sur `IA_Dash` simultanément.
Enhanced Input le permet nativement ; ça couvre les souris sans boutons latéraux sans coûter un réglage.

**`E` n'est pas mappé** : réservé à une éventuelle interaction future, laissé libre.

**Nommage** : l'action de debug s'appelle **`IA_DebugToggle`** (verbe en second, comme `IA_Restart`),
sur **`F1`**, dans `IMC_Debug` — cf. `11_ARBITRAGES D15`. `IA_ToggleDebug` n'existe pas.

---

## 2. Input Mapping Contexts

| Context | Priorité | Quand il est actif |
|---|---|---|
| `IMC_Gameplay` | 0 | Pendant le gameplay |
| `IMC_UI` | 10 | Menus, pause, écran de résultats, coffre |
| `IMC_Debug` | 20 | Toujours en build éditeur, retiré en Shipping |

**Règle** : à l'ouverture d'un menu, on **ajoute** `IMC_UI` et on **retire** `IMC_Gameplay`.
On ne se contente jamais de `Set Input Mode`.

---

## 3. Modificateurs & triggers

### `IA_Look`
- Modificateur : `Negate` sur Y (inversion optionnelle via Settings)
- Sensibilité gérée dans le `PC_Overdrive`, **pas** dans le modificateur — sinon elle n'est pas réglable à chaud
- Pas de Dead Zone (souris)

### `IA_Move`
- Modificateur : `Swizzle Input Axis Values` (`YXZ`) pour mapper W/S sur Y
- Pas de `Normalize` : la normalisation se fait dans `BPC_MovementState`, car l'air strafe
  a besoin du vecteur d'input brut (`WishDir`)

### `IA_Fire`
- **Trigger `Pressed` uniquement.** Le laser est semi-auto (GDD §19).
  Le cooldown est géré par `BPC_Heat` / `BP_LaserWeapon`, pas par le trigger.

### `IA_Sprint`
- Trigger `Hold` par défaut. Le mode Toggle est une option de Settings :
  le `PC_Overdrive` lit `Sprint_Mode` et interprète l'événement, on ne change pas l'asset.

### `IA_Slide`
- Trigger `Hold`. Relâcher termine le slide même si `Slide_MaxDuration` n'est pas écoulée.

### `IA_Restart`
- Trigger `Hold` **0.4 s** pour éviter les restarts accidentels en plein run (`11_ARBITRAGES D16`).
- Cible technique : **< 0.5 s** entre la mort et le retour en jouable (cf. `Restart_FadeDuration`, `Docs/07_TUNING.md §16`).

---

## 4. Flux d'input

```
PlayerInput
   ↓ Enhanced Input
PC_Overdrive           ← applique la sensibilité, l'inversion, le mode sprint
   ↓ appels d'API
BP_PlayerCharacter     ← ne fait QUE router vers le bon composant
   ↓
BPC_MovementState / BPC_Dash / BPC_Slide / BP_LaserWeapon / BPC_Melee
```

**Règle R-INPUT-1** : `BP_PlayerCharacter` ne contient **aucune logique de gameplay** liée à l'input.
Il reçoit l'événement et appelle `TryStartSlide()`, `TryDash()`, `Fire()`… Le composant décide s'il accepte.

**Règle R-INPUT-2** : chaque `Try*()` retourne un booléen et gère lui-même ses conditions
(cooldown, état, ressource). Aucun check de condition côté character.

---

## 5. Buffering

| Action | Buffer | Raison |
|---|---|---|
| `IA_Jump` | `Jump_BufferTime` (`Docs/07_TUNING.md §6`) | permet le bunny hop |
| `IA_Slide` | `Jump_BufferTime` (le **même** buffer) | un saut pressé pendant le slide se déclenche à la sortie |
| `IA_Dash` | aucun | doit rester une décision instantanée |
| `IA_Fire` | aucun | semi-auto, le spam ne doit pas être récompensé |

> **`Jump_BufferTime` et `Slide_JumpWindow` sont deux choses différentes** — ne pas les confondre :
> - **`Jump_BufferTime`** (`§6`) est un **buffer d'entrée** : « j'ai appuyé sur saut un peu trop tôt,
>   déclenche-le dès que c'est possible ». C'est le seul buffer, et il sert aussi bien à l'atterrissage
>   (bunny hop) qu'à la sortie de slide. `IA_Slide` n'a pas de buffer qui lui soit propre.
> - **`Slide_JumpWindow`** (`§5`) est une **fenêtre de conservation** : pendant 0.20 s *après* la fin
>   du slide, un saut conserve le boost de slide. C'est une règle de gameplay dans `BPC_Slide` /
>   `BPC_MovementState`, **pas** un mécanisme d'input.
>
> Autrement dit : le buffer décide **si** le saut part, la fenêtre décide **combien de vitesse** il garde.

Implémentation : un timestamp `LastPressedTime` par action bufferisée dans `BPC_MovementState`,
comparé à `Get Game Time in Seconds` au moment où la condition devient vraie.
**Pas de queue d'inputs.**

---

## 6. Rebind

**Hors MVP** (`Docs/03_SCOPE_LOCK.md §2`). Prévu uniquement si la semaine 4 est en avance.
Si implémenté : `Enhanced Input User Settings` (UE5.3+), pas de système maison.

Le mapping est conçu pour être jouable tel quel par un joueur de FPS PC standard —
c'est ce qui rend le rebind optionnel plutôt que bloquant.

---

## 7. Manette

**Non prévu.** Le dash 360° et l'air strafe supposent une précision souris.
Si la question revient : backlog post-v1.

---

## 8. Checklist de validation

- [ ] Toutes les `IA_*` créées avec le bon type de valeur
- [ ] `IMC_Gameplay` complet, priorités correctes
- [ ] Bascule `IMC_Gameplay` ↔ `IMC_UI` propre (pas de tir en ouvrant la pause)
- [ ] Sensibilité souris modifiable à chaud depuis les Settings
- [ ] Inversion Y fonctionnelle
- [ ] Mode sprint Hold **et** Toggle testés
- [ ] Dash déclenché par Souris 4 **et** Q
- [ ] Jump buffer perceptible : sauter juste avant d'atterrir enchaîne le hop
- [ ] Restart en `Hold` : impossible à déclencher par accident
- [ ] Aucun input bloqué après un écran de résultats ou un coffre
- [ ] `IMC_Debug` retiré en build Shipping
