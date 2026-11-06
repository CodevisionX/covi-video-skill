"""장면 목록에서 index.html 을 만든다. 시간은 장면 시작 기준 상대값.

python3 build.py      index.html 생성
python3 build.py vo   빠진 내레이션 mp3 만들기 (대본이 바뀌면 그 mp3 를 지우고 다시)
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
VOICE = ["--voice", "ko-KR-SunHiNeural", "--rate=+5%"]

SCREEN = dict(left=210, top=124, width=1500, height=810)
PAD = 12
SUB_MAX_WIDTH = 1660
SUB_FONT = 40

# vo: (시작, 파일 이름, 자막[, 읽을 대본]). 영문 이름은 TTS 가 영어식으로 읽으니 대본은 한글 발음으로 따로 쓴다.
SCENES = [
    dict(id="title", kind="title", length=6.5, title="Covi AX Platform 소개", subtitle="한 줄 설명",
         vo=[(0.6, "s0", "Covi AX Platform을 소개할게요.", "코비 에이엑스 플랫폼을 소개할게요.")]),
    dict(id="intro", kind="card", length=10, kicker="준비물", heading="카드 제목",
         rows=[("항목", "설명"), ("항목", "설명")],
         vo=[(0.5, "s1", "카드 장면 내레이션이에요.")]),
    # dict(id="demo", kind="clip", src="assets/clips/demo.mp4", step="1단계", label="화면 녹화",
    #      speed=[(0, "3배속"), (12.0, "일시 정지"), (18.0, "1배속")],
    #      marks=[(12.0, 18.0, 100, 420, 240, 34)],  # (시작, 끝, x, y, w, h) 클립 픽셀 기준
    #      vo=[(0.5, "s2", "녹화 장면 내레이션이에요.")]),
    dict(id="end", kind="end", length=10, heading="한눈에 보기",
         rows=[("1", "첫 단계"), ("2", "둘째 단계")], more="자세한 내용 · 사내 Notion 「문서 이름」",
         vo=[(0.5, "s9", "이 순서대로 하면 돼요.")]),
]


def probe(path, entries, stream=False):
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", "v"] if stream else []) + ["-show_entries", entries, "-of", "csv=p=0", str(HERE / path)]
    return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()


def dur(path):
    return float(probe(path, "format=duration"))


def size(path):
    return [int(x) for x in probe(path, "stream=width,height", stream=True).split(",")]


def fit(rect, src):
    """rect 안에 영상 비율 그대로 들어가는 테두리 상자와 영상 상자."""
    w, h = size(src)
    iw = rect["width"] - 2 * PAD
    ih = iw * h / w
    if ih > rect["height"] - 2 * PAD:
        ih = rect["height"] - 2 * PAD
        iw = ih * w / h
    left = rect["left"] + (rect["width"] - iw - 2 * PAD) / 2
    top = rect["top"] + (rect["height"] - ih - 2 * PAD) / 2
    frame = dict(left=left, top=top, width=iw + 2 * PAD, height=ih + 2 * PAD)
    return frame, dict(left=left + PAD, top=top + PAD, width=iw, height=ih)


def box(r):
    return ";".join(f"{k}:{round(r[k], 1)}px" for k in ("left", "top", "width", "height"))


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def sub_width(text):
    return sum(SUB_FONT * (0.92 if ord(c) > 0x2000 else 0.54) for c in text)


def voices():
    for sc in SCENES:
        for at, name, text, *say in sc["vo"]:
            yield name, say[0] if say else text


def make_vo():
    (HERE / "assets/vo").mkdir(parents=True, exist_ok=True)
    for name, script in voices():
        out = HERE / f"assets/vo/{name}.mp3"
        if out.exists():
            continue
        subprocess.run(["uvx", "--from", "edge-tts", "edge-tts", *VOICE, "--text", script, "--write-media", str(out)], check=True)
        print(f"{name}: {script}")


def title(sc, t):
    body = f'''<section id="{sc["id"]}" class="clip title" data-start="{t}" data-duration="{sc["length"]}" data-track-index="0">
  <img src="assets/logo.png" alt="" /><h1>{esc(sc["title"])}</h1><p>{esc(sc.get("subtitle", ""))}</p>
</section>'''
    return [body], [f'tl.from("#{sc["id"]} > *", {{ opacity: 0, y: 30, duration: 0.7, stagger: 0.2, ease: "power3.out" }}, {t + 0.1});']


def card(sc, t):
    sid = sc["id"]
    rows = "".join(f"<li><b>{esc(a)}</b>{esc(b)}</li>" for a, b in sc["rows"])
    body = f'''<section id="{sid}" class="clip card-scene" data-start="{t}" data-duration="{sc["length"]}" data-track-index="0">
  <div class="text-card"><div class="kicker">{esc(sc["kicker"])}</div><h2>{esc(sc["heading"])}</h2><ul>{rows}</ul></div>
</section>'''
    return [body], [f'tl.from("#{sid} .text-card", {{ opacity: 0, y: 40, duration: 0.6, ease: "power3.out" }}, {t});',
                    f'tl.from("#{sid} li", {{ opacity: 0, x: -24, duration: 0.45, stagger: 0.45, ease: "power2.out" }}, {t + 0.6});']


def end(sc, t):
    sid = sc["id"]
    value = "<code>{}</code>" if sc.get("mono", True) else "<span>{}</span>"
    rows = "".join(f"<li><b>{esc(a)}</b>{value.format(esc(b))}</li>" for a, b in sc["rows"])
    more = f'<p class="more">{esc(sc["more"])}</p>' if sc.get("more") else ""
    body = f'''<section id="{sid}" class="clip card-scene" data-start="{t}" data-duration="{sc["length"]}" data-track-index="0">
  <div class="text-card end"><img src="assets/logo.png" alt="" /><h2>{esc(sc["heading"])}</h2><ul>{rows}</ul>{more}</div>
</section>'''
    return [body], [f'tl.from("#{sid} .text-card", {{ opacity: 0, y: 40, duration: 0.6, ease: "power3.out" }}, {t});',
                    f'tl.from("#{sid} li", {{ opacity: 0, x: -24, duration: 0.4, stagger: 0.3 }}, {t + 0.5});',
                    f'tl.from("#{sid} .more", {{ opacity: 0, y: 16, duration: 0.5 }}, {t + sc.get("more_at", min(4.8, sc["length"] - 2.5))});']


def sub(sc, t):
    return [f'<div id="{sc["id"]}" class="clip" data-composition-id="{sc["composition"]}" data-composition-src="compositions/{sc["composition"]}.html" '
            f'data-start="{t}" data-duration="{sc["length"]}" data-track-index="0"></div>'], []


def clip(sc, t):
    sid, L = sc["id"], sc["length"]
    f, v = fit(sc.get("rect", SCREEN), sc["src"])
    sp = sc.get("speed", [])
    speed = "".join(f'<span id="{sid}-sp{i}">{esc(s)}</span>' for i, (_, s) in enumerate(sp))
    body = [f'''<section id="{sid}" class="clip" data-start="{t}" data-duration="{L}" data-track-index="0">
  <div class="chip"><span class="step">{esc(sc["step"])}</span><span class="label">{esc(sc["label"])}</span></div>
  {f'<div class="speed">{speed}</div>' if speed else ''}
  <div class="frame" style="{box(f)}"></div>
</section>
<video id="{sid}-v" class="clip vid" data-start="{t}" data-duration="{L}" data-track-index="1" src="{sc["src"]}" muted playsinline
  style="{box(v)}"></video>''']
    js = [f'tl.set("#{sid}-v", {{ opacity: 0 }}, 0);',
          f'tl.fromTo("#{sid} .frame, #{sid}-v", {{ opacity: 0, scale: 0.97 }}, {{ opacity: 1, scale: 1, duration: 0.5, ease: "power3.out" }}, {t});']
    k = v["width"] / size(sc["src"])[0]
    for i, (m0, m1, mx, my, mw, mh) in enumerate(sc.get("marks", [])):
        h = mh * k + 12
        arm = round(min(32, h * 0.4))
        body.append(f'<div id="{sid}-m{i}" class="clip mark" data-start="{round(t + m0, 2)}" data-duration="{round(m1 - m0, 2)}" data-track-index="4" '
                    f'style="left:{round(v["left"] + mx * k - 6, 1)}px;top:{round(v["top"] + my * k - 6, 1)}px;width:{round(mw * k + 12, 1)}px;height:{round(h, 1)}px;--arm:{arm}px"><i></i><i></i><i></i><i></i></div>')
        js.append(f'tl.fromTo("#{sid}-m{i}", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.45, ease: "power2.out" }}, {round(t + m0, 2)});')
        for n, (dx, dy) in enumerate(((-14, -14), (14, -14), (-14, 14), (14, 14)), 1):
            js.append(f'tl.fromTo("#{sid}-m{i} i:nth-child({n})", {{ x: {dx}, y: {dy} }}, {{ x: 0, y: 0, duration: 0.6, ease: "power3.out" }}, {round(t + m0, 2)});')
    for i, (at, _) in enumerate(sp):
        if i:
            js.append(f'tl.set("#{sid}-sp{i}", {{ display: "none" }}, 0);')
            js.append(f'tl.set("#{sid}-sp{i - 1}", {{ display: "none" }}, {t + at});')
            js.append(f'tl.set("#{sid}-sp{i}", {{ display: "inline" }}, {t + at});')
            js.append(f'tl.fromTo("#{sid} .speed", {{ backgroundColor: "#002387", color: "#ffffff" }}, {{ backgroundColor: "#ffffff", color: "#002387", duration: 0.8, ease: "power2.out", immediateRender: false }}, {t + at});')
    return body, js


ICONS = dict(
    camera='<rect x="8" y="22" width="56" height="38" rx="8"/><circle cx="36" cy="41" r="11"/><path d="M25 22l5-9h12l5 9"/>',
    ai='<rect x="17" y="17" width="38" height="38" rx="7"/><path d="M27 9v8M36 9v8M45 9v8M27 55v8M36 55v8M45 55v8M9 27h8M9 36h8M9 45h8M55 27h8M55 36h8M55 45h8"/>'
       '<text x="36" y="42" text-anchor="middle" font-size="16" font-weight="800" stroke="none" fill="currentColor">AI</text>',
    dashboard='<rect x="7" y="11" width="58" height="40" rx="6"/><path d="M28 62h16M36 51v11M20 41v-7M30 41v-14M40 41v-5M50 41v-17"/>',
    nas='<rect x="14" y="8" width="44" height="56" rx="7"/><path d="M14 26h44M14 45h44"/><circle cx="47" cy="17" r="2.5"/><circle cx="47" cy="35" r="2.5"/><circle cx="47" cy="54" r="2.5"/>',
)


def flow(sc, t):
    """nodes: (아이콘, 이름, 설명, 켜지는 시각). 아이콘이 verdict 면 OK·NG 알약."""
    sid, nodes = sc["id"], sc["nodes"]
    parts = []
    for i, (icon, name, note, _) in enumerate(nodes):
        if i:
            parts.append(f'<div class="arrow" id="{sid}-a{i}"></div>')
        art = ('<div class="pills"><em class="ok">OK</em><em class="ng">NG</em></div>' if icon == "verdict"
               else f'<svg viewBox="0 0 72 72">{ICONS[icon]}</svg>')
        parts.append(f'<div class="node" id="{sid}-n{i}"><div class="art">{art}</div><b>{esc(name)}</b><span>{esc(note)}</span></div>')
    body = f'''<section id="{sid}" class="clip flow" data-start="{t}" data-duration="{sc["length"]}" data-track-index="0">
  <h2 id="{sid}-h">{esc(sc["heading"])}</h2>
  <div class="flow-row">{"".join(parts)}</div>
</section>'''
    js = [f'tl.from("#{sid}-h", {{ opacity: 0, y: 20, duration: 0.5, ease: "power3.out" }}, {t});']
    for i, (icon, *_, at) in enumerate(nodes):
        at = round(t + at, 2)
        if i:
            js.append(f'tl.fromTo("#{sid}-a{i}", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.35, ease: "power2.out" }}, {round(at - 0.35, 2)});')
        js.append(f'tl.fromTo("#{sid}-n{i}", {{ opacity: 0.25, y: 24 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "back.out(1.6)" }}, {at});')
        js.append(f'tl.to("#{sid}-n{i}", {{ borderColor: "#002387", duration: 0.3 }}, {at});')
        if icon == "verdict":
            js.append(f'tl.from("#{sid}-n{i} .ok", {{ scale: 0.4, opacity: 0, duration: 0.35, ease: "back.out(3)" }}, {round(at + 0.3, 2)});')
            js.append(f'tl.from("#{sid}-n{i} .ng", {{ scale: 0.4, opacity: 0, duration: 0.35, ease: "back.out(3)" }}, {round(at + 0.8, 2)});')
    return [body], js


KINDS = dict(title=title, card=card, end=end, sub=sub, clip=clip, flow=flow)


def build():
    names = [name for name, _ in voices()]
    dup = {n for n in names if names.count(n) > 1}
    assert not dup, f"vo 이름 중복: {dup}"
    t = 0.0
    body, subs, audio, js = [], [], [], []
    for sc in SCENES:
        if sc["kind"] == "clip" and "length" not in sc:
            sc["length"] = round(dur(sc["src"]) + 0.3, 2)
        b, j = KINDS[sc["kind"]](sc, t)
        body += b
        js += j
        for at, name, text, *_ in sc["vo"]:
            if sub_width(text) > SUB_MAX_WIDTH:
                print(f"자막 두 줄 예상, 내레이션을 나누세요: {name}", file=sys.stderr)
            vd = dur(f"assets/vo/{name}.mp3")
            subs.append(f'<div id="sub-{name}" class="clip sub" data-start="{round(t + at, 2)}" data-duration="{round(vd + 0.3, 2)}" data-track-index="2">{esc(text)}</div>')
            audio.append(f'<audio id="vo-{name}" data-start="{round(t + at, 2)}" data-duration="{round(vd, 2)}" data-track-index="3" src="assets/vo/{name}.mp3"></audio>')
            js.append(f'tl.from("#sub-{name}", {{ opacity: 0, y: 12, duration: 0.3 }}, {round(t + at, 2)});')
        t = round(t + sc["length"], 2)

    html = (HERE / "template.tpl").read_text(encoding="utf-8")
    html = html.replace("{{DURATION}}", str(t)).replace("{{BODY}}", "\n".join(body + subs + audio)).replace("{{JS}}", "\n      ".join(js))
    (HERE / "index.html").write_text(html, encoding="utf-8")
    print(json.dumps({"total": t}))


if sys.argv[1:] == ["vo"]:
    make_vo()
else:
    build()
