"""
overdrive_sfx — recettes des SFX d'OVERDRIVE.

Une fonction par son du catalogue. Les descriptions sonores citees en
docstring sont celles de Docs/Specs/SPEC_AUDIO.md §2, qui fait foi (D19).

TOUS les nombres reglables sont dans le dict P ci-dessous : c'est la seule
zone a toucher pour iterer apres une ecoute. Ne modifie pas les recettes
elles-memes tant qu'un simple parametre peut faire le travail.

Usage :
    python overdrive_sfx.py              # regenere tout dans ../out/
    python overdrive_sfx.py S_Laser_Hit_Head
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

from sfx_core import (SR, at, bandpass, declick, env_ar, env_perc, fit,
                      gain_db, highpass, layer, loop_am, loop_spectral,
                      loop_stereo, lowpass, noise, normalize, peak_dbfs,
                      pitch_shift, resonate, ring, saw_sweep, shape_band,
                      shape_peaks, sine_sweep, soft_clip, sweep_bandpass,
                      trim, widen, write_wav)

OUT = Path(__file__).resolve().parent.parent / "out"


# ==========================================================================
# PARAMETRES — la seule zone a editer entre deux ecoutes
# ==========================================================================

P = {
    # ---- S_Laser_Fire (250 ms, 2D, 4 var) --------------------------------
    # "attaque = transient claquant 3-8 kHz · corps = sweep saw descendant
    #  · queue = resonance 120 ms"
    "fire": {
        "dur":          0.250,
        "click_lo":     3000.0,   # bande du transient d'attaque
        "click_hi":     8000.0,
        "click_tau":    0.0035,   # plus court = plus claquant
        "click_amp":    0.85,
        "body_f0":      1400.0,   # depart du sweep saw
        "body_f1":      190.0,    # arrivee
        "body_dur":     0.130,
        "body_curve":   0.35,     # <1 : chute vite puis s'aplatit
        "body_tau":     0.050,
        "body_amp":     1.00,
        "body_drive":   2.6,      # saturation du corps
        "tail_hz":      520.0,    # resonance de queue
        "tail_q":       9.0,
        "tail_delay":   0.130,    # attaque + corps + queue = les 250 ms de la spec
        "tail_dur":     0.120,
        "tail_tau":     0.048,
        "tail_amp":     0.34,
        "hpf":          140.0,    # SPEC_AUDIO §7 : passe-haut sauf impacts lourds
        "width":        0.30,
    },

    # ---- S_Laser_Hit_Body (150 ms, 2D, 4 var) ----------------------------
    # "thud sourd + « fizz » electrique, bas-medium"
    "hit_body": {
        "dur":          0.150,
        "thud_f0":      110.0,
        "thud_f1":      52.0,
        "thud_dur":     0.075,
        "thud_curve":   0.40,
        "thud_tau":     0.028,
        "thud_amp":     1.00,
        "fizz_lo":      2200.0,
        "fizz_hi":      6500.0,
        "fizz_dur":     0.110,
        "fizz_tau":     0.030,
        "fizz_amp":     0.34,     # monter = plus electrique, moins charnu
        "fizz_ringmod": 85.0,     # modulation en anneau = crepitement
        "mid_lo":       260.0,    # la couche "bas-medium" du texte de spec
        "mid_hi":       900.0,
        "mid_tau":      0.040,
        "mid_amp":      0.45,
        "drive":        1.8,
        "hpf":          45.0,
        "width":        0.25,
    },

    # ---- S_Laser_Hit_Head (300 ms, 2D, 3 var) ----------------------------
    # "timbre nettement distinct : crack aigu + sub court + micro-silence avant"
    "hit_head": {
        "dur":          0.300,
        "gap":          0.022,    # LE micro-silence. C'est lui qui fait le headshot.
        "crack_lo":     4000.0,
        "crack_hi":     11000.0,
        "crack_tau":    0.006,    # tres court : c'est un crack, pas un souffle
        "crack_amp":    1.00,
        "chirp_f0":     9500.0,   # descente aigue qui double le crack
        "chirp_f1":     2200.0,
        "chirp_dur":    0.020,
        "chirp_curve":  0.45,
        "chirp_amp":    0.55,
        "sub_f0":       78.0,
        "sub_f1":       42.0,
        "sub_dur":      0.130,
        "sub_curve":    0.50,
        "sub_tau":      0.045,
        "sub_amp":      0.90,     # "sub court" : present mais il ne doit pas trainer
        "ring_hz":      (2350.0, 3900.0, 5600.0),   # queue cristalline
        "ring_tau":     (0.075, 0.050, 0.032),
        "ring_amp":     0.20,
        "drive":        1.5,
        "width":        0.45,     # plus large que le body : ca aide a le distinguer
    },

    # ---- S_Enemy_Death (500 ms, 3D mono, 4 var) --------------------------
    # "shatter cristallin descendant, queue 400 ms"
    "death": {
        "dur":          0.500,
        "shards":       16,       # nombre d'eclats
        "shard_spread": 0.190,    # etalement des eclats dans le temps
        "shard_f_hi":   5200.0,   # premier eclat
        "shard_f_lo":   900.0,    # dernier eclat — la descente
        "shard_tau":    (0.014, 0.045),
        "shard_amp":    0.55,
        "burst_lo":     700.0,    # souffle initial qui colle les eclats ensemble
        "burst_hi":     7000.0,
        "burst_tau":    0.035,
        "burst_amp":    0.45,
        "tail_delay":   0.100,    # shatter ~100 ms puis queue 400 ms = 500 ms
        "tail_dur":     0.400,
        "tail_hz":      (620.0, 1450.0, 2600.0),
        "tail_tau":     (0.175, 0.130, 0.090),
        "tail_amp":     0.22,
        "tail_air":     0.10,     # nappe de bruit filtre qui simule la reverbe
        "hpf":          160.0,
    },
    # ======================================================================
    # MOUVEMENT — SPEC_AUDIO §2.1
    # ======================================================================

    # "souffle court, attaque douce, corps bruite filtre, queue nulle"
    "jump": {
        "dur":          0.120,
        "f0":           1600.0,   # le souffle descend legerement
        "f1":           700.0,
        "width":        3.0,
        "attack":       0.008,    # "attaque douce" : surtout pas un clic
        "tau":          0.030,
        "release":      0.030,    # "queue nulle" : on coupe net
        "amp":          1.00,
        "hpf":          160.0,
    },

    # "clic mat + basse courte, pas de queue"
    "land_light": {
        "dur":          0.150,
        "click_lo":     300.0,    # "mat" : bande basse, rien au-dessus de 3 kHz
        "click_hi":     2600.0,
        "click_tau":    0.008,
        "click_amp":    1.00,
        "low_f0":       150.0,
        "low_f1":       88.0,
        "low_dur":      0.130,
        "low_curve":    0.45,
        "low_tau":      0.036,
        # "basse COURTE" : ce son doit rester plus leger que S_Land_Heavy.
        # A 0.85 il avait plus de grave que l'atterrissage lourd — a l'envers.
        "low_amp":      0.42,
        "hpf":          40.0,
        "width":        0.18,
    },

    # "impact sub 60 Hz + noise burst, queue 200 ms"
    "land_heavy": {
        "dur":          0.400,
        "sub_f0":       95.0,
        "sub_f1":       48.0,
        "sub_dur":      0.220,
        "sub_curve":    0.50,
        "sub_tau":      0.078,
        "sub_amp":      1.00,
        "burst_lo":     120.0,
        "burst_hi":     4500.0,
        "burst_tau":    0.022,
        "burst_amp":    0.70,
        "tail_delay":   0.030,
        "tail_dur":     0.380,    # recouvre l'impact et porte jusqu'aux 400 ms
        "tail_lpf":     900.0,
        "tail_tau":     0.095,    # la "queue 200 ms" audible du texte de spec
        "tail_amp":     0.28,
        "drive":        1.6,
        "hpf":          28.0,     # impact lourd : SPEC_AUDIO §7 leve le HPF a 120
        "width":        0.22,
    },

    # "whoosh synthetique, sweep descendant 4 kHz -> 400 Hz, attaque immediate"
    "dash": {
        "dur":          0.250,
        "f0":           4000.0,   # les valeurs sont litteralement dans la spec
        "f1":           400.0,
        "width":        2.8,
        "curve":        0.55,
        "attack":       0.0005,   # "attaque immediate"
        "tau":          0.075,
        "amp":          1.00,
        "res_hz":       520.0,    # petit corps a l'arrivee du sweep
        "res_q":        6.0,
        "res_amp":      0.22,
        "hpf":          120.0,
        "width_st":     0.40,
    },

    # "double bip aigu, tres court, cristallin"
    # Meme famille que S_Heat_Ready (§2.2) : sinus purs + octave, rien d'autre.
    "dash_ready": {
        "dur":          0.090,
        "bip1_hz":      2100.0,
        "bip2_hz":      3150.0,   # une quinte au-dessus : ca monte, donc c'est pret
        "bip_gap":      0.040,
        "bip_tau":      0.010,
        "bip_len":      0.045,
        "octave_amp":   0.28,     # l'harmonique qui fait "cristallin"
        "width":        0.30,
    },

    # "scratch bruite + montee de resonance"
    "slide_start": {
        "dur":          0.200,
        "f0":           600.0,    # ca MONTE : c'est une prise d'appui
        "f1":           1650.0,
        "width":        1.8,
        "curve":        1.0,
        "attack":       0.004,
        "release":      0.045,
        "rough_hz":     90.0,     # rugosite du scratch
        "rough_depth":  0.35,
        "res_hz":       1500.0,
        "res_q":        10.0,
        "res_amp":      0.30,
        "hpf":          180.0,
        "width_st":     0.30,
    },

    # "boucle de bruit filtre band-pass ~1.2 kHz, seamless"
    "slide_loop": {
        "dur":          2.000,    # assez long pour ne pas s'entendre tourner
        "lo":           700.0,    # centre geometrique = sqrt(700*2100) = 1212 Hz
        "hi":           2100.0,
        # ordre 4.5 et non 2 : a 12 dB/oct la traine aigue portait le
        # centroide a 3200 Hz, loin des "~1.2 kHz" de la spec.
        "order":        4.5,
        "tilt":         -0.20,
        "am1_cycles":   3,        # ENTIER obligatoire : sinon la boucle claque
        "am1_depth":    0.16,
        "am2_cycles":   7,
        "am2_depth":    0.10,
        "decorr":       0.50,
    },

    # "queue descendante, decay 250 ms"
    "slide_end": {
        "dur":          0.250,
        "f0":           1500.0,
        "f1":           380.0,
        "width":        2.2,
        "curve":        0.80,
        "attack":       0.002,
        "tau":          0.085,
        "hpf":          120.0,
        "width_st":     0.28,
    },

    # "claquement + resonance"
    "wallride_enter": {
        "dur":          0.180,
        "clack_lo":     1800.0,
        "clack_hi":     8000.0,
        "clack_tau":    0.008,    # a 4 ms le claquement ne pesait rien face
        "clack_amp":    1.35,     # aux partiels : 2.5 % d'energie au-dessus de 4 kHz
        # partiels inharmoniques : c'est l'inharmonicite qui fait "metal"
        "res_hz":       (970.0, 1490.0, 2280.0, 3410.0),
        "res_tau":      (0.045, 0.035, 0.025, 0.015),
        "res_amp":      0.42,
        "hpf":          200.0,
        "width":        0.35,
    },

    # "frottement metallique tonal" — lit statique ; MS_WallRide (§4.3) fera
    # monter le Q au runtime. Ce WAV ne doit donc PAS deja etre urgent.
    "wallride_loop": {
        "dur":          2.000,
        "lo":           500.0,
        "hi":           3000.0,
        "order":        4.5,      # meme raison que slide_loop
        "tilt":         -0.30,
        "peaks":        (980.0, 1520.0, 2290.0),
        "peak_q":       28.0,
        "peak_amount":  1.60,
        "am_cycles":    5,
        "am_depth":     0.14,
        "decorr":       0.45,
    },

    # "impact + whoosh, plus aigu que S_Jump"
    "walljump": {
        "dur":          0.220,
        "imp_lo":       400.0,
        "imp_hi":       3000.0,
        "imp_tau":      0.010,
        "imp_amp":      0.75,
        "low_f0":       180.0,
        "low_f1":       95.0,
        "low_dur":      0.050,
        "low_tau":      0.018,
        "low_amp":      0.50,
        "wh_f0":        5000.0,   # S_Jump part de 1600 : celui-ci est bien plus aigu
        "wh_f1":        900.0,
        "wh_width":     2.6,
        "wh_curve":     0.60,
        "wh_tau":       0.070,
        "wh_amp":       0.85,
        "hpf":          130.0,
        "width":        0.38,
    },

    # S_Wind_Loop — 2 COUCHES, pas 2 variantes (§2.1 colonne "Var.").
    # Placeholder : MS_Wind_Speed (§4.2) genere son bruit dans le moteur.
    "wind_low": {
        "dur":          3.000,
        "lo":           120.0,
        "hi":           2500.0,
        "order":        2.0,
        "tilt":         -0.50,    # pente rose
        "am1_cycles":   2,
        "am1_depth":    0.12,
        "am2_cycles":   5,
        "am2_depth":    0.08,
        "decorr":       0.90,     # "stereo large"
    },
    "wind_high": {
        "dur":          3.000,
        "lo":           3000.0,   # §4.2 : "seconde couche band-passe 3-6 kHz"
        "hi":           6000.0,
        "order":        3.0,
        "tilt":         0.0,
        "am1_cycles":   3,
        "am1_depth":    0.18,
        "am2_cycles":   0,
        "am2_depth":    0.0,
        "decorr":       1.00,
    },

    # ======================================================================
    # COMBAT / ENNEMI — le reste de §2.2 et §2.3
    # ======================================================================

    # "clic sec + petite queue metallique, distant" — 3D, donc MONO
    "impact_surface": {
        "dur":          0.180,
        "click_lo":     1800.0,
        "click_hi":     9000.0,
        "click_tau":    0.003,
        "click_amp":    1.00,
        "res_hz":       (2600.0, 4100.0, 5900.0),
        "res_tau":      (0.030, 0.022, 0.014),
        "res_amp":      0.26,
        "slap_delay":   0.012,    # micro-reflexion : c'est ce qui dit "loin"
        "slap_amp":     0.18,
        "distance_lpf": 6500.0,   # "distant" : les aigus se perdent en chemin
        "hpf":          220.0,
    },

    # "grunt court + fizz" — 3D, donc MONO
    "enemy_hit": {
        "dur":          0.180,
        "grunt_f0":     165.0,
        "grunt_f1":     128.0,
        "grunt_dur":    0.175,
        "grunt_curve":  0.60,
        "grunt_tau":    0.050,
        "grunt_attack": 0.004,
        "grunt_amp":    1.00,
        "formant_1":    620.0,    # deux formants = voyelle, donc "grunt"
        "formant_q1":   8.0,
        "formant_2":    1150.0,
        "formant_q2":   10.0,
        "fizz_lo":      2500.0,
        "fizz_hi":      6500.0,
        "fizz_dur":     0.070,
        "fizz_tau":     0.022,
        "fizz_amp":     0.30,
        "fizz_ringmod": 110.0,
        "drive":        1.7,
        "hpf":          90.0,
    },

    # "ticks courts, intervalle qui se resserre avec HeatRatio"
    # Le resserrement est un timer BP : ce WAV est UN tick.
    # Contrainte dominante : il sera joue des dizaines de fois par seconde
    # a la fin. Tout ce qui agresse ici devient insupportable en 3 secondes.
    "heat_warning": {
        "dur":          0.040,
        "tick_hz":      2650.0,
        "tick_tau":     0.007,
        "tick_amp":     1.00,
        "octave_amp":   0.22,
        "click_lo":     3000.0,
        "click_hi":     8000.0,   # plafonne : rien de strident
        "click_tau":    0.0015,
        "click_amp":    0.30,
        "hpf":          400.0,
        "width":        0.20,
    },
}

# Variantes : (demi-tons, dB). L'index 0 est la version de reference.
# SPEC_AUDIO §7 : "3-4 variantes (pitch +-2 demi-tons, gain +-2 dB)".
VARIANTS_1 = [(0.0, 0.0)]
VARIANTS_2 = [(0.0, 0.0), (+1.5, -1.0)]
VARIANTS_4 = [(0.0, 0.0), (+1.4, -1.2), (-1.7, +1.0), (+2.0, +1.8)]
VARIANTS_3 = [(0.0, 0.0), (+1.3, -1.0), (-1.5, +1.2)]
VARIANTS_5 = [(0.0, 0.0), (+1.2, -0.9), (-1.4, +0.8), (+2.0, +1.5), (-2.0, -0.6)]


# ==========================================================================
# RECETTES
# ==========================================================================

def s_laser_fire(rng: np.random.Generator) -> np.ndarray:
    """S_Laser_Fire — SPEC_AUDIO §2.2, 250 ms, 2D, -2 dB."""
    p = P["fire"]

    click = (bandpass(noise(0.020, rng), p["click_lo"], p["click_hi"])
             * env_perc(0.020, 0.0002, p["click_tau"]) * p["click_amp"])

    body = saw_sweep(p["body_f0"], p["body_f1"], p["body_dur"], p["body_curve"])
    body = soft_clip(body * env_perc(p["body_dur"], 0.0008, p["body_tau"]),
                     p["body_drive"]) * p["body_amp"]

    tail = (resonate(noise(p["tail_dur"], rng), p["tail_hz"], p["tail_q"])
            * env_perc(p["tail_dur"], 0.004, p["tail_tau"]) * p["tail_amp"])

    mix = layer(click, body, at(p["tail_delay"], tail))
    mix = highpass(fit(mix, p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def s_laser_hit_body(rng: np.random.Generator) -> np.ndarray:
    """S_Laser_Hit_Body — SPEC_AUDIO §2.2, 150 ms, 2D, -6 dB."""
    p = P["hit_body"]

    thud = (sine_sweep(p["thud_f0"], p["thud_f1"], p["thud_dur"], p["thud_curve"])
            * env_perc(p["thud_dur"], 0.0010, p["thud_tau"]) * p["thud_amp"])

    fz = bandpass(noise(p["fizz_dur"], rng), p["fizz_lo"], p["fizz_hi"])
    ringmod = 0.55 + 0.45 * np.sin(2 * np.pi * p["fizz_ringmod"]
                                   * np.arange(len(fz)) / SR)
    fizz = fz * ringmod * env_perc(p["fizz_dur"], 0.0008, p["fizz_tau"]) * p["fizz_amp"]

    mid = (bandpass(noise(p["dur"], rng), p["mid_lo"], p["mid_hi"])
           * env_perc(p["dur"], 0.0010, p["mid_tau"]) * p["mid_amp"])

    mix = soft_clip(layer(thud, fizz, mid), p["drive"])
    mix = highpass(fit(mix, p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def s_laser_hit_head(rng: np.random.Generator) -> np.ndarray:
    """S_Laser_Hit_Head — SPEC_AUDIO §2.2, 300 ms, 2D, 0 dB. Headshot."""
    p = P["hit_head"]

    crack = (bandpass(noise(0.030, rng), p["crack_lo"], p["crack_hi"])
             * env_perc(0.030, 0.0001, p["crack_tau"]) * p["crack_amp"])

    chirp = (sine_sweep(p["chirp_f0"], p["chirp_f1"], p["chirp_dur"], p["chirp_curve"])
             * env_perc(p["chirp_dur"], 0.0001, p["chirp_dur"] * 0.4) * p["chirp_amp"])

    sub = (sine_sweep(p["sub_f0"], p["sub_f1"], p["sub_dur"], p["sub_curve"])
           * env_perc(p["sub_dur"], 0.0015, p["sub_tau"]) * p["sub_amp"])

    tail_len = p["dur"] - p["gap"]
    tail = layer(*[ring(hz, tail_len, tau)
                   for hz, tau in zip(p["ring_hz"], p["ring_tau"])]) * p["ring_amp"]

    hit = soft_clip(layer(crack, chirp, sub, tail), p["drive"])
    # Le micro-silence est du vrai silence en tete du fichier : il ne survit
    # pas au trim. C'est voulu — le trim n'est pas applique a ce son.
    mix = fit(at(p["gap"], hit), p["dur"])
    return widen(declick(mix), rng, p["width"])


def s_enemy_death(rng: np.random.Generator) -> np.ndarray:
    """S_Enemy_Death — SPEC_AUDIO §2.3, 500 ms, 3D mono, -5 dB."""
    p = P["death"]

    burst = (bandpass(noise(0.060, rng), p["burst_lo"], p["burst_hi"])
             * env_perc(0.060, 0.0003, p["burst_tau"]) * p["burst_amp"])

    shards = []
    for i in range(p["shards"]):
        k = i / max(p["shards"] - 1, 1)
        # la descente : chaque eclat est plus grave que le precedent
        freq = p["shard_f_hi"] * (p["shard_f_lo"] / p["shard_f_hi"]) ** k
        freq *= rng.uniform(0.92, 1.09)
        tau = rng.uniform(*p["shard_tau"])
        when = k * p["shard_spread"] * rng.uniform(0.7, 1.25)
        amp = p["shard_amp"] * rng.uniform(0.45, 1.0) * (1.0 - 0.45 * k)
        shards.append(at(when, ring(freq, tau * 6, tau) * amp))

    air = (lowpass(highpass(noise(p["tail_dur"], rng), 400.0), 4200.0)
           * env_perc(p["tail_dur"], 0.010, p["tail_dur"] * 0.34) * p["tail_air"])
    partials = layer(*[ring(hz, p["tail_dur"], tau)
                       for hz, tau in zip(p["tail_hz"], p["tail_tau"])]) * p["tail_amp"]

    mix = layer(burst, *shards, at(p["tail_delay"], layer(air, partials)))
    mix = highpass(fit(mix, p["dur"]), p["hpf"])
    return declick(mix)          # mono : son 3D


# --------------------------------------------------------------------------
# Mouvement — SPEC_AUDIO §2.1
# --------------------------------------------------------------------------

def s_jump(rng: np.random.Generator) -> np.ndarray:
    """S_Jump — 120 ms, 2D, -8 dB. "souffle court, attaque douce, queue nulle"."""
    p = P["jump"]
    body = sweep_bandpass(noise(p["dur"], rng), p["f0"], p["f1"], p["width"], 0.6)
    env = env_perc(p["dur"], p["attack"], p["tau"]) * env_ar(p["dur"], 0.0, p["release"])
    mix = highpass(body * env * p["amp"], p["hpf"])
    return widen(declick(fit(mix, p["dur"])), rng, 0.22)


def s_land_light(rng: np.random.Generator) -> np.ndarray:
    """S_Land_Light — 150 ms, 2D, -10 dB. "clic mat + basse courte, pas de queue"."""
    p = P["land_light"]
    click = (bandpass(noise(0.030, rng), p["click_lo"], p["click_hi"])
             * env_perc(0.030, 0.0003, p["click_tau"]) * p["click_amp"])
    low = (sine_sweep(p["low_f0"], p["low_f1"], p["low_dur"], p["low_curve"])
           * env_perc(p["low_dur"], 0.0012, p["low_tau"]) * p["low_amp"])
    mix = highpass(fit(layer(click, low), p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def s_land_heavy(rng: np.random.Generator) -> np.ndarray:
    """S_Land_Heavy — 400 ms, 2D, -4 dB. "sub 60 Hz + noise burst, queue 200 ms"."""
    p = P["land_heavy"]
    sub = (sine_sweep(p["sub_f0"], p["sub_f1"], p["sub_dur"], p["sub_curve"])
           * env_perc(p["sub_dur"], 0.0020, p["sub_tau"]) * p["sub_amp"])
    burst = (bandpass(noise(0.090, rng), p["burst_lo"], p["burst_hi"])
             * env_perc(0.090, 0.0004, p["burst_tau"]) * p["burst_amp"])
    tail = (lowpass(noise(p["tail_dur"], rng), p["tail_lpf"])
            * env_perc(p["tail_dur"], 0.006, p["tail_tau"]) * p["tail_amp"])
    mix = soft_clip(layer(sub, burst, at(p["tail_delay"], tail)), p["drive"])
    mix = highpass(fit(mix, p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def s_dash(rng: np.random.Generator) -> np.ndarray:
    """S_Dash — 250 ms, 2D, -3 dB. Sweep 4 kHz -> 400 Hz, attaque immediate."""
    p = P["dash"]
    src = noise(p["dur"], rng)
    wh = sweep_bandpass(src, p["f0"], p["f1"], p["width"], p["curve"])
    wh = wh * env_perc(p["dur"], p["attack"], p["tau"]) * p["amp"]
    res = (resonate(src, p["res_hz"], p["res_q"])
           * env_perc(p["dur"], 0.020, p["tau"] * 1.3) * p["res_amp"])
    mix = highpass(fit(layer(wh, res), p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width_st"])


def s_dash_ready(rng: np.random.Generator) -> np.ndarray:
    """S_Dash_Ready — 90 ms, 2D, -14 dB. Double bip cristallin."""
    p = P["dash_ready"]

    def bip(hz: float) -> np.ndarray:
        return (ring(hz, p["bip_len"], p["bip_tau"])
                + ring(hz * 2, p["bip_len"], p["bip_tau"] * 0.55) * p["octave_amp"])

    mix = fit(layer(bip(p["bip1_hz"]), at(p["bip_gap"], bip(p["bip2_hz"]))), p["dur"])
    return widen(declick(mix), rng, p["width"])


def s_slide_start(rng: np.random.Generator) -> np.ndarray:
    """S_Slide_Start — 200 ms, 2D, -6 dB. "scratch bruite + montee de resonance"."""
    p = P["slide_start"]
    src = noise(p["dur"], rng)
    rough = 1.0 - p["rough_depth"] * (0.5 + 0.5 * np.sin(
        2 * np.pi * p["rough_hz"] * np.arange(len(src)) / SR))
    swept = sweep_bandpass(src * rough, p["f0"], p["f1"], p["width"], p["curve"])
    res = resonate(src, p["res_hz"], p["res_q"]) * p["res_amp"]
    env = env_ar(p["dur"], p["attack"], p["release"])
    mix = highpass(fit((swept + res * np.linspace(0, 1, len(src))) * env, p["dur"]),
                   p["hpf"])
    return widen(declick(mix), rng, p["width_st"])


def s_slide_loop(rng: np.random.Generator) -> np.ndarray:
    """S_Slide_Loop — boucle seamless, 2D, -9 dB. Band-pass ~1.2 kHz."""
    p = P["slide_loop"]
    x = loop_stereo(p["dur"], rng,
                    shape_band(p["lo"], p["hi"], p["order"], p["tilt"]),
                    p["decorr"])
    x = loop_am(x, p["am1_cycles"], p["am1_depth"])
    return loop_am(x, p["am2_cycles"], p["am2_depth"], phase=1.7)


def s_slide_end(rng: np.random.Generator) -> np.ndarray:
    """S_Slide_End — 250 ms, 2D, -10 dB. "queue descendante"."""
    p = P["slide_end"]
    swept = sweep_bandpass(noise(p["dur"], rng), p["f0"], p["f1"],
                           p["width"], p["curve"])
    mix = swept * env_perc(p["dur"], p["attack"], p["tau"])
    mix = highpass(fit(mix, p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width_st"])


def s_wallride_enter(rng: np.random.Generator) -> np.ndarray:
    """S_WallRide_Enter — 180 ms, 2D, -6 dB. "claquement + resonance"."""
    p = P["wallride_enter"]
    clack = (bandpass(noise(0.025, rng), p["clack_lo"], p["clack_hi"])
             * env_perc(0.025, 0.0002, p["clack_tau"]) * p["clack_amp"])
    res = layer(*[ring(hz, p["dur"], tau)
                  for hz, tau in zip(p["res_hz"], p["res_tau"])]) * p["res_amp"]
    mix = highpass(fit(layer(clack, res), p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def s_wallride_loop(rng: np.random.Generator) -> np.ndarray:
    """S_WallRide_Loop — boucle seamless, 2D, -7 dB. "frottement metallique tonal"."""
    p = P["wallride_loop"]
    shape = shape_peaks(shape_band(p["lo"], p["hi"], p["order"], p["tilt"]),
                        p["peaks"], p["peak_q"], p["peak_amount"])
    x = loop_stereo(p["dur"], rng, shape, p["decorr"])
    return loop_am(x, p["am_cycles"], p["am_depth"])


def s_walljump(rng: np.random.Generator) -> np.ndarray:
    """S_WallJump — 220 ms, 2D, -4 dB. "impact + whoosh, plus aigu que S_Jump"."""
    p = P["walljump"]
    imp = (bandpass(noise(0.040, rng), p["imp_lo"], p["imp_hi"])
           * env_perc(0.040, 0.0003, p["imp_tau"]) * p["imp_amp"])
    low = (sine_sweep(p["low_f0"], p["low_f1"], p["low_dur"], 0.5)
           * env_perc(p["low_dur"], 0.0010, p["low_tau"]) * p["low_amp"])
    wh = (sweep_bandpass(noise(p["dur"], rng), p["wh_f0"], p["wh_f1"],
                         p["wh_width"], p["wh_curve"])
          * env_perc(p["dur"], 0.0008, p["wh_tau"]) * p["wh_amp"])
    mix = highpass(fit(layer(imp, low, wh), p["dur"]), p["hpf"])
    return widen(declick(mix), rng, p["width"])


def _wind(key: str, rng: np.random.Generator) -> np.ndarray:
    p = P[key]
    x = loop_stereo(p["dur"], rng,
                    shape_band(p["lo"], p["hi"], p["order"], p["tilt"]),
                    p["decorr"])
    x = loop_am(x, p["am1_cycles"], p["am1_depth"])
    if p["am2_cycles"]:
        x = loop_am(x, p["am2_cycles"], p["am2_depth"], phase=2.1)
    return x


def s_wind_low(rng: np.random.Generator) -> np.ndarray:
    """S_Wind_Loop couche 1 — lit rose. Placeholder de MS_Wind_Speed (§4.2)."""
    return _wind("wind_low", rng)


def s_wind_high(rng: np.random.Generator) -> np.ndarray:
    """S_Wind_Loop couche 2 — band-passe 3-6 kHz, s'ajoute a haute vitesse."""
    return _wind("wind_high", rng)


