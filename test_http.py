# Edge node 상태 조회 UI를 임시 검증하기 위한 모의 HTTP 서버 파일입니다.
# 실제 Raspberry Pi 없이 `/monitor/top` 응답을 생성합니다.
# AI server UI의 `엣지 노드 상태 조회` 버튼은 기본적으로 이 서버를 조회할 수 있습니다.
# 표와 꺾은선 그래프가 변하는지 확인할 수 있도록 사용률과 배터리 값을 바꿉니다.
# 10번 성공 응답한 뒤에는 일부러 응답을 보내지 않아 연결 실패 UI를 확인합니다.

"""Edge node 모니터링 API 모의 서버입니다."""

import argparse
import json
import math
import os
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


class MockResourceState:
    """모의 자원 사용률 값을 생성하고 보관합니다.

    인자:
        process_id: 응답에 표시할 임시 프로세스 ID입니다.
    반환값:
        MockResourceState 인스턴스를 반환합니다.
    """

    def __init__(self, process_id=None, max_successful_responses=10):
        """모의 응답 상태를 초기화합니다.

        인자:
            process_id: 응답에 표시할 임시 프로세스 ID이며 없으면 현재 프로세스입니다.
            max_successful_responses: 정상 JSON을 반환할 최대 횟수입니다.
        반환값:
            없음.
        """

        self.started_at = time.monotonic()
        self.process_id = process_id if process_id is not None else os.getpid()
        self.max_successful_responses = max_successful_responses
        self.successful_response_count = 0

    def can_respond(self):
        """정상 JSON 응답을 더 보낼 수 있는지 판단합니다.

        인자:
            없음.
        반환값:
            정상 응답 가능 여부를 bool로 반환합니다.
        """

        return self.successful_response_count < self.max_successful_responses

    def build_response(self):
        """현재 시점의 모의 자원 사용률 JSON을 생성합니다.

        인자:
            없음.
        반환값:
            Edge node 모니터링 API와 같은 구조의 딕셔너리를 반환합니다.
        """

        self.successful_response_count += 1
        elapsed = time.monotonic() - self.started_at
        cpu_total = self._wave(elapsed, base=42.0, amplitude=28.0, speed=0.75)
        memory_total = self._wave(elapsed, base=55.0, amplitude=14.0, speed=0.35)
        process_cpu = self._wave(elapsed, base=18.0, amplitude=16.0, speed=1.2)
        process_memory = self._wave(elapsed, base=3.5, amplitude=2.0, speed=0.5)
        battery_remaining = self._wave(elapsed, base=62.0, amplitude=18.0, speed=0.2)
        external_power_connected = int(elapsed / 8) % 2 == 0
        type_c_input_millivolt = 5100 if external_power_connected else 0
        micro_usb_input_millivolt = 0
        return {
            "collected_at": datetime.now().isoformat(timespec="seconds"),
            "cpu": {"total_percent": round(cpu_total, 1)},
            "memory": {"total_percent": round(memory_total, 1)},
            "process": {
                "pid": self.process_id,
                "name": "mock-edge-monitor",
                "cpu_percent": round(process_cpu, 1),
                "memory_percent": round(process_memory, 1),
            },
            "power": {
                "captured_at": datetime.now().isoformat(timespec="seconds"),
                "available": True,
                "battery_remaining_percent": round(battery_remaining, 1),
                "external_power_connected": external_power_connected,
                "type_c_input_millivolt": type_c_input_millivolt,
                "micro_usb_input_millivolt": micro_usb_input_millivolt,
                "power_status_raw": 1,
                "error": None,
            },
        }

    def _wave(self, elapsed, base, amplitude, speed):
        """사인파 기반의 0~100 범위 모의 백분율 값을 계산합니다.

        인자:
            elapsed: 서버 시작 이후 지난 시간입니다.
            base: 기준 백분율 값입니다.
            amplitude: 변동 폭입니다.
            speed: 변동 속도입니다.
        반환값:
            0부터 100 사이의 float 값을 반환합니다.
        """

        value = base + amplitude * math.sin(elapsed * speed)
        return max(0.0, min(100.0, value))


