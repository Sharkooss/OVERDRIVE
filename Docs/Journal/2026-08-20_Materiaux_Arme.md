# Journal — 2026-08-20 — Matériaux de l'arme FP

**Temps effectif** : ~1 h
**Objectif du jour (roadmap)** : hors roadmap du jour — lot art avancé du **J22** (« toon shader +
matériaux appliqués »), à la demande de Louis : *« importer la texture de mon arme et mettre les
couleurs emissive rouge dessus, que ça fasse laser gun »*.

---

## Fait

### Traduction de la demande

**Il n'y a aucune texture bitmap à importer, et il ne doit pas y en avoir.** `SM_Weapon_LaserPistol`
a été modélisé sans texture (décision 3 de `2026-08-18_SM_Weapon_LaserPistol.md`, validée par Louis) :
la couleur vient des **slots de matériau**, pas d'une image. `Art_Source/Weapons/` ne contient que le
`.blend`, le `.fbx` et des PNG d'**aperçu de contrôle** (`ortho_*.png`, `hero_3q.png`, `uv_layout.png`)
— des images de validation, pas des assets. Les importer aurait créé 4 textures inutiles dans un projet
dont le plafond est de **6 textures au total** (`SPEC_ART_DIRECTION §12.4`).

« Importer la texture » a donc été exécuté comme : **créer les matériaux et les assigner aux 4 slots.**

### Assets créés

| Asset | Chemin UE |
|---|---|
| `M_Weapon_Base` | `/Game/OVERDRIVE/Art/Materials/Master/M_Weapon_Base` |
| `MI_Weapon_Body` | `/Game/OVERDRIVE/Art/Materials/Instances/MI_Weapon_Body` |
| `MI_Weapon_Panel` | `/Game/OVERDRIVE/Art/Materials/Instances/MI_Weapon_Panel` |
| `MI_Weapon_Accent` | `/Game/OVERDRIVE/Art/Materials/Instances/MI_Weapon_Accent` |
| `MI_Weapon_Emissive` | `/Game/OVERDRIVE/Art/Materials/Instances/MI_Weapon_Emissive` |

Asset modifié : `/Game/OVERDRIVE/Player/Meshes/SM_Weapon_LaserPistol` (les 4 slots).
Tous sauvegardés (`save_assets`) — vus par `git status`. **Aucun commit** (R10).

`M_Weapon_Base` : `Surface` / `Opaque` / `Default Lit`, **6 expressions, 5 paramètres**, zéro texture,
zéro normal map. Les 4 pins branchés et relus un par un : `MP_BaseColor` (sortie `RGB` du
`VectorParameter`), `MP_Metallic`, `MP_Roughness`, `MP_EmissiveColor` (via
`EmissiveColor × EmissiveIntensity`). `MP_Normal` vide, volontairement. Compile.

Valeurs, conversion sRGB → linéaire et tableau complet : **`SPEC_ART_DIRECTION §6.4`**, pas ici.

### Le point technique : sRGB ≠ linéaire

Les HEX de la demande sont en **sRGB**. Un `VectorParameter` de matériau attend du **linéaire**.
`PALETTE.md §8.2` le dit déjà pour la saisie manuelle (« ne jamais saisir les composantes RGB à la
main »), mais l'avertissement vaut **encore plus** par outil : `MaterialInstanceTools.set_vector_parameter`
écrit la valeur **telle quelle**, sans aucune conversion — il n'y a pas de color picker pour rattraper
l'erreur. Poser `#24282E` en `36/255, 40/255, 46/255` aurait donné un gris **3 fois trop clair et
délavé**, sans la moindre erreur.

Les valeurs linéaires sont écrites **à côté des HEX** dans `SPEC_ART_DIRECTION §6.4`, avec la formule,
pour que personne ne recopie le HEX plus tard.

## Pas fait / reporté

- **Aucun aperçu rendu.** Un autre agent travaille en parallèle sur `BPC_WallRide` et lancera PIE :
  `StartPIE`/`StopPIE` m'étaient interdits pour cette session. Le rendu réel de l'arme (et surtout
  l'intensité de l'émissif) n'a donc **pas** été vu — c'est le point n°1 de la checklist de Louis.
