# AI CCTV 이상 상황 판단 규칙 파일입니다.
# YOLO 추적 결과를 사람 감지, 체류 시간 등 이벤트 조건으로 평가합니다.
# 규칙 객체를 조합하여 문서 기준의 이상 상황 판단 계층을 구성합니다.

from datetime import datetime

from .events import AnomalyEvent


class AnomalyRule:
    """이상 상황 판단 규칙의 공통 인터페이스입니다.

    인자:
        없음.
    반환값:
        AnomalyRule 인스턴스를 반환합니다.
    """

    def evaluate(self, detections, now):
        """감지 결과를 평가하여 이상 상황 이벤트를 반환합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            now: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        raise NotImplementedError


class ObjectPresenceRule(AnomalyRule):
    """특정 객체가 새로 감지되면 이상 상황으로 판단합니다.

    인자:
        target_class: 감지 대상 객체 클래스명입니다.
        event_type: 생성할 이상 상황 유형입니다.
    반환값:
        ObjectPresenceRule 인스턴스를 반환합니다.
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
        self.seen_object_keys = set()

    def evaluate(self, detections, now):
        """새로운 객체 추적 ID를 이상 상황 이벤트로 변환합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            now: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        events = []
        for detection in detections:
            if detection.get("class_name") != self.target_class:
                continue

            object_key = self._build_object_key(detection)
            if object_key in self.seen_object_keys:
                continue

            self.seen_object_keys.add(object_key)
            confidence = float(detection.get("conf", 0.0))
            person_id = detection.get("person_id")
            events.append(
                AnomalyEvent(
                    event_type=self.event_type,
                    object_name=self.target_class,
                    confidence=confidence,
                    occurred_at=now,
                    person_id=person_id,
                    message=(
                        f"{self.target_class} 객체가 감지되었습니다. "
                        f"신뢰도: {confidence:.2f}"
                    ),
                    metadata={"bbox": detection.get("bbox")},
                )
            )

        return events

    def _build_object_key(self, detection):
        """감지 객체를 중복 판단하기 위한 식별자를 생성합니다.

        인자:
            detection: YOLO 추적 결과 딕셔너리입니다.
        반환값:
            객체 중복 판단용 튜플을 반환합니다.
        """

        return (
            detection.get("class_name"),
            detection.get("person_id"),
            detection.get("bbox"),
        )


class DwellTimeRule(AnomalyRule):
    """객체가 일정 시간 이상 감지되면 이상 상황으로 판단합니다.

    인자:
        target_class: 감지 대상 객체 클래스명입니다.
        dwell_seconds: 이상 상황으로 판단할 체류 시간입니다.
    반환값:
        DwellTimeRule 인스턴스를 반환합니다.
    """

    def __init__(self, target_class="person", dwell_seconds=30.0):
        """체류 시간 판단 규칙을 초기화합니다.

        인자:
            target_class: 감지 대상 객체 클래스명입니다.
            dwell_seconds: 이상 상황으로 판단할 체류 시간입니다.
        반환값:
            없음.
        """

        self.target_class = target_class
        self.dwell_seconds = dwell_seconds
        self.first_seen_at = {}
        self.reported_keys = set()

    def evaluate(self, detections, now):
        """객체별 체류 시간을 계산하여 이상 상황 이벤트를 생성합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            now: 평가 기준 시각입니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        events = []
        active_keys = set()
        for detection in detections:
            if detection.get("class_name") != self.target_class:
                continue

            object_key = detection.get("person_id")
            if object_key is None:
                object_key = tuple(detection.get("bbox", ()))
            active_keys.add(object_key)

            self.first_seen_at.setdefault(object_key, now)
            if object_key in self.reported_keys:
                continue

            elapsed = (now - self.first_seen_at[object_key]).total_seconds()
            if elapsed < self.dwell_seconds:
                continue

            self.reported_keys.add(object_key)
            confidence = float(detection.get("conf", 0.0))
            events.append(
                AnomalyEvent(
                    event_type="dwell_time_exceeded",
                    object_name=self.target_class,
                    confidence=confidence,
                    occurred_at=now,
                    person_id=detection.get("person_id"),
                    message=(
                        f"{self.target_class} 객체가 "
                        f"{self.dwell_seconds:.0f}초 이상 감지되었습니다."
                    ),
                    metadata={
                        "bbox": detection.get("bbox"),
                        "elapsed_seconds": elapsed,
                    },
                )
            )

        self._forget_missing_objects(active_keys)
        return events

    def _forget_missing_objects(self, active_keys):
        """현재 프레임에서 사라진 객체의 체류 상태를 정리합니다.

        인자:
            active_keys: 현재 프레임에서 감지된 객체 식별자 집합입니다.
        반환값:
            없음.
        """

        for object_key in list(self.first_seen_at):
            if object_key not in active_keys:
                self.first_seen_at.pop(object_key, None)
                self.reported_keys.discard(object_key)


class AnomalyDetector:
    """여러 이상 상황 판단 규칙을 실행하는 조정자입니다.

    인자:
        rules: 실행할 이상 상황 판단 규칙 목록입니다.
    반환값:
        AnomalyDetector 인스턴스를 반환합니다.
    """

    def __init__(self, rules=None):
        """이상 상황 판단 규칙 목록을 초기화합니다.

        인자:
            rules: 실행할 이상 상황 판단 규칙 목록입니다.
        반환값:
            없음.
        """

        self.rules = list(rules or [ObjectPresenceRule(target_class="person")])

    def evaluate(self, detections, now=None):
        """감지 결과를 전체 규칙으로 평가합니다.

        인자:
            detections: YOLO 추적 결과 딕셔너리 목록입니다.
            now: 평가 기준 시각이며 없으면 현재 시각을 사용합니다.
        반환값:
            AnomalyEvent 목록을 반환합니다.
        """

        evaluated_at = now or datetime.now()
        events = []
        for rule in self.rules:
            events.extend(rule.evaluate(detections, evaluated_at))
        return events

