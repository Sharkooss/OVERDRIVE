# 12 — PIÈGES D'OUTILLAGE & ERREURS DÉJÀ COMMISES

> **Lis ce fichier avant de toucher à un Blueprint, un asset ou l'éditeur.**
> Chaque ligne ici a coûté du temps de production. Aucune n'est théorique.
>
> **Tu ajoutes une entrée à chaque fois que tu tombes dans un piège** — outil qui ment,
> erreur silencieuse, ou bêtise de ta part. Une entrée = symptôme observable + cause + parade.
> Un piège non écrit sera refait par le prochain agent (`Docs/00_INDEX.md`, R9 de `CLAUDE.md`).

Légende de gravité : 💀 destructeur · 🔴 casse le jeu en silence · 🟠 fait perdre du temps · ⚪ cosmétique

---

## 1. Les trois règles qui résument tout

1. **Un outil qui ne renvoie pas d'erreur n'a pas forcément fait ce que tu crois.**
   Après *toute* écriture, relis l'état réel — et pas via l'outil qui vient d'écrire.
2. **Ne supprime jamais en masse sans lister ce que tu vas supprimer et le faire valider.**
   Deux destructions accidentelles en 3 jours, les deux par « nettoyage automatique ».
3. **Une preuve qui contredit ton hypothèse est une preuve, pas une anomalie.**
   Si une valeur ne colle pas, cherche pourquoi *avant* de conclure « c'est l'environnement ».

---

## 2. Blueprint — DSL de graphe (`write_graph_dsl` / `read_graph_dsl`)

C'est l'outil le plus puissant du projet **et le plus traître**. 100 % des régressions du J3 viennent d'ici.

| # | Gravité | Piège | Symptôme | Parade |
|---|---|---|---|---|
| 2.1 | 💀 | **`read_graph_dsl` ne suit que le pin d'exec par défaut.** Les branches sur `Triggered` / `Started` / `Completed` des events Enhanced Input sont **invisibles**. | `BP_PlayerCharacter:EventGraph` se lit comme 5 events au corps vide alors qu'il contient 19 nœuds. Un `write_graph_dsl` dessus **efface tout le câblage d'input**. | Avant d'écrire : `find_nodes(graph, title="")`. Si le nombre de nœuds dépasse ce que montre le DSL → **interdiction d'écrire en DSL**, passer par `create_node` + `connect_pins`. |
| 2.2 | 💀 | **`write_graph_dsl` EMPILE, il n'écrase pas** (dans un `EventGraph`). Les anciens nœuds restent, orphelins. | L'`EventGraph` de `BPC_MovementState` avait **101 nœuds / 5 copies** de sa boucle de Tick, accumulées sur 2 jours. `read_graph_dsl` n'en montrait qu'une : les orphelines masquaient l'état réel. | Compter les nœuds après chaque écriture. Purger par accessibilité **exec** (cf. 2.3). Sur un graphe de **fonction**, l'écriture remplace correctement. |
| 2.3 | 💀 | **`find_nodes(entry_points_only=True)` ne renvoie PAS les events Enhanced Input.** | Une purge « supprime tout ce qui n'est pas atteignable depuis un point d'entrée » **a supprimé les 5 events d'input** de `BP_PlayerCharacter`. | Traiter les `K2Node_EnhancedInputAction` comme des racines **à la main**. Et lister les nœuds à supprimer avant de le faire. |
| 2.4 | 🟠 | **`get_connected_subgraph` suit aussi les liens de données** — inutilisable pour détecter du code mort. | Il renvoyait 101/101 nœuds « connectés » : les chaînes orphelines partagent le pin `DeltaSeconds` du même Event Tick. | Calculer soi-même : BFS sur les pins **Exec** depuis les racines, puis remonter les alimentations de données des nœuds vivants. |
| 2.5 | 🔴 | **Argument positionnel sur une fonction membre → il part sur le pin `self`.** S'il est incompatible, il est **jeté en silence** et le vrai pin garde son défaut. | `(SetComponentTickEnabled true)` a laissé `bEnabled = false` → **Tick du composant désactivé, 3 features mortes, 0 erreur, compilation OK**. | **Toujours nommer les pins** : `(CallFunction|Foo :NomDuPin valeur)`. Sans exception. |
| 2.6 | 🔴 | **La sortie de `read_graph_dsl` n'est pas réinjectable.** Elle écrit en positionnel (cf. 2.5). | Recopier `(CallFunction|UpdateSpeedCap DeltaSeconds)` échoue ou câble faux. | Jamais de round-trip aveugle read → edit → write. Renommer tous les pins en réécrivant. |
| 2.7 | 🔴 | **Collision fonction / variable homonyme : le writer choisit la variable, en silence.** | `(CallFunction|SetHorizontalSpeed …)` a produit le *setter de la variable* `HorizontalSpeed` : l'affichage bougeait, la vélocité non. | Éviter de nommer une fonction `SetX` quand une variable `X` existe. Sinon, écrire la logique en clair (ici : `Class|MovementComponent|SetVelocity`). |
| 2.8 | 🟠 | Les **setters de variables** veulent le chemin de catégorie complet et **sans underscores**. | Le lecteur affiche `(\|SetTune_SpeedWalk …)`, mais il faut écrire `(Variables\|Movement\|Cached\|SetTuneSpeedWalk …)`. Les booléens perdent leur `b` : `GetIsGrounded`. | `find_node_types(graph, filtre)` avant d'écrire. |
| 2.9 | ⚪ | Les `type_id` à **parenthèses** fonctionnent (`Math\|Trig\|Cos(Degrees)`, `Utilities\|String\|ToString(Float)`) — contrairement à ce qu'affirmait le J2. | — | C'est l'argument **positionnel** qui casse, pas la parenthèse. Nommer le pin (`:A`, `:InDouble`). |
| 2.10 | 🟠 | `Transformation\|GetVelocity` (ce que le lecteur affiche) **refuse un CMC** en `self`. | `Could not connect pin CachedCMC to self`. | `Class\|MovementComponent\|GetVelocity`. |
| 2.11 | 🟠 | Un `if` **termine le flux d'exec** : ce qui suit dans le même corps ne s'exécute pas. | — | Mettre l'`if` en dernier, ou extraire en fonction. |
| 2.12 | ⚪ | `get_node_type_pins` **instancie un nœud temporaire** dans le graphe interrogé. | Nœuds orphelins qui traînent (un `ToString(Boolean)` est resté 2 jours dans `BP_PlayerCharacter`). | Interroger un graphe qui sera réécrit, ou nettoyer après. |
| 2.13 | ⚪ | `arrange_nodes` ne fait rien (0 nœud déplacé, sans erreur). | — | Positionner via l'argument `pos` de `create_node`. |

