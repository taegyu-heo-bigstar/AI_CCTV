# RTSP 스트림 수신 안정화 파일입니다.
# AI server가 라즈베리파이 RTSP 스트림을 별도 thread에서 읽도록 합니다.
# TCP 포트 확인, FFmpeg timeout, watchdog, 재연결 루프를 묶어 OpenCV 장기 대기를 줄입니다.
# VideoStream은 이 객체를 통해 최신 RTSP 프레임을 가져옵니다.

import socket
import threading
import time
from dataclasses import dataclass
from urllib.parse import urlparse

DEFAULT_FFMPEG_CAPTURE_OPTIONS = "rtsp_transport;tcp;stimeout;2000000;timeout;2000000"


@dataclass(frozen=True)
class RtspFrameSnapshot:
    """RTSP 수신기가 보관한 최신 프레임 상태를 표현합니다.

    인자:
        success: 새 프레임을 반환할 수 있는지 여부입니다.
        frame: OpenCV BGR 프레임이며 실패 시 None입니다.
        sequence: 프레임 갱신 순번입니다.
        connected: 현재 RTSP 캡처가 연결 상태인지 여부입니다.
        error: 마지막 수신 오류 메시지입니다.
    반환값:
        RtspFrameSnapshot 인스턴스를 반환합니다.
    """

    success: bool
    frame: object
    sequence: int
    connected: bool
    error: str = ""


def is_rtsp_source(source):
    """입력 소스가 RTSP URL인지 확인합니다.

    인자:
        source: OpenCV 입력 소스 값입니다.
    반환값:
        rtsp:// 문자열이면 True, 아니면 False를 반환합니다.
    """

    return isinstance(source, str) and source.lower().startswith("rtsp://")


def check_rtsp_port_open(rtsp_url, timeout_seconds=1.5):
    """RTSP URL의 TCP 포트가 열려 있는지 빠르게 확인합니다.

    인자:
        rtsp_url: 확인할 RTSP URL입니다.
        timeout_seconds: TCP 연결 시도 제한 시간입니다.
    반환값:
        포트 연결에 성공하면 True, 실패하면 False를 반환합니다.
    """

    parsed_url = urlparse(rtsp_url)
    hostname = parsed_url.hostname
    port = parsed_url.port or 8554
    if not hostname:
        return False

    try:
        with socket.create_connection((hostname, port), timeout=timeout_seconds):
            return True
    except OSError:
        return False


