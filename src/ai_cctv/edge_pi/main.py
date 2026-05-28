# Raspberry Pi 실행 진입점 파일입니다.
# GStreamer + MediaMTX 송출 명령을 생성하고 운영자가 실행할 수 있게 출력합니다.
# 실제 장기 실행 서비스화는 systemd나 운영 스크립트에서 이 명령을 사용합니다.

from .streaming import GStreamerMediaMtxCommandBuilder, PiStreamingConfig


def build_default_streaming_command():
    """기본 Raspberry Pi 송출 명령을 생성합니다.

    인자:
        없음.
    반환값:
        GStreamer 송출 명령 문자열을 반환합니다.
    """

    return GStreamerMediaMtxCommandBuilder(PiStreamingConfig()).build_shell_text()


def main():
    """Raspberry Pi 실행용 송출 명령을 출력합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    print(build_default_streaming_command())


if __name__ == "__main__":
    main()

