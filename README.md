# covi-video-skill

코드비전 사내 영상을 만드는 Claude Code 플러그인이에요. 녹화본이나 내용만 주면 회사 색, Pretendard, SunHi 내레이션으로 설명 영상을 만들어 줘요.

## 설치

Claude Code가 설치되어 있으면 돼요. 공개 레포라 GitHub 로그인이나 권한 요청은 필요 없어요.

**1. 플러그인 설치**

```bash
claude plugin marketplace add https://github.com/CodevisionX/covi-video-skill.git
claude plugin install codevision-video@covi
```

**2. 자동 업데이트 켜기**

Claude Code에서 `/plugin` → Marketplaces → `covi` → Enable auto-update를 선택해요. Anthropic 공식이 아닌 마켓플레이스는 기본으로 꺼져 있어요.

## 사용

Claude Code에서 평소처럼 말하면 돼요.

```text
이 녹화본에 설명 입혀서 영상 만들어줘 ~/Videos/raw.webm
우리 플랫폼 소개 영상 만들어줘
```

처음 쓰는 PC에서는 Node.js 22 이상, Python, uv, ffmpeg가 있는지 Claude가 점검하고, 빠진 도구의 설치 명령을 알려 줘요. 내레이션과 첫 렌더 준비에는 인터넷 연결이 필요해요.

## 수동 업데이트

```bash
claude plugin marketplace update covi
claude plugin update codevision-video@covi
```

Claude Code를 다시 시작하면 반영돼요.

## 스킬 수정

- 스킬 본문과 스타터는 `plugins/codevision-video/skills/codevision-video/`에 있어요.
- `version`을 적지 않아서 커밋마다 새 버전으로 배포돼요. 공개 레포라 고객사 정보나 원본 영상이 들어가지 않게, 푸시 전에 꼭 확인해 주세요.

## 포함된 서드파티

Pretendard 폰트는 SIL Open Font License 1.1을 따라요. 전문은 `plugins/codevision-video/skills/codevision-video/assets/starter/assets/fonts/OFL.txt`에 있어요.
