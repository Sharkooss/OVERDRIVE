# 02 — GAME DESIGN DOCUMENT (référence d'origine)

> **Document d'intention, rédigé par Louis en préproduction (v1.0, 2026-08-18).**
> Il est conservé comme **trace de l'intention originale**. Il n'est pas modifié au fil du développement.
>
> ⚠️ **Pour implémenter, utilise les documents dérivés** :
> valeurs → `Docs/07_TUNING.md` · systèmes → `Docs/Specs/` · scope → `Docs/03_SCOPE_LOCK.md`.
> En cas de contradiction, **les documents dérivés font foi** — ils intègrent les arbitrages postérieurs.

| | |
|---|---|
| Moteur | Unreal Engine 5.8 |
| Développement | Solo |
| Technologie | Blueprints |
| Temps disponible | ~20 h/semaine |
| Durée de production cible | 4 semaines |
| Scope cible | 6 niveaux + 2 boss |

---

## 1. VISION

FPS arcade stylisé centré sur la vitesse, le momentum et la précision. Niveaux linéaires composés de
grands espaces permettant d'accumuler et de conserver de la vitesse.

Outils de déplacement : Sprint · Slide · Dash 360° · Wall Ride · Jump · Bunny Hop · Air Strafing.
La vitesse peut dépasser largement la vitesse de déplacement normale. Le joueur doit apprendre à
enchaîner les mouvements pour construire son momentum.

Combat : **laser hitscan à tir unique** et **melee à fort knockback**.
Les erreurs sont sévèrement punies : recevoir un projectile ou une attaque fait perdre une quantité
importante de vitesse.

Fin de niveau → score (temps, kills, vitesse, style/flow) → rang **S / A / B / C / D** → coffre →
upgrades aléatoires temporaires. À la mort, la run est perdue et les upgrades temporaires disparaissent.

## 2. PILIERS

**1 — MOVEMENT** : le joueur doit aimer simplement se déplacer. Rapide, fluide, précis, prévisible,
satisfaisant, récompensant le skill.
**2 — MOMENTUM** : la vitesse est une ressource de gameplay. La construire, la conserver, la perdre,
la récupérer, atteindre des vitesses très élevées par la maîtrise.
**3 — COMBAT** : rapide. Les ennemis ordinaires meurent vite. Le joueur ne reste jamais immobile.
Mouvement et combat fonctionnent ensemble.
**4 — SCORE** : donner envie de rejouer pour améliorer temps, kills, style, score, rank. Encourager le S Rank.
**5 — JUICE** : chaque action importante a un feedback clair (animation, caméra, FOV, VFX, SFX, musique,
impacts, particules, UI, transitions). **Le sound design est une feature de gameplay, pas une finition.**

## 3. BOUCLE DE JEU

```
MENU → START RUN → LEVEL → COMBAT + MOVEMENT → FIN DU LEVEL
     → CALCUL DU SCORE → RANK → COFFRE → UPGRADE
     → LEVEL SUIVANT → … → BOSS → NIVEAUX SUIVANTS → BOSS FINAL → FIN DE RUN
```

## 4. STRUCTURE DE LA RUN

**WORLD 1** : Level 01 · Level 02 · Level 03 · Boss 01
**WORLD 2** : Level 04 · Level 05 · Level 06 · Boss 02 (final)

La structure doit rester assez modulaire pour ajouter plus tard niveaux, boss, ennemis, upgrades et armes
sans refaire le système central.

---

## MOVEMENT

**5 — Philosophie.** Vitesse de base relativement élevée, mais vitesse maximale théorique **beaucoup**
plus élevée, inatteignable par simple sprint. Elle nécessite une combinaison de mécaniques :
`Sprint → Slide → Jump → Air Strafing → Wall Ride → Jump → Dash → Wall Ride → Slide`.
Le joueur expert doit être capable d'aller beaucoup plus vite qu'un débutant.

