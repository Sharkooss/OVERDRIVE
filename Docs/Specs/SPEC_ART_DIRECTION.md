# SPEC — DIRECTION ARTISTIQUE (v2)

> **Réécriture complète du 2026-08-18.** La DA a changé : on abandonne la ville néon nocturne
> en Unlit pour une **ville blanche en plein jour, rendue en éclairage réel**.
> Arbitrages fondateurs : `11_ARBITRAGES D2` (rendu éclairé, Lumen + VSM actifs), `D3` (palette
> fonctionnelle), `D32` (FPS, bras seulement), `D33` (ciel et atmosphère).
>
> Couleurs : **`Docs/ArtDirection/PALETTE.md` fait autorité, aucun HEX n'est dupliqué ici.**
> Nommage : `Docs/06_CONVENTIONS.md`. Valeurs de gameplay : `Docs/07_TUNING.md`.
> Kit modulaire : **`Docs/Specs/SPEC_LEVELDESIGN.md §3` (23 meshes), verrouillé, non redéfini ici.**
>
> **Critère d'arbitrage n°1 : la vitesse de production.** Un choix esthétique qui coûte plus de
> 90 min par asset est refusé, même s'il est plus joli.

---

## 1. Intention

OVERDRIVE se joue **en plein soleil, dans une ville blanche**. Le joueur doit ressentir de l'**air**,
de l'**élan** et de l'**évidence** : on voit loin, on comprend la trajectoire d'un coup d'œil, rien
n'est caché dans l'ombre. La beauté vient de la **lumière franche**, des **aplats** et de la **vitesse**,
jamais du détail. Ce qui est coloré est fonctionnel ; ce qui est blanc est du décor.

**Les 3 mots-clés : LUMINEUX · GÉOMÉTRIQUE · LISIBLE.**

**Pourquoi une v2.** La v1 (ville cyberpunk nocturne, néons, Unlit, éclairage simulé en matériau) est
**caduque**. La nouvelle key art repose sur des **ombres portées franches** et une **perspective aérienne
bleutée** : les simuler en Unlit coûterait plus cher en temps de production que de laisser Lumen les
calculer, pour un résultat plat. On garde donc le rendu éclairé du template et on obtient le look toon
**en post-process** (`11_ARBITRAGES D2`). Contrepartie assumée : la perf devient le **risque n°1 du projet**
(§5.5).

---

## 2. Références

**Fichier de référence à déposer dans `Docs/ArtDirection/` sous le nom exact `KEYART_REF_02.png`.**
Toute question de DA se tranche en regardant cette image.

> `KEYART_REF_01.png` (v1 nocturne) est **ABANDONNÉE**. Elle ne fait plus autorité sur rien.
> Si elle est encore présente dans le dossier, elle est conservée à titre d'archive uniquement.

### 2.1 Style
Low poly stylisé, **cel-shading propre**, aplats de couleur, formes géométriques nettes, très peu de
détail. Lisible, lumineux, optimiste. Repère : **un Mirror's Edge coloré et cartoon**.

### 2.2 Environnement
- Gratte-ciels **blancs et gris très clairs**, blocs cubiques, plateformes flottantes, toits praticables,
  gouffres entre les bâtiments.
- Ciel **bleu clair avec nuages blancs stylisés**, **soleil visible**, lumière franche.
- **Ombres portées nettes et douces** : contour net, pénombre légère. Ce sont elles qui donnent le volume.
- **Perspective aérienne** : les bâtiments lointains virent au **bleu pâle** et perdent leur contraste.

### 2.3 Marquages de traversée
Des **bandes lumineuses rouge/corail** courent sur les **arêtes de toit**, les **rampes** et les **murs**.
Elles ne décorent pas : elles **indiquent les surfaces qu'on parcourt**. La key art montre le personnage
courant sur un **rail rouge courbe** et sur une **large diagonale rouge appliquée à un mur**.

### 2.4 Signalétique
Panneaux et écrans **violets** portant des **chevrons blancs `»`** qui donnent la direction.
Un panneau « RUN FASTER ». Une enseigne verticale « OVERDRIVE » en rouge lumineux.

### 2.5 Personnage (planche de character design)
4 vues T-pose + une pose de course. Humanoïde athlétique **encapuchonné**, tenue près du corps
**bleu nuit très foncé**, panneaux **violets**, accents **rouge/magenta** (chevrons de torse, semelles,
lignes de jambe). Visage masqué, **visière/masque rouge**. Silhouette anguleuse, très lisible.
→ Usage au MVP : **identité visuelle et bras FP uniquement** (§8, `11_ARBITRAGES D32`).

### 2.6 Assets d'environnement (planche)
Panneaux publicitaires sur pied, écrans, bornes cubiques, caisses, rambardes, rails courbes, petits blocs.
Tous **blanc / gris clair avec accents violets et liserés rouges**.

### 2.7 Logo
« OVERDRIVE » en **italique très gras**, dégradé **magenta → rouge**, précédé de deux barres obliques `//`
violettes. Tagline « MOVE FAST. HIT HARD. NEVER STOP. » en violet.
→ C'est une **image** (`T_Logo_Overdrive_D`), pas une police.

### 2.8 Nuancier de la planche
Bleu nuit profond · violet · magenta/rose · rouge/corail · blanc cassé. Tokens : `PALETTE.md §2`.

---

## 3. Palette et règle d'usage

**Codes HEX, tokens, ambiances, UI : `Docs/ArtDirection/PALETTE.md`. Ce document ne duplique aucune valeur.**

### 3.1 La règle capitale — le fond est CLAIR

À 3000 uu/s le joueur ne lit pas une forme, **il lit un contraste**. Le monde est blanc et lumineux :
un élément clair y **disparaît**. Donc :

> **Toute information de gameplay doit être FONCÉE ou TRÈS SATURÉE.**
> C'est l'inverse exact de la contrainte v1, où l'information était « ce qui brille ».

Conséquences directes :
- Un émissif blanc ou pastel ne signale **rien** en plein jour. Interdit comme signal.
- Les silhouettes qui doivent être vues (ennemis, UI, crosshair) sont **sombres** (navy / charbon).
- Les signaux positifs (traversée, joueur) sont **saturés** (rouge, magenta), pas lumineux.

### 3.2 Assignation fonctionnelle (`11_ARBITRAGES D3`)

| Information | Token | Où on la voit |
|---|---|---|
| **Je peux courir dessus** — wall ride, rail, boost | `OD_Red_Traversal` | bandes sur arêtes, rampes, murs |
| **Va par là** | `OD_Purple_Primary` | chevrons `»`, panneaux, écrans |
| **C'est moi** — laser, dash, melee, traînée | `OD_Magenta_Player` | tout ce qui émane du joueur |
| **C'est hostile** | `OD_Amber_Enemy` | visière, émissif, projectile ennemi |
| **Ça va me tuer** | `OD_Red_Danger` | kill volume, attaque imminente |

Le rouge et le violet **existent dans le décor** en v2 — c'est voulu : ils y sont **fonctionnels**
(rouge = surface parcourable, violet = signalétique). Un rouge posé sur une surface non parcourable
est un **bug de lisibilité**, pas une décoration.
`OD_Cyan_Accent` et `OD_Red_Enemy` (v1) n'existent plus.

### 3.3 Test de validation obligatoire par niveau
Capture d'écran → passage en **niveaux de gris**. Les **ennemis** et les **bandes de traversée** doivent
rester les zones de **contraste maximal** (les plus foncées ou les plus saturées) de l'image.
Si le niveau se lit comme un aplat gris uniforme, il est refusé (§10.4).

---

## 4. Le rendu cel-shadé sur scène éclairée

### 4.1 La décision

| Approche | Verdict |
|---|---|
| Unlit + N·L simulé en Material Function (v1) | **Abandonnée.** Ne produit pas d'ombre portée, or l'ombre portée **est** la DA v2. |
| Shading model toon par matériau (banding dans chaque `M_`) | Refusé. Il faudrait le répliquer dans 6 masters, il ne s'applique **pas** aux VFX, ni au ciel, ni aux décals, et chaque nouveau matériau devient une occasion de diverger. |
| **Post-process : posterisation de la luminance + outlines Sobel** | **RETENU.** |

