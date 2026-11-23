"""배경음악을 직접 합성한다. 외부 음원을 쓰지 않아 저작권·라이선스 문제가 없다.

G장조 112BPM, 밝은 팝 반주(킥·클랩·하이햇·베이스·플럭·패드·벨 멜로디).
내레이션 구간에서는 소리를 줄인다(ducking). render(출력 mp3, 총 길이, [(시작, 길이)]).
"""
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np

SR = 44100
BPM = 112
BEAT = 60 / BPM
BAR = BEAT * 4
LEVEL = 0.55
DUCK = 0.22
RNG = np.random.default_rng(7)

CHORDS = {
    "G": ([55, 59, 62], 43), "D": ([54, 57, 62], 38), "Em": ([55, 59, 64], 40), "C": ([55, 60, 64], 36),
    "Bm": ([54, 59, 62], 35), "Am": ([57, 60, 64], 45),
}
PROG_A = ["G", "D", "Em", "C"]
PROG_B = ["C", "D", "Bm", "Em", "Am", "D", "G", "G"]
MELODY = [  # 8분음표 단위 (마디 안 위치, 미디 음, 길이)
    [(0, 74, 2), (2, 71, 2), (4, 74, 1), (5, 76, 3)],
    [(0, 74, 2), (2, 69, 4), (7, 71, 1)],
    [(0, 71, 2), (2, 67, 2), (4, 71, 1), (5, 74, 3)],
    [(0, 76, 2), (2, 74, 2), (4, 71, 4)],
]
# (이름, 진행, 마디 수, 드럼, 멜로디)
SECTIONS = [("intro", PROG_A, 4, 0, False), ("verse", PROG_A, 8, 1, False), ("chorus", PROG_A, 8, 2, True),
            ("bridge", PROG_B, 8, 1, False), ("chorus", PROG_A, 8, 2, True), ("break", PROG_A, 4, 0, True),
            ("verse", PROG_A, 8, 1, False), ("chorus", PROG_A, 8, 2, True)]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tvec(d):
    return np.arange(int(d * SR)) / SR


def add(buf, at, sig):
    i = int(at * SR)
    if i >= len(buf):
        return
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n]


def fast_len(n):
    best = 1 << (n - 1).bit_length()
    for a in (1, 3, 5, 9, 15, 25, 27, 45, 75, 81):
        p = a
        while p < n:
            p *= 2
        best = min(best, p)
    return best


def shape(x, fn):
    """FFT 로 크기 응답 fn(f) 을 곱한다(영위상)."""
    n = fast_len(len(x))
    X = np.fft.rfft(x, n)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.fft.irfft(X * fn(f), n)[:len(x)]


def lowpass(x, fc, order=2):
    return shape(x, lambda f: 1 / np.sqrt(1 + (f / fc) ** (2 * order)))


def highpass(x, fc, order=2):
    return shape(x, lambda f: 1 / np.sqrt(1 + (fc / np.maximum(f, 1e-3)) ** (2 * order)))


def convolve(x, ir, block=1 << 17):
    out = np.zeros(len(x) + len(ir))
    n = fast_len(block + len(ir))
    IR = np.fft.rfft(ir, n)
    for s in range(0, len(x), block):
        seg = x[s:s + block]
        y = np.fft.irfft(np.fft.rfft(seg, n) * IR, n)[:len(seg) + len(ir)]
        out[s:s + len(y)] += y
    return out[:len(x)]


# ── 악기 ───────────────────────────────────────────────────────────

def kick():
    t = tvec(0.38)
    f = 48 + 95 * np.exp(-t * 32)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 8.5)
    click = lowpass(RNG.standard_normal(len(t)) * np.exp(-t * 400), 4000) * 0.12
    return body + click


def clap():
    t = tvec(0.3)
    env = np.exp(-t * 16)
    for d in (0.0, 0.011, 0.022):
        env += 0.6 * (t >= d) * np.exp(-np.maximum(t - d, 0) * 160)
    n = RNG.standard_normal(len(t)) * env
    return highpass(lowpass(n, 3200), 900) * 1.4


