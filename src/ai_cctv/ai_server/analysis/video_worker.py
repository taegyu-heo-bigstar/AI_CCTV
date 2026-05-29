# AI CCTV 영상 처리 스레드를 정의하는 파일입니다.
# 스트림 읽기, 추적, 녹화, VLM 작업 시작과 종료 흐름을 조정합니다.
# 카메라 프리뷰를 먼저 표시하고 AI 모델은 별도 thread에서 준비합니다.

import threading
from datetime import datetime
from PyQt5.QtCore import QThread, pyqtSignal

from ..alerts.dispatcher import DiscordNotificationChannel, NotificationDispatcher
from .anomaly.detector import AnomalyRuleEngine
from .crop_manager import CropManager
from .full_body_checker import FullBodyChecker
from .pipeline.person_frame_processor import PersonFrameProcessor
from .person_state_manager import PersonStateManager
from ..storage.clip_manager import ClipManager
from ..storage.recording_manager import RecordingManager
from .video_stream import VideoStream


class VideoWorker(QThread):
    """영상 캡처, 추적, 녹화, 선택적 VLM 분석을 조정합니다.

    인자:
        source: OpenCV VideoCapture에 전달할 입력 소스입니다.
        use_vlm: VLM 분석 사용 여부입니다.
        ai_cctv_path: 녹화 파일 저장 루트 경로입니다.
        original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
        clip_max_seconds: 이벤트 클립 파일 하나의 최대 길이 초 단위입니다.
    반환값:
        VideoWorker 인스턴스를 반환합니다.
    """

    frame_ready = pyqtSignal(object)
    metrics_ready = pyqtSignal(dict)
    event_ready = pyqtSignal(dict)
    loading_ready = pyqtSignal(str)

    def __init__(
        self,
        source=0,
        use_vlm=False,
        ai_cctv_path="",
        original_segment_seconds=10,
        clip_max_seconds=10,
        tracker_model_path="yolo26s.pt",
        anomaly_rule_engine=None,
        notification_dispatcher=None,
    ):
        """영상 처리 스레드와 협력 객체를 초기화합니다.

        인자:
            source: OpenCV VideoCapture 입력 소스입니다.
            use_vlm: VLM 분석 사용 여부입니다.
            ai_cctv_path: 녹화 파일 저장 루트 경로입니다.
            original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
            clip_max_seconds: 이벤트 클립 파일 하나의 최대 길이 초 단위입니다.
            tracker_model_path: YOLO 추적 모델 파일 경로입니다.
            anomaly_rule_engine: 감지 결과를 이상 상황으로 변환하는 규칙 엔진입니다.
            notification_dispatcher: 이상 상황 알림을 전송하는 디스패처입니다.
        반환값:
            없음.
        """

        super().__init__()
        self.source = source
        self.running = True
        self.use_vlm = use_vlm
        self.tracker_model_path = tracker_model_path

        self.stream = VideoStream(source=self.source)
        self.tracker = None
        self.tracker_load_error = None
        self.tracker_thread = None
        self.tracker_lock = threading.Lock()
        self.full_body_checker = FullBodyChecker()
        self.crop_manager = CropManager()
        self.state_manager = PersonStateManager(disappear_timeout=3.0)
        self.ai_cctv_path = ai_cctv_path
        self.original_segment_seconds = original_segment_seconds
        self.recording_manager = None
        self.clip_max_seconds = clip_max_seconds
        self.clip_manager = None
        self.anomaly_rule_engine = anomaly_rule_engine or AnomalyRuleEngine()
        self.notification_dispatcher = (
            notification_dispatcher or self._create_default_notification_dispatcher()
        )

        self.vlm_worker = None
        self.vlm_load_error = None
        self.vlm_thread = None
        self.vlm_lock = threading.Lock()
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

        self.loading_ready.emit("영상 스트림 연결 중...")
        if not self.stream.open():
            self.event_ready.emit({
                "type": "error",
                "message": "Failed to open video stream",
            })
            return

        if self.ai_cctv_path:
            fps = self.stream.get_fps()
            self.recording_manager = RecordingManager(
                base_dir=self.ai_cctv_path,
                fps=fps,
                segment_seconds=self.original_segment_seconds,
            )
            self.clip_manager = ClipManager(
                base_dir=self.ai_cctv_path,
                fps=fps,
                max_clip_seconds=self.clip_max_seconds,
                disappear_timeout=self.state_manager.disappear_timeout,
            )

        self.loading_ready.emit("실시간 화면 준비 중...")
        self._start_tracker_loading()
        if self.use_vlm:
            self._start_vlm_loading()

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

            tracker = self._get_tracker()
            if tracker is None:
                self._emit_preview_frame(frame)
                continue

            persons = tracker.track(frame)
            clip_frame = frame.copy() if self.clip_manager is not None else None
            for person in persons:
                for event in self.person_processor.process(frame, person):
                    self.event_ready.emit(event)
                self._record_person_clip(person, clip_frame)

            for anomaly_event in self.anomaly_rule_engine.evaluate_detections(persons):
                self.event_ready.emit(anomaly_event.to_worker_event())
                self.notification_dispatcher.dispatch_anomaly_event(anomaly_event)

            for removed_id in self.state_manager.remove_disappeared_persons():
                if self.clip_manager is not None:
                    self.clip_manager.finish_person(removed_id)
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

    def _start_tracker_loading(self):
        """YOLO 추적 모델을 별도 thread에서 비동기로 로드합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.tracker_thread is not None and self.tracker_thread.is_alive():
            return

        self.event_ready.emit({
            "type": "status",
            "message": "AI 모델 로딩 중입니다. 먼저 영상 미리보기를 표시합니다.",
        })
        self.loading_ready.emit("AI 모델 로딩 중...")
        self.tracker_thread = threading.Thread(
            target=self._load_tracker,
            name="PersonTrackerLoader",
            daemon=True,
        )
        self.tracker_thread.start()

    def _load_tracker(self):
        """YOLO 추적 모델을 로드하고 준비되면 분석 루프에 연결합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            from .person_tracker import PersonTracker

            tracker = PersonTracker(model_path=self.tracker_model_path)
        except Exception as exc:
            self.tracker_load_error = exc
            self.event_ready.emit({
                "type": "error",
                "message": f"AI 모델 로딩 실패: {exc}",
            })
            return

        with self.tracker_lock:
            if not self.running:
                return
            self.tracker = tracker

        self.event_ready.emit({
            "type": "status",
            "message": "AI 모델 로딩 완료. 분석을 시작합니다.",
        })

    def _record_person_clip(self, person, frame):
        """추적 인물의 이벤트 클립 저장을 ClipManager에 위임합니다.

        인자:
            person: 추적 결과 딕셔너리입니다.
            frame: 주석이 그려지기 전 OpenCV BGR 프레임입니다.
        반환값:
            없음.
        """

        if self.clip_manager is None:
            return

        person_id = person["person_id"]
        state = self.state_manager.get_state(person_id)
        crop_path = state.get("crop_path") if state is not None else None
        self.clip_manager.update_person(
            person_id=person_id,
            frame=frame,
            bbox=person["bbox"],
            crop_path=crop_path,
        )

    def _get_tracker(self):
        """현재 사용할 수 있는 YOLO 추적 모델을 반환합니다.

        인자:
            없음.
        반환값:
            로딩 완료된 PersonTracker 객체 또는 None을 반환합니다.
        """

        with self.tracker_lock:
            return self.tracker

    def _start_vlm_loading(self):
        """VLM 작업자를 별도 thread에서 준비합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.vlm_thread is not None and self.vlm_thread.is_alive():
            return

        self.vlm_thread = threading.Thread(
            target=self._load_vlm_worker,
            name="VLMWorkerLoader",
            daemon=True,
        )
        self.vlm_thread.start()

    def _load_vlm_worker(self):
        """VLM 작업자를 생성하고 인물 처리 파이프라인에 연결합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            from .vlm_worker import VLMWorker

            vlm_worker = VLMWorker(self.state_manager)
            vlm_worker.start()
        except Exception as exc:
            self.vlm_load_error = exc
            self.event_ready.emit({
                "type": "error",
                "message": f"VLM 작업자 준비 실패: {exc}",
            })
            return

        with self.vlm_lock:
            if not self.running:
                vlm_worker.stop()
                return
            self.vlm_worker = vlm_worker
            self.person_processor.vlm_worker = vlm_worker

        self.event_ready.emit({
            "type": "status",
            "message": "VLM 작업자 준비를 시작했습니다.",
        })

    def _emit_preview_frame(self, frame):
        """AI 모델 준비 전 프리뷰 프레임과 기본 지표를 발행합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            없음.
        """

        self.metrics_ready.emit({
            "current_objects": 0,
            "tracked_total": len(self.state_manager.person_states),
        })
        self.frame_ready.emit(frame)

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

        if self.clip_manager is not None:
            self.clip_manager.finish_all()

        self._join_loader_threads()
        self.stream.release()

    def _join_loader_threads(self):
        """모델 로더 thread가 짧은 시간 안에 끝나면 정리합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        for loader_thread in [self.tracker_thread, self.vlm_thread]:
            if loader_thread is not None and loader_thread.is_alive():
                loader_thread.join(timeout=1)

    def _create_default_notification_dispatcher(self):
        """기본 Discord 이상 상황 알림 디스패처를 생성합니다.

        인자:
            없음.
        반환값:
            Discord 채널이 등록된 NotificationDispatcher 객체를 반환합니다.
        """

        from ..alerts.chat_bot import chat_bot as chatbot

        return NotificationDispatcher([DiscordNotificationChannel(chatbot)])
