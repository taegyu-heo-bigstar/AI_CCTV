# YOLO 기반 객체 추적기를 정의하는 파일입니다.
# 사람뿐 아니라 문서 기준의 차량, 특정 객체 등으로 대상 클래스를 확장할 수 있습니다.
# VideoWorker는 이 객체를 통해 프레임별 추적 결과를 획득합니다.
# YOLO 라이브러리는 실제 추적기 생성 시점에 지연 import합니다.


class PersonTracker:
    """YOLO와 ByteTrack으로 대상 객체를 추적합니다.

    인자:
        model_path: YOLO 모델 파일 경로입니다.
        target_class: 단일 추적 대상 클래스명입니다.
        target_classes: 복수 추적 대상 클래스명 목록입니다.
        conf_threshold: 추적 결과로 인정할 최소 신뢰도입니다.
        tracker_config: Ultralytics tracker 설정 파일명입니다.
    반환값:
        PersonTracker 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        model_path="yolo26s.pt",
        target_class="person",
        target_classes=None,
        conf_threshold=0.7,
        tracker_config="bytetrack.yaml",
    ):
        """객체 추적 모델과 대상 클래스 설정을 초기화합니다.

        인자:
            model_path: YOLO 모델 파일 경로입니다.
            target_class: 단일 추적 대상 클래스명입니다.
            target_classes: 복수 추적 대상 클래스명 목록입니다.
            conf_threshold: 추적 결과로 인정할 최소 신뢰도입니다.
            tracker_config: Ultralytics tracker 설정 파일명입니다.
        반환값:
            없음.
        """

        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.target_classes = set(target_classes or [target_class])
        self.conf_threshold = conf_threshold
        self.tracker_config = tracker_config

    def track(self, frame):
        """프레임에서 대상 객체를 탐지하고 추적합니다.

        인자:
            frame: OpenCV BGR 프레임입니다.
        반환값:
            추적 객체 정보 딕셔너리 목록을 반환합니다.
        """

        results = self.model.track(
            frame,
            persist=True,
            tracker=self.tracker_config,
            verbose=False,
        )
        tracked_objects = []

        if results is None or len(results) == 0:
            return tracked_objects

        result = results[0]
        if result.boxes is None:
            return tracked_objects

        for box in result.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = self.model.names[cls_id]

            if class_name not in self.target_classes:
                continue
            if conf < self.conf_threshold:
                continue
            if box.id is None:
                continue

            track_id = int(box.id[0])
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            tracked_objects.append({
                "person_id": track_id,
                "track_id": track_id,
                "bbox": (x1, y1, x2, y2),
                "conf": conf,
                "class_name": class_name,
            })

        return tracked_objects