def hat(open_=False):
    t = tvec(0.22 if open_ else 0.07)
    n = RNG.standard_normal(len(t)) * np.exp(-t * (18 if open_ else 70))
    return lowpass(highpass(n, 7000, 3), 13000)


def pluck(m, d=0.6):
    t = tvec(d)
    f = hz(m)
    s = sum(np.sin(2 * np.pi * f * h * t) / h ** 1.15 * np.exp(-t * (3.2 + h * 2.2)) for h in range(1, 9) if f * h < 12000)
    return s * np.minimum(1, t / 0.003)


def bell(m, d=1.4):
    t = tvec(d)
    f = hz(m)
    mod = 2.2 * np.exp(-t * 5) * np.sin(2 * np.pi * f * 3.5 * t)
    return np.sin(2 * np.pi * f * t + mod) * np.exp(-t * 2.6) * np.minimum(1, t / 0.004)


def bass(m, d):
    t = tvec(d)
    f = hz(m)
    saw = sum(np.sin(2 * np.pi * f * k * t) / k for k in range(1, 10))
    sub = np.sin(2 * np.pi * f * t)
    env = np.exp(-t * 3.0) * 0.7 + 0.3
    env *= np.minimum(1, t / 0.004) * np.minimum(1, (d - t) / 0.02)
    return (0.45 * saw + 0.8 * sub) * env


def pad(notes, d):
    t = tvec(d)
    s = np.zeros(len(t))
    for m in notes:
        for det in (-0.08, 0.0, 0.08):
            f = hz(m + 12) * 2 ** (det / 12)
            s += sum(np.sin(2 * np.pi * f * k * t + k) / k for k in range(1, 7))
    env = np.minimum(1, t / 0.35) * np.minimum(1, (d - t) / 0.4)
    return s * env / (len(notes) * 3)


# ── 곡 ─────────────────────────────────────────────────────────────

def arrangement(total):
    """총 길이를 채울 때까지 섹션을 이어 붙인다. [(시작, 이름, 진행, 마디, 드럼, 멜로디)]."""
    out, t, i = [], 0.0, 0
    while t < total:
        name, prog, bars, drums, mel = SECTIONS[i % len(SECTIONS)] if i < len(SECTIONS) else SECTIONS[1 + (i - 1) % (len(SECTIONS) - 1)]
        out.append((t, name, prog, bars, drums, mel))
        t += bars * BAR
        i += 1
    return out


def compose(total):
    n = int((total + 3) * SR)
    st = {k: np.zeros(n) for k in ("kick", "clap", "hat", "bass", "pluckL", "pluckR", "pad", "bell")}
    K, C, H, HO = kick(), clap(), hat(), hat(True)
    pump = np.ones(n)
    beat_env = 1 - 0.38 * np.exp(-tvec(BEAT) * 9)
    for start, name, prog, bars, drums, mel in arrangement(total):
        for b in range(bars):
            ch = prog[b % len(prog)]
            notes, root = CHORDS[ch]
            t0 = start + b * BAR
            add(st["pad"], t0, pad(notes, BAR + 0.05))
            arp = notes + [notes[0] + 12, notes[1] + 12]
            pattern = [0, 2, 1, 3, 2, 4, 3, 1] if name != "bridge" else [0, 1, 2, 3, 4, 3, 2, 1]
            for s, idx in enumerate(pattern):
                at = t0 + s * BEAT / 2
                key = "pluckL" if s % 2 == 0 else "pluckR"
                vel = 0.9 if s % 2 == 0 else 0.65
                if name == "intro" and s % 2:
                    continue
                add(st[key], at, pluck(arp[idx] + 12, 0.55) * vel)
            if drums or name == "break":
                bass_pat = [(0, 0, 1.5), (1.5, 0, 0.5), (2, 12, 0.5), (2.5, 0, 0.5), (3, 7, 0.5), (3.5, 12, 0.5)]
                for off, iv, ln in bass_pat:
                    add(st["bass"], t0 + off * BEAT, bass(root + iv, ln * BEAT * 0.95) * (0.6 if name == "break" else 1))
            if drums:
                for q in range(4):
                    add(st["kick"], t0 + q * BEAT, K)
                    i = int((t0 + q * BEAT) * SR)
                    seg = pump[i:i + len(beat_env)]
                    seg[:] = beat_env[:len(seg)]
                    add(st["hat"], t0 + q * BEAT + BEAT / 2, HO * 0.7)
                    if drums == 2:
                        add(st["hat"], t0 + q * BEAT + BEAT / 4, H * 0.45)
                        add(st["hat"], t0 + q * BEAT + 3 * BEAT / 4, H * 0.45)
                add(st["clap"], t0 + BEAT, C)
                add(st["clap"], t0 + 3 * BEAT, C)
                if b == bars - 1 and drums == 2:
                    for q in range(4):
                        add(st["clap"], t0 + 3 * BEAT + q * BEAT / 4, C * (0.3 + 0.15 * q))
            if mel:
                for pos, m, ln in MELODY[b % 4]:
                    add(st["bell"], t0 + pos * BEAT / 2, bell(m, max(0.8, ln * BEAT / 2 + 0.6)))
    return st, pump, n


