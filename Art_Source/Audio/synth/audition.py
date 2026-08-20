"""
audition — montage d'ecoute pour juger les SFX en contexte.

Le Test 4 de SPEC_AUDIO §10 ("un headshot procure une vraie satisfaction")
est **comparatif** : un headshot ne peut etre satisfaisant que par rapport a
un tir au corps. L'ecouter seul dans un explorateur de fichiers ne permet
pas de le juger. Ce script enchaine les sons dans l'ordre ou le jeu les
produit, avec les variantes qui tournent, comme le fera le Sound Cue.

Sortie : ../out/_AUDITION_J10.wav

Usage :
    python audition.py
"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np

from sfx_core import SR, normalize, write_wav

OUT = Path(__file__).resolve().parent.parent / "out"

CADENCE = 0.42      # secondes entre deux tirs [A CALIBRER — cf. 07_TUNING]
IMPACT_LAG = 0.012  # hitscan : l'impact suit le tir de presque rien
RESPIRATION = 0.90  # pause entre deux sequences


def load(name: str) -> np.ndarray:
    """Charge un WAV en stereo (les mono sont dupliques)."""
    path = next(OUT.rglob(f"{name}.wav"))
    with wave.open(str(path), "rb") as w:
        ch, n = w.getnchannels(), w.getnframes()
        x = np.frombuffer(w.readframes(n), dtype="<i2").astype(np.float64) / 32768.0
    x = x.reshape(-1, ch)
    return np.repeat(x, 2, axis=1) if ch == 1 else x


class Timeline:
    """Piste stereo sur laquelle on depose des sons a un instant donne."""

    def __init__(self) -> None:
        self.buf = np.zeros((0, 2))
        self.cursor = 0.0

    def put(self, x: np.ndarray, at: float, gain_db: float = 0.0) -> None:
        start = int(round(at * SR))
        end = start + len(x)
        if end > len(self.buf):
            self.buf = np.vstack([self.buf, np.zeros((end - len(self.buf), 2))])
        self.buf[start:end] += x * (10 ** (gain_db / 20))

    def put_loop(self, x: np.ndarray, at: float, dur: float,
                 gain_db: float = 0.0, ramp: tuple | None = None) -> None:
        """
        Deroule une boucle sur `dur` secondes en la repetant bout a bout.
        C'est le seul moyen d'entendre le raccord : une boucle jouee une
        seule fois ne prouve rien.

        `ramp` = (dB_debut, dB_fin) pour les boucles pilotees par un parametre
        de gameplay (le vent suit la vitesse, §5).
        """
        n = int(round(dur * SR))
        tiled = np.vstack([x] * (n // len(x) + 1))[:n]
        if ramp is not None:
            g = np.linspace(10 ** (ramp[0] / 20), 10 ** (ramp[1] / 20), n)
            tiled = tiled * g[:, None]
        # fondu d'entree/sortie sur la SEQUENCE, pas sur la boucle elle-meme
        edge = int(0.05 * SR)
        tiled[:edge] *= np.linspace(0, 1, edge)[:, None]
        tiled[-edge:] *= np.linspace(1, 0, edge)[:, None]
        self.put(tiled, at, gain_db)

    def render(self) -> np.ndarray:
        return normalize(self.buf, -3.0)


# Les dB de SPEC_AUDIO §2.1 — sans eux on juge un faux mix.
DB_MOVE = {
    "jump": -8, "land_light": -10, "land_heavy": -4, "dash": -3,
    "dash_ready": -14, "slide_start": -6, "slide_loop": -9, "slide_end": -10,
    "wallride_enter": -6, "wallride_loop": -7, "walljump": -4,
}


def montage_mouvement() -> Path:
    """
    Une course simulee : les sons de mouvement ne se jugent qu'enchaines,
    avec le vent dessous. Ecoutes isolement ils sont tous "corrects".
    """
    jump = [load(f"S_Jump_{i:02d}") for i in range(1, 4)]
    land_l = [load(f"S_Land_Light_{i:02d}") for i in range(1, 4)]
    land_h = [load(f"S_Land_Heavy_{i:02d}") for i in range(1, 4)]
    dash = [load(f"S_Dash_{i:02d}") for i in range(1, 3)]
    ready = load("S_Dash_Ready_01")
    sl_start = [load(f"S_Slide_Start_{i:02d}") for i in range(1, 3)]
    sl_loop = load("S_Slide_Loop_01")
    sl_end = [load(f"S_Slide_End_{i:02d}") for i in range(1, 3)]
    wr_enter = [load(f"S_WallRide_Enter_{i:02d}") for i in range(1, 3)]
    wr_loop = load("S_WallRide_Loop_01")
    wjump = [load(f"S_WallJump_{i:02d}") for i in range(1, 3)]
    wind_lo, wind_hi = load("S_Wind_Loop_01"), load("S_Wind_Loop_02")

    tl = Timeline()
    total = 10.5

    # Le vent monte avec la vitesse (§5 : -40 dB a l'arret, -6 dB a 5000 uu/s).
    tl.put_loop(wind_lo, 0.0, total, 0.0, ramp=(-34, -9))
    tl.put_loop(wind_hi, 3.0, total - 3.0, 0.0, ramp=(-40, -16))

    print("Montage mouvement :")
    print("  0.00s — 2 sauts : atterrissage leger, puis lourd")
    tl.put(jump[0], 0.00, DB_MOVE["jump"])
    tl.put(land_l[0], 0.55, DB_MOVE["land_light"])
    tl.put(jump[1], 1.30, DB_MOVE["jump"])
    tl.put(land_h[0], 2.05, DB_MOVE["land_heavy"])

    print("  3.00s — dash, puis le bip de cooldown pret")
    tl.put(dash[0], 3.00, DB_MOVE["dash"])
    tl.put(ready, 3.70, DB_MOVE["dash_ready"])
    tl.put(dash[1], 4.10, DB_MOVE["dash"])
    tl.put(ready, 4.80, DB_MOVE["dash_ready"])

    print("  5.40s — slide complet : start, boucle 1.1 s, end")
    tl.put(sl_start[0], 5.40, DB_MOVE["slide_start"])
    tl.put_loop(sl_loop, 5.55, 1.10, DB_MOVE["slide_loop"])
    tl.put(sl_end[0], 6.65, DB_MOVE["slide_end"])

    print("  7.40s — wall ride : accroche, boucle 1.3 s, wall jump")
    tl.put(wr_enter[0], 7.40, DB_MOVE["wallride_enter"])
    tl.put_loop(wr_loop, 7.55, 1.30, DB_MOVE["wallride_loop"])
    tl.put(wjump[0], 8.85, DB_MOVE["walljump"])

    print("  9.40s — atterrissage lourd de fin")
    tl.put(land_h[2], 9.40, DB_MOVE["land_heavy"])

    return write_wav(OUT / "_AUDITION_MOUVEMENT.wav", tl.render())


def montage_chaleur() -> Path:
    """
    S_Heat_Warning avec son resserrement (§2.2 : "intervalle qui se resserre
    avec HeatRatio"). Un tick isole ne dit rien : la seule question qui compte
    est "est-ce que ca devient insupportable avant l'overheat ?".
    """
    tick = [load(f"S_Heat_Warning_{i:02d}") for i in range(1, 3)]
    impact = [load(f"S_Laser_Impact_Surface_{i:02d}") for i in range(1, 5)]
    ehit = [load(f"S_Enemy_Hit_{i:02d}") for i in range(1, 6)]
    fire = [load(f"S_Laser_Fire_{i:02d}") for i in range(1, 5)]

    tl = Timeline()
    print("\nMontage combat :")

    print("  0.00s — 4 tirs qui manquent leur cible (impacts decor, 3D)")
    tk = 0.0
    for i in range(4):
        tl.put(fire[i], tk, -2)
        tl.put(impact[i], tk + 0.030, -12)
        tk += 0.42

    tk += 0.9
    print(f"  {tk:4.2f}s — 5 impacts sur ennemi non letaux")
    for i in range(5):
        tl.put(fire[i % 4], tk, -2)
        tl.put(ehit[i], tk + 0.012, -9)
        tk += 0.42

    tk += 1.2
    start = tk
    print(f"  {tk:4.2f}s — LE TEST : la chaleur monte, les ticks se resserrent")
    interval, floor = 0.380, 0.055
    i = 0
    while tk - start < 4.6:
        tl.put(tick[i % 2], tk, -9)
        tk += interval
        interval = max(interval * 0.88, floor)
        i += 1
    print(f"          {i} ticks en {tk - start:.1f}s, de 380 ms a {floor*1000:.0f} ms")

    return write_wav(OUT / "_AUDITION_COMBAT.wav", tl.render())


def montage_j10() -> Path:
    fire = [load(f"S_Laser_Fire_{i:02d}") for i in range(1, 5)]
    body = [load(f"S_Laser_Hit_Body_{i:02d}") for i in range(1, 5)]
    head = [load(f"S_Laser_Hit_Head_{i:02d}") for i in range(1, 4)]
    death = [load(f"S_Enemy_Death_{i:02d}") for i in range(1, 5)]

    # Les dB de SPEC_AUDIO §2.2/§2.3, en relatif : c'est l'equilibre que les
    # Sound Classes produiront en jeu. Sans eux, on juge un faux mix.
    DB = {"fire": -2.0, "body": -6.0, "head": 0.0, "death": -5.0}

    tl = Timeline()
    tk = 0.0
    seq = 0

    def shot(kind: str | None, i: int) -> None:
        nonlocal tk
        tl.put(fire[i % 4], tk, DB["fire"])
        if kind == "body":
            tl.put(body[i % 4], tk + IMPACT_LAG, DB["body"])
        elif kind == "head":
            tl.put(head[i % 3], tk + IMPACT_LAG, DB["head"])
        tk += CADENCE

    def gap(label: str) -> None:
        nonlocal tk, seq
        seq += 1
        print(f"  {seq}. {tk:5.2f}s — {label}")
        tk += RESPIRATION

    print("Montage :")
    print(f"  0. {tk:5.2f}s — 4 tirs a vide (les 4 variantes de S_Laser_Fire)")
    for i in range(4):
        shot(None, i)
    gap("4 tirs au corps")

    for i in range(4):
        shot("body", i)
    gap("3 headshots")

    for i in range(3):
        shot("head", i)
    gap("LE TEST : corps, corps, TETE, corps, TETE")

    for i, kind in enumerate(["body", "body", "head", "body", "head"]):
        shot(kind, i)
    gap("kill au corps puis kill en tete, avec la mort")

    shot("body", 0)
    tl.put(death[0], tk - CADENCE + 0.10, DB["death"])
    tk += RESPIRATION
    shot("head", 1)
    tl.put(death[2], tk - CADENCE + 0.10, DB["death"])
    tk += 1.0

    return write_wav(OUT / "_AUDITION_J10.wav", tl.render())


def main() -> int:
    for path in (montage_j10(), montage_mouvement(), montage_chaleur()):
        with wave.open(str(path), "rb") as w:
            dur = w.getnframes() / w.getframerate()
        print(f"-> {path.name:28s} {dur:5.1f} s")
    print(f"\n   dans {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
