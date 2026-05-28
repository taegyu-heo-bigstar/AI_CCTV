# AI CCTV 공통 메시지 타입 파일입니다.
# 이상 상황 이벤트를 알림 채널로 전달할 메시지 형식으로 변환합니다.
# 기존 alerts.message 모듈과의 호환성을 유지합니다.

from ai_cctv.alerts.message import AlertMessage


__all__ = ["AlertMessage"]

