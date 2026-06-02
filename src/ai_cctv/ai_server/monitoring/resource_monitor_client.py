# Edge node 자원 모니터링 MQTT 구독 클라이언트 파일입니다.
# Edge node가 MQTT topic으로 발행한 상태 JSON을 AI server에서 수신합니다.
# broker 주소와 topic은 AI_CCTV_MQTT_* 환경 변수로 바꿀 수 있습니다.
# UI와 진단 도구는 최신 수신 메시지를 기존 딕셔너리 형태로 사용할 수 있습니다.

"""Edge node 자원 모니터링 MQTT 구독 클라이언트입니다."""

from dataclasses import dataclass
import copy
import json
import threading
import time

from ...config import get_env_float, get_env_int, get_env_value


DEFAULT_MQTT_HOST = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC = "ai-cctv/edge-node/status"
DEFAULT_TIMEOUT_SECONDS = 5.0
DEFAULT_STALE_SECONDS = 6.0
DEFAULT_CLIENT_ID = "ai-cctv-ai-server-monitor"


@dataclass(frozen=True)
class MqttResourceMonitorConfig:
    """MQTT 기반 Edge node 상태 수신 설정을 표현합니다.

    인자:
        broker_host: MQTT broker 호스트입니다.
        broker_port: MQTT broker 포트입니다.
        topic: Edge node 상태 JSON을 구독할 MQTT topic입니다.
        timeout_seconds: 최신 메시지를 기다릴 최대 시간입니다.
        stale_seconds: 수신 메시지를 최신으로 인정할 시간입니다.
        client_id: AI server MQTT 클라이언트 ID입니다.
    반환값:
        MqttResourceMonitorConfig 인스턴스를 반환합니다.
    """

    broker_host: str = DEFAULT_MQTT_HOST
    broker_port: int = DEFAULT_MQTT_PORT
    topic: str = DEFAULT_MQTT_TOPIC
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    stale_seconds: float = DEFAULT_STALE_SECONDS
    client_id: str = DEFAULT_CLIENT_ID

    @classmethod
    def from_environment(cls):
        """환경 변수에서 MQTT 상태 수신 설정을 생성합니다.

        인자:
            없음.
        반환값:
            MqttResourceMonitorConfig 인스턴스를 반환합니다.
        """

        return cls(
            broker_host=get_env_value("AI_CCTV_MQTT_HOST", DEFAULT_MQTT_HOST),
            broker_port=get_env_int("AI_CCTV_MQTT_PORT", DEFAULT_MQTT_PORT),
            topic=get_env_value("AI_CCTV_MQTT_STATUS_TOPIC", DEFAULT_MQTT_TOPIC),
            timeout_seconds=get_env_float(
                "AI_CCTV_MQTT_STATUS_TIMEOUT_SECONDS",
                DEFAULT_TIMEOUT_SECONDS,
            ),
            stale_seconds=get_env_float(
                "AI_CCTV_MQTT_STATUS_STALE_SECONDS",
                DEFAULT_STALE_SECONDS,
            ),
            client_id=get_env_value("AI_CCTV_MQTT_AI_CLIENT_ID", DEFAULT_CLIENT_ID),
        )