class MockResourceRequestHandler(BaseHTTPRequestHandler):
    """모의 모니터링 HTTP 요청을 처리합니다.

    인자:
        request: 클라이언트 소켓 요청입니다.
        client_address: 클라이언트 주소입니다.
        server: 요청을 받은 HTTP 서버입니다.
    반환값:
        MockResourceRequestHandler 인스턴스를 반환합니다.
    """

    def do_GET(self):
        """GET 요청 경로에 따라 JSON 응답 또는 404를 반환합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        path = urlparse(self.path).path
        if path != "/monitor/top":
            self._send_json({"detail": "not found"}, status_code=404)
            return

        if not self.server.resource_state.can_respond():
            print("[mock-edge] response limit reached; keeping request silent")
            time.sleep(self.server.silent_seconds)
            return

        self._send_json(self.server.resource_state.build_response())

    def log_message(self, format_text, *args):
        """HTTP 서버 기본 접근 로그를 한 줄 형태로 출력합니다.

        인자:
            format_text: BaseHTTPRequestHandler가 전달한 로그 포맷입니다.
            args: 로그 포맷에 들어갈 값들입니다.
        반환값:
            없음.
        """

        print(f"[mock-edge] {self.address_string()} - {format_text % args}")

    def _send_json(self, payload, status_code=200):
        """딕셔너리 응답을 JSON HTTP 응답으로 전송합니다.

        인자:
            payload: JSON으로 직렬화할 딕셔너리입니다.
            status_code: HTTP 상태 코드입니다.
        반환값:
            없음.
        """

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class MockResourceServer(ThreadingHTTPServer):
    """모의 자원 상태 객체를 포함한 HTTP 서버입니다.

    인자:
        server_address: 서버가 바인딩할 주소와 포트입니다.
        request_handler_class: 요청 처리 핸들러 클래스입니다.
    반환값:
        MockResourceServer 인스턴스를 반환합니다.
    """

    def __init__(self, server_address, request_handler_class, silent_seconds=30):
        """HTTP 서버와 모의 자원 상태를 초기화합니다.

        인자:
            server_address: 서버가 바인딩할 주소와 포트입니다.
            request_handler_class: 요청 처리 핸들러 클래스입니다.
            silent_seconds: 응답 제한 이후 요청을 붙잡고 있을 시간입니다.
        반환값:
            없음.
        """

        super().__init__(server_address, request_handler_class)
        self.resource_state = MockResourceState()
        self.silent_seconds = silent_seconds


def build_argument_parser():
    """명령행 인자 파서를 생성합니다.

    인자:
        없음.
    반환값:
        argparse.ArgumentParser 인스턴스를 반환합니다.
    """

    parser = argparse.ArgumentParser(description="Run mock Edge node monitor API.")
    parser.add_argument("--host", default="127.0.0.1", help="HTTP bind host.")
    parser.add_argument("--port", type=int, default=8001, help="HTTP bind port.")
    return parser


def run_server(host, port):
    """모의 Edge node 모니터링 HTTP 서버를 실행합니다.

    인자:
        host: 서버가 바인딩할 호스트입니다.
        port: 서버가 바인딩할 포트입니다.
    반환값:
        정상적으로는 반환하지 않습니다.
    """

    server = MockResourceServer((host, port), MockResourceRequestHandler)
    print(f"Mock Edge node monitor API: http://{host}:{port}/monitor/top")
    print("Normal responses: 10; then requests stay silent.")
    print("Stop: Ctrl+C")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server stopped.")
    finally:
        server.server_close()


def main():
    """명령행 인자를 읽고 모의 HTTP 서버를 시작합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    args = build_argument_parser().parse_args()
    run_server(args.host, args.port)


if __name__ == "__main__":
    main()
