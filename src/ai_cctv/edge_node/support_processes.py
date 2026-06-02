# Edge node 보조 프로세스 관리 파일입니다.
# 기본 Edge 실행에서 상태 MQTT publisher와 백업 복구 API를 함께 실행합니다.
# GStreamer 송출 프로세스와 같은 생명주기로 보조 프로세스를 시작하고 정리합니다.

import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from ..config import get_env_bool, get_env_int


@dataclass(frozen=True)
class EdgeSupportProcessConfig:
    """Edge node 보조 프로세스 실행 여부와 Python 실행 파일을 보관합니다.

    인자:
        enabled: 보조 프로세스를 실행할지 여부입니다.
        run_mqtt_broker: Edge node 내장 MQTT broker 실행 여부입니다.
        run_resource_monitor: MQTT 자원 상태 publisher 실행 여부입니다.
        run_backup_recovery: FastAPI 백업 복구 서버 실행 여부입니다.
        python_executable: 하위 Python 모듈 실행에 사용할 Python 경로입니다.
        suppress_startup_info: 보조 프로세스의 중복 연결 정보 출력을 숨길지 여부입니다.
    반환값:
        EdgeSupportProcessConfig 인스턴스를 반환합니다.
    """

    enabled: bool = True
    run_mqtt_broker: bool = True
    run_resource_monitor: bool = True
    run_backup_recovery: bool = True
    python_executable: str = sys.executable
    suppress_startup_info: bool = True