**6 — Vitesse.** Valeur interne continue, pas des paliers nommés.
Échelle conceptuelle : `0` immobile · `100` normal · `150` sprint · `200` très rapide · `300` excellent ·
`400` expert · `500+` extrême. Affichage HUD possible : `SPEED: 347`. Les km/h ne sont pas obligatoires.
→ *Mapping vers les uu/s : `Docs/07_TUNING.md §1`.*

**7 — Accélération.** Progressive vers la vitesse cible. Pas d'accélération instantanée, pour des transitions fluides.

**8 — Sprint** (`Shift`). Augmente la vitesse, permet d'entrer en slide, construit du momentum.
**Plafond relativement bas — ne doit jamais permettre d'atteindre la vitesse maximale théorique.**

**9 — Slide** (`Ctrl`/`C`). Mécanique de mouvement, pas d'évitement. Entrée depuis le sprint.
Conserve la vitesse, donne un petit boost, permet de passer sous des obstacles, maintient le momentum,
durée limitée. Doit s'enchaîner agréablement avec jump, dash, wall ride.

**10 — Jump.** Assez permissif pour permettre bunny hopping, franchissement, transitions vers les wall rides
et air strafing. Le joueur conserve une grande partie de sa vitesse en l'air.

**11 — Bunny hop.** Relance du mouvement en enchaînant les sauts correctement.
**Jamais nécessaire pour terminer un niveau**, mais améliore les performances d'un joueur expert.
Objectif : skill floor faible, skill ceiling élevé.

**12 — Air strafing.** Influence de la trajectoire horizontale en l'air : correction, maintien du momentum,
approche d'un wall ride, optimisation. Assez permissif pour être amusant, assez contrôlable pour récompenser la maîtrise.

**13 — Dash.** Libre sur 360°, direction déterminée par l'input de mouvement. **Conserve la vitesse horizontale**
(`250 speed → Dash → 250 speed`). Ne donne pas automatiquement un énorme boost. Il sert à changer de direction,
franchir une distance, atteindre un mur, corriger une trajectoire, maintenir le flow.

**14 — Wall Ride.** Mécanique avancée : `Wall Ride → Jump → Air Strafe → autre mur → Wall Ride`.
Conserve une grande partie de la vitesse horizontale, permet des trajectoires extrêmement rapides,
plusieurs murs consécutifs. Le level design doit créer les espaces le permettant.

**15 — Perte de vitesse.** La vitesse est une ressource. Certaines erreurs la réduisent fortement :
projectile ennemi, collision dangereuse, mauvaise trajectoire, chute, arrêt brutal.
Le joueur n'est pas immobilisé systématiquement, il doit pouvoir récupérer son momentum.
**Principe : `Erreur = perte de vitesse`, jamais `Erreur = mort immédiate`.**

**16 — Collisions.** À tester très tôt. Une collision légère ne doit pas arrêter complètement le joueur.
Une collision majeure peut réduire fortement la vitesse, provoquer un feedback caméra, jouer un son,
interrompre temporairement le mouvement.

---

## COMBAT

**17 — Deux actions seulement** : Laser et Melee. Pas d'arsenal complexe en v1.

**18 — Laser.** Hitscan, aucun projectile physique.
`Input → Line Trace → Hit → Damage → VFX → SFX`. Simple, précis, performant, adapté au FPS rapide.

**19 — Tir.** Tirs individuels : chaque clic produit un tir. Pas d'automatique. Encourage la précision.

**20 — Cooldown.** Court cooldown par tir, pas de spam instantané. Assez court pour garder le rythme arcade.

**21 — Heat.** Jauge de chaleur au lieu de munitions. Chaque tir ajoute de la chaleur, qui diminue
progressivement quand le joueur ne tire pas. Rythme visé :
`Tir → Tir → Tir → chaleur élevée → arrêter → refroidissement → tir`.

**22 — Surchauffe.** Si la chaleur atteint le maximum : **Overheat**. Impossible de tirer, feedback sonore,
visuel et UI clairs. Assez court pour ne pas casser le flow.

**23 — Headshot.** Activés. Dégâts énormes. Sur les ennemis faibles : **headshot = one shot**.
Récompense précision, connaissance des ennemis, prise de risque.
Feedback particulièrement fort : son distinct, VFX, hitmarker spécial, petit hit-stop, animation de réaction.

