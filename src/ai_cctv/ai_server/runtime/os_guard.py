# AI server가 지원 대상 운영체제에서 실행되는지 확인하는 파일입니다.
# 본 프로젝트의 AI server는 Windows 데스크톱 실행을 기준으로 구성됩니다.
# Windows가 아니면 명확한 오류 메시지를 출력하고 진입점에서 종료합니다.

import platform
import sys


def is_windows_os(system_name=None):
    """현재 운영체제가 Windows인지 판단합니다.

    인자:
        system_name: 테스트나 호출자가 지정한 운영체제 이름입니다.
    반환값:
        Windows이면 True, 아니면 False를 반환합니다.
    """

    resolved_name = system_name or platform.system()
    return resolved_name.lower() == "windows"


def ensure_windows_os(system_name=None, stream=None):
    """AI server 실행 대상 운영체제가 Windows인지 확인하고 아니면 종료합니다.

    인자:
        system_name: 테스트나 호출자가 지정한 운영체제 이름입니다.
        stream: 오류 메시지를 출력할 스트림이며 기본값은 표준 오류입니다.
    반환값:
        Windows이면 None을 반환합니다.
    """

    resolved_name = system_name or platform.system()
    if is_windows_os(resolved_name):
        return

    output_stream = stream or sys.stderr
    print(
        "AI server는 Windows 데스크톱 환경에서만 실행할 수 있습니다. "
        f"현재 감지된 OS: {resolved_name}",
        file=output_stream,
    )
    raise SystemExit(1)
