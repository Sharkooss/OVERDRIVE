# 10 — DEFINITION OF DONE & TESTS DE VALIDATION

---

## 1. Une feature est FINIE si et seulement si

- [ ] **Elle fonctionne** dans le jeu, pas seulement dans le graph
- [ ] **Elle est compréhensible** sans explication par un joueur qui la découvre
- [ ] **Elle a un feedback** — visuel, sonore, ou les deux
- [ ] **Elle ne crée pas de bug majeur**
- [ ] **Elle fonctionne avec les autres systèmes** (matrice d'interactions testée)
- [ ] **Elle a été testée en situation réelle**, pas dans une boîte vide
- [ ] **Le Blueprint compile sans warning**
- [ ] **Ses valeurs sont dans `Docs/07_TUNING.md`**, aucune valeur en dur
- [ ] **La spec est à jour** si le comportement réel a divergé
- [ ] **Le journal est renseigné** (`Docs/Journal/`)

> **« Le Blueprint fonctionne » ≠ « la feature est terminée ».**

---

## 2. La règle de production

```
        Prototype
            ↓
          Test
            ↓
     C'est fun ?
        ↙       ↘
      OUI       NON
       ↓         ↓
    Polish   Modifier ou SUPPRIMER
```

**Ne jamais produire un système complet avant d'avoir vérifié qu'il est amusant.**
Supprimer une feature qui ne fonctionne pas n'est pas un échec, c'est la méthode.

---

## 3. Les 8 tests de validation du jeu

> Ces tests se passent **manche en main**, pas sur le papier.
> Si plusieurs réponses sont NON : **on n'ajoute aucun contenu**, on corrige le core.

| # | Test | Quand | Réponse | Date |
|---|---|---|---|---|
| **1** | Le joueur joue 5 minutes sans aucun contenu. Le mouvement est-il amusant ? | Gate S1 | ✅ **OUI** — 5 min jouées par Louis, « sans souci », avec sprint + saut + air strafe seuls | 2026-08-19 (J3) |
| **2** | Peut-il atteindre une vitesse élevée en maîtrisant plusieurs mécaniques ? | Gate S1 | ✅ **OUI** — validé sur les **6** mécaniques (sprint, saut, air strafe, slide, dash, wall ride) après le retune du momentum à `800 / 0.25` : « tout marche correctement ». *Pic de vitesse non relevé — à chiffrer au premier passage de score (J18).* | 2026-08-19 (J7) |
| **3** | Est-il plus intéressant de tuer un ennemi en mouvement que de s'arrêter ? | Gate S2 | | |
| **4** | Un headshot procure-t-il une vraie satisfaction ? | Gate S2 | ✅ **OUI** — hitmarker à 3 paliers, hit-stop 0.06 s et `S_Laser_Hit_Head_01` joués manche en main : « c'est good, j'ai testé, ça me convient ». Les trois retours (visuel / temporel / sonore) sont livrés au J10bis + J11 | 2026-08-21 |
| **5** | Un impact ennemi fait-il réellement *ressentir* une erreur ? | Gate S2 | | |
| **6** | Le joueur comprend-il pourquoi il obtient A plutôt que S ? | Gate S3 | | |
| **7** | Le loot donne-t-il envie de continuer ? | Gate S3 | | |
| **8** | Le joueur veut-il **immédiatement** recommencer un niveau pour améliorer son temps ? | Gate S3 | | |

### Gates de fin de semaine

**🚦 GATE SEMAINE 1 — le mouvement** → ✅ **PASSÉE le 2026-08-19**
Tests 1 et 2 doivent passer. Si non : **on ne commence pas le combat.** On reste sur le mouvement.
C'est le seul système dont l'échec justifie de tout arrêter (`Docs/03_SCOPE_LOCK.md §6`, palier Stop).

> **Passée avec 6 mécaniques et non 7** : le bunny hop a été construit, mesuré, puis **coupé au J7**
> sur le feeling (`D52`, `07_TUNING §6`). Le gain de vitesse au-dessus du sprint cap est l'affaire du
> seul air strafe, complété par le slide en pente, le dash et le wall ride.
> **La semaine 2 (combat) est débloquée.**

**🚦 GATE SEMAINE 2 — le combat**
Tests 3, 4, 5. Le joueur doit pouvoir enchaîner :
`courir → tirer → headshot → melee → projeter un ennemi → dash → wall ride → continuer`
sans que la chaîne se casse.

**🚦 GATE SEMAINE 3 — la boucle**
Tests 6, 7, 8. Le jeu doit se jouer **du début à la fin** : niveau → score → rank → coffre → upgrade → boss.
Incomplet mais entier.

**🚦 GATE FINALE — le critère de qualité**
Le joueur doit pouvoir faire cette séquence **et avoir la sensation d'avoir accompli quelque chose** :
```
Sprint → Slide → Jump → Air Strafe → Wall Ride → Dash
      → Laser Headshot → Melee → Enemy Knockback
      → Speed Recovery → Wall Ride → Finish
```

---

## 4. Ordre de priorité du polish

```
1. Movement          6. Level design
2. Combat            7. UI
3. Audio             8. Art secondaire
4. VFX               9. Optimisation
5. Camera           10. Bugs mineurs
```

**L'audio est en 3ᵉ position, pas en dernière.** C'est un pilier (`Docs/01_VISION.md §3`).

---

## 5. Definition of Done — par type de livrable

### Un niveau est fini si
- [ ] Il se termine sans blocage possible
- [ ] Durée première completion entre 90 et 180 s
- [ ] Au moins 2 espaces de vitesse et 2 sections de combat
- [ ] Au moins une bifurcation Safe Way / Speed Way
- [ ] Les seuils de rank sont calibrés (`PDA_LevelData`)
- [ ] Un S Rank a été atteint **au moins une fois** par Louis
- [ ] Aucune arête qui accroche à 4000 uu/s
- [ ] Aucun endroit où le joueur perd sa vitesse sans comprendre pourquoi
- [ ] Kill volume sous tout le niveau
- [ ] 60 fps stable

### Un ennemi est fini si
- [ ] Il est reconnaissable en 0.2 s à 3000 uu/s
- [ ] Son TTK respecte la cible (`Docs/07_TUNING.md §13`)
- [ ] Il a un télégraphe visible avant chaque attaque
- [ ] Il a hit reaction, VFX et SFX de mort
- [ ] Il réagit au knockback et au wall slam
- [ ] Ses stats sont dans son `DA_Enemy_*`, pas dans le BP
- [ ] Il se désactive hors de portée

### Un boss est fini si
- [ ] 2 phases maximum
- [ ] Chaque attaque a un télégraphe lisible et une parade par une mécanique de mouvement
- [ ] Le combat dure environ `Boss_TargetFightDuration`
- [ ] Il est battable sans aucune upgrade
- [ ] Il n'est pas trivialisable avec toutes les upgrades

### Le juice est fini si
- [ ] Chaque action de la table de feedback (`SPEC_COMBAT §10`) a son VFX **et** son SFX
- [ ] Aucun son placeholder ne reste
- [ ] Le shake ne gêne jamais la lisibilité
- [ ] Les options de confort existent (shake, FOV, motion blur, speed lines)

---

## 6. Ce qui doit rester vrai en permanence

| Invariant | Comment le vérifier |
|---|---|
| 60 fps stable | `stat unit` en jeu, sur le niveau le plus chargé |
| Zéro warning de compilation | Recompiler tous les BP avant chaque fin de journée |
| Restart quasi instantané | Chronométrer mort → jouable : < 1 s |
| Aucune valeur en dur | Recherche de nombres magiques dans les BP |
| Le scope n'a pas bougé | Relire `Docs/03_SCOPE_LOCK.md` chaque lundi |
| La doc reflète le jeu | Toute divergence est un bug de doc |

---

## 7. Rituel de fin de journée (10 min)

1. Recompiler tous les Blueprints — zéro warning
2. Jouer 3 minutes le niveau le plus avancé
3. Cocher la roadmap (`Docs/04_ROADMAP.md`)
4. Écrire l'entrée du jour (`Docs/Journal/`)
5. Reporter dans `Docs/07_TUNING.md §18` toute valeur modifiée
6. Commit

---

## 8. Le signal d'arrêt

> **Si le MVP n'est pas fun, ne pas continuer à produire du contenu.**

Le MVP = movement + sprint + jump + slide + dash + wall ride + air strafe + laser + heat + melee
+ 1 ennemi + 1 niveau + timer + score + rank + restart.

S'il n'est pas fun : on revient sur le mouvement. Autant de temps qu'il faut.
Ajouter du contenu par-dessus un core qui ne fonctionne pas ne fait que rendre le problème plus cher à corriger.