**24 — Melee.** Attaque courte portée, **très fort knockback**. Sert à repousser, interrompre, tuer,
ou modifier la position d'un ennemi.

**25 — Collision avec le décor.** Un ennemi projeté contre un mur reçoit énormément de dégâts :
`Melee → Knockback → Mur → énormes dégâts`. Le joueur apprend à positionner les ennemis.
Permet du combat environnemental sans système complexe.

**26 — Melee propulsif.** Transformer le melee en outil de propulsion est **expérimental**, hors MVP.
Si c'est fun et techniquement raisonnable → intégration. Sinon → suppression sans impact sur le reste.

---

## ENNEMIS

**27 — Scope** : 3 archétypes + boss. Rapides à tuer. Ils existent pour créer des obstacles, forcer des décisions,
récompenser la précision, interrompre le flow en cas d'erreur, et participer au score.

**28 — Grunt.** Faible HP, déplacement simple, attaque courte portée ou charge, facile à tuer.
Rôle : créer le rythme, permettre de pratiquer l'aim.

**29 — Shooter.** Ennemi à distance, projectiles assez lents et visibles pour être évités.
Un impact **réduit fortement la vitesse du joueur**. Force l'usage de dash, slide, jump, wall ride, air strafe.

**30 — Tank.** Plus résistant, lent, volumineux, dangereux, plus long à tuer.
Crée la décision : *le tuer pour le score ou continuer sa trajectoire ?*
Doit rester assez rapide à tuer pour ne pas transformer le jeu en FPS classique.

**31 — Boss.** Deux maximum. Chacun : une arène, **deux phases maximum**, attaques lisibles, interactions avec
le mouvement. Le boss doit obliger le joueur à utiliser les mécaniques de déplacement.
**Interdit** : 10 phases, cinématiques complexes, systèmes de combat séparés, dizaines d'attaques.

---

## LEVEL DESIGN

**32 — Structure.** Niveaux linéaires, pas des labyrinthes :
`START → INTRODUCTION → ESPACE DE VITESSE → COMBAT → SECTION MOVEMENT → ESPACE DE VITESSE → COMBAT → FINAL RUN → FIN`

**33 — Grands espaces.** Chaque niveau contient des zones permettant accélération, bunny hop, slide,
wall ride, dash, trajectoires alternatives. **Un niveau ne doit jamais être uniquement des couloirs.**

**34 — Safe Way / Speed Way.** Certaines sections proposent une trajectoire facile et une trajectoire plus
difficile mais plus rapide.
```
              ┌── WALL RIDE ── SHORTCUT ──┐
START ────────┤                           ├──── FIN
              └── SAFE PATH ──────────────┘
```
Le raccourci n'est **jamais nécessaire** pour terminer le niveau. Il sert à améliorer le temps, le score,
et à atteindre le S Rank.

**35 — Durée.** Cible 1 à 3 minutes. Première completion accessible, temps expert nettement inférieur,
potentiel d'optimisation suffisant.

**36 — Checkpoints.** Autorisés si un niveau devient trop long. Sauvegardent la position, permettent un restart
rapide, conservent les upgrades, ne suppriment pas la difficulté. Privilégier des niveaux courts.

**37 — Restart.** Extrêmement rapide : `Death → Restart → gameplay` en quelques secondes.
Aucune longue transition. Le joueur doit pouvoir recommencer immédiatement pour chasser son score.

---

## SCORE & PROGRESSION

**38 — Composants** : TIME (plus faible = mieux) · KILLS · SPEED · STYLE/FLOW.

**39 — Style multiplier.** Gagné par : kills rapides, headshots, melee, wall ride, dash, slide, bunny hop,
maintien de vitesse, enchaînements. Diminue quand le joueur ralentit fortement, subit des dégâts,
reste immobile, rate des actions importantes.

**40 — Objectif du style.** Ne doit **pas** devenir un système de combo compliqué.
Le joueur doit comprendre intuitivement : *« Je joue bien → mon multiplicateur monte. »*
HUD : `STYLE x3.4`.