class EdgeSupportProcessManager:
    """Edge node 보조 프로세스의 시작과 종료 책임을 담당합니다.

    인자:
        config: 보조 프로세스 실행 설정입니다.
    반환값:
        EdgeSupportProcessManager 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """보조 프로세스 관리자 상태를 초기화합니다.

        인자:
            config: 보조 프로세스 실행 설정이며 없으면 기본 설정을 사용합니다.
        반환값:
            없음.
        """

        self.config = config or EdgeSupportProcessConfig()
        self.processes = []

    def start_mqtt_broker(self):
        """Edge node 내장 MQTT broker를 하위 프로세스로 실행합니다.

        인자:
            없음.
        반환값:
            실행한 subprocess.Popen 객체 또는 실행하지 않았을 때 None을 반환합니다.
        """

        if not self.config.enabled or not self.config.run_mqtt_broker:
            return None

        process = self._start_module("ai_cctv.edge_node.monitoring.mqtt_broker")
        broker_port = get_env_int("AI_CCTV_MQTT_PORT", 1883)
        if self._wait_for_tcp_port("127.0.0.1", broker_port):
            return process

        if process.poll() is not None:
            raise RuntimeError("Edge node MQTT broker 프로세스가 시작 직후 종료되었습니다.")
        raise RuntimeError("Edge node MQTT broker 포트가 열리지 않았습니다.")

    def start_backup_recovery(self, backup_dir):
        """백업 복구 FastAPI 서버를 하위 프로세스로 실행합니다.

        인자:
            backup_dir: 복구 API가 읽을 Edge node 로컬 백업 폴더입니다.
        반환값:
            실행한 subprocess.Popen 객체 또는 실행하지 않았을 때 None을 반환합니다.
        """

        if not self.config.enabled or not self.config.run_backup_recovery:
            return None

        args = ["--backup-dir", str(backup_dir)]
        if self.config.suppress_startup_info:
            args.append("--no-startup-info")
        process = self._start_module("ai_cctv.edge_node.backup_recovery_server", args)
        recovery_port = get_env_int("AI_CCTV_BACKUP_RECOVERY_PORT", 8002)
        health_url = f"http://127.0.0.1:{recovery_port}/health"
        if self._wait_for_http_health(health_url):
            return process

        if process.poll() is not None:
            raise RuntimeError("Edge node 백업 복구 서버가 시작 직후 종료되었습니다.")
        raise RuntimeError("Edge node 백업 복구 서버 health 확인에 실패했습니다.")

    def start_resource_monitor(self, monitored_process_id=None):
        """MQTT 자원 상태 publisher를 하위 프로세스로 실행합니다.

        인자:
            monitored_process_id: 상태 JSON에 포함할 감시 대상 프로세스 ID입니다.
        반환값:
            실행한 subprocess.Popen 객체 또는 실행하지 않았을 때 None을 반환합니다.
        """

        if not self.config.enabled or not self.config.run_resource_monitor:
            return None

        args = []
        if monitored_process_id is not None:
            args.extend(["--process-id", str(monitored_process_id)])
        if self.config.suppress_startup_info:
            args.append("--no-startup-info")
        return self._start_module(
            "ai_cctv.edge_node.monitoring.resource_monitor_publisher",
            args,
        )

    def stop(self):
        """이 관리자가 실행한 보조 프로세스를 모두 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        for process in reversed(self.processes):
            if process.poll() is not None:
                continue
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        self.processes.clear()

    def _start_module(self, module_name, args=None):
        """Python 모듈을 하위 프로세스로 실행하고 목록에 등록합니다.

        인자:
            module_name: python -m으로 실행할 모듈 이름입니다.
            env: 하위 프로세스에 전달할 환경 변수 딕셔너리입니다.
        반환값:
            실행한 subprocess.Popen 객체를 반환합니다.
        """

        command = [self.config.python_executable, "-m", module_name]
        if args:
            command.extend(args)
        process = subprocess.Popen(command)
        self.processes.append(process)
        return process

    def _wait_for_tcp_port(self, host, port, timeout_seconds=3.0):
        """지정한 TCP 포트가 연결 가능한 상태가 될 때까지 짧게 대기합니다.

        인자:
            host: 확인할 호스트 주소입니다.
            port: 확인할 TCP 포트입니다.
            timeout_seconds: 최대 대기 시간입니다.
        반환값:
            연결 가능하면 True, 제한 시간까지 실패하면 False를 반환합니다.
        """

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.2):
                    return True
            except OSError:
                time.sleep(0.1)
        return False

    def _wait_for_http_health(self, health_url, timeout_seconds=5.0):
        """지정한 HTTP health endpoint가 200을 반환할 때까지 대기합니다.

        인자:
            health_url: 확인할 HTTP health endpoint URL입니다.
            timeout_seconds: 최대 대기 시간입니다.
        반환값:
            HTTP 200 응답을 받으면 True, 제한 시간까지 실패하면 False를 반환합니다.
        """

        deadline = time.monotonic() + timeout_seconds
        request = Request(health_url, method="GET")
        while time.monotonic() < deadline:
            try:
                with urlopen(request, timeout=0.5) as response:
                    if response.status == 200:
                        return True
            except (HTTPError, OSError, URLError, TimeoutError):
                time.sleep(0.1)
        return False

    def _build_environment(self, extra_env=None):
        """보조 프로세스에 전달할 환경 변수를 생성합니다.

        인자:
            extra_env: 기본 환경에 추가할 환경 변수 딕셔너리입니다.
        반환값:
            하위 프로세스용 환경 변수 딕셔너리를 반환합니다.
        """

        return dict(extra_env or {})


def build_support_process_config_from_environment():
    """환경 변수 기준으로 Edge node 보조 프로세스 실행 설정을 생성합니다.

    인자:
        없음.
    반환값:
        EdgeSupportProcessConfig 인스턴스를 반환합니다.
    """

    return EdgeSupportProcessConfig(
        enabled=get_env_bool("AI_CCTV_EDGE_ENABLE_SUPPORT_SERVICES", True),
        run_mqtt_broker=get_env_bool("AI_CCTV_EDGE_ENABLE_MQTT_BROKER", True),
        run_resource_monitor=get_env_bool("AI_CCTV_EDGE_ENABLE_MONITOR", True),
        run_backup_recovery=get_env_bool("AI_CCTV_EDGE_ENABLE_RECOVERY", True),
    )


def build_support_process_manager_from_environment():
    """환경 변수 기준으로 Edge node 보조 프로세스 관리자를 생성합니다.

    인자:
        없음.
    반환값:
        EdgeSupportProcessManager 인스턴스를 반환합니다.
    """

    return EdgeSupportProcessManager(build_support_process_config_from_environment())


def _read_bool_env(name, default):
    """환경 변수 문자열을 bool 값으로 변환합니다.

    인자:
        name: 읽을 환경 변수 이름입니다.
        default: 환경 변수가 없을 때 사용할 기본값입니다.
    반환값:
        bool 값을 반환합니다.
    """

    return get_env_bool(name, default)
