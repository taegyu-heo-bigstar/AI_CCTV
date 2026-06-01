# Edge node가 지원 대상 운영체제에서 실행되는지 확인하는 파일입니다.
# Edge node는 Raspberry Pi 계열 Linux 운영을 기준으로 구성됩니다.
# Linux가 아니거나 확인 가능한 배포판이 Debian 계열이 아니면 실행을 중단합니다.

import platform
import sys
from pathlib import Path


DEBIAN_FAMILY_IDS = frozenset({"debian", "raspbian", "ubuntu"})


def read_os_release(path="/etc/os-release"):
    """os-release 파일을 읽어 운영체제 배포판 정보를 반환합니다.

    인자:
        path: 읽을 os-release 파일 경로입니다.
    반환값:
        os-release key/value 딕셔너리를 반환합니다.
    """

    for os_release_path in _resolve_os_release_paths(path):
        try:
            return _parse_os_release_text(os_release_path.read_text(encoding="utf-8"))
        except OSError:
            continue
    return {}


def is_supported_edge_os(system_name=None, os_release=None):
    """Edge node 실행이 허용되는 운영체제인지 판단합니다.

    인자:
        system_name: 테스트나 호출자가 지정한 운영체제 이름입니다.
        os_release: 테스트나 호출자가 지정한 os-release 정보입니다.
    반환값:
        지원 대상이면 True, 아니면 False를 반환합니다.
    """

    resolved_name = system_name or platform.system()
    if resolved_name.lower() != "linux":
        return False

    resolved_release = os_release if os_release is not None else read_os_release()
    if not resolved_release:
        return True

    distro_tokens = _collect_distribution_tokens(resolved_release)
    if not distro_tokens:
        return True
    return bool(distro_tokens & DEBIAN_FAMILY_IDS)


def ensure_supported_edge_os(system_name=None, os_release=None, stream=None):
    """Edge node 운영체제가 Linux 또는 Debian 계열인지 확인하고 아니면 종료합니다.

    인자:
        system_name: 테스트나 호출자가 지정한 운영체제 이름입니다.
        os_release: 테스트나 호출자가 지정한 os-release 정보입니다.
        stream: 오류 메시지를 출력할 스트림이며 기본값은 표준 오류입니다.
    반환값:
        지원 대상이면 None을 반환합니다.
    """

    if is_supported_edge_os(system_name=system_name, os_release=os_release):
        return

    resolved_name = system_name or platform.system()
    resolved_release = os_release if os_release is not None else read_os_release()
    distro = resolved_release.get("PRETTY_NAME") or resolved_release.get("ID") or "unknown"
    print(
        "Edge node는 Linux 또는 Debian 계열(Debian/Raspbian/Ubuntu)에서만 실행할 수 있습니다. "
        f"현재 감지된 OS: {resolved_name}, 배포판: {distro}",
        file=stream or sys.stderr,
    )
    raise SystemExit(1)


def _parse_os_release_text(text):
    """os-release 파일 내용을 key/value 딕셔너리로 변환합니다.

    인자:
        text: os-release 파일 원문입니다.
    반환값:
        os-release key/value 딕셔너리를 반환합니다.
    """

    values = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = _strip_os_release_quotes(value.strip())
    return values


def _resolve_os_release_paths(path):
    """읽을 os-release 후보 경로 목록을 생성합니다.

    인자:
        path: 우선 확인할 os-release 파일 경로입니다.
    반환값:
        Path 객체 목록을 반환합니다.
    """

    paths = [Path(path)]
    default_usr_release = Path("/usr/lib/os-release")
    if str(path) == "/etc/os-release":
        paths.append(default_usr_release)
    return paths


def _strip_os_release_quotes(value):
    """os-release 값의 양끝 따옴표를 제거합니다.

    인자:
        value: os-release 값 문자열입니다.
    반환값:
        따옴표가 제거된 문자열을 반환합니다.
    """

    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _collect_distribution_tokens(os_release):
    """os-release 정보에서 배포판 계열 판정용 토큰을 수집합니다.

    인자:
        os_release: os-release key/value 딕셔너리입니다.
    반환값:
        소문자 배포판 토큰 집합을 반환합니다.
    """

    tokens = set()
    for key in ("ID", "ID_LIKE"):
        for token in os_release.get(key, "").replace(",", " ").split():
            normalized = token.strip().lower()
            if normalized:
                tokens.add(normalized)
    return tokens
