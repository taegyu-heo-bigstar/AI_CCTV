# AI CCTV 이벤트 클립 저장 매니저 파일입니다.
# 추적된 인물별로 짧은 MP4 클립과 이동 궤적 이미지를 저장합니다.
# 저장 폴더명은 StoragePathManager의 event_clips 규칙과 맞춥니다.

import os
import shutil
from datetime import datetime

import cv2


class ClipManager:
    """추적 인물별 이벤트 클립 저장을 담당합니다.

    인자:
        base_dir: AI_CCTV 저장 루트 경로입니다.
        fps: 저장할 클립 영상 FPS입니다.
        max_clip_seconds: 클립 파일 하나의 최대 길이 초 단위입니다.
        disappear_timeout: 인물 사라짐 판정 대기 시간입니다.
    반환값:
        ClipManager 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        base_dir,
        fps=30,
        max_clip_seconds=10,
        disappear_timeout=3.0,
    ):
        """클립 저장 경로와 인물별 클립 상태를 초기화합니다.

        인자:
            base_dir: AI_CCTV 저장 루트 경로입니다.
            fps: 저장할 클립 영상 FPS입니다.
            max_clip_seconds: 클립 파일 하나의 최대 길이 초 단위입니다.
            disappear_timeout: 인물 사라짐 판정 대기 시간입니다.
        반환값:
            없음.
        """

        self.base_dir = base_dir
        self.fps = fps if fps and fps > 0 else 30
        self.max_clip_seconds = max_clip_seconds
        self.disappear_timeout = disappear_timeout
        self.clip_root_dir = os.path.join(self.base_dir, "event_clips")
        self.person_clips = {}

        os.makedirs(self.clip_root_dir, exist_ok=True)

    def update_person(self, person_id, frame, bbox, crop_path=None):
        """현재 프레임을 해당 인물의 이벤트 클립에 기록합니다.

        인자:
            person_id: 추적 인물 식별자입니다.
            frame: 저장할 OpenCV BGR 프레임입니다.
            bbox: 인물 바운딩 박스입니다.
            crop_path: 전신 crop 이미지 경로이며 없으면 None입니다.
        반환값:
            없음.
        """

        if frame is None or bbox is None:
            return

        state = self.person_clips.get(person_id)
        if state is None:
            state = self._create_person_state(person_id, frame)
            self.person_clips[person_id] = state

        state["last_seen"] = datetime.now()
        state["last_frame"] = frame.copy()
        state["points"].append(self._get_bbox_center(bbox))

        if crop_path is not None:
            self._copy_crop_once(state, crop_path)

        frame_size = self._get_frame_size(frame)
        if state["writer"] is None:
            self._start_new_clip(state, frame_size)

        if self._should_rotate_clip(state):
            self._close_writer(state)
            self._start_new_clip(state, frame_size)

        if state["writer"] is not None:
            state["writer"].write(frame)

    def finish_person(self, person_id):
        """인물 추적이 끝났을 때 클립 파일과 궤적 이미지를 마감합니다.

        인자:
            person_id: 추적 인물 식별자입니다.
        반환값:
            없음.
        """

        state = self.person_clips.pop(person_id, None)
        if state is None:
            return

        self._close_writer(state)
        self._save_trajectory_image(state)

    def finish_all(self):
        """현재 열려 있는 모든 인물 클립을 마감합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        for person_id in list(self.person_clips.keys()):
            self.finish_person(person_id)

    def _create_person_state(self, person_id, frame):
        """새 인물 클립 저장 상태와 전용 폴더를 생성합니다.

        인자:
            person_id: 추적 인물 식별자입니다.
            frame: 상태 초기화에 사용할 OpenCV BGR 프레임입니다.
        반환값:
            인물 클립 상태 딕셔너리를 반환합니다.
        """

        now = datetime.now()
        first_seen_text = now.strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = f"{first_seen_text}_person{person_id}_tracking"
        folder_path = self._get_unique_folder_path(folder_name)

        os.makedirs(folder_path, exist_ok=True)

        return {
            "person_id": person_id,
            "first_seen": now,
            "last_seen": now,
            "folder_path": folder_path,
            "clip_index": 0,
            "clip_started_at": None,
            "writer": None,
            "points": [],
            "last_frame": frame.copy(),
            "crop_saved": False,
        }

    def _start_new_clip(self, state, frame_size):
        """인물 상태에 새 MP4 클립 writer를 연결합니다.

        인자:
            state: 인물 클립 상태 딕셔너리입니다.
            frame_size: 저장할 프레임 크기 튜플입니다.
        반환값:
            없음.
        """

        state["clip_index"] += 1
        state["clip_started_at"] = datetime.now()

        clip_filename = f"clip_{state['clip_index']:03d}.mp4"
        clip_path = os.path.join(state["folder_path"], clip_filename)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(clip_path, fourcc, self.fps, frame_size)

        if not writer.isOpened():
            print(f"클립 영상 writer 생성 실패: {clip_path}")
            state["writer"] = None
            return

        state["writer"] = writer

    def _close_writer(self, state):
        """인물 상태에 연결된 클립 writer를 닫습니다.

        인자:
            state: 인물 클립 상태 딕셔너리입니다.
        반환값:
            없음.
        """

        writer = state.get("writer")
        if writer is not None:
            writer.release()
            state["writer"] = None

    def _should_rotate_clip(self, state):
        """현재 클립 파일을 새 파일로 분리해야 하는지 판단합니다.

        인자:
            state: 인물 클립 상태 딕셔너리입니다.
        반환값:
            최대 길이를 넘었으면 True, 아니면 False를 반환합니다.
        """

        if self.max_clip_seconds is None:
            return False

        if state["clip_started_at"] is None:
            return False

        elapsed_seconds = (datetime.now() - state["clip_started_at"]).total_seconds()
        return elapsed_seconds >= self.max_clip_seconds

    def _save_trajectory_image(self, state):
        """마지막 프레임 위에 인물 이동 궤적 이미지를 저장합니다.

        인자:
            state: 인물 클립 상태 딕셔너리입니다.
        반환값:
            없음.
        """

        frame = state.get("last_frame")
        points = state.get("points", [])

        if frame is None or len(points) == 0:
            return

        trajectory_frame = frame.copy()

        for index, point in enumerate(points):
            cv2.circle(trajectory_frame, point, 4, (0, 255, 255), -1)

            if index > 0:
                cv2.line(
                    trajectory_frame,
                    points[index - 1],
                    point,
                    (0, 255, 255),
                    2,
                )

        save_path = os.path.join(state["folder_path"], "trajectory.jpg")
        cv2.imwrite(save_path, trajectory_frame)

    def _copy_crop_once(self, state, crop_path):
        """인물 전신 crop 이미지를 클립 폴더에 한 번만 복사합니다.

        인자:
            state: 인물 클립 상태 딕셔너리입니다.
            crop_path: 복사할 전신 crop 이미지 경로입니다.
        반환값:
            없음.
        """

        if state["crop_saved"]:
            return

        if not os.path.exists(crop_path):
            return

        save_path = os.path.join(state["folder_path"], "full_crop.jpg")

        try:
            shutil.copy2(crop_path, save_path)
            state["crop_saved"] = True
        except Exception as error:
            print(f"전신 crop 복사 실패: {error}")

    def _get_bbox_center(self, bbox):
        """바운딩 박스의 중심 좌표를 계산합니다.

        인자:
            bbox: 인물 바운딩 박스입니다.
        반환값:
            (x, y) 중심 좌표 튜플을 반환합니다.
        """

        x1, y1, x2, y2 = map(int, bbox)
        return ((x1 + x2) // 2, (y1 + y2) // 2)

    def _get_frame_size(self, frame):
        """프레임에서 VideoWriter용 크기 튜플을 계산합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            (width, height) 튜플을 반환합니다.
        """

        height, width = frame.shape[:2]
        return width, height

    def _get_unique_folder_path(self, folder_name):
        """중복되지 않는 인물 클립 폴더 경로를 생성합니다.

        인자:
            folder_name: 기본 폴더명입니다.
        반환값:
            사용 가능한 폴더 경로 문자열을 반환합니다.
        """

        folder_path = os.path.join(self.clip_root_dir, folder_name)

        if not os.path.exists(folder_path):
            return folder_path

        index = 2
        while True:
            candidate = os.path.join(self.clip_root_dir, f"{folder_name}_{index}")
            if not os.path.exists(candidate):
                return candidate
            index += 1