# --------------------------------------------------------------------------
# Combat / Ennemi — le reste de §2.2 et §2.3
# --------------------------------------------------------------------------

def s_laser_impact_surface(rng: np.random.Generator) -> np.ndarray:
    """S_Laser_Impact_Surface — 180 ms, 3D mono, -12 dB. "clic sec, distant"."""
    p = P["impact_surface"]
    click = (bandpass(noise(0.020, rng), p["click_lo"], p["click_hi"])
             * env_perc(0.020, 0.0001, p["click_tau"]) * p["click_amp"])
    res = layer(*[ring(hz, p["dur"], tau)
                  for hz, tau in zip(p["res_hz"], p["res_tau"])]) * p["res_amp"]
    dry = layer(click, res)
    mix = layer(dry, at(p["slap_delay"], dry * p["slap_amp"]))
    mix = highpass(lowpass(fit(mix, p["dur"]), p["distance_lpf"]), p["hpf"])
    return declick(mix)          # mono : son 3D


def s_enemy_hit(rng: np.random.Generator) -> np.ndarray:
    """S_Enemy_Hit — 180 ms, 3D mono, -9 dB. "grunt court + fizz"."""
    p = P["enemy_hit"]
    src = saw_sweep(p["grunt_f0"], p["grunt_f1"], p["grunt_dur"], p["grunt_curve"])
    voiced = (resonate(src, p["formant_1"], p["formant_q1"])
              + resonate(src, p["formant_2"], p["formant_q2"]) * 0.7)
    grunt = (voiced * env_perc(p["grunt_dur"], p["grunt_attack"], p["grunt_tau"])
             * p["grunt_amp"])

    fz = bandpass(noise(p["fizz_dur"], rng), p["fizz_lo"], p["fizz_hi"])
    ringmod = 0.55 + 0.45 * np.sin(2 * np.pi * p["fizz_ringmod"]
                                   * np.arange(len(fz)) / SR)
    fizz = fz * ringmod * env_perc(p["fizz_dur"], 0.0008, p["fizz_tau"]) * p["fizz_amp"]

    mix = soft_clip(layer(grunt, fizz), p["drive"])
    return declick(highpass(fit(mix, p["dur"]), p["hpf"]))


