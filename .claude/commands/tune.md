---
description: Modifie une valeur de tuning proprement — doc, asset, historique
argument-hint: <clé> <nouvelle valeur> [raison]
---

Modifie la valeur de tuning demandée : **$ARGUMENTS**

Procédure obligatoire, dans cet ordre :

1. **Trouve la clé** dans `Docs/07_TUNING.md`. Si elle n'existe pas, arrête-toi et dis-le —
   ne crée pas une clé silencieusement.
2. **Vérifie les dépendances** : cherche cette clé dans `Docs/Specs/` et signale tout endroit
   où elle intervient dans une formule ou une contrainte de level design.
   Exemple : changer `Jump_ZVelocity` invalide les métriques de `SPEC_LEVELDESIGN §2`.
3. **Modifie la valeur** dans `Docs/07_TUNING.md`.
4. **Ajoute une ligne** dans `Docs/07_TUNING.md §18` (date, clé, ancien, nouveau, raison).
5. **Dis-moi quel DataAsset ou variable** doit être mis à jour dans l'éditeur
   (`DA_Movement_Default`, `DA_Weapon_Laser`, `DA_Enemy_*`…). Si l'éditeur UE est ouvert,
   propose de le faire via `unreal-mcp`.
6. **Si des métriques dérivées changent** (portée de saut, distance de wall ride…),
   recalcule-les et mets à jour `Docs/Specs/SPEC_LEVELDESIGN §2`.

Termine par :
```
IMPACT   <ce qui doit être re-testé en jeu suite à ce changement>
```
