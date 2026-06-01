# Edge node 실행 진입점 파일입니다.
# MediaMTX 준비와 GStreamer 송출 프로세스를 Python 런타임으로 실행합니다.
# 운영자는 ai-cctv-edge 명령으로 Raspberry Pi 송출 노드를 시작합니다.

import argparse
import os

from .os_guard import ensure_supported_edge_os
from .runtime import build_default_edge_runtime


def build_default_edge_stream_command():
    """기본 Edge node 송출 명령 문자열을 생성합니다.

    인자:
        없음.
    반환값:
        GStreamer 송출 명령 문자열을 반환합니다.
    """

    return build_default_edge_runtime().command_builder.build_shell_command_text()


def build_argument_parser():
    """Edge node 실행 옵션 파서를 생성합니다.

    인자:
        없음.
    반환값:
        argparse.ArgumentParser 객체를 반환합니다.
    """

    parser = argparse.ArgumentParser(description="AI CCTV Edge node runtime")
    parser.add_argument(
        "--print-command",
        action="store_true",
        help="실제 실행 대신 GStreamer 명령만 출력합니다.",
    )
    parser.add_argument(
        "--no-support-services",
        action="store_true",
        help="MQTT 상태 발행과 백업 복구 API 보조 프로세스를 실행하지 않습니다.",
    )
    return parser


def main(argv=None):
    """Edge node 런타임을 실행합니다.

    인자:
        argv: 명령행 인자 목록입니다.
    반환값:
        없음.
    """

    ensure_supported_edge_os()
    args = build_argument_parser().parse_args(argv)
    if args.no_support_services:
        os.environ["AI_CCTV_EDGE_ENABLE_SUPPORT_SERVICES"] = "0"

    runtime = build_default_edge_runtime()
    if args.print_command:
        print(runtime.command_builder.build_shell_command_text())
        return

    raise SystemExit(runtime.run())


if __name__ == "__main__":
    main()
