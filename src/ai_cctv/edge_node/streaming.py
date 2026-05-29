# Edge node GStreamer 파이프라인 생성 파일입니다.
# Raspberry Pi 카메라 영상을 로컬 백업과 MediaMTX 송출로 분기합니다.
# 실제 프로세스 실행은 runtime.py가 담당하고 이 파일은 명령 생성만 맡습니다.

from dataclasses import dataclass

from .local_backup import LocalBackupConfig


@dataclass(frozen=True)
class EdgeStreamConfig:
    """Edge node 영상 송출 파이프라인 설정을 표현합니다.

    인자:
        width: 송출 영상 너비입니다.
        height: 송출 영상 높이입니다.
        fps: 초당 프레임 수입니다.
        bitrate: x264enc에 전달할 kbps 단위 비트레이트입니다.
        publish_url: 로컬 MediaMTX에 전달할 RTMP publish URL입니다.
    반환값:
        EdgeStreamConfig 인스턴스를 반환합니다.
    """

    width: int = 640
    height: int = 480
    fps: int = 30
    bitrate: int = 500
    publish_url: str = "rtmp://127.0.0.1:1935/live"


class MediaMtxGStreamerCommandBuilder:
    """GStreamer 기반 백업과 MediaMTX 송출 명령을 생성합니다.

    인자:
        config: Edge node 영상 송출 설정입니다.
        backup_config: 로컬 백업 저장 설정입니다.
    반환값:
        MediaMtxGStreamerCommandBuilder 인스턴스를 반환합니다.
    """

    def __init__(self, config=None, backup_config=None):
        """송출 명령 생성 설정을 초기화합니다.

        인자:
            config: Edge node 영상 송출 설정입니다.
            backup_config: 로컬 백업 저장 설정입니다.
        반환값:
            없음.
        """

        self.config = config or EdgeStreamConfig()
        self.backup_config = backup_config or LocalBackupConfig()

    def build_command_args(self):
        """GStreamer 백업 및 송출 명령 인자 목록을 생성합니다.

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
            "-e",
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
            "key-int-max=15",
            "bframes=0",
            "threads=4",
            "sliced-threads=true",
            "!",
            "h264parse",
            "config-interval=1",
            "!",
            "tee",
            "name=t",
            "t.",
            "!",
            "queue",
            "max-size-buffers=150",
            "max-size-time=0",
            "max-size-bytes=0",
            "!",
            "splitmuxsink",
            f"location={self.backup_config.build_segment_pattern()}",
            f"max-size-time={self.backup_config.segment_duration_nanoseconds()}",
            "async-handling=true",
            "t.",
            "!",
            "queue",
            "leaky=downstream",
            "max-size-buffers=60",
            "max-size-time=0",
            "max-size-bytes=0",
            "!",
            "flvmux",
            "streamable=true",
            "!",
            "queue",
            "leaky=downstream",
            "max-size-buffers=60",
            "max-size-time=0",
            "max-size-bytes=0",
            "!",
            "rtmpsink",
            f"location={self.config.publish_url}",
        ]

    def build_shell_command_text(self):
        """운영자가 확인할 수 있는 GStreamer 명령 문자열을 생성합니다.

        인자:
            없음.
        반환값:
            공백으로 결합한 GStreamer 명령 문자열을 반환합니다.
        """

        return " ".join(self.build_command_args())
