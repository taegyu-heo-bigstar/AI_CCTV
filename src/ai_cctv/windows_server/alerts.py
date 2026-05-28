# Windows 서버 Discord 알림 계층 호환 파일입니다.
# 현재 운영 알림 채널인 Discord 디스패처를 Windows 서버 패키지 이름으로 제공합니다.
# 향후 다른 채널은 alerts 패키지에서 확장합니다.

from ai_cctv.alerts.dispatcher import AlertDispatcher, DiscordChatBotChannel
from ai_cctv.alerts.message import AlertMessage


__all__ = ["AlertDispatcher", "AlertMessage", "DiscordChatBotChannel"]

