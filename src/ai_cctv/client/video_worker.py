from datetime import datetime

import cv2
from PyQt5.QtCore import QThread, pyqtSignal

from .crop_manager import CropManager
from .full_body_checker import FullBodyChecker
from .person_state_manager import PersonStateManager
from .person_tracker import PersonTracker
from .recording_manager import RecordingManager
from .video_stream import VideoStream
from .vlm_worker import VLMWorker


class VideoWorker(QThread):
    """Coordinates capture, detection, recording, and optional VLM analysis."""

    frame_ready = pyqtSignal(object)
    metrics_ready = pyqtSignal(dict)
    event_ready = pyqtSignal(dict)

    def __init__(
        self,
        source=0,
        use_vlm=False,
        ai_cctv_path="",
        original_segment_seconds=10,
    ):
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

        self.vlm_worker = VLMWorker(self.state_manager) if self.use_vlm else None

    def run(self):
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
                self._handle_person(frame, person)

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
        self.running = False
        self.wait()

    def _handle_person(self, frame, person):
        person_id = person["person_id"]
        bbox = person["bbox"]
        conf = person["conf"]
        x1, y1, x2, y2 = map(int, bbox)

        is_full_body = self.full_body_checker.is_full_body_visible(
            bbox,
            frame.shape,
        )
        self.state_manager.update_person(
            person_id=person_id,
            bbox=bbox,
            is_full_body=is_full_body,
        )

        if self._should_queue_vlm(person_id, is_full_body):
            crop_path = self.crop_manager.save_crop(
                frame=frame,
                bbox=bbox,
                person_id=person_id,
            )
            if crop_path is not None:
                self.state_manager.mark_crop_saved(person_id, crop_path)
                self.vlm_worker.add_task(person_id, crop_path)
                self.event_ready.emit({
                    "type": "vlm_queue",
                    "person_id": person_id,
                    "time": datetime.now().strftime("%H:%M:%S"),
                })

        status = self.full_body_checker.get_status_text(bbox, frame.shape)
        color = (0, 255, 0) if is_full_body else (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        state = self.state_manager.get_state(person_id)
        vlm_text = " VLM_DONE" if state and state.get("vlm_done", False) else ""
        label = f"ID:{person_id} {status} {conf:.2f}{vlm_text}"
        cv2.putText(
            frame,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
        )

    def _should_queue_vlm(self, person_id, is_full_body):
        return (
            self.vlm_worker is not None
            and is_full_body
            and not self.state_manager.has_crop_saved(person_id)
        )

    def _cleanup(self):
        if self.vlm_worker is not None:
            self.vlm_worker.stop()

        if self.recording_manager is not None:
            self.recording_manager.stop_recording()

        self.stream.release()
