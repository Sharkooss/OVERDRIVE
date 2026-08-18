# PALETTE — OVERDRIVE

> **v2 — 2026-08-18.** Refonte complète suite au changement de DA :
> on passe d'une ville néon nocturne à une **ville lumineuse en plein jour**.
> Cette palette prime sur toute autre source de couleur, y compris les specs.
>
> Référence : `KEYART_REF_02.png` (à déposer dans ce dossier).
> Les tokens sont les noms à utiliser dans les `MI_`, les widgets et les `DA_World_*`.

---

## 1. Principe

Le monde est **clair, blanc, lumineux**. Les couleurs saturées sont **rares et signifiantes** :
elles ne décorent pas, elles **informent**.

```
Blanc / gris clair  = structure, sol, murs — le décor neutre
Violet              = signalétique, direction, « par ici »
Rouge / corail      = surface de traversée, vitesse
Magenta             = le joueur et ce qu'il projette
Orange              = tout ce qui est hostile
Navy profond        = silhouettes, contraste, UI
```

**Le fond est clair.** Toute information de gameplay doit donc être **foncée ou très saturée**
pour ressortir. C'est l'inverse de la contrainte de la v1 : ici, un élément blanc lumineux disparaît.

---

## 2. Palette de base

| Token | HEX | Rôle | Interdit |
|---|---|---|---|
| `OD_White_Structure` | `#EDEFF4` | Faces éclairées des bâtiments, sol, modules | Élément interactif |
| `OD_White_Pure` | `#FBFCFE` | Highlights, chevrons, texte sur fond foncé | — |
| `OD_Grey_Shadow` | `#C4CBDE` | Faces à l'ombre, faces latérales, profondeur | — |
| `OD_Grey_Deep` | `#9AA3BF` | Ombre portée, occlusion, éléments lointains | — |
| `OD_Navy_Deep` | `#2E2748` | Silhouette joueur, contours, fond d'UI | — |
| `OD_Navy_Ink` | `#1B1730` | Texte, outlines, ombre la plus dense | — |
| `OD_Purple_Primary` | `#7A4FC7` | **Signalétique directionnelle**, panneaux, chevrons | Décor sans fonction |
| `OD_Purple_Light` | `#A588E0` | Variante claire, signalétique secondaire | — |
| `OD_Magenta_Player` | `#E8336E` | **Joueur** : laser, dash, traînée, accents de tenue | Tout ce qui n'est pas le joueur |
| `OD_Red_Traversal` | `#F4453F` | **Surfaces de traversée** : wall ride, rails, boost | Décor sans fonction |
| `OD_Red_Danger` | `#C81E2E` | Danger, kill volume, attaque qui va toucher | Tout le reste |
| `OD_Amber_Enemy` | `#FF8A1F` | **Ennemis** : visière, émissif, projectile | Ce qui n'est pas hostile |
| `OD_Amber_Heat` | `#FFB020` | Jauge de chaleur, overheat, warning | — |
| `OD_Gold_Rank` | `#FFD24A` | Rank, coffre, récompense | — |
| `OD_Sky_Blue` | `#A8CDEF` | Ciel, brume atmosphérique lointaine | — |
| `OD_Sky_Pale` | `#DCEBFA` | Ciel à l'horizon, fog proche | — |
| `OD_Sun_Warm` | `#FFF6E0` | Lumière directionnelle, rim light chaud | — |

---

## 3. Couleurs réservées au gameplay

> **Règle dure.** Ces couleurs portent une information. Les employer comme décoration
> est un bug de lisibilité, pas une jolie image.

| Information | Token | Où on la voit |
|---|---|---|
| **Je peux courir dessus** (wall ride, rail, boost) | `OD_Red_Traversal` | bandes émissives au sol et sur les murs |
| **Va par là** | `OD_Purple_Primary` | chevrons `»`, panneaux, écrans |
| **C'est moi** (laser, dash, melee, traînée) | `OD_Magenta_Player` | tout ce qui émane du joueur |
| **C'est hostile** | `OD_Amber_Enemy` | visière ennemie, projectile, télégraphe |
| **Ça va me tuer** | `OD_Red_Danger` | kill volume, attaque imminente |
| **Ma chaleur** | `OD_Amber_Heat` | jauge, overheat |
| **Récompense** | `OD_Gold_Rank` | rank, coffre |

### Pourquoi l'ennemi est orange et pas rouge

