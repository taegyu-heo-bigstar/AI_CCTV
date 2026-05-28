# crop_manager.py 파일입니다.
# AI CCTV 프로젝트의 control_center 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

# crop_manager.py ?????.
# AI CCTV ????? client ???? ???? ?? ?????.
# ? ??? ???? ?? ??? ? ?? docstring? ???? ????.

# crop_manager.py

import os
import cv2


class CropManager:
    """CropManager 클래스의 주요 책임을 수행합니다.
    
    인자:
        생성자 인자는 __init__ 문서를 따릅니다.
    반환값:
        CropManager 인스턴스를 반환합니다.
    """
    def __init__(self, save_dir="outputs/crops", padding=20):
        """__init__ 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.save_dir = save_dir
        self.padding = padding

        os.makedirs(self.save_dir, exist_ok=True)

    def crop_person(self, frame, bbox):
        """crop_person 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        x1, y1, x2, y2 = bbox
        frame_height, frame_width = frame.shape[:2]

        # padding 적용 + 프레임 밖으로 나가지 않게 보정
        x1 = max(0, x1 - self.padding)
        y1 = max(0, y1 - self.padding)
        x2 = min(frame_width, x2 + self.padding)
        y2 = min(frame_height, y2 + self.padding)

        crop = frame[y1:y2, x1:x2]

        if crop.size == 0:
            return None

        return crop

    def save_crop(self, frame, bbox, person_id):
        """save_crop 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        crop = self.crop_person(frame, bbox)

        if crop is None:
            return None

        filename = f"person_{person_id}.jpg"
        save_path = os.path.join(self.save_dir, filename)

        cv2.imwrite(save_path, crop)

        return save_path

    def save_crop_once(self, frame, bbox, person_id, saved_person_ids):
        # saved_person_ids = 이미 crop 저장한 person_id를 담는 set

        """save_crop_once 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        if person_id in saved_person_ids:
            return None

        save_path = self.save_crop(frame, bbox, person_id)

        if save_path is not None:
            saved_person_ids.add(person_id)

        return save_path
