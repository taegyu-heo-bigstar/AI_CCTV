# Edge node 실행 런타임 파일입니다.
# MediaMTX 준비, 로컬 백업 폴더 생성, GStreamer 실행 순서를 조율합니다.
# Raspberry Pi에서 ai-cctv-edge 명령이 실제 송출 프로세스를 실행하도록 합니다.

import signal
import subprocess

from .local_backup import LocalBackupConfig
from .mediamtx import MediaMtxConfig, MediaMtxInstaller, MediaMtxProcessManager
from .startup_info import print_edge_connection_info
from .streaming import EdgeStreamConfig, MediaMtxGStreamerCommandBuilder


class EdgeNodeRuntime:
    """Edge node 송출 프로세스의 실행 흐름을 조율합니다.

    인자:
        backup_config: 로컬 백업 저장 설정입니다.
        mediamtx_installer: MediaMTX 설치 보장 객체입니다.
        mediamtx_process_manager: MediaMTX 프로세스 관리 객체입니다.
        command_builder: GStreamer 명령 생성 객체입니다.
    반환값:
        EdgeNodeRuntime 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        backup_config=None,
        mediamtx_installer=None,
        mediamtx_process_manager=None,
        command_builder=None,
    ):
        """Edge node 런타임 의존 객체를 초기화합니다.

        인자:
            backup_config: 로컬 백업 저장 설정입니다.
            mediamtx_installer: MediaMTX 설치 보장 객체입니다.
            mediamtx_process_manager: MediaMTX 프로세스 관리 객체입니다.
            command_builder: GStreamer 명령 생성 객체입니다.
        반환값:
            없음.
        """

        mediamtx_config = MediaMtxConfig()
        self.backup_config = backup_config or LocalBackupConfig()
        self.mediamtx_installer = mediamtx_installer or MediaMtxInstaller(mediamtx_config)
        self.mediamtx_process_manager = (
            mediamtx_process_manager or MediaMtxProcessManager(mediamtx_config)
        )
        self.command_builder = command_builder or MediaMtxGStreamerCommandBuilder(
            EdgeStreamConfig(),
            self.backup_config,
        )
        self.gstreamer_process = None

    def build_command_args(self):
        """현재 런타임 설정으로 GStreamer 실행 인자를 생성합니다.

        인자:
            없음.
        반환값:
            subprocess에 전달할 GStreamer 명령 인자 리스트를 반환합니다.
        """

        return self.command_builder.build_command_args()

    def run(self):
        """MediaMTX와 GStreamer를 순서대로 실행하고 종료 시 정리합니다.

        인자:
            없음.
        반환값:
            GStreamer 프로세스 종료 코드를 반환합니다.
        """

        print_edge_connection_info(backup_dir=str(self.backup_config.directory))
        self.backup_config.ensure_directory()
        self.mediamtx_installer.ensure_installed()
        self.mediamtx_process_manager.start()
        self._install_signal_handlers()

        try:
            self.gstreamer_process = subprocess.Popen(self.build_command_args())
            return self.gstreamer_process.wait()
        finally:
            self.stop()

    def stop(self):
        """GStreamer와 이 런타임이 실행한 MediaMTX 프로세스를 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.gstreamer_process is not None and self.gstreamer_process.poll() is None:
            self.gstreamer_process.terminate()
            try:
                self.gstreamer_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.gstreamer_process.kill()
                self.gstreamer_process.wait(timeout=5)

        self.mediamtx_process_manager.stop()

    def _install_signal_handlers(self):
        """운영체제 종료 신호를 Edge node 정리 동작에 연결합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        signal.signal(signal.SIGINT, self._handle_stop_signal)
        signal.signal(signal.SIGTERM, self._handle_stop_signal)

    def _handle_stop_signal(self, signum, frame):
        """종료 신호를 받으면 실행 중인 하위 프로세스를 정리합니다.

        인자:
            signum: 수신한 운영체제 신호 번호입니다.
            frame: 신호 수신 시점의 프레임 객체입니다.
        반환값:
            없음.
        """

        self.stop()
        raise SystemExit(0)


def build_default_edge_runtime():
    """기본 설정을 사용하는 Edge node 런타임을 생성합니다.

    인자:
        없음.
    반환값:
        EdgeNodeRuntime 인스턴스를 반환합니다.
    """

    return EdgeNodeRuntime()
