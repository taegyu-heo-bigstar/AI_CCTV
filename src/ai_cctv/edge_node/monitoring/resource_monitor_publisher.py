# Edge node 자원 상태 MQTT 발행 파일입니다.
# Edge node의 CPU, 메모리, 프로세스, UPS 전원 상태를 주기적으로 수집합니다.
# 수집한 상태 JSON은 MQTT broker의 상태 topic으로 publish합니다.
# AI server는 같은 topic을 subscribe해 최신 Edge node 상태를 UI에 표시합니다.

"""Edge node 자원 상태 MQTT 발행 모듈입니다."""

from dataclasses import dataclass
from datetime import datetime
import json
import os
import time

from .power_status import CachedPowerStatusProvider


DEFAULT_MQTT_HOST = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC = "ai-cctv/edge-node/status"
DEFAULT_PUBLISH_INTERVAL_SECONDS = 2.0
DEFAULT_MQTT_QOS = 0
DEFAULT_MQTT_RETAIN = True
DEFAULT_CLIENT_ID = "ai-cctv-edge-monitor"


@dataclass(frozen=True)
class MqttResourceMonitorConfig:
    """MQTT 기반 Edge node 상태 발행 설정을 표현합니다.

    인자:
        broker_host: MQTT broker 호스트입니다.
        broker_port: MQTT broker 포트입니다.
        topic: 상태 JSON을 발행할 MQTT topic입니다.
        publish_interval_seconds: 상태 발행 주기입니다.
        qos: MQTT publish QoS 값입니다.
        retain: broker가 마지막 상태 메시지를 보관할지 여부입니다.
        client_id: Edge node MQTT 클라이언트 ID입니다.
    반환값:
        MqttResourceMonitorConfig 인스턴스를 반환합니다.
    """

    broker_host: str = DEFAULT_MQTT_HOST
    broker_port: int = DEFAULT_MQTT_PORT
    topic: str = DEFAULT_MQTT_TOPIC
    publish_interval_seconds: float = DEFAULT_PUBLISH_INTERVAL_SECONDS
    qos: int = DEFAULT_MQTT_QOS
    retain: bool = DEFAULT_MQTT_RETAIN
    client_id: str = DEFAULT_CLIENT_ID

    @classmethod
    def from_environment(cls):
        """환경 변수에서 MQTT 상태 발행 설정을 생성합니다.

        인자:
            없음.
        반환값:
            MqttResourceMonitorConfig 인스턴스를 반환합니다.
        """

        return cls(
            broker_host=os.getenv("AI_CCTV_MQTT_HOST", DEFAULT_MQTT_HOST),
            broker_port=int(os.getenv("AI_CCTV_MQTT_PORT", DEFAULT_MQTT_PORT)),
            topic=os.getenv("AI_CCTV_MQTT_STATUS_TOPIC", DEFAULT_MQTT_TOPIC),
            publish_interval_seconds=float(
                os.getenv(
                    "AI_CCTV_MQTT_STATUS_INTERVAL_SECONDS",
                    DEFAULT_PUBLISH_INTERVAL_SECONDS,
                )
            ),
            qos=int(os.getenv("AI_CCTV_MQTT_QOS", DEFAULT_MQTT_QOS)),
            retain=_read_bool_env("AI_CCTV_MQTT_RETAIN", DEFAULT_MQTT_RETAIN),
            client_id=os.getenv("AI_CCTV_MQTT_EDGE_CLIENT_ID", DEFAULT_CLIENT_ID),
        )


