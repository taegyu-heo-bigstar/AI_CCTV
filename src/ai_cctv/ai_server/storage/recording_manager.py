# AI CCTV 원본 영상 녹화 매니저 파일입니다.
# 프레임을 MP4 파일로 저장하고 일정 시간 단위로 파일을 분할합니다.
# 저장 폴더명은 StoragePathManager와 동일한 규칙을 사용합니다.

import os
from datetime import datetime

import cv2


class RecordingManager:
    """원본 영상 프레임을 시간 단위 MP4 파일로 저장합니다.

    인자:
        base_dir: AI_CCTV 저장 루트 경로입니다.
        fps: 저장할 영상 FPS입니다.
        frame_size: 저장할 프레임 크기 튜플입니다.
        segment_seconds: 파일을 분할할 시간 단위입니다.
    반환값:
        RecordingManager 인스턴스를 반환합니다.
    """

    def __init__(self, base_dir, fps=30, frame_size=None, segment_seconds=60):
        """녹화 저장 상태와 기본 경로를 초기화합니다.

        인자:
            base_dir: AI_CCTV 저장 루트 경로입니다.
            fps: 저장할 영상 FPS입니다.
            frame_size: 저장할 프레임 크기 튜플입니다.
            segment_seconds: 파일을 분할할 시간 단위입니다.
        반환값:
            없음.
        """

        self.base_dir = base_dir
        self.fps = fps
        self.frame_size = frame_size
        self.segment_seconds = segment_seconds
        self.writer = None
        self.recording_dir = os.path.join(self.base_dir, "original_records")
        os.makedirs(self.recording_dir, exist_ok=True)

        self.start_time = None
        self.start_time_str = None
        self.temp_save_path = None

    def start_recording(self, frame_size):
        """새 MP4 녹화 파일을 시작합니다.

        인자:
            frame_size: 현재 프레임의 (width, height) 크기입니다.
        반환값:
            writer 생성에 성공하면 True, 실패하면 False를 반환합니다.
        """

        self.frame_size = frame_size
        self.start_time = datetime.now()
        self.start_time_str = self.start_time.strftime("%Y-%m-%d_%H-%M-%S")
        temp_filename = f"recording_{self.start_time_str}.mp4"
        self.temp_save_path = os.path.join(self.recording_dir, temp_filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            self.temp_save_path,
            fourcc,
            self.fps,
            self.frame_size,
        )

        if not self.writer.isOpened():
            print("원본 영상 저장 Writer 생성 실패")
            self.writer = None
            return False

        print(f"원본 영상 저장 시작: {self.temp_save_path}")
        return True

    def write_frame(self, frame):
        """프레임을 현재 녹화 파일에 기록합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            없음.
        """

        if frame is None:
            return

        height, width = frame.shape[:2]
        current_frame_size = (width, height)
        if self.writer is None:
            self.start_recording(current_frame_size)
        if self.writer is None:
            return

        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        if elapsed_seconds >= self.segment_seconds:
            self.stop_recording()
            self.start_recording(current_frame_size)

        if self.writer is not None:
            self.writer.write(frame)

    def stop_recording(self):
        """현재 녹화 파일을 닫고 최종 파일명으로 변경합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.writer is None:
            return

        self.writer.release()
        self.writer = None

        end_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        final_filename = f"{self.start_time_str}~{end_time_str}.mp4"
        final_save_path = os.path.join(self.recording_dir, final_filename)

        try:
            os.rename(self.temp_save_path, final_save_path)
            print(f"원본 영상 저장 종료: {final_save_path}")
        except Exception as error:
            print(f"파일 이름 변경 실패: {error}")

        self.start_time = None
        self.start_time_str = None
        self.temp_save_path = None
