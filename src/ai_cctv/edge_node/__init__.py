# AI CCTV Edge node 실행 패키지입니다.
# Raspberry Pi 카메라 송출, MediaMTX 실행, 로컬 백업 정책을 제공합니다.
# AI 분석과 UI 코드는 Windows 기반 AI server 패키지에 분리합니다.

from .failover import EdgeFailoverDecision, EdgeNetworkFailoverPolicy
from .local_backup import LocalBackupConfig
from .mediamtx import MediaMtxConfig, MediaMtxInstaller, MediaMtxProcessManager
from .runtime import EdgeNodeRuntime
from .streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder
from .backup_recovery_server import BackupRecoveryService, BackupSegmentFinder

__all__ = [
    "EdgeFailoverDecision",
    "EdgeNetworkFailoverPolicy",
    "EdgeNodeRuntime",
    "EdgeStreamConfig",
    "BackupRecoveryService",
    "BackupSegmentFinder",
    "LocalBackupConfig",
    "MediaMtxGStreamerCommandBuilder",
    "MediaMtxConfig",
    "MediaMtxInstaller",
    "MediaMtxProcessManager",
]
