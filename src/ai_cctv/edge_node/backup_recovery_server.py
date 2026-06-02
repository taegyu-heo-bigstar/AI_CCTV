# Edge node 백업 복구 FastAPI 서버 파일입니다.
# AI server가 요청한 장애 시간대와 겹치는 로컬 TS 백업을 ZIP으로 묶어 반환합니다.
# FastAPI 엔드포인트는 /health와 /recover이며 /recover는 start/end 쿼리 값을 사용합니다.
# 기본 포트는 8002이며 AI_CCTV_BACKUP_RECOVERY_PORT로 변경할 수 있습니다.

import argparse
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ..config import get_env_int, get_env_value


@dataclass(frozen=True)
class BackupRecoveryArchive:
    """복구 요청으로 생성된 임시 ZIP 파일 정보를 표현합니다.

    인자:
        path: 임시 ZIP 파일 경로입니다.
        filename: 클라이언트에 전달할 다운로드 파일명입니다.
        file_count: ZIP에 포함된 백업 세그먼트 개수입니다.
    반환값:
        BackupRecoveryArchive 인스턴스를 반환합니다.
    """

    path: Path
    filename: str
    file_count: int


class BackupSegmentFinder:
    """로컬 백업 폴더에서 시간 구간과 겹치는 TS 세그먼트를 찾습니다.

    인자:
        backup_dir: 백업 TS 파일이 저장된 폴더입니다.
        segment_seconds: 세그먼트 하나의 영상 길이입니다.
    반환값:
        BackupSegmentFinder 인스턴스를 반환합니다.
    """

    def __init__(self, backup_dir, segment_seconds=10):
        """백업 탐색 위치와 세그먼트 길이를 초기화합니다.

        인자:
            backup_dir: 백업 TS 파일이 저장된 폴더입니다.
            segment_seconds: 세그먼트 하나의 영상 길이입니다.
        반환값:
            없음.
        """

        self.backup_dir = Path(backup_dir)
        self.segment_seconds = segment_seconds

    def find_segments(self, start_time, end_time):
        """요청 시간대와 겹치는 TS 백업 파일 목록을 반환합니다.

        인자:
            start_time: 복구 시작 시각입니다.
            end_time: 복구 종료 시각입니다.
        반환값:
            pathlib.Path 객체 목록을 반환합니다.
        """

        if not self.backup_dir.exists():
            raise FileNotFoundError(f"백업 디렉터리가 없습니다: {self.backup_dir}")

        target_files = []
        for path in sorted(self.backup_dir.glob("*.ts")):
            try:
                stat_result = path.stat()
            except OSError:
                continue

            file_end_time = datetime.fromtimestamp(stat_result.st_mtime)
            file_start_time = datetime.fromtimestamp(
                stat_result.st_mtime - self.segment_seconds
            )
            if self._ranges_overlap(start_time, end_time, file_start_time, file_end_time):
                target_files.append(path)
        return target_files

    def _ranges_overlap(self, request_start, request_end, file_start, file_end):
        """두 시간 구간이 겹치는지 확인합니다.

        인자:
            request_start: 요청 구간 시작 시각입니다.
            request_end: 요청 구간 종료 시각입니다.
            file_start: 파일 구간 시작 시각입니다.
            file_end: 파일 구간 종료 시각입니다.
        반환값:
            겹치면 True, 아니면 False를 반환합니다.
        """

        return max(request_start, file_start) < min(request_end, file_end)


class BackupRecoveryService:
    """복구 요청 시간을 검증하고 대상 백업 파일을 ZIP으로 묶습니다.

    인자:
        segment_finder: 백업 세그먼트 탐색 객체입니다.
    반환값:
        BackupRecoveryService 인스턴스를 반환합니다.
    """

    def __init__(self, segment_finder):
        """백업 세그먼트 탐색 의존 객체를 저장합니다.

        인자:
            segment_finder: BackupSegmentFinder 인스턴스입니다.
        반환값:
            없음.
        """

        self.segment_finder = segment_finder

    def recover(self, start_text, end_text):
        """요청 구간에 해당하는 백업 세그먼트 ZIP을 생성합니다.

        인자:
            start_text: ISO 8601 형식의 복구 시작 시각 문자열입니다.
            end_text: ISO 8601 형식의 복구 종료 시각 문자열입니다.
        반환값:
            BackupRecoveryArchive 객체를 반환합니다.
        """

        start_time = self._parse_iso_datetime(start_text, "start")
        end_time = self._parse_iso_datetime(end_text, "end")
        if start_time > end_time:
            raise ValueError("시작 시각이 종료 시각보다 늦을 수 없습니다.")

        target_files = self.segment_finder.find_segments(start_time, end_time)
        if not target_files:
            raise FileNotFoundError("해당 시간대에 해당하는 백업 파일이 없습니다.")

        return self._build_archive(target_files)

    def _parse_iso_datetime(self, value, field_name):
        """ISO 8601 시각 문자열을 datetime으로 변환합니다.

        인자:
            value: 변환할 문자열입니다.
            field_name: 오류 메시지에 사용할 필드 이름입니다.
        반환값:
            datetime 객체를 반환합니다.
        """

        if not value:
            raise ValueError(f"{field_name} 값이 필요합니다.")
        try:
            return datetime.fromisoformat(value)
        except ValueError as error:
            raise ValueError(
                f"{field_name} 값은 YYYY-MM-DDTHH:MM:SS 형식이어야 합니다."
            ) from error

    def _build_archive(self, target_files):
        """대상 TS 파일 목록을 임시 ZIP 파일로 묶습니다.

        인자:
            target_files: ZIP에 포함할 pathlib.Path 목록입니다.
        반환값:
            BackupRecoveryArchive 객체를 반환합니다.
        """

        temp_dir = Path(tempfile.gettempdir())
        filename = f"recovered_backups_{int(time.time())}.zip"
        archive_path = temp_dir / filename
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for target_file in target_files:
                zip_file.write(target_file, arcname=target_file.name)
        return BackupRecoveryArchive(
            path=archive_path,
            filename=filename,
            file_count=len(target_files),
        )


