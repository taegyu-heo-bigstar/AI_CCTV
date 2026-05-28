# Raspberry Pi 장애 대응 모듈 호환 파일입니다.
# 실제 구현은 edge_pi.failover 패키지에 있습니다.
# 기존 edge.failover import 경로를 유지하기 위해 재노출합니다.

from ai_cctv.edge_pi.failover import FailoverAction, NetworkFailoverPolicy


__all__ = ["FailoverAction", "NetworkFailoverPolicy"]