def s_heat_warning(rng: np.random.Generator) -> np.ndarray:
    """S_Heat_Warning — 40 ms, 2D, -9 dB. Un tick ; le rythme est un timer BP."""
    p = P["heat_warning"]
    tick = (ring(p["tick_hz"], p["dur"], p["tick_tau"])
            + ring(p["tick_hz"] * 2, p["dur"], p["tick_tau"] * 0.5) * p["octave_amp"])
    click = (bandpass(noise(p["dur"], rng), p["click_lo"], p["click_hi"])
             * env_perc(p["dur"], 0.0001, p["click_tau"]) * p["click_amp"])
    mix = highpass(fit(layer(tick * p["tick_amp"], click), p["dur"]), p["hpf"])
    return widen(declick(mix, fade_out=0.004), rng, p["width"])


# ==========================================================================
# CATALOGUE ET RENDU
# ==========================================================================

def _e(recipe, family, variants, seed, trim_out=True, loop=False):
    return dict(recipe=recipe, family=family, variants=variants,
                seed=seed, trim=trim_out, loop=loop)


def _layers(recipes, family, seed):
    """Asset dont les index ne sont pas des variantes mais des COUCHES."""
    return dict(layers=recipes, family=family, seed=seed, loop=True)


# Les familles suivent 06_CONVENTIONS §5 : Content/OVERDRIVE/Audio/SFX/<Famille>/
CATALOG = {
    # --- Combat / Ennemi (§2.2, §2.3) ---
    "S_Laser_Fire":           _e(s_laser_fire,       "Combat",   VARIANTS_4, 1001),
    "S_Laser_Hit_Body":       _e(s_laser_hit_body,   "Combat",   VARIANTS_4, 2001),
    # trim=False : le micro-silence de tete EST le son. Le trim le mangerait.
    "S_Laser_Hit_Head":       _e(s_laser_hit_head,   "Combat",   VARIANTS_3, 3001, False),
    "S_Enemy_Death":          _e(s_enemy_death,      "Enemy",    VARIANTS_4, 4001),
    "S_Laser_Impact_Surface": _e(s_laser_impact_surface, "Combat", VARIANTS_4, 5001),
    "S_Enemy_Hit":            _e(s_enemy_hit,        "Enemy",    VARIANTS_5, 6001),
    "S_Heat_Warning":         _e(s_heat_warning,     "Combat",   VARIANTS_2, 7001),

    # --- Mouvement (§2.1) ---
    "S_Jump":                 _e(s_jump,             "Movement", VARIANTS_3, 8001),
    "S_Land_Light":           _e(s_land_light,       "Movement", VARIANTS_3, 8101),
    "S_Land_Heavy":           _e(s_land_heavy,       "Movement", VARIANTS_3, 8201),
    "S_Dash":                 _e(s_dash,             "Movement", VARIANTS_2, 8301),
    "S_Dash_Ready":           _e(s_dash_ready,       "Movement", VARIANTS_1, 8401),
    "S_Slide_Start":          _e(s_slide_start,      "Movement", VARIANTS_2, 8501),
    "S_Slide_End":            _e(s_slide_end,        "Movement", VARIANTS_2, 8601),
    "S_WallRide_Enter":       _e(s_wallride_enter,   "Movement", VARIANTS_2, 8701),
    "S_WallJump":             _e(s_walljump,         "Movement", VARIANTS_2, 8801),

    # --- Boucles : ni trim ni fade, sinon le raccord claque ---
    "S_Slide_Loop":           _e(s_slide_loop,       "Movement", VARIANTS_1, 9001,
                                 trim_out=False, loop=True),
    "S_WallRide_Loop":        _e(s_wallride_loop,    "Movement", VARIANTS_1, 9101,
                                 trim_out=False, loop=True),
    # 01 = lit rose, 02 = couche 3-6 kHz. Deux COUCHES (§2.1), pas deux variantes.
    "S_Wind_Loop":            _layers((s_wind_low, s_wind_high), "Movement", 9201),
}


