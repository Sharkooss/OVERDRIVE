"""
analyze — mesures objectives sur les WAV generes.

Ne remplace pas l'ecoute (R8) : aucune de ces colonnes ne dit si un son est
bon. Elles disent seulement si un son est conforme a ce que SPEC_AUDIO §2
en decrit — duree, niveau, et surtout si deux sons cense etre "nettement
distincts" le sont reellement.

Usage :
    python analyze.py                 # tous les WAV de ../out
    python analyze.py S_Laser_Hit     # filtre par prefixe
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent.parent / "out"


def read(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        n, ch, sr = w.getnframes(), w.getnchannels(), w.getframerate()
        raw = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float64) / 32768.0
    return (raw.reshape(-1, ch).mean(axis=1) if ch > 1 else raw), sr


def measure(path: Path) -> dict:
    x, sr = read(path)
    mag = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    total = mag.sum() + 1e-12

    peak = np.max(np.abs(x))
    rms = np.sqrt(np.mean(x ** 2))
    onset = np.flatnonzero(np.abs(x) > peak * 10 ** (-40 / 20))

    return {
        "nom":      path.name,
        "ms":       len(x) / sr * 1000,
        "crete":    20 * np.log10(peak + 1e-12),
        "rms":      20 * np.log10(rms + 1e-12),
        "crest":    20 * np.log10(peak / (rms + 1e-12)),
        "centro":   float((freqs * mag).sum() / total),
        "sub%":     float(mag[freqs < 120].sum() / total * 100),
        "aigu%":    float(mag[freqs > 4000].sum() / total * 100),
        "attaque":  (onset[0] / sr * 1000) if len(onset) else 0.0,
    }


def seam(path: Path) -> tuple[float, float]:
    """
    Qualite du raccord d'une boucle.

    Un signal circulaire n'a PAS un ecart nul au bouclage : x[0] et x[-1] sont
    deux echantillons voisins comme les autres, donc leur ecart doit ressembler
    a n'importe quel autre ecart du signal. Comparer a la mediane donne des
    faux positifs (un pas a 3x la mediane est banal dans du bruit).

    Le bon test est un rang centile : parmi tous les pas du signal, a quel
    centile se situe celui du bouclage ? Au-dela de ~99.9, il sort de la
    distribution et s'entend comme un clic.

    Renvoie (ecart_dB_relatif_a_la_crete, centile).
    """
    x, _ = read(path)
    if len(x) < 3:
        return 0.0, 0.0
    steps = np.abs(np.diff(x))
    wrap = abs(x[0] - x[-1])
    centile = float((steps < wrap).mean() * 100.0)
    db = 20 * np.log10(wrap / (np.max(np.abs(x)) + 1e-12) + 1e-12)
    return db, centile


def check_loops() -> None:
    loops = sorted(p for p in OUT.rglob("*Loop_*.wav"))
    if not loops:
        return
    print("\nRaccord des boucles (centile du pas de bouclage ; > 99.9 = clic)")
    print("-" * 66)
    for p in loops:
        db, centile = seam(p)
        verdict = "OK" if centile < 99.9 else "!! CLIC"
        print(f"{p.name:30s} ecart {db:+7.1f} dB   centile {centile:6.2f}   {verdict}")


def main(argv: list[str]) -> int:
    pref = argv[1] if len(argv) > 1 else ""
    files = sorted(p for p in OUT.rglob("*.wav") if p.name.startswith(pref))
    if not files:
        print(f"Aucun WAV dans {OUT}")
        return 1

    head = (f"{'fichier':30s} {'duree':>8s} {'crete':>7s} {'RMS':>7s} "
            f"{'crest':>6s} {'centroide':>10s} {'sub':>6s} {'aigu':>6s} {'attaque':>8s}")
    print(head)
    print("-" * len(head))
    for f in files:
        m = measure(f)
        print(f"{m['nom']:30s} {m['ms']:7.1f}m {m['crete']:+6.1f} {m['rms']:+6.1f} "
              f"{m['crest']:5.1f} {m['centro']:9.0f}Hz {m['sub%']:5.1f}% "
              f"{m['aigu%']:5.1f}% {m['attaque']:7.1f}m")
    check_loops()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
