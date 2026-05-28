# AI CCTV 공통 메시지 재노출 파일입니다.
# 여러 계층이 같은 알림 메시지 값 객체를 참조할 수 있게 공개합니다.
# 실제 메시지 생성 로직은 ai_cctv.ai_server.alerts.message에 둡니다.

from ..alerts.message import NotificationMessage


__all__ = ["NotificationMessage"]
