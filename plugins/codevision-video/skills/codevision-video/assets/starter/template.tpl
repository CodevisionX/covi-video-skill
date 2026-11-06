<!doctype html>
<html lang="ko">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Pretendard"; font-weight: 400; src: url("assets/fonts/Pretendard-Regular.woff2") format("woff2"); }
      @font-face { font-family: "Pretendard"; font-weight: 500; src: url("assets/fonts/Pretendard-Medium.woff2") format("woff2"); }
      @font-face { font-family: "Pretendard"; font-weight: 600; src: url("assets/fonts/Pretendard-SemiBold.woff2") format("woff2"); }
      @font-face { font-family: "Pretendard"; font-weight: 700; src: url("assets/fonts/Pretendard-Bold.woff2") format("woff2"); }
      @font-face { font-family: "Pretendard"; font-weight: 800; src: url("assets/fonts/Pretendard-ExtraBold.woff2") format("woff2"); }
      :root {
        --ground: #f4f6fa;
        --brand: #002387;
        --ink: #0b1a3a;
        --ink-2: #4a5670;
        --line: #d9dfeb;
        --ok: #12a150;
        --ng: #ff6b2c;
        --lift: 0 6px 16px rgba(11, 26, 58, 0.12);
      }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: var(--ground); }
      #root { position: relative; width: 100%; height: 100%; font-family: "Pretendard", sans-serif; color: var(--ink); letter-spacing: -0.02em; }
      .clip { position: absolute; inset: 0; }

      .title { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 36px; }
      .title img { width: 420px; }
      .title h1 { font-size: 92px; font-weight: 800; color: var(--brand); }
      .title p { font-size: 34px; font-weight: 500; color: var(--ink-2); }

      .card-scene { display: flex; align-items: center; justify-content: center; }
      .text-card { width: 1320px; background: #fff; border: 1px solid var(--line); border-radius: 36px; padding: 72px 88px; box-shadow: var(--lift); margin-bottom: 80px; }
      .text-card .kicker { font-size: 28px; font-weight: 700; color: var(--brand); margin-bottom: 18px; }
      .text-card h2 { font-size: 64px; font-weight: 800; margin-bottom: 44px; }
      .text-card li { list-style: none; font-size: 36px; font-weight: 500; color: var(--ink-2); padding: 16px 0; border-top: 1px solid var(--line); display: flex; gap: 24px; }
      .text-card li b { color: var(--ink); font-weight: 700; min-width: 280px; }
      .text-card.end { width: 1500px; padding: 56px 80px; }
      .text-card.end img { width: 220px; margin-bottom: 18px; }
      .text-card.end h2 { margin-bottom: 28px; }
      .text-card.end li { font-size: 30px; padding: 14px 0; }
      .text-card.end li b { min-width: 150px; color: var(--brand); }
      .shot { position: absolute; top: 210px; width: 820px; margin: 0; }
      .shot .screen { width: 820px; height: 461px; border-radius: 22px; border: 12px solid #fff; box-shadow: var(--lift); overflow: hidden; position: relative; background: #f4f6fa; box-sizing: content-box; }
      .shot .screen > img { width: 100%; height: 100%; object-fit: cover; display: block; }
      .shot .screen.boot { background: #000; display: flex; flex-direction: column; align-items: center; justify-content: center; }
      .shot .screen.boot .logo { width: 180px; height: auto; flex: none; }
      .shot .screen.boot .dots { display: flex; gap: 4px; margin-top: 37px; }
      .shot .screen.boot .dot { width: 6px; height: 6px; flex: none; opacity: 0.2; }
      .shot figcaption { margin-top: 26px; text-align: center; font-size: 32px; font-weight: 700; color: var(--ink); }
      .brand-note { position: absolute; top: 820px; left: 0; right: 0; text-align: center; font-size: 26px; font-weight: 500; color: var(--ink-2); }
      .mark { position: absolute; inset: auto; z-index: 4; background: rgba(255, 107, 44, 0.1); }
      .mark i { position: absolute; width: var(--arm); height: var(--arm); border: 0 solid var(--ng); }
      .mark i:nth-child(1) { left: 0; top: 0; border-width: 5px 0 0 5px; }
      .mark i:nth-child(2) { right: 0; top: 0; border-width: 5px 5px 0 0; }
      .mark i:nth-child(3) { left: 0; bottom: 0; border-width: 0 0 5px 5px; }
      .mark i:nth-child(4) { right: 0; bottom: 0; border-width: 0 5px 5px 0; }
      .text-card.end .more { margin-top: 24px; font-size: 28px; font-weight: 600; color: var(--brand); }
      .text-card code { font-family: "DejaVu Sans Mono", monospace; font-size: 28px; color: var(--ink); }

      .chip { position: absolute; left: 96px; top: 56px; display: flex; gap: 14px; align-items: center; }
      .chip .step { background: var(--brand); color: #fff; font-size: 26px; font-weight: 700; padding: 10px 22px; border-radius: 999px; }
      .chip .label { font-size: 30px; font-weight: 700; color: var(--ink); }
      .speed { position: absolute; right: 96px; top: 60px; background: #fff; border: 1px solid var(--line); color: var(--brand); font-size: 24px; font-weight: 700; padding: 10px 20px; border-radius: 999px; }
      .frame { position: absolute; border-radius: 22px; box-shadow: var(--lift); background: #fff; border: 1px solid var(--line); }
      video.vid { inset: auto; position: absolute; object-fit: contain; border-radius: 10px; z-index: 2; }

      .flow { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 72px; padding-bottom: 90px; }
      .flow h2 { font-size: 56px; font-weight: 800; color: var(--ink); }
      .flow-row { display: flex; align-items: center; gap: 18px; }
      .flow .node { width: 268px; height: 300px; background: #fff; border: 3px solid var(--line); border-radius: 28px; box-shadow: var(--lift); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; }
      .flow .node .art { height: 104px; display: flex; align-items: center; justify-content: center; color: var(--brand); }
      .flow .node svg { width: 96px; height: 96px; fill: none; stroke: currentColor; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
      .flow .node svg text { font-family: "Pretendard", sans-serif; }
      .flow .node b { font-size: 34px; font-weight: 800; color: var(--ink); }
      .flow .node span { font-size: 26px; font-weight: 500; color: var(--ink-2); }
      .flow .pills { display: flex; flex-direction: column; gap: 8px; }
      .flow .pills em { font-style: normal; font-size: 30px; font-weight: 800; color: #fff; padding: 3px 30px; border-radius: 999px; text-align: center; }
      .flow .pills .ok { background: var(--ok); }
      .flow .pills .ng { background: var(--ng); color: var(--ink); }
      .flow .arrow { width: 52px; height: 4px; background: var(--brand); position: relative; transform-origin: left center; }
      .flow .arrow::after { content: ""; position: absolute; right: -4px; top: -8px; border-left: 14px solid var(--brand); border-top: 10px solid transparent; border-bottom: 10px solid transparent; }

      .sub { z-index: 5; position: absolute; inset: auto 0 32px 0; margin: 0 auto; width: fit-content; max-width: 1728px; background: rgba(11, 26, 58, 0.88); color: #fff; font-size: 40px; font-weight: 600; line-height: 1.45; padding: 14px 34px; border-radius: 10px; text-align: center; word-break: keep-all; }
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{DURATION}}" data-width="1920" data-height="1080">
{{BODY}}
    </div>
    <script>
      const tl = gsap.timeline({ paused: true });
      {{JS}}
      window.__timelines = window.__timelines || {};
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
