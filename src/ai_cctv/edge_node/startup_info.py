# Edge node 시작 시 AI server 설정에 필요한 연결 정보를 만드는 파일입니다.
# 실행자가 지정한 Edge node host를 기준으로 연결 정보를 만듭니다.
# RTSP 수신 주소, MQTT 상태 topic, 백업 복구 API 주소를 한 번에 출력합니다.
# AI_CCTV_EDGE_HOST가 없으면 자동 추정하지 않고 오류를 반환합니다.

from dataclasses import dataclass
import sys

from ..config import get_env_bool, get_env_int, get_env_value
from .monitoring.resource_monitor_publisher import (
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_TOPIC,
)


DEFAULT_RTSP_PORT = 8554
DEFAULT_RTSP_PATH = "live"
DEFAULT_BACKUP_RECOVERY_PORT = 8002
DEFAULT_BACKUP_DIR = "~/backups"


@dataclass(frozen=True)
class EdgeConnectionInfo:
    """Edge node와 AI server 연결에 필요한 값을 보관합니다.

    인자:
        edge_host: AI server가 접근할 Edge node IP 또는 호스트 이름입니다.
        rtsp_url: AI server UI 영상 입력에 사용할 RTSP 주소입니다.
        mqtt_host: Edge 상태 정보를 주고받을 MQTT broker 호스트입니다.
        mqtt_port: MQTT broker 포트입니다.
        mqtt_topic: Edge 상태 JSON이 발행되는 MQTT topic입니다.
        backup_recovery_url: AI server가 누락 구간을 요청할 백업 복구 API 주소입니다.
        backup_dir: Edge node가 로컬 백업 TS 파일을 저장하는 경로입니다.
    반환값:
        EdgeConnectionInfo 인스턴스를 반환합니다.
    """

    edge_host: str
    rtsp_url: str
    mqtt_host: str
    mqtt_port: int
    mqtt_topic: str
    backup_recovery_url: str
    backup_dir: str

    def to_terminal_text(self):
        """터미널에 출력할 표준 연결 정보 블록을 생성합니다.

        인자:
            없음.
        반환값:
            운영자가 복사할 수 있는 여러 줄 문자열을 반환합니다.
        """

        return "\n".join(
            [
                "[AI_CCTV Edge Node Connection]",
                f"EDGE_HOST={self.edge_host}",
                f"RTSP_URL={self.rtsp_url}",
                f"MQTT_BROKER={self.mqtt_host}:{self.mqtt_port}",
                f"MQTT_TOPIC={self.mqtt_topic}",
                f"BACKUP_RECOVERY_URL={self.backup_recovery_url}",
                f"BACKUP_DIR={self.backup_dir}",
                "",
                "[AI server PowerShell]",
                f'$env:AI_CCTV_MQTT_HOST="{self.mqtt_host}"',
                f'$env:AI_CCTV_MQTT_PORT="{self.mqtt_port}"',
                f'$env:AI_CCTV_MQTT_STATUS_TOPIC="{self.mqtt_topic}"',
                f'$env:AI_CCTV_RECOVERY_SERVER_URL="{self.backup_recovery_url}"',
                f'영상 입력 주소: "{self.rtsp_url}"',
                "",
                "[주의]",
                "AI_CCTV_EDGE_HOST에는 AI server가 접근할 수 있는 Edge node 유선 IP를 지정하세요.",
                "MQTT broker는 기본적으로 Edge node에서 실행됩니다.",
                "외부 MQTT broker를 사용할 때만 AI_CCTV_MQTT_HOST를 별도로 지정하세요.",
            ]
        )


