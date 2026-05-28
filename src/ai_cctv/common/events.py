# AI CCTV 공통 이벤트 타입 파일입니다.
# Windows 서버의 이상 상황 판단 결과와 알림 계층이 같은 이벤트 형식을 공유합니다.
# 기존 anomaly.events 모듈과의 호환성을 유지합니다.

from ai_cctv.anomaly.events import AnomalyEvent


__all__ = ["AnomalyEvent"]

