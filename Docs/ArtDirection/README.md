# ArtDirection — références visuelles

## ⚠️ Fichier manquant

Le key art de référence validé par Louis a été partagé dans une conversation et **n'a pas pu être
enregistré sur le disque automatiquement**.

👉 **Dépose-le ici sous le nom exact : `KEYART_REF_02.png`**

Sa description écrite complète est conservée dans
[`../Specs/SPEC_ART_DIRECTION.md §2`](../Specs/SPEC_ART_DIRECTION.md) et sert de source de vérité
en attendant le fichier. La palette qui en a été extraite est dans [`PALETTE.md`](PALETTE.md).

### Historique

| Version | Date | DA | Statut |
|---|---|---|---|
| `KEYART_REF_01.png` | 2026-08-18 | Ville cyberpunk **nocturne**, néons, violets profonds, cyan | ❌ **Abandonnée** |
| `KEYART_REF_02.png` | 2026-08-18 | Ville **blanche en plein jour**, ciel bleu, accents rouge/violet/magenta | ✅ **En vigueur** |

Ne pas redéposer la v1 : toute la doc a été réalignée sur la v2 (`../11_ARBITRAGES.md D2, D3`).

---

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `PALETTE.md` | Palette officielle, tokens, couleurs réservées au gameplay |
| `KEYART_REF_02.png` | **À déposer** — key art principal |
| `REF_*.png` | Références additionnelles (libres) |

## Convention de nommage des références

```
KEYART_REF_<NN>.png        key art officiel du projet
REF_ENV_<Nom>.png          référence d'environnement
REF_ENEMY_<Nom>.png        référence d'ennemi
REF_UI_<Nom>.png           référence d'interface
REF_VFX_<Nom>.png          référence d'effet
MOOD_<World>_<NN>.png      planche d'ambiance par monde
```

## Règles

1. Une référence n'est **jamais** une consigne de copie : c'est une cible de sensation.
   En cas de conflit avec `SPEC_ART_DIRECTION.md`, **la spec gagne** (elle intègre les contraintes
   de production d'un dev solo en 4 semaines).
2. Toute référence ajoutée doit être **citée** dans `SPEC_ART_DIRECTION.md §2`, sinon elle n'existe pas
   pour les agents.
3. Ne pas stocker ici les assets sources de production — ils vont dans `Art_Source/`
   (cf. `../06_CONVENTIONS.md §9`).
4. Les images de ce dossier sont suivies par Git LFS.
