# Edge node MediaMTX 관리 파일입니다.
# Raspberry Pi 로컬 MediaMTX 실행 파일을 확인하고 필요 시 다운로드합니다.
# GStreamer가 송출할 로컬 중계 서버 프로세스의 시작과 종료를 담당합니다.

import os
import platform
import stat
import subprocess
import tarfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MediaMtxConfig:
    """MediaMTX 설치와 실행 경로 설정을 표현합니다.

    인자:
        version: 다운로드할 MediaMTX 릴리스 버전입니다.
        work_dir: 실행 파일과 설정 파일을 둘 작업 폴더입니다.
        binary_name: MediaMTX 실행 파일명입니다.
        config_name: MediaMTX 설정 파일명입니다.
        log_name: MediaMTX 실행 로그 파일명입니다.
    반환값:
        MediaMtxConfig 인스턴스를 반환합니다.
    """

    version: str = "v1.9.0"
    work_dir: str = "~/.ai_cctv/mediamtx"
    binary_name: str = "mediamtx"
    config_name: str = "mediamtx.yml"
    log_name: str = "mediamtx.log"

    @property
    def work_path(self):
        """MediaMTX 작업 폴더 경로를 반환합니다.

        인자:
            없음.
        반환값:
            pathlib.Path 작업 폴더 객체를 반환합니다.
        """

        return Path(self.work_dir).expanduser()

    @property
    def binary_path(self):
        """MediaMTX 실행 파일 경로를 반환합니다.

        인자:
            없음.
        반환값:
            pathlib.Path 실행 파일 객체를 반환합니다.
        """

        return self.work_path / self.binary_name

    @property
    def config_path(self):
        """MediaMTX 설정 파일 경로를 반환합니다.

        인자:
            없음.
        반환값:
            pathlib.Path 설정 파일 객체를 반환합니다.
        """

        return self.work_path / self.config_name

    @property
    def log_path(self):
        """MediaMTX 로그 파일 경로를 반환합니다.

        인자:
            없음.
        반환값:
            pathlib.Path 로그 파일 객체를 반환합니다.
        """

        return self.work_path / self.log_name


class MediaMtxReleaseResolver:
    """Raspberry Pi 아키텍처에 맞는 MediaMTX 다운로드 주소를 결정합니다.

    인자:
        config: MediaMTX 버전 설정입니다.
    반환값:
        MediaMtxReleaseResolver 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """릴리스 주소 결정에 사용할 설정을 초기화합니다.

        인자:
            config: MediaMTX 설치 설정입니다.
        반환값:
            없음.
        """

        self.config = config or MediaMtxConfig()

    def resolve_download_url(self, machine=None):
        """현재 장비 아키텍처에 맞는 MediaMTX 압축 파일 URL을 반환합니다.

        인자:
            machine: platform.machine 값입니다.
        반환값:
            다운로드 가능한 MediaMTX 릴리스 URL 문자열을 반환합니다.
        """

        architecture = machine or platform.machine()
        if architecture == "aarch64":
            package = "linux_arm64v8"
        elif architecture.startswith("arm"):
            package = "linux_armv7"
        else:
            raise ValueError(f"지원하지 않는 Edge node 아키텍처입니다: {architecture}")

        version = self.config.version
        return (
            "https://github.com/bluenviron/mediamtx/releases/download/"
            f"{version}/mediamtx_{version}_{package}.tar.gz"
        )


class MediaMtxInstaller:
    """MediaMTX 실행 파일과 설정 파일의 존재를 보장합니다.

    인자:
        config: MediaMTX 설치 설정입니다.
        resolver: 아키텍처별 다운로드 URL 결정 객체입니다.
    반환값:
        MediaMtxInstaller 인스턴스를 반환합니다.
    """

    def __init__(self, config=None, resolver=None):
        """MediaMTX 설치 준비 객체를 초기화합니다.

        인자:
            config: MediaMTX 설치 설정입니다.
            resolver: 다운로드 URL 결정 객체입니다.
        반환값:
            없음.
        """

        self.config = config or MediaMtxConfig()
        self.resolver = resolver or MediaMtxReleaseResolver(self.config)

    def is_installed(self):
        """MediaMTX 실행 파일과 설정 파일이 모두 있는지 확인합니다.

        인자:
            없음.
        반환값:
            설치되어 있으면 True, 아니면 False를 반환합니다.
        """

        return self.config.binary_path.is_file() and self.config.config_path.is_file()

    def ensure_installed(self):
        """MediaMTX가 없으면 다운로드하고 압축을 해제합니다.

        인자:
            없음.
        반환값:
            MediaMTX 실행 파일 경로를 반환합니다.
        """

        self.config.work_path.mkdir(parents=True, exist_ok=True)
        if self.is_installed():
            return self.config.binary_path

        archive_path = self.config.work_path / "mediamtx.tar.gz"
        download_url = self.resolver.resolve_download_url()
        urllib.request.urlretrieve(download_url, archive_path)
        self._extract_required_files(archive_path)
        archive_path.unlink(missing_ok=True)
        self._make_binary_executable()
        return self.config.binary_path

    def _extract_required_files(self, archive_path):
        """MediaMTX 압축 파일에서 실행 파일과 설정 파일만 추출합니다.

        인자:
            archive_path: 다운로드한 tar.gz 파일 경로입니다.
        반환값:
            없음.
        """

        required_names = {self.config.binary_name, self.config.config_name}
        with tarfile.open(archive_path, "r:gz") as archive:
            for member in archive.getmembers():
                member_name = Path(member.name).name
                if member_name not in required_names:
                    continue
                member.name = member_name
                archive.extract(member, self.config.work_path)

    def _make_binary_executable(self):
        """MediaMTX 실행 파일에 실행 권한을 부여합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if os.name == "nt":
            return
        current_mode = self.config.binary_path.stat().st_mode
        self.config.binary_path.chmod(current_mode | stat.S_IXUSR)


class MediaMtxProcessManager:
    """MediaMTX 프로세스의 실행 상태를 관리합니다.

    인자:
        config: MediaMTX 실행 설정입니다.
    반환값:
        MediaMtxProcessManager 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """MediaMTX 프로세스 관리 상태를 초기화합니다.

        인자:
            config: MediaMTX 실행 설정입니다.
        반환값:
            없음.
        """

        self.config = config or MediaMtxConfig()
        self.process = None
        self._log_handle = None

    def is_running(self):
        """MediaMTX 프로세스가 이미 실행 중인지 확인합니다.

        인자:
            없음.
        반환값:
            실행 중이면 True, 아니면 False를 반환합니다.
        """

        return self.process is not None and self.process.poll() is None

    def start(self):
        """MediaMTX를 백그라운드 프로세스로 실행합니다.

        인자:
            없음.
        반환값:
            새로 실행한 subprocess.Popen 객체 또는 이미 실행 중일 때 None을 반환합니다.
        """

        if self.is_running():
            return None

        self._log_handle = self.config.log_path.open("ab")
        self.process = subprocess.Popen(
            [str(self.config.binary_path.resolve())],
            cwd=str(self.config.work_path),
            stdout=self._log_handle,
            stderr=subprocess.STDOUT,
        )
        time.sleep(2)
        if self.process.poll() is not None:
            raise RuntimeError(f"MediaMTX 실행 직후 종료됐습니다. 로그를 확인하세요: {self.config.log_path}")
        return self.process

    def stop(self):
        """이 관리자가 실행한 MediaMTX 프로세스를 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)

        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