def build_edge_connection_info(
    edge_host=None,
    mqtt_host=None,
    mqtt_port=None,
    mqtt_topic=None,
    backup_recovery_port=None,
    backup_dir=None,
):
    """환경 변수와 인자를 합쳐 Edge node 연결 정보를 생성합니다.

    인자:
        edge_host: 자동 감지 대신 사용할 Edge node 호스트입니다.
        mqtt_host: MQTT broker 호스트입니다.
        mqtt_port: MQTT broker 포트입니다.
        mqtt_topic: 상태 JSON 발행 topic입니다.
        backup_recovery_port: 백업 복구 FastAPI 서버 포트입니다.
        backup_dir: 로컬 백업 저장 경로입니다.
    반환값:
        EdgeConnectionInfo 인스턴스를 반환합니다.
    """

    explicit_mqtt_host = mqtt_host or get_env_value("AI_CCTV_MQTT_HOST", "")
    resolved_mqtt_port = _resolve_int(
        mqtt_port,
        "AI_CCTV_MQTT_PORT",
        DEFAULT_MQTT_PORT,
    )
    resolved_topic = mqtt_topic or get_env_value(
        "AI_CCTV_MQTT_STATUS_TOPIC",
        DEFAULT_MQTT_TOPIC,
    )
    resolved_recovery_port = _resolve_int(
        backup_recovery_port,
        "AI_CCTV_BACKUP_RECOVERY_PORT",
        DEFAULT_BACKUP_RECOVERY_PORT,
    )
    resolved_backup_dir = backup_dir or get_env_value("AI_CCTV_BACKUP_DIR", DEFAULT_BACKUP_DIR)
    resolved_edge_host = resolve_edge_host(edge_host, explicit_mqtt_host)
    resolved_mqtt_host = explicit_mqtt_host or resolved_edge_host
    rtsp_url = _build_rtsp_url(resolved_edge_host)
    backup_recovery_url = (
        f"http://{resolved_edge_host}:{resolved_recovery_port}/recover"
    )

    return EdgeConnectionInfo(
        edge_host=resolved_edge_host,
        rtsp_url=rtsp_url,
        mqtt_host=resolved_mqtt_host,
        mqtt_port=resolved_mqtt_port,
        mqtt_topic=resolved_topic,
        backup_recovery_url=backup_recovery_url,
        backup_dir=resolved_backup_dir,
    )


def print_edge_connection_info(connection_info=None, stream=None, **overrides):
    """Edge node 연결 정보를 표준 출력으로 즉시 표시합니다.

    인자:
        connection_info: 이미 생성된 연결 정보 객체입니다.
        stream: 출력 대상 스트림이며 기본값은 표준 출력입니다.
        overrides: build_edge_connection_info에 전달할 선택 인자입니다.
    반환값:
        출력한 EdgeConnectionInfo 인스턴스를 반환합니다.
    """

    output_stream = stream or sys.stdout
    info = connection_info or build_edge_connection_info(**overrides)
    if not _read_bool_env("AI_CCTV_PRINT_STARTUP_INFO", True):
        return info

    print(info.to_terminal_text(), file=output_stream, flush=True)
    return info


def resolve_edge_host(edge_host=None, probe_host=None):
    """AI server가 접속할 Edge node 호스트 값을 결정합니다.

    인자:
        edge_host: 호출자가 명시한 Edge node 호스트입니다.
        probe_host: 현재는 사용하지 않는 예약 인자입니다.
    반환값:
        명시된 IP 또는 호스트 문자열을 반환합니다.
    """

    explicit_host = edge_host or get_env_value("AI_CCTV_EDGE_HOST", "")
    if explicit_host:
        return explicit_host

    raise RuntimeError("AI_CCTV_EDGE_HOST를 .env에 설정하거나 edge_host 인자로 전달해야 합니다.")


def _build_rtsp_url(edge_host):
    """MediaMTX 기본 RTSP 주소를 생성합니다.

    인자:
        edge_host: AI server가 접근할 Edge node 호스트입니다.
    반환값:
        rtsp:// 형식의 문자열을 반환합니다.
    """

    port = _resolve_int(None, "AI_CCTV_RTSP_PORT", DEFAULT_RTSP_PORT)
    path = get_env_value("AI_CCTV_RTSP_PATH", DEFAULT_RTSP_PATH).strip("/")
    return f"rtsp://{edge_host}:{port}/{path}"


def _resolve_int(value, env_name, default):
    """명시값 또는 환경 변수를 정수로 해석합니다.

    인자:
        value: 우선 사용할 값입니다.
        env_name: value가 없을 때 읽을 환경 변수 이름입니다.
        default: 값이 없을 때 사용할 기본 정수입니다.
    반환값:
        정수 값을 반환합니다.
    """

    if value is not None:
        return int(value)
    return get_env_int(env_name, default)


def _read_bool_env(name, default):
    """환경 변수 문자열을 bool 값으로 변환합니다.

    인자:
        name: 읽을 환경 변수 이름입니다.
        default: 환경 변수가 없을 때 사용할 기본값입니다.
    반환값:
        bool 값을 반환합니다.
    """

    return get_env_bool(name, default)


