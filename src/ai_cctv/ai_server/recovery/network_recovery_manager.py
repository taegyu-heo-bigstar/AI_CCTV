# 네트워크 장애 구간 복구 요청 파일입니다.
# AI server가 RTSP 단절 구간을 기록한 뒤 Edge node 백업 서버에 ZIP을 요청합니다.
# requests 라이브러리로 Edge node FastAPI 복구 API에 HTTP 요청을 보냅니다.
# 복구 서버 URL은 환경 변수 AI_CCTV_RECOVERY_SERVER_URL로 설정합니다.

import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote


@dataclass(frozen=True)
class NetworkRecoveryConfig:
    """네트워크 복구 요청 설정을 표현합니다.

    인자:
        camera_id: 복구 파일명에 사용할 카메라 식별자입니다.
        server_url: Edge node 백업 복구 API URL입니다.
        recovery_dir: 다운로드한 ZIP 파일을 저장할 폴더입니다.
        min_failure_seconds: 복구 요청을 보낼 최소 장애 지속 시간입니다.
        request_timeout_seconds: HTTP 요청 제한 시간입니다.
    반환값:
        NetworkRecoveryConfig 인스턴스를 반환합니다.
    """

    camera_id: str = "cam01"
    server_url: str = ""
    recovery_dir: str = "복구 영상"
    min_failure_seconds: float = 2.0
    request_timeout_seconds: float = 5.0


