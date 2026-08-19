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
| 2.2 | 💀 | **`write_graph_dsl` EMPILE, il n'écrase pas.** Les anciens nœuds restent, orphelins. | L'`EventGraph` de `BPC_MovementState` avait **101 nœuds / 5 copies** de sa boucle de Tick, accumulées sur 2 jours. `read_graph_dsl` n'en montrait qu'une : les orphelines masquaient l'état réel. | Compter les nœuds après chaque écriture. Purger par accessibilité **exec** (cf. 2.3). |
| 2.2b | 💀 | **~~Sur un graphe de fonction, l'écriture remplace correctement.~~ FAUX — corrigé au J4.** L'empilement frappe **aussi** les graphes de fonction, mais **pas systématiquement** : sur 5 réécritures du J4, 3 ont proprement remplacé et 2 ont empilé (`SetSlideInput` +6 nœuds, `CanEnterState` **+74**, soit une copie entière de la table d'états). | `CanEnterState` est passé de 75 à 149 nœuds sans une seule erreur. `read_graph_dsl` ne montrait que la chaîne vivante — l'ancienne était invisible. | **Compter les nœuds avant et après chaque `write_graph_dsl`, sans exception.** Si le total a augmenté, purger par accessibilité exec. Ne jamais déduire « ça a remplacé » d'une lecture qui a l'air correcte. |
| 2.3 | 💀 | **`find_nodes(entry_points_only=True)` ne renvoie PAS les events Enhanced Input.** | Une purge « supprime tout ce qui n'est pas atteignable depuis un point d'entrée » **a supprimé les 5 events d'input** de `BP_PlayerCharacter`. | Traiter les `K2Node_EnhancedInputAction` comme des racines **à la main**. Et lister les nœuds à supprimer avant de le faire. |
| 2.3b | 🔴 | **Le `bind` du DSL ne fait PAS une copie de valeur.** `(bind x (Variables\|…\|GetFoo))` crée un nœud **pure**, évalué **quand sa sortie est tirée** — donc *après* un `Set` écrit plus haut dans la chaîne d'exec. Toute détection de front écrite naïvement est morte. | `SetSlideInput` : `(bind was (GetbSlideHeld))` puis `(SetbSlideHeld bHeld)` puis `(if (and bHeld (not was)) …)`. Le `Branch` tire `was` **après** l'écriture → `was == bHeld` → condition **toujours fausse**. Le slide n'a jamais pu se déclencher, sans une seule erreur nulle part. | **Ne jamais lire une variable après l'avoir écrite dans la même fonction.** Faire la comparaison **avant** toute écriture (mettre le `Set` dans les branches du `if`), ou passer par une vraie variable locale. Vérifier dans le graphe que le `Branch` précède le `Set` dans la chaîne d'exec. |
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
| 2.14 | 🟠 | **Le `type_id` que `get_node_infos` affiche pour un event Enhanced Input n'est pas celui que `create_node` accepte.** Le lecteur dit `Input\|EnhancedActionEvents\|EnhancedInputActionIA_Slide` ; `create_node` répond « does not exist ». | — | Le vrai id est `Input\|EnhancedActionEvents\|IA_Slide`. **Toujours passer par `find_node_types(graph, "IA_")`** au lieu de recopier ce que le lecteur affiche. Vaut aussi pour `EnhancedActionValues`. |
| 2.15 | 🟠 | **Les pins « float » du Blueprint s'appellent `InDouble`, pas `InFloat`.** `Utilities\|String\|ToString(Float)` prend `:InDouble`. | `Unknown input pin "InFloat"` — au moins l'erreur est explicite et bloque l'écriture. | `get_node_type_pins` avant d'écrire tout nœud de conversion. Le message d'erreur liste les pins valides : le lire au lieu de deviner. |
| 2.16 | 🟠 | `get_node_type_pins` / `find_node_types` sur un `type_id` inexistant **lève une exception qui avorte tout le script** `execute_tool_script` (les appels précédents, eux, ont bien été exécutés). | Un `remove_variable` en début de script part, puis le script meurt sur une sonde ratée → état intermédiaire. | Envelopper **chaque** sonde dans un `try/except Exception` (pas seulement `RuntimeError` : le binding en lève d'autres). Ne jamais mélanger sondes et écritures dans le même script. |
| 2.17 | ⚪ | `add_variable` n'accepte qu'une liste fermée de types : `bool, int, float, byte, name, string, text, Vector, Rotator, Transform, Vector2D, LinearColor`. **`double` est refusé** alors que le float Blueprint d'UE 5.8 *est* un double. | — | Utiliser `float` : le moteur crée bien un double. Pour un type objet, `add_object_variable` ; pour un struct, `add_struct_variable`. |
| 2.18 | 🔴 | **`remove_function_param` ne nettoie pas les nœuds d'appel existants.** Le pin supprimé reste sur chaque `CallFunction` déjà posé → `Pin X named X doesn't match any parameters of function Y` à **chaque** compilation, y compris celles déclenchées par un `write_graph_dsl` sur un **autre** graphe. Tout le Blueprint devient inécrivable. | Une réécriture parfaitement valide échoue avec une erreur qui désigne un graphe qu'on ne touche pas. | Après un `remove_function_param` : chercher les nœuds d'appel de cette fonction dans **tous** les graphes (`find_nodes` + `get_node_infos`, filtrer sur le `type_id`) et les **supprimer** — `delete_node` ne recompile pas, donc il passe même quand le BP est en erreur. Puis réécrire les graphes appelants. |

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
| 4.7 | ⚪ | Signatures incohérentes : `get_properties` prend `properties`, `set_properties` prend `values` (une **chaîne** JSON), `list_properties` prend `instance`. Idem dans `BlueprintTools` : `remove_variable` prend `name`, `set_variable_category` prend `variable_name`. | `describe_toolset` avant, en cas de doute. Ne pas supposer qu'un paramètre porte le même nom d'un outil à l'autre. |
| 4.8 | 🟠 | **On ne peut pas armer un état de jeu pour un test headless** : `set_properties` refuse toute variable Blueprint qui n'est pas `Instance Editable` (extension de 4.6), et aucun outil ne sait **appeler** une fonction Blueprint sur une instance PIE. Une mécanique déclenchée par input est donc invérifiable sans simuler la touche (4.3 / 4.4). | Se rabattre sur les **preuves indirectes** : (a) les valeurs cachées au `BeginPlay` correspondent-elles au DataAsset → le cache a tourné ; (b) une variable écrite **uniquement** par le Tick a-t-elle changé → le composant tick ; (c) les propriétés du CMC modifiées au `BeginPlay`. Puis **le dire** et déléguer le reste à Louis (R8). |

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
| 5.8 | 🟠 | **Renommer un `IA_*` ne renomme pas la classe générée de son event node.** `AssetTools.move` met bien à jour l'`IMC` et la référence d'asset dans le nœud, mais le `type_id` du `K2Node_EnhancedInputAction` reste `…EnhancedInputActionIA_AncienNom`. Un `find_node_types` renverra donc l'ancien nom indéfiniment. | Après `IA_Sprint` → `IA_Walk` : le nœud pointait sur `IA_Walk.IA_Walk` et fonctionnait, mais s'annonçait encore `EnhancedInputActionIA_Sprint`. | **Supprimer puis recréer le nœud d'event** avec le nouveau `type_id` (`Input\|EnhancedActionEvents\|IA_NouveauNom`, cf. 2.14), et recâbler ses pins exec. Pas d'autre moyen. |
| 5.9 | 🟠 | **Aucun outil ne renomme un graphe de fonction Blueprint.** | — | Créer la nouvelle fonction, réécrire son corps, recréer les nœuds d'appel avec le nouveau `type_id` (`CallFunction\|NouveauNom`), recâbler, puis `remove_function_graph` sur l'ancienne. **Cartographier les sites d'appel avant** (`find_nodes` + `get_node_infos`, filtrer sur le `type_id`) : rien ne les liste automatiquement. |

---

## 6. Pièges UE5 de gameplay (non liés à l'outillage)

Ceux-ci vivent aussi dans `Docs/Specs/SPEC_MOVEMENT.md §15`. Les deux plus coûteux à ce jour :

| # | Gravité | Piège | Parade |
|---|---|---|---|
| 6.1 | 🔴 | **Tout ce qui écrit `CMC.Velocity` doit s'exécuter AVANT l'écriture de `MaxWalkSpeed`.** `DriveCMC` placé avant l'air strafe calculait le plafond sur la vitesse d'avant le gain ; le CMC reclampait dessus à la frame suivante et effaçait le gain. Vitesse bloquée au sprint cap. | Ordre du Tick : toute écriture de vélocité → hard clamp → **`DriveCMC` en dernier**. Vaudra pour le dash (J5), le wall ride (J6), le bunny hop (J7). |
| 6.2 | 🔴 | **Un saut déclenché depuis `Event OnLanded` est détruit.** Juste après `Landed()`, le CMC appelle `SetPostLandedPhysics` → `SetMovementMode(Walking)` → **`Velocity.Z = 0`**. | Ne rien faire de physique dans `OnLanded` : poser un drapeau, consommer au Tick suivant (`ConsumeBufferedJump`). |
| 6.3 | 🟠 | Les constantes de Quake **ne sont pas transposables** telles quelles : Quake court à 320 u/s, OVERDRIVE à 1500 (facteur ≈ 4.7). | Rééchelonner `AirStrafe_WishSpeedCap` et `_SpeedGainPerSec` avec `Speed_SprintCap`. Cf. `07_TUNING §7`. |
| 6.4 | 🟠 | Deux modèles d'air strafe existent et **ne se jouent pas pareil** : Quake 1/CPMA (`wishspeed` bridé ~30 → strafe à la touche latérale **seule**) et Quake 3 (`wishspeed` = vitesse de course → **Z+Q / Z+D + souris**). | **OVERDRIVE utilise le modèle Quake 3** (`WishSpeedCap = Speed_SprintCap`), validé par Louis au J3. |
| 6.5 | 🔴 | **`Character::Crouch()` ne fait rien si `CharacterMovement.NavAgentProps.bCanCrouch` est faux** — et c'est le défaut. Aucun warning, aucune erreur : la capsule ne bouge simplement pas. | Cocher « Can Crouch » sur le CMC du Blueprint (ou `set_properties` sur `NavAgentProps`). **Vérifier ensuite `CrouchedHalfHeight` en PIE**, pas dans l'éditeur. |
| 6.6 | 🔴 | **`MaxWalkSpeedCrouched` (défaut 300) remplace `MaxWalkSpeed` dès que le personnage est accroupi** — un slide à 1900 uu/s se fait écraser à 300 sans que `DriveCMC` (qui n'écrit que `MaxWalkSpeed`) ne s'en aperçoive. | `BPC_Slide.CacheTuning` pose `MaxWalkSpeedCrouched = Speed_HardCap` au `BeginPlay`. Toute future mécanique accroupie doit vérifier ce doublon de plafond. |
| 6.7 | 🟠 | **Un composant qui tick avant `BPC_MovementState` voit l'état de la frame précédente.** Au frame d'atterrissage, `CurrentState` est encore `Falling` : un `RequestState(Sliding)` y est refusé (§1.3). Une action bufferisée consommée « une seule fois » à l'atterrissage ne part donc **jamais**. | Ne pas consommer le buffer au moment de la tentative : **réessayer chaque frame** tant que la fenêtre est ouverte, et vider le buffer seulement en cas de succès. Vaut pour le dash (J5) et le wall ride (J6). |
| 6.8 | 🔴 | **Une trace de sol calibrée sur la capsule *accroupie* rate le sol dès que la pente monte.** Sous le **centre** d'une capsule posée sur un plan incliné, le sol est à `(HalfHeight − Radius) + Radius / cos θ` — pas à `HalfHeight`. Avec `R = 34`, `HH = 88` : **88 uu à plat, 102 uu à 45°**. Une trace de `HalfHeight_Slide + MaxStepHeight = 94` **ne touche rien** à 45°, et n'a que **0.7 uu** de marge à 30°. | La normale retombe sur son défaut `(0,0,1)` → **plus aucune pente n'existe** pour le gameplay : pas d'accélération en descente, pas de freinage en montée, joueur figé accroupi sur une rampe. **Zéro erreur, zéro warning** — la fonction « marche », elle renvoie juste toujours le même résultat. | Calibrer la portée sur la capsule **debout** : `CapsuleHalfHeight + MaxStepHeight` (138 uu ici), ce qui couvre jusqu'à `WalkableFloorAngle` = 50°. **Vérifier le calcul avant d'écrire la trace**, pas après le playtest. Et afficher la valeur mesurée dans l'overlay de debug : une normale de sol qui vaut toujours `(0,0,1)` est invisible autrement. |
| 6.9 | 💀 | **Un plafond de vitesse piloté à 0 devient un softlock quand l'état qui le lève est inatteignable.** `MaxWalkSpeedCrouched = 0` implémentait « on ne peut pas accélérer accroupi » — mais coincé sous un plafond bas, on ne peut **ni se lever ni bouger**, définitivement. | Joueur bloqué au milieu du tunnel de la zone B, sans aucun message. | Tout plafond mis à 0 doit avoir une **échappatoire** : ici `bForcedSlide` remonte le plancher à `Speed_Walk` pour ramper dehors. Se poser la question « quel état lève cette contrainte, et est-il toujours atteignable ? » **avant** de brider à 0. |
| 6.10 | 🔴 | **`bCanWalkOffLedgesWhenCrouching` vaut `false` par défaut dans UE**, indépendamment de `bCanWalkOffLedges` (qui est à `true`). Accroupi, le CMC **refuse de franchir le moindre rebord**. | Debout on tombe normalement d'une plateforme ; **en slide on heurte un mur invisible** à chaque bord et en bas de chaque rampe. Aucune erreur, aucun log — c'est un comportement voulu du moteur, pour les IA et les jeux à couverture. | Cocher **« Can Walk Off Ledges When Crouching »** sur le CMC (ou `set_properties` sur le CDO). **À vérifier dès qu'une mécanique accroupie existe** — le symptôme ressemble à un bug de collision et fait chercher au mauvais endroit. |
