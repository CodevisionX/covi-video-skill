"""영상 제작에 필요한 도구를 점검한다. 빠진 게 있으면 OS 별 설치 명령을 출력하고 종료 코드 1."""
import platform
import re
import shutil
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

MIN_NODE = 22
MIN_PYTHON = (3, 9)

INSTALL = {
    "Windows": {
        "node": "winget install OpenJS.NodeJS.LTS",
        "uv": "winget install astral-sh.uv",
        "ffmpeg": "winget install Gyan.FFmpeg",
        "python": "winget install Python.Python.3.12",
    },
    "Linux": {
        "node": "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.3/install.sh | bash && nvm install 22",
        "uv": "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "ffmpeg": "sudo apt install -y ffmpeg",
        "python": "sudo apt install -y python3",
    },
    "Darwin": {
        "node": "brew install node",
        "uv": "brew install uv",
        "ffmpeg": "brew install ffmpeg",
        "python": "brew install python",
    },
}


def version_of(tool):
    path = shutil.which(tool)
    if not path:
        return None
    # Windows 의 npx 는 .cmd 라 찾은 전체 경로로 실행해야 한다.
    out = subprocess.run([path, "--version"], capture_output=True, text=True, errors="replace", timeout=60)
    return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""


def main():
    missing = []

    def report(name, ok, detail, key):
        print(f"{'OK ' if ok else 'NG '} {name}: {detail}")
        if not ok and key not in missing:
            missing.append(key)

    py_ok = sys.version_info[:2] >= MIN_PYTHON
    report("python", py_ok, platform.python_version(), "python")

    node = version_of("node")
    major = int(re.search(r"\d+", node).group()) if node and re.search(r"\d+", node) else 0
    report("node", major >= MIN_NODE, f"{node or '없음'} ({MIN_NODE} 이상 필요)", "node")
    report("npx", bool(version_of("npx")), version_of("npx") or "없음", "node")

    for tool, key in [("uvx", "uv"), ("ffmpeg", "ffmpeg"), ("ffprobe", "ffmpeg")]:
        found = version_of(tool)
        report(tool, found is not None, found or "없음", key)

    if not missing:
        print("\n준비 완료")
        return 0

    commands = INSTALL.get(platform.system(), INSTALL["Linux"])
    print(f"\n설치 필요 ({platform.system()}):")
    for key in missing:
        print(f"  {commands[key]}")
    if platform.system() == "Windows":
        print("설치 후 터미널과 Claude Code 를 다시 열어야 PATH 가 반영된다.")
    return 1


sys.exit(main())