def mixdown(total):
    st, pump, n = compose(total)
    st["bass"] = lowpass(st["bass"], 700) * pump
    st["pad"] = lowpass(st["pad"], 1800) * pump
    dry = {
        "kick": (0.62, 0.0), "clap": (0.36, 0.05), "hat": (0.14, 0.25), "bass": (0.38, 0.0),
        "pluckL": (0.40, -0.35), "pluckR": (0.40, 0.35), "pad": (0.26, 0.0), "bell": (0.24, -0.15),
    }
    L = np.zeros(n)
    R = np.zeros(n)
    send = np.zeros(n)
    for k, (g, pan) in dry.items():
        L += st[k] * g * (1 - pan) / 2 * 2
        R += st[k] * g * (1 + pan) / 2 * 2
        if k in ("clap", "pluckL", "pluckR", "pad", "bell"):
            send += st[k] * g
    tir = tvec(1.6)
    for side, seed in ((L, 1), (R, 2)):
        ir = np.random.default_rng(seed).standard_normal(len(tir)) * np.exp(-tir / 0.32)
        ir = lowpass(ir, 5000) / np.sqrt(np.sum(ir ** 2))
        side += convolve(send, ir) * 0.22
    out = np.stack([L, R], 1)
    return out / np.max(np.abs(out)) * 0.95


def duck_env(n, cues):
    g = np.ones(n)
    for s, d in cues:
        g[max(0, int((s - 0.15) * SR)):int((s + d + 0.2) * SR)] = DUCK
    w = int(0.3 * SR)
    c = np.cumsum(np.concatenate([np.ones(w) * g[0], g]))
    return (c[w:] - c[:-w]) / w


def render(out, total, cues):
    mix = mixdown(total)
    n = int(total * SR)
    mix = mix[:n]
    g = duck_env(n, cues) * LEVEL
    t = np.arange(n) / SR
    g *= np.minimum(1, t / 1.0) * np.clip((total - t) / 3.0, 0, 1)
    mix *= g[:, None]
    write_mp3(out, mix)
    print(f"bgm: {out} {total:.1f}s")


def write_mp3(out, stereo):
    pcm = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "out.wav"
        with wave.open(str(wav), "wb") as w:
            w.setnchannels(2)
            w.setsampwidth(2)
            w.setframerate(SR)
            w.writeframes(pcm.tobytes())
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame", "-b:a", "192k", str(out)], check=True)


if __name__ == "__main__":
    import sys
    total = float(sys.argv[2]) if len(sys.argv) > 2 else 40
    render(Path(sys.argv[1]), total, [])
