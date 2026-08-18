---
description: Rituel de fin de journée — roadmap, tuning, journal, commit
---

Exécute le rituel de fin de journée d'OVERDRIVE (`Docs/10_DEFINITION_OF_DONE.md §7`).

1. **Roadmap** — Relis notre conversation d'aujourd'hui et coche dans `Docs/04_ROADMAP.md`
   ce qui a réellement été terminé. Une case ne se coche que si les critères de
   `Docs/10_DEFINITION_OF_DONE.md §1` sont remplis. En cas de doute, laisse `[~]`.

2. **Tuning** — Reporte dans `Docs/07_TUNING.md §18` toute valeur modifiée aujourd'hui
   (clé, ancien, nouveau, raison). Si une valeur a été validée en jeu par Louis,
   passe-la de `[À CALIBRER]` à `[VALIDÉ]`.

3. **Specs** — Si le comportement implémenté diverge de la spec, corrige la spec.
   La doc doit refléter le jeu, pas l'intention.

4. **Journal** — Crée `Docs/Journal/AAAA-MM-JJ.md` à partir de `Docs/Journal/TEMPLATE.md`,
   rempli avec ce qui s'est réellement passé. Sois factuel, y compris sur ce qui a échoué.

5. **Contrôle** — Signale :
   - toute valeur en dur repérée dans un Blueprint aujourd'hui
   - toute contradiction entre deux documents
   - tout asset créé hors convention

6. **Commit** — Propose un message de commit au format `type(scope): message`
   (`Docs/06_CONVENTIONS.md §10`). **Ne commit pas sans mon accord.**

Termine par une ligne unique : `DEMAIN → <la première tâche de demain>`.
