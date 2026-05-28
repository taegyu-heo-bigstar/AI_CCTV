# person_state_manager.py 파일입니다.
# AI CCTV 프로젝트의 control_center 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

# person_state_manager.py ?????.
# AI CCTV ????? client ???? ???? ?? ?????.
# ? ??? ???? ?? ??? ? ?? docstring? ???? ????.

# person_state_manager.py

import time


class PersonStateManager:
    """PersonStateManager 클래스의 주요 책임을 수행합니다.
    
    인자:
        생성자 인자는 __init__ 문서를 따릅니다.
    반환값:
        PersonStateManager 인스턴스를 반환합니다.
    """
    def __init__(self, disappear_timeout=3.0):
        """__init__ 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.person_states = {}
        self.disappear_timeout = disappear_timeout

    def create_person_state(self):
        """create_person_state 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        now = time.time()

        return {
            "first_seen": now,
            "last_seen": now,
            "bbox": None,
            "is_full_body": False,
            "crop_saved": False,
            "crop_path": None,
            "is_recording": False,
            "clip_path": None,
            "vlm_done": False,
            "vlm_result": None,
        }

    def update_person(self, person_id, bbox, is_full_body):

        """update_person 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        now = time.time()

        if person_id not in self.person_states:
            self.person_states[person_id] = self.create_person_state()

        state = self.person_states[person_id]

        state["last_seen"] = now
        state["bbox"] = bbox
        state["is_full_body"] = is_full_body

        return state

    def mark_crop_saved(self, person_id, crop_path):

        """mark_crop_saved 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if person_id not in self.person_states:
            self.person_states[person_id] = self.create_person_state()

        self.person_states[person_id]["crop_saved"] = True
        self.person_states[person_id]["crop_path"] = crop_path

    def mark_recording_started(self, person_id, clip_path=None):

        """mark_recording_started 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if person_id not in self.person_states:
            self.person_states[person_id] = self.create_person_state()

        self.person_states[person_id]["is_recording"] = True
        self.person_states[person_id]["clip_path"] = clip_path

    def mark_recording_stopped(self, person_id):

        """mark_recording_stopped 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if person_id in self.person_states:
            self.person_states[person_id]["is_recording"] = False

    def mark_vlm_done(self, person_id, vlm_result):
        """
        VLM 분석 완료 상태 기록
        """

        if person_id not in self.person_states:
            self.person_states[person_id] = self.create_person_state()

        self.person_states[person_id]["vlm_done"] = True
        self.person_states[person_id]["vlm_result"] = vlm_result

    def get_state(self, person_id):
        """get_state 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        return self.person_states.get(person_id)

    def has_crop_saved(self, person_id):
        """has_crop_saved 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        state = self.get_state(person_id)
        return state is not None and state["crop_saved"]

    def is_recording(self, person_id):
        """is_recording 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        state = self.get_state(person_id)
        return state is not None and state["is_recording"]

    def is_vlm_done(self, person_id):
        """is_vlm_done 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        state = self.get_state(person_id)
        return state is not None and state["vlm_done"]

    def remove_disappeared_persons(self):
        """remove_disappeared_persons 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        now = time.time()
        removed_ids = []

        for person_id, state in list(self.person_states.items()):
            if now - state["last_seen"] > self.disappear_timeout:
                removed_ids.append(person_id)
                del self.person_states[person_id]

        return removed_ids
