# Journal — 2026-08-18 — Jour 01

**Temps effectif** : ~2 h de travail utile, sur une session de 6 h
(3 h 17 perdues sur un éditeur figé, cf. « Bugs rencontrés »).
**Objectif du jour (roadmap)** : J1 — Fondations.

---

## Fait

- **Dépôt git initialisé** + Git LFS (`.gitignore` / `.gitattributes` étaient déjà prêts).
  402 fichiers au premier commit, dont 271 en LFS.
- **Template First Person supprimé** — 150 fichiers : `Content/FirstPerson`,
  `Content/Characters`, `Content/LevelPrototyping/Interactable`, et les external actors
  World Partition de `Lvl_FirstPerson`.
- **Canaux et presets de collision** (`Config/DefaultEngine.ini`, conforme à `SPEC_MOVEMENT §12`) :
  object type `WallRideSurface` (`ECC_GameTraceChannel2`), trace channel `Weapon`
  (`ECC_GameTraceChannel3`), et les 5 presets `OD_Player`, `OD_Enemy`, `OD_EnemyProjectile`,
  `OD_WallRideSurface`, `OD_LevelGeo`.
  *Vérifié en jeu* : `SceneTools.get_collision_channels` retourne bien 8 object types
  (6 moteur + `Projectile` + `WallRideSurface`), et une capsule en `OD_Player` résout
  en `ECC_Pawn`.
- **Squelette Core** dans `Content/OVERDRIVE/Core/` : `GM_Overdrive`, `GS_Overdrive`,
  `PC_Overdrive`, `GI_Overdrive`, `PS_Overdrive`. Les classes par défaut du GameMode
  pointent sur les bons Blueprints.
- **`BP_PlayerCharacter`** (`Player/Blueprints/`) : capsule 88/34 en `OD_Player`,
  `FirstPersonCamera` à `EyeHeight` 64 avec `bUsePawnControlRotation`, `ArmsMesh`
  (SkeletalMesh placeholder, vide) parenté à la caméra, mesh de Character masqué.
  CMC réglé sur `07_TUNING §2` : `GravityScale` 2.4, `MaxStepHeight` 50,
  `WalkableFloorAngle` 50, `GroundFriction` 3.0, `BrakingDecelerationWalking` 1500,
  `MaxWalkSpeed` 1000, `bUseFlatBaseForFloorChecks` true (piège d'accroche d'arête,
  `SPEC_MOVEMENT §16`).
- **Input complet** (`Player/Input/`) : 11 `IA_*` avec le bon `ValueType`,
  `IMC_Gameplay` (14 mappings), `IMC_UI`, `IMC_Debug` (1 mapping).
  Triggers et modificateurs posés et relus : `Negate` sur Y seul pour `IA_Look`,
  `Hold` à 0,4 s pour `IA_Restart`, `Swizzle`/`Negate` sur WASD.
- **`L_Sandbox_Movement`** (`Levels/Sandbox/`) : dupliqué de `Template_Default`
  (garde l'éclairage Lumen/VSM du moteur intact, cf. `11_ARBITRAGES D2`), sol porté
  à **20000 × 20000 uu** en `OD_LevelGeo` / mobilité `Static`, `PlayerStart` à z=92.
- **Réglages projet** : `EditorStartupMap` et `GameDefaultMap` → `L_Sandbox_Movement`,
  `GlobalDefaultGameMode` → `GM_Overdrive`, `GameInstanceClass` → `GI_Overdrive`.

## Pas fait / reporté

- **Les 13 Enums de `08_DATA_SCHEMAS §1` n'ont pas d'entrées.** Les 13 assets existent,
  bien nommés, dans `Data/Enums/`, mais **vides**. C'est un blocage d'outillage, pas un
  choix — voir « Décisions » D3. **À saisir à la main par Louis avant le J2** :
  c'est l'étape 1 de l'ordre de création recommandé, elle débloque tout le reste.
- Pas de playtest : il n'y a pas encore de logique de mouvement (c'est le J2).

## Décisions prises