class NetworkRecoveryManager:
    """RTSP 단절 시작/복구 시각을 기록하고 누락 영상 ZIP을 요청합니다.

    인자:
        config: 네트워크 복구 요청 설정입니다.
    반환값:
        NetworkRecoveryManager 인스턴스를 반환합니다.
    """

    def __init__(self, config):
        """복구 요청 상태와 중복 요청 방지 목록을 초기화합니다.

        인자:
            config: 네트워크 복구 요청 설정입니다.
        반환값:
            없음.
        """

        self.config = config
        self.failure_start_time = None
        self.requested_ranges = set()

    def has_active_failure(self):
        """현재 기록 중인 네트워크 장애 구간이 있는지 반환합니다.

        인자:
            없음.
        반환값:
            장애 구간이 열려 있으면 True, 아니면 False를 반환합니다.
        """

        return self.failure_start_time is not None

    def record_failure(self, failed_time=None):
        """네트워크 장애 시작 시각을 기록합니다.

        인자:
            failed_time: 장애가 감지된 시각이며 없으면 현재 시각입니다.
        반환값:
            장애 시작 여부와 시작 시각을 담은 딕셔너리를 반환합니다.
        """

        failed_time = failed_time or datetime.now()
        if self.failure_start_time is None:
            self.failure_start_time = failed_time
            return {
                "started": True,
                "failure_start_time": self._format_time(self.failure_start_time),
            }

        return {
            "started": False,
            "failure_start_time": self._format_time(self.failure_start_time),
        }

    def record_recovery(self, recovered_time=None):
        """네트워크 복구 시각을 기록하고 필요하면 백업 ZIP을 요청합니다.

        인자:
            recovered_time: 복구가 감지된 시각이며 없으면 현재 시각입니다.
        반환값:
            요청 수행 여부, 성공 여부, 저장 경로 등을 담은 딕셔너리를 반환합니다.
        """

        if self.failure_start_time is None:
            return {"requested": False, "success": False, "reason": "no_active_failure"}

        recovered_time = recovered_time or datetime.now()
        failure_start_time = self.failure_start_time
        self.failure_start_time = None
        duration_seconds = (recovered_time - failure_start_time).total_seconds()
        payload = self.build_payload(failure_start_time, recovered_time)

        if duration_seconds < self.config.min_failure_seconds:
            return {
                "requested": False,
                "success": True,
                "skipped": True,
                "reason": "too_short",
                "duration_seconds": duration_seconds,
                "payload": payload,
            }

        request_key = self._get_request_key(payload)
        if request_key in self.requested_ranges:
            return {
                "requested": False,
                "success": True,
                "skipped": True,
                "reason": "duplicate",
                "duration_seconds": duration_seconds,
                "payload": payload,
            }

        result = self.request_recovery(payload)
        if result.get("success"):
            self.requested_ranges.add(request_key)

        result["duration_seconds"] = duration_seconds
        result["payload"] = payload
        return result

    def build_payload(self, start_time, end_time):
        """복구 요청에 사용할 시작/종료 시각 payload를 생성합니다.

        인자:
            start_time: 장애 시작 시각입니다.
            end_time: 장애 복구 시각입니다.
        반환값:
            start와 end 문자열을 담은 딕셔너리를 반환합니다.
        """

        start = self._format_time(start_time)
        end = self._format_time(end_time)
        return {"start": start, "end": end}

    def request_recovery(self, payload):
        """Edge node 복구 서버에 ZIP 파일을 요청하고 저장합니다.

        인자:
            payload: start와 end 시각 문자열을 담은 딕셔너리입니다.
        반환값:
            요청 결과 딕셔너리를 반환합니다.
        """

        if not self.config.server_url:
            return {
                "requested": False,
                "success": False,
                "reason": "server_url_not_configured",
            }

        try:
            import requests
        except ImportError as error:
            return {
                "requested": False,
                "success": False,
                "reason": "requests_not_installed",
                "error": str(error),
            }

        try:
            response = requests.get(
                self.config.server_url,
                params=payload,
                timeout=self.config.request_timeout_seconds,
            )
        except requests.RequestException as error:
            return {"requested": True, "success": False, "error": str(error)}

        if response.status_code >= 400:
            return {
                "requested": True,
                "success": False,
                "status_code": response.status_code,
                "error": response.text[:200],
            }

        if not response.content:
            return {
                "requested": True,
                "success": False,
                "error": "복구 서버 응답에 파일 데이터가 없습니다.",
            }

        save_path = self._save_file_response(response.headers, response.content, payload)
        return {
            "requested": True,
            "success": True,
            "saved_file": True,
            "file_path": str(save_path),
            "message": "복구 영상 ZIP 파일 저장 완료",
        }

    def _save_file_response(self, headers, content, payload):
        """HTTP 응답 파일명을 해석하고 ZIP 파일을 저장합니다.

        인자:
            headers: HTTP 응답 헤더 딕셔너리입니다.
            content: 저장할 ZIP 바이트입니다.
            payload: 기본 파일명 생성에 사용할 요청 payload입니다.
        반환값:
            저장된 pathlib.Path 객체를 반환합니다.
        """

        recovery_dir = Path(self.config.recovery_dir)
        recovery_dir.mkdir(parents=True, exist_ok=True)
        filename = self._get_response_filename(headers) or self._make_default_filename(payload)
        save_path = self._get_unique_save_path(recovery_dir / filename)
        save_path.write_bytes(content)
        return save_path

    def _get_response_filename(self, headers):
        """Content-Disposition 헤더에서 파일명을 추출합니다.

        인자:
            headers: HTTP 응답 헤더 딕셔너리입니다.
        반환값:
            안전하게 정리한 파일명 또는 None을 반환합니다.
        """

        content_disposition = headers.get("Content-Disposition", "")
        for part in content_disposition.split(";"):
            part = part.strip()
            lower_part = part.lower()
            if lower_part.startswith("filename*="):
                filename = part.split("=", 1)[1].strip().strip('"')
                if filename.lower().startswith("utf-8''"):
                    filename = filename[7:]
                return self._sanitize_filename(unquote(filename))
            if lower_part.startswith("filename="):
                filename = part.split("=", 1)[1].strip().strip('"')
                return self._sanitize_filename(unquote(filename))
        return None

    def _make_default_filename(self, payload):
        """복구 응답에 파일명이 없을 때 사용할 기본 파일명을 생성합니다.

        인자:
            payload: start와 end 시각 문자열을 담은 딕셔너리입니다.
        반환값:
            안전하게 정리한 ZIP 파일명을 반환합니다.
        """

        start_time = payload["start"].replace(":", "-")
        end_time = payload["end"].replace(":", "-")
        return self._sanitize_filename(
            f"recovered_backups_{self.config.camera_id}_{start_time}_{end_time}.zip"
        )

    def _get_unique_save_path(self, save_path):
        """같은 파일명이 있을 때 번호를 붙인 저장 경로를 반환합니다.

        인자:
            save_path: 우선 저장하려는 경로입니다.
        반환값:
            아직 존재하지 않는 pathlib.Path 객체를 반환합니다.
        """

        if not save_path.exists():
            return save_path

        index = 2
        while True:
            candidate = save_path.with_name(f"{save_path.stem}_{index}{save_path.suffix}")
            if not candidate.exists():
                return candidate
            index += 1

    def _get_request_key(self, payload):
        """중복 요청 확인에 사용할 키를 생성합니다.

        인자:
            payload: start와 end 시각 문자열을 담은 딕셔너리입니다.
        반환값:
            카메라 ID와 시간 구간 튜플을 반환합니다.
        """

        return (self.config.camera_id, payload["start"], payload["end"])

    def _format_time(self, value):
        """datetime 값을 초 단위 ISO 문자열로 변환합니다.

        인자:
            value: 변환할 datetime 객체입니다.
        반환값:
            ISO 8601 형식 문자열을 반환합니다.
        """

        return value.replace(microsecond=0).isoformat()

    def _sanitize_filename(self, filename):
        """파일명에서 경로와 Windows 금지 문자를 제거합니다.

        인자:
            filename: 원본 파일명입니다.
        반환값:
            안전하게 정리한 파일명을 반환합니다.
        """

        filename = os.path.basename(filename)
        return re.sub(r'[<>:"/\\|?*]', "_", filename)

def build_network_recovery_manager_from_env():
    """환경 변수 기준으로 NetworkRecoveryManager를 생성합니다.

    인자:
        없음.
    반환값:
        URL이 설정되면 NetworkRecoveryManager를, 없으면 None을 반환합니다.
    """

    server_url = os.getenv("AI_CCTV_RECOVERY_SERVER_URL", "").strip()
    if not server_url:
        return None

    config = NetworkRecoveryConfig(
        camera_id=os.getenv("AI_CCTV_RECOVERY_CAMERA_ID", "cam01"),
        server_url=server_url,
        recovery_dir=os.getenv("AI_CCTV_RECOVERY_DIR", "복구 영상"),
        min_failure_seconds=float(os.getenv("AI_CCTV_RECOVERY_MIN_FAILURE_SECONDS", "2.0")),
        request_timeout_seconds=float(os.getenv("AI_CCTV_RECOVERY_TIMEOUT_SECONDS", "5.0")),
    )
    return NetworkRecoveryManager(config)