**Pourquoi le post-process ici :**
1. **Un seul point de contrôle.** Un asset (`PP_ToonPost`) règle le look de tout le jeu. On change
   le nombre de bandes une fois, pas dans 6 graphes.
2. **Ça marche sur tout** : géométrie, ciel, fog, décals, **VFX Niagara**, arme FP. Un shading custom
   par matériau laisse tout le reste en rendu réaliste — c'est ce qui trahit un faux toon.
3. **Compatible Lumen.** On posterise la Scene Color **après** l'éclairage : les ombres de VSM et le
   rebond de Lumen deviennent des **bandes franches**, exactement le look de la key art.
4. **Zéro coût de production par asset.** Un matériau standard suffit (§6.4).

### 4.2 `PP_ToonPost` — le matériau de post-process

Un seul asset dans `Content/OVERDRIVE/Art/PostProcess/`.
`Material Domain = Post Process` · `Blendable Location = **Before Tonemapping**` · porté par
**`BP_PlayerCameraManager`** (`11_ARBITRAGES D27` : les blendables réactifs suivent le joueur,
le `PostProcessVolume` ne porte que les réglages statiques).

**Passe A — posterisation de la luminance**

On ne quantifie **pas** la couleur RGB (ça produit des dérives de teinte et détruit la palette).
On quantifie **la luminance seule**, puis on réapplique la teinte d'origine :

```
Scene   = SceneTexture:PostProcessInput0.rgb
L       = dot( Scene , (0.2126, 0.7152, 0.0722) )          // luminance
Lq      = floor( saturate(L / LuminanceRange) * Bands ) / (Bands - 1) * LuminanceRange
Lq      = lerp( L , Lq , PosterizeStrength )                // dosage
Lq      = Lq + ShadowLift * (1 - Lq)                        // les ombres ne tombent JAMAIS au noir
Out     = Scene * ( Lq / max(L, 0.0001) )                   // on ne change que la valeur, pas la teinte
Out     = lerp( Out , Out * ShadowTint , 1 - Lq )           // les bandes basses virent au bleu froid
```

**Passe B — outlines Sobel (deux sources)**

- **Sobel sur `SceneTexture:SceneDepth`** → silhouettes et séparation des volumes.
  Normalisation par la profondeur : `Edge = abs(gradient) / (SceneDepth * DepthSensitivity)`
  → **épaisseur constante à l'écran** quelle que soit la distance.
- **Sobel sur `SceneTexture:WorldNormal`** → **plis internes** (arête de toit, chanfrein, rebord de
  plateforme) que la profondeur ne détecte pas sur une surface continue.
  **Ceci est possible en v2 et ne l'était pas en v1** : en rendu éclairé, le GBuffer contient une
  normale fiable. C'est un gain net du passage à l'éclairé.
- Les deux edges sont combinés par `max()`, seuillés, puis composés en `lerp(Out, OutlineColor, Edge)`.

**Passe C — perspective aérienne (optionnelle, 3 nodes)**
Fade des outlines et de la posterisation au-delà de `MaxOutlineDistance` pour ne pas cerner la skyline
et laisser le fog bleuir le fond.

### 4.3 Paramètres exposés

| Paramètre | Type | Défaut | Plage | Rôle |
|---|---|---|---|---|
| `Bands` | Scalar | `4` | 2–6 | Nombre de paliers de luminance. 3 = très cartoon, 4 = défaut, 6 = subtil |
| `PosterizeStrength` | Scalar | `0.85` | 0–1 | Dosage entre rendu continu et posterisé. `1` = aplats purs |
| `LuminanceRange` | Scalar | `1.4` | 1–3 | Plage de luminance quantifiée. Au-delà, les hautes lumières restent continues (évite le banding du ciel) |
| `ShadowLift` | Scalar | `0.12` | 0–0.3 | Plancher des ombres. **Jamais 0** : le noir pur est interdit (§12) |
| `ShadowTint` | Vector | `OD_Grey_Shadow` | — | Teinte des bandes basses. Bleu froid, cohérent avec la lumière du ciel |
| `OutlineColor` | Vector | `OD_Navy_Ink` | — | Couleur des contours. **Jamais `#000000`** |
| `OutlineThickness` | Scalar | `1.5` | 0.5–3 | Épaisseur en pixels |
| `DepthSensitivity` | Scalar | `0.6` | 0.1–2 | Seuil du Sobel de profondeur |
| `NormalSensitivity` | Scalar | `0.5` | 0.1–2 | Seuil du Sobel de normale (plis internes) |
| `MaxOutlineDistance` | Scalar | `15000` | uu | Fade des contours au loin |
| `SkyMask` | Static Switch | `true` | — | N'applique ni posterisation ni outline au ciel (`SceneDepth` > 100000) |

### 4.4 Anti-aliasing
**TSR obligatoire.** Une outline de 1,5 px scintille en FXAA et bave en TAA.
`Default Screen Percentage = 100`. Ne pas descendre sous 80 % : les contours disparaissent.

### 4.5 Ce que le post-process ne fait PAS
Il ne remplace pas la **couleur authored**. Les aplats viennent des matériaux (§6), la posterisation
ne fait que **discrétiser l'éclairage**. Si un mur est gris sale avant le post-process, il sera gris
sale après. Le look toon se joue **d'abord** dans la palette, ensuite dans le post-process.

---

## 5. Éclairage — le nouveau chapitre central

> `11_ARBITRAGES D2` et `D33` font foi : **Lumen et Virtual Shadow Maps restent ACTIFS**, réglages du
> template conservés (`r.DynamicGlobalIlluminationMethod=1`, `r.ReflectionMethod=1`,
> `r.Shadow.Virtual.Enable=1`). **Pas de HDRI, pas de Sky Sphere texturée.**

### 5.1 Le setup d'un niveau — exactement 5 actors

Tous portés par **`BP_LightingRig`** (§5.4), un seul actor placé par niveau.

| Actor | Réglage | Valeur World 1 (*Ascension*) |
|---|---|---|
| **`DirectionalLight`** | Mobility | **Movable** |
| | Rotation (Pitch / Yaw) | **−48° / −35°** — soleil haut, ombres longues d'environ 0,9 × la hauteur |
| | Intensity | **6.0** lux |
| | Light Color | `OD_Sun_Warm` |
| | Cast Shadows | **✔** — les ombres portées **sont** la DA |
| | Source Angle | **1.5°** — pénombre légère : contour net mais pas dur |
| | Dynamic Shadow Distance | **20000 uu** |
| | Volumetric Shadow / Ray Traced Shadow | ✘ / ✘ |
| **`SkyLight`** | Source Type | **SLS Captured Scene** (capture le `SkyAtmosphere`) |
| | Mobility | **Movable**, Real Time Capture **✔** |
| | Intensity | **1.8** |
| | Cast Shadows | **✘** — l'occlusion vient de Lumen et de l'AO |
| **`SkyAtmosphere`** | Rayleigh Scattering Scale | **0.033** (défaut) |
| | Mie Scattering / Absorption | défauts — ne pas toucher |
| | Multiscattering | **0.75** — ciel plus laiteux, cohérent avec les aplats |
| **`ExponentialHeightFog`** | Fog Density | **0.008** (une valeur par monde, `PALETTE.md §4`) |
| | Fog Height Falloff | **0.15** — le fog monte et bleuit les gratte-ciels lointains |
| | Fog Inscattering Color | `OD_Sky_Pale` |
| | Start Distance | **2000 uu** — rien de bleuté à moins de 20 m |
| | Directional Inscattering | **✔**, Exponent `4.0`, Color `OD_Sun_Warm` — halo autour du soleil |
| | **Volumetric Fog** | **✘** (1–3 ms pour un gain nul une fois posterisé) |
| **`PostProcessVolume`** | Unbound ✔, Priority 0 | réglages statiques uniquement (`11_ARBITRAGES D27`) |

**C'est l'`ExponentialHeightFog` qui produit la perspective aérienne de la key art**, pas un shader.
C'est le premier réglage à ajuster si la profondeur ne se lit pas.

### 5.2 Les nuages — arbitrage pour un dev solo

