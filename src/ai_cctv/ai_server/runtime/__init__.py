# AI server 실행 전 런타임 환경을 점검하는 패키지입니다.
# OS 지원 여부, Python 패키지, 모델 파일과 캐시 상태를 확인합니다.
# UI는 이 패키지의 점검 결과를 보고 자동 설치 여부를 사용자에게 묻습니다.

from .bootstrap import ensure_pyqt5_available
from .environment_check import (
    RuntimeEnvironmentChecker,
    RuntimeInstaller,
    RuntimeRequirement,
    RuntimeRequirementResult,
    RuntimeReadinessReport,
    build_analysis_requirements,
    build_startup_requirements,
)
from .os_guard import ensure_windows_os, is_windows_os

__all__ = [
    "RuntimeEnvironmentChecker",
    "RuntimeInstaller",
    "RuntimeRequirement",
    "RuntimeRequirementResult",
    "RuntimeReadinessReport",
    "build_analysis_requirements",
    "build_startup_requirements",
    "ensure_pyqt5_available",
    "ensure_windows_os",
    "is_windows_os",
]
