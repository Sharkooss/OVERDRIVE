<div align="center">

# OVERDRIVE

### MOVE FAST. HIT HARD. NEVER STOP.

FPS arcade solo centré sur la vitesse, le momentum et la précision.

`Unreal Engine 5.8` · `Blueprint only` · `PC Windows` · `Solo dev` · `4 semaines`

</div>

---

## Le jeu

Le joueur traverse des niveaux courts et linéaires à très haute vitesse. Il enchaîne
**sprint, slide, dash 360°, wall ride, bunny hop et air strafing** pour construire et conserver
son momentum, détruit des ennemis au **laser hitscan** et au **poing** — un ennemi projeté contre
un mur y laisse la vie — puis est noté sur son **temps, ses kills, sa vitesse et son style**.

Son **rang (D → S)** ouvre un coffre d'**upgrades temporaires**. Une run complète mène à deux boss.

**Erreur = perte de vitesse. Jamais mort immédiate.**

---

## Démarrer

```bash
# Ouvrir le projet
"L:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" \
  "L:/Unreal Engine/Projects/OVERDRIVE/OVERDRIVE.uproject"
```

Prérequis : **Unreal Engine 5.8** · **Git LFS** (`git lfs install`) · **Blender** pour les assets.

---

## Documentation

👉 **Tout commence par [`Docs/00_INDEX.md`](Docs/00_INDEX.md).**

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Règles pour les agents IA — **à lire en premier** |
| [`Docs/01_VISION.md`](Docs/01_VISION.md) | Pitch, 5 piliers, contrat joueur |
| [`Docs/03_SCOPE_LOCK.md`](Docs/03_SCOPE_LOCK.md) | Ce qui est dans le jeu, et ce qui n'y sera pas |
| [`Docs/04_ROADMAP.md`](Docs/04_ROADMAP.md) | 28 jours, 4 gates |
| [`Docs/07_TUNING.md`](Docs/07_TUNING.md) | **Toutes** les valeurs de gameplay |
| [`Docs/Specs/`](Docs/Specs/) | 12 specs système détaillées |

---

## Structure

```
OVERDRIVE/
├─ CLAUDE.md            règles agents
├─ Docs/                documentation (source de vérité)
│  ├─ 00..10_*.md       fondations
│  ├─ Specs/            12 specs système
│  ├─ ArtDirection/     palette + références
│  └─ Journal/          journal de dev quotidien
├─ Art_Source/          sources Blender (.blend, .fbx) — hors Content
├─ Content/OVERDRIVE/   tout le contenu du jeu
├─ Config/
└─ .claude/             agents + commandes projet
```

---

## Commandes de projet

| Commande | Effet |
|---|---|
| `/jour` | État de la roadmap et les 3 tâches du jour |
| `/fin-de-journee` | Roadmap, tuning, journal, commit |
| `/tune <clé> <valeur>` | Modifie une valeur de tuning proprement |
| `/check-doc` | Audite la cohérence de la documentation |

Agents : `ue-gameplay` · `ue-leveldesign` · `ue-art` · `scope-guardian`

---

## Les 4 règles qui priment sur tout

1. **Blueprint uniquement.** Aucun C++.
2. **Aucune valeur en dur.** Tout vit dans `Docs/07_TUNING.md`.
3. **Le scope est verrouillé.** Une idée hors scope va au backlog, pas dans le jeu.
4. **Prototype → test → fun ? → polish ou supprime.** Jamais l'inverse.

> Le jeu doit être terminé avant d'être enrichi.
