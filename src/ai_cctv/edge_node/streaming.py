# Edge node RTSP 송출 명령 생성 파일입니다.
# Raspberry Pi 카메라 영상을 GStreamer로 MediaMTX에 publish하는 명령을 만듭니다.
# 프로세스 실행 책임은 운영 서비스나 ai_cctv.edge_node.main 진입점에 둡니다.

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeStreamConfig:
    """Edge node 영상 송출 설정을 표현합니다.

    인자:
        width: 송출 영상 너비입니다.
        height: 송출 영상 높이입니다.
        fps: 초당 프레임 수입니다.
        bitrate: x264enc에 전달할 kbps 단위 비트레이트입니다.
        mediamtx_url: MediaMTX RTSP publish URL입니다.
    반환값:
        EdgeStreamConfig 인스턴스를 반환합니다.
    """

    width: int = 640
    height: int = 480
    fps: int = 30
    bitrate: int = 1000
    mediamtx_url: str = "rtsp://127.0.0.1:8554/stream"


class MediaMtxGStreamerCommandBuilder:
    """GStreamer 기반 MediaMTX 송출 명령을 생성합니다.

    인자:
        config: Edge node 영상 송출 설정입니다.
    반환값:
        MediaMtxGStreamerCommandBuilder 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """송출 명령 생성 설정을 초기화합니다.

        인자:
            config: Edge node 영상 송출 설정입니다.
        반환값:
            없음.
        """

        self.config = config or EdgeStreamConfig()

    def build_command_args(self):
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

    def build_shell_command_text(self):
        """운영 스크립트에 표시할 송출 명령 문자열을 생성합니다.

        인자:
            없음.
        반환값:
            공백으로 결합한 GStreamer 명령 문자열을 반환합니다.
        """

        return " ".join(self.build_command_args())