| Décision | Fichier de doc mis à jour |
|---|---|
| **D1** — `Content/LevelPrototyping` n'est pas supprimé entièrement. Le J1 demande de le supprimer *et* de garder les matériaux de grid, qui vivent dedans. Gardé : `Materials/`, `Textures/` (matériaux de grid, exception explicite) et `Meshes/` (SM_Cube, SM_Ramp, SM_Cylinder — nécessaires au sol du sandbox aujourd'hui et aux pentes du J4). Supprimé : `Interactable/` (porte, jump pad, cible), hors scope. | à valider par Louis |
| **D2** — `GM_Overdrive` hérite de **`GameModeBase`**, pas de `GameMode`. `05_ARCHITECTURE §39` dit juste « GameMode ». OVERDRIVE est solo, sans match state : `GameModeBase` est plus léger et suffit. | — |
| **D3** — « Hold » dans `09_INPUT §1` recouvrait deux mécaniques différentes d'Enhanced Input. Tranché : `IA_Sprint` / `IA_Slide` = **aucun trigger** (sémantique `Down`, agit tant que la touche est tenue) ; seul `IA_Restart` utilise un vrai `InputTriggerHold` (0,4 s). Un `InputTriggerHold` sur le sprint imposerait 1 s de délai avant de démarrer. | **`Docs/09_INPUT.md §3`** ✅ |
| **D4** — Nommage des composants du `BP_PlayerCharacter` : `FirstPersonCamera` et `ArmsMesh`. Aucune convention n'existait pour les composants. | — |
| **D5** — ~~Passerelle Python éditeur ajoutée~~ → **refusée par Louis, supprimée.** Remplacée par `bAutoStartServer = true` dans les réglages du plugin ModelContextProtocol. Voir « Outillage ». | — |
| **D6** — Les entrées des 13 enums sont saisies **à la main par Louis**. Après vérification des 52 toolsets MCP, de l'API Python d'UE et de l'arbre d'accessibilité Slate, aucune voie automatisée n'existe. | `04_ROADMAP.md` J1 ✅ |

## Valeurs modifiées

Aucune. Toutes les valeurs posées viennent telles quelles de `07_TUNING §2`.

## Outillage

**`Saved/mcp.py`** — client HTTP direct vers le serveur MCP de l'éditeur
(`127.0.0.1:8000/mcp`). `Saved/` est gitignoré, ce n'est pas un asset du projet.
Écrit parce que la connexion MCP native de Claude Code est tombée avec l'éditeur
figé et n'est jamais revenue dans la session.

**Passerelle Python — créée puis SUPPRIMÉE le jour même (décision de Louis).**
`Content/Python/init_unreal.py` exécutait tout `.py` déposé dans `Saved/py_inbox/`.
Elle servait à une seule chose en pratique : relancer le serveur MCP quand son
listener HTTP ne démarrait pas au lancement de l'éditeur (arrivé 2 fois sur 3).
Elle a aussi gelé l'éditeur une fois (bug de ré-entrance, cf. « Bugs »).

**Remplacée par le vrai réglage** : `Editor > General > ModelContextProtocolSettings`
→ **`bAutoStartServer` passé de `false` à `true`**. Le listener démarre désormais
tout seul, sans script. C'est la bonne solution : celle qu'il fallait chercher en
premier au lieu d'écrire un contournement.

## Bugs rencontrés

| Bug | Gravité | Corrigé ? |
|---|---|---|
| Un probe de classes invalides via les factories MCP a ouvert **deux dialogues modaux** dans l'éditeur. Le game thread est resté figé **3 h 17** (14h51 → 18h08), transport MCP tombé. | **Bloquant** | Oui — règle enregistrée : vérifier la hiérarchie de classe avec `ObjectTools.search_subclasses` **avant** toute factory, jamais de lot non validé |
| Première version de la passerelle Python : le fichier source était supprimé en `finally`, après l'exec. Or `delete_asset`/`create_asset` font tourner la boucle Slate → le tick se redéclenchait sur le même fichier → **récursion infinie**, éditeur gelé. | **Bloquant** | Oui — suppression **avant** l'exec + garde de ré-entrance |
| Un script a écrasé `unreal.AssetEditorSubsystem` (la classe) par une instance, cassant `get_editor_subsystem` pour tous les scripts suivants du même process. | Moyen | Oui — ne jamais assigner dans le module `unreal` |
| `ObjectTools.set_properties` sur `BodyInstance.CollisionProfileName` pose le **nom** du preset mais n'applique pas les réponses en mémoire (pas de `LoadProfileData`). Les valeurs sont correctes après un aller-retour disque. | Faible (piège) | Contourné — vérifier les presets **après** rechargement, pas juste après l'écriture |

## Demain

- **Préalable bloquant** : saisir les entrées des 13 enums à la main.
- J2 — `PDA_MovementData` + `DA_Movement_Default`, `BPC_MovementState`, sprint,
  overlay debug.

---

## Vérifications de fin de journée

- [x] Tous les BP recompilés, zéro warning
- [ ] 3 minutes de jeu réel — **sans objet** : aucune logique de gameplay au J1
- [x] Roadmap cochée
- [x] Tuning à jour (aucune valeur modifiée)
- [x] Commit fait
