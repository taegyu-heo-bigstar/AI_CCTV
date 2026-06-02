# pseudo Edge node 명령행 진입점 파일입니다.
# Windows에서 ai-cctv-pseudo-edge 명령으로 테스트용 Edge node를 실행합니다.
# 포트와 topic은 명령행 인자 또는 AI_CCTV_PSEUDO_* 환경 변수로 바꿀 수 있습니다.
# 실행 직후 AI server 시작 UI에 붙여넣을 연결 정보 블록을 표준 출력에 표시합니다.

import argparse

from .config import PseudoEdgeNodeConfig, merge_config_with_overrides
from .runtime import PseudoEdgeNodeRuntime


def build_argument_parser():
    """pseudo Edge node 명령행 인자 parser를 생성합니다.

    인자:
        없음.
    반환값:
        argparse.ArgumentParser 인스턴스를 반환합니다.
    """

    parser = argparse.ArgumentParser(description="AI CCTV pseudo Edge node runtime")
    parser.add_argument("--host", help="pseudo Edge node host")
    parser.add_argument("--rtsp-port", type=int, help="RTSP 검증용 TCP 포트")
    parser.add_argument("--rtsp-path", help="RTSP URL path")
    parser.add_argument("--mqtt-port", type=int, help="MQTT broker TCP 포트")
    parser.add_argument("--mqtt-topic", help="MQTT 상태 topic")
    parser.add_argument("--recovery-port", type=int, help="백업 복구 HTTP 포트")
    parser.add_argument("--backup-dir", help="pseudo 백업 폴더")
    parser.add_argument("--status-interval", type=float, help="MQTT 상태 발행 주기")
    parser.add_argument("--frame-width", type=int, help="synthetic 영상 너비")
    parser.add_argument("--frame-height", type=int, help="synthetic 영상 높이")
    parser.add_argument("--frame-fps", type=int, help="synthetic 영상 FPS")
    return parser


def build_config_from_args(args):
    """명령행 인자와 환경 변수를 조합해 실행 설정을 생성합니다.

    인자:
        args: argparse가 반환한 Namespace 객체입니다.
    반환값:
        PseudoEdgeNodeConfig 인스턴스를 반환합니다.
    """

    return merge_config_with_overrides(
        PseudoEdgeNodeConfig.from_environment(),
        host=args.host,
        rtsp_port=args.rtsp_port,
        rtsp_path=args.rtsp_path,
        mqtt_port=args.mqtt_port,
        mqtt_topic=args.mqtt_topic,
        backup_recovery_port=args.recovery_port,
        backup_dir=args.backup_dir,
        status_interval_seconds=args.status_interval,
        frame_width=args.frame_width,
        frame_height=args.frame_height,
        frame_fps=args.frame_fps,
    )


def main(argv=None):
    """pseudo Edge node 실행체를 시작합니다.

    인자:
        argv: 명령행 인자 목록이며 없으면 sys.argv를 사용합니다.
    반환값:
        프로세스 종료 코드 정수를 반환합니다.
    """

    args = build_argument_parser().parse_args(argv)
    config = build_config_from_args(args)
    runtime = PseudoEdgeNodeRuntime(config)
    return runtime.run_forever()


if __name__ == "__main__":
    raise SystemExit(main())
