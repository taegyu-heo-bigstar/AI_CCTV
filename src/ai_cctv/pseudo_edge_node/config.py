# pseudo Edge node 실행 설정 파일입니다.
# Windows 단일 PC 테스트에서 사용할 RTSP, MQTT, 백업 복구 API 주소를 관리합니다.
# 실제 Edge node 표준 출력과 같은 형식으로 AI server 입력값을 생성합니다.
# 환경 변수와 명령행 인자를 조합해 테스트용 포트와 topic을 바꿀 수 있습니다.

from dataclasses import dataclass
import os


DEFAULT_HOST = "127.0.0.1"
DEFAULT_RTSP_PORT = 8554
DEFAULT_RTSP_PATH = "live"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC = "ai-cctv/edge-node/status"
DEFAULT_BACKUP_RECOVERY_PORT = 8002
DEFAULT_BACKUP_DIR = "./pseudo_backups"
DEFAULT_STATUS_INTERVAL_SECONDS = 2.0
DEFAULT_FRAME_WIDTH = 640
DEFAULT_FRAME_HEIGHT = 480
DEFAULT_FRAME_FPS = 30


@dataclass(frozen=True)
class PseudoEdgeNodeConfig:
    """pseudo Edge node 실행에 필요한 네트워크와 영상 설정을 보관합니다.

    인자:
        host: AI server가 접근할 pseudo Edge node 호스트입니다.
        rtsp_port: RTSP 포트 검증에 사용할 TCP 포트입니다.
        rtsp_path: RTSP URL 경로입니다.
        mqtt_port: 최소 MQTT broker가 사용할 TCP 포트입니다.
        mqtt_topic: Edge node 상태 JSON을 발행할 MQTT topic입니다.
        backup_recovery_port: 백업 복구 HTTP API 포트입니다.
        backup_dir: pseudo 백업 파일을 저장하거나 생성할 폴더입니다.
        status_interval_seconds: 상태 JSON 발행 주기입니다.
        frame_width: AI server synthetic 영상 프레임 너비입니다.
        frame_height: AI server synthetic 영상 프레임 높이입니다.
        frame_fps: AI server synthetic 영상 FPS입니다.
    반환값:
        PseudoEdgeNodeConfig 인스턴스를 반환합니다.
    """

    host: str = DEFAULT_HOST
    rtsp_port: int = DEFAULT_RTSP_PORT
    rtsp_path: str = DEFAULT_RTSP_PATH
    mqtt_port: int = DEFAULT_MQTT_PORT
    mqtt_topic: str = DEFAULT_MQTT_TOPIC
    backup_recovery_port: int = DEFAULT_BACKUP_RECOVERY_PORT
    backup_dir: str = DEFAULT_BACKUP_DIR
    status_interval_seconds: float = DEFAULT_STATUS_INTERVAL_SECONDS
    frame_width: int = DEFAULT_FRAME_WIDTH
    frame_height: int = DEFAULT_FRAME_HEIGHT
    frame_fps: int = DEFAULT_FRAME_FPS

    @classmethod
    def from_environment(cls):
        """환경 변수에서 pseudo Edge node 설정을 생성합니다.

        인자:
            없음.
        반환값:
            환경 변수값이 반영된 PseudoEdgeNodeConfig 인스턴스를 반환합니다.
        """

        return cls(
            host=os.getenv("AI_CCTV_PSEUDO_EDGE_HOST", DEFAULT_HOST),
            rtsp_port=int(os.getenv("AI_CCTV_PSEUDO_RTSP_PORT", DEFAULT_RTSP_PORT)),
            rtsp_path=os.getenv("AI_CCTV_PSEUDO_RTSP_PATH", DEFAULT_RTSP_PATH),
            mqtt_port=int(os.getenv("AI_CCTV_PSEUDO_MQTT_PORT", DEFAULT_MQTT_PORT)),
            mqtt_topic=os.getenv(
                "AI_CCTV_PSEUDO_MQTT_TOPIC",
                DEFAULT_MQTT_TOPIC,
            ),
            backup_recovery_port=int(
                os.getenv(
                    "AI_CCTV_PSEUDO_BACKUP_RECOVERY_PORT",
                    DEFAULT_BACKUP_RECOVERY_PORT,
                )
            ),
            backup_dir=os.getenv("AI_CCTV_PSEUDO_BACKUP_DIR", DEFAULT_BACKUP_DIR),
            status_interval_seconds=float(
                os.getenv(
                    "AI_CCTV_PSEUDO_STATUS_INTERVAL_SECONDS",
                    DEFAULT_STATUS_INTERVAL_SECONDS,
                )
            ),
            frame_width=int(
                os.getenv("AI_CCTV_PSEUDO_FRAME_WIDTH", DEFAULT_FRAME_WIDTH)
            ),
            frame_height=int(
                os.getenv("AI_CCTV_PSEUDO_FRAME_HEIGHT", DEFAULT_FRAME_HEIGHT)
            ),
            frame_fps=int(os.getenv("AI_CCTV_PSEUDO_FRAME_FPS", DEFAULT_FRAME_FPS)),
        )

    @property
    def rtsp_url(self):
        """AI server 영상 입력에 사용할 RTSP URL을 반환합니다.

        인자:
            없음.
        반환값:
            rtsp:// 형식의 pseudo RTSP URL 문자열을 반환합니다.
        """

        return f"rtsp://{self.host}:{self.rtsp_port}/{self.rtsp_path.strip('/')}"

    @property
    def mqtt_broker_text(self):
        """표준 출력에 표시할 MQTT broker 주소를 반환합니다.

        인자:
            없음.
        반환값:
            host:port 형식의 MQTT broker 문자열을 반환합니다.
        """

        return f"{self.host}:{self.mqtt_port}"

    @property
    def backup_recovery_url(self):
        """AI server 백업 복구 요청에 사용할 HTTP URL을 반환합니다.

        인자:
            없음.
        반환값:
            /recover endpoint를 포함한 HTTP URL 문자열을 반환합니다.
        """

        return f"http://{self.host}:{self.backup_recovery_port}/recover"

    def to_terminal_text(self):
        """AI server 시작 UI에 붙여넣을 연결 정보 블록을 생성합니다.

        인자:
            없음.
        반환값:
            pseudo Edge node 연결 정보와 PowerShell 환경 변수 예시 문자열을 반환합니다.
        """

        return "\n".join(
            [
                "[AI_CCTV Pseudo Edge Node Connection]",
                "PSEUDO_EDGE=1",
                f"EDGE_HOST={self.host}",
                f"RTSP_URL={self.rtsp_url}",
                f"MQTT_BROKER={self.mqtt_broker_text}",
                f"MQTT_TOPIC={self.mqtt_topic}",
                f"BACKUP_RECOVERY_URL={self.backup_recovery_url}",
                f"BACKUP_DIR={self.backup_dir}",
                "",
                "[AI server PowerShell]",
                '$env:AI_CCTV_USE_PSEUDO_EDGE="1"',
                f'$env:AI_CCTV_RTSP_URL="{self.rtsp_url}"',
                f'$env:AI_CCTV_MQTT_HOST="{self.host}"',
                f'$env:AI_CCTV_MQTT_PORT="{self.mqtt_port}"',
                f'$env:AI_CCTV_MQTT_STATUS_TOPIC="{self.mqtt_topic}"',
                f'$env:AI_CCTV_RECOVERY_SERVER_URL="{self.backup_recovery_url}"',
                f'$env:AI_CCTV_PSEUDO_FRAME_WIDTH="{self.frame_width}"',
                f'$env:AI_CCTV_PSEUDO_FRAME_HEIGHT="{self.frame_height}"',
                f'$env:AI_CCTV_PSEUDO_FRAME_FPS="{self.frame_fps}"',
                "",
                "[주의]",
                "이 실행체는 Windows 테스트용이며 실제 Raspberry Pi 카메라 품질이나 GStreamer 송출을 검증하지 않습니다.",
            ]
        )


def merge_config_with_overrides(base_config, **overrides):
    """기본 설정과 명령행 override 값을 합쳐 새 설정을 생성합니다.

    인자:
        base_config: 기준으로 사용할 PseudoEdgeNodeConfig 인스턴스입니다.
        overrides: None이 아닌 값만 반영할 설정 필드입니다.
    반환값:
        override가 반영된 PseudoEdgeNodeConfig 인스턴스를 반환합니다.
    """

    values = base_config.__dict__.copy()
    values.update({key: value for key, value in overrides.items() if value is not None})
    return PseudoEdgeNodeConfig(**values)
