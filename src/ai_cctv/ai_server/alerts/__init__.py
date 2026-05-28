# AI CCTV Discord 알림 패키지입니다.
# 이상 상황 이벤트를 Discord로 전달하는 메시지와 디스패처를 제공합니다.
# 다른 알림 방식은 향후 확장 지점이며 현재 실행 책임에는 포함하지 않습니다.

from .dispatcher import DiscordNotificationChannel, NotificationChannel, NotificationDispatcher
from .message import NotificationMessage

__all__ = [
    "DiscordNotificationChannel",
    "NotificationChannel",
    "NotificationDispatcher",
    "NotificationMessage",
]
