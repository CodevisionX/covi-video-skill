"""원본 녹화(RAW)에서 assets/clips/ 를 자른다. python3 cut.py [클립 이름 ...]"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
RAW = HERE.parent.parent / "mp4"
OUT = HERE / "assets/clips"
FPS = 30
TERM_BG = "0x2A0321"

# 터미널 글자가 녹화 가장자리에 붙어 있으면 둥근 모서리에 잘리므로 터미널 색 여백을 덧댄다.
TERM = f"crop=1854:1000:66:80,pad=1920:1080:33:40:{TERM_BG}"
FULL = "null"

# 조각: (원본, 시작, 끝, 배속, 화면) — 끝이 None 이면 시작 프레임을 '배속' 자리의 초만큼 멈춘다.
# 화면: ffmpeg 필터 문자열, 또는 ("blur", x, y, w, h) 를 섞은 목록. 블러 좌표는 앞 필터를 거친 뒤 기준.
CLIPS = {
    # "demo": [("16-13-47", 154, 214.3, 3, TERM), ("16-13-47", 214.3, None, 4.0, TERM),
    #          ("16-13-47", 214.3, 239, 1, [TERM, ("blur", 245, 230, 390, 117)])],
}


def view(steps, n):
    """화면 정의를 [in] → [out] 필터 그래프 조각으로."""
    steps = steps if isinstance(steps, list) else [steps]
    graph, cur = [], f"[p{n}]"
    for j, st in enumerate(steps):
        nxt = f"[p{n}_{j}]"
        if isinstance(st, tuple):
            _, x, y, w, h = st
            graph.append(f"{cur}split[p{n}_{j}a][p{n}_{j}b];[p{n}_{j}b]crop={w}:{h}:{x}:{y},boxblur=12:2[p{n}_{j}c];"
                         f"[p{n}_{j}a][p{n}_{j}c]overlay={x}:{y}{nxt}")
        else:
            graph.append(f"{cur}{st}{nxt}")
        cur = nxt
    return graph, cur


def cut(name, parts):
    srcs = list(dict.fromkeys(p[0] for p in parts))
    uses = {s: [i for i, p in enumerate(parts) if p[0] == s] for s in srcs}
    graph = []
    for k, s in enumerate(srcs):
        graph.append(f"[{k}:v]split={len(uses[s])}" + "".join(f"[in{i}]" for i in uses[s]))
    for i, (src, a, b, x, steps) in enumerate(parts):
        if b is None:
            # tpad 는 길이 0 으로 나와서 한 프레임을 loop 로 늘린다.
            graph.append(f"[in{i}]trim=start={a}:duration=0.04,setpts=PTS-STARTPTS,fps={FPS},trim=end_frame=1,"
                         f"loop=loop={round(x * FPS) - 1}:size=1:start=0,setpts=N/{FPS}/TB[p{i}]")
        else:
            graph.append(f"[in{i}]trim={a}:{b},setpts=(PTS-STARTPTS)/{x},fps={FPS}[p{i}]")
        g, last = view(steps, i)
        graph += g
        graph.append(f"{last}setsar=1[s{i}]")
    graph.append("".join(f"[s{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[v]")
    inputs = [arg for s in srcs for arg in ("-i", str(RAW / f"{s}.mp4"))]
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", ";".join(graph), "-map", "[v]", "-an",
                    "-c:v", "libx264", "-crf", "16", "-preset", "medium", "-pix_fmt", "yuv420p", str(OUT / f"{name}.mp4")], check=True)
    print(name)


OUT.mkdir(parents=True, exist_ok=True)
for name, parts in CLIPS.items():
    if not sys.argv[1:] or name in sys.argv[1:]:
        cut(name, parts)