### La vérification qui aurait tout évité

Un graphe qui compile ne prouve rien. **Après écriture, relire les *valeurs de pins*, pas le DSL :**

```python
infos = get_node_infos(nodes)
# pour chaque pin d'entrée non-Exec et NON CONNECTÉ, afficher sa valeur littérale
```

⚠️ Un filtre « non connecté **et** valeur vide » **ne suffit pas** : un argument perdu laisse le
défaut du pin — `false`, `0.0` — qui n'est pas vide. C'est précisément ce qui a laissé passer 2.5.

---

## 3. Destructions accidentelles

| # | Gravité | Ce qui s'est passé | Leçon |
|---|---|---|---|
| 3.1 | 💀 | **J2** — suppression de `Content/Input/` : 9 assets emportés au lieu des 6 annoncés (le dossier contenait aussi `Touch/`). | Lister le contenu réel **avant** de supprimer un dossier, pas ce qu'on croit qu'il contient. |
| 3.2 | 💀 | **J3** — une purge de nœuds morts a supprimé les 5 events Enhanced Input (cf. 2.3). Corrigé en les reconstruisant un par un. | Toute suppression en masse : produire la liste, la vérifier, **puis** supprimer. Jamais dans le même appel. |
| 3.3 | 🟠 | **J3** — commit effectué avant validation de Louis, sur une régression qui cassait tout le jeu. | **Ne jamais committer une feature de gameplay avant que Louis l'ait jouée.** Sauvegarder les assets, s'arrêter, attendre. Cf. R8 + R10. |

---

## 4. Vérification & PIE

| # | Gravité | Piège | Parade |
|---|---|---|---|
| 4.1 | 🔴 | **Expliquer une preuve contradictoire par « l'environnement ».** Le relevé PIE montrait `MaxAcceleration = 2048` (défaut moteur) au lieu de 4000 : le Tick était mort. J'ai conclu « l'éditeur n'a pas le focus » et commité. | Une hypothèse d'environnement **se teste**. Ici, `CMC.MovementMode = MOVE_Walking` prouvait que le monde tickait — une seule propriété séparait le bon du mauvais diagnostic. |
| 4.2 | 🟠 | `bThrottleCPUWhenNotForeground` (Editor → General → Performance) fait tourner PIE à **3 tick/s** sans focus. **Mis à `false` le 2026-08-19**, réglage local non versionné. | Vérifier `max tick rate 60` dans le log après `StartPIE`. Sur un nouveau poste, le remettre à `false`. |
| 4.3 | 🔴 | `SlateInspectorToolset.PressKey` n'atteint le jeu que si **`GameGetsMouseControl = true`** (Editor → LevelEditor → PlayIn). Sinon : faux négatif. | L'activer **le temps du test**, puis le remettre à `false` — sinon le PIE capture la souris pendant les playtests de Louis. |
| 4.4 | 🟠 | **Un aller-retour MCP fait avancer ~20 s de temps de jeu.** Impossible de tester une fenêtre inférieure à la seconde (buffer de saut, coyote time, i-frames). | Viser une **trace persistante** (`bDebugEnabled`, `PreviousState`, `LandedTime`), jamais une grandeur instantanée. Pour les fenêtres courtes : monter temporairement la valeur de tuning, vérifier le mécanisme, restaurer. Sinon, **le dire** et déléguer à Louis. |
| 4.5 | 🟠 | `time.sleep()` dans `execute_tool_script` **gèle le jeu** : les appels MCP s'exécutent sur le game thread. | Pour laisser le monde avancer, faire deux appels MCP séparés. |
| 4.6 | 🟠 | `ObjectTools.get_properties` ne lit pas les propriétés transientes (`Controller`, `PlayerInput`, `EnhancedActionMappings`) ; `set_properties` refuse les variables `BlueprintReadOnly`. | Juger par l'effet observable, pas par introspection. |
| 4.7 | ⚪ | Signatures incohérentes : `get_properties` prend `properties`, `set_properties` prend `values` (une **chaîne** JSON), `list_properties` prend `instance`. | `describe_toolset` avant, en cas de doute. |