class ResourceUsageCollector:
    """Edge node와 특정 프로세스의 자원 사용률을 수집합니다.

    인자:
        process_id: 모니터링할 프로세스 ID입니다.
        sample_interval_seconds: CPU 사용률 샘플링 시간입니다.
        power_status_provider: UPS Plus 전원 상태를 제공하는 객체입니다.
    반환값:
        ResourceUsageCollector 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        process_id=None,
        sample_interval_seconds=0.1,
        power_status_provider=None,
    ):
        """자원 사용률 수집 대상을 초기화합니다.

        인자:
            process_id: 모니터링할 프로세스 ID이며 없으면 현재 프로세스입니다.
            sample_interval_seconds: CPU 사용률을 계산할 샘플링 시간입니다.
            power_status_provider: UPS Plus 전원 상태를 제공하는 객체입니다.
        반환값:
            없음.
        """

        self.process_id = process_id if process_id is not None else os.getpid()
        self.sample_interval_seconds = sample_interval_seconds
        self.power_status_provider = (
            power_status_provider
            if power_status_provider is not None
            else CachedPowerStatusProvider()
        )

    def collect(self):
        """전체 시스템과 대상 프로세스의 자원 사용률을 수집합니다.

        인자:
            없음.
        반환값:
            CPU, 메모리, 프로세스, UPS 전원 상태 딕셔너리를 반환합니다.
        """

        psutil_module = _load_psutil_module()
        process = self._get_process()
        return {
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "cpu": {
                "total_percent": psutil_module.cpu_percent(
                    interval=self.sample_interval_seconds
                ),
            },
            "memory": {
                "total_percent": psutil_module.virtual_memory().percent,
            },
            "process": {
                "pid": self.process_id,
                "name": process.name(),
                "cpu_percent": process.cpu_percent(
                    interval=self.sample_interval_seconds
                ),
                "memory_percent": process.memory_percent(),
            },
            "power": self.power_status_provider.get_snapshot().to_dict(),
        }

    def _get_process(self):
        """모니터링 대상 프로세스 객체를 반환합니다.

        인자:
            없음.
        반환값:
            psutil.Process 객체를 반환합니다.
        """

        psutil_module = _load_psutil_module()
        try:
            return psutil_module.Process(self.process_id)
        except psutil_module.NoSuchProcess as error:
            raise RuntimeError(f"프로세스를 찾을 수 없습니다: {self.process_id}") from error
        except psutil_module.AccessDenied as error:
            raise RuntimeError(f"프로세스 접근 권한이 없습니다: {self.process_id}") from error


class MqttResourceMonitorPublisher:
    """Edge node 자원 상태를 MQTT broker로 주기 발행합니다.

    인자:
        config: MQTT 접속과 발행 설정입니다.
        collector: 자원 상태를 수집하는 객체입니다.
    반환값:
        MqttResourceMonitorPublisher 인스턴스를 반환합니다.
    """

    def __init__(self, config=None, collector=None):
        """MQTT 발행자 상태와 의존 객체를 초기화합니다.

        인자:
            config: MQTT 접속과 발행 설정입니다.
            collector: 자원 상태를 수집하는 객체입니다.
        반환값:
            없음.
        """

        self.config = config if config is not None else MqttResourceMonitorConfig()
        self.collector = collector if collector is not None else ResourceUsageCollector()
        self.mqtt_client = _create_mqtt_client(self.config.client_id)
        self.is_running = False

    def publish_once(self):
        """자원 상태를 한 번 수집해 MQTT topic으로 발행합니다.

        인자:
            없음.
        반환값:
            발행한 자원 상태 딕셔너리를 반환합니다.
        """

        resource_usage = self.collector.collect()
        payload = json.dumps(resource_usage, ensure_ascii=False)
        publish_info = self.mqtt_client.publish(
            self.config.topic,
            payload,
            qos=self.config.qos,
            retain=self.config.retain,
        )
        publish_info.wait_for_publish(timeout=5)
        return resource_usage

    def run_forever(self):
        """MQTT broker에 접속한 뒤 설정 주기마다 상태를 발행합니다.

        인자:
            없음.
        반환값:
            정상적으로는 반환하지 않습니다.
        """

        self.is_running = True
        self.mqtt_client.connect(
            self.config.broker_host,
            self.config.broker_port,
            keepalive=60,
        )
        self.mqtt_client.loop_start()
        try:
            while self.is_running:
                self.publish_once()
                time.sleep(self.config.publish_interval_seconds)
        finally:
            self.stop()

    def stop(self):
        """MQTT 발행 루프와 broker 연결을 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.is_running = False
        try:
            self.mqtt_client.loop_stop()
        finally:
            self.mqtt_client.disconnect()


def build_resource_usage_collector_from_environment():
    """환경 변수 기준으로 자원 상태 수집기를 생성합니다.

    인자:
        없음.
    반환값:
        ResourceUsageCollector 인스턴스를 반환합니다.
    """

    process_id_text = os.getenv("AI_CCTV_MONITOR_PROCESS_ID")
    process_id = int(process_id_text) if process_id_text else None
    return ResourceUsageCollector(process_id=process_id)


def build_resource_monitor_publisher():
    """환경 변수 기준으로 MQTT 자원 상태 발행자를 생성합니다.

    인자:
        없음.
    반환값:
        MqttResourceMonitorPublisher 인스턴스를 반환합니다.
    """

    return MqttResourceMonitorPublisher(
        config=MqttResourceMonitorConfig.from_environment(),
        collector=build_resource_usage_collector_from_environment(),
    )


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


def _load_psutil_module():
    """설치된 psutil 모듈을 지연 import로 반환합니다.

    인자:
        없음.
    반환값:
        psutil 모듈을 반환합니다.
    """

    import psutil

    return psutil


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


def main():
    """Edge node 자원 상태 MQTT 발행 루프를 실행합니다.

    인자:
        없음.
    반환값:
        정상적으로는 반환하지 않습니다.
    """

    from ..os_guard import ensure_supported_edge_os
    from ..startup_info import print_edge_connection_info

    ensure_supported_edge_os()
    publisher = build_resource_monitor_publisher()
    print_edge_connection_info(
        mqtt_host=publisher.config.broker_host,
        mqtt_port=publisher.config.broker_port,
        mqtt_topic=publisher.config.topic,
    )
    try:
        publisher.run_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