def render(name: str) -> list[Path]:
    e = CATALOG[name]
    family, seed0 = e["family"], e["seed"]
    written = []

    if "layers" in e:
        jobs = [(fn, 0.0, 0.0) for fn in e["layers"]]
    else:
        jobs = [(e["recipe"], s, g) for s, g in e["variants"]]

    for i, (recipe, semis, db) in enumerate(jobs, start=1):
        x = recipe(np.random.default_rng(seed0 + i))

        if not e["loop"]:
            # Une boucle ne se transpose pas (le re-echantillonnage change sa
            # duree, donc son raccord avec le timer qui la pilote) et ne se
            # trime pas (le silence de tete/queue n'existe pas).
            if x.ndim == 2:
                x = np.stack([pitch_shift(x[:, c], semis) for c in range(x.shape[1])],
                             axis=1)
                if e["trim"]:
                    mono = x.sum(axis=1)
                    keep = np.flatnonzero(
                        np.abs(mono) > 10 ** (-60 / 20) * np.max(np.abs(mono)))
                    x = x[keep[0]:keep[-1] + 1] if len(keep) else x
            else:
                x = pitch_shift(x, semis)
                if e["trim"]:
                    x = trim(x)

        # normaliser d'abord (SPEC_AUDIO §7), puis appliquer l'ecart de gain
        # de la variante : sinon la normalisation l'annulerait.
        x = gain_db(normalize(x, -3.0), db)

        path = OUT / family / f"{name}_{i:02d}.wav"
        write_wav(path, x)
        written.append(path)
        tag = "BOUCLE" if e["loop"] else ("stereo" if x.ndim == 2 else "mono  ")
        print(f"  {path.name:30s} {len(x)/SR*1000:7.1f} ms  {tag}  "
              f"crete {peak_dbfs(x):+.1f} dBFS")
    return written


def main(argv: list[str]) -> int:
    names = argv[1:] or list(CATALOG)
    unknown = [n for n in names if n not in CATALOG]
    if unknown:
        print(f"Inconnu : {', '.join(unknown)}\nDisponible : {', '.join(CATALOG)}")
        return 1
    for name in names:
        print(f"\n{name}")
        render(name)
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
