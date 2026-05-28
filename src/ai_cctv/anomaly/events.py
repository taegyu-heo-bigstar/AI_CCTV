# AI CCTV 이상 상황 이벤트 값 객체 파일입니다.
# 감지 객체, 신뢰도, 발생 시각, 메시지 등 알림에 필요한 정보를 담습니다.
# 탐지 파이프라인과 알림 채널이 같은 이벤트 형식을 사용하게 합니다.

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class AnomalyEvent:
    """이상 상황 이벤트 정보를 표현합니다.

    인자:
        event_type: 이상 상황 유형입니다.
        object_name: 감지된 객체 이름입니다.
        confidence: 객체 감지 신뢰도입니다.
        occurred_at: 이상 상황 발생 시각입니다.
        message: 사용자에게 전달할 설명 문구입니다.
        person_id: 추적 인물 식별자입니다.
        image_path: 이벤트 이미지 경로입니다.
        metadata: 추가 이벤트 정보 딕셔너리입니다.
    반환값:
        AnomalyEvent 인스턴스를 반환합니다.
    """

    event_type: str
    object_name: str
    confidence: float
    occurred_at: datetime
    message: str
    person_id: int | None = None
    image_path: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_worker_event(self):
        """PyQt VideoWorker 신호로 전달할 이벤트 딕셔너리를 생성합니다.

        인자:
            없음.
        반환값:
            UI와 알림 계층에서 사용할 이벤트 딕셔너리를 반환합니다.
        """

        return {
            "type": "anomaly",
            "event_type": self.event_type,
            "object_name": self.object_name,
            "confidence": self.confidence,
            "person_id": self.person_id,
            "image_path": self.image_path,
            "message": self.message,
            "time": self.occurred_at.strftime("%H:%M:%S"),
            "occurred_at": self.occurred_at.isoformat(),
            "metadata": self.metadata,
        }

