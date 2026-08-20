# Journal — 2026-08-20 — Asset : `SK_Enemy_Grunt` (modèle + rig + animations)

**Objectif (roadmap)** : aucun — travail d'art anticipé sur **J12/J13 (Ennemi de base, Grunt)**.
Rien n'est coché dans `04_ROADMAP` : aucun Blueprint n'existe encore.

---

## Fait

- **Modèle** `SK_Enemy_Grunt` — 1824 tris, **180.00 × 70.00 uu**, ratio L/H **0.389**
  (fiche Grunt de `SPEC_ART_DIRECTION §9.3` : 180 / 70 / 0.39).
  Silhouette triangle pointe en bas, visière **point rond centré**, coque `OD_Navy_Deep`,
  plaques `OD_Navy_Ink`, émissif `OD_Amber_Enemy`. Test niveaux de gris `§3.3` : **réussi**.
- **UV0** par îlots plats — 301 îlots, tous dans `[0,1]`, aucune face orpheline.
- **Vertex colors** `FLOAT_COLOR` : `R` masque émissif, `G` masque plaque, `B = 0.85`, `A = 0.5`.
- **Squelette** `SKEL_Enemy_Humanoid` — 33 os au nommage UE5 strict
  (`root`/`pelvis`/`spine_01..05`/`neck_01-02`/`head`/`clavicle`/`upperarm`/`lowerarm`/`hand`/
  `thigh`/`calf`/`foot`/`ball` + 7 os IK). Pondération **rigide**, 1 os par pièce :
  0 vertex sans poids, 0 poids multiple sur 1012 vertices.
- **12 clips à 30 fps, tous sur place** (aucune root motion) : `Idle` `Walk` `Run` ·
  Grunt `ChargeWindup` `Charge` `ChargeRecover` · Shooter `Telegraph` `Fire` `Recover` ·
  Tank `SlamWindup` `Slam` `Stagger`. 78 courbes chacun, contact au sol vérifié à **0.0000 m**.
- **Export FBX du Grunt uniquement** → `Art_Source/Grunt/` (7 fichiers).
  Aller-retour de contrôle : 33 os, 19 groupes, écart en positions monde **0.0000 m**.

## Pas fait / reporté

- **Import dans UE** : pas fait, en attente de la validation de Louis.
- **Shooter** (bras-canon) et **Tank** (volumes d'épaules/jambes, `Component Scale 1.44`) :
  reportés à la demande de Louis. Leurs 6 clips existent déjà et tourneront sur les variantes.
- Pas de `ABP_Enemy`, pas de `BS_Enemy_Locomotion`, pas de `DA_Enemy_Grunt` — c'est le J12/J13.

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| Squelette **construit** au nommage UE5 au lieu du vrai Manny (absent du projet, template nettoyé au J1). Retarget via IK Rig reste possible, les noms d'os correspondent. | tranché avec Louis en session |
| Set d'animation limité au **socle 3 archétypes (12 clips)** et non à un set large : `SPEC_ENEMIES §7/§8` supprime déjà anim de mort (dissolve) et hit react Grunt | — |
| Pondération **rigide** (1 os par pièce) plutôt que lissée : bon choix sur du hard-surface, zéro déformation de plaque | — |
| Modèle construit face à **+X** (et non `−Y`) pour neutraliser l'inversion Y du FBX (`12_PIEGES 5.13/5.24`) | `12_PIEGES 5.47` |
| `object_types = {MESH, ARMATURE}` à l'export, là où `06_CONVENTIONS §9` dit `{MESH, EMPTY}` — la table vise les static meshes, un skeletal exige l'armature | à répercuter dans `06_CONVENTIONS §9` |

## Valeurs modifiées

Aucune valeur de `07_TUNING` touchée.

## Ressenti de playtest

**Non évaluable par l'agent (R8).** Les timings des clips sont des points de départ alignés sur
`07_TUNING §13`, pas des valeurs jouées. À juger par Louis : le `Run` a-t-il l'air *rapide*,
le `ChargeWindup` est-il vu assez tôt pour esquiver.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| `bound_box` est un cache : dimensions fausses de ~1 % pendant 3 relevés | 🔴 | oui — `12_PIEGES 5.44` |
| Suffixes `_R`/`_L` inversés depuis la modélisation (face à `−Y`, la droite est `−X`) | 🟠 | oui — `5.47` |
| Semelles non à plat : il faut `foot = −(thigh + calf)`, robot sur la pointe des pieds sur 9 clips | 🔴 | oui — `5.45` |
| Écartement des bras inversé au-dessus de l'horizontale (Euler Z en espace de repos) | 🟠 | oui — `5.46` |
| **Coudes en hyperextension sur les 12 clips** : `lowerarm` négatif au lieu de positif. Six contrôles automatiques verts, repéré par Louis en 5 s | 🔴 | oui — `5.48` |
| Fausse alerte « 5 os manquants » à la vérification FBX (`ignore_leaf_bones=True`) | 🟠 | oui — `5.49` |
| Vertex colors `BYTE_COLOR` encodées sRGB : `B` et `A` décalés | 🟠 | oui — `5.50` |

## Demain

- Retour de Louis sur les clips → correction des timings
- Import UE (`Enemies/Shared/` pour squelette + locomotion, `Enemies/Grunt/` pour le reste)
- Puis J10–J11 (melee, knockback) avant J12

---

## Vérifications de fin de journée

- [ ] Tous les BP recompilés, zéro warning — *sans objet, aucun BP touché*
- [ ] 3 minutes de jeu réel — **à faire par Louis**
- [ ] Roadmap cochée — *rien à cocher, J12/J13 non entamés*
- [x] Tuning à jour — aucune valeur touchée
- [ ] Commit fait — **en attente de la validation de Louis (R10)**
