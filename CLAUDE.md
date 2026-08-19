# OVERDRIVE — Instructions Agent

> **Lis ce fichier en entier avant toute action. Il est court exprès.**
> Tout le reste est dans `Docs/`. Ne fouille pas le projet pour comprendre : la doc fait autorité.

---

## 1. Le projet en 5 lignes

FPS arcade solo, UE 5.8, **100 % Blueprints**, développé par **une seule personne** en **~20 h/semaine sur 4 semaines**.
Le joueur traverse des niveaux linéaires courts (1–3 min) à très haute vitesse en enchaînant
sprint / slide / dash 360° / wall ride / bunny hop / air strafe, tue des ennemis au laser hitscan
et au melee à knockback, puis reçoit un **score → rank (D→S) → coffre → upgrades temporaires**.
Une run = 6 niveaux + 2 boss. **Les upgrades se gardent au sein d'une run, jamais entre deux runs.
3 vies : à la 3ᵉ mort la run est perdue** (`Docs/11_ARBITRAGES.md D1`).

**La phrase qui tranche tous les arbitrages : le jeu doit être FUN À CONTRÔLER.**

---

## 2. Où trouver l'info (ne devine jamais)

| Besoin | Fichier |
|---|---|
| Vue d'ensemble / point d'entrée | `Docs/00_INDEX.md` |
| Vision, piliers, ton | `Docs/01_VISION.md` |
| GDD complet de référence | `Docs/02_GDD.md` |
| Ce qui est DANS / HORS scope | `Docs/03_SCOPE_LOCK.md` |
| Planning jour par jour | `Docs/04_ROADMAP.md` |
| Arborescence Blueprint, qui possède quoi | `Docs/05_ARCHITECTURE.md` |
| Nommage assets, dossiers, variables | `Docs/06_CONVENTIONS.md` |
| **Toutes les valeurs numériques** | `Docs/07_TUNING.md` |
| Enums, Structs, DataTables, DataAssets | `Docs/08_DATA_SCHEMAS.md` |
| Inputs & Enhanced Input | `Docs/09_INPUT.md` |
| Definition of Done + tests de validation | `Docs/10_DEFINITION_OF_DONE.md` |
| **Arbitrages tranchés** (à respecter sans discuter) | `Docs/11_ARBITRAGES.md` |
| **Pièges d'outillage & erreurs déjà commises** | `Docs/12_PIEGES_OUTILLAGE.md` |
| Spec détaillée d'un système | `Docs/Specs/SPEC_*.md` |
| Direction artistique + palette | `Docs/Specs/SPEC_ART_DIRECTION.md` + `Docs/ArtDirection/` |
| Journal de dev | `Docs/Journal/` |

---

## 3. Règles non négociables

### R1 — Blueprint only
Aucun C++. Aucune création de module C++, aucun `.cpp/.h`. Si une feature semble impossible en BP,
propose une alternative BP ou signale-le, ne bascule pas en C++ de ta propre initiative.

### R2 — Le scope est verrouillé
`Docs/03_SCOPE_LOCK.md` fait loi. Toute idée nouvelle doit passer le test :
> *Est-ce que ça améliore directement le mouvement, le combat, le score, la progression ou le juice ?*

Si non → tu l'écris dans `Docs/03_SCOPE_LOCK.md` section « Backlog post-v1 » et **tu ne l'implémentes pas**.
Tu ne rajoutes jamais d'arme, d'ennemi, de système ou de menu non listé.

### R3 — Aucune valeur en dur dans un Blueprint
Toutes les valeurs de gameplay vivent dans `Docs/07_TUNING.md` et sont exposées via
DataAssets / variables `Instance Editable` + `Category`. Si tu as besoin d'un nombre :
1. Cherche-le dans `Docs/07_TUNING.md`.
2. S'il n'y est pas, ajoute-le au doc **avec la mention `[À CALIBRER]`**, puis utilise-le.
3. Ne change jamais une valeur du doc sans mettre à jour le doc.

### R4 — Prototype avant polish
```
Prototype → Test en jeu → C'est fun ? → oui: polish / non: modifier ou supprimer
```
Ne produis jamais un système complet avant d'avoir vérifié qu'il est amusant.
« Le Blueprint compile » ≠ « la feature est finie ». Voir `Docs/10_DEFINITION_OF_DONE.md`.

### R5 — Ordre de priorité en cas de retard
`Movement > Laser > Enemy > Level > Score > Juice > Loot > Boss > Menus > Extras`
On coupe par la fin, jamais par le début.

### R6 — Conventions de nommage strictes
Voir `Docs/06_CONVENTIONS.md`. Tout asset créé hors convention est un bug.
Tout nouveau contenu va dans `Content/OVERDRIVE/`, jamais à la racine de `Content/`.