**41 — Rank.** `D / C / B / A / S`. Seuils **spécifiques à chaque niveau**, définis à partir de temps de
référence et de performance. Le S doit être difficile mais atteignable.

**42 — Écran de fin de niveau.**
```
LEVEL COMPLETE          S RANK          YOUR RUN
TIME       01:24        01:15           01:24
KILLS      18 / 20      20 KILLS        18 KILLS
MAX SPEED  342          STYLE x4.0      STYLE x3.2
STYLE      x3.2
SCORE      8,742
RANK       A
```
**Le joueur doit immédiatement comprendre pourquoi il n'a pas obtenu S.**

**43 — Loot.** Le rang détermine le coffre : `D → D Chest` … `S → S Chest`. Chaque coffre a sa table de loot.

**44 — Drop rates.** Les coffres supérieurs ont de meilleures chances de rareté, de meilleurs upgrades,
éventuellement davantage de choix. D : majoritairement Common. C : Common + faible chance Rare.
B : Common + Rare. A : Rare + possibilité Epic. S : Rare + Epic avec forte probabilité.

**45 — Raretés** : Common · Rare · Epic. **Pas de Legendary dans le MVP.**

**46 — Upgrades temporaires.** Valables uniquement pendant la run actuelle. À la mort, tous les upgrades
sont perdus, une nouvelle run recommence avec le personnage de base.

**47 — Upgrades de stats** : +HP · +Laser Damage · +Melee Damage · +Max Speed · +Acceleration ·
+Speed Retention · +Dash Recharge · +Slide Boost · +Wall Ride Duration · +Heat Capacity · +Heat Recovery.

**48 — Upgrades de gameplay** :
*Dash Recharge* (un kill réduit le cooldown du dash) · *Overcharged Laser* (premier tir après refroidissement
complet plus puissant) · *Momentum Core* (plus de vitesse conservée après un saut) · *Impact* (plus de knockback) ·
*Thermal Core* (chaleur qui diminue plus vite). Ces upgrades doivent rester simples.

**49 — Limitations.** Les upgrades ne doivent jamais supprimer la nécessité du skill, rendre le joueur invincible,
trivialiser les boss, casser le level design, ni multiplier les systèmes.
Ils rendent le joueur *un peu* plus rapide / précis / efficace / confortable.

**50 — Mort.** Ne supprime pas immédiatement la progression de la partie actuelle. Le joueur recommence au niveau
ou au checkpoint. Les upgrades restent actifs. Mais la performance finale est affectée : plus de temps,
moins de score, rank réduit, coffre de moindre qualité.

**51 — Fin de run.** Se termine au boss final. Si le joueur meurt définitivement, la run est ratée,
les upgrades sont perdus, il recommence une nouvelle run.

**52 — Pas de méta-progression dans le MVP.** Pas de niveau de joueur, monnaie permanente, arbre permanent,
XP, ni équipement permanent. Une méta-progression pourra être ajoutée ultérieurement.

---

## DIRECTION ARTISTIQUE & PRÉSENTATION

**53 — DA** : Low Poly Stylized + Toon / Cel Shader + Cartoon. Formes simples, silhouettes lisibles,
couleurs saturées, ombres toon, matériaux simples, VFX stylisés, environnement volontairement peu réaliste.
**La DA est choisie pour permettre de produire rapidement les assets.**

**54 — Personnages / ennemis** : humanoïdes / robots stylisés. Animation plus simple, silhouettes lisibles,
modularité, production rapide, cohérence low-poly. Reconnaissables instantanément.

**55 — Environnements** : kit modulaire — mur, sol, plateforme, rampe, colonne, mur de wall ride, tunnel,
obstacle, porte, arche, plateforme verticale. Les niveaux sont construits à partir de ces éléments.

**56 — VFX** (priorité) : tir laser, impact laser, headshot, kill, explosion, melee impact, dash, slide,
wall ride, projectile ennemi, hit joueur, overheat, chest, rank, boss.

