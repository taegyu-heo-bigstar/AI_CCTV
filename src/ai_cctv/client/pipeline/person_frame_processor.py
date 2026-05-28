# 한 프레임 안의 추적 인물을 처리하는 파일입니다.
# 전신 판정, 상태 갱신, crop 저장, VLM 큐 등록, 화면 주석 표시를 담당합니다.
# VideoWorker는 실행 흐름만 조정하고 인물 처리 세부 로직은 이 객체에 위임합니다.

from datetime import datetime

import cv2


class PersonFrameProcessor:
    """추적된 인물 하나에 대한 프레임 처리 책임을 담당합니다.

    인자:
        full_body_checker: 전신 노출 여부를 판정하는 객체입니다.
        crop_manager: 인물 crop 이미지를 저장하는 객체입니다.
        state_manager: 인물별 상태를 관리하는 객체입니다.
        vlm_worker: VLM 분석 작업을 처리하는 작업자입니다.
    반환값:
        PersonFrameProcessor 인스턴스를 반환합니다.
    """

    def __init__(self, full_body_checker, crop_manager, state_manager, vlm_worker):
        """인물 처리에 필요한 협력 객체를 주입합니다.

        인자:
            full_body_checker: 전신 판정 객체입니다.
            crop_manager: crop 저장 객체입니다.
            state_manager: 인물 상태 저장 객체입니다.
            vlm_worker: VLM 작업자이며 비활성화 시 None입니다.
        반환값:
            없음.
        """

        self.full_body_checker = full_body_checker
        self.crop_manager = crop_manager
        self.state_manager = state_manager
        self.vlm_worker = vlm_worker

    def process(self, frame, person):
        """추적 인물 상태를 갱신하고 필요한 화면 주석을 그립니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
            person: 추적 결과 딕셔너리입니다.
        반환값:
            발생한 이벤트 딕셔너리 목록을 반환합니다.
        """

        person_id = person["person_id"]
        bbox = person["bbox"]
        conf = person["conf"]
        x1, y1, x2, y2 = map(int, bbox)

        is_full_body = self.full_body_checker.is_full_body_visible(bbox, frame.shape)
        self.state_manager.update_person(
            person_id=person_id,
            bbox=bbox,
            is_full_body=is_full_body,
        )

        events = []
        if self._should_queue_vlm(person_id, is_full_body):
            events.extend(self._queue_vlm(frame, bbox, person_id))

        self._draw_annotation(frame, bbox, conf, person_id, is_full_body)
        return events

    def _should_queue_vlm(self, person_id, is_full_body):
        """VLM 분석 큐 등록 가능 여부를 판단합니다.

        인자:
            person_id: 추적 인물 식별자입니다.
            is_full_body: 전신 노출 여부입니다.
        반환값:
            큐 등록 조건을 만족하면 True, 아니면 False를 반환합니다.
        """

        return (
            self.vlm_worker is not None
            and is_full_body
            and not self.state_manager.has_crop_saved(person_id)
        )

    def _queue_vlm(self, frame, bbox, person_id):
        """전신 crop을 저장하고 VLM 작업 큐에 등록합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
            bbox: 인물 바운딩 박스입니다.
            person_id: 추적 인물 식별자입니다.
        반환값:
            VLM 큐 등록 이벤트 목록을 반환합니다.
        """

        crop_path = self.crop_manager.save_crop(
            frame=frame,
            bbox=bbox,
            person_id=person_id,
        )
        if crop_path is None:
            return []

        self.state_manager.mark_crop_saved(person_id, crop_path)
        self.vlm_worker.add_task(person_id, crop_path)
        return [self._build_event("vlm_queue", person_id)]

    def _draw_annotation(self, frame, bbox, conf, person_id, is_full_body):
        """프레임 위에 추적 박스와 라벨을 그립니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
            bbox: 인물 바운딩 박스입니다.
            conf: 탐지 신뢰도입니다.
            person_id: 추적 인물 식별자입니다.
            is_full_body: 전신 노출 여부입니다.
        반환값:
            없음.
        """

        x1, y1, x2, y2 = map(int, bbox)
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

    def _build_event(self, event_type, person_id):
        """인물 이벤트 딕셔너리를 생성합니다.

        인자:
            event_type: 이벤트 유형 문자열입니다.
            person_id: 추적 인물 식별자입니다.
        반환값:
            이벤트 딕셔너리를 반환합니다.
        """

        return {
            "type": event_type,
            "person_id": person_id,
            "time": datetime.now().strftime("%H:%M:%S"),
        }
