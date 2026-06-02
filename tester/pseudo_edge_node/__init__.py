# Windows 테스트용 pseudo Edge node 패키지입니다.
# 실제 Raspberry Pi, GStreamer, MediaMTX, UPS 하드웨어 없이 Edge node 계약을 흉내 냅니다.
# RTSP 포트, MQTT 상태 broker, 백업 복구 HTTP API를 한 실행체에서 제공합니다.
# AI server는 이 패키지의 표준 출력값을 붙여넣어 Edge node 모드 테스트를 진행할 수 있습니다.

from .config import PseudoEdgeNodeConfig
from .runtime import PseudoEdgeNodeRuntime

__all__ = [
    "PseudoEdgeNodeConfig",
    "PseudoEdgeNodeRuntime",
]
