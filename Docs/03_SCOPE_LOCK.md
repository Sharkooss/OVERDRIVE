# 03 — SCOPE LOCK

> **Ce document fait loi.** Il est plus important que l'enthousiasme.
> Verrouillé le **2026-08-18**. Toute modification doit être datée et signée dans §5.

---

## 0. Le test unique

Toute idée qui apparaît pendant le développement doit répondre **oui** à :

> **Est-ce que ça améliore directement le mouvement, le combat, le score, la progression ou le juice ?**

- **Non** → §4 « Backlog post-v1 ». On n'implémente pas.
- **Oui mais ça augmente fortement le scope** → §4 aussi.
- **Oui et c'est petit** → on discute, on chiffre, on décide.

**Le jeu doit être terminé avant d'être enrichi.**

---

## 1. DANS le scope (v1) — verrouillé

### Mouvement
Sprint · Jump · Slide · Dash 360° · Wall Ride · Bunny Hop · Air Strafing ·
système de vitesse continue · momentum · perte de vitesse sur erreur · coyote time · jump buffer

### Combat
Laser hitscan semi-auto · jauge de Heat · Overheat · Headshots · Melee · Knockback ·
dégâts d'impact mural (wall slam)

### Ennemis
**Exactement 3** : Grunt · Shooter · Tank
**Exactement 2 boss** : Boss 01 (fin World 1) · Boss 02 (final), 2 phases max chacun

### Progression
Score (temps + kills + vitesse + style) · Style multiplier · Rank D/C/B/A/S ·
Coffres par rank · Loot tables · Raretés Common/Rare/Epic · Upgrades **temporaires** ·
Run-based · **Système de 3 vies** (`Run_MaxLives`) · Mort = −1 vie + perte de temps et de score ·
0 vie = run perdue · upgrades conservés au sein d'une run, remis à zéro entre deux runs

### Contenu
**6 niveaux + 2 boss** · linéaires · 1–3 min · grands espaces · Safe Path / Speed Way ·
0–2 checkpoints par niveau

### Présentation
Low Poly Stylisé · Toon / Cel Shader · VFX · SFX · Musique · HUD minimal ·
Menu (Play / Settings / Quit) · Settings · Juice

### Technique
Unreal Engine 5.8 · **Blueprints uniquement** · PC Windows · développement solo ·
une seule sauvegarde : les **Settings**

---

## 2. HORS scope — interdit pendant les 4 semaines

| Interdit | Pourquoi |
|---|---|
| Nouvelles armes | Le combat repose sur 2 outils, c'est un choix de design |
| 4ᵉ archétype d'ennemi | Chaque ennemi coûte modèle + anim + IA + équilibrage |
| 3ᵉ boss | Un boss ≈ 1 journée pleine minimum |
| Multijoueur | Multiplie le coût de chaque système par 3 |
| Génération procédurale | Le level design est le cœur du score, il doit être authoré |
| Crafting / inventaire | Aucun rapport avec les piliers |
| Dialogues / lore / cinématiques | Aucun rapport avec les piliers |
| Méta-progression permanente | Explicitement reporté (GDD §52) |
| Système de quêtes | — |
| Open world | — |
| Sauvegarde de progression complexe | Une run tient en une session |
| Rareté Legendary | Complexifie la table de loot sans rien apporter |
| Gameplay Ability System | Sur-ingénierie pour 2 actions de combat |
| Common UI | Sur-ingénierie pour 4 écrans |
| Migration C++ | Contrainte technique assumée du projet |
| Refactor « pour faire propre » non demandé | Coût sans valeur joueur |
| Plugin marketplace | Sauf validation explicite de Louis |
| Rebind des touches | **Seulement si le temps le permet** (GDD §64) |
| Support manette | Non prévu. Le jeu est pensé clavier/souris |

---

## 3. Zone grise — à trancher par le playtest, pas par la théorie

