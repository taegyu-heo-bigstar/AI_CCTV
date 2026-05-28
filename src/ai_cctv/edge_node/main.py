# Edge node 실행 진입점 파일입니다.
# GStreamer + MediaMTX 송출 명령을 생성하여 운영자가 실행할 수 있게 출력합니다.
# 실제 장기 실행 서비스화는 systemd 또는 운영 스크립트에서 담당합니다.

from .streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder


def build_default_edge_stream_command():
    """기본 Edge node 송출 명령을 생성합니다.

    인자:
        없음.
    반환값:
        GStreamer 송출 명령 문자열을 반환합니다.
    """

    return MediaMtxGStreamerCommandBuilder(EdgeStreamConfig()).build_shell_command_text()


def main():
    """Edge node 실행 시 송출 명령을 출력합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    print(build_default_edge_stream_command())


if __name__ == "__main__":
    main()
