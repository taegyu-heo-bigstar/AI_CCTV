# receiver.py 파일입니다.
# AI CCTV 프로젝트의 streaming 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

# receiver.py ?????.
# AI CCTV ????? streaming ???? ???? ?? ?????.
# ? ??? ???? ?? ??? ? ?? docstring? ???? ????.

# RTSP ?? ???? ?? ?????.
# ?? ?? ??? legacy_rtsp_receiver? ???? ????.
# ???? ??? ??? ???? ?? ?????.

import cv2
import os

#지연 시간을 줄이는 기본 옵션
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "fflags;nobuffer|flags;low_delay"

# 라즈베리파이의 IP 주소
RTSP_URL = "rtsp://10.60.242.11:8554/stream"

print(f"[{RTSP_URL}] 에 연결중")

cap = cv2.VideoCapture(RTSP_URL)

if not cap.isOpened():
    print("에러: RTSP 스트림에 연결할 수 없습니다.")
    print("라즈베리파이에서 sender.py가 실행 중인지 확인하세요.")
    print("IP 주소가 정확한지 확인하세요.")
    exit()

print("연결 성공. 실시간 영상을 수신합니다.")

while True:
    ret, frame = cap.read()

    if not ret:
        print("프레임 수신 실패")
        break

    # ==========================================================
    # 모델 들어갈 자리
    # ==========================================================

    # 화면 띄우기
    cv2.imshow("AI CCTV Receiver", frame)

    #q 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord("q"):
        print("수신을 종료합니다.")
        break

cap.release()
cv2.destroyAllWindows()