### R7 — Tu documentes ce que tu fais
Après toute implémentation significative :
- coche la ligne correspondante dans `Docs/04_ROADMAP.md`
- ajoute une entrée dans `Docs/Journal/` (copie `Docs/Journal/TEMPLATE.md`)
- mets à jour la spec concernée si le comportement réel diffère de la spec

### R8 — Tu ne peux pas tester le feeling
Tu peux implémenter, compiler, vérifier la logique. **Tu ne peux pas juger si c'est fun.**
Termine toujours une feature de gameplay par une **liste de vérification manuelle explicite**
pour Louis (quoi tester, quoi ressentir, quels chiffres regarder).

### R9 — Tu lis et tu alimentes le registre des pièges
`Docs/12_PIEGES_OUTILLAGE.md` recense chaque piège d'outillage et **chaque erreur déjà commise**
par un agent sur ce projet — suppressions accidentelles comprises. Il fait autorité.

- **Avant** de toucher à un Blueprint, un asset ou l'éditeur : tu le lis.
- **Après** être tombé dans un piège — outil qui ment, erreur silencieuse, ou ta propre bêtise :
  tu y ajoutes une entrée. Symptôme observable + cause + parade.

Un piège non écrit sera refait par le prochain agent. **Écrire l'entrée fait partie du correctif,
pas du bonus.** Tu ne masques jamais une erreur que tu as commise : tu la consignes.

Corollaire : **un outil qui ne renvoie pas d'erreur n'a pas forcément fait ce que tu crois.**
Après toute écriture, relis l'état réel — et pas via l'outil qui vient d'écrire.

### R10 — Tu ne commites pas une feature de gameplay avant que Louis l'ait jouée
Compiler et vérifier la logique ne prouve pas que ça marche (R8). Quand une feature touche
le mouvement, le combat ou le feeling :

1. tu implémentes, tu vérifies ce qui est vérifiable, tu **sauvegardes les assets** ;
2. tu **t'arrêtes** et tu donnes la checklist de test ;
3. tu commites **seulement** après le retour de Louis.

Un commit prématuré transforme une régression en historique à défaire.

---

## 4. Environnement technique

| | |
|---|---|
| Moteur | Unreal Engine 5.8 — `L:\Program Files\Epic Games\UE_5.8` |
| Projet | `L:\Unreal Engine\Projects\OVERDRIVE\OVERDRIVE.uproject` |
| Template d'origine | First Person BP (à nettoyer, voir `Docs/04_ROADMAP.md` J1) |
| Input | Enhanced Input (déjà actif) |
| Plateforme | PC Windows, DX12 / SM6 |
| Rendu | **Éclairé, plein jour.** Lumen + Virtual Shadow Maps **actifs** (réglages du template conservés). Cel-shading par post-process de posterisation + outlines Sobel — cf. `Docs/11_ARBITRAGES.md D2` |
| MCP Unreal | `unreal-mcp` sur `http://127.0.0.1:8000/mcp` — nécessite l'éditeur ouvert |
| Langue | **Doc et communication en français. Noms d'assets, variables et code en anglais.** |

### Unités
UE : `1 uu = 1 cm`. **Toute vitesse est en `uu/s` en interne.**
Affichage HUD `SPEED = uu/s ÷ 10`. Détail complet et table de conversion : `Docs/07_TUNING.md §1`.

### Outils MCP
- `unreal-mcp` : manipulation de l'éditeur ouvert. Vérifie que l'éditeur tourne avant de l'utiliser.
  Utilise `list_toolsets` / `describe_toolset` avant d'appeler `call_tool`.
- `blender` : création de meshes low-poly. **Les sources `.blend` et les `.fbx` d'export vivent dans
  `Art_Source/` à la racine, jamais dans `Content/`** — réglages d'export FBX : `Docs/06_CONVENTIONS.md §9`.

---

## 5. Workflow attendu d'un agent

1. **Lire** `Docs/00_INDEX.md` + la spec du système concerné + `Docs/07_TUNING.md`.
2. **Vérifier le scope** dans `Docs/03_SCOPE_LOCK.md`.
3. **Annoncer** ce que tu vas faire, dans quels fichiers/assets, avec quels noms.
4. **Implémenter** en respectant l'architecture (`Docs/05_ARCHITECTURE.md`).
5. **Documenter** (R7) + fournir la checklist de test manuel (R8).

Si la doc est ambiguë ou contradictoire : **tu poses la question, tu n'inventes pas.**
Si la doc est incomplète sur un point que tu dois trancher : tu proposes, tu écris ta décision
dans la doc concernée, et tu la signales explicitement dans ta réponse.

---

## 6. Interdits absolus pendant les 4 semaines

Multijoueur · génération procédurale · crafting · inventaire · dialogues · cinématiques ·
lore · méta-progression permanente · système de quêtes · open world · sauvegarde complexe ·
armes supplémentaires · ennemis supplémentaires · refactor « pour faire propre » non demandé ·
migration C++ · plugin marketplace non validé par Louis.