**`VolumetricCloud` est REFUSÉ.** 2 à 5 ms/frame, illisible une fois posterisé, et sans intérêt dans un
jeu où le regard est sur le sol et les murs. Pas de budget pour un ciel qu'on ne regarde jamais.

**Retenu : nuages en cartes.** 4 à 6 `SM_Cloud_Card_*` (quads de 2 tris) posés très loin (> 30000 uu),
matériau `M_Env_Emissive` en **Unlit / Masked**, texture `T_CloudShape_M` (512, alpha, formes stylisées
à bords durs). Immobiles, sans ombre, coût nul. Le dégradé de ciel vient du `SkyAtmosphere`.

### 5.3 Preset `PostProcessVolume` (Unbound, Priority 0)

| Groupe | Réglage | Valeur |
|---|---|---|
| Exposure | Metering Mode | **Manual** (la scène est uniformément claire : l'auto-exposure ne fait que pomper) |
| | Exposure Compensation · Physical Camera | `0.0` · ✘ |
| Bloom | Method / Intensity / Threshold | `Standard` / **`0.6`** / **`1.1`** — discret : en plein jour le bloom délave le blanc |
| Lens | Vignette **`0.2`** · Chromatic Aberration `0.0` | piloté 0 → `ChromaticAberration_MaxAtFullSpeed` (`07_TUNING §16`) |
| | Lens Flare / Film Grain | `0.0` / `0.0` |
| Film | Expand Gamut `0.0` · Tone Curve Amount **`0.5`** | au-dessus, le tonemapper écrase les aplats |
| Color Grading | Saturation `1.10` · Contrast `1.05` · Temperature `6500` | |
| Rendering | **Ambient Occlusion Intensity `0.4`** | recolle les objets au sol sur fond blanc — indispensable en v2 |
| | Motion Blur / DOF | **`0.0`** / `0.0` (illisibles à 3000 uu/s) |
| | Lumen Scene Detail / Final Gather Quality | `0.5` / `0.5` (§5.5) |
| Blendables | — | **vide.** Tous les blendables sont sur `BP_PlayerCameraManager` |

Sauvegardé en preset, **identique dans les 8 niveaux**. Seul le `PDA_WorldData` change.

### 5.4 `BP_LightingRig` — un actor, un DataAsset

`BP_LightingRig` possède les 4 composants d'éclairage et une variable `WorldData : PDA_WorldData`
(Instance Editable). Au `BeginPlay` :

```
1. Lire WorldData                             (schéma : 08_DATA_SCHEMAS §3)
2. Appliquer aux composants :
     DirectionalLight ← SunColor, SunIntensity, SunRotation
     SkyLight         ← SkyIntensity, puis Recapture Sky
     SkyAtmosphere    ← SkyZenithColor, SkyHorizonColor
     HeightFog        ← FogColor, FogDensity
3. Pousser dans MPC_Global : SunDirection, SunColor, AmbientColor, FogColor, WorldTint
```

Changer de monde = **un seul DataAsset à échanger**. Aucun matériau dupliqué, aucun asset refait.
C'est ce qui rend 4 ambiances tenables en 4 semaines.

> **Écart signalé à reporter dans `08_DATA_SCHEMAS §3`** : `PDA_WorldData.SunDirection` y est décrit
> comme « direction du N·L simulé (rendu Unlit) ». En v2 c'est la **rotation réelle du
> `DirectionalLight`**. Le schéma gagne 4 champs : `SunIntensity` (Float), `SkyIntensity` (Float),
> `SkyZenithColor` / `SkyHorizonColor` (Linear Color), `FogDensity` (Float).

Les valeurs des 4 ambiances (ciel, structure, ombre, accent, soleil, fog density) sont dans
**`PALETTE.md §4`**, et nulle part ailleurs.

### 5.5 Budget perf — le risque n°1 du projet

Le passage à l'éclairé a un coût réel. **Cible : GPU < 10 ms** (16,6 ms disponibles à 60 fps).
Contrôle hebdomadaire obligatoire : `stat unit` + `stat GPU` dans `L_Sandbox_Movement`.

| Règle | Valeur |
|---|---|
| Lumières dynamiques **projetant des ombres** | **1 par niveau** — le `DirectionalLight`. Aucune autre, jamais. |
| Lumières d'appoint (`PointLight` / `RectLight`) | **6 max par niveau**, `Attenuation Radius < 800`, **`Cast Shadows ✘`**, Movable |
| `r.Shadow.Virtual.ResolutionLodBiasDirectional` | **1.0** — baisse la résolution VSM d'un cran, invisible après posterisation, ~1 ms gagné |
| Lumen — Scene Detail / Final Gather | **0.5 / 0.5** (dans le `PostProcessVolume`) |
| Lumen — `r.Lumen.TraceMeshSDFs` | **0** — sur de la géométrie cubique le tracing global suffit |
| Portée de Lumen — `r.LumenScene.ViewDistance` | **20000 uu**, alignée sur la Dynamic Shadow Distance |
| Nanite | **✘ partout** — coût fixe supérieur au gain à 150 tris/module |
| Substrate | **✘** (recommandé par `D2` : complique tous les graphes sans bénéfice) |
| Translucidité | `M_Hologram` uniquement, **jamais plein écran**, **jamais plus de 3 couches** |
| Instancing | **HISM obligatoire** pour tout module répété > 20 fois dans un niveau |
| LOD | Aucun sur les modules (< 300 tris). LOD auto 3 niveaux sur ennemis et boss |

**Interdits perf, sans exception :** Volumetric Fog · Volumetric Clouds · Ray Tracing matériel ·
SSR en plus de Lumen · toute lumière mobile avec ombres autre que le soleil · `Cast Shadow` sur les
VFX et les décals · Static Lighting (aucun lightmap UV dans le projet).

**Ordre de coupe si on dépasse 10 ms** (on descend la liste, on ne saute pas d'étape) :
`ResolutionLodBiasDirectional 1.0 → 2.0` → `Lumen Final Gather 0.5 → 0.25` →
`Dynamic Shadow Distance 20000 → 12000` → `r.DynamicGlobalIlluminationMethod=0`.
Ce dernier point est le **filet de sécurité du projet** : sans Lumen, le `SkyLight` + l'AO + la
posterisation donnent encore un rendu correct. On perd le rebond, pas le look.

---

## 6. Matériaux

**Règle absolue : très peu de textures, beaucoup de Material Instances qui ne changent que des couleurs.**
Un nouveau look = un `MI_`, **jamais** un nouveau `M_`.
Plafond de textures du projet : **6** — `T_CloudShape_M`, `T_Chevron_M`, `T_Noise_01`, `T_Scanline_01`,
`T_Dither_01`, `T_Logo_Overdrive_D`.

Masters à créer dans `Content/OVERDRIVE/Art/Materials/Master/` :

| Master | Domaine / Blend | Paramètres exposés |
|---|---|---|
| `M_Env_Base` | **Default Lit** / Opaque | `BaseColor`, `EdgeAccentColor`, `EdgeAccentWidth` (uu), `bEdgeAccent` (Static Switch), `Roughness`, `FakeAO_VC` (Static Switch → `VertexColor.B`), `TintVariation_VC` (→ `VertexColor.A`) |
| `M_Env_Emissive` | Unlit / Opaque ou Masked | `EmissiveColor`, `Intensity` (0–20), `PulseSpeed`, `PulseAmount`, `ScrollSpeed`, `ScrollDirection`, `bUseAlphaMask` |
| `M_Enemy` | **Default Lit** / Opaque | `ShellColor`, `PlateColor`, `VisorColor`, `VisorIntensity` (0–20), `AccentColor`, `HitFlashAmount` (0–1, DMI), **`DissolveAmount` (0–1)**, `DissolveEdgeColor`, `DissolveEdgeWidth`, `EmissiveMask_VC` (`VertexColor.R`), `PlateMask_VC` (`VertexColor.G`) |
| `M_Player` | **Default Lit** / Opaque | `SuitColor`, `PanelColor`, `AccentColor`, `GloveColor`, `HeatEmissiveColor`, `HeatRatio` (lu dans `MPC_Global`), `Roughness` |
| `M_Sign` | Unlit / Masked | `PanelColor`, `GlyphColor`, `GlyphTexture` (`T_Chevron_M`), `ScrollSpeed`, `EmissiveIntensity` (0–8) |
| `M_Hologram` | Unlit / **Translucent Additive** | `HoloColor`, `Opacity`, `ScanlineDensity`, `ScanlineSpeed`, `FresnelPower`, `GlitchAmount`, `GlitchSpeed` |

Masters utilitaires : `M_Dev_Grid` (blockout, checker procédural, **Default Lit**), `PP_ToonPost` (§4),
`PP_SpeedLines`, `DEC_LaserScorch`, `DEC_ShadowBlob` *(supprimé — l'ombre est réelle en v2)*.

> **`DissolveAmount` vit sur `M_Enemy`, et nulle part ailleurs** (`11_ARBITRAGES D5`). C'est le seul
> mécanisme de mort d'un ennemi : jamais de ragdoll, jamais de Physics Asset. Piloté par une DMI sur
> `BP_EnemyBase`, sur la durée `Death_DissolveDuration` (`07_TUNING §13`).

### 6.1 Pas de grille world-aligned en v2
`M_Env_Grid` (v1) disparaît : la grille émissive était un artefact du monde nocturne. En v2 la lecture
du sol vient de l'**ombre portée** et des **liserés rouges** sur les arêtes praticables.
Conséquence conservée : **les modules d'environnement n'ont toujours pas besoin d'UV utile** — les
liserés sont produits par `bEdgeAccent` (masque sur `AbsoluteWorldPosition` + `WorldAlignedBlend`)
ou par un mesh dédié posé dessus.

### 6.2 Pourquoi un matériau standard donne un rendu propre une fois posterisé
La chaîne est : **couleur en aplat → éclairage réel → posterisation**. Un `Default Lit` avec
`BaseColor` = aplat de palette, `Metallic = 0`, `Specular = 0.2`, `Roughness = 0.75` produit un dégradé
doux que `PP_ToonPost` découpe en 3–4 bandes franches. C'est **exactement** le cel-shading de la key art,
sans un seul node de shading custom.

**Réglages imposés sur tout `MI_` d'environnement :**
`Metallic = 0` (aucune exception) · `Specular = 0.2` · `Roughness ∈ [0.6 ; 0.9]` · aucune normal map ·
aucun clear coat · aucun SSS.
Sous `Roughness 0.5`, un highlight spéculaire survit à la posterisation et fait « plastique mouillé ».

### 6.3 Émissifs
Sur fond clair, un émissif faible est **invisible**. Intensités de référence (`PALETTE.md §8`) :
`1.0` décor · `3.0` signalétique · `8.0` surfaces de traversée · `15.0` laser et VFX.
**Un émissif ne remplace jamais une valeur foncée pour signaler un objet proche** (§3.1).

### 6.4 Matériaux de l'arme FP — `M_Weapon_Base` (créé le 2026-08-20, en avance sur le J22)

**Master : `Content/OVERDRIVE/Art/Materials/Master/M_Weapon_Base`**
`Material Domain = Surface` · `Blend Mode = Opaque` · `Shading Model = Default Lit` · aucune texture,
aucune normal map. Volontairement minimal — 6 expressions, 5 paramètres :

| Paramètre | Type | Groupe | Défaut | Branché sur |
|---|---|---|---|---|
| `BaseColor` | Vector | `01 - Surface` | `0.215861` gris neutre | `MP_BaseColor` (sortie RGB) |
| `Metallic` | Scalar | `01 - Surface` | `0.0` | `MP_Metallic` |
| `Roughness` | Scalar | `01 - Surface` | `0.7` | `MP_Roughness` |
| `EmissiveColor` | Vector | `02 - Emissive` | `#FF1025` linéaire | `× EmissiveIntensity` → `MP_EmissiveColor` |
| `EmissiveIntensity` | Scalar | `02 - Emissive` | `0.0` | idem |

**Instances : `Content/OVERDRIVE/Art/Materials/Instances/`**, assignées aux 4 slots de
`SM_Weapon_LaserPistol` dans cet ordre.

> ⚠️ **Les valeurs à saisir sont les LINÉAIRES.** Les HEX sont donnés à titre de référence de
> conception uniquement. Un paramètre `Vector` de matériau **n'est pas** un color picker sRGB :
> y coller le HEX composante par composante donne une couleur délavée (`PALETTE.md §8.2`).
> Conversion : `c ≤ 0.04045 ? c/12.92 : ((c+0.055)/1.055)^2.4`.

| Slot | `MI_` | HEX sRGB (référence) | **BaseColor linéaire (à saisir)** | Rough | Metal | `EmissiveIntensity` |
|---|---|---|---|---|---|---|
| 0 `M_LaserPistol_Body` | `MI_Weapon_Body` | `#24282E` | `0.017642 / 0.021219 / 0.027321` | 0.65 | 0.55 | 0 |
| 1 `M_LaserPistol_Panel` | `MI_Weapon_Panel` | `#1A1D22` | `0.010330 / 0.012286 / 0.015996` | 0.72 | 0.45 | 0 |
| 2 `M_LaserPistol_Accent` | `MI_Weapon_Accent` | `#3A3F47` | `0.042311 / 0.049707 / 0.063010` | 0.55 | 0.65 | 0 |
| 3 `M_LaserPistol_Emissive` | `MI_Weapon_Emissive` | `#FF1025` | `1.000000 / 0.005182 / 0.018500` | 0.60 | 0.00 | **8** `[À CALIBRER]` |

`EmissiveColor` vaut `#FF1025` linéaire (`1.000000 / 0.005182 / 0.018500`) sur les **quatre** instances ;
seule `EmissiveIntensity` distingue la bande lumineuse du reste.

**`EmissiveIntensity = 8` est `[À CALIBRER]`** et c'est le seul réglage sensible : la scène est
**éclairée en plein jour** (`11_ARBITRAGES D2`). Trop bas, l'émissif n'existe pas ; trop haut, le
tonemapper + le bloom délavent la bande vers le blanc et **le rouge disparaît**. Point de départ aligné
sur l'échelle §6.3 (`8.0` = surfaces de traversée). Fourchette de réglage attendue : 5 à 15.

#### 6.4.1 ⚠️ Tension de palette à arbitrer par Louis — l'arme est rouge, son tir est magenta

Trois sources se contredisent aujourd'hui :

| Source | Ce qu'elle dit |
|---|---|
| `PALETTE.md §3` / `11_ARBITRAGES D3` | **Tout ce qui émane du joueur est `OD_Magenta_Player` `#E8336E`.** Le rouge appartient au **danger** (`OD_Red_Danger`) et aux **surfaces de traversée** (`OD_Red_Traversal`). |
| `SPEC_ART_DIRECTION §8.2` | Arme : corps `OD_Navy_Deep`, panneaux `OD_Purple_Primary`, **bandes émissives `OD_Magenta_Player`**. |
| **Demande de Louis, 2026-08-20** | Émissif **rouge `#FF1025`**, « que ça fasse laser gun ». Corps/panneaux en gris charbon, pas en navy/violet. |

**Ce qui est implémenté : la demande de Louis (rouge).** La tension n'est pas tranchée, elle est signalée.

Le problème concret, à vitesse de jeu : le **faisceau** du laser est magenta (`SPEC_COMBAT`,
`OD_Magenta_Player`). L'arme annonce donc une couleur que son tir ne produit pas — et `#FF1025` est
à moins de 10 % de teinte de `OD_Red_Danger` `#C81E2E` et de `OD_Red_Traversal` `#F4453F`, les deux
couleurs qui signifient « ça va me tuer » et « je peux courir dessus ». Le risque n'est pas esthétique,
il est de **lisibilité** : une source rouge saturée en permanence dans le champ de vision use le signal
rouge du décor.

Trois issues possibles, **au choix de Louis** :

| Option | Conséquence |
|---|---|
| **A — Rouge, on assume** *(état actuel)* | Le plus proche du « laser gun » demandé. `PALETTE.md §3` gagne une exception explicite : « l'arme FP est la seule source rouge non-traversale du jeu ». Il faudra vérifier en playtest que les liserés rouges de wall ride restent lisibles avec le pistolet à l'écran. |
| **B — Magenta `#E8336E`** | L'arme **annonce la couleur de son tir**, la règle D3 reste intacte, aucun coût : un `set_vector_parameter` sur `MI_Weapon_Emissive`. On perd le look « rouge chaud » demandé. |
| **C — Dégradé rouge → magenta** | L'émissif part de `#FF1025` au repos et vire à `OD_Magenta_Player` au tir. Coût réel (pilotage par DMI), à ne pas payer avant que le reste soit joué. |

Le changement A → B coûte **une valeur** dans `MI_Weapon_Emissive`. Rien n'est verrouillé.

#### 6.4.2 Écarts assumés par rapport à §6.2 et §12.2

`§6.2` impose `Metallic = 0` et `Roughness ∈ [0.6 ; 0.9]` — mais explicitement **« sur tout `MI_`
d'environnement »**. `§12.2` généralise le `Metallic = 0` à tout le projet. Les valeurs demandées par
Louis pour l'arme sont métalliques (0.45 à 0.65) et l'accent descend à `Roughness 0.55`.

C'est **conservé tel quel**, pour une raison : l'arme est à ~40 cm de la caméra, elle est le seul objet
du jeu qui bénéficie d'un highlight spéculaire — c'est précisément ce que §6.2 interdit dans le décor
(« plastique mouillé » à 3000 uu/s), et ce qui fait lire un objet comme métallique en main.
**À surveiller après activation de `PP_ToonPost`** : si le highlight spéculaire survit à la
posterisation et fait scintiller l'arme en mouvement, descendre `Metallic` vers 0.2 et remonter
`Roughness` au-dessus de 0.6. C'est le seul endroit du projet où `Metallic > 0` est toléré.

---

## 7. Modélisation

### 7.1 Budgets de triangles (plafonds durs)

| Type d'asset | Budget |
|---|---|
| Module d'env simple (sol, mur, rampe) | **50 – 300 tris** — la majorité sous 150 |
| Module d'env complexe (arche, pilier, tunnel) | **300 – 800 tris** |
| Prop décoratif (borne, caisse, rambarde, panneau, rail) | **100 – 500 tris** |
| Prop hero (coffre, checkpoint, enseigne OVERDRIVE) | **500 – 1 500 tris** |
| Ennemi `Grunt` / `Shooter` / `Tank` | **1 200 – 2 000** / **1 500 – 2 500** / **2 500 – 4 000 tris** |
| Boss | **6 000 – 12 000 tris** (un seul à l'écran) |
| Arme FP (`SM_Weapon_LaserPistol`, `11_ARBITRAGES D21`) | **2 000 – 4 000 tris** |
| Bras FP (`SK_Player_Arms`) | **1 500 – 2 500 tris** |

Budget scène visible : **< 1,5 M tris**. Avec 30 ennemis + 400 modules on est à ~300 k :
**la géométrie n'est pas le facteur limitant en v2, l'éclairage l'est** (§5.5).

### 7.2 Règles de style
- Formes **cubiques et anguleuses**. Aucune courbe organique. Cylindres à **8 segments max**
  (6 pour les props). Les rails courbes de la key art : **arcs polygonaux de 6 à 8 segments**.
- **Chanfreins de 2 à 4 uu sur les arêtes principales des modules d'environnement.**
  **Changement par rapport à la v1** : en rendu éclairé, un chanfrein attrape le soleil et crée une
  ligne claire qui sépare deux faces blanches. C'est le remède n°1 au « blanc uniforme » (§10.4).
  **Un seul segment de chanfrein, jamais deux.**
- **Aucun détail géométrique inférieur à 10 uu** : invisible à 3000 uu/s, coûteux à modéliser.
- **Test de la silhouette** : rempli en noir plein, l'asset doit rester identifiable. Sinon on le
  simplifie, on ne le détaille pas.
- Un asset ne dépasse **jamais 90 min** de modélisation. Passé ce délai, il est trop détaillé : on coupe.

### 7.3 UV et vertex color
- **Modules d'environnement : pas d'UV utile.** Garder un UV0 valide et non chevauchant (unwrap
  automatique) uniquement pour éviter les warnings d'import.
- **Pas d'UV de lightmap** : `Allow Static Lighting ✘`, tout l'éclairage est dynamique.
- **Ennemis / arme / bras / boss** : UV0 simple par îlots plats, servant à placer les masques.
- **Le vertex color reste l'outil d'authoring principal** (gratuit, modifiable en 10 s dans Blender) :

| Canal | Usage |
|---|---|
| `R` | Masque émissif (1 = zone lumineuse) |
| `G` | Masque plaque sombre (1 = `PlateColor` au lieu de `ShellColor`) |
| `B` | Occlusion peinte (0 = recoin, 1 = exposé) — **complète l'AO du moteur, ne la remplace plus** |
| `A` | Variation aléatoire de teinte — **essentiel en v2** pour casser la répétition des modules blancs |

### 7.4 Pipeline Blender → FBX → UE5

> **`Docs/06_CONVENTIONS.md §9` fait autorité sur les réglages d'export FBX.**
> Ils ne sont **pas** redéfinis ici : s'y référer avant tout export. En cas de divergence, c'est
> `06_CONVENTIONS` qui gagne.

Rappels propres à cette spec, non couverts par `§9` :
- Échelle : **1 unité Blender = 1 m = 100 uu.** Un module de 400 uu mesure 4 m dans Blender.
- Origine à `(0,0,0)`, sur la grille : **coin bas** pour les modules, **au sol** pour les personnages.
  Les pivots exacts du kit sont dans `SPEC_LEVELDESIGN §3`.
- **`Ctrl+A → All Transforms`** avant tout export. Non négociable.
- Collision : mesh convexe séparé `UCX_<NomDuMesh>_01`, `_02`… dans le même FBX.
- Sources `.blend` et `.fbx` dans **`Art_Source/`**, jamais dans `Content/`.

**Import UE5** : `Generate Lightmap UVs ✘` · `Auto Generate Collision ✘` · `Combine Meshes ✘` ·
`Normal Import Method = Import Normals` · `Vertex Color Import Option = Replace` ·
`Import Materials / Import Textures ✘` · **`Build Nanite ✘`** (§5.5).

### 7.5 Le kit modulaire n'est pas défini ici

**`SPEC_LEVELDESIGN §3` verrouille le kit d'environnement** : liste, dimensions, pivots, presets de
collision — **23 meshes**. Cette spec ne fixe que la **manière** de les fabriquer (§7.1–§7.4) et leur
**look** (§10).

> **Renommage v2, déjà répercuté dans `SPEC_LEVELDESIGN §3`** : le mesh n° 23, ex-`SM_Module_NeonStrip_400`
> (« bande néon verticale » de la v1), devient **`SM_Module_TraversalStrip_400`**. Il **garde ses
> dimensions et son slot** mais **change de fonction** : c'est désormais la **bande de traversée**
> `OD_Red_Traversal`, posée sur les arêtes de toit, les rampes et les murs ridables.
> Le kit reste à **23 meshes** : aucun ajout, aucune suppression.

---

## 8. Le joueur

> **`11_ARBITRAGES D32` : le jeu reste en vue FPS. On ne modélise que les BRAS + l'ARME au MVP.**
> Le personnage complet de la key art sert à l'identité visuelle (logo, écrans de menu, marketing) et
> à une éventuelle vue 3ᵉ personne **post-v1**. Il n'est **pas** produit pendant les 4 semaines.

### 8.1 Charte des bras FP (`SK_Player_Arms`)

Les bras sont la **seule partie du personnage que le joueur voit**. Ils doivent porter l'ADN visuel de
la key art en trois éléments seulement.

| Élément | Traitement | Token |
|---|---|---|
| **Manche / avant-bras** | Tissu technique près du corps, aplat mat, `Roughness 0.8` | `OD_Navy_Deep` |
| **Panneau d'avant-bras** | Un seul panneau anguleux sur le dessus, aplat | `OD_Purple_Primary` |
| **Chevron d'accent** | Un `»` unique par avant-bras, côté extérieur, émissif `Intensity 3` | `OD_Magenta_Player` |
| **Gant** | Plus clair que la manche pour détacher la main de l'arme | `OD_Grey_Shadow` |
| **Liseré de poignet** | Ligne fine de 2 uu qui sépare gant et manche | `OD_Magenta_Player` |

**Règles :**
- **Trois couleurs maximum** sur les bras. Le regard doit aller à l'arme et à la scène, pas aux mains.
- Les bras sont **foncés** : ils se détachent du monde blanc et du ciel bleu sans effort. C'est le seul
  endroit du jeu où le navy est dominant, et c'est voulu (§3.1).
- **Aucun chevron animé, aucun scroll, aucun pulse** sur les bras. Seule l'arme réagit (`HeatRatio`).
- Chanfrein autorisé (§7.2) : les bras et l'arme sont à ~40 cm de la caméra, ce sont les deux seuls
  assets qui méritent du temps.
- Matériau : `M_Player` → `MI_Player_Arms`. Un seul `MI_`.

### 8.2 L'arme (`SM_Weapon_LaserPistol`)

> ⚠️ **Cette section décrit l'INTENTION v2. Les matériaux réellement posés le 2026-08-20 en
> divergent** (gris charbon + émissif **rouge**, à la demande de Louis) : voir **§6.4** pour les
> valeurs en vigueur et **§6.4.1** pour la tension de palette à arbitrer.
> Tant que §6.4.1 n'est pas tranché, **c'est §6.4 qui décrit l'état du jeu**, pas ce paragraphe.

Corps **`OD_Navy_Deep`**, panneaux **`OD_Purple_Primary`**, bandes émissives **`OD_Magenta_Player`**
pilotées par `MPC_Global.HeatRatio` : elles virent progressivement vers `OD_Amber_Heat` à l'approche de
l'overheat, puis clignotent en `OD_Red_Danger`. Afficheur de chaleur sur le flanc en `M_Sign`.
Seuils et durées : `07_TUNING §11`, jamais ici.

### 8.3 Ce que le personnage complet impose quand même aujourd'hui
Deux VFX de traversée doivent être cohérents avec lui : la **traînée de dash** et les **semelles**
au wall ride sont en `OD_Magenta_Player` (`11_ARBITRAGES D3`). Rien d'autre.

---

## 9. Ennemis — charte visuelle

> **Point à résoudre : la key art ne montre AUCUN ennemi.** Cette section est une **proposition
> tranchée** de l'agent, écrite ici faute de référence. À valider par Louis au premier ennemi modélisé.

### 9.1 Le problème et sa réponse
Le fond est **blanc et très lumineux**. Un ennemi blanc (v1 : coque `OD_Bone_White`) y serait
**invisible**. La règle §3.1 s'applique intégralement :

> **Les ennemis sont des SILHOUETTES FONCÉES** (navy / charbon) **avec un émissif ORANGE**
> (`OD_Amber_Enemy`). C'est l'inversion exacte de la charte v1.

Trois raisons : (a) le foncé ressort sur blanc **et** sur le ciel bleu pâle ; (b) l'orange est la seule
teinte chaude libre — le rouge est pris par la traversée, le magenta par le joueur (`11_ARBITRAGES D3`) ;
(c) une silhouette sombre en mouvement rapide est détectée en vision périphérique, une tache claire non.

### 9.2 Base commune
- Coque : **`OD_Navy_Deep`** dominant.
- Plaques et articulations : **`OD_Navy_Ink`** (plus sombre, découpe les volumes).
- Visière / émissif : **`OD_Amber_Enemy`**, `VisorIntensity = 12`.
- Un liseré `OD_Amber_Enemy` de 3 uu par silhouette, jamais plus — sinon la lecture se brouille à 3+.
- **Règle absolue : une forme foncée à visière orange dans le monde = un ennemi. Aucune autre source.**
- Cerclage : tous les ennemis, boss, projectiles ennemis et pickups sont en
  `Render CustomDepth Pass = true`, `Stencil Value = 1`. Une passe Sobel dédiée dans `PP_ToonPost`
  leur donne un contour de **2 px `OD_Amber_Enemy`** — un ennemi devant un mur blanc reste détouré.
  C'est un **outil de gameplay, pas un effet**.

### 9.3 Reconnaissance en 0,2 s — code de forme par archétype

La reconnaissance passe par la **SILHOUETTE**, la **TAILLE** et la **FORME DE VISIÈRE**.
La couleur ne fait que confirmer « ceci est hostile ».

| | `Grunt` | `Shooter` | `Tank` |
|---|---|---|---|
| **Hauteur** | **180 uu** | **190 uu** | **260 uu** (ratio 1.44) |
| **Largeur d'épaules** | 70 uu | 60 uu | **130 uu** |
| **Ratio L/H** | 0.39 — élancé | 0.32 — maigre | **0.50 — bloc** |
| **Silhouette** | Triangle pointe en bas : épaules larges, taille fine, jambes longues | **Asymétrique** : bras-canon massif à droite, corps maigre à gauche | **Rectangle** : épaules carrées, jambes courtes et écartées |
| **Code de forme (visière)** | **Point rond**, centré | **Barre horizontale** large, façon fente | **Deux points** + barre — trois émissifs |
| **Lecture instantanée** | « fin et rapide » | « déséquilibré » | « mur » |
| **Répartition de valeur** | Navy dominant, plaques Ink | Navy dominant, **canon en Ink** (attire l'œil sur la menace) | **INVERSÉE : `OD_Grey_Deep` dominant, plaques Navy Ink** |
| **Accent** | Liseré ambre fin sur le torse | Liseré ambre **sur le canon uniquement** (= d'où vient le tir) | Liseré ambre épais + **cœur pulsant** `OD_Amber_Heat` (point faible) |
| **Anim** | Course rapide, penché en avant | Statique, pivote sur place, recule | Marche lourde, ne court jamais |

**L'inversion de valeur du `Tank` est le levier le plus rentable** : il se lit comme **clair-gris**,
les deux autres comme **sombres**. Deux catégories visuelles pour zéro coût de production.
Combiné à la hauteur (260 vs 180 uu), il est identifiable à 4000 uu de distance.

### 9.4 Boss

| | Boss 01 | Boss 02 |
|---|---|---|
| Silhouette | Trapu, large, bas sur pattes | Élancé, pointes, épaules hautes |
| Coque | `OD_Navy_Deep` + panneaux **`OD_Gold_Rank`** | **`OD_Navy_Ink`** + panneaux `OD_Red_Danger` |
| Cœur (point faible) | `OD_Amber_Heat`, pulse 1 Hz | `OD_Red_Danger`, pulse 2 Hz |
| Taille | ×2,5 le `Grunt` (~450 uu) | ×3 le `Grunt` (~540 uu) |

Le cœur est **toujours** la seule zone à émissif > 15 sur le boss : c'est le point d'ancrage du regard.

### 9.5 Modularité — une seule chaîne d'animation
- **Un seul squelette** : `SKEL_Enemy_Humanoid` = squelette du **UE5 Mannequin (Manny)**. On récupère
  gratuitement la locomotion du template First Person et tout l'écosystème de retarget.
- **Un seul `ABP_Enemy`**, un `BS_Enemy_Locomotion`, 3 `AM_` d'attaque.
- Les variantes sont des **meshes skinnés différents sur le même squelette** + des `MI_` différents.
- `Tank` = `Grunt` + volumes d'épaules/jambes remplacés + **`Component Scale = 1.44`** (`260 / 180`).
- `Shooter` = `Grunt` + bras droit remplacé par un canon.
- **Coût réel : 1 personnage modélisé, 2 kits de pièces.**
- Hitboxes : `11_ARBITRAGES D4` / `D30` (capsule + `HeadHitbox` sphérique). Aucun `PHYS_`.

---

## 10. Environnements

### 10.1 La grammaire visuelle (identique dans les 4 ambiances)

1. **Trois plans de lecture, jamais plus.**
   - *Proche / jouable* : blocs **blancs** (`OD_White_Structure`), arêtes chanfreinées, ombres portées nettes.
   - *Moyen* : mêmes blocs, contraste réduit, quelques accents violets de signalétique.
   - *Fond / skyline* : silhouettes **bleu pâle** noyées dans le fog, **aucun détail, aucun accent**.
2. **Une arête soulignée de rouge = une arête qu'on peut parcourir.** C'est la règle qui structure tout
   le level art. Bord de toit praticable, rampe, mur ridable, rail : liseré `OD_Red_Traversal`,
   émissif 8. **Une arête non praticable n'est jamais rouge.** Aucune exception.
3. **Le violet donne la direction.** Panneaux, écrans, chevrons `»` — toujours **orientés vers l'avant
   du parcours**. Un panneau violet qui ne pointe nulle part est un bug.
4. **La trajectoire jouable est la zone la plus contrastée de l'image.** Ce qui n'est pas jouable est
   désaturé et rapproché de la valeur du fond.
5. **Maximum 3 couleurs saturées visibles simultanément** dans un cadre.
6. **Plateformes flottantes** : volume cubique blanc + liseré `OD_Red_Traversal` sur l'arête supérieure
   **uniquement si on peut atterrir dessus**.
7. Tout est sur la grille **100 uu**, tailles 100/200/400/800/1600 (`06_CONVENTIONS §6`).
8. **Rythme visuel** : `SM_Module_TraversalStrip_400` (bande de traversée, §7.5) posé tous les **800 à
   1600 uu** le long des lignes de course. C'est le métronome de la vitesse : sans lui, à 3000 uu/s,
   le joueur ne sent plus qu'il avance.

### 10.2 Les 4 ambiances
**`PALETTE.md §4` fait autorité** : ciel, structure, ombre, accent de signalétique, couleur de soleil et
fog density y sont tabulés pour *Ascension*, *Redline*, *Boss 01* et *Boss 02*.
Le décor reste **blanc partout** ; seuls **le ciel, la lumière et l'accent de signalétique** changent.
Un `DA_World_*` (`PDA_WorldData`) par ambiance, poussé par `BP_LightingRig` (§5.4).
**Aucun mesh, aucun matériau n'est dupliqué entre deux mondes.**

### 10.3 Props et signalétique
Panneaux sur pied, écrans, bornes cubiques, caisses, rambardes, rails courbes, petits blocs :
tous en `OD_White_Structure` / `OD_Grey_Shadow`, **accents violets** (panneau `M_Sign`) et
**liserés rouges uniquement s'ils sont praticables** (rails, rambardes qu'on peut longer).
Un prop décoratif ne porte **jamais** de rouge.

### 10.4 Éviter le « blanc uniforme illisible » — 5 leviers

C'est **le risque de lisibilité n°1 de la DA v2**, l'équivalent du « tout est noir » de la v1.

| Levier | Application |
|---|---|
| **1. Variation de valeur** | Trois valeurs de blanc, jamais une seule : `OD_White_Pure` (faces au soleil), `OD_White_Structure` (faces neutres), `OD_Grey_Shadow` (faces latérales et sous-faces). Se règle **par `MI_`**, pas par mesh. |
| **2. Ombres portées** | Le soleil à −48° projette des ombres longues qui **découpent le sol**. C'est la principale source de lecture spatiale — d'où l'obligation `Cast Shadows ✔` (§5.1). |
| **3. Chanfreins** | 2–4 uu sur les arêtes (§7.2) : chaque arête devient une ligne claire entre deux faces. |
| **4. Ambient Occlusion** | `AO Intensity 0.4` (§5.3) + `VertexColor.B` peint dans les recoins : les objets se **posent** au sol au lieu de flotter. |
| **5. Accents** | Violet et rouge en petites quantités cassent le monochrome. Densité cible : **5 à 10 % de la surface d'un cadre**, jamais plus. |

**Test obligatoire par niveau** : capture → niveaux de gris → si le sol, les murs et les plateformes
forment un aplat gris continu où l'on ne distingue plus le bord d'un gouffre, le niveau est **refusé**
et on applique les leviers dans l'ordre 2 → 1 → 4 → 3 → 5.

---

## 11. UI visuelle

### 11.1 La règle inversée
Le monde est lumineux : **une UI claire disparaît**. Sur fond clair, **l'UI est SOMBRE**.
Couleurs, opacités et halos : **`PALETTE.md §7` fait autorité**, aucune valeur n'est dupliquée ici.

En résumé opérationnel (détail dans `PALETTE.md §7`) :
- Panneaux plein écran : fond `OD_Navy_Deep` très opaque, bordures fines `OD_Magenta_Player`.
- Éléments de HUD **sans panneau** (heat, speed, style, vies) : tracés en `OD_Navy_Ink` avec un
  **halo blanc de 2 px** — c'est ce halo qui les garde lisibles devant un mur blanc **et** devant le ciel.
  Il remplace le drop shadow noir de la v1.
- Crosshair : `OD_Navy_Ink` bordé de blanc. **Jamais magenta** (il se confondrait avec le laser).
- **Sanctuaire central** : les **40 % centraux en largeur et en hauteur** ne contiennent que le réticule
  (`11_ARBITRAGES D22`).
- Angles **droits**, aucun arrondi. Grille d'espacement de **8 px**, marge de sécurité écran **48 px**.

### 11.2 Polices (`11_ARBITRAGES D8`)

| Asset | Police | Rôle | Licence |
|---|---|---|---|
| **`F_Overdrive_Display`** | **Chakra Petch** (Bold, BoldItalic) | titres, rank, score, vitesse, gros chiffres | **SIL OFL 1.1** |
| **`F_Overdrive_Data`** | **Rajdhani** (Medium, SemiBold, Bold) | labels, valeurs, listes, tableaux, tooltips | **SIL OFL 1.1** |

Dans `Content/OVERDRIVE/UI/Fonts/`, avec le fichier `OFL.txt` de chaque police à côté.
**Font Cache = `Offline`** sur les deux assets : build reproductible, aucun hitch au premier affichage —
obligatoire pour un jeu qui relance un niveau en moins de 0,5 s (`Restart_FadeDuration`, `07_TUNING §16`).
**`F_Overdrive_Mono` n'existe pas.** Le logo n'est pas une police : c'est `T_Logo_Overdrive_D`
(PNG alpha 2048×1024, dégradé magenta → rouge + `//` violettes, §2.7).
`SPEC_UI_HUD` s'aligne sur cette section.

---

## 12. Ce qui est interdit

1. **Le réalisme**, sous toutes ses formes.
2. **Le PBR complexe** : metalness variable, roughness map, clear coat, SSS, anisotropie. `Metallic = 0` partout.
3. **Les normal maps détaillées.** Aucune normal map dans le projet, point.
4. **Les textures 4K.** Plafond dur **512×512**, sauf `T_Logo_Overdrive_D` (2048×1024). Cible : **6 textures**.
5. **Megascans / Quixel / Fab scans / assets photoréalistes.** Sans exception.
6. **Assets marketplace** non validés explicitement par Louis (`CLAUDE.md §6`).
7. **Le noir pur `#000000`** en ombre ou en outline. `ShadowLift` ne descend jamais à 0 (§4.3).
8. **Les couleurs réservées employées en décoration** (§3.2) — en particulier **du rouge sur une
   surface non praticable**.
9. **Motion blur, DOF, film grain, chromatic aberration statique.** Illisibles à 3000 uu/s.
10. **Volumetric Fog, Volumetric Clouds, Ray Tracing matériel, Nanite, Substrate, Static Lighting** (§5.5).
11. **Plus d'une lumière dynamique projetant des ombres par niveau.**
12. **Créer un nouveau `M_`** quand un `MI_` suffit.
13. **TOUT CE QUI ASSOMBRIT LE MONDE.** La DA v2 est lumineuse : pas de niveau nocturne, pas d'intérieur
    sombre, pas de fog dense qui mange le ciel, pas d'exposure négative, pas de « zone d'ambiance
    inquiétante ». Un joueur doit voir le fond du niveau depuis le départ. Une idée qui commence par
    « et si à cet endroit il faisait sombre » est **hors DA et hors scope**.

---

## 13. Pipeline de production sur 4 semaines

**Principe directeur : l'art ne bloque jamais le gameplay.** Le jeu doit être jouable et fun en gris
avant qu'un pixel de couleur n'existe.

> **Ce document planifie en SEMAINES** (`11_ARBITRAGES D23`). **`04_ROADMAP.md` est le seul document
> qui planifie en jours** : c'est lui qui décide quel lot tombe quel jour. Ce §13 donne l'**ordre de
> production** et le **contenu des lots**, jamais une date.

### Semaine 1 — BLOCKOUT GRIS, ÉCLAIRAGE DÈS LE PREMIER JOUR
- **Zéro art.** Un seul matériau : `M_Dev_Grid` (checker gris, **Default Lit**).
- Toute la géométrie = cubes UE scalés sur la grille 100 uu. Aucun export Blender.
- **Nouveauté v2, à faire en semaine 1 (~1 h)** : monter le **`BP_LightingRig` de base**
  (`DirectionalLight` + `SkyLight` + `SkyAtmosphere` + `HeightFog`, valeurs §5.1) dans
  `L_Sandbox_Movement`. On teste le mouvement **sous le vrai éclairage** dès le premier jour, sinon on
  découvre le coût GPU en semaine 3 et il est trop tard.
- **Premier `stat GPU` de référence** en fin de semaine : c'est le chiffre auquel on comparera tout.
- Réglages projet : Substrate ✘, Nanite ✘, Static Lighting ✘, **TSR**, Screen Percentage 100.
  **On ne touche PAS à Lumen ni aux VSM** (`D2`).
- Livrables art : `M_Dev_Grid`, `BP_LightingRig`, l'arbo `Content/OVERDRIVE/Art/`.

### Semaine 2 — LE MOTEUR VISUEL, PUIS LES ENNEMIS
Trois lots, **dans cet ordre strict** :
1. **Fondations (~2 j)** : `MPC_Global` → `PP_ToonPost` (§4) → `M_Env_Base` → `M_Env_Emissive` →
   `M_Sign` → **10 à 12 `MI_` de palette**. À l'issue de ce lot, activer `PP_ToonPost` et swapper
   `M_Dev_Grid` pour les `MI_` blancs **fait basculer tout le blockout en style final en moins d'une
   heure**. C'est le meilleur retour sur investissement du projet.
2. **Ennemis (~3 j)** : un **seul** humanoïde (`Grunt`, ~1 800 tris) sur le squelette Manny, puis les
   kits de pièces (`Shooter` bras-canon, `Tank` volumes lourds + `Component Scale 1.44`).
   `M_Enemy` + 3 `MI_`. **Test de contraste immédiat sur un mur blanc** (§9.1) : si la silhouette ne
   ressort pas, on assombrit avant d'aller plus loin.
3. **Premier lot de modules (~2 j)** : les 8 modules qui portent la traversée
   (`Floor_800`, `Floor_1600`, `Wall_800`, `Wall_1600`, `WallRide_1600`, `Ramp_1600x400`,
   `Platform_800`, `TraversalStrip_400` — liste et cotes : `SPEC_LEVELDESIGN §3`).

### Semaine 3 — ARME & BRAS, VFX, HUD, AMBIANCES, RESTE DU KIT
- **Bras FP + arme** (§8) : les deux seuls assets qui méritent chanfreins et budget de temps (4 h max).
- **VFX Niagara stylisés** : impact laser, dissolve de mort, speed lines, poussière de slide.
  Formes plates, palette imposée, **aucun `Cast Shadow`**. Catalogue : `SPEC_VFX §2`.
- **HUD + écran de résultats** avec les 2 polices et la charte §11.
- **Les 4 ambiances** : 4 `DA_World_*` poussés par `BP_LightingRig`. **Une journée suffit parce
  qu'aucun asset n'est dupliqué.**
- **Fin du kit modulaire** : les 15 modules restants de `SPEC_LEVELDESIGN §3`, à la demande.
- **Passe perf obligatoire en fin de semaine** (§5.5). C'est le dernier moment où couper coûte peu.

### Semaine 4 — BOSS, PROPS, POLISH
- **Les 2 boss** (kitbash de pièces d'ennemis + volumes hero).
- **Props et signalétique** (§10.3) : panneaux, écrans, bornes, caisses, rails. Lot compressible.
- **GEL DE LA PRODUCTION D'ASSETS en milieu de semaine.** Après le gel : plus aucun mesh, plus aucune
  texture. Uniquement du réglage de `MI_`, de post-process, d'éclairage et de placement.
  *(La date du gel est fixée par `04_ROADMAP.md`, pas ici.)*
- **Fin de semaine** : passe de lisibilité (§3.3 et §10.4 sur les 8 niveaux), réglage du fog et du
  bloom, `stat unit` / `stat GPU` (**cible GPU < 10 ms**).

### Règles de bascule gris → cel-shading
- Un niveau ne passe du gris au cel-shading que lorsque son **layout est `[VALIDÉ]`** en jeu.
- Un asset de blockout n'est remplacé par un mesh final que s'il apparaît dans **au moins 2 niveaux**.
- **`PP_ToonPost` s'active globalement, une fois, en semaine 2** : ce n'est pas une bascule par niveau.
- Si le planning glisse, on coupe dans l'ordre inverse de `CLAUDE.md §R5` : **props, puis boss, puis VFX,
  puis ennemis, puis environnement.** Le blockout gris **éclairé** est un état livrable.

---

## 14. Checklist de validation

**Rendu (une fois, en semaine 2)**
- [ ] Lumen actif, VSM actives, Substrate off, Nanite off, Static Lighting off, TSR actif.
- [ ] `PP_ToonPost` porté par `BP_PlayerCameraManager`, `Before Tonemapping`. Aucun blendable sur le volume.
- [ ] `Bands` entre 3 et 5 : les faces éclairées montrent des **paliers francs**, pas un dégradé.
- [ ] Les outlines tiennent **1,5 px à toute distance** et ne scintillent pas en mouvement à 3000 uu/s.
- [ ] Le ciel n'est **ni posterisé ni cerné** (`SkyMask`).
- [ ] Aucune ombre ne tombe au noir pur (`ShadowLift > 0`).

**Éclairage (par niveau)**
- [ ] **Exactement une** lumière dynamique avec ombres. `BP_LightingRig` présent, `WorldData` assigné.
- [ ] Les ombres portées **découpent le sol** et permettent de juger une distance de saut.
- [ ] La skyline lointaine est **bleu pâle** et sans détail (perspective aérienne lisible).
- [ ] `stat GPU` **< 10 ms** en course à vitesse de croisière, avec 8 ennemis à l'écran.

**Lisibilité (par niveau, bloquant)**
- [ ] Test niveaux de gris : ennemis et bandes de traversée = zones de contraste maximal (§3.3).
- [ ] Aucun aplat blanc continu où le bord d'un gouffre disparaît (§10.4).
- [ ] **Toute arête rouge est praticable. Aucune arête praticable n'est sans rouge.**
- [ ] Tout panneau violet pointe vers l'avant du parcours.
- [ ] Moins de 4 couleurs saturées simultanées dans un cadre ; accents ≤ 10 % de la surface.

**Assets**
- [ ] Budgets de triangles respectés (§7.1), aucun asset > 90 min de production.
- [ ] `Metallic = 0`, `Roughness ∈ [0.6 ; 0.9]`, aucune normal map, aucun lightmap UV.
- [ ] Nommage conforme à `06_CONVENTIONS §2`, rangement conforme à `§5`, sources dans `Art_Source/`.
- [ ] Aucun HEX en dur dans un `MI_` ou un widget : tout passe par `MPC_Global` / `DA_UITokens`.
- [ ] Les 3 archétypes d'ennemis sont identifiables **en 0,2 s** sur un mur blanc (§9.3).

**À faire valider par Louis (l'agent ne peut pas en juger)**
- [ ] La charte ennemis §9 (aucune référence n'existe dans la key art) — **décision de l'agent**.
- [ ] Le nombre de bandes de posterisation : 3 (très cartoon) vs 4 (défaut) vs 5 (subtil).
- [ ] La dureté des ombres (`Source Angle` 1.5° : trop net ? trop mou ?).
- [ ] La densité d'accents rouges : est-ce qu'on lit la trajectoire **sans réfléchir** à pleine vitesse ?
