# AI server 실행 패키지 파일입니다.
# GUI 분석 실행, 이상 상황 판단, Discord 알림 연결 객체를 공개합니다.
# Edge node 송출 코드와 분리된 서버 측 배포 단위입니다.

"""AI 서버 실행 패키지입니다."""

from .analysis import AnomalyDetector, DwellTimeRule, ObjectPresenceRule, VideoWorker
from .alerts import AlertDispatcher, AlertMessage, DiscordChatBotChannel
from .main import main

__all__ = [
    "main",
    "AnomalyDetector",
    "DwellTimeRule",
    "ObjectPresenceRule",
    "VideoWorker",
    "AlertDispatcher",
    "AlertMessage",
    "DiscordChatBotChannel",
]