---

## 5. Assets, enums, input

| # | Gravité | Piège | Parade |
|---|---|---|---|
| 5.1 | 🔴 | **Un `IMC_*` créé par outil a ses mappings dans le tableau déprécié `Mappings`**, alors qu'UE 5.8 ne lit que `DefaultKeyMappings`. Contexte appliqué, tableau vide, **aucune erreur nulle part**. | Après création d'un IMC par outil, vérifier `DefaultKeyMappings`. Ne jamais laisser les deux tableaux remplis (double source de vérité). |
| 5.2 | 🔴 | **Aucun outil ne sait écrire les entrées d'un `UserDefinedEnum`**, ni créer une variable/pin typée enum. | Les `E_*` et `S_*` de `08_DATA_SCHEMAS` sont saisis **à la main par Louis**. Lui fournir une liste exacte, précise, en fin de journal. |
| 5.3 | 🟠 | Le flag **`Pure`** d'une fonction n'est pas exposé par l'outillage. | Cochage manuel par Louis. |
| 5.4 | 💀 | **Sonder une classe invalide via une factory fige l'éditeur** (modale bloquante) et tue la connexion MCP. | Ne jamais sonder une classe au hasard. |
| 5.5 | 🟠 | Des assets **homonymes** dans deux dossiers (`Content/Input/IA_Move` vs `OVERDRIVE/Player/Input/IA_Move`) font que l'éditeur lie les nœuds au mauvais asset, sans moyen de désambiguïser par outil. | Un seul emplacement par nom. Tout le contenu du projet vit dans `Content/OVERDRIVE/`. |
| 5.6 | 🟠 | Les modifications faites par outil restent **en mémoire de l'éditeur** : `git status` ne voit rien. | `AssetTools.save_assets([...])` avant tout `git add`. |
| 5.7 | ⚪ | Le format littéral d'un pin `Vector2D` est `(X=0.000000,Y=0.000000)`. `"0,0"` échoue à la compilation. | — |

---

## 6. Pièges UE5 de gameplay (non liés à l'outillage)

Ceux-ci vivent aussi dans `Docs/Specs/SPEC_MOVEMENT.md §15`. Les deux plus coûteux à ce jour :

| # | Gravité | Piège | Parade |
|---|---|---|---|
| 6.1 | 🔴 | **Tout ce qui écrit `CMC.Velocity` doit s'exécuter AVANT l'écriture de `MaxWalkSpeed`.** `DriveCMC` placé avant l'air strafe calculait le plafond sur la vitesse d'avant le gain ; le CMC reclampait dessus à la frame suivante et effaçait le gain. Vitesse bloquée au sprint cap. | Ordre du Tick : toute écriture de vélocité → hard clamp → **`DriveCMC` en dernier**. Vaudra pour le dash (J5), le wall ride (J6), le bunny hop (J7). |
| 6.2 | 🔴 | **Un saut déclenché depuis `Event OnLanded` est détruit.** Juste après `Landed()`, le CMC appelle `SetPostLandedPhysics` → `SetMovementMode(Walking)` → **`Velocity.Z = 0`**. | Ne rien faire de physique dans `OnLanded` : poser un drapeau, consommer au Tick suivant (`ConsumeBufferedJump`). |
| 6.3 | 🟠 | Les constantes de Quake **ne sont pas transposables** telles quelles : Quake court à 320 u/s, OVERDRIVE à 1500 (facteur ≈ 4.7). | Rééchelonner `AirStrafe_WishSpeedCap` et `_SpeedGainPerSec` avec `Speed_SprintCap`. Cf. `07_TUNING §7`. |
| 6.4 | 🟠 | Deux modèles d'air strafe existent et **ne se jouent pas pareil** : Quake 1/CPMA (`wishspeed` bridé ~30 → strafe à la touche latérale **seule**) et Quake 3 (`wishspeed` = vitesse de course → **Z+Q / Z+D + souris**). | **OVERDRIVE utilise le modèle Quake 3** (`WishSpeedCap = Speed_SprintCap`), validé par Louis au J3. |
