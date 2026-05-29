# Edge node 로컬 백업 설정 파일입니다.
# Raspberry Pi에서 송출과 동시에 저장할 영상 세그먼트 경로를 관리합니다.
# GStreamer splitmuxsink에 전달할 파일명 패턴과 세그먼트 길이를 제공합니다.

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class LocalBackupConfig:
    """Edge node 로컬 백업 저장 정책을 표현합니다.

    인자:
        directory: 백업 파일을 저장할 폴더입니다.
        segment_seconds: 백업 파일 하나가 담을 영상 길이입니다.
        filename_prefix: 백업 파일명 앞에 붙일 접두사입니다.
    반환값:
        LocalBackupConfig 인스턴스를 반환합니다.
    """

    directory: str = "./backups"
    segment_seconds: int = 10
    filename_prefix: str = "backup"

    def ensure_directory(self):
        """백업 저장 폴더를 생성하고 경로를 반환합니다.

        인자:
            없음.
        반환값:
            생성이 보장된 pathlib.Path 객체를 반환합니다.
        """

        backup_dir = Path(self.directory)
        backup_dir.mkdir(parents=True, exist_ok=True)
        return backup_dir

    def build_segment_pattern(self, started_at=None):
        """splitmuxsink에 전달할 백업 세그먼트 파일명 패턴을 생성합니다.

        인자:
            started_at: 파일명에 사용할 시작 시각입니다.
        반환값:
            GStreamer가 사용할 세그먼트 파일명 패턴 문자열을 반환합니다.
        """

        timestamp = (started_at or datetime.now()).strftime("%Y%m%d_%H%M%S")
        filename = f"{self.filename_prefix}_{timestamp}_%05d.ts"
        return str(Path(self.directory) / filename)

    def segment_duration_nanoseconds(self):
        """백업 세그먼트 길이를 나노초 단위로 변환합니다.

        인자:
            없음.
        반환값:
            GStreamer max-size-time에 전달할 정수 값을 반환합니다.
        """

        return self.segment_seconds * 1_000_000_000
