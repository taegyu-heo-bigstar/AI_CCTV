# AI server 시작 전 Edge node 연결 설정을 검증하는 파일입니다.
# Edge node 표준 출력값을 UI 입력값으로 변환하고 환경 변수에 반영합니다.
# RTSP, MQTT, 백업 복구 API의 최소 연결 가능 여부를 확인합니다.
# 실제 영상 분석은 연결 검증이 성공한 뒤 기존 메인 창에서 시작합니다.

from dataclasses import dataclass
import os
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from ..analysis.rtsp_receiver import check_rtsp_port_open, is_rtsp_source
from ..monitoring.resource_monitor_client import (
    DEFAULT_MQTT_HOST,
    DEFAULT_MQTT_PORT,
    DEFAULT_MQTT_TOPIC,
)


DEFAULT_RTSP_URL = "rtsp://127.0.0.1:8554/live"
DEFAULT_BACKUP_RECOVERY_URL = "http://127.0.0.1:8002/recover"


@dataclass(frozen=True)
class EdgeConnectionConfig:
    """AI server가 Edge node에 접속하는 데 필요한 설정을 보관합니다.

    인자:
        rtsp_url: 영상 수신에 사용할 Edge node RTSP URL입니다.
        mqtt_host: Edge node 상태를 수신할 MQTT broker 호스트입니다.
        mqtt_port: MQTT broker 포트입니다.
        mqtt_topic: Edge node 상태 JSON을 구독할 MQTT topic입니다.
        backup_recovery_url: 누락 구간 복구 요청을 보낼 Edge node HTTP URL입니다.
    반환값:
        EdgeConnectionConfig 인스턴스를 반환합니다.
    """

    rtsp_url: str = DEFAULT_RTSP_URL
    mqtt_host: str = DEFAULT_MQTT_HOST
    mqtt_port: int = DEFAULT_MQTT_PORT
    mqtt_topic: str = DEFAULT_MQTT_TOPIC
    backup_recovery_url: str = DEFAULT_BACKUP_RECOVERY_URL

    @classmethod
    def from_environment(cls):
        """환경 변수에서 AI server 연결 설정을 생성합니다.

        인자:
            없음.
        반환값:
            EdgeConnectionConfig 인스턴스를 반환합니다.
        """

        return cls(
            rtsp_url=os.getenv("AI_CCTV_RTSP_URL", DEFAULT_RTSP_URL),
            mqtt_host=os.getenv("AI_CCTV_MQTT_HOST", DEFAULT_MQTT_HOST),
            mqtt_port=int(os.getenv("AI_CCTV_MQTT_PORT", DEFAULT_MQTT_PORT)),
            mqtt_topic=os.getenv("AI_CCTV_MQTT_STATUS_TOPIC", DEFAULT_MQTT_TOPIC),
            backup_recovery_url=os.getenv(
                "AI_CCTV_RECOVERY_SERVER_URL",
                DEFAULT_BACKUP_RECOVERY_URL,
            ),
        )

    def apply_environment(self):
        """현재 연결 설정을 기존 AI server 코드가 읽는 환경 변수에 반영합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        os.environ["AI_CCTV_RTSP_URL"] = self.rtsp_url
        os.environ["AI_CCTV_MQTT_HOST"] = self.mqtt_host
        os.environ["AI_CCTV_MQTT_PORT"] = str(self.mqtt_port)
        os.environ["AI_CCTV_MQTT_STATUS_TOPIC"] = self.mqtt_topic
        os.environ["AI_CCTV_RECOVERY_SERVER_URL"] = self.backup_recovery_url


@dataclass(frozen=True)
class EdgeConnectionValidationResult:
    """Edge node 연결 검증 결과를 표현합니다.

    인자:
        success: 모든 필수 연결 검증이 성공했는지 여부입니다.
        errors: 실패한 검증 항목의 메시지 목록입니다.
    반환값:
        EdgeConnectionValidationResult 인스턴스를 반환합니다.
    """

    success: bool
    errors: tuple[str, ...] = ()

    def message(self):
        """검증 결과를 화면 표시용 문자열로 변환합니다.

        인자:
            없음.
        반환값:
            성공 또는 실패 사유 문자열을 반환합니다.
        """

        if self.success:
            return "Edge node 연결 검증에 성공했습니다."
        return "\n".join(self.errors)


class EdgeConnectionValidator:
    """RTSP, MQTT, 백업 복구 API의 접속 가능 여부를 검증합니다.

    인자:
        rtsp_timeout_seconds: RTSP TCP 포트 확인 제한 시간입니다.
        mqtt_timeout_seconds: MQTT broker TCP 확인 제한 시간입니다.
        http_timeout_seconds: 백업 복구 HTTP 확인 제한 시간입니다.
    반환값:
        EdgeConnectionValidator 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        rtsp_timeout_seconds=1.5,
        mqtt_timeout_seconds=1.5,
        http_timeout_seconds=2.0,
    ):
        """연결 검증 제한 시간을 초기화합니다.

        인자:
            rtsp_timeout_seconds: RTSP TCP 포트 확인 제한 시간입니다.
            mqtt_timeout_seconds: MQTT broker TCP 확인 제한 시간입니다.
            http_timeout_seconds: 백업 복구 HTTP 확인 제한 시간입니다.
        반환값:
            없음.
        """

        self.rtsp_timeout_seconds = rtsp_timeout_seconds
        self.mqtt_timeout_seconds = mqtt_timeout_seconds
        self.http_timeout_seconds = http_timeout_seconds

    def validate(self, config):
        """Edge node 연결 설정의 필수 접속 가능 여부를 검증합니다.

        인자:
            config: 검증할 EdgeConnectionConfig 인스턴스입니다.
        반환값:
            EdgeConnectionValidationResult 인스턴스를 반환합니다.
        """

        errors = []
        errors.extend(self._validate_rtsp(config.rtsp_url))
        errors.extend(self._validate_mqtt(config.mqtt_host, config.mqtt_port))
        errors.extend(self._validate_backup_recovery(config.backup_recovery_url))
        return EdgeConnectionValidationResult(
            success=not errors,
            errors=tuple(errors),
        )

    def _validate_rtsp(self, rtsp_url):
        """RTSP URL 형식과 TCP 포트 접근 가능 여부를 검증합니다.

        인자:
            rtsp_url: 확인할 RTSP URL입니다.
        반환값:
            오류 메시지 목록을 반환합니다.
        """

        if not is_rtsp_source(rtsp_url):
            return ["RTSP_URL은 rtsp:// 형식이어야 합니다."]

        if check_rtsp_port_open(rtsp_url, timeout_seconds=self.rtsp_timeout_seconds):
            return []
        return [f"RTSP 포트에 연결할 수 없습니다: {rtsp_url}"]

    def _validate_mqtt(self, mqtt_host, mqtt_port):
        """MQTT broker TCP 포트 접근 가능 여부를 검증합니다.

        인자:
            mqtt_host: MQTT broker 호스트입니다.
            mqtt_port: MQTT broker 포트입니다.
        반환값:
            오류 메시지 목록을 반환합니다.
        """

        if not mqtt_host:
            return ["MQTT broker 호스트가 비어 있습니다."]

        try:
            with socket.create_connection(
                (mqtt_host, int(mqtt_port)),
                timeout=self.mqtt_timeout_seconds,
            ):
                return []
        except OSError as error:
            return [f"MQTT broker에 연결할 수 없습니다: {mqtt_host}:{mqtt_port} ({error})"]

    def _validate_backup_recovery(self, backup_recovery_url):
        """백업 복구 HTTP endpoint 접근 가능 여부를 검증합니다.

        인자:
            backup_recovery_url: 확인할 백업 복구 API URL입니다.
        반환값:
            오류 메시지 목록을 반환합니다.
        """

        parsed_url = urlparse(backup_recovery_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            return ["BACKUP_RECOVERY_URL은 http:// 또는 https:// 형식이어야 합니다."]

        request = Request(backup_recovery_url, method="GET")
        try:
            with urlopen(request, timeout=self.http_timeout_seconds) as response:
                if response.status < 500:
                    return []
                return [f"백업 복구 서버가 오류 응답을 반환했습니다: HTTP {response.status}"]
        except HTTPError as error:
            if error.code < 500:
                return []
            return [f"백업 복구 서버가 오류 응답을 반환했습니다: HTTP {error.code}"]
        except (OSError, URLError, TimeoutError) as error:
            return [f"백업 복구 API에 연결할 수 없습니다: {backup_recovery_url} ({error})"]


def parse_edge_startup_text(text, base_config=None):
    """Edge node 표준 출력 블록에서 AI server 연결 설정을 추출합니다.

    인자:
        text: Edge node 터미널에 출력된 연결 정보 문자열입니다.
        base_config: 누락된 값을 채울 기본 연결 설정입니다.
    반환값:
        EdgeConnectionConfig 인스턴스를 반환합니다.
    """

    values = _parse_key_value_lines(text)
    fallback = base_config or EdgeConnectionConfig.from_environment()
    mqtt_host = values.get("AI_CCTV_MQTT_HOST", fallback.mqtt_host)
    mqtt_port = values.get("AI_CCTV_MQTT_PORT", str(fallback.mqtt_port))
    if "MQTT_BROKER" in values:
        mqtt_host, mqtt_port = _split_host_port(values["MQTT_BROKER"], mqtt_host, mqtt_port)

    return EdgeConnectionConfig(
        rtsp_url=values.get("RTSP_URL", fallback.rtsp_url),
        mqtt_host=mqtt_host,
        mqtt_port=int(mqtt_port),
        mqtt_topic=values.get(
            "MQTT_TOPIC",
            values.get("AI_CCTV_MQTT_STATUS_TOPIC", fallback.mqtt_topic),
        ),
        backup_recovery_url=values.get(
            "BACKUP_RECOVERY_URL",
            values.get("AI_CCTV_RECOVERY_SERVER_URL", fallback.backup_recovery_url),
        ),
    )


def _parse_key_value_lines(text):
    """여러 줄 문자열에서 KEY=VALUE 형식의 값을 추출합니다.

    인자:
        text: 분석할 여러 줄 문자열입니다.
    반환값:
        key와 value를 담은 딕셔너리를 반환합니다.
    """

    values = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = _normalize_key(key)
        if not key:
            continue
        values[key] = value.strip().strip('"')
    return values


def _normalize_key(key):
    """환경 변수 또는 출력 항목 이름을 내부 키로 정규화합니다.

    인자:
        key: 원본 key 문자열입니다.
    반환값:
        정규화된 key 문자열을 반환합니다.
    """

    return key.strip().replace("$env:", "").replace("$Env:", "")


def _split_host_port(value, default_host, default_port):
    """host:port 문자열을 호스트와 포트로 분리합니다.

    인자:
        value: MQTT_BROKER 출력 문자열입니다.
        default_host: 분리 실패 시 사용할 호스트입니다.
        default_port: 분리 실패 시 사용할 포트입니다.
    반환값:
        호스트와 포트 문자열 튜플을 반환합니다.
    """

    if ":" not in value:
        return value or default_host, default_port
    host, port = value.rsplit(":", 1)
    return host or default_host, port or default_port
