# AI server RTSP 수신 미리보기 파일입니다.
# MediaMTX로 송출된 Edge node 영상을 OpenCV 창으로 확인하는 보조 기능을 제공합니다.
# 장기 분석 파이프라인은 VideoWorker가 담당하고, 이 파일은 수동 연결 점검에 집중합니다.

import os

import cv2


DEFAULT_RTSP_URL = "rtsp://10.60.242.11:8554/stream"


class RtspPreviewSession:
    """RTSP 스트림을 OpenCV 창으로 미리보기하는 세션입니다.

    인자:
        rtsp_url: 수신할 RTSP 스트림 URL입니다.
    반환값:
        RtspPreviewSession 인스턴스를 반환합니다.
    """

    def __init__(self, rtsp_url=DEFAULT_RTSP_URL):
        """RTSP 미리보기 세션을 초기화합니다.

        인자:
            rtsp_url: 수신할 RTSP 스트림 URL입니다.
        반환값:
            없음.
        """

        self.rtsp_url = rtsp_url

    def run(self):
        """RTSP 스트림을 수신하여 OpenCV 창에 표시합니다.

        인자:
            없음.
        반환값:
            연결 실패 또는 정상 종료 시 None을 반환합니다.
        """

        self._configure_low_latency_capture()
        print(f"[{self.rtsp_url}] 에 연결중")

        capture = cv2.VideoCapture(self.rtsp_url)
        if not capture.isOpened():
            print("에러: RTSP 스트림에 연결할 수 없습니다.")
            print("Raspberry Pi에서 GStreamer + MediaMTX 송출이 실행 중인지 확인하세요.")
            print("IP 주소와 포트가 정확한지 확인하세요.")
            return None

        print("연결 성공. 실시간 영상을 수신합니다.")
        self._show_frames(capture)
        return None

    def _configure_low_latency_capture(self):
        """OpenCV FFMPEG 수신 옵션을 낮은 지연 설정으로 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "fflags;nobuffer|flags;low_delay"

    def _show_frames(self, capture):
        """VideoCapture에서 프레임을 읽어 미리보기 창에 표시합니다.

        인자:
            capture: OpenCV VideoCapture 객체입니다.
        반환값:
            없음.
        """

        while True:
            frame_received, frame = capture.read()
            if not frame_received:
                print("프레임 수신 실패")
                break

            cv2.imshow("AI CCTV Receiver", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                print("수신을 종료합니다.")
                break

        capture.release()
        cv2.destroyAllWindows()


def preview_rtsp_stream(rtsp_url=DEFAULT_RTSP_URL):
    """RTSP 미리보기 세션을 생성해 실행합니다.

    인자:
        rtsp_url: 수신할 RTSP 스트림 URL입니다.
    반환값:
        연결 실패 또는 정상 종료 시 None을 반환합니다.
    """

    return RtspPreviewSession(rtsp_url).run()


def main():
    """기본 RTSP URL로 수신 미리보기를 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    preview_rtsp_stream()


if __name__ == "__main__":
    main()
