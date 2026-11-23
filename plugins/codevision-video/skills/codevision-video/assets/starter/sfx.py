"""효과음을 코드로 합성해 영상 길이만큼의 한 트랙(mp3)으로 만든다. 외부 음원을 쓰지 않아 저작권 문제가 없다.

python3 sfx.py out.mp3    다섯 가지 효과음을 1초 간격으로 늘어놓은 시험 파일
"""
import numpy as np

from bgm import SR, add, bell, highpass, hz, lowpass, tvec, write_mp3

RNG = np.random.default_rng(3)


def norm(x):
    return x / np.max(np.abs(x))


def click():
    t = tvec(0.09)
    snap = highpass(lowpass(RNG.standard_normal(len(t)) * np.exp(-t * 700), 7000), 1800)
    s = snap + 0.5 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 900)
    release = np.zeros_like(s)
    off = int(0.045 * SR)
    release[off:] = s[:len(s) - off] * 0.45
    return norm(s + release)


def pop():
    t = tvec(0.14)
    f = 620 + 520 * (1 - np.exp(-t * 55))
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30) * np.minimum(1, t / 0.002))


def whoosh(d=0.6):
    t = tvec(d)
    n = RNG.standard_normal(len(t))
    x = t / d
    s = lowpass(highpass(n, 250), 1200) * (1 - x) + lowpass(highpass(n, 1500), 6000) * x * 0.7
    return norm(s * np.sin(np.pi * x) ** 2)


def tone(m, d):
    t = tvec(d)
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    return s * np.minimum(1, t / 0.005) * np.exp(-t * 7)


def alert():
    out = np.zeros(int(0.7 * SR))
    add(out, 0, tone(79, 0.3))
    add(out, 0.17, tone(74, 0.5))
    return norm(out)


def chime():
    out = np.zeros(int(2.6 * SR))
    for i, m in enumerate((79, 83, 86, 91)):
        add(out, i * 0.08, bell(m, 2.2) * (1 - i * 0.1))
    return norm(lowpass(out, 9000))


SOUNDS = dict(click=(click, 0.30), pop=(pop, 0.16), whoosh=(whoosh, 0.14), alert=(alert, 0.30), chime=(chime, 0.34))


def render(out, total, events):
    made = {k: fn() * g for k, (fn, g) in SOUNDS.items()}
    buf = np.zeros(int(total * SR))
    for at, kind in events:
        add(buf, max(0.0, at), made[kind])
    write_mp3(out, np.stack([buf, buf], 1))
    print(f"sfx: {out} {len(events)}개")


if __name__ == "__main__":
    import sys
    from pathlib import Path
    render(Path(sys.argv[1]), len(SOUNDS) + 2, [(i + 0.5, k) for i, k in enumerate(SOUNDS)])
