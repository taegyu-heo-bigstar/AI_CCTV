# video_stream.py 파일입니다.
# AI CCTV 프로젝트의 analysis 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

import cv2


class VideoStream:
    """VideoStream 클래스의 주요 책임을 수행합니다.
    
    인자:
        생성자 인자는 __init__ 문서를 따릅니다.
    반환값:
        VideoStream 인스턴스를 반환합니다.
    """
    def __init__(self, source=0):
        """__init__ 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.source = source
        self.cap = None

    def open(self):
        """open 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.cap = cv2.VideoCapture(self.source)

        if not self.cap.isOpened():
            print("영상 스트림 연결 실패")
            return False

        print("영상 스트림 연결 성공")
        return True

    def read(self):
        """read 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.cap is None:
            return False, None

        return self.cap.read()

    def get_fps(self):
        """get_fps 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.cap is None:
            return 30

        fps = self.cap.get(cv2.CAP_PROP_FPS)

        if fps <= 0:
            return 30

        return fps

    def get_frame_size(self):
        """get_frame_size 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.cap is None:
            return 640, 480

        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        return width, height

    def release(self):
        """release 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None
