# AI server 실행 패키지 파일입니다.
# GUI 분석 실행, 이상 상황 판정, Discord 알림 연결 객체를 공개합니다.
# Edge node 송출 코드는 분리된 배포 단위로 유지합니다.

"""AI 서버 실행 패키지입니다."""

from .alerts import (
    DiscordNotificationChannel,
    NotificationDispatcher,
    NotificationMessage,
)
from .analysis import (
    AnomalyRuleEngine,
    DwellTimeAnomalyRule,
    ObjectAppearanceRule,
    VideoWorker,
)
from .main import main

__all__ = [
    "main",
    "AnomalyRuleEngine",
    "DwellTimeAnomalyRule",
    "ObjectAppearanceRule",
    "VideoWorker",
    "DiscordNotificationChannel",
    "NotificationDispatcher",
    "NotificationMessage",
]
