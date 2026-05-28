# AI CCTV 영상 처리 스레드를 정의하는 파일입니다.
# 스트림 읽기, 추적, 녹화, VLM 작업 시작과 종료 흐름을 조정합니다.
# 인물별 세부 처리는 PersonFrameProcessor에 위임합니다.

from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from ..alerts.dispatcher import AlertDispatcher
from ..anomaly.detector import AnomalyDetector
from .crop_manager import CropManager
from .full_body_checker import FullBodyChecker
from .pipeline.person_frame_processor import PersonFrameProcessor
from .person_state_manager import PersonStateManager
from .person_tracker import PersonTracker
from .recording_manager import RecordingManager
from .video_stream import VideoStream
from .vlm_worker import VLMWorker


class VideoWorker(QThread):
    """영상 캡처, 추적, 녹화, 선택적 VLM 분석을 조정합니다.

    인자:
        source: OpenCV VideoCapture에 전달할 입력 소스입니다.
        use_vlm: VLM 분석 사용 여부입니다.
        ai_cctv_path: 녹화 파일 저장 루트 경로입니다.
        original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
    반환값:
        VideoWorker 인스턴스를 반환합니다.
    """

    frame_ready = pyqtSignal(object)
    metrics_ready = pyqtSignal(dict)
    event_ready = pyqtSignal(dict)

    def __init__(
        self,
        source=0,
        use_vlm=False,
        ai_cctv_path="",
        original_segment_seconds=10,
        anomaly_detector=None,
        alert_dispatcher=None,
    ):
        """영상 처리 스레드와 협력 객체를 초기화합니다.

        인자:
            source: OpenCV VideoCapture 입력 소스입니다.
            use_vlm: VLM 분석 사용 여부입니다.
            ai_cctv_path: 녹화 파일 저장 루트 경로입니다.
            original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
            anomaly_detector: 감지 결과를 이상 상황으로 변환하는 객체입니다.
            alert_dispatcher: 이상 상황 알림을 전송하는 객체입니다.
        반환값:
            없음.
        """

        super().__init__()
        self.source = source
        self.running = True
        self.use_vlm = use_vlm

        self.stream = VideoStream(source=self.source)
        self.tracker = PersonTracker(model_path="yolo26s.pt")
        self.full_body_checker = FullBodyChecker()
        self.crop_manager = CropManager()
        self.state_manager = PersonStateManager(disappear_timeout=3.0)
        self.ai_cctv_path = ai_cctv_path
        self.original_segment_seconds = original_segment_seconds
        self.recording_manager = None
        self.anomaly_detector = anomaly_detector or AnomalyDetector()
        self.alert_dispatcher = alert_dispatcher or AlertDispatcher()

        self.vlm_worker = VLMWorker(self.state_manager) if self.use_vlm else None
        self.person_processor = PersonFrameProcessor(
            full_body_checker=self.full_body_checker,
            crop_manager=self.crop_manager,
            state_manager=self.state_manager,
            vlm_worker=self.vlm_worker,
        )

    def run(self):
        """스레드 메인 루프에서 프레임 처리와 신호 발행을 수행합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if not self.stream.open():
            self.event_ready.emit({
                "type": "error",
                "message": "Failed to open video stream",
            })
            return

        if self.ai_cctv_path:
            self.recording_manager = RecordingManager(
                base_dir=self.ai_cctv_path,
                fps=self.stream.get_fps(),
                segment_seconds=self.original_segment_seconds,
            )

        if self.vlm_worker is not None:
            self.vlm_worker.start()

        while self.running:
            ret, frame = self.stream.read()

            if not ret:
                self.event_ready.emit({
                    "type": "error",
                    "message": "Failed to read frame",
                })
                continue

            if self.recording_manager is not None:
                self.recording_manager.write_frame(frame)

            persons = self.tracker.track(frame)
            for person in persons:
                for event in self.person_processor.process(frame, person):
                    self.event_ready.emit(event)

            for anomaly_event in self.anomaly_detector.evaluate(persons):
                self.event_ready.emit(anomaly_event.to_worker_event())
                self.alert_dispatcher.dispatch_anomaly(anomaly_event)

            for removed_id in self.state_manager.remove_disappeared_persons():
                self.event_ready.emit({
                    "type": "disappear",
                    "person_id": removed_id,
                    "time": datetime.now().strftime("%H:%M:%S"),
                })

            self.metrics_ready.emit({
                "current_objects": len(persons),
                "tracked_total": len(self.state_manager.person_states),
            })
            self.frame_ready.emit(frame)

        self._cleanup()

    def stop(self):
        """영상 처리 루프를 중지하고 스레드 종료를 기다립니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False
        self.wait()

    def _cleanup(self):
        """사용 중인 분석 작업자, 녹화기, 영상 스트림을 정리합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.vlm_worker is not None:
            self.vlm_worker.stop()

        if self.recording_manager is not None:
            self.recording_manager.stop_recording()

        self.stream.release()