class ResourceMonitorClient:
    """MQTT topic에서 Edge node 자원 상태 JSON을 수신합니다.

    인자:
        config: MQTT broker 접속과 구독 설정입니다.
    반환값:
        ResourceMonitorClient 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """MQTT 수신 클라이언트 상태를 초기화합니다.

        인자:
            config: MQTT broker 접속과 구독 설정입니다.
        반환값:
            없음.
        """

        self.config = config if config is not None else MqttResourceMonitorConfig()
        self.mqtt_client = _create_mqtt_client(self.config.client_id)
        self.mqtt_client.on_connect = self._handle_connect
        self.mqtt_client.on_message = self._handle_message
        self.latest_resource_usage = None
        self.latest_received_at = 0.0
        self.last_error = None
        self.is_started = False
        self._lock = threading.Lock()
        self._message_event = threading.Event()

    def matches_config(self, config):
        """현재 클라이언트가 지정한 설정과 같은 broker/topic을 쓰는지 확인합니다.

        인자:
            config: 비교할 MQTT 상태 수신 설정입니다.
        반환값:
            설정이 같으면 True, 아니면 False를 반환합니다.
        """

        return self.config == config

    def start(self):
        """MQTT broker에 접속하고 상태 topic 구독을 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.is_started:
            return

        self.mqtt_client.connect(
            self.config.broker_host,
            self.config.broker_port,
            keepalive=60,
        )
        self.mqtt_client.loop_start()
        self.is_started = True

    def request_resource_usage(self):
        """최신 Edge node 자원 상태 JSON을 반환합니다.

        인자:
            없음.
        반환값:
            Edge node가 MQTT로 발행한 자원 상태 딕셔너리를 반환합니다.
        """

        self.start()
        cached_resource_usage = self._get_fresh_resource_usage()
        if cached_resource_usage is not None:
            return cached_resource_usage

        self._message_event.clear()
        cached_resource_usage = self._get_fresh_resource_usage()
        if cached_resource_usage is not None:
            return cached_resource_usage

        if not self._message_event.wait(timeout=self.config.timeout_seconds):
            message = self.last_error or "MQTT 상태 메시지 수신 대기 시간이 초과되었습니다."
            raise RuntimeError(message)

        if self.last_error is not None:
            raise RuntimeError(self.last_error)

        cached_resource_usage = self._get_fresh_resource_usage()
        if cached_resource_usage is None:
            message = self.last_error or "MQTT 상태 메시지가 최신 상태가 아닙니다."
            raise RuntimeError(message)
        return cached_resource_usage

    def stop(self):
        """MQTT 구독 루프와 broker 연결을 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if not self.is_started:
            return
        try:
            self.mqtt_client.loop_stop()
        finally:
            self.mqtt_client.disconnect()
            self.is_started = False

    def _handle_connect(self, client, _userdata, _flags, reason_code, _properties=None):
        """MQTT 연결 완료 시 상태 topic을 구독합니다.

        인자:
            client: 연결된 MQTT 클라이언트입니다.
            _userdata: paho-mqtt 사용자 데이터입니다.
            _flags: 연결 플래그입니다.
            reason_code: 연결 결과 코드입니다.
            _properties: MQTT v5 연결 속성입니다.
        반환값:
            없음.
        """

        status_code = _to_int_reason_code(reason_code)
        if status_code != 0:
            self.last_error = f"MQTT broker 연결 실패: {reason_code}"
            self._message_event.set()
            return
        self.last_error = None
        client.subscribe(self.config.topic)

    def _handle_message(self, _client, _userdata, message):
        """MQTT 상태 메시지를 JSON 딕셔너리로 변환해 보관합니다.

        인자:
            _client: 메시지를 수신한 MQTT 클라이언트입니다.
            _userdata: paho-mqtt 사용자 데이터입니다.
            message: 수신한 MQTT 메시지입니다.
        반환값:
            없음.
        """

        try:
            payload_text = message.payload.decode("utf-8")
            resource_usage = json.loads(payload_text)
        except Exception as error:
            self.last_error = f"MQTT 상태 메시지 해석 실패: {error}"
            self._message_event.set()
            return

        with self._lock:
            self.latest_resource_usage = resource_usage
            self.latest_received_at = time.monotonic()
            self.last_error = None
        self._message_event.set()

    def _get_fresh_resource_usage(self):
        """보관 중인 최신 상태가 유효하면 복사본을 반환합니다.

        인자:
            없음.
        반환값:
            최신 자원 상태 딕셔너리 또는 None을 반환합니다.
        """

        with self._lock:
            if self.latest_resource_usage is None:
                return None
            age_seconds = time.monotonic() - self.latest_received_at
            if age_seconds > self.config.stale_seconds:
                return None
            return copy.deepcopy(self.latest_resource_usage)


_monitor_client = None


def build_monitor_client():
    """환경 변수 기준으로 공유 MQTT 모니터링 클라이언트를 생성합니다.

    인자:
        없음.
    반환값:
        ResourceMonitorClient 인스턴스를 반환합니다.
    """

    global _monitor_client
    config = MqttResourceMonitorConfig.from_environment()
    if _monitor_client is None or not _monitor_client.matches_config(config):
        if _monitor_client is not None:
            _monitor_client.stop()
        _monitor_client = ResourceMonitorClient(config=config)
    return _monitor_client


def request_resource_usage():
    """공유 MQTT 클라이언트에서 최신 Edge node 자원 상태를 반환합니다.

    인자:
        없음.
    반환값:
        Edge node가 MQTT로 발행한 자원 상태 딕셔너리를 반환합니다.
    """

    return build_monitor_client().request_resource_usage()


def stop_monitor_client():
    """공유 MQTT 모니터링 클라이언트 연결을 종료합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    global _monitor_client
    if _monitor_client is not None:
        _monitor_client.stop()
        _monitor_client = None


def print_resource_usage(resource_usage):
    """자원 사용률 응답을 콘솔에 JSON 형태로 출력합니다.

    인자:
        resource_usage: Edge node가 MQTT로 발행한 자원 사용률 딕셔너리입니다.
    반환값:
        없음.
    """

    print(json.dumps(resource_usage, ensure_ascii=False, indent=2))


def _create_mqtt_client(client_id):
    """설치된 paho-mqtt 버전에 맞는 MQTT 클라이언트를 생성합니다.

    인자:
        client_id: MQTT broker에 전달할 클라이언트 ID입니다.
    반환값:
        paho.mqtt.client.Client 인스턴스를 반환합니다.
    """

    import paho.mqtt.client as mqtt

    try:
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
        )
    except (AttributeError, TypeError):
        return mqtt.Client(client_id=client_id)


def _to_int_reason_code(reason_code):
    """paho-mqtt 연결 결과 코드를 정수로 변환합니다.

    인자:
        reason_code: MQTT 연결 결과 코드입니다.
    반환값:
        정수 형태의 연결 결과 코드를 반환합니다.
    """

    if hasattr(reason_code, "value"):
        return int(reason_code.value)
    return int(reason_code)


def main():
    """Edge node MQTT 상태 메시지를 한 번 수신해 콘솔에 출력합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    try:
        print_resource_usage(request_resource_usage())
    finally:
        stop_monitor_client()


if __name__ == "__main__":
    main()