**57 — Caméra** : FOV dynamique avec la vitesse, légère inclinaison au strafe, caméra de slide, feedback de dash,
léger shake d'impact, effet de vitesse. **Tout doit rester lisible, le shake doit être subtil.**

**58 — Audio** — priorité majeure. Chaque mécanique importante a un feedback audio.
*Movement* : jump, landing, dash, slide, wall ride, vitesse élevée.
*Combat* : laser, hit, headshot, kill, melee, impact mural, overheat.
*Interface* : rank, score, chest, upgrade, boss.

**59 — Musique** : rythmique, énergique, entraînante. Doit donner envie de bouger.
Musique dynamique complexe non obligatoire pour le MVP.
Version initiale : gameplay, boss, menu, variations/stingers.

**60 — Juice audiovisuel.** Chaque action doit être ressentie.
`CLICK → Flash → Rayon → Impact → Hit sound → Hitmarker → Micro shake → Réaction ennemie`
`Headshot → son spécial → VFX → ennemi détruit → micro hit-stop → feedback UI`

**61 — HUD minimal.** Obligatoire : HP, Heat, Crosshair, Dash, Speed, Style multiplier.
Secondaire : objectif, timer, kills. Le HUD reste minimal pour préserver la visibilité.

**62 — Menu principal (MVP)** : Play · Settings · Quit. Pas de boutique.

**63 — Settings** : Master/Music/SFX Volume, sensibilité souris, FOV, fullscreen/windowed, résolution,
éventuellement motion blur.

**64 — Inputs** : `WASD` movement · souris aim · `LMB` laser · `RMB` melee · `Espace` jump · `Shift` sprint ·
`Ctrl` slide · `Souris latérale / Q / E` dash. Remappables uniquement si le temps le permet.

---

## TECHNIQUE

**65 — Architecture Blueprint.**
`BP_PlayerCharacter` (movement, camera, input, health, speed, dash, slide, wall ride) ·
`BP_LaserWeapon` · `BP_MeleeComponent` · `BPC_Health` · `BPC_PlayerStats` · `BPC_UpgradeManager` ·
`BPC_ScoreManager` · `BP_RunManager` · `BP_LevelManager` · `BP_EnemyBase` (+ Grunt, Shooter, Tank) · `BP_BossBase`
→ *version détaillée et arbitrée : `Docs/05_ARCHITECTURE.md`.*

**66 — Data-driven design.** Les valeurs sont stockées dans des structures/data assets autant que possible :
`EnemyData`, `WeaponData`, `UpgradeData`, `LevelData`, `BossData`, `LootTableData`.
Cela permet de modifier les valeurs sans modifier constamment les Blueprints.

**67 — Game states** : `Main Menu → Run Starting → Gameplay → Level Complete → Loot → Next Level → Boss
→ Run Complete / Run Failed`.

**68 — Priorité absolue.** Si le projet prend du retard, conserver dans cet ordre :
`Movement > Laser > Enemy > Level > Score > Juice > Loot > Boss > Menus > Extras`

**69 — Features interdites pendant le mois** : nouvelles armes, multiplayer, procedural generation, crafting,
inventaire complexe, dialogue, cinématiques, lore complexe, meta progression, dizaines d'ennemis,
système de quête, open world, sauvegarde complexe.

**70 — MVP** : movement, sprint, jump, slide, dash, wall ride, air strafing, laser, heat, melee,
1 ennemi, 1 niveau, timer, score, rank, restart.
**Si le MVP n'est pas fun : ne pas continuer à produire du contenu.**

**71 — Vertical slice** : movement finalisé, laser finalisé, melee finalisé, 3 ennemis, 1 niveau complet,
1 mini-boss ou boss prototype, scoring, rank, loot, toon shader, VFX principaux, sound design principal,
musique, HUD, restart. Il doit représenter la qualité finale recherchée.

**72 — Contenu final** : L1 introduction au mouvement · L2 premières grandes sections de vitesse ·
L3 movement + combat · Boss 01 · L4 movement avancé · L5 sections de speed optimisées ·
L6 gauntlet final · Boss 02 final.

