# Raspberry Pi 카메라 RTSP 송출 설정 파일입니다.
# rpicam-vid와 MediaMTX를 연결하기 위한 명령 구성을 제공합니다.
# 실제 프로세스 실행은 운영 스크립트나 서비스 계층에서 수행합니다.

from dataclasses import dataclass


@dataclass(frozen=True)
class PiStreamingConfig:
    """Raspberry Pi 영상 송출 설정을 표현합니다.

    인자:
        width: 송출 영상 너비입니다.
        height: 송출 영상 높이입니다.
        fps: 초당 프레임 수입니다.
        bitrate: 영상 비트레이트입니다.
        mediamtx_url: MediaMTX 입력 URL입니다.
    반환값:
        PiStreamingConfig 인스턴스를 반환합니다.
    """

    width: int = 640
    height: int = 480
    fps: int = 30
    bitrate: int = 1_000_000
    mediamtx_url: str = "rtsp://127.0.0.1:8554/stream"


class RpicamMediaMtxCommandBuilder:
    """rpicam-vid 기반 MediaMTX 송출 명령을 생성합니다.

    인자:
        config: Raspberry Pi 영상 송출 설정입니다.
    반환값:
        RpicamMediaMtxCommandBuilder 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """송출 명령 생성 설정을 초기화합니다.

        인자:
            config: Raspberry Pi 영상 송출 설정입니다.
        반환값:
            없음.
        """

        self.config = config or PiStreamingConfig()

    def build_command(self):
        """rpicam-vid 송출 명령 인자 목록을 생성합니다.

        인자:
            없음.
        반환값:
            subprocess 실행에 사용할 명령 인자 리스트를 반환합니다.
        """

        return [
            "rpicam-vid",
            "--width",
            str(self.config.width),
            "--height",
            str(self.config.height),
            "--framerate",
            str(self.config.fps),
            "--bitrate",
            str(self.config.bitrate),
            "--codec",
            "h264",
            "--inline",
            "--listen",
            "-o",
            self.config.mediamtx_url,
        ]

    def build_shell_text(self):
        """문서와 운영 스크립트에 표시할 송출 명령 문자열을 생성합니다.

        인자:
            없음.
        반환값:
            공백으로 결합된 명령 문자열을 반환합니다.
        """

        return " ".join(self.build_command())

