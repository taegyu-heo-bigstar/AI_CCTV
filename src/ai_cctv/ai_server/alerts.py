# AI server 알림 계층 재노출 파일입니다.
# Discord 중심 알림 디스패처와 메시지 객체를 서버 실행 묶음에서 사용할 수 있게 모읍니다.
# 실제 전송 구현은 ai_cctv.alerts에 두어 서버 진입점과 분리합니다.

"""AI 서버 알림 계층 재노출 모듈입니다."""

from ai_cctv.alerts.dispatcher import (
    DiscordNotificationChannel,
    NotificationDispatcher,
)
from ai_cctv.alerts.message import NotificationMessage

__all__ = [
    "DiscordNotificationChannel",
    "NotificationDispatcher",
    "NotificationMessage",
]
