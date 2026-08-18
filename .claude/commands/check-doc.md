---
description: Audite la cohérence de la documentation — contradictions, valeurs orphelines, liens morts
---

Audite la documentation d'OVERDRIVE. **Tu ne modifies rien**, tu rapportes.

Vérifie :

1. **Contradictions entre documents.** Applique la hiérarchie d'autorité de `Docs/00_INDEX.md`.
   Cherche en particulier : noms d'assets divergents entre `05_ARCHITECTURE.md` et les `Specs/`,
   signatures d'interface, noms de structs/enums vs `08_DATA_SCHEMAS.md`.

2. **Valeurs orphelines.** Toute clé référencée dans une `Specs/SPEC_*.md` qui n'existe pas
   dans `Docs/07_TUNING.md`. Et l'inverse : les clés de tuning que plus aucune spec n'utilise.

3. **Valeurs en dur dans la doc.** Tout nombre de gameplay écrit ailleurs que dans `07_TUNING.md`
   sans renvoi vers celui-ci (les valeurs UI/audio/VFX purement cosmétiques sont tolérées).

4. **Liens morts.** Tout chemin de fichier cité dans un doc qui n'existe pas sur le disque.

5. **Scope.** Toute feature décrite dans une spec qui n'apparaît pas dans `03_SCOPE_LOCK.md §1`.

6. **Conventions.** Tout nom d'asset cité dans la doc qui viole `06_CONVENTIONS.md §2`.

Rapporte au format :

```
🔴 BLOQUANT   <empêche d'implémenter — contradiction ou valeur manquante>
🟠 À CORRIGER <incohérence sans blocage immédiat>
🟡 À SURVEILLER <dette de doc>
✅ RAS        <ce qui a été vérifié et est propre>
```

Pour chaque point : le fichier, la ligne, et la correction proposée en une phrase.
Termine par le nombre total de problèmes par catégorie. Si tout est propre, dis-le franchement.
