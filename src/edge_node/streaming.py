# Edge node 카메라 RTSP 송출 설정 파일입니다.
# GStreamer 파이프라인이 카메라 영상을 MediaMTX RTSP 경로로 publish합니다.
# 실제 프로세스 실행은 edge_node.main 또는 운영 서비스에서 수행합니다.

from dataclasses import dataclass


@dataclass(frozen=True)
class PiStreamingConfig:
    """Edge node GStreamer 영상 송출 설정을 표현합니다.

    인자:
        width: 송출 영상 너비입니다.
        height: 송출 영상 높이입니다.
        fps: 초당 프레임 수입니다.
        bitrate: x264enc에 전달할 kbps 단위 비트레이트입니다.
        mediamtx_url: MediaMTX RTSP publish URL입니다.
    반환값:
        PiStreamingConfig 인스턴스를 반환합니다.
    """

    width: int = 640
    height: int = 480
    fps: int = 30
    bitrate: int = 1000
    mediamtx_url: str = "rtsp://127.0.0.1:8554/stream"


class GStreamerMediaMtxCommandBuilder:
    """GStreamer 기반 MediaMTX 송출 명령을 생성합니다.

    인자:
        config: Edge node 영상 송출 설정입니다.
    반환값:
        GStreamerMediaMtxCommandBuilder 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """송출 명령 생성 설정을 초기화합니다.

        인자:
            config: Edge node 영상 송출 설정입니다.
        반환값:
            없음.
        """

        self.config = config or PiStreamingConfig()

    def build_command(self):
        """GStreamer 송출 명령 인자 목록을 생성합니다.

        인자:
            없음.
        반환값:
            subprocess 실행에 사용할 명령 인자 리스트를 반환합니다.
        """

        caps = (
            f"video/x-raw,width={self.config.width},height={self.config.height},"
            f"framerate={self.config.fps}/1"
        )
        return [
            "gst-launch-1.0",
            "-v",
            "libcamerasrc",
            "!",
            caps,
            "!",
            "videoconvert",
            "!",
            "x264enc",
            "tune=zerolatency",
            "speed-preset=ultrafast",
            f"bitrate={self.config.bitrate}",
            f"key-int-max={self.config.fps}",
            "!",
            "h264parse",
            "config-interval=1",
            "!",
            "rtspclientsink",
            f"location={self.config.mediamtx_url}",
            "protocols=tcp",
        ]

    def build_shell_text(self):
        """문서와 운영 스크립트에 표시할 송출 명령 문자열을 생성합니다.

        인자:
            없음.
        반환값:
            공백으로 결합된 GStreamer 명령 문자열을 반환합니다.
        """

        return " ".join(self.build_command())


class RpicamMediaMtxCommandBuilder(GStreamerMediaMtxCommandBuilder):
    """기존 import 호환을 위한 GStreamer 명령 생성기 별칭입니다.

    인자:
        config: Edge node 영상 송출 설정입니다.
    반환값:
        RpicamMediaMtxCommandBuilder 인스턴스를 반환합니다.
    """

    pass
