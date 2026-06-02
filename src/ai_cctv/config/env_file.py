# AI CCTV .env 설정 파일 유틸입니다.
# 프로젝트 루트 또는 실행 위치 상위 경로의 .env 파일을 읽습니다.
# OS 환경변수는 설정값 출처로 사용하지 않습니다.
# UI가 입력한 값은 현재 프로세스의 런타임 오버라이드로만 보관합니다.

from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import Iterable


_ENV_FILE_NAME = ".env"
_runtime_values: dict[str, str] = {}
_runtime_lock = RLock()


def get_env_value(key: str, default: str | None = "") -> str:
    """지정한 설정 키의 값을 런타임 오버라이드 또는 .env 파일에서 읽습니다.

    인자:
        key: 조회할 설정 키 이름입니다.
        default: 값이 없을 때 반환할 기본 문자열입니다.
    반환값:
        설정값 문자열을 반환합니다.
    """

    normalized_key = _normalize_key(key)
    with _runtime_lock:
        if normalized_key in _runtime_values:
            runtime_value = _runtime_values[normalized_key]
            if runtime_value != "":
                return runtime_value
            return "" if default is None else str(default)

    value = _read_env_file_values().get(normalized_key)
    if value is None or value == "":
        return "" if default is None else str(default)
    return value


def get_env_int(key: str, default: int) -> int:
    """지정한 설정 키의 값을 정수로 읽습니다.

    인자:
        key: 조회할 설정 키 이름입니다.
        default: 값이 없을 때 사용할 기본 정수입니다.
    반환값:
        정수로 변환한 설정값을 반환합니다.
    """

    return int(get_env_value(key, str(default)))


def get_env_float(key: str, default: float) -> float:
    """지정한 설정 키의 값을 실수로 읽습니다.

    인자:
        key: 조회할 설정 키 이름입니다.
        default: 값이 없을 때 사용할 기본 실수입니다.
    반환값:
        실수로 변환한 설정값을 반환합니다.
    """

    return float(get_env_value(key, str(default)))


def get_env_bool(key: str, default: bool) -> bool:
    """지정한 설정 키의 값을 불리언으로 읽습니다.

    인자:
        key: 조회할 설정 키 이름입니다.
        default: 값이 없을 때 사용할 기본 불리언입니다.
    반환값:
        true 계열 문자열이면 True, false 계열 문자열이면 False를 반환합니다.
    """

    raw_value = get_env_value(key, None)
    if raw_value == "":
        return default
    return raw_value.strip().lower() in {"1", "true", "yes", "y", "on"}


def set_runtime_env_values(values: dict[str, object | None]) -> None:
    """현재 프로세스에서만 사용할 설정 오버라이드를 등록합니다.

    인자:
        values: 설정 키와 값의 딕셔너리이며 None 값은 해당 키 삭제를 의미합니다.
    반환값:
        없음.
    """

    with _runtime_lock:
        for key, value in values.items():
            normalized_key = _normalize_key(key)
            if value is None:
                _runtime_values.pop(normalized_key, None)
            else:
                _runtime_values[normalized_key] = str(value)


def clear_runtime_env_values(keys: Iterable[str] | None = None) -> None:
    """현재 프로세스의 설정 오버라이드를 제거합니다.

    인자:
        keys: 제거할 설정 키 목록이며 None이면 전체를 제거합니다.
    반환값:
        없음.
    """

    with _runtime_lock:
        if keys is None:
            _runtime_values.clear()
            return
        for key in keys:
            _runtime_values.pop(_normalize_key(key), None)


def _read_env_file_values() -> dict[str, str]:
    """발견한 .env 파일의 key-value 값을 읽습니다.

    인자:
        없음.
    반환값:
        설정 키와 값의 딕셔너리를 반환합니다.
    """

    env_path = _find_env_file()
    if env_path is None:
        return {}

    try:
        return _parse_env_text(env_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def _find_env_file() -> Path | None:
    """실행 위치와 소스 상위 경로에서 .env 파일을 찾습니다.

    인자:
        없음.
    반환값:
        발견한 .env 경로 또는 None을 반환합니다.
    """

    for candidate in _iter_env_file_candidates():
        if candidate.is_file():
            return candidate
    return None


def _iter_env_file_candidates():
    """중복 없이 .env 후보 경로를 생성합니다.

    인자:
        없음.
    반환값:
        Path 객체 iterator를 반환합니다.
    """

    seen = set()
    search_roots = [Path.cwd(), Path(__file__).resolve()]
    for search_root in search_roots:
        current_dir = search_root if search_root.is_dir() else search_root.parent
        for directory in [current_dir, *current_dir.parents]:
            candidate = directory / _ENV_FILE_NAME
            normalized = candidate.resolve()
            if normalized in seen:
                continue
            seen.add(normalized)
            yield candidate


def _parse_env_text(text: str) -> dict[str, str]:
    """dotenv 형식의 텍스트를 설정 딕셔너리로 변환합니다.

    인자:
        text: .env 파일 내용입니다.
    반환값:
        설정 키와 값의 딕셔너리를 반환합니다.
    """

    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_key = _normalize_key(key)
        if normalized_key:
            values[normalized_key] = _strip_env_value(value)
    return values


def _strip_env_value(value: str) -> str:
    """dotenv 값 주변의 공백과 단순 따옴표를 제거합니다.

    인자:
        value: 원본 dotenv 값 문자열입니다.
    반환값:
        정리된 값 문자열을 반환합니다.
    """

    stripped = value.strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] and stripped[0] in {"'", '"'}:
        return stripped[1:-1]
    return stripped


def _normalize_key(key: str) -> str:
    """PowerShell 접두사를 제거하고 설정 키 이름을 정규화합니다.

    인자:
        key: 원본 설정 키 문자열입니다.
    반환값:
        정규화된 설정 키 문자열을 반환합니다.
    """

    return key.strip().replace("$env:", "").replace("$Env:", "")
