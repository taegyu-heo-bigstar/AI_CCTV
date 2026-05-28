# AI CCTV 이상 상황 판정 규칙 파일입니다.
# YOLO 추적 결과를 도메인 이벤트로 변환하는 순수 판정 로직만 포함합니다.
# 외부 알림, UI, 영상 입출력 책임은 포함하지 않습니다.

from datetime import datetime

from .events import AnomalyEvent


class AnomalyDetectionRule:
    """이상 상황 판정 규칙의 공통 인터페이스입니다.

    인자:
        없음.
    반환값:
        AnomalyDetectionRule 인스턴스를 반환합니다.
    """

    def evaluate_detections(self, detections, evaluated_at):
        """감지 결과를 평가하여 이상 상황 이벤트를 반환합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            evaluated_at: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        raise NotImplementedError


class ObjectAppearanceRule(AnomalyDetectionRule):
    """새로운 대상 객체가 등장하면 이상 상황으로 판단합니다.

    인자:
        target_class: 감지 대상 객체 클래스명입니다.
        event_type: 생성할 이상 상황 유형입니다.
    반환값:
        ObjectAppearanceRule 인스턴스를 반환합니다.
    """

    def __init__(self, target_class="person", event_type="object_detected"):
        """객체 등장 규칙을 초기화합니다.

        인자:
            target_class: 감지 대상 객체 클래스명입니다.
            event_type: 생성할 이상 상황 유형입니다.
        반환값:
            없음.
        """

        self.target_class = target_class
        self.event_type = event_type
        self.reported_object_keys = set()

    def evaluate_detections(self, detections, evaluated_at):
        """아직 보고하지 않은 추적 객체를 이상 상황 이벤트로 변환합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            evaluated_at: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        events = []
        for detection in detections:
            if detection.get("class_name") != self.target_class:
                continue

            object_key = self._build_object_key(detection)
            if object_key in self.reported_object_keys:
                continue

            self.reported_object_keys.add(object_key)
            events.append(self._build_event(detection, evaluated_at))

        return events

    def _build_object_key(self, detection):
        """객체 중복 보고를 막기 위한 식별자를 생성합니다.

        인자:
            detection: YOLO 추적 결과 딕셔너리입니다.
        반환값:
            객체 중복 판단용 튜플을 반환합니다.
        """

        return (
            detection.get("class_name"),
            detection.get("track_id") or detection.get("person_id") or detection.get("bbox"),
        )

    def _build_event(self, detection, occurred_at):
        """감지 결과 하나를 이상 상황 이벤트로 변환합니다.

        인자:
            detection: YOLO 추적 결과 딕셔너리입니다.
            occurred_at: 이벤트 발생 시각입니다.
        반환값:
            AnomalyEvent 객체를 반환합니다.
        """

        confidence = float(detection.get("conf", 0.0))
        return AnomalyEvent(
            event_type=self.event_type,
            object_name=self.target_class,
            confidence=confidence,
            occurred_at=occurred_at,
            person_id=detection.get("person_id"),
            message=f"{self.target_class} 객체가 감지되었습니다. 신뢰도: {confidence:.2f}",
            metadata={"bbox": detection.get("bbox")},
        )


class DwellTimeAnomalyRule(AnomalyDetectionRule):
    """객체가 일정 시간 이상 감지되면 이상 상황으로 판단합니다.

    인자:
        target_class: 감지 대상 객체 클래스명입니다.
        dwell_seconds: 이상 상황으로 판단할 체류 시간입니다.
    반환값:
        DwellTimeAnomalyRule 인스턴스를 반환합니다.
    """

    def __init__(self, target_class="person", dwell_seconds=30.0):
        """체류 시간 판정 규칙을 초기화합니다.

        인자:
            target_class: 감지 대상 객체 클래스명입니다.
            dwell_seconds: 이상 상황으로 판단할 체류 시간입니다.
        반환값:
            없음.
        """

        self.target_class = target_class
        self.dwell_seconds = dwell_seconds
        self.first_seen_at_by_key = {}
        self.reported_object_keys = set()

    def evaluate_detections(self, detections, evaluated_at):
        """객체별 체류 시간을 계산하여 기준 초과 이벤트를 생성합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            evaluated_at: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        events = []
        active_object_keys = set()
        for detection in detections:
            if detection.get("class_name") != self.target_class:
                continue

            object_key = self._resolve_object_key(detection)
            active_object_keys.add(object_key)
            self.first_seen_at_by_key.setdefault(object_key, evaluated_at)

            if object_key in self.reported_object_keys:
                continue

            elapsed_seconds = (
                evaluated_at - self.first_seen_at_by_key[object_key]
            ).total_seconds()
            if elapsed_seconds < self.dwell_seconds:
                continue

            self.reported_object_keys.add(object_key)
            events.append(self._build_event(detection, evaluated_at, elapsed_seconds))

        self._forget_missing_objects(active_object_keys)
        return events

    def _resolve_object_key(self, detection):
        """체류 시간을 추적할 객체 식별자를 결정합니다.

        인자:
            detection: YOLO 추적 결과 딕셔너리입니다.
        반환값:
            person_id 또는 bbox 기반 식별자를 반환합니다.
        """

        if detection.get("person_id") is not None:
            return detection.get("person_id")
        return tuple(detection.get("bbox", ()))

    def _build_event(self, detection, occurred_at, elapsed_seconds):
        """체류 시간 초과 감지 결과를 이상 상황 이벤트로 변환합니다.

        인자:
            detection: YOLO 추적 결과 딕셔너리입니다.
            occurred_at: 이벤트 발생 시각입니다.
            elapsed_seconds: 누적 체류 시간입니다.
        반환값:
            AnomalyEvent 객체를 반환합니다.
        """

        confidence = float(detection.get("conf", 0.0))
        return AnomalyEvent(
            event_type="dwell_time_exceeded",
            object_name=self.target_class,
            confidence=confidence,
            occurred_at=occurred_at,
            person_id=detection.get("person_id"),
            message=f"{self.target_class} 객체가 {self.dwell_seconds:.0f}초 이상 감지되었습니다.",
            metadata={
                "bbox": detection.get("bbox"),
                "elapsed_seconds": elapsed_seconds,
            },
        )

    def _forget_missing_objects(self, active_object_keys):
        """현재 프레임에서 사라진 객체의 체류 상태를 정리합니다.

        인자:
            active_object_keys: 현재 프레임에서 감지된 객체 식별자 집합입니다.
        반환값:
            없음.
        """

        for object_key in list(self.first_seen_at_by_key):
            if object_key not in active_object_keys:
                self.first_seen_at_by_key.pop(object_key, None)
                self.reported_object_keys.discard(object_key)


class AnomalyRuleEngine:
    """여러 이상 상황 판정 규칙을 순서대로 실행합니다.

    인자:
        rules: 실행할 이상 상황 판정 규칙 목록입니다.
    반환값:
        AnomalyRuleEngine 인스턴스를 반환합니다.
    """

    def __init__(self, rules=None):
        """이상 상황 판정 규칙 목록을 초기화합니다.

        인자:
            rules: 실행할 이상 상황 판정 규칙 목록입니다.
        반환값:
            없음.
        """

        self.rules = list(rules or [ObjectAppearanceRule(target_class="person")])

    def evaluate_detections(self, detections, evaluated_at=None):
        """감지 결과를 전체 규칙으로 평가합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            evaluated_at: 평가 기준 시각이며 없으면 현재 시각을 사용합니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        evaluation_time = evaluated_at or datetime.now()
        events = []
        for rule in self.rules:
            events.extend(rule.evaluate_detections(detections, evaluation_time))
        return events
