# pseudo Edge node 백업 복구 HTTP 서버 파일입니다.
# AI server의 BACKUP_RECOVERY_URL 검증과 복구 ZIP 요청을 Windows에서 테스트하게 합니다.
# /health endpoint는 연결 검증용 상태를, /recover endpoint는 테스트 ZIP을 반환합니다.
# 실제 TS 인코딩 품질과 ffmpeg 병합 성공 여부는 라즈베리파이 Edge node에서 별도로 검증해야 합니다.

from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import parse_qs, urlparse
import json
import os
import threading
import time
import zipfile


class PseudoBackupRecoveryRequestHandler(BaseHTTPRequestHandler):
    """pseudo 백업 복구 HTTP 요청을 처리합니다.

    인자:
        request: HTTP client socket 요청입니다.
        client_address: client 주소입니다.
        server: backup_dir 속성을 가진 HTTP server입니다.
    반환값:
        PseudoBackupRecoveryRequestHandler 인스턴스를 반환합니다.
    """

    def do_GET(self):
        """GET 요청을 처리하고 /health 또는 /recover 응답을 반환합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        parsed_url = urlparse(self.path)
        if parsed_url.path == "/health":
            self._send_json(200, {"status": "ok"})
            return

        if parsed_url.path != "/recover":
            self._send_json(404, {"error": "unknown endpoint"})
            return

        query = parse_qs(parsed_url.query)
        start = _first_query_value(query, "start")
        end = _first_query_value(query, "end")
        if not start or not end:
            self._send_json(
                400,
                {"error": "start/end query is required for pseudo recovery"},
            )
            return

        archive = build_pseudo_recovery_archive(start, end, self.server.backup_dir)
        self.send_response(200)
        self.send_header("Content-Type", "application/zip")
        self.send_header(
            "Content-Disposition",
            'attachment; filename="pseudo_recovered_backups.zip"',
        )
        self.send_header("Content-Length", str(len(archive)))
        self.end_headers()
        self.wfile.write(archive)

    def log_message(self, format, *args):
        """기본 HTTP access log 출력을 억제합니다.

        인자:
            format: BaseHTTPRequestHandler가 전달한 log format입니다.
            args: format에 적용할 값입니다.
        반환값:
            없음.
        """

        del format, args

    def _send_json(self, status_code, payload):
        """JSON 응답을 전송합니다.

        인자:
            status_code: HTTP 상태 코드입니다.
            payload: JSON으로 변환할 딕셔너리입니다.
        반환값:
            없음.
        """

        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class PseudoBackupRecoveryHttpServer(ThreadingHTTPServer):
    """backup_dir 값을 보관하는 ThreadingHTTPServer 확장입니다.

    인자:
        server_address: listen할 HTTP 주소 튜플입니다.
        backup_dir: pseudo 백업 파일을 둘 폴더입니다.
    반환값:
        PseudoBackupRecoveryHttpServer 인스턴스를 반환합니다.
    """

    def __init__(self, server_address, backup_dir):
        """HTTP server와 backup_dir 속성을 초기화합니다.

        인자:
            server_address: listen할 HTTP 주소 튜플입니다.
            backup_dir: pseudo 백업 파일을 둘 폴더입니다.
        반환값:
            없음.
        """

        super().__init__(server_address, PseudoBackupRecoveryRequestHandler)
        self.backup_dir = Path(backup_dir)


class PseudoBackupRecoveryServer:
    """pseudo 백업 복구 HTTP 서버의 생명주기를 관리합니다.

    인자:
        host: listen할 호스트입니다.
        port: listen할 TCP 포트입니다.
        backup_dir: pseudo 백업 파일을 둘 폴더입니다.
    반환값:
        PseudoBackupRecoveryServer 인스턴스를 반환합니다.
    """

    def __init__(self, host="127.0.0.1", port=8002, backup_dir="./pseudo_backups"):
        """HTTP server 설정과 thread 상태를 초기화합니다.

        인자:
            host: listen할 호스트입니다.
            port: listen할 TCP 포트입니다.
            backup_dir: pseudo 백업 파일을 둘 폴더입니다.
        반환값:
            없음.
        """

        self.host = host
        self.port = int(port)
        self.backup_dir = backup_dir
        self.server = None
        self.thread = None

    def start(self):
        """백업 복구 HTTP server thread를 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.server is not None:
            return

        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
        self.server = PseudoBackupRecoveryHttpServer(
            (self.host, self.port),
            self.backup_dir,
        )
        self.thread = threading.Thread(
            target=self.server.serve_forever,
            name="PseudoBackupRecoveryServer",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """백업 복구 HTTP server를 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.server is None:
            return

        self.server.shutdown()
        self.server.server_close()
        self.server = None
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2)


def build_pseudo_recovery_archive(start_text, end_text, backup_dir):
    """복구 요청 구간을 흉내 내는 ZIP bytes를 생성합니다.

    인자:
        start_text: 복구 시작 시각 문자열입니다.
        end_text: 복구 종료 시각 문자열입니다.
        backup_dir: pseudo TS 파일 기록 폴더입니다.
    반환값:
        TS 파일 하나가 포함된 ZIP bytes를 반환합니다.
    """

    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    filename = build_pseudo_segment_filename(start_text)
    segment_bytes = (
        f"pseudo edge recovery segment\nstart={start_text}\nend={end_text}\n"
    ).encode("utf-8")
    segment_path = Path(backup_dir) / filename
    segment_path.write_bytes(segment_bytes)
    now = time.time()
    os.utime(segment_path, (now, now))

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(filename, segment_bytes)
    return buffer.getvalue()


def build_pseudo_segment_filename(start_text):
    """복구 시작 시각으로 pseudo TS 파일명을 생성합니다.

    인자:
        start_text: ISO 형식일 수 있는 시작 시각 문자열입니다.
    반환값:
        backup_YYYYMMDD_HHMMSS_00001.ts 형식의 파일명을 반환합니다.
    """

    try:
        started_at = datetime.fromisoformat(start_text)
        timestamp = started_at.strftime("%Y%m%d_%H%M%S")
    except ValueError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"backup_{timestamp}_00001.ts"


def _first_query_value(query, name):
    """query dict에서 첫 번째 값을 반환합니다.

    인자:
        query: parse_qs가 반환한 query 딕셔너리입니다.
        name: 조회할 query key입니다.
    반환값:
        값이 있으면 첫 번째 문자열을 반환하고 없으면 None을 반환합니다.
    """

    values = query.get(name)
    if not values:
        return None
    return values[0]