| Feature | Statut | Critère de décision |
|---|---|---|
| **Melee comme outil de propulsion** | EXPÉRIMENTAL (GDD §26) | Si c'est fun ET implémentable en < 3 h → on garde. Sinon on supprime, zéro impact sur le reste |
| **Affichage km/h vs SPEED au HUD** | Décision reportée | Voir `Docs/07_TUNING.md §1`. Le HUD par défaut affiche `SPEED` |
| **Musique dynamique en couches** | Optionnel | MVP = pistes statiques. Couches seulement si la semaine 4 est en avance |
| **Double jump** | Écarté par défaut | Le dash remplit ce rôle. À rouvrir seulement si le wall ride s'avère trop dur |
| **i-frames sur le dash** | À 0 par défaut | Si les Shooters deviennent frustrants, ouvrir la clé `Dash_IFrames` |
| **Nombre de vies (3 ?)** | **Au scope**, valeur à calibrer | 3 morts pour 8 niveaux est sévère. Si le taux d'échec dépasse ~70 % en playtest : passer à 5, ou recharger 1 vie à chaque boss vaincu |
| **Personnage complet visible** | Bras FP uniquement au MVP | La key art montre un personnage entier. Le modéliser + l'animer = 2 à 3 jours. Post-v1 (cf. `11_ARBITRAGES D32`) |
| **Ragdoll vs dissolve à la mort** | Tranché : **dissolve** | Voir `Docs/Specs/SPEC_ENEMIES.md §8` |
| **Motion blur** | OFF par défaut, option disponible | Voir `Docs/Specs/SPEC_CAMERA_JUICE.md §7` |

---

## 4. Backlog post-v1

> Les bonnes idées ne sont pas jetées, elles sont **datées et rangées**.
> Écrire ici est un acte de discipline, pas un abandon.

| Date | Idée | Origine | Pilier concerné |
|---|---|---|---|
| 2026-08-18 | Grappin / crochet | GDD (implicite) | Movement |
| 2026-08-18 | Armes alternatives (shotgun, railgun) | GDD §69 | Combat |
| 2026-08-18 | Méta-progression permanente | GDD §52 | Progression |
| 2026-08-18 | Leaderboards / ghosts / replays | — | Score |
| 2026-08-18 | Mode Time Attack sur niveau isolé | — | Score |
| 2026-08-18 | Rareté Legendary + upgrades qui changent une règle | GDD §45 | Progression |
| 2026-08-18 | Support manette + rebind complet | GDD §64 | Confort |
| 2026-08-18 | Musique adaptative multi-couches | GDD §59 | Juice |
| 2026-08-18 | World 3 / niveaux supplémentaires | GDD §4 | Contenu |
| 2026-08-18 | Melee propulsif si écarté du MVP | GDD §26 | Movement |
| 2026-08-18 | Personnage jouable complet + vue 3ᵉ personne optionnelle | Key art v2 | Présentation |
| 2026-08-18 | Vie supplémentaire comme loot Epic rare | Système de vies (D31) | Progression |

---

## 5. Journal des modifications de scope

| Date | Modification | Raison | Impact planning |
|---|---|---|---|
| 2026-08-18 | Verrouillage initial | Préproduction | — |
| 2026-08-18 | **+ Système de 3 vies** | Arbitrage de Louis : il manquait une condition de défaite | ~2 h (compteur + HUD + écran `Run Failed`) |
| 2026-08-18 | **Changement de DA** : ville blanche en plein jour | Nouvelle key art validée | Rendu éclairé au lieu d'Unlit. Neutre en jours, mais déplace le risque perf |

---

## 6. Ordre de sacrifice

Si le planning dérape, on coupe **par la fin de cette liste**, jamais par le début.

```
1. Movement       ← ne se coupe JAMAIS
2. Laser
3. Enemy
4. Level
5. Score
6. Juice
7. Loot
8. Boss
9. Menus
10. Extras        ← se coupe en premier
```

### Paliers de repli déjà décidés

| Palier | Contenu livré | Quand on y bascule |
|---|---|---|
| **Full** | 6 niveaux + 2 boss | Tout va bien |
| **Repli 1** | 6 niveaux + 1 boss | Fin de semaine 4 sans Boss 02 jouable |
| **Repli 2** | 4 niveaux + 1 boss | Fin de semaine 3 sans le vertical slice complet |
| **Repli 3** | 3 niveaux + 0 boss, mais **poli** | Fin de semaine 3 avec le core encore instable |
| **Stop** | 1 niveau + movement + combat | Si le MVP n'est **pas fun** (cf. `Docs/10_DEFINITION_OF_DONE.md §3`) |

**Un jeu court et poli bat un jeu long et mou.** Trois niveaux excellents valent mieux que six moyens.
