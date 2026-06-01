# 문서 기준 구조 보강 모듈의 단위 테스트 파일입니다.
# 서비스와 AI 모델 없이 이상 상황, 알림, 엣지 송출 역할 경계를 검증합니다.
# 종합설계 문서의 핵심 실행 단위가 코드로 유지되는지 확인합니다.

import unittest
import os
import tempfile
import tomllib
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from ai_cctv.ai_server.alerts.dispatcher import (
    NotificationChannel,
    NotificationDispatcher,
)
from ai_cctv.ai_server.analysis.anomaly.detector import (
    AnomalyRuleEngine,
    DwellTimeAnomalyRule,
    ObjectAppearanceRule,
)
from ai_cctv.ai_server.monitoring.resource_monitor_client import (
    MqttResourceMonitorConfig as MqttResourceSubscriberConfig,
)
from ai_cctv.ai_server.analysis.rtsp_receiver import is_rtsp_source
from ai_cctv.ai_server.recovery.network_recovery_manager import (
    NetworkRecoveryConfig,
    NetworkRecoveryManager,
)
from ai_cctv.edge_node.backup_recovery_server import (
    BackupRecoveryService,
    BackupSegmentFinder,
)
from ai_cctv.edge_node.failover import EdgeNetworkFailoverPolicy
from ai_cctv.edge_node.local_backup import LocalBackupConfig
from ai_cctv.edge_node.mediamtx import MediaMtxConfig, MediaMtxReleaseResolver
from ai_cctv.edge_node.monitoring.power_status import UpsPlusPowerReader
from ai_cctv.edge_node.monitoring.resource_monitor_publisher import (
    MqttResourceMonitorConfig,
)
from ai_cctv.edge_node.streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder


class FakeSmbus:
    """UPS Plus 전원 리더 테스트용 가짜 SMBus입니다.

    인자:
        registers: 레지스터 주소별 반환 값을 담은 딕셔너리입니다.
    반환값:
        FakeSmbus 인스턴스를 반환합니다.
    """

    def __init__(self, registers):
        """가짜 레지스터 저장소와 close 호출 여부를 초기화합니다.

        인자:
            registers: 레지스터 주소별 반환 값을 담은 딕셔너리입니다.
        반환값:
            없음.
        """

        self.registers = registers
        self.closed = False

    def read_byte_data(self, device_address, register_address):
        """지정한 레지스터의 가짜 바이트 값을 반환합니다.

        인자:
            device_address: 요청된 I2C 장치 주소입니다.
            register_address: 읽을 레지스터 주소입니다.
        반환값:
            레지스터에 저장된 정수 값을 반환합니다.
        """

        del device_address
        return self.registers[register_address]

    def close(self):
        """가짜 SMBus가 닫혔음을 기록합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.closed = True


class FakeUpsPlusPowerReader(UpsPlusPowerReader):
    """가짜 SMBus를 주입받는 UPS Plus 전원 리더입니다.

    인자:
        bus: 테스트에 사용할 FakeSmbus 인스턴스입니다.
    반환값:
        FakeUpsPlusPowerReader 인스턴스를 반환합니다.
    """

    def __init__(self, bus):
        """가짜 SMBus를 저장하고 기본 UPS Plus 리더 설정을 초기화합니다.

        인자:
            bus: 테스트에 사용할 FakeSmbus 인스턴스입니다.
        반환값:
            없음.
        """

        super().__init__()
        self.bus = bus

    def _open_bus(self):
        """테스트용 가짜 SMBus를 반환합니다.

        인자:
            없음.
        반환값:
            FakeSmbus 인스턴스를 반환합니다.
        """

        return self.bus


class FailingUpsPlusPowerReader(UpsPlusPowerReader):
    """I2C 열기 실패를 재현하는 UPS Plus 전원 리더입니다.

    인자:
        없음.
    반환값:
        FailingUpsPlusPowerReader 인스턴스를 반환합니다.
    """

    def _open_bus(self):
        """I2C 버스 열기 실패를 발생시킵니다.

        인자:
            없음.
        반환값:
            정상적으로 반환하지 않습니다.
        """

        raise RuntimeError("I2C unavailable")


class MemoryNotificationChannel(NotificationChannel):
    """테스트용 메모리 알림 채널입니다.

    인자:
        없음.
    반환값:
        MemoryNotificationChannel 인스턴스를 반환합니다.
    """

    def __init__(self):
        """전송 메시지 저장 목록을 초기화합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.messages = []

    def send(self, message):
        """전송된 알림 메시지를 메모리에 저장합니다.

        인자:
            message: NotificationMessage 객체입니다.
        반환값:
            없음.
        """

        self.messages.append(message)


