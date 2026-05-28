# Edge node 장애 대응 호환 파일입니다.
# 실제 장애 대응 정책은 src/ai_cctv/edge_node/failover.py에 있습니다.
# 기존 ai_cctv.edge_pi.failover import 경로를 유지합니다.

from ai_cctv.edge_node.failover import FailoverAction, NetworkFailoverPolicy

__all__ = ["FailoverAction", "NetworkFailoverPolicy"]
