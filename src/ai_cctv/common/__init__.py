# AI CCTV 공통 값 객체 패키지입니다.
# Edge node와 AI server가 함께 참조할 수 있는 이벤트와 메시지를 공개합니다.
# 실행 로직은 edge_node와 ai_server 패키지에 분리합니다.

from .events import AnomalyEvent
from .messages import NotificationMessage

__all__ = [
    "AnomalyEvent",
    "NotificationMessage",
]