class RtspFrameReceiver:
    """RTSP 프레임을 백그라운드에서 수신하고 재연결을 관리합니다.

    인자:
        rtsp_url: 수신할 RTSP URL입니다.
        reconnect_interval_seconds: 재연결 전 대기 시간입니다.
        port_timeout_seconds: TCP 포트 확인 제한 시간입니다.
        frame_timeout_seconds: 최신 프레임 대기 제한 시간입니다.
        watchdog_timeout_seconds: 새 프레임이 없을 때 capture를 강제 해제할 기준 시간입니다.
        watchdog_interval_seconds: watchdog 점검 주기입니다.
    반환값:
        RtspFrameReceiver 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        rtsp_url,
        reconnect_interval_seconds=3.0,
        port_timeout_seconds=1.5,
        frame_timeout_seconds=0.1,
        watchdog_timeout_seconds=5.0,
        watchdog_interval_seconds=1.0,
    ):
        """RTSP 수신 thread 상태와 동기화 객체를 초기화합니다.

        인자:
            rtsp_url: 수신할 RTSP URL입니다.
            reconnect_interval_seconds: 연결 실패 후 재시도 대기 시간입니다.
            port_timeout_seconds: TCP 포트 확인 제한 시간입니다.
            frame_timeout_seconds: read 호출에서 새 프레임을 기다릴 시간입니다.
            watchdog_timeout_seconds: 새 프레임이 없을 때 capture를 강제 해제할 기준 시간입니다.
            watchdog_interval_seconds: watchdog 점검 주기입니다.
        반환값:
            없음.
        """

        self.rtsp_url = rtsp_url
        self.reconnect_interval_seconds = reconnect_interval_seconds
        self.port_timeout_seconds = port_timeout_seconds
        self.frame_timeout_seconds = frame_timeout_seconds
        self.watchdog_timeout_seconds = watchdog_timeout_seconds
        self.watchdog_interval_seconds = watchdog_interval_seconds
        self.running = False
        self.connected = False
        self.last_error = ""
        self.frame = None
        self.frame_sequence = 0
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.thread = None
        self.watchdog_thread = None
        self.active_capture = None
        self.last_frame_received_at = time.monotonic()
        self.capture_lock = threading.Lock()
        self.condition = threading.Condition()

    def start(self):
        """RTSP 수신 thread를 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.thread is not None and self.thread.is_alive():
            return

        self.running = True
        self.last_frame_received_at = time.monotonic()
        self.thread = threading.Thread(
            target=self._receive_loop,
            name="RtspFrameReceiver",
            daemon=True,
        )
        self.thread.start()
        self.watchdog_thread = threading.Thread(
            target=self._watchdog_loop,
            name="RtspFrameReceiverWatchdog",
            daemon=True,
        )
        self.watchdog_thread.start()

    def read_new_frame(self, last_sequence=0):
        """이전 순번 이후의 최신 프레임을 반환합니다.

        인자:
            last_sequence: 호출자가 마지막으로 받은 프레임 순번입니다.
        반환값:
            RtspFrameSnapshot 객체를 반환합니다.
        """

        deadline = time.monotonic() + self.frame_timeout_seconds
        with self.condition:
            while (
                self.running
                and self.frame_sequence <= last_sequence
                and time.monotonic() < deadline
            ):
                remaining = max(0.0, deadline - time.monotonic())
                self.condition.wait(timeout=remaining)

            if self.frame is None or self.frame_sequence <= last_sequence:
                return RtspFrameSnapshot(
                    success=False,
                    frame=None,
                    sequence=last_sequence,
                    connected=self.connected,
                    error=self.last_error,
                )

            return RtspFrameSnapshot(
                success=True,
                frame=self.frame.copy(),
                sequence=self.frame_sequence,
                connected=self.connected,
                error=self.last_error,
            )

    def stop(self):
        """RTSP 수신 thread를 중지합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False
        self._release_active_capture("RTSP 수신 중지 요청")
        with self.condition:
            self.condition.notify_all()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=3)
        if self.watchdog_thread is not None and self.watchdog_thread.is_alive():
            self.watchdog_thread.join(timeout=3)

    def _watchdog_loop(self):
        """프레임 정체가 길어지면 활성 VideoCapture를 강제로 해제합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        while self.running:
            time.sleep(self.watchdog_interval_seconds)
            if not self.running:
                break
            if not self._has_active_capture():
                continue

            elapsed_seconds = time.monotonic() - self.last_frame_received_at
            if elapsed_seconds < self.watchdog_timeout_seconds:
                continue

            released = self._release_active_capture(
                "RTSP 프레임 수신 watchdog timeout"
            )
            if released:
                self._set_connection_state(
                    False,
                    "RTSP 프레임 수신 watchdog timeout",
                )

    def _receive_loop(self):
        """RTSP 연결과 프레임 수신을 반복합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        while self.running:
            if not check_rtsp_port_open(self.rtsp_url, self.port_timeout_seconds):
                self._set_connection_state(False, "RTSP 포트 연결 실패")
                time.sleep(self.reconnect_interval_seconds)
                continue

            import cv2

            cap = cv2.VideoCapture(self.rtsp_url)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not cap.isOpened():
                cap.release()
                self._set_connection_state(False, "RTSP 스트림 열기 실패")
                time.sleep(self.reconnect_interval_seconds)
                continue

            self._set_active_capture(cap)
            try:
                self._update_capture_metadata(cap)
                self._set_connection_state(True, "")
                self._read_capture_until_failure(cap)
            finally:
                self._clear_active_capture(cap)
                cap.release()

            if self.running:
                self._set_connection_state(False, "RTSP 프레임 수신 중단")
                time.sleep(self.reconnect_interval_seconds)

    def _read_capture_until_failure(self, cap):
        """열려 있는 VideoCapture에서 프레임을 읽고 실패 시 루프를 종료합니다.

        인자:
            cap: OpenCV VideoCapture 객체입니다.
        반환값:
            없음.
        """

        consecutive_failures = 0
        while self.running:
            try:
                success, frame = cap.read()
            except Exception as error:
                self._set_connection_state(False, f"RTSP 프레임 읽기 오류: {error}")
                break

            if not success:
                if not self._is_active_capture(cap):
                    break
                consecutive_failures += 1
                if consecutive_failures >= 80:
                    break
                time.sleep(0.01)
                continue

            consecutive_failures = 0
            self._store_frame(frame)

    def _set_active_capture(self, cap):
        """watchdog이 감시할 현재 VideoCapture 객체를 등록합니다.

        인자:
            cap: 현재 RTSP 수신 루프에서 사용하는 OpenCV VideoCapture 객체입니다.
        반환값:
            없음.
        """

        with self.capture_lock:
            self.active_capture = cap
        self.last_frame_received_at = time.monotonic()

    def _clear_active_capture(self, cap):
        """현재 VideoCapture 객체가 감시 대상이면 등록을 해제합니다.

        인자:
            cap: 등록 해제할 OpenCV VideoCapture 객체입니다.
        반환값:
            없음.
        """

        with self.capture_lock:
            if self.active_capture is cap:
                self.active_capture = None

    def _has_active_capture(self):
        """watchdog이 해제할 수 있는 활성 VideoCapture가 있는지 반환합니다.

        인자:
            없음.
        반환값:
            활성 VideoCapture가 있으면 True, 없으면 False를 반환합니다.
        """

        with self.capture_lock:
            return self.active_capture is not None

    def _is_active_capture(self, cap):
        """전달된 VideoCapture가 현재 감시 대상인지 확인합니다.

        인자:
            cap: 비교할 OpenCV VideoCapture 객체입니다.
        반환값:
            현재 감시 대상이면 True, 아니면 False를 반환합니다.
        """

        with self.capture_lock:
            return self.active_capture is cap

    def _release_active_capture(self, reason):
        """watchdog 또는 종료 요청이 활성 VideoCapture를 강제로 해제합니다.

        인자:
            reason: 강제 해제 사유 메시지입니다.
        반환값:
            실제 release를 호출했으면 True, 대상이 없으면 False를 반환합니다.
        """

        with self.capture_lock:
            cap = self.active_capture
            self.active_capture = None

        if cap is None:
            return False

        try:
            cap.release()
        except Exception as error:
            self._set_connection_state(False, f"{reason}: {error}")
            return False
        return True

    def _store_frame(self, frame):
        """수신한 최신 프레임을 thread-safe하게 저장합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            없음.
        """

        height, width = frame.shape[:2]
        self.last_frame_received_at = time.monotonic()
        with self.condition:
            self.frame = frame.copy()
            self.frame_width = width
            self.frame_height = height
            self.frame_sequence += 1
            self.connected = True
            self.last_error = ""
            self.condition.notify_all()

    def _set_connection_state(self, connected, error):
        """RTSP 연결 상태와 마지막 오류 메시지를 갱신합니다.

        인자:
            connected: 현재 연결 여부입니다.
            error: 마지막 오류 메시지입니다.
        반환값:
            없음.
        """

        with self.condition:
            self.connected = connected
            self.last_error = error
            self.condition.notify_all()

    def _update_capture_metadata(self, cap):
        """VideoCapture에서 FPS와 프레임 크기 정보를 읽어 저장합니다.

        인자:
            cap: OpenCV VideoCapture 객체입니다.
        반환값:
            없음.
        """

        import cv2

        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        with self.condition:
            if fps and fps > 0:
                self.fps = fps
            if width > 0 and height > 0:
                self.frame_width = width
                self.frame_height = height