- **`EmissiveIntensity` non calibré.** Voir ci-dessous.
- `PP_ToonPost`, `MPC_Global`, `M_Env_Base`, `M_Env_Emissive`, `M_Sign` : toujours au J22.
  `M_Weapon_Base` ne référence **pas** `MPC_Global` — quand la collection existera, il faudra décider
  si les couleurs de l'arme y passent (`SPEC_ART_DIRECTION §14`, « aucun HEX en dur dans un `MI_` »).

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| « Importer la texture » = créer les matériaux. Aucun PNG d'`Art_Source/` n'est importé : ce sont des aperçus de contrôle, pas des assets | ce journal |
| Un seul master `M_Weapon_Base` volontairement minimal (5 paramètres) plutôt qu'un `M_Player` complet : le master complet du §6 arrive au J22, celui-ci ne doit pas le préempter | `SPEC_ART_DIRECTION §6.4` |
| Valeurs saisies en **linéaire**, HEX conservés en référence à côté | `SPEC_ART_DIRECTION §6.4` |
| `EmissiveIntensity = 8` comme point de départ, aligné sur l'échelle « surfaces de traversée » du §6.3 | `SPEC_ART_DIRECTION §6.4` |
| `MI_Weapon_Emissive` : `BaseColor` mis au **même rouge** que l'émissif (`Metallic 0`, `Roughness 0.6`) — non spécifié par la demande, tranché ici | `SPEC_ART_DIRECTION §6.4` |
| `Metallic > 0` toléré **sur l'arme uniquement**, en écart assumé de `§6.2`/`§12.2` | `SPEC_ART_DIRECTION §6.4.2` |
| Les valeurs de matériau ne vont **pas** dans `07_TUNING.md` : ce n'est pas du gameplay | `SPEC_ART_DIRECTION §6.4` |

## Valeurs modifiées

Aucune valeur de `07_TUNING.md`. Les réglages de matériau vivent dans `SPEC_ART_DIRECTION §6.4`.
Seule valeur marquée `[À CALIBRER]` : `EmissiveIntensity = 8` sur `MI_Weapon_Emissive`.

---

## ⚠️ Tension de palette — à arbitrer par Louis, je ne tranche pas

**En une phrase : l'arme du joueur est rouge alors que le tir qu'elle produit est magenta, et le rouge
appartient déjà au danger et aux surfaces de wall ride.**

Le détail, les trois sources qui se contredisent et les trois options de sortie sont dans
**`SPEC_ART_DIRECTION §6.4.1`**. Un pointeur non normatif a aussi été posé dans `PALETTE.md §3` —
**la règle réservée n'a pas été modifiée**, elle est seulement annotée d'une divergence ouverte.

Résumé :

- `PALETTE.md §3` + `11_ARBITRAGES D3` : tout ce qui émane du joueur = `OD_Magenta_Player` `#E8336E`.
  Le rouge = `OD_Red_Danger` (« ça va me tuer ») et `OD_Red_Traversal` (« je peux courir dessus »).
- `SPEC_ART_DIRECTION §8.2` : bandes émissives de l'arme = **magenta**.
- Louis, aujourd'hui : **rouge**, « que ça fasse laser gun ».

**J'ai fait ce que Louis demande : rouge.** Mais `#FF1025` est à moins de 10 % de teinte de
`OD_Red_Danger` `#C81E2E` et de `OD_Red_Traversal` `#F4453F`. Une source rouge saturée **en
permanence** au centre-bas de l'écran use le signal rouge du décor — c'est un risque de lisibilité,
pas une question de goût.

