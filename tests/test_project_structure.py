# 문서 기준 구조 보강 모듈의 단위 테스트 파일입니다.
# 서비스와 AI 모델 없이 이상 상황, 알림, 엣지 송출 역할 경계를 검증합니다.
# 종합설계 문서의 핵심 실행 단위가 코드로 유지되는지 확인합니다.

import unittest
import tomllib
from datetime import datetime, timedelta
from pathlib import Path

from ai_cctv.ai_server.alerts.dispatcher import (
    NotificationChannel,
    NotificationDispatcher,
)
from ai_cctv.ai_server.anomaly.detector import (
    AnomalyRuleEngine,
    DwellTimeAnomalyRule,
    ObjectAppearanceRule,
)
from ai_cctv.edge_node.failover import EdgeNetworkFailoverPolicy
from ai_cctv.edge_node.streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder


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

    def test_gstreamer_mediamtx_command_uses_rtsp_destination(self):
        """GStreamer 송출 명령에 MediaMTX RTSP 목적지가 포함되는지 검증합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        config = EdgeStreamConfig(mediamtx_url="rtsp://127.0.0.1:8554/test")
        command = MediaMtxGStreamerCommandBuilder(config).build_command_args()

        self.assertIn("gst-launch-1.0", command)
        self.assertIn("libcamerasrc", command)
        self.assertIn("location=rtsp://127.0.0.1:8554/test", command)

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
            scripts["ai-cctv-ai-server"],
            "ai_cctv.ai_server.main:main",
        )
        self.assertEqual(scripts["ai-cctv"], "ai_cctv.ai_server.main:main")
        self.assertIn("edge-node", extras)
        self.assertIn("ai-server", extras)
        self.assertNotIn("edge-pi", extras)
        self.assertNotIn("windows-server", extras)
        self.assertNotIn("edge", extras)
        self.assertNotIn("ai-cctv-windows-server", scripts)
        self.assertTrue(Path("src/ai_cctv/edge_node").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/client").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/anomaly").is_dir())
        self.assertTrue(Path("src/ai_cctv/ai_server/alerts").is_dir())
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
        self.assertFalse(Path("src/ai_cctv/ai_server/client/legacy_cctv_gui.py").exists())
        self.assertFalse(Path("src/ai_cctv/streaming/legacy_rtsp_receiver.py").exists())
        self.assertFalse(Path("src/ai_cctv/server/fail_over.py").exists())
        self.assertTrue(Path("requirements/edge-node.txt").is_file())
        self.assertTrue(Path("requirements/ai-server.txt").is_file())


if __name__ == "__main__":
    unittest.main()
