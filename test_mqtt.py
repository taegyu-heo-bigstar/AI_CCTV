# Edge node 상태 조회 UI를 임시 검증하기 위한 모의 MQTT publisher 파일입니다.
# 실제 Raspberry Pi 없이 상태 JSON을 MQTT broker로 주기 발행합니다.
# AI server UI의 엣지 노드 상태 조회 창은 같은 topic을 구독해 값을 표시합니다.
# 표와 꺾은선 그래프가 변하는지 확인할 수 있도록 사용률과 배터리 값을 바꿉니다.
# 10번 정상 발행한 뒤에는 일부러 발행을 멈춰 연결 실패 UI를 확인합니다.

"""Edge node 모니터링 MQTT 모의 publisher입니다."""

import argparse
from datetime import datetime
import json
import math
import os
import time


DEFAULT_MQTT_HOST = "127.0.0.1"
DEFAULT_MQTT_PORT = 1883
DEFAULT_MQTT_TOPIC = "ai-cctv/edge-node/status"


class MockResourceState:
    """모의 자원 사용률 값을 생성하고 보관합니다.

    인자:
        process_id: 응답에 표시할 임시 프로세스 ID입니다.
        max_successful_messages: 정상 JSON을 발행할 최대 횟수입니다.
    반환값:
        MockResourceState 인스턴스를 반환합니다.
    """

    def __init__(self, process_id=None, max_successful_messages=10):
        """모의 발행 상태를 초기화합니다.

        인자:
            process_id: 응답에 표시할 임시 프로세스 ID이며 없으면 현재 프로세스입니다.
            max_successful_messages: 정상 JSON을 발행할 최대 횟수입니다.
        반환값:
            없음.
        """

        self.started_at = time.monotonic()
        self.process_id = process_id if process_id is not None else os.getpid()
        self.max_successful_messages = max_successful_messages
        self.successful_message_count = 0

    def can_publish(self):
        """정상 JSON 메시지를 더 발행할 수 있는지 판단합니다.

        인자:
            없음.
        반환값:
            정상 발행 가능 여부를 bool로 반환합니다.
        """

        return self.successful_message_count < self.max_successful_messages

    def build_message(self):
        """현재 시점의 모의 자원 사용률 JSON을 생성합니다.

        인자:
            없음.
        반환값:
            Edge node MQTT publisher와 같은 구조의 딕셔너리를 반환합니다.
        """

        self.successful_message_count += 1
        elapsed = time.monotonic() - self.started_at
        cpu_total = self._wave(elapsed, base=42.0, amplitude=28.0, speed=0.75)
        memory_total = self._wave(elapsed, base=55.0, amplitude=14.0, speed=0.35)
        process_cpu = self._wave(elapsed, base=18.0, amplitude=16.0, speed=1.2)
        process_memory = self._wave(elapsed, base=3.5, amplitude=2.0, speed=0.5)
        battery_remaining = self._wave(elapsed, base=62.0, amplitude=18.0, speed=0.2)
        external_power_connected = int(elapsed / 8) % 2 == 0
        type_c_input_millivolt = 5100 if external_power_connected else 0
        micro_usb_input_millivolt = 0
        return {
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "cpu": {"total_percent": round(cpu_total, 1)},
            "memory": {"total_percent": round(memory_total, 1)},
            "process": {
                "pid": self.process_id,
                "name": "mock-edge-monitor",
                "cpu_percent": round(process_cpu, 1),
                "memory_percent": round(process_memory, 1),
            },
            "power": {
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "available": True,
                "battery_remaining_percent": round(battery_remaining, 1),
                "external_power_connected": external_power_connected,
                "type_c_input_millivolt": type_c_input_millivolt,
                "micro_usb_input_millivolt": micro_usb_input_millivolt,
                "power_status_raw": 1,
                "error": None,
            },
        }

    def _wave(self, elapsed, base, amplitude, speed):
        """사인파 기반의 0~100 범위 모의 백분율 값을 계산합니다.

        인자:
            elapsed: publisher 시작 이후 지난 시간입니다.
            base: 기준 백분율 값입니다.
            amplitude: 변동 폭입니다.
            speed: 변동 속도입니다.
        반환값:
            0부터 100 사이의 float 값을 반환합니다.
        """

        value = base + amplitude * math.sin(elapsed * speed)
        return max(0.0, min(100.0, value))


class MockMqttResourcePublisher:
    """모의 Edge node 상태를 MQTT topic으로 발행합니다.

    인자:
        broker_host: MQTT broker 호스트입니다.
        broker_port: MQTT broker 포트입니다.
        topic: 상태 JSON을 발행할 MQTT topic입니다.
        interval_seconds: 발행 주기입니다.
    반환값:
        MockMqttResourcePublisher 인스턴스를 반환합니다.
    """

    def __init__(self, broker_host, broker_port, topic, interval_seconds=2.0):
        """모의 publisher 설정과 자원 상태 생성기를 초기화합니다.

        인자:
            broker_host: MQTT broker 호스트입니다.
            broker_port: MQTT broker 포트입니다.
            topic: 상태 JSON을 발행할 MQTT topic입니다.
            interval_seconds: 발행 주기입니다.
        반환값:
            없음.
        """

        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.interval_seconds = interval_seconds
        self.resource_state = MockResourceState()
        self.client = _create_mqtt_client("ai-cctv-mock-edge-monitor")

    def run(self):
        """MQTT broker에 연결한 뒤 모의 상태 메시지를 발행합니다.

        인자:
            없음.
        반환값:
            정상적으로는 반환하지 않습니다.
        """

        self.client.connect(self.broker_host, self.broker_port, keepalive=60)
        self.client.loop_start()
        try:
            while True:
                if not self.resource_state.can_publish():
                    print("[mock-edge] publish limit reached; staying silent")
                    time.sleep(self.interval_seconds)
                    continue

                payload = json.dumps(
                    self.resource_state.build_message(),
                    ensure_ascii=False,
                )
                self.client.publish(self.topic, payload, qos=0, retain=True)
                print(f"[mock-edge] published {self.resource_state.successful_message_count}")
                time.sleep(self.interval_seconds)
        finally:
            self.client.loop_stop()
            self.client.disconnect()


def build_argument_parser():
    """명령행 인자 파서를 생성합니다.

    인자:
        없음.
    반환값:
        argparse.ArgumentParser 인스턴스를 반환합니다.
    """

    parser = argparse.ArgumentParser(description="Run mock Edge node MQTT monitor.")
    parser.add_argument("--host", default=DEFAULT_MQTT_HOST, help="MQTT broker host.")
    parser.add_argument("--port", type=int, default=DEFAULT_MQTT_PORT, help="MQTT port.")
    parser.add_argument("--topic", default=DEFAULT_MQTT_TOPIC, help="MQTT status topic.")
    parser.add_argument("--interval", type=float, default=2.0, help="Publish interval.")
    return parser


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


def main():
    """명령행 인자를 읽고 모의 MQTT publisher를 시작합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    args = build_argument_parser().parse_args()
    publisher = MockMqttResourcePublisher(
        broker_host=args.host,
        broker_port=args.port,
        topic=args.topic,
        interval_seconds=args.interval,
    )
    print(f"Mock Edge node MQTT publisher: {args.host}:{args.port} topic={args.topic}")
    print("Normal publishes: 10; then publisher stays silent.")
    print("Stop: Ctrl+C")
    try:
        publisher.run()
    except KeyboardInterrupt:
        print("\nMock publisher stopped.")


if __name__ == "__main__":
    main()
