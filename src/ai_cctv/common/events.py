# AI CCTV 공통 이벤트 재노출 파일입니다.
# 여러 계층이 같은 이상 상황 이벤트 값 객체를 참조할 수 있게 공개합니다.
# 실제 이벤트 정의는 ai_cctv.anomaly.events에 둡니다.

from ai_cctv.anomaly.events import AnomalyEvent


__all__ = ["AnomalyEvent"]
