import hashlib
import json
from pathlib import Path

QUESTIONS_DIR = Path(__file__).parent.parent / "data"

# 신규로 시작하는 시험에 적용할 문제 버전. 차수가 바뀌면 이 값만 바꾸면 됨.
ACTIVE_VERSION = "v2"

_cache: dict[str, list] = {}


def load_questions(version: str | None = None) -> list:
    version = version or ACTIVE_VERSION
    if version not in _cache:
        path = QUESTIONS_DIR / f"questions_{version}.json"
        _cache[version] = json.loads(path.read_text(encoding="utf-8"))
    return _cache[version]


def questions_fingerprint(version: str | None = None) -> str:
    """문제 파일 내용의 지문(6자리). 배포 반영 여부를 화면에서 바로 대조하기 위한 값."""
    version = version or ACTIVE_VERSION
    path = QUESTIONS_DIR / f"questions_{version}.json"
    return hashlib.sha1(path.read_bytes()).hexdigest()[:6]
