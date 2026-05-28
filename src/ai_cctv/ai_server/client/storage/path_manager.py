# AI CCTV 저장 경로를 생성하고 관리하는 파일입니다.
# 사용자 선택 루트 아래에 표준 하위 폴더를 만듭니다.
# UI 설정 화면과 녹화 매니저가 같은 경로 규칙을 사용하게 합니다.

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StoragePaths:
    """저장소 경로 묶음을 표현합니다.

    인자:
        root_path: 사용자가 선택한 최상위 저장 위치입니다.
        ai_cctv_path: AI_CCTV 표준 저장 폴더입니다.
        original_recordings_path: 원본 녹화 파일 저장 폴더입니다.
        event_clips_path: 이벤트 클립 저장 폴더입니다.
    반환값:
        dataclass 생성자는 StoragePaths 인스턴스를 반환합니다.
    """

    root_path: str
    ai_cctv_path: str
    original_recordings_path: str
    event_clips_path: str


class StoragePathManager:
    """AI CCTV 저장 폴더 구조를 생성합니다.

    인자:
        app_folder_name: 사용자 선택 경로 아래에 만들 애플리케이션 폴더명입니다.
        original_folder_name: 원본 녹화 폴더명입니다.
        event_folder_name: 이벤트 클립 폴더명입니다.
    반환값:
        StoragePathManager 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        app_folder_name="AI_CCTV",
        original_folder_name="original_records",
        event_folder_name="event_clips",
    ):
        """저장 경로 규칙을 초기화합니다.

        인자:
            app_folder_name: 애플리케이션 저장 폴더 이름입니다.
            original_folder_name: 원본 녹화 하위 폴더 이름입니다.
            event_folder_name: 이벤트 클립 하위 폴더 이름입니다.
        반환값:
            없음.
        """

        self.app_folder_name = app_folder_name
        self.original_folder_name = original_folder_name
        self.event_folder_name = event_folder_name

    def build_paths(self, root_path):
        """루트 경로 기준의 표준 저장 경로를 계산합니다.

        인자:
            root_path: 사용자가 선택한 최상위 저장 위치입니다.
        반환값:
            StoragePaths 객체를 반환합니다.
        """

        ai_cctv_path = os.path.join(root_path, self.app_folder_name)
        return StoragePaths(
            root_path=root_path,
            ai_cctv_path=ai_cctv_path,
            original_recordings_path=os.path.join(
                ai_cctv_path,
                self.original_folder_name,
            ),
            event_clips_path=os.path.join(ai_cctv_path, self.event_folder_name),
        )

    def ensure_paths(self, root_path):
        """표준 저장 폴더를 만들고 경로 묶음을 반환합니다.

        인자:
            root_path: 사용자가 선택한 최상위 저장 위치입니다.
        반환값:
            생성된 StoragePaths 객체를 반환합니다.
        """

        paths = self.build_paths(root_path)
        os.makedirs(paths.original_recordings_path, exist_ok=True)
        os.makedirs(paths.event_clips_path, exist_ok=True)
        return paths
