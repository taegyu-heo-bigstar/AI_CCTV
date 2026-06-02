# pseudo Edge node 통합 실행 파일입니다.
# RTSP 포트 stub, 최소 MQTT broker, 백업 복구 HTTP 서버를 같은 생명주기로 실행합니다.
# MQTT broker는 Edge node 자원 상태 JSON을 주기적으로 발행합니다.
# AI server는 출력된 연결 정보 블록을 붙여넣어 Windows에서 엣지 모드 테스트를 수행합니다.

from datetime import datetime
import json
import math
import os
import threading
import time

from .backup_recovery import PseudoBackupRecoveryServer
from .config import PseudoEdgeNodeConfig
from .mqtt_broker import TinyMqttBroker
from .rtsp_stub import RtspPortStub


class PseudoResourceStatusBuilder:
    """작업관리자 형태 UI 테스트용 Edge node 상태 JSON을 생성합니다.

    인자:
        process_id: 상태 JSON에 포함할 감시 대상 프로세스 ID입니다.
    반환값:
        PseudoResourceStatusBuilder 인스턴스를 반환합니다.
    """

    def __init__(self, process_id=None):
        """상태값 변화 계산에 필요한 기준 시각과 PID를 초기화합니다.

        인자:
            process_id: 감시 대상 프로세스 ID이며 없으면 현재 프로세스 ID를 사용합니다.
        반환값:
            없음.
        """

        self.process_id = process_id if process_id is not None else os.getpid()
        self.started_at = time.monotonic()

    def build(self):
        """현재 시점의 pseudo 자원 상태 딕셔너리를 생성합니다.

        인자:
            없음.
        반환값:
            CPU, memory, process, power 정보를 포함한 딕셔너리를 반환합니다.
        """

        elapsed = time.monotonic() - self.started_at
        cpu_percent = 35.0 + 20.0 * math.sin(elapsed / 3.0)
        memory_percent = 48.0 + 8.0 * math.sin(elapsed / 5.0)
        process_cpu_percent = 12.0 + 6.0 * math.sin(elapsed / 2.0)
        process_memory_percent = 3.0 + 1.5 * math.sin(elapsed / 4.0)
        battery_percent = max(0, min(100, int(87 - elapsed / 120)))
        return {
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "cpu": {"total_percent": round(cpu_percent, 2)},
            "memory": {"total_percent": round(memory_percent, 2)},
            "process": {
                "pid": self.process_id,
                "name": "pseudo_edge_node",
                "cpu_percent": round(process_cpu_percent, 2),
                "memory_percent": round(process_memory_percent, 2),
            },
            "power": {
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "available": True,
                "battery_remaining_percent": battery_percent,
                "external_power_connected": True,
                "type_c_input_millivolt": 5100,
                "micro_usb_input_millivolt": 0,
                "power_status_raw": 1,
                "error": None,
            },
        }


class PseudoEdgeNodeRuntime:
    """Windows 테스트용 pseudo Edge node 실행 흐름을 조율합니다.

    인자:
        config: pseudo Edge node 실행 설정입니다.
        status_builder: MQTT 상태 JSON 생성 객체입니다.
    반환값:
        PseudoEdgeNodeRuntime 인스턴스를 반환합니다.
    """

    def __init__(self, config=None, status_builder=None):
        """하위 서버 객체와 상태 발행 thread 상태를 초기화합니다.

        인자:
            config: pseudo Edge node 실행 설정입니다.
            status_builder: MQTT 상태 JSON 생성 객체입니다.
        반환값:
            없음.
        """

        self.config = config if config is not None else PseudoEdgeNodeConfig()
        self.status_builder = (
            status_builder
            if status_builder is not None
            else PseudoResourceStatusBuilder()
        )
        self.rtsp_stub = RtspPortStub(
            host=self.config.host,
            port=self.config.rtsp_port,
            path=self.config.rtsp_path,
        )
        self.mqtt_broker = TinyMqttBroker(
            host=self.config.host,
            port=self.config.mqtt_port,
        )
        self.recovery_server = PseudoBackupRecoveryServer(
            host=self.config.host,
            port=self.config.backup_recovery_port,
            backup_dir=self.config.backup_dir,
        )
        self.running = False
        self.status_thread = None

    def start(self):
        """pseudo Edge node의 모든 하위 서비스를 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.running:
            return

        self.rtsp_stub.start()
        self.mqtt_broker.start()
        self.recovery_server.start()
        self.running = True
        self.status_thread = threading.Thread(
            target=self._publish_status_loop,
            name="PseudoEdgeStatusPublisher",
            daemon=True,
        )
        self.status_thread.start()

    def stop(self):
        """pseudo Edge node의 모든 하위 서비스를 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False
        if self.status_thread is not None and self.status_thread.is_alive():
            self.status_thread.join(timeout=2)
        self.recovery_server.stop()
        self.mqtt_broker.stop()
        self.rtsp_stub.stop()

    def run_forever(self):
        """연결 정보를 출력한 뒤 pseudo Edge node를 계속 실행합니다.

        인자:
            없음.
        반환값:
            정상 종료 시 0을 반환합니다.
        """

        print(self.config.to_terminal_text(), flush=True)
        self.start()
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            return 0
        finally:
            self.stop()

    def _publish_status_loop(self):
        """설정된 주기마다 MQTT 상태 JSON을 발행합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        while self.running:
            resource_status = self.status_builder.build()
            payload = json.dumps(resource_status, ensure_ascii=False)
            self.mqtt_broker.publish(self.config.mqtt_topic, payload, retain=True)
            time.sleep(self.config.status_interval_seconds)