def remove_temp_file(path):
    """파일 전송 완료 후 임시 ZIP 파일을 삭제합니다.

    인자:
        path: 삭제할 임시 ZIP 파일 경로입니다.
    반환값:
        없음.
    """

    try:
        Path(path).unlink(missing_ok=True)
    except OSError as error:
        print(f"[BackupRecovery] 임시 파일 삭제 실패: {error}")


def create_backup_recovery_app(service):
    """BackupRecoveryService를 사용하는 FastAPI 앱을 생성합니다.

    인자:
        service: 백업 복구 요청을 처리할 서비스 객체입니다.
    반환값:
        FastAPI 애플리케이션 객체를 반환합니다.
    """

    from fastapi import BackgroundTasks, FastAPI, HTTPException
    from fastapi.responses import FileResponse, JSONResponse

    app = FastAPI(title="AI CCTV Edge Backup Recovery Server")

    @app.get("/health")
    def health_check():
        """백업 복구 서버가 요청을 받을 준비가 되었는지 반환합니다.

        인자:
            없음.
        반환값:
            서버 상태를 담은 JSON 딕셔너리를 반환합니다.
        """

        return {"status": "ok"}

    @app.get("/recover")
    def recover_backups(start: str, end: str, background_tasks: BackgroundTasks):
        """요청 시간대와 겹치는 백업 TS 파일을 ZIP으로 반환합니다.

        인자:
            start: ISO 8601 형식의 복구 시작 시각입니다.
            end: ISO 8601 형식의 복구 종료 시각입니다.
            background_tasks: 응답 후 임시 파일 삭제를 예약하는 FastAPI 객체입니다.
        반환값:
            FileResponse 객체를 반환합니다.
        """

        try:
            archive = service.recover(start, end)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except FileNotFoundError as error:
            return JSONResponse(
                status_code=404,
                content={"message": str(error)},
            )
        except OSError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

        background_tasks.add_task(remove_temp_file, archive.path)
        return FileResponse(
            path=archive.path,
            media_type="application/x-zip-compressed",
            filename=archive.filename,
        )

    return app


def build_backup_recovery_app(backup_dir="~/backups"):
    """환경 설정을 반영한 FastAPI 백업 복구 앱을 생성합니다.

    인자:
        backup_dir: 백업 TS 파일이 저장된 폴더입니다.
    반환값:
        FastAPI 애플리케이션 객체를 반환합니다.
    """

    segment_finder = BackupSegmentFinder(Path(backup_dir).expanduser())
    return create_backup_recovery_app(BackupRecoveryService(segment_finder))


try:
    app = build_backup_recovery_app(
        get_env_value("AI_CCTV_BACKUP_DIR", "~/backups")
    )
except ImportError:
    app = None


def build_argument_parser():
    """백업 복구 서버 명령행 인자 파서를 생성합니다.

    인자:
        없음.
    반환값:
        argparse.ArgumentParser 객체를 반환합니다.
    """

    parser = argparse.ArgumentParser(description="AI CCTV edge backup recovery server")
    parser.add_argument("--host", default=None)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--backup-dir", default=None)
    parser.add_argument("--no-startup-info", action="store_true")
    return parser


def main(argv=None):
    """환경 변수 기준으로 Edge node 백업 복구 FastAPI 서버를 실행합니다.

    인자:
        없음.
    반환값:
        정상적으로는 반환하지 않습니다.
    """

    import uvicorn
    from .os_guard import ensure_supported_edge_os
    from .startup_info import print_edge_connection_info

    ensure_supported_edge_os()
    args = build_argument_parser().parse_args(argv)
    host = args.host or get_env_value("AI_CCTV_BACKUP_RECOVERY_HOST", "0.0.0.0")
    port = args.port if args.port is not None else get_env_int("AI_CCTV_BACKUP_RECOVERY_PORT", 8002)
    backup_dir = args.backup_dir or get_env_value("AI_CCTV_BACKUP_DIR", "~/backups")
    recovery_app = build_backup_recovery_app(backup_dir)
    if not args.no_startup_info:
        print_edge_connection_info(
            backup_recovery_port=port,
            backup_dir=backup_dir,
        )
    uvicorn.run(recovery_app, host=host, port=port)


if __name__ == "__main__":
    main()
