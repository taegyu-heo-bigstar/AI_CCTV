# 라즈베리파이 자원 상태 수집 파일입니다.
# 전체 CPU/메모리 사용률과 감시 대상 프로세스의 CPU/메모리 사용률을 수집합니다.
# 감시 대상 PID가 없으면 gst-launch-1.0 프로세스를 찾고, 없으면 현재 API 프로세스를 사용합니다.

import os

import psutil


DEFAULT_PROCESS_NAME = "gst-launch-1.0"


class ResourceStatusCollector:
    """엣지 노드 시스템과 특정 프로세스의 자원 사용률을 수집합니다.

    인자:
        process_id: 모니터링할 프로세스 ID입니다.
        process_name: PID가 없을 때 찾을 프로세스 이름입니다.
        sample_interval_seconds: CPU 사용률 샘플링 시간입니다.
    반환값:
        ResourceStatusCollector 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        process_id=None,
        process_name=DEFAULT_PROCESS_NAME,
        sample_interval_seconds=0.1,
    ):
        """자원 상태 수집 설정을 초기화합니다.

        인자:
            process_id: 모니터링할 프로세스 ID입니다.
            process_name: PID가 없을 때 찾을 프로세스 이름입니다.
            sample_interval_seconds: CPU 사용률 샘플링 시간입니다.
        반환값:
            없음.
        """

        self.process_id = process_id
        self.process_name = process_name
        self.sample_interval_seconds = sample_interval_seconds

    def collect(self):
        """전체 시스템과 대상 프로세스의 자원 사용률을 수집합니다.

        인자:
            없음.
        반환값:
            CPU, 메모리, 프로세스 사용률 딕셔너리를 반환합니다.
        """

        process = self._resolve_process()
        return {
            "cpu": {
                "total_percent": psutil.cpu_percent(
                    interval=self.sample_interval_seconds
                ),
            },
            "memory": {
                "total_percent": psutil.virtual_memory().percent,
            },
            "process": self._collect_process_usage(process),
        }

    def _resolve_process(self):
        """모니터링 대상 프로세스를 결정합니다.

        인자:
            없음.
        반환값:
            psutil.Process 인스턴스를 반환합니다.
        """

        if self.process_id is not None:
            try:
                return psutil.Process(self.process_id)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        process = self._find_process_by_name(self.process_name)
        if process is not None:
            return process

        return psutil.Process(os.getpid())

    def _find_process_by_name(self, process_name):
        """프로세스 이름으로 실행 중인 프로세스를 찾습니다.

        인자:
            process_name: 찾을 프로세스 이름입니다.
        반환값:
            찾은 psutil.Process 또는 None을 반환합니다.
        """

        if not process_name:
            return None

        for process in psutil.process_iter(["pid", "name"]):
            try:
                name = process.info.get("name") or ""
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

            if name == process_name:
                return process
        return None

    def _collect_process_usage(self, process):
        """대상 프로세스의 CPU와 메모리 사용률을 수집합니다.

        인자:
            process: psutil.Process 인스턴스입니다.
        반환값:
            프로세스 사용률 딕셔너리를 반환합니다.
        """

        try:
            return {
                "pid": process.pid,
                "name": process.name(),
                "cpu_percent": process.cpu_percent(
                    interval=self.sample_interval_seconds
                ),
                "memory_percent": process.memory_percent(),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied) as error:
            return {
                "pid": getattr(process, "pid", None),
                "name": "-",
                "cpu_percent": None,
                "memory_percent": None,
                "error": str(error),
            }


def build_resource_status_collector_from_environment():
    """환경 변수 기준으로 자원 상태 수집기를 생성합니다.

    인자:
        없음.
    반환값:
        ResourceStatusCollector 인스턴스를 반환합니다.
    """

    process_id_text = os.getenv("EDGE_MONITOR_PROCESS_ID", "").strip()
    process_id = int(process_id_text) if process_id_text else None
    process_name = os.getenv("EDGE_MONITOR_PROCESS_NAME", DEFAULT_PROCESS_NAME)
    return ResourceStatusCollector(
        process_id=process_id,
        process_name=process_name,
    )

