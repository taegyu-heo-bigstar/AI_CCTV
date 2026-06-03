# 라즈베리파이 엣지 노드 상태 FastAPI 서버 파일입니다.
# AI 서버가 HTTP로 조회할 수 있도록 자원 상태와 UPS Plus 전원 상태를 JSON으로 제공합니다.
# 기본 포트는 백업 복구 API 8002와 구분하기 위해 8003을 사용합니다.

from datetime import datetime
import os
import socket

from fastapi import FastAPI

from power_status import CachedPowerStatusProvider
from resource_status import build_resource_status_collector_from_environment


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8003


class EdgeStatusService:
    """엣지 노드 상태 조회에 필요한 수집기를 조율합니다.

    인자:
        resource_collector: CPU/메모리/프로세스 상태 수집 객체입니다.
        power_provider: UPS Plus 전원 상태 제공 객체입니다.
    반환값:
        EdgeStatusService 인스턴스를 반환합니다.
    """

    def __init__(self, resource_collector=None, power_provider=None):
        """엣지 상태 서비스의 의존 객체를 초기화합니다.

        인자:
            resource_collector: CPU/메모리/프로세스 상태 수집 객체입니다.
            power_provider: UPS Plus 전원 상태 제공 객체입니다.
        반환값:
            없음.
        """

        self.resource_collector = (
            resource_collector
            if resource_collector is not None
            else build_resource_status_collector_from_environment()
        )
        self.power_provider = (
            power_provider
            if power_provider is not None
            else CachedPowerStatusProvider()
        )

    def collect_status(self):
        """엣지 노드 전체 상태를 수집합니다.

        인자:
            없음.
        반환값:
            노드, 자원, 전원 상태를 담은 딕셔너리를 반환합니다.
        """

        return {
            "node": self.collect_node_status(),
            "resource": self.collect_resource_status(),
            "power": self.collect_power_status(),
        }

    def collect_node_status(self):
        """엣지 노드 식별 정보를 수집합니다.

        인자:
            없음.
        반환값:
            역할, 호스트명, 수집 시각을 담은 딕셔너리를 반환합니다.
        """

        return {
            "role": "edge_node",
            "hostname": socket.gethostname(),
            "collected_at": datetime.now().isoformat(timespec="seconds"),
        }

    def collect_resource_status(self):
        """엣지 노드 자원 상태를 수집합니다.

        인자:
            없음.
        반환값:
            CPU, 메모리, 프로세스 상태 딕셔너리를 반환합니다.
        """

        return self.resource_collector.collect()

    def collect_power_status(self):
        """엣지 노드 UPS Plus 전원 상태를 수집합니다.

        인자:
            없음.
        반환값:
            전원 상태 딕셔너리를 반환합니다.
        """

        return self.power_provider.get_snapshot().to_dict()


edge_status_service = EdgeStatusService()
app = FastAPI(title="AI CCTV Edge Status API")


@app.get("/health")
def read_health():
    """엣지 상태 API 서버의 생존 여부를 반환합니다.

    인자:
        없음.
    반환값:
        서버 상태 딕셔너리를 반환합니다.
    """

    return {
        "status": "ok",
        "service": "edge-status-api",
        "hostname": socket.gethostname(),
    }


@app.get("/status")
def read_status():
    """엣지 노드 전체 상태를 반환합니다.

    인자:
        없음.
    반환값:
        노드, 자원, 전원 상태 딕셔너리를 반환합니다.
    """

    return edge_status_service.collect_status()


@app.get("/status/resource")
def read_resource_status():
    """엣지 노드 자원 상태만 반환합니다.

    인자:
        없음.
    반환값:
        CPU, 메모리, 프로세스 상태 딕셔너리를 반환합니다.
    """

    return edge_status_service.collect_resource_status()


@app.get("/status/power")
def read_power_status():
    """엣지 노드 UPS Plus 전원 상태만 반환합니다.

    인자:
        없음.
    반환값:
        전원 상태 딕셔너리를 반환합니다.
    """

    return edge_status_service.collect_power_status()


def main():
    """uvicorn으로 엣지 상태 API 서버를 실행합니다.

    인자:
        없음.
    반환값:
        정상 실행 중에는 반환하지 않습니다.
    """

    import uvicorn

    host = os.getenv("EDGE_STATUS_API_HOST", DEFAULT_HOST)
    port = int(os.getenv("EDGE_STATUS_API_PORT", str(DEFAULT_PORT)))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()

