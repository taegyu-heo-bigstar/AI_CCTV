# AI CCTV 이상 상황 판정 패키지입니다.
# 객체 감지 결과를 프로젝트 기준의 이상 상황 이벤트로 변환합니다.
# 영상 입출력과 알림 전송 책임은 다른 패키지에 둡니다.

from .detector import AnomalyRuleEngine, DwellTimeAnomalyRule, ObjectAppearanceRule
from .events import AnomalyEvent

__all__ = [
    "AnomalyEvent",
    "AnomalyRuleEngine",
    "DwellTimeAnomalyRule",
    "ObjectAppearanceRule",
]