| Option | Coût du changement |
|---|---|
| **A — rouge, on assume** *(état actuel)* | 0. `PALETTE.md §3` gagne une exception explicite pour l'arme FP. |
| **B — magenta `#E8336E`** *(l'arme annonce la couleur de son tir)* | **une valeur** dans `MI_Weapon_Emissive`. Linéaire : `0.806952 / 0.033105 / 0.155926`. |
| **C — rouge au repos → magenta au tir** | réel (DMI + pilotage), à ne pas payer avant d'avoir joué A ou B. |

Rien n'est verrouillé : A → B est un `set_vector_parameter`.

---

## Vérifications faites (règle n°1 du registre : relire avec un autre outil)

- **Slots du mesh** : écrits par `StaticMeshTools.set_material`, **relus par `ObjectTools.get_properties`
  sur `staticMaterials`**. Les 4 slots pointent sur les bons `MI_`, **dans l'ordre** 0→3.
  Les noms de slots réels ont été **mesurés** avant écriture (`get_material_slots`), pas supposés —
  ils correspondent bien à ceux du journal du 2026-08-18 (`5.24` : un journal n'est pas une mesure).
- **Paramètres des `MI_`** : écrits par `MaterialInstanceTools.set_*_parameter`, **relus un par un par
  `ObjectTools.get_properties`** sur `scalarParameterValues` / `vectorParameterValues` / `parent`.
  Les 4 instances ont le bon parent et les 5 overrides attendus.
- **Master** : `recompile` sans erreur ; les 4 pins relus par `MaterialTools.get_property_input`
  (et non par le DSL qui les a écrits) ; `MP_Normal` confirmé vide ;
  `MaterialInstanceTools.list_parameters` confirme exactement 5 paramètres, pas un de plus.
- **Domaine / blend / shading model** relus : `MD_Surface` / `BLEND_Opaque` / `MSM_DefaultLit`.
- **`git status`** confirme les 5 nouveaux `.uasset` + le mesh modifié sur disque (donc `save_assets`
  a bien écrit, cf. `5.6`).
- **PIE non lancé** (consigne de session : un autre agent l'utilise).

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| Aucun | — | — |

Aucun nouveau piège d'outillage : `MaterialTools` et `MaterialInstanceTools` se sont comportés
exactement comme annoncé. Une entrée a quand même été ajoutée à `12_PIEGES_OUTILLAGE` (**5.31**) sur
l'absence de conversion sRGB des setters de couleur — c'est une erreur silencieuse évidente à commettre.

---

## Checklist de test manuel pour Louis (R8 — je ne peux pas juger le rendu)

L'éditeur ouvert, **sans commit** :

1. Ouvre `SM_Weapon_LaserPistol` : les 4 slots doivent afficher `MI_Weapon_Body` / `_Panel` /
   `_Accent` / `_Emissive`, **dans cet ordre**.
2. Lance le jeu et **regarde l'arme en main, en plein soleil**, pas dans le viewport de l'éditeur.
   C'est le seul test qui compte : la scène est éclairée (`11_ARBITRAGES D2`).
3. **La bande rouge est-elle rouge, ou blanche ?** Si elle tire vers le blanc, `EmissiveIntensity`
   est trop haut → descends vers **5**. Si elle est terne et se confond avec le corps, monte vers
   **12–15**. Le réglage vit dans `MI_Weapon_Emissive`, paramètre `EmissiveIntensity`.
4. **Cours le long d'un mur de wall ride** (`SM_Module_WallRide_1600`, liserés `OD_Red_Traversal`) :
   est-ce que l'arme rouge à l'écran gêne la lecture du rouge du mur ? C'est la question que §6.4.1
   pose et que je ne peux pas trancher.
5. **Tire.** L'arme est rouge, le faisceau est magenta. Est-ce que ça te dérange ? → option A, B ou C
   de `SPEC_ART_DIRECTION §6.4.1`.
6. Bouge la souris vite : si l'arme **scintille** (highlight spéculaire qui saute), c'est le
   `Metallic 0.45–0.65` — voir `§6.4.2`, descendre vers 0.2.

## Demain

- Trancher `§6.4.1` (rouge vs magenta) — 30 secondes de décision, une valeur à changer.
- Caler `EmissiveIntensity` après le premier regard en jeu.
- Le reste du lot matériaux (`PP_ToonPost` + masters d'environnement) reste au J22.

---

## Vérifications de fin de journée

- [x] Assets sauvegardés (`save_assets`), présents dans `git status`
- [x] Master recompilé, 4 pins relus, zéro erreur
- [x] Slots relus dans l'ordre avec un autre outil que celui qui a écrit
- [ ] 3 minutes de jeu réel — **à faire par Louis** (PIE interdit cette session)
- [x] Roadmap annotée (J22)
- [x] Doc à jour (`SPEC_ART_DIRECTION §6.4`, `PALETTE.md §3`, `12_PIEGES_OUTILLAGE 5.31`)
- [ ] Commit fait — **non, volontairement** (R10)
