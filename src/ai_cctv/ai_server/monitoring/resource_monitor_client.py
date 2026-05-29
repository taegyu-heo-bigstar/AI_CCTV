# Edge node 자원 모니터링 HTTP 클라이언트 파일입니다.
# Edge node FastAPI 서버의 모니터링 API로 요청을 보내고 JSON 결과를 받습니다.
# 서버 주소는 RESOURCE_MONITOR_SERVER_URL 환경 변수로 바꿀 수 있습니다.
# AI server UI나 별도 진단 도구에서 Edge node 자원 상태를 조회할 때 사용할 수 있습니다.

"""Edge node 자원 모니터링 API 클라이언트입니다."""

import json
import os

import requests


DEFAULT_SERVER_URL = "http://127.0.0.1:8001"


class ResourceMonitorClient:
    """Edge node 자원 모니터링 API 호출을 담당합니다.

    인자:
        server_url: Edge node 모니터링 서버의 기본 URL입니다.
        timeout_seconds: 요청 제한 시간입니다.
    반환값:
        ResourceMonitorClient 인스턴스를 반환합니다.
    """

    def __init__(self, server_url=DEFAULT_SERVER_URL, timeout_seconds=5):
        """모니터링 서버 접속 정보를 초기화합니다.

        인자:
            server_url: Edge node 모니터링 서버의 기본 URL입니다.
            timeout_seconds: 요청 제한 시간입니다.
        반환값:
            없음.
        """

        self.server_url = server_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def request_resource_usage(self):
        """Edge node에 자원 사용률 정보를 요청합니다.

        인자:
            없음.
        반환값:
            서버가 반환한 JSON 딕셔너리를 반환합니다.
        """

        endpoint = f"{self.server_url}/monitor/top"
        try:
            response = requests.get(endpoint, timeout=self.timeout_seconds)
        except requests.RequestException as error:
            raise RuntimeError(f"Edge node 모니터링 서버 요청 실패: {error}") from error

        if response.status_code >= 400:
            raise RuntimeError(f"Edge node 모니터링 서버 오류: {response.text}")

        return response.json()


def build_monitor_client():
    """환경 변수 기준으로 모니터링 클라이언트를 생성합니다.

    인자:
        없음.
    반환값:
        ResourceMonitorClient 인스턴스를 반환합니다.
    """

    server_url = os.getenv("RESOURCE_MONITOR_SERVER_URL", DEFAULT_SERVER_URL)
    return ResourceMonitorClient(server_url=server_url)


def request_resource_usage():
    """Edge node 자원 모니터링 결과를 요청해 그대로 반환합니다.

    인자:
        없음.
    반환값:
        Edge node 서버가 반환한 자원 사용률 딕셔너리를 반환합니다.
    """

    return build_monitor_client().request_resource_usage()


def print_resource_usage(resource_usage):
    """자원 사용률 응답을 콘솔에 JSON 형태로 출력합니다.

    인자:
        resource_usage: Edge node 서버가 반환한 자원 사용률 딕셔너리입니다.
    반환값:
        없음.
    """

    print(json.dumps(resource_usage, ensure_ascii=False, indent=2))


def main():
    """Edge node 자원 모니터링 결과를 요청하고 콘솔에 출력합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    print_resource_usage(request_resource_usage())


if __name__ == "__main__":
    main()
