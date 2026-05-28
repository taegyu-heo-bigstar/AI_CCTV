# AI CCTV Edge node 실행 패키지입니다.
# Raspberry Pi 카메라 송출과 네트워크 장애 대응 정책을 제공합니다.
# AI 분석과 UI 코드는 Windows 기반 AI server 패키지에 분리합니다.

from .failover import EdgeFailoverDecision, EdgeNetworkFailoverPolicy
from .streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder

__all__ = [
    "EdgeFailoverDecision",
    "EdgeNetworkFailoverPolicy",
    "EdgeStreamConfig",
    "MediaMtxGStreamerCommandBuilder",
]