**73 — Roadmap** → `Docs/04_ROADMAP.md` (version détaillée et datée).

**74 — Règle de production.** `Prototype → Test → Fun ? → Oui : Polish / Non : Modifier ou supprimer`.
Ne jamais produire un système complet avant de vérifier qu'il est amusant.

**75 — Ordre du polish** : Movement · Combat · Audio · VFX · Camera · Level design · UI · Art secondaire.

**76 — Définition de "fini".** Une feature est terminée seulement si : elle fonctionne, elle est compréhensible,
elle possède un feedback, elle ne crée pas de bug majeur, elle fonctionne avec les autres systèmes,
elle a été testée en situation réelle. **« Le Blueprint fonctionne » ≠ « la feature est terminée ».**

**77 — Critère de qualité final.** Le joueur doit pouvoir faire :
`Sprint → Slide → Jump → Air Strafe → Wall Ride → Dash → Laser Headshot → Melee → Enemy Knockback
→ Speed Recovery → Wall Ride → Finish`
et avoir la sensation d'avoir accompli quelque chose. Le jeu récompense vitesse + précision + maîtrise.

**78 — Design philosophy.** Le jeu ne demande jamais *« as-tu assez de stats ? »* mais *« es-tu assez bon ? »*.
Les upgrades aident le joueur, elles ne remplacent pas son skill.

**79 — Risques principaux.**
| Risque | Solution |
|---|---|
| Movement trop compliqué | Construire chaque mécanique séparément. Pas de level design avant un movement stable |
| Vitesse difficile à contrôler | Tester énormément le feeling. Impressionnante mais lisible |
| Level design trop long | Limiter chaque niveau à 1–3 minutes |
| Trop de contenu | 3 ennemis, 2 armes, 6 niveaux, 2 boss. Aucun système supplémentaire sans raison |
| Loot trop complexe | Stats simples + quelques modifications de gameplay |
| Le joueur ignore les ennemis | Kills intégrés au score et au style |
| Le joueur s'arrête pour tirer | Ennemis rapides à tuer, laser précis, style récompensant le mouvement |

**80 — Tests de validation** → `Docs/10_DEFINITION_OF_DONE.md §3` (les 8 tests).

**81 — Définition du projet final.** *Un FPS arcade solo stylisé dans lequel le joueur traverse des niveaux
courts et linéaires à très haute vitesse, combine sprint, slide, dash, wall ride, bunny hop et air strafing
pour conserver son momentum, détruit rapidement des ennemis avec un laser hitscan et une attaque melee,
puis est évalué sur sa vitesse, son temps, ses kills et son style. Son rank lui donne accès à des coffres
contenant des upgrades temporaires. Une run complète mène à deux boss.*
Le jeu doit être **rapide, lisible, précis, satisfaisant, rejouable, stylé**, et surtout **FUN À CONTRÔLER**.

**82 — Scope final verrouillé** → `Docs/03_SCOPE_LOCK.md`.

**83 — Ce qui reste volontairement ouvert.** Ne pas décider trop tôt : valeurs exactes de vitesse,
vitesse maximale, durée et cooldown du dash, puissance du slide, durée du wall ride, valeurs de dégâts,
valeurs de heat, seuils exacts des ranks, probabilités des coffres, valeurs des upgrades, durée exacte
des niveaux, layout précis des niveaux, design définitif des boss, palette finale, nombre de props.
**Ces éléments seront déterminés par le prototype, pas par la théorie.**

**84 — Règle absolue du projet.** Toute nouvelle idée doit répondre :
*Est-ce que cette feature améliore directement le mouvement, le combat, le score, la progression ou le juice ?*
Si non, ou si elle augmente fortement le scope → **reportée après la v1**.
**Le jeu doit être terminé avant d'être enrichi.**

**85 — Objectif final.** Pas « un prototype avec plein de systèmes », mais
**un petit FPS complet, jouable du début à la fin, avec une identité visuelle, un movement reconnaissable,
un système de scoring, une progression temporaire, six niveaux, deux boss et suffisamment de polish
pour donner envie de recommencer une run.**
