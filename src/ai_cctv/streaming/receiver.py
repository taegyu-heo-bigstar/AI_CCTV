# RTSP 수신 데모 실행 파일입니다.
# import 시 자동으로 네트워크 접속이나 GUI 루프가 시작되지 않도록 main 진입점을 사용합니다.
# 운영 클라이언트는 client.video_stream.VideoStream을 사용하고 이 파일은 수동 확인용입니다.

import os

import cv2


DEFAULT_RTSP_URL = "rtsp://10.60.242.11:8554/stream"


def receive_rtsp(rtsp_url=DEFAULT_RTSP_URL):
    """RTSP 스트림을 수신하여 OpenCV 창에 표시합니다.

    인자:
        rtsp_url: 수신할 RTSP 스트림 URL입니다.
    반환값:
        정상 종료 또는 연결 실패 시 None을 반환합니다.
    """

    os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "fflags;nobuffer|flags;low_delay"
    print(f"[{rtsp_url}] 에 연결중")

    cap = cv2.VideoCapture(rtsp_url)
    if not cap.isOpened():
        print("에러: RTSP 스트림에 연결할 수 없습니다.")
        print("Raspberry Pi에서 GStreamer + MediaMTX 송출이 실행 중인지 확인하세요.")
        print("IP 주소가 정확한지 확인하세요.")
        return

    print("연결 성공. 실시간 영상을 수신합니다.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("프레임 수신 실패")
            break

        cv2.imshow("AI CCTV Receiver", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("수신을 종료합니다.")
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    """RTSP 수신 데모를 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    receive_rtsp()


if __name__ == "__main__":
    main()