class ProjectStructureTest(unittest.TestCase):
    """문서 기준 구조 보강 모듈을 검증합니다.

    인자:
        unittest.TestCase 초기화 인자를 따릅니다.
    반환값:
        ProjectStructureTest 인스턴스를 반환합니다.
    """

    def test_object_appearance_rule_emits_once_per_track(self):
        """동일 추적 ID에 대한 객체 등장 이벤트가 한 번만 생성되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        rule_engine = AnomalyRuleEngine([ObjectAppearanceRule(target_class="person")])
        detection = {
            "person_id": 1,
            "class_name": "person",
            "conf": 0.91,
            "bbox": (1, 2, 3, 4),
        }

        first_events = rule_engine.evaluate_detections(
            [detection], evaluated_at=datetime(2026, 5, 28)
        )
        second_events = rule_engine.evaluate_detections(
            [detection], evaluated_at=datetime(2026, 5, 28)
        )
        moved_detection = dict(detection, bbox=(2, 3, 4, 5))
        moved_events = rule_engine.evaluate_detections(
            [moved_detection], evaluated_at=datetime(2026, 5, 28)
        )

        self.assertEqual(len(first_events), 1)
        self.assertEqual(len(second_events), 0)
        self.assertEqual(len(moved_events), 0)
        self.assertEqual(first_events[0].object_name, "person")

    def test_dwell_time_rule_emits_after_threshold(self):
        """체류 시간 초과 규칙이 임계 시간 이후 이벤트를 생성하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        rule = DwellTimeAnomalyRule(target_class="person", dwell_seconds=10)
        detection = {
            "person_id": 7,
            "class_name": "person",
            "conf": 0.8,
            "bbox": (0, 0, 10, 10),
        }
        started_at = datetime(2026, 5, 28, 10, 0, 0)

        self.assertEqual(rule.evaluate_detections([detection], started_at), [])
        events = rule.evaluate_detections([detection], started_at + timedelta(seconds=11))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "dwell_time_exceeded")

    def test_notification_dispatcher_sends_anomaly_message(self):
        """이상 상황 이벤트가 알림 메시지로 변환되어 채널로 전달되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        channel = MemoryNotificationChannel()
        dispatcher = NotificationDispatcher([channel])
        event = AnomalyRuleEngine().evaluate_detections([
            {
                "person_id": 3,
                "class_name": "person",
                "conf": 0.77,
                "bbox": (0, 0, 20, 20),
            }
        ])[0]

        sent_count = dispatcher.dispatch_anomaly_event(event)

        self.assertEqual(sent_count, 1)
        self.assertIn("감지 객체: person", channel.messages[0].to_text())

    def test_edge_failover_policy_matches_project_document(self):
        """네트워크 장애 시 로컬 저장과 최소 알림을 선택하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        policy = EdgeNetworkFailoverPolicy(enable_minimal_alert=True)
        action = policy.decide_for_network(network_available=False)

        self.assertFalse(action.should_stream)
        self.assertTrue(action.should_record_local)
        self.assertTrue(action.should_send_minimal_alert)

    def test_gstreamer_mediamtx_command_streams_and_records(self):
        """GStreamer 명령이 MediaMTX 송출과 로컬 백업을 함께 수행하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        config = EdgeStreamConfig(publish_url="rtmp://127.0.0.1:1935/test")
        backup_config = LocalBackupConfig(directory="./test_backups", segment_seconds=10)
        command = MediaMtxGStreamerCommandBuilder(
            config,
            backup_config,
        ).build_command_args()

        self.assertIn("gst-launch-1.0", command)
        self.assertIn("libcamerasrc", command)
        self.assertIn("tee", command)
        self.assertIn("splitmuxsink", command)
        self.assertIn("rtmpsink", command)
        self.assertIn("location=rtmp://127.0.0.1:1935/test", command)
        self.assertIn("max-size-time=10000000000", command)

    def test_mediamtx_release_resolver_selects_raspberry_pi_package(self):
        """Raspberry Pi 아키텍처에 맞는 MediaMTX 패키지 URL을 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        resolver = MediaMtxReleaseResolver(MediaMtxConfig(version="v1.9.0"))

        self.assertIn("linux_arm64v8", resolver.resolve_download_url("aarch64"))
        self.assertIn("linux_armv7", resolver.resolve_download_url("armv7l"))

    def test_ups_plus_power_reader_reads_battery_and_external_power(self):
        """UPS Plus 레지스터에서 배터리 잔량과 외부 전원 상태를 해석하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        bus = FakeSmbus({
            0x07: 0xEC,
            0x08: 0x13,
            0x09: 0x00,
            0x0A: 0x00,
            0x13: 75,
            0x14: 0,
            0x17: 1,
        })
        reader = FakeUpsPlusPowerReader(bus)

        snapshot = reader.read_snapshot()

        self.assertTrue(snapshot.available)
        self.assertEqual(snapshot.battery_remaining_percent, 75)
        self.assertTrue(snapshot.external_power_connected)
        self.assertEqual(snapshot.type_c_input_millivolt, 5100)
        self.assertEqual(snapshot.micro_usb_input_millivolt, 0)
        self.assertEqual(snapshot.power_status_raw, 1)
        self.assertTrue(bus.closed)

    def test_ups_plus_power_reader_reports_unavailable_on_i2c_error(self):
        """UPS Plus I2C 접근 실패가 사용 불가 스냅샷으로 변환되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        snapshot = FailingUpsPlusPowerReader().read_snapshot()

        self.assertFalse(snapshot.available)
        self.assertIsNone(snapshot.battery_remaining_percent)
        self.assertIn("I2C unavailable", snapshot.error)

    def test_console_scripts_are_split_by_deployment_bundle(self):
        """Edge node와 AI server 실행 진입점이 분리되어 있는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
        scripts = pyproject["project"]["scripts"]
        extras = pyproject["project"]["optional-dependencies"]

        self.assertEqual(scripts["ai-cctv-edge"], "ai_cctv.edge_node.main:main")
        self.assertEqual(
            scripts["ai-cctv-edge-monitor"],
            "ai_cctv.edge_node.monitoring.resource_monitor_publisher:main",
        )
        self.assertEqual(
            scripts["ai-cctv-edge-backup-recovery"],
            "ai_cctv.edge_node.backup_recovery_server:main",
        )
        self.assertEqual(
            scripts["ai-cctv-ai-server"],
            "ai_cctv.ai_server.server_run:main",
        )
        self.assertEqual(scripts["ai-cctv"], "ai_cctv.ai_server.server_run:main")
        self.assertIn("edge-node", extras)
        self.assertIn("ai-server", extras)
        self.assertIn("smbus2", extras["edge-node"])
        self.assertIn("paho-mqtt", extras["edge-node"])
        self.assertIn("paho-mqtt", extras["ai-server"])
        self.assertIn("fastapi", extras["edge-node"])
        self.assertIn("uvicorn", extras["edge-node"])
        self.assertIn("requests", extras["ai-server"])
        self.assertNotIn("edge-pi", extras)
        self.assertNotIn("windows-server", extras)
        self.assertNotIn("edge", extras)
        self.assertNotIn("ai-cctv-windows-server", scripts)
        self.assertTrue(Path("src/ai_cctv/edge_node").is_dir())
        self.assertTrue(Path("src/ai_cctv/edge_node/local_backup.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/mediamtx.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/runtime.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/backup_recovery_server.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/monitoring").is_dir())
        self.assertTrue(
            Path(
                "src/ai_cctv/edge_node/monitoring/resource_monitor_publisher.py"
            ).is_file()
        )
        self.assertFalse(
            Path("src/ai_cctv/edge_node/monitoring/resource_monitor_server.py").exists()
        )
        self.assertTrue(
            Path("src/ai_cctv/edge_node/monitoring/power_status.py").is_file()
        )
        self.assertTrue(Path("src/ai_cctv/ai_server").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/server_run.py").is_file())
        self.assertTrue(Path("src/ai_cctv/ai_server/monitoring").is_dir())
        self.assertTrue(
            Path("src/ai_cctv/ai_server/monitoring/resource_monitor_client.py").is_file()
        )
        self.assertFalse(
            Path("src/ai_cctv/ai_server/monitoring/resource_monitor_server.py").exists()
        )
        self.assertTrue(Path("src/ai_cctv/ai_server/ui").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/ui/edge_status_window.py").is_file())
        self.assertTrue(Path("src/ai_cctv/ai_server/analysis").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/analysis/rtsp_receiver.py").is_file())
        self.assertTrue(Path("src/ai_cctv/ai_server/recovery").is_dir())
        self.assertTrue(
            Path("src/ai_cctv/ai_server/recovery/network_recovery_manager.py").is_file()
        )
        self.assertTrue(Path("src/ai_cctv/ai_server/analysis/anomaly").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/storage").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/storage/clip_manager.py").is_file())
        self.assertTrue(Path("src/ai_cctv/ai_server/alerts").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/alerts/chat_bot").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/common").is_dir())
        self.assertFalse(Path("src/ai_cctv/edge").exists())
        self.assertFalse(Path("src/ai_cctv/edge_pi").exists())
        self.assertFalse(Path("src/ai_cctv/windows_server").exists())
        self.assertFalse(Path("src/ai_cctv/server").exists())
        self.assertFalse(Path("src/ai_cctv/streaming").exists())
        self.assertFalse(Path("src/ai_cctv/client").exists())
        self.assertFalse(Path("src/ai_cctv/anomaly").exists())
        self.assertFalse(Path("src/ai_cctv/alerts").exists())
        self.assertFalse(Path("src/ai_cctv/common").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/client").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/control_center").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/main.py").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/analysis.py").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/anomaly").exists())
        self.assertFalse(Path("src/ai_cctv/ai_server/ui/legacy_cctv_gui.py").exists())
        self.assertFalse(Path("src/ai_cctv/streaming/legacy_rtsp_receiver.py").exists())
        self.assertFalse(Path("src/ai_cctv/server/fail_over.py").exists())
        self.assertFalse(Path("scripts/stream_and_record.sh").exists())
        self.assertTrue(Path("requirements/edge-node.txt").is_file())
        self.assertTrue(Path("requirements/ai-server.txt").is_file())

    def test_rtsp_source_detection(self):
        """RTSP URL과 일반 카메라 번호를 구분하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.assertTrue(is_rtsp_source("rtsp://192.168.137.2:8554/live"))
        self.assertFalse(is_rtsp_source(0))
        self.assertFalse(is_rtsp_source("http://127.0.0.1/video"))

    def test_network_recovery_manager_skips_when_url_missing(self):
        """복구 서버 URL이 없을 때 네트워크 요청 없이 실패 사유를 반환하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        manager = NetworkRecoveryManager(NetworkRecoveryConfig(server_url=""))
        manager.record_failure(datetime(2026, 5, 31, 10, 0, 0))

        result = manager.record_recovery(datetime(2026, 5, 31, 10, 0, 5))

        self.assertFalse(result["requested"])
        self.assertEqual(result["reason"], "server_url_not_configured")

    def test_backup_recovery_service_archives_overlapping_segments(self):
        """요청 시간대와 겹치는 TS 백업 파일을 ZIP으로 묶는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = Path(temp_dir)
            segment_path = backup_dir / "backup_20260531_100000_00001.ts"
            segment_path.write_bytes(b"segment")
            end_time = datetime(2026, 5, 31, 10, 0, 10)
            os.utime(segment_path, (end_time.timestamp(), end_time.timestamp()))

            service = BackupRecoveryService(
                BackupSegmentFinder(backup_dir, segment_seconds=10)
            )
            archive = service.recover(
                "2026-05-31T10:00:05",
                "2026-05-31T10:00:12",
            )

            try:
                with zipfile.ZipFile(archive.path) as zip_file:
                    self.assertEqual(
                        zip_file.namelist(),
                        ["backup_20260531_100000_00001.ts"],
                    )
                self.assertEqual(archive.file_count, 1)
            finally:
                archive.path.unlink(missing_ok=True)

    def test_resource_monitor_mqtt_defaults_match_between_nodes(self):
        """Edge node와 AI server의 기본 MQTT topic이 같은지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        edge_config = MqttResourceMonitorConfig()
        ai_server_config = MqttResourceSubscriberConfig()

        self.assertEqual(edge_config.broker_host, "127.0.0.1")
        self.assertEqual(edge_config.broker_port, 1883)
        self.assertEqual(edge_config.topic, "ai-cctv/edge-node/status")
        self.assertEqual(ai_server_config.broker_host, edge_config.broker_host)
        self.assertEqual(ai_server_config.broker_port, edge_config.broker_port)
        self.assertEqual(ai_server_config.topic, edge_config.topic)


if __name__ == "__main__":
    unittest.main()
