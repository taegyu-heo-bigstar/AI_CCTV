# 문서 기준 구조 보강 모듈의 단위 테스트 파일입니다.
# 서비스와 AI 모델 없이 이상 상황, 알림, 엣지 송출 역할 경계를 검증합니다.
# 종합설계 문서의 핵심 실행 단위가 코드로 유지되는지 확인합니다.

import unittest
import os
import socket
import sys
import tempfile
import tomllib
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch

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
from ai_cctv.ai_server.analysis import video_stream as video_stream_module
from ai_cctv.ai_server.analysis.rtsp_receiver import (
    RtspFrameReceiver,
    RtspFrameSnapshot,
    is_rtsp_source,
)
from ai_cctv.ai_server.analysis.video_stream import VideoStream
from ai_cctv.ai_server.connection.edge_connection import (
    EdgeConnectionConfig,
    parse_edge_startup_text,
)
from ai_cctv.ai_server.recovery.network_recovery_manager import (
    NetworkRecoveryConfig,
    NetworkRecoveryManager,
)
from ai_cctv.ai_server.runtime.bootstrap import ensure_pyqt5_available
from ai_cctv.ai_server.runtime.environment_check import (
    RuntimeReadinessReport,
    RuntimeRequirement,
    RuntimeRequirementResult,
    build_analysis_requirements,
    build_startup_requirements,
)
from ai_cctv.ai_server.runtime.os_guard import ensure_windows_os, is_windows_os
from ai_cctv.edge_node.backup_recovery_server import (
    BackupRecoveryService,
    BackupSegmentFinder,
)
from ai_cctv.edge_node.failover import EdgeNetworkFailoverPolicy
from ai_cctv.edge_node.local_backup import LocalBackupConfig
from ai_cctv.edge_node.mediamtx import MediaMtxConfig, MediaMtxReleaseResolver
from ai_cctv.edge_node.os_guard import ensure_supported_edge_os, is_supported_edge_os
from ai_cctv.edge_node.monitoring.power_status import UpsPlusPowerReader
from ai_cctv.edge_node.monitoring.mqtt_broker import (
    MqttBrokerConfig,
    TinyMqttBroker,
    build_publish_packet,
    read_mqtt_packet,
)
from ai_cctv.edge_node.monitoring.resource_monitor_publisher import (
    MqttResourceMonitorConfig,
    SUPPORTED_MQTT_QOS_VALUES,
)
from ai_cctv.edge_node.startup_info import build_edge_connection_info
from ai_cctv.edge_node.streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder
from ai_cctv.edge_node.support_processes import EdgeSupportProcessConfig
from tester.pseudo_edge_node.backup_recovery import build_pseudo_recovery_archive
from tester.pseudo_edge_node.config import PseudoEdgeNodeConfig


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
            scripts["ai-cctv-edge-mqtt-broker"],
            "ai_cctv.edge_node.monitoring.mqtt_broker:main",
        )
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
        self.assertNotIn("pseudo-edge-node", extras)
        self.assertIn("smbus2", extras["edge-node"])
        self.assertIn("paho-mqtt", extras["edge-node"])
        self.assertIn("paho-mqtt", extras["ai-server"])
        self.assertIn("fastapi", extras["edge-node"])
        self.assertIn("uvicorn", extras["edge-node"])
        self.assertNotIn("pygobject", extras["edge-node"])
        self.assertIn("requests", extras["ai-server"])
        self.assertIn("torch", extras["ai-server"])
        self.assertIn("huggingface-hub", extras["ai-server"])
        self.assertNotIn("edge-pi", extras)
        self.assertNotIn("windows-server", extras)
        self.assertNotIn("edge", extras)
        self.assertNotIn("ai-cctv-windows-server", scripts)
        self.assertTrue(Path("src/ai_cctv/edge_node").is_dir())
        self.assertTrue(Path("src/ai_cctv/edge_node/local_backup.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/mediamtx.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/os_guard.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/runtime.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/startup_info.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/support_processes.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/backup_recovery_server.py").is_file())
        self.assertTrue(Path("src/ai_cctv/edge_node/monitoring").is_dir())
        self.assertTrue(
            Path("src/ai_cctv/edge_node/monitoring/mqtt_broker.py").is_file()
        )
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
        self.assertFalse(Path("src/ai_cctv/pseudo_edge_node").exists())
        self.assertTrue(Path("tester").is_dir())
        self.assertTrue(Path("tester/README.md").is_file())
        self.assertTrue(Path("tester/tests/test_project_structure.py").is_file())
        self.assertTrue(Path("tester/tools/mock_edge_mqtt_publisher.py").is_file())
        self.assertTrue(Path("tester/pseudo_edge_node").is_dir())
        self.assertTrue(Path("tester/pseudo_edge_node/main.py").is_file())
        self.assertTrue(Path("tester/pseudo_edge_node/mqtt_broker.py").is_file())
        self.assertTrue(Path("tester/pseudo_edge_node/rtsp_stub.py").is_file())
        self.assertTrue(Path("tester/pseudo_edge_node/backup_recovery.py").is_file())
        self.assertFalse(Path("inst").exists())
        self.assertTrue(Path("instructions").is_dir())
        self.assertTrue(Path("instructions/README.md").is_file())
        self.assertTrue(Path("instructions/flow.md").is_file())
        self.assertTrue(Path("instructions/structure.md").is_file())
        self.assertTrue(Path("instructions/change.md").is_file())
        self.assertTrue(Path("legacy").is_dir())
        self.assertTrue(Path("legacy/README.md").is_file())
        self.assertTrue(Path("legacy/archive").is_dir())
        self.assertTrue(Path("legacy/study").is_dir())
        self.assertTrue(Path("legacy/rtsp_v1").is_dir())
        self.assertFalse(Path("docs/study").exists())
        self.assertFalse(Path("docs/rtsp_v1.md").exists())
        self.assertTrue(Path("docs/rtsp.md").is_file())
        self.assertFalse(Path(".proj_env").exists())
        self.assertTrue(Path(".env.example").is_file())
        self.assertIn(".env", Path(".gitignore").read_text(encoding="utf-8"))
        self.assertTrue(Path("src/ai_cctv/ai_server").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/server_run.py").is_file())
        self.assertTrue(Path("src/ai_cctv/ai_server/connection").is_dir())
        self.assertTrue(
            Path("src/ai_cctv/ai_server/connection/edge_connection.py").is_file()
        )
        self.assertTrue(Path("src/ai_cctv/ai_server/monitoring").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/runtime").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/runtime/bootstrap.py").is_file())
        self.assertTrue(
            Path("src/ai_cctv/ai_server/runtime/os_guard.py").is_file()
        )
        self.assertTrue(
            Path("src/ai_cctv/ai_server/runtime/environment_check.py").is_file()
        )
        self.assertTrue(
            Path("src/ai_cctv/ai_server/monitoring/resource_monitor_client.py").is_file()
        )
        self.assertFalse(
            Path("src/ai_cctv/ai_server/monitoring/resource_monitor_server.py").exists()
        )
        self.assertTrue(Path("src/ai_cctv/ai_server/ui").is_dir())
        self.assertTrue(
            Path("src/ai_cctv/ai_server/ui/edge_connection_dialog.py").is_file()
        )
        self.assertTrue(
            Path("src/ai_cctv/ai_server/ui/runtime_readiness_dialog.py").is_file()
        )
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

    def test_video_stream_local_fps_uses_lazy_cv2_constants(self):
        """로컬 카메라 FPS 조회가 지연 import한 OpenCV 상수를 사용하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        class FakeCv2:
            """OpenCV 상수를 흉내 내는 테스트용 객체입니다.

            인자:
                없음.
            반환값:
                FakeCv2 인스턴스를 반환합니다.
            """

            CAP_PROP_FPS = 5

        class FakeCapture:
            """OpenCV VideoCapture의 get 호출을 흉내 내는 테스트용 객체입니다.

            인자:
                없음.
            반환값:
                FakeCapture 인스턴스를 반환합니다.
            """

            def get(self, prop):
                """요청된 속성 값을 반환합니다.

                인자:
                    prop: OpenCV 속성 상수입니다.
                반환값:
                    FPS 속성이면 24를 반환합니다.
                """

                if prop == FakeCv2.CAP_PROP_FPS:
                    return 24
                return 0

        original_loader = video_stream_module._load_cv2_module
        try:
            video_stream_module._load_cv2_module = lambda: FakeCv2
            stream = VideoStream(0)
            stream.cap = FakeCapture()

            self.assertEqual(stream.get_fps(), 24)
        finally:
            video_stream_module._load_cv2_module = original_loader

    def test_rtsp_receiver_watchdog_releases_active_capture(self):
        """RTSP watchdog이 활성 VideoCapture를 강제 해제하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        receiver = RtspFrameReceiver("rtsp://192.168.137.2:8554/live")
        fake_capture = Mock()

        receiver._set_active_capture(fake_capture)
        released = receiver._release_active_capture("test watchdog")

        self.assertTrue(released)
        self.assertFalse(receiver._is_active_capture(fake_capture))
        fake_capture.release.assert_called_once()

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

    def test_network_recovery_manager_uses_rtsp_review_request_contract(self):
        """복구 요청이 start/end만 전송하고 실패 시 장애 구간을 유지하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        calls = []

        class FakeResponse:
            """복구 API 404 응답을 흉내 내는 객체입니다.

            인자:
                없음.
            반환값:
                FakeResponse 인스턴스를 반환합니다.
            """

            status_code = 404
            ok = False
            text = '{"message": "no backup"}'
            headers = {}

            def json(self):
                """JSON 오류 메시지를 반환합니다.

                인자:
                    없음.
                반환값:
                    message 필드가 있는 딕셔너리를 반환합니다.
                """

                return {"message": "no backup"}

        class FakeRequests:
            """requests 모듈의 get 호출만 흉내 내는 객체입니다.

            인자:
                없음.
            반환값:
                FakeRequests 인스턴스를 반환합니다.
            """

            RequestException = Exception

            @staticmethod
            def get(url, params, timeout, stream):
                """복구 API 호출 인자를 기록하고 404 응답을 반환합니다.

                인자:
                    url: 호출 대상 URL입니다.
                    params: HTTP query parameter 딕셔너리입니다.
                    timeout: 요청 제한 시간입니다.
                    stream: 스트리밍 응답 사용 여부입니다.
                반환값:
                    FakeResponse 인스턴스를 반환합니다.
                """

                calls.append({
                    "url": url,
                    "params": params,
                    "timeout": timeout,
                    "stream": stream,
                })
                return FakeResponse()

        manager = NetworkRecoveryManager(
            NetworkRecoveryConfig(
                server_url="http://edge-node:8002/recover",
                settle_seconds=0,
            )
        )
        manager.record_failure(datetime(2026, 5, 31, 10, 0, 0))

        with patch.dict(sys.modules, {"requests": FakeRequests}):
            result = manager.record_recovery(datetime(2026, 5, 31, 10, 0, 5))

        self.assertEqual(
            calls[0]["params"],
            {
                "start": "2026-05-31T10:00:00",
                "end": "2026-05-31T10:00:05",
            },
        )
        self.assertTrue(calls[0]["stream"])
        self.assertEqual(result["reason"], "not_found")
        self.assertEqual(result["error"], "no backup")
        self.assertTrue(manager.has_active_failure())

    def test_network_recovery_manager_merges_recovered_ts_segments_to_mp4(self):
        """복구 ZIP의 TS 세그먼트를 원본 녹화 폴더의 MP4로 병합하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            root_dir = Path(temp_dir)
            recovery_dir = root_dir / "복구 영상"
            recording_dir = root_dir / "original_records"
            zip_path = root_dir / "recovered.zip"
            merged_names = []

            with zipfile.ZipFile(zip_path, "w") as zip_file:
                zip_file.writestr("backup_20260531_100000_00002.ts", b"two")
                zip_file.writestr("backup_20260531_100000_00001.ts", b"one")
                zip_file.writestr("../escape.ts", b"skip")
                zip_file.writestr("ignore.txt", b"skip")

            manager = NetworkRecoveryManager(
                NetworkRecoveryConfig(
                    server_url="",
                    recovery_dir=str(recovery_dir),
                    recording_dir=str(recording_dir),
                    settle_seconds=0,
                )
            )

            def fake_merge_ts_files(ts_files, output_path, work_dir):
                """테스트에서 ffmpeg 실행을 대체하고 병합 대상 순서를 기록합니다.

                인자:
                    ts_files: 병합할 TS 파일 목록입니다.
                    output_path: 생성할 MP4 경로입니다.
                    work_dir: 임시 작업 폴더입니다.
                반환값:
                    성공 결과 딕셔너리를 반환합니다.
                """

                del work_dir
                merged_names.extend(path.name for path in ts_files)
                Path(output_path).write_bytes(b"mp4")
                return {"success": True}

            manager._merge_ts_files = fake_merge_ts_files
            payload = manager.build_payload(
                datetime(2026, 5, 31, 10, 0, 0),
                datetime(2026, 5, 31, 10, 0, 10),
            )

            result = manager._extract_and_merge(zip_path, payload)

            self.assertTrue(result["success"])
            self.assertEqual(result["ts_count"], 2)
            self.assertEqual(
                merged_names,
                [
                    "backup_20260531_100000_00001.ts",
                    "backup_20260531_100000_00002.ts",
                ],
            )
            output_path = Path(result["file_path"])
            self.assertEqual(output_path.parent, recording_dir)
            self.assertIn("장애복구파일", output_path.name)

    def test_video_stream_waits_for_first_rtsp_frame_before_recording_failure(self):
        """첫 RTSP 프레임 수신 전 대기 상태를 장애 복구 요청으로 오인하지 않는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        class FakeRecoveryManager:
            """VideoStream 테스트용 복구 관리자입니다.

            인자:
                없음.
            반환값:
                FakeRecoveryManager 인스턴스를 반환합니다.
            """

            def __init__(self):
                """기록된 장애 횟수를 초기화합니다.

                인자:
                    없음.
                반환값:
                    없음.
                """

                self.failure_count = 0

            def record_failure(self):
                """장애 기록 호출 횟수를 증가시킵니다.

                인자:
                    없음.
                반환값:
                    장애 시작 결과 딕셔너리를 반환합니다.
                """

                self.failure_count += 1
                return {"started": True}

            def has_active_failure(self):
                """테스트용 활성 장애 상태를 반환합니다.

                인자:
                    없음.
                반환값:
                    활성 장애가 있으면 True를 반환합니다.
                """

                return self.failure_count > 0

        class FakeReceiver:
            """VideoStream 테스트용 RTSP 수신기입니다.

            인자:
                snapshots: 순서대로 반환할 수신 결과 목록입니다.
            반환값:
                FakeReceiver 인스턴스를 반환합니다.
            """

            def __init__(self, snapshots):
                """수신 결과 목록을 초기화합니다.

                인자:
                    snapshots: read_new_frame이 반환할 결과 목록입니다.
                반환값:
                    없음.
                """

                self.snapshots = list(snapshots)
                self.connected = False

            def read_new_frame(self, last_sequence):
                """준비된 RTSP 수신 결과를 하나 반환합니다.

                인자:
                    last_sequence: 호출자가 마지막으로 받은 프레임 순번입니다.
                반환값:
                    RtspFrameSnapshot 객체를 반환합니다.
                """

                del last_sequence
                snapshot = self.snapshots.pop(0)
                self.connected = snapshot.connected
                return snapshot

        manager = FakeRecoveryManager()
        stream = VideoStream(
            "rtsp://192.168.137.2:8554/live",
            recovery_manager=manager,
        )
        stream.receiver = FakeReceiver([
            RtspFrameSnapshot(False, None, 0, False, "initial wait"),
            RtspFrameSnapshot(True, object(), 1, True, ""),
            RtspFrameSnapshot(False, None, 1, False, "lost"),
        ])

        self.assertEqual(stream._read_rtsp_frame(), (False, None))
        self.assertEqual(manager.failure_count, 0)

        success, _frame = stream._read_rtsp_frame()
        self.assertTrue(success)

        self.assertEqual(stream._read_rtsp_frame(), (False, None))
        self.assertEqual(manager.failure_count, 1)

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

    def test_resource_monitor_mqtt_defaults_use_edge_broker(self):
        """Edge node 내장 broker와 MQTT 상태 발행 기본값을 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        broker_config = MqttBrokerConfig()
        edge_config = MqttResourceMonitorConfig()
        ai_server_config = MqttResourceSubscriberConfig()
        support_config = EdgeSupportProcessConfig()

        self.assertEqual(broker_config.host, "0.0.0.0")
        self.assertEqual(broker_config.port, 1883)
        self.assertEqual(edge_config.broker_host, "127.0.0.1")
        self.assertEqual(edge_config.broker_port, 1883)
        self.assertEqual(edge_config.topic, "ai-cctv/edge-node/status")
        self.assertEqual(ai_server_config.broker_host, "127.0.0.1")
        self.assertEqual(ai_server_config.broker_port, edge_config.broker_port)
        self.assertEqual(ai_server_config.topic, edge_config.topic)
        self.assertTrue(support_config.run_mqtt_broker)

    def test_resource_monitor_mqtt_qos_is_fixed_to_zero(self):
        """MQTT 상태 발행 QoS가 현재 정책상 0으로 고정되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        with patch.dict(os.environ, {"AI_CCTV_MQTT_QOS": "1"}):
            config = MqttResourceMonitorConfig.from_environment()

        self.assertEqual(SUPPORTED_MQTT_QOS_VALUES, (0,))
        self.assertEqual(config.qos, 0)
        with self.assertRaises(ValueError):
            MqttResourceMonitorConfig(qos=1)

    def test_edge_connection_info_prints_ai_server_settings(self):
        """Edge node 시작 정보가 AI server 설정값을 포함하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        connection_info = build_edge_connection_info(
            edge_host="192.168.137.2",
            mqtt_port=1883,
            mqtt_topic="ai-cctv/edge-node/status",
            backup_recovery_port=8002,
            backup_dir="/home/phoenix/backups",
        )
        terminal_text = connection_info.to_terminal_text()

        self.assertEqual(connection_info.rtsp_url, "rtsp://192.168.137.2:8554/live")
        self.assertEqual(
            connection_info.backup_recovery_url,
            "http://192.168.137.2:8002/recover",
        )
        self.assertIn("EDGE_HOST=192.168.137.2", terminal_text)
        self.assertIn("MQTT_BROKER=192.168.137.2:1883", terminal_text)
        self.assertIn(
            '$env:AI_CCTV_RECOVERY_SERVER_URL="http://192.168.137.2:8002/recover"',
            terminal_text,
        )

    def test_edge_node_os_guard_accepts_linux_debian_family(self):
        """Edge node OS guard가 Linux Debian 계열만 허용하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.assertTrue(
            is_supported_edge_os("Linux", {"ID": "debian", "ID_LIKE": ""})
        )
        self.assertTrue(
            is_supported_edge_os("Linux", {"ID": "ubuntu", "ID_LIKE": "debian"})
        )
        self.assertTrue(
            is_supported_edge_os("Linux", {"ID": "raspbian", "ID_LIKE": "debian"})
        )
        self.assertTrue(is_supported_edge_os("Linux", {}))
        self.assertFalse(is_supported_edge_os("Windows", {"ID": "ubuntu"}))
        self.assertFalse(is_supported_edge_os("Linux", {"ID": "fedora"}))
        ensure_supported_edge_os("Linux", {"ID": "debian"})
        with self.assertRaises(SystemExit):
            ensure_supported_edge_os("Windows", {"ID": "windows"}, stream=Mock())

    def test_ai_server_parses_edge_startup_connection_text(self):
        """AI server 시작 UI가 Edge node 표준 출력값을 설정 객체로 해석하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        startup_text = """
        [AI_CCTV Edge Node Connection]
        EDGE_HOST=192.168.137.2
        RTSP_URL=rtsp://192.168.137.2:8554/live
        MQTT_BROKER=192.168.137.1:1883
        MQTT_TOPIC=ai-cctv/edge-node/status
        BACKUP_RECOVERY_URL=http://192.168.137.2:8002/recover
        """

        config = parse_edge_startup_text(
            startup_text,
            base_config=EdgeConnectionConfig(),
        )

        self.assertEqual(config.rtsp_url, "rtsp://192.168.137.2:8554/live")
        self.assertEqual(config.mqtt_host, "192.168.137.1")
        self.assertEqual(config.mqtt_port, 1883)
        self.assertEqual(config.mqtt_topic, "ai-cctv/edge-node/status")
        self.assertEqual(
            config.backup_recovery_url,
            "http://192.168.137.2:8002/recover",
        )

    def test_tester_edge_connection_text_is_parsed_as_regular_edge(self):
        """tester의 Edge 연결 출력값이 일반 Edge 설정으로만 해석되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        startup_text = PseudoEdgeNodeConfig(
            host="127.0.0.1",
            rtsp_port=8554,
            mqtt_port=1883,
            backup_recovery_port=8002,
        ).to_terminal_text()

        config = parse_edge_startup_text(
            startup_text,
            base_config=EdgeConnectionConfig(),
        )

        self.assertFalse(hasattr(config, "use_pseudo_edge"))
        self.assertEqual(config.rtsp_url, "rtsp://127.0.0.1:8554/live")
        self.assertEqual(config.mqtt_host, "127.0.0.1")
        self.assertEqual(config.mqtt_port, 1883)
        self.assertEqual(
            config.backup_recovery_url,
            "http://127.0.0.1:8002/recover",
        )

    def test_tester_edge_config_does_not_publish_test_flag(self):
        """tester Edge 설정 출력이 AI server에 테스트 플래그를 노출하지 않는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        terminal_text = PseudoEdgeNodeConfig(host="127.0.0.1").to_terminal_text()

        self.assertIn("[AI_CCTV Edge Node Connection]", terminal_text)
        self.assertNotIn("PSEUDO_EDGE=1", terminal_text)
        self.assertNotIn("AI_CCTV_USE_PSEUDO_EDGE", terminal_text)
        self.assertIn("RTSP_URL=rtsp://127.0.0.1:8554/live", terminal_text)

    def test_mqtt_publish_packet_contains_topic_and_payload(self):
        """MQTT broker helper가 publish packet을 생성하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        packet = build_publish_packet("ai-cctv/edge-node/status", '{"ok": true}')

        self.assertTrue(packet.startswith(b"\x31"))
        self.assertIn(b"ai-cctv/edge-node/status", packet)
        self.assertIn(b'{"ok": true}', packet)

    def test_edge_mqtt_broker_accepts_basic_subscribe_and_publish(self):
        """Edge node 내장 MQTT broker가 기본 구독과 발행을 처리하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        topic = "ai-cctv/edge-node/status"
        broker = TinyMqttBroker(MqttBrokerConfig(host="127.0.0.1", port=0))
        broker.start()
        port = broker.server_socket.getsockname()[1]

        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2) as client:
                client.settimeout(2)
                client.sendall(b"\x10\x0c\x00\x04MQTT\x04\x02\x00<\x00\x00")

                fixed_header, payload = read_mqtt_packet(client)
                self.assertEqual(fixed_header, 0x20)
                self.assertEqual(payload, b"\x00\x00")

                topic_bytes = topic.encode("utf-8")
                subscribe_payload = (
                    b"\x00\x01"
                    + len(topic_bytes).to_bytes(2, "big")
                    + topic_bytes
                    + b"\x00"
                )
                client.sendall(
                    b"\x82"
                    + bytes([len(subscribe_payload)])
                    + subscribe_payload
                )

                fixed_header, payload = read_mqtt_packet(client)
                self.assertEqual(fixed_header, 0x90)
                self.assertEqual(payload, b"\x00\x01\x00")

                client.sendall(build_publish_packet(topic, '{"ok": true}', retain=True))
                fixed_header, payload = read_mqtt_packet(client)

                self.assertEqual(fixed_header, 0x31)
                self.assertIn(topic_bytes, payload)
                self.assertIn(b'{"ok": true}', payload)
        finally:
            broker.stop()

    def test_pseudo_backup_recovery_archive_contains_ts_segment(self):
        """pseudo 백업 복구 응답 ZIP에 TS segment가 포함되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        with tempfile.TemporaryDirectory() as temp_dir:
            archive_bytes = build_pseudo_recovery_archive(
                "2026-05-31T10:00:00",
                "2026-05-31T10:00:10",
                temp_dir,
            )
            archive_path = Path(temp_dir) / "pseudo.zip"
            archive_path.write_bytes(archive_bytes)
            with zipfile.ZipFile(archive_path) as zip_file:
                names = zip_file.namelist()

        self.assertEqual(names, ["backup_20260531_100000_00001.ts"])

    def test_ai_server_os_guard_accepts_only_windows(self):
        """AI server OS guard가 Windows만 허용하고 다른 OS는 종료하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.assertTrue(is_windows_os("Windows"))
        self.assertFalse(is_windows_os("Linux"))
        ensure_windows_os("Windows")
        with self.assertRaises(SystemExit):
            ensure_windows_os("Linux", stream=Mock())

    def test_pyqt5_bootstrap_installs_only_when_user_accepts(self):
        """PyQt5 bootstrap이 사용자가 동의한 경우에만 설치 함수를 호출하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        installer = Mock()
        availability = [False, True]

        ensure_pyqt5_available(
            finder=lambda: availability.pop(0),
            ask_user=lambda: True,
            installer=installer,
        )

        installer.assert_called_once()
        with self.assertRaises(SystemExit):
            ensure_pyqt5_available(
                finder=lambda: False,
                ask_user=lambda: False,
                installer=Mock(),
                stream=Mock(),
            )

    def test_local_camera_connection_config_uses_camera_index(self):
        """Windows 자체 카메라 분기 설정이 Edge node 값 대신 카메라 번호를 사용하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        config = EdgeConnectionConfig(use_local_camera=True, local_camera_index=1)

        self.assertEqual(config.video_source(), 1)

    def test_local_camera_connection_does_not_publish_edge_environment(self):
        """로컬 카메라 모드는 RTSP/MQTT/복구 환경 변수를 남기지 않는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        names = [
            "AI_CCTV_RTSP_URL",
            "AI_CCTV_MQTT_HOST",
            "AI_CCTV_MQTT_PORT",
            "AI_CCTV_MQTT_STATUS_TOPIC",
            "AI_CCTV_RECOVERY_SERVER_URL",
        ]
        original = {name: os.environ.get(name) for name in names}
        try:
            for name in names:
                os.environ[name] = "test"
            EdgeConnectionConfig(use_local_camera=True, local_camera_index=2).apply_environment()

            self.assertEqual(os.environ["AI_CCTV_USE_LOCAL_CAMERA"], "1")
            self.assertEqual(os.environ["AI_CCTV_LOCAL_CAMERA_INDEX"], "2")
            for name in names:
                self.assertNotIn(name, os.environ)
        finally:
            for name, value in original.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value
            os.environ.pop("AI_CCTV_USE_LOCAL_CAMERA", None)
            os.environ.pop("AI_CCTV_LOCAL_CAMERA_INDEX", None)

    def test_runtime_readiness_report_finds_missing_required_items(self):
        """런타임 준비 상태 결과가 누락된 필수 항목을 구분하는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        requirement = RuntimeRequirement(
            name="missing",
            kind="package",
            import_name="missing_package",
            install_spec="missing-package",
        )
        report = RuntimeReadinessReport(
            results=(RuntimeRequirementResult(requirement, False, "없음"),)
        )

        self.assertFalse(report.is_ready())
        self.assertEqual(report.missing_required()[0].requirement.name, "missing")

    def test_runtime_requirements_follow_selected_features(self):
        """시작/분석 요구사항이 선택한 기능에 맞게 분리되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        local_startup_names = {
            requirement.name
            for requirement in build_startup_requirements(use_edge_node=False)
        }
        yolo_names = {
            requirement.name
            for requirement in build_analysis_requirements(use_yolo=True, use_vlm=False)
        }

        self.assertIn("OpenCV", local_startup_names)
        self.assertNotIn("paho-mqtt", local_startup_names)
        self.assertIn("YOLO 모델", yolo_names)
        self.assertNotIn("Qwen VLM 모델", yolo_names)
        self.assertNotIn("InsightFace", yolo_names)

    def test_test_tools_are_separated_from_runtime_modules(self):
        """테스트 보조 도구가 production 경로와 루트 경로를 오염시키지 않는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.assertFalse(Path("test_mqtt.py").exists())
        self.assertFalse(Path("tests").exists())
        self.assertFalse(Path("tools").exists())
        self.assertTrue(Path("tester/tools/mock_edge_mqtt_publisher.py").is_file())
        self.assertTrue(Path("tester/README.md").is_file())
        self.assertTrue(Path("tester/tests/test_project_structure.py").is_file())
        self.assertTrue(Path("tester/pseudo_edge_node/main.py").is_file())
        self.assertFalse(Path("src/ai_cctv/pseudo_edge_node").exists())
        self.assertFalse(
            Path(
                "src/ai_cctv/ai_server/analysis/vlm_person_analyzer_qwen_test.py"
            ).exists()
        )
        self.assertTrue(
            Path("src/ai_cctv/ai_server/analysis/qwen_person_analyzer.py").is_file()
        )


if __name__ == "__main__":
    unittest.main()
