"""
sfx_core — primitives de synthese pour les SFX d'OVERDRIVE.

Ce module ne connait aucun son du jeu : il ne fournit que des briques.
Le catalogue vit dans overdrive_sfx.py, et fait foi via Docs/Specs/SPEC_AUDIO.md §2.

Conventions de sortie (SPEC_AUDIO §7, "Finition") :
  WAV 44.1 kHz / 16-bit · normalise a -3 dBFS · silences trimes
  mono pour les sons 3D · stereo pour les sons 2D
"""

from __future__ import annotations

import struct
import wave
from pathlib import Path

import numpy as np
from scipy import signal

SR = 44100


# --------------------------------------------------------------------------
# Temps et bruit
# --------------------------------------------------------------------------

def t(dur: float) -> np.ndarray:
    """Vecteur temps de `dur` secondes."""
    return np.arange(int(round(dur * SR)), dtype=np.float64) / SR


def silence(dur: float) -> np.ndarray:
    return np.zeros(int(round(dur * SR)), dtype=np.float64)


def noise(dur: float, rng: np.random.Generator) -> np.ndarray:
    """Bruit blanc dans [-1, 1]."""
    return rng.uniform(-1.0, 1.0, int(round(dur * SR)))


def pink(dur: float, rng: np.random.Generator) -> np.ndarray:
    """Bruit rose (-3 dB/octave), via filtrage IIR de Voss-McCartney approche."""
    white = noise(dur, rng)
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1.0, -2.494956002, 2.017265875, -0.522189400]
    return _safe(signal.lfilter(b, a, white))


# --------------------------------------------------------------------------
# Oscillateurs
# --------------------------------------------------------------------------

def _phase(f0: float, f1: float, dur: float, curve: float) -> np.ndarray:
    """
    Phase d'un sweep de f0 vers f1.

    curve < 1 : la frequence chute vite puis s'aplatit (percussif).
    curve = 1 : glissando lineaire.
    curve > 1 : la frequence tient puis chute tard.
    """
    x = t(dur)
    if len(x) == 0:
        return x
    k = np.linspace(0.0, 1.0, len(x)) ** curve
    freq = f0 * (f1 / f0) ** k
    return 2 * np.pi * np.cumsum(freq) / SR


def sine_sweep(f0: float, f1: float, dur: float, curve: float = 1.0) -> np.ndarray:
    return np.sin(_phase(f0, f1, dur, curve))


def saw_sweep(f0: float, f1: float, dur: float, curve: float = 1.0,
              tame_hz: float = 11000.0) -> np.ndarray:
    """
    Dent de scie balayee. Naive + passe-bas : l'aliasing residuel est une
    couleur acceptable sur un son de laser de 250 ms, et couterait cher a
    supprimer proprement (PolyBLEP) pour un gain inaudible ici.
    """
    ph = _phase(f0, f1, dur, curve)
    raw = 2.0 * ((ph / (2 * np.pi)) % 1.0) - 1.0
    return lowpass(raw, tame_hz)


def square_sweep(f0: float, f1: float, dur: float, curve: float = 1.0,
                 tame_hz: float = 11000.0) -> np.ndarray:
    ph = _phase(f0, f1, dur, curve)
    return lowpass(np.sign(np.sin(ph)), tame_hz)


def ring(freq: float, dur: float, tau: float, phase: float = 0.0) -> np.ndarray:
    """Sinus amorti — la brique du timbre "cristallin" (SPEC_AUDIO §2.2)."""
    x = t(dur)
    return np.sin(2 * np.pi * freq * x + phase) * np.exp(-x / max(tau, 1e-6))


# --------------------------------------------------------------------------
# Enveloppes
# --------------------------------------------------------------------------

def env_perc(dur: float, attack: float, tau: float) -> np.ndarray:
    """Enveloppe percussive : attaque lineaire courte, decroissance exponentielle."""
    x = t(dur)
    e = np.exp(-x / max(tau, 1e-6))
    na = max(int(round(attack * SR)), 1)
    if na < len(e):
        e[:na] *= np.linspace(0.0, 1.0, na)
    return e


def env_ar(dur: float, attack: float, release: float) -> np.ndarray:
    """Enveloppe attack / release lineaire, plateau au milieu."""
    n = int(round(dur * SR))
    e = np.ones(n)
    na, nr = int(round(attack * SR)), int(round(release * SR))
    if na > 0:
        e[:min(na, n)] = np.linspace(0.0, 1.0, min(na, n))
    if nr > 0:
        e[-min(nr, n):] *= np.linspace(1.0, 0.0, min(nr, n))
    return e


# --------------------------------------------------------------------------
# Filtres
# --------------------------------------------------------------------------

def _nyq(hz: float) -> float:
    return float(np.clip(hz / (SR / 2), 1e-5, 0.999))


def lowpass(x: np.ndarray, hz: float, order: int = 4) -> np.ndarray:
    b, a = signal.butter(order, _nyq(hz), btype="low")
    return _safe(signal.lfilter(b, a, x))


