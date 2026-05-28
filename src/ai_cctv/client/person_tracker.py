# person_tracker.py 파일입니다.
# AI CCTV 프로젝트의 client 영역에서 사용하는 소스 코드입니다.
# 이 파일의 클래스와 함수 책임은 각 국문 docstring에 정리되어 있습니다.

# person_tracker.py ?????.
# AI CCTV ????? client ???? ???? ?? ?????.
# ? ??? ???? ?? ??? ? ?? docstring? ???? ????.

# person_tracker.py

from ultralytics import YOLO


class PersonTracker:
    """PersonTracker 클래스의 주요 책임을 수행합니다.
    
    인자:
        생성자 인자는 __init__ 문서를 따릅니다.
    반환값:
        PersonTracker 인스턴스를 반환합니다.
    """
    def __init__(
        self,
        model_path="yolo26s.pt",
        target_class="person",
        conf_threshold=0.5,
        tracker_config="bytetrack.yaml",
    ):
        """__init__ 함수의 주요 기능을 수행합니다.
        
        인자:
            함수 시그니처에 정의된 값을 사용합니다.
        반환값:
            처리 결과 또는 None을 반환합니다.
        """
        self.model = YOLO(model_path)
        self.target_class = target_class
        self.conf_threshold = conf_threshold
        self.tracker_config = tracker_config

    def track(self, frame):
        """
        YOLO 추론 + 객체 추적 수행

        return:
        [
            {
                "person_id": 1,
                "bbox": (x1, y1, x2, y2),
                "conf": 0.87,
                "class_name": "person"
            }
        ]
        """

        results = self.model.track(
            frame,
            persist=True,
            tracker=self.tracker_config,
            verbose=False
        )

        tracked_persons = []

        if results is None or len(results) == 0:
            return tracked_persons

        result = results[0]

        if result.boxes is None:
            return tracked_persons

        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = self.model.names[cls_id]

            if class_name != self.target_class:
                continue

            if conf < self.conf_threshold:
                continue

            # track_id가 없는 경우 방어 처리
            if box.id is None:
                continue

            person_id = int(box.id[0])

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            tracked_persons.append({
                "person_id": person_id,
                "bbox": (x1, y1, x2, y2),
                "conf": conf,
                "class_name": class_name
            })

        return tracked_persons
