# Edge node 호환 패키지 파일입니다.
# 실제 Edge node 실행 묶음은 src/ai_cctv/edge_node 패키지에 있습니다.
# 기존 ai_cctv.edge_pi import 경로를 유지하기 위해 공개 객체를 재노출합니다.

from ai_cctv.edge_node.failover import FailoverAction, NetworkFailoverPolicy
from ai_cctv.edge_node.main import build_default_streaming_command, main
from ai_cctv.edge_node.streaming import (
    GStreamerMediaMtxCommandBuilder,
    PiStreamingConfig,
    RpicamMediaMtxCommandBuilder,
)

__all__ = [
    "main",
    "build_default_streaming_command",
    "FailoverAction",
    "NetworkFailoverPolicy",
    "GStreamerMediaMtxCommandBuilder",
    "PiStreamingConfig",
    "RpicamMediaMtxCommandBuilder",
]
