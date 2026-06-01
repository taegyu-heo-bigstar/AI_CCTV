# Edge node 시작 시 AI server 설정에 필요한 연결 정보를 만드는 파일입니다.
# SSH 접속으로 실행하는 라즈베리 파이의 유선 IP를 우선 추정합니다.
# RTSP 수신 주소, MQTT 상태 topic, 백업 복구 API 주소를 한 번에 출력합니다.
# 자동 감지가 틀리면 AI_CCTV_EDGE_HOST 환경 변수로 값을 고정할 수 있습니다.

from dataclasses import dataclass
import os
import socket
import subprocess
import sys

from .monitoring.resource_monitor_publisher import (
    DEFAULT_MQTT_HOST,
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
                "EDGE_HOST가 127.0.0.1이면 AI_CCTV_EDGE_HOST에 유선 IP를 지정한 뒤 다시 실행하세요.",
                "MQTT broker를 Windows AI server에서 실행한다면 AI_CCTV_MQTT_HOST에 Windows 유선 IP를 지정하세요.",
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

    resolved_mqtt_host = mqtt_host or os.getenv("AI_CCTV_MQTT_HOST", DEFAULT_MQTT_HOST)
    resolved_mqtt_port = _resolve_int(
        mqtt_port,
        "AI_CCTV_MQTT_PORT",
        DEFAULT_MQTT_PORT,
    )
    resolved_topic = mqtt_topic or os.getenv(
        "AI_CCTV_MQTT_STATUS_TOPIC",
        DEFAULT_MQTT_TOPIC,
    )
    resolved_recovery_port = _resolve_int(
        backup_recovery_port,
        "AI_CCTV_BACKUP_RECOVERY_PORT",
        DEFAULT_BACKUP_RECOVERY_PORT,
    )
    resolved_backup_dir = backup_dir or os.getenv("AI_CCTV_BACKUP_DIR", DEFAULT_BACKUP_DIR)
    resolved_edge_host = resolve_edge_host(edge_host, resolved_mqtt_host)
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
        probe_host: UDP 경로 감지에 사용할 상대 호스트입니다.
    반환값:
        감지된 IP 또는 호스트 문자열을 반환합니다.
    """

    explicit_host = edge_host or os.getenv("AI_CCTV_EDGE_HOST")
    if explicit_host:
        return explicit_host

    ssh_host = _read_ssh_server_host()
    if ssh_host:
        return ssh_host

    interface_host = _read_interface_host(os.getenv("AI_CCTV_EDGE_INTERFACE"))
    if interface_host:
        return interface_host

    route_probe_host = probe_host if probe_host and not _is_loopback_host(probe_host) else None
    probed_host = _detect_host_by_udp_probe(route_probe_host or "8.8.8.8")
    if probed_host:
        return probed_host

    hostname_host = _read_hostname_host()
    if hostname_host:
        return hostname_host

    return "127.0.0.1"


def _build_rtsp_url(edge_host):
    """MediaMTX 기본 RTSP 주소를 생성합니다.

    인자:
        edge_host: AI server가 접근할 Edge node 호스트입니다.
    반환값:
        rtsp:// 형식의 문자열을 반환합니다.
    """

    port = _resolve_int(None, "AI_CCTV_RTSP_PORT", DEFAULT_RTSP_PORT)
    path = os.getenv("AI_CCTV_RTSP_PATH", DEFAULT_RTSP_PATH).strip("/")
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
    return int(os.getenv(env_name, default))


def _read_bool_env(name, default):
    """환경 변수 문자열을 bool 값으로 변환합니다.

    인자:
        name: 읽을 환경 변수 이름입니다.
        default: 환경 변수가 없을 때 사용할 기본값입니다.
    반환값:
        bool 값을 반환합니다.
    """

    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _read_ssh_server_host():
    """SSH 접속 환경에서 서버 측 IP를 읽습니다.

    인자:
        없음.
    반환값:
        SSH_CONNECTION의 서버 IP 또는 None을 반환합니다.
    """

    ssh_connection = os.getenv("SSH_CONNECTION", "")
    parts = ssh_connection.split()
    if len(parts) >= 3 and not _is_loopback_host(parts[2]):
        return parts[2]
    return None


def _read_interface_host(interface_name):
    """지정한 네트워크 인터페이스의 IPv4 주소를 조회합니다.

    인자:
        interface_name: 조회할 Linux 네트워크 인터페이스 이름입니다.
    반환값:
        IPv4 주소 문자열 또는 None을 반환합니다.
    """

    if not interface_name:
        return None

    try:
        result = subprocess.run(
            ["ip", "-o", "-4", "addr", "show", "dev", interface_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    for line in result.stdout.splitlines():
        fields = line.split()
        if "inet" in fields:
            address = fields[fields.index("inet") + 1].split("/", 1)[0]
            if not _is_loopback_host(address):
                return address
    return None


def _detect_host_by_udp_probe(probe_host, probe_port=80):
    """UDP 라우팅 결과로 로컬 IPv4 주소를 추정합니다.

    인자:
        probe_host: 라우팅 판단에 사용할 상대 호스트입니다.
        probe_port: 라우팅 판단에 사용할 상대 포트입니다.
    반환값:
        로컬 IPv4 주소 또는 None을 반환합니다.
    """

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect((probe_host, probe_port))
            detected_host = sock.getsockname()[0]
    except OSError:
        return None

    if _is_loopback_host(detected_host):
        return None
    return detected_host


def _read_hostname_host():
    """호스트 이름 해석 결과에서 외부 접속 가능한 IPv4 주소를 찾습니다.

    인자:
        없음.
    반환값:
        IPv4 주소 문자열 또는 None을 반환합니다.
    """

    try:
        host_candidates = socket.getaddrinfo(
            socket.gethostname(),
            None,
            family=socket.AF_INET,
            type=socket.SOCK_STREAM,
        )
    except OSError:
        return None

    for candidate in host_candidates:
        host = candidate[4][0]
        if not _is_loopback_host(host):
            return host
    return None


def _is_loopback_host(host):
    """호스트 값이 loopback 주소인지 판단합니다.

    인자:
        host: 검사할 IP 또는 호스트 이름입니다.
    반환값:
        loopback이면 True, 아니면 False를 반환합니다.
    """

    normalized_host = str(host).strip().lower()
    return normalized_host in {"localhost", "::1"} or normalized_host.startswith("127.")