def highpass(x: np.ndarray, hz: float, order: int = 4) -> np.ndarray:
    b, a = signal.butter(order, _nyq(hz), btype="high")
    return _safe(signal.lfilter(b, a, x))


def bandpass(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    b, a = signal.butter(order, [_nyq(lo), _nyq(hi)], btype="band")
    return _safe(signal.lfilter(b, a, x))


def resonate(x: np.ndarray, hz: float, q: float = 12.0) -> np.ndarray:
    """Pic resonant — donne le "metallique" et le "tonal" sans oscillateur."""
    b, a = signal.iirpeak(_nyq(hz), q)
    return _safe(signal.lfilter(b, a, x))


# --------------------------------------------------------------------------
# Traitement
# --------------------------------------------------------------------------

def soft_clip(x: np.ndarray, drive: float = 2.0) -> np.ndarray:
    """Saturation douce (SPEC_AUDIO §7 : "saturation legere")."""
    return np.tanh(x * drive) / np.tanh(drive)


def layer(*parts: np.ndarray) -> np.ndarray:
    """Somme des couches, alignees sur leur debut, longueur = la plus longue."""
    parts = [p for p in parts if len(p)]
    if not parts:
        return np.zeros(0)
    n = max(len(p) for p in parts)
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p
    return out


def at(delay: float, x: np.ndarray) -> np.ndarray:
    """Decale une couche de `delay` secondes — sert au micro-silence (§2.2)."""
    return np.concatenate([silence(delay), x])


def fit(x: np.ndarray, dur: float) -> np.ndarray:
    """Force la longueur exacte, en coupant ou en completant de silence."""
    n = int(round(dur * SR))
    if len(x) >= n:
        return x[:n]
    return np.concatenate([x, np.zeros(n - len(x))])


def declick(x: np.ndarray, fade_in: float = 0.0005, fade_out: float = 0.006) -> np.ndarray:
    """Micro-fades anti-clic. Le fade-in reste sous 1 ms pour ne pas mollir les transitoires."""
    return x * env_ar(len(x) / SR, fade_in, fade_out)


def trim(x: np.ndarray, thresh_db: float = -60.0) -> np.ndarray:
    """Trim des silences de tete et de queue (SPEC_AUDIO §10)."""
    if not len(x):
        return x
    thr = 10 ** (thresh_db / 20) * np.max(np.abs(x))
    idx = np.flatnonzero(np.abs(x) > thr)
    return x if not len(idx) else x[idx[0]:idx[-1] + 1]


def normalize(x: np.ndarray, dbfs: float = -3.0) -> np.ndarray:
    """Normalisation crete a -3 dBFS (SPEC_AUDIO §7)."""
    peak = np.max(np.abs(x)) if len(x) else 0.0
    return x if peak < 1e-9 else x * (10 ** (dbfs / 20) / peak)


def widen(x: np.ndarray, rng: np.random.Generator, amount: float = 0.35) -> np.ndarray:
    """
    Stereo pour les sons 2D : decorrelation des hautes frequences seulement.
    Les basses restent au centre — un sub decorrele se perd en mono.
    """
    hi = highpass(x, 900.0)
    lo = x - hi
    jitter = rng.uniform(-1.0, 1.0, len(hi)) * amount
    side = highpass(hi * jitter, 1800.0)
    return np.stack([lo + hi + side, lo + hi - side], axis=1)


def pitch_shift(x: np.ndarray, semitones: float) -> np.ndarray:
    """
    Transposition facon bande : re-echantillonnage. La duree change avec le
    pitch (+-2 demi-tons ~ +-12 %), ce qui est exactement l'effet voulu pour
    les variantes decrites en SPEC_AUDIO §7.
    """
    if abs(semitones) < 1e-6:
        return x
    ratio = 2.0 ** (semitones / 12.0)
    n = max(int(round(len(x) / ratio)), 1)
    src = np.linspace(0.0, len(x) - 1, n)
    return np.interp(src, np.arange(len(x)), x)


def gain_db(x: np.ndarray, db: float) -> np.ndarray:
    return x * (10 ** (db / 20))


def _safe(x: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.asarray(x, dtype=np.float64), nan=0.0, posinf=0.0, neginf=0.0)


# --------------------------------------------------------------------------
# Balayages de filtre — les whoosh et les scratches
# --------------------------------------------------------------------------

def sweep_bandpass(x: np.ndarray, f0: float, f1: float,
                   width: float = 2.5, curve: float = 1.0,
                   block: int = 64) -> np.ndarray:
    """
    Passe-bande dont la frequence centrale glisse de f0 vers f1.

    Traitement par blocs de 64 echantillons avec report de l'etat du filtre :
    les coefficients changent en cours de route, ce qui ajoute un grain leger.
    C'est audible comme de la matiere, pas comme un defaut, et c'est ce qui
    donne leur texture aux whoosh (S_Dash, S_WallJump).

    `width` = rapport haut/bas de la bande. 2.5 = large et souffle,
    1.3 = etroit et siffle.
    """
    n = len(x)
    if n == 0:
        return x
    out = np.zeros(n)
    half = np.sqrt(max(width, 1.01))
    zi = None
    for start in range(0, n, block):
        stop = min(start + block, n)
        k = (start / max(n - 1, 1)) ** curve
        f = f0 * (f1 / f0) ** k
        b, a = signal.butter(2, [_nyq(max(f / half, 20.0)),
                                 _nyq(min(f * half, SR * 0.48))], btype="band")
        if zi is None:
            zi = np.zeros(max(len(a), len(b)) - 1)
        out[start:stop], zi = signal.lfilter(b, a, x[start:stop], zi=zi)
    return _safe(out)


# --------------------------------------------------------------------------
# Boucles seamless
# --------------------------------------------------------------------------
#
# Une boucle fabriquee par filtrage temporel (lfilter) n'est jamais seamless :
# le filtre est causal, son etat au dernier echantillon ne correspond pas a
# celui du premier, et le raccord clique. Un fade croise masque le clic mais
# creuse un trou audible a chaque tour.
#
# La parade : synthetiser directement dans le domaine frequentiel. Une IFFT
# produit un signal **circulaire par construction** — le dernier echantillon
# enchaine exactement sur le premier. Toute mise en forme spectrale se fait
# donc sur la magnitude, jamais avec un filtre temporel.
#
# Corollaire : on n'applique NI declick NI trim a une boucle.

def shape_band(lo: float, hi: float, order: float = 2.0,
               tilt: float = 0.0) -> "callable":
    """
    Reponse en magnitude d'un passe-bande, pour loop_spectral.
    `tilt` = -0.5 donne une pente rose sur la bande.
    """
    def f(freqs: np.ndarray) -> np.ndarray:
        w = np.maximum(freqs, 1e-6)
        band = (1.0 / np.sqrt(1.0 + (w / hi) ** (2 * order))
                * 1.0 / np.sqrt(1.0 + (lo / w) ** (2 * order)))
        return band * w ** tilt
    return f


def shape_peaks(base: "callable", peaks: tuple, q: float = 24.0,
                amount: float = 1.0) -> "callable":
    """Ajoute des pics resonants a une reponse — c'est ce qui fait "metallique"."""
    def f(freqs: np.ndarray) -> np.ndarray:
        w = np.maximum(freqs, 1e-6)
        out = base(freqs)
        for hz in peaks:
            out = out + amount * base(freqs) / (1.0 + (q * (w - hz) / hz) ** 2)
        return out
    return f


def loop_spectral(dur: float, rng: np.random.Generator,
                  shape: "callable") -> np.ndarray:
    """Boucle mono seamless : phases aleatoires, magnitude imposee, IFFT."""
    n = int(round(dur * SR))
    freqs = np.fft.rfftfreq(n, 1 / SR)
    spec = shape(freqs).astype(np.complex128)
    spec *= np.exp(1j * rng.uniform(0.0, 2 * np.pi, len(freqs)))
    spec[0] = 0.0                                  # pas de composante continue
    if n % 2 == 0:
        spec[-1] = np.abs(spec[-1])                # Nyquist doit etre reel
    x = np.fft.irfft(spec, n)
    return x / (np.max(np.abs(x)) + 1e-12)


def loop_stereo(dur: float, rng: np.random.Generator, shape: "callable",
                decorr: float = 0.8) -> np.ndarray:
    """
    Boucle stereo seamless. `decorr` 0 = mono, 1 = canaux independants.
    Les deux realisations partagent la magnitude, donc le timbre ; seules
    les phases different.
    """
    a = loop_spectral(dur, rng, shape)
    b = loop_spectral(dur, rng, shape)
    d = float(np.clip(decorr, 0.0, 1.0))
    return np.stack([a, a * np.sqrt(1.0 - d ** 2) + b * d], axis=1)


def loop_am(x: np.ndarray, cycles: int, depth: float = 0.2,
            phase: float = 0.0) -> np.ndarray:
    """
    Modulation d'amplitude circulaire — donne de la vie a une boucle de bruit,
    qui sans elle sonne comme un souffle de climatisation.

    `cycles` doit etre un ENTIER : c'est ce qui garantit que la modulation
    boucle en meme temps que le signal.
    """
    n = len(x)
    c = np.arange(n) / n
    mod = 1.0 - depth + depth * (0.5 + 0.5 * np.sin(2 * np.pi * int(cycles) * c + phase))
    return x * (mod[:, None] if x.ndim == 2 else mod)


# La mesure du raccord vit dans analyze.py (fonction `seam`) : elle travaille
# sur le WAV ecrit, pas sur le tableau en memoire — c'est le fichier importe
# dans UE qui compte, pas ce que le script croit avoir produit.


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

def write_wav(path: Path, x: np.ndarray) -> Path:
    """Ecrit un WAV 44.1 kHz / 16-bit. `x` est mono (1D) ou stereo (N, 2)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = np.atleast_2d(x.T).T if x.ndim == 1 else x
    channels = 1 if x.ndim == 1 else x.shape[1]
    clipped = np.clip(x, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(channels)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return path


def peak_dbfs(x: np.ndarray) -> float:
    peak = np.max(np.abs(x)) if len(x) else 0.0
    return -np.inf if peak < 1e-9 else 20 * np.log10(peak)