Le rouge est pris par la traversée — c'est ce que montre la key art : les rails et les murs
de wall ride sont soulignés de rouge. L'orange est la seule teinte chaude restante qui :
- ressort violemment sur un fond blanc et bleu ciel,
- ne se confond ni avec le magenta du joueur ni avec le rouge des surfaces,
- reste distinguable du violet et du bleu du décor pour un deutéranope.

**À valider en playtest** : si orange et rouge se confondent en mouvement rapide,
le repli est `#00D9C0` (turquoise) — la seule teinte froide saturée absente du décor.

---

## 4. Ambiances par monde

Le décor reste blanc partout. **Ce qui change : le ciel, la lumière, et la couleur d'accent
de la signalétique.** Un `PDA_WorldData` par ambiance, poussé dans `MPC_Global` par `BP_LightingRig`.

| | World 1 — *Ascension* | World 2 — *Redline* | Boss 01 | Boss 02 |
|---|---|---|---|---|
| Ciel (zénith → horizon) | `#A8CDEF` → `#DCEBFA` | `#FFC8A8` → `#FFE8D4` | `#B8A8EF` → `#E4DCFA` | `#FF9A8A` → `#FFD4C4` |
| Structure | `#EDEFF4` | `#F0EAE6` | `#E8E4F4` | `#F4E6E2` |
| Ombre | `#C4CBDE` | `#D8C4BC` | `#BCB4D8` | `#D4B8B0` |
| Accent signalétique | `OD_Purple_Primary` | `OD_Magenta_Player`\* | `OD_Purple_Light` | `OD_Red_Danger` |
| Soleil | `#FFF6E0`, zénith | `#FFE0B0`, rasant | `#F0E8FF`, diffus | `#FFD0B0`, contre-jour |
| Fog density | 0.008 | 0.012 | 0.010 | 0.015 |

\* En World 2 la signalétique passe au magenta **et les accents du joueur passent au blanc pur**
pour rester distincts. C'est le seul cas où une couleur réservée change de main.
Il est documenté ici et nulle part ailleurs.

---

## 5. Raretés de loot

| Rareté | HEX | Note |
|---|---|---|
| Common | `#8A93AD` | gris-bleu neutre, volontairement terne |
| Rare | `#3AA8FF` | bleu franc — absent du décor, donc lisible |
| Epic | `#B14BFF` | violet saturé, plus intense que `OD_Purple_Primary` |

Aucune n'utilise le magenta, le rouge ni l'orange : ils sont réservés au gameplay.

## 6. Rangs

| Rang | HEX |
|---|---|
| `OD_Rank_D` | `#8A93AD` |
| `OD_Rank_C` | `#7FC6A0` |
| `OD_Rank_B` | `#3AA8FF` |
| `OD_Rank_A` | `#FFD24A` |
| `OD_Rank_S` | `#E8336E` |

Le S reprend le magenta du joueur : c'est le rang « tu as joué comme le jeu le voulait ».

---

## 7. UI sur fond clair

Le monde est lumineux : **une UI claire disparaît**. Règle inversée par rapport à la v1.

- Fond de panneau plein écran : `OD_Navy_Deep` à **92 %** d'opacité
- Texte principal : `OD_White_Pure` · Texte secondaire : `OD_Grey_Shadow`
- Bordures : `OD_Magenta_Player`, 1 à 2 px
- Éléments de HUD **sans panneau** (heat, speed, style, vies) : tracés en `OD_Navy_Ink`
  avec un **halo blanc de 2 px**, pour rester lisibles devant un mur blanc comme devant le ciel.
- Crosshair : `OD_Navy_Ink` bordé de blanc. **Jamais magenta** — il se confondrait avec le laser.

---

## 8. Saisir ces couleurs dans UE5

Les HEX ci-dessus sont en **sRGB**.

1. Color picker → onglet **Hex sRGB**, coller la valeur. UE convertit en linéaire tout seul.
2. Dans un Material : `Constant3Vector` → ouvrir son picker → coller le HEX sRGB.
   **Ne jamais saisir les composantes RGB à la main** : elles sont linéaires, la couleur sortira délavée.
3. Pour un émissif, la couleur ne change pas — c'est l'`EmissiveIntensity` qui varie :
   `1.0` décor · `3.0` signalétique · `8.0` surfaces de traversée · `15.0` laser et VFX.
4. Les tokens vivent dans `MPC_Global` et `DA_UITokens`. **Jamais en dur** dans un widget
   ou un matériau : un changement de palette doit se faire en un seul endroit.
