# 네트워크 장애 구간 복구 요청 파일입니다.
# AI server가 RTSP 단절 구간을 기록한 뒤 Edge node 백업 서버에 ZIP을 요청합니다.
# requests 라이브러리로 Edge node FastAPI 복구 API에 HTTP 요청을 보냅니다.
# 복구 ZIP은 TS 세그먼트 추출 후 MP4로 병합해 원본 녹화 폴더에 저장합니다.
# 복구 서버 URL은 환경 변수 AI_CCTV_RECOVERY_SERVER_URL로 설정합니다.

import os
import re
import shutil
import subprocess
import tempfile
import zipfile
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
        recording_dir: 복구 MP4 파일을 저장할 원본 녹화 폴더입니다.
        min_failure_seconds: 복구 요청을 보낼 최소 장애 지속 시간입니다.
        request_timeout_seconds: HTTP 요청 제한 시간입니다.
        settle_seconds: Edge node 백업 파일 쓰기 완료를 기다릴 시간입니다.
        ffmpeg_path: TS 병합에 사용할 ffmpeg 실행 파일 경로입니다.
    반환값:
        NetworkRecoveryConfig 인스턴스를 반환합니다.
    """

    camera_id: str = "cam01"
    server_url: str = ""
    recovery_dir: str = "복구 영상"
    recording_dir: str = ""
    min_failure_seconds: float = 2.0
    request_timeout_seconds: float = 30.0
    settle_seconds: float = 2.0
    ffmpeg_path: str = "ffmpeg"


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
        self.recovery_dir = Path(self.config.recovery_dir)
        self.recording_dir = (
            Path(self.config.recording_dir)
            if self.config.recording_dir
            else self.recovery_dir
        )

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
        duration_seconds = (recovered_time - failure_start_time).total_seconds()
        payload = self.build_payload(failure_start_time, recovered_time)

        if duration_seconds < self.config.min_failure_seconds:
            self.failure_start_time = None
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
            self.failure_start_time = None
            return {
                "requested": False,
                "success": True,
                "skipped": True,
                "reason": "duplicate",
                "duration_seconds": duration_seconds,
                "payload": payload,
            }

        if self.config.settle_seconds > 0:
            import time

            time.sleep(self.config.settle_seconds)

        result = self.request_recovery(payload)
        if result.get("success"):
            self.requested_ranges.add(request_key)
            self.failure_start_time = None

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
        return {
            "start": start,
            "end": end,
            "start_time": start,
            "end_time": end,
            "start_dt": start_time,
            "end_dt": end_time,
        }

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
                params={
                    "start": payload["start"],
                    "end": payload["end"],
                },
                timeout=self.config.request_timeout_seconds,
                stream=True,
            )
        except requests.RequestException as error:
            return {"requested": True, "success": False, "error": str(error)}

        if response.status_code == 404:
            return {
                "requested": True,
                "success": False,
                "status_code": 404,
                "reason": "not_found",
                "error": self._get_response_error_text(
                    response,
                    "요청한 시간 구간에 해당하는 백업 파일이 없습니다.",
                ),
            }

        if not response.ok:
            return {
                "requested": True,
                "success": False,
                "status_code": response.status_code,
                "error": self._get_response_error_text(response, response.text[:200]),
            }

        save_path = self._save_file_response(response, payload)
        if save_path is None:
            return {
                "requested": True,
                "success": False,
                "status_code": response.status_code,
                "error": "복구 ZIP 파일 저장 실패",
            }

        merge_result = self._extract_and_merge(save_path, payload)
        if not merge_result.get("success"):
            merge_result.update({
                "requested": True,
                "status_code": response.status_code,
                "zip_path": str(save_path),
            })
            return merge_result

        return {
            "requested": True,
            "success": True,
            "saved_file": True,
            "zip_path": str(save_path),
            "file_path": merge_result["file_path"],
            "ts_count": merge_result["ts_count"],
            "message": "복구 영상 MP4 파일 저장 완료",
        }

    def _save_file_response(self, response, payload):
        """HTTP 응답 파일명을 해석하고 ZIP 파일을 스트리밍 저장합니다.

        인자:
            response: requests가 반환한 HTTP 응답 객체입니다.
            payload: 기본 파일명 생성에 사용할 요청 payload입니다.
        반환값:
            저장된 pathlib.Path 객체 또는 저장 실패 시 None을 반환합니다.
        """

        self.recovery_dir.mkdir(parents=True, exist_ok=True)
        filename = self._get_response_filename(response.headers) or self._make_default_zip_filename(payload)
        save_path = self._get_unique_save_path(self.recovery_dir / filename)

        try:
            wrote_any = False
            with save_path.open("wb") as file:
                iter_content = getattr(response, "iter_content", None)
                if callable(iter_content):
                    for chunk in iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            wrote_any = True
                            file.write(chunk)
                else:
                    content = getattr(response, "content", b"")
                    if content:
                        wrote_any = True
                        file.write(content)
            if not wrote_any:
                save_path.unlink(missing_ok=True)
                return None
        except OSError:
            return None

        return save_path

    def _extract_and_merge(self, zip_path, payload):
        """복구 ZIP에서 TS 파일을 추출하고 MP4 파일로 병합합니다.

        인자:
            zip_path: Edge node에서 내려받은 복구 ZIP 파일 경로입니다.
            payload: 복구 구간 시작/종료 시각을 담은 딕셔너리입니다.
        반환값:
            병합 성공 여부와 MP4 저장 경로를 담은 딕셔너리를 반환합니다.
        """

        self.recording_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="ai_cctv_recovery_") as temp_dir:
            try:
                with zipfile.ZipFile(zip_path, "r") as zip_file:
                    self._safe_extract(zip_file, temp_dir)
            except Exception as error:
                return {
                    "success": False,
                    "error": f"복구 ZIP 압축 해제 실패: {error}",
                }

            ts_files = self._find_ts_files(temp_dir)
            if not ts_files:
                return {
                    "success": False,
                    "error": "복구 ZIP 안에 TS 파일이 없습니다.",
                }

            output_filename = self._make_recovered_mp4_filename(payload)
            output_path = self._get_unique_save_path(self.recording_dir / output_filename)
            merge_result = self._merge_ts_files(ts_files, output_path, temp_dir)
            if not merge_result.get("success"):
                return merge_result

            return {
                "success": True,
                "file_path": str(output_path),
                "ts_count": len(ts_files),
            }

    def _safe_extract(self, zip_file, target_dir):
        """ZIP 내부의 TS 파일만 경로 탈출 없이 안전하게 추출합니다.

        인자:
            zip_file: 읽을 zipfile.ZipFile 객체입니다.
            target_dir: 압축 해제 대상 임시 폴더입니다.
        반환값:
            없음.
        """

        target_dir_path = Path(target_dir).resolve()
        for info in zip_file.infolist():
            if not info.filename.lower().endswith(".ts"):
                continue

            destination = (target_dir_path / info.filename).resolve()
            if not self._is_relative_to(destination, target_dir_path):
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            with zip_file.open(info) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)

    def _find_ts_files(self, folder):
        """폴더 안의 TS 파일 목록을 세그먼트 순서대로 반환합니다.

        인자:
            folder: TS 파일을 찾을 폴더입니다.
        반환값:
            pathlib.Path 객체 목록을 반환합니다.
        """

        ts_files = [
            path
            for path in Path(folder).rglob("*")
            if path.is_file() and path.suffix.lower() == ".ts"
        ]
        return sorted(ts_files, key=self._ts_sort_key)

    def _ts_sort_key(self, path):
        """TS 파일명을 기준으로 병합 순서를 계산합니다.

        인자:
            path: 정렬할 TS 파일 경로입니다.
        반환값:
            정렬에 사용할 튜플을 반환합니다.
        """

        filename = path.name
        numbers = re.findall(r"\d+", filename)
        if numbers:
            prefix = filename[: filename.rfind(numbers[-1])]
            return (prefix, int(numbers[-1]))
        return (filename, int(path.stat().st_mtime))

    def _merge_ts_files(self, ts_files, output_path, work_dir):
        """ffmpeg concat 입력으로 TS 파일을 MP4 파일 하나로 병합합니다.

        인자:
            ts_files: 병합할 TS 파일 경로 목록입니다.
            output_path: 생성할 MP4 파일 경로입니다.
            work_dir: ffmpeg concat 목록을 작성할 임시 작업 폴더입니다.
        반환값:
            병합 성공 여부와 오류 메시지를 담은 딕셔너리를 반환합니다.
        """

        concat_list_path = Path(work_dir) / "concat_list.txt"
        try:
            with concat_list_path.open("w", encoding="utf-8") as list_file:
                for ts_path in ts_files:
                    safe_path = str(ts_path).replace("\\", "/").replace("'", "'\\''")
                    list_file.write(f"file '{safe_path}'\n")

            command = [
                self.config.ffmpeg_path,
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(concat_list_path),
                "-fflags",
                "+genpts",
                "-avoid_negative_ts",
                "make_zero",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-pix_fmt",
                "yuv420p",
                "-an",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
            completed = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return {
                "success": False,
                "error": "ffmpeg 실행 파일을 찾을 수 없습니다. ffmpeg를 설치하고 PATH에 추가하세요.",
            }
        except Exception as error:
            return {
                "success": False,
                "error": f"TS 병합 중 오류 발생: {error}",
            }

        if completed.returncode != 0:
            return {
                "success": False,
                "error": completed.stderr[-500:] or "ffmpeg 병합 실패",
            }

        if not output_path.exists() or output_path.stat().st_size == 0:
            return {
                "success": False,
                "error": "ffmpeg 병합 결과 파일이 생성되지 않았습니다.",
            }

        return {"success": True}

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

    def _get_response_error_text(self, response, default):
        """복구 API 오류 응답에서 사용자에게 보여줄 메시지를 추출합니다.

        인자:
            response: requests가 반환한 HTTP 응답 객체입니다.
            default: 구조화된 메시지가 없을 때 사용할 기본 메시지입니다.
        반환값:
            오류 메시지 문자열을 반환합니다.
        """

        try:
            data = response.json()
        except Exception:
            return default

        if isinstance(data, dict):
            return str(data.get("message") or data.get("detail") or default)
        return default

    def _make_default_zip_filename(self, payload):
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

    def _make_default_filename(self, payload):
        """기존 호출 호환성을 위해 기본 ZIP 파일명을 반환합니다.

        인자:
            payload: start와 end 시각 문자열을 담은 딕셔너리입니다.
        반환값:
            안전하게 정리한 ZIP 파일명을 반환합니다.
        """

        return self._make_default_zip_filename(payload)

    def _make_recovered_mp4_filename(self, payload):
        """복구 MP4 파일명을 장애 시작/종료 시각으로 생성합니다.

        인자:
            payload: start/end 문자열 또는 datetime 값을 담은 딕셔너리입니다.
        반환값:
            안전하게 정리한 MP4 파일명을 반환합니다.
        """

        start_dt = payload.get("start_dt")
        end_dt = payload.get("end_dt")
        if start_dt is None:
            start_text = payload["start"].replace("T", "_").replace(":", "-")
        else:
            start_text = start_dt.strftime("%Y-%m-%d_%H-%M-%S")

        if end_dt is None:
            end_text = payload["end"].replace("T", "_").replace(":", "-")
        else:
            end_text = end_dt.strftime("%Y-%m-%d_%H-%M-%S")

        return self._sanitize_filename(f"{start_text}~{end_text}(장애복구파일).mp4")

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

    def _is_relative_to(self, path, parent):
        """경로가 지정한 부모 폴더 내부에 있는지 확인합니다.

        인자:
            path: 확인할 경로입니다.
            parent: 기준 부모 경로입니다.
        반환값:
            path가 parent 아래에 있으면 True, 아니면 False를 반환합니다.
        """

        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

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

def build_network_recovery_manager_from_env(base_dir=""):
    """환경 변수 기준으로 NetworkRecoveryManager를 생성합니다.

    인자:
        base_dir: 사용자 저장 루트인 AI_CCTV 폴더 경로입니다.
    반환값:
        URL이 설정되면 NetworkRecoveryManager를, 없으면 None을 반환합니다.
    """

    server_url = os.getenv("AI_CCTV_RECOVERY_SERVER_URL", "").strip()
    if not server_url:
        return None

    base_path = Path(base_dir) if base_dir else None
    default_recovery_dir = (
        base_path / "복구 영상" if base_path is not None else Path("복구 영상")
    )
    default_recording_dir = (
        base_path / "original_records"
        if base_path is not None
        else default_recovery_dir
    )

    config = NetworkRecoveryConfig(
        camera_id=os.getenv("AI_CCTV_RECOVERY_CAMERA_ID", "cam01"),
        server_url=server_url,
        recovery_dir=os.getenv("AI_CCTV_RECOVERY_DIR", str(default_recovery_dir)),
        recording_dir=os.getenv(
            "AI_CCTV_RECOVERY_RECORDING_DIR",
            str(default_recording_dir),
        ),
        min_failure_seconds=float(os.getenv("AI_CCTV_RECOVERY_MIN_FAILURE_SECONDS", "2.0")),
        request_timeout_seconds=float(os.getenv("AI_CCTV_RECOVERY_TIMEOUT_SECONDS", "30.0")),
        settle_seconds=float(os.getenv("AI_CCTV_RECOVERY_SETTLE_SECONDS", "2.0")),
        ffmpeg_path=os.getenv("AI_CCTV_RECOVERY_FFMPEG_PATH", "ffmpeg"),
    )
    return NetworkRecoveryManager(config)
