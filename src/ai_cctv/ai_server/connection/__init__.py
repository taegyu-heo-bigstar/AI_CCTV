# AI server와 Edge node 연결 설정 패키지입니다.
# UI가 입력받은 RTSP, MQTT, 백업 복구 주소를 검증하는 객체를 노출합니다.
# 실행 진입점은 이 패키지를 통해 메인 관제 창 시작 전 연결 성공 여부를 확인합니다.

from .edge_connection import (
    EdgeConnectionConfig,
    EdgeConnectionValidationResult,
    EdgeConnectionValidator,
    parse_edge_startup_text,
)

__all__ = [
    "EdgeConnectionConfig",
    "EdgeConnectionValidationResult",
    "EdgeConnectionValidator",
    "parse_edge_startup_text",
]
