# 영상 입력 스트림 추상화 파일입니다.
# 웹캠과 RTSP 입력을 같은 read/open/release 인터페이스로 제공합니다.
# RTSP 입력은 별도 수신 thread를 사용해 단선 후 재연결을 시도합니다.
# 복구 서버 URL이 설정되면 RTSP 장애 구간의 백업 영상 요청도 기록합니다.

import cv2

from ..recovery import build_network_recovery_manager_from_env
from .rtsp_receiver import RtspFrameReceiver, is_rtsp_source


class VideoStream:
    """웹캠 또는 RTSP 영상 입력을 공통 인터페이스로 감쌉니다.

    인자:
        source: OpenCV 카메라 번호 또는 RTSP URL입니다.
        recovery_manager: RTSP 복구 요청을 담당하는 객체입니다.
    반환값:
        VideoStream 인스턴스를 반환합니다.
    """

    def __init__(self, source=0, recovery_manager=None):
        """입력 소스와 RTSP 수신 상태를 초기화합니다.

        인자:
            source: OpenCV 카메라 번호 또는 RTSP URL입니다.
            recovery_manager: 네트워크 복구 요청 관리자이며 없으면 환경 변수에서 생성합니다.
        반환값:
            없음.
        """

        self.source = source
        self.cap = None
        self.receiver = None
        self.is_rtsp = is_rtsp_source(source)
        self.last_rtsp_sequence = 0
        self.recovery_manager = recovery_manager
        if self.is_rtsp and self.recovery_manager is None:
            self.recovery_manager = build_network_recovery_manager_from_env()
        self.last_recovery_result = None

    def open(self):
        """영상 입력을 엽니다.

        인자:
            없음.
        반환값:
            입력 준비에 성공하면 True, 실패하면 False를 반환합니다.
        """

        if self.is_rtsp:
            self.receiver = RtspFrameReceiver(self.source)
            self.receiver.start()
            return True

        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            print("영상 스트림 연결 실패")
            return False

        print("영상 스트림 연결 성공")
        return True

    def read(self):
        """최신 영상 프레임을 읽습니다.

        인자:
            없음.
        반환값:
            성공 여부와 OpenCV BGR 프레임 튜플을 반환합니다.
        """

        if self.is_rtsp:
            return self._read_rtsp_frame()

        if self.cap is None:
            return False, None
        return self.cap.read()

    def get_fps(self):
        """입력 영상의 FPS를 반환합니다.

        인자:
            없음.
        반환값:
            FPS 숫자를 반환하며 알 수 없으면 30을 반환합니다.
        """

        if self.is_rtsp:
            return self.receiver.fps if self.receiver is not None else 30

        if self.cap is None:
            return 30

        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            return 30
        return fps

    def get_frame_size(self):
        """입력 영상의 프레임 크기를 반환합니다.

        인자:
            없음.
        반환값:
            (width, height) 튜플을 반환합니다.
        """

        if self.is_rtsp:
            if self.receiver is None:
                return 640, 480
            return self.receiver.frame_width, self.receiver.frame_height

        if self.cap is None:
            return 640, 480

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return width, height

    def is_recovering(self):
        """RTSP 입력이 현재 복구 대기 상태인지 반환합니다.

        인자:
            없음.
        반환값:
            RTSP 연결이 아직 프레임을 주지 못하면 True를 반환합니다.
        """

        return self.is_rtsp and (
            self.receiver is None or not self.receiver.connected
        )

    def get_last_recovery_result(self):
        """마지막 백업 복구 요청 결과를 반환합니다.

        인자:
            없음.
        반환값:
            복구 요청 결과 딕셔너리 또는 None을 반환합니다.
        """

        return self.last_recovery_result

    def release(self):
        """영상 입력 자원을 해제합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.receiver is not None:
            self.receiver.stop()
            self.receiver = None

        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _read_rtsp_frame(self):
        """RTSP 수신기에서 새 프레임을 가져오고 장애/복구 상태를 기록합니다.

        인자:
            없음.
        반환값:
            성공 여부와 OpenCV BGR 프레임 튜플을 반환합니다.
        """

        if self.receiver is None:
            return False, None

        snapshot = self.receiver.read_new_frame(self.last_rtsp_sequence)
        if not snapshot.success:
            self._record_rtsp_failure()
            return False, None

        self.last_rtsp_sequence = snapshot.sequence
        self._record_rtsp_recovery()
        return True, snapshot.frame

    def _record_rtsp_failure(self):
        """RTSP 프레임 미수신 상태를 복구 관리자에 기록합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.recovery_manager is not None:
            self.recovery_manager.record_failure()

    def _record_rtsp_recovery(self):
        """RTSP 프레임 재수신 상태를 복구 관리자에 기록합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if (
            self.recovery_manager is not None
            and self.recovery_manager.has_active_failure()
        ):
            self.last_recovery_result = self.recovery_manager.record_recovery()
