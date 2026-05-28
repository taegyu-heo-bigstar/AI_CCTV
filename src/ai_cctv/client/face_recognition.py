# 얼굴 인식 데모와 보조 함수를 제공하는 파일입니다.
# import 시 카메라나 모델이 실행되지 않도록 지연 초기화 구조를 사용합니다.
# 운영 코드에서는 FaceIdentifier 사용을 우선하고 이 파일은 실험 진입점으로 유지합니다.

from pathlib import Path

import cv2
import mediapipe as mp
import numpy as np
from insightface.app import FaceAnalysis
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from ultralytics import YOLO


RTSP_URL = "rtsp://192.168.10.2:8554/stream"
VIDEO_SOURCE = 0
YOLO_MODEL_PATH = "yolo26s.pt"
FACE_TASK_MODEL_PATH = "blaze_face_short_range.tflite"
KNOWN_FACE_DIR = "known_faces"
TARGET_CLASSES = ["person", "apple"]
YOLO_CONF_TH = 0.5
FACE_SIM_THRESHOLD = 0.20

_yolo_model = None
_face_app = None


def get_yolo_model(model_path=YOLO_MODEL_PATH):
    """YOLO 모델을 지연 로딩하여 반환합니다.

    인자:
        model_path: 로딩할 YOLO 모델 파일 경로입니다.
    반환값:
        ultralytics YOLO 모델 객체를 반환합니다.
    """

    global _yolo_model
    if _yolo_model is None:
        _yolo_model = YOLO(model_path)
    return _yolo_model


def get_face_app():
    """InsightFace 분석 객체를 지연 로딩하여 반환합니다.

    인자:
        없음.
    반환값:
        준비된 FaceAnalysis 객체를 반환합니다.
    """

    global _face_app
    if _face_app is None:
        _face_app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _face_app.prepare(ctx_id=-1, det_size=(640, 640))
    return _face_app


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """얼굴 임베딩 벡터를 정규화합니다.

    인자:
        embedding: 원본 얼굴 임베딩 벡터입니다.
    반환값:
        L2 정규화된 numpy 배열을 반환합니다.
    """

    embedding_array = embedding.astype(np.float32)
    norm = np.linalg.norm(embedding_array) + 1e-8
    return embedding_array / norm


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """두 정규화 임베딩 사이의 코사인 유사도를 계산합니다.

    인자:
        a: 첫 번째 정규화 임베딩입니다.
        b: 두 번째 정규화 임베딩입니다.
    반환값:
        코사인 유사도 실수값을 반환합니다.
    """

    return float(np.dot(a, b))


def get_largest_face(faces):
    """검출된 얼굴 목록에서 가장 큰 얼굴을 선택합니다.

    인자:
        faces: InsightFace가 반환한 얼굴 객체 목록입니다.
    반환값:
        가장 큰 얼굴 객체 또는 None을 반환합니다.
    """

    if not faces:
        return None
    return max(
        faces,
        key=lambda face: (
            (face.bbox[2] - face.bbox[0])
            * (face.bbox[3] - face.bbox[1])
        ),
    )


def expand_box(x1, y1, x2, y2, img_w, img_h, scale=0.4):
    """바운딩 박스를 지정 비율만큼 확장하고 이미지 경계 안으로 보정합니다.

    인자:
        x1: 원본 박스 왼쪽 좌표입니다.
        y1: 원본 박스 위쪽 좌표입니다.
        x2: 원본 박스 오른쪽 좌표입니다.
        y2: 원본 박스 아래쪽 좌표입니다.
        img_w: 이미지 너비입니다.
        img_h: 이미지 높이입니다.
        scale: 확장 비율입니다.
    반환값:
        보정된 (x1, y1, x2, y2) 튜플을 반환합니다.
    """

    width = x2 - x1
    height = y2 - y1
    dx = int(width * scale)
    dy = int(height * scale)
    return (
        max(0, x1 - dx),
        max(0, y1 - dy),
        min(img_w, x2 + dx),
        min(img_h, y2 + dy),
    )


def load_known_faces(face_dir: str):
    """등록 얼굴 폴더에서 인물별 얼굴 임베딩 DB를 생성합니다.

    인자:
        face_dir: 인물별 얼굴 이미지가 저장된 폴더 경로입니다.
    반환값:
        인물 이름을 키로 하고 임베딩 목록을 값으로 갖는 딕셔너리를 반환합니다.
    """

    face_db = {}
    base = Path(face_dir)
    face_app = get_face_app()

    if not base.exists():
        print(f"[경고] 등록 얼굴 폴더가 없습니다: {face_dir}")
        return face_db

    for person_dir in base.iterdir():
        if not person_dir.is_dir():
            continue

        person_name = person_dir.name
        embeddings = []
        for image_path in person_dir.iterdir():
            if image_path.suffix.lower() not in [".jpg", ".jpeg", ".png", ".bmp"]:
                continue

            image = cv2.imread(str(image_path))
            if image is None:
                continue

            face = get_largest_face(face_app.get(image))
            if face is None:
                print(f"[등록 실패] {person_name}: 얼굴 검출 안됨 - {image_path.name}")
                continue

            embeddings.append(normalize_embedding(face.embedding))

        if embeddings:
            face_db[person_name] = embeddings
            print(f"[등록 완료] {person_name}: {len(embeddings)}장")
        else:
            print(f"[등록 실패] {person_name}: 사용 가능한 얼굴 이미지 없음")

    return face_db


def recognize_face(face_crop: np.ndarray, face_db: dict, threshold=FACE_SIM_THRESHOLD):
    """얼굴 crop 이미지를 등록 얼굴 DB와 비교합니다.

    인자:
        face_crop: 얼굴 영역 BGR 이미지입니다.
        face_db: 등록 얼굴 임베딩 DB입니다.
        threshold: 동일 인물로 인정할 최소 유사도입니다.
    반환값:
        (인물 이름, 유사도) 튜플을 반환합니다.
    """

    face = get_largest_face(get_face_app().get(face_crop))
    if face is None:
        return "Unknown", -1.0

    embedding = normalize_embedding(face.embedding)
    best_name = "Unknown"
    best_score = -1.0

    for person_name, embeddings in face_db.items():
        score = max(cosine_similarity(embedding, ref) for ref in embeddings)
        if score > best_score:
            best_score = score
            best_name = person_name

    if best_score < threshold:
        return "Unknown", best_score
    return best_name, best_score


def detect_face_with_tasks(face_detector, bgr_roi: np.ndarray):
    """MediaPipe FaceDetector로 ROI 안의 가장 큰 얼굴 박스를 찾습니다.

    인자:
        face_detector: MediaPipe FaceDetector 객체입니다.
        bgr_roi: 얼굴을 찾을 BGR ROI 이미지입니다.
    반환값:
        얼굴 박스 (x1, y1, x2, y2) 또는 None을 반환합니다.
    """

    if bgr_roi is None or bgr_roi.size == 0:
        return None

    rgb_roi = cv2.cvtColor(bgr_roi, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_roi)
    result = face_detector.detect(mp_image)

    if not result.detections:
        return None

    height, width, _ = bgr_roi.shape
    best_box = None
    best_area = -1

    for detection in result.detections:
        bbox = detection.bounding_box
        x1 = max(0, int(bbox.origin_x))
        y1 = max(0, int(bbox.origin_y))
        x2 = min(width, int(bbox.origin_x + bbox.width))
        y2 = min(height, int(bbox.origin_y + bbox.height))

        area = max(0, x2 - x1) * max(0, y2 - y1)
        if area > best_area:
            best_area = area
            best_box = (x1, y1, x2, y2)

    return best_box


def run_demo(video_source=VIDEO_SOURCE):
    """YOLO와 얼굴 인식을 함께 실행하는 데모 루프를 시작합니다.

    인자:
        video_source: OpenCV VideoCapture 입력 소스입니다.
    반환값:
        없음.
    """

    yolo_model = get_yolo_model()
    face_db = load_known_faces(KNOWN_FACE_DIR)
    if not face_db:
        print("[경고] 등록 얼굴 DB가 비어 있습니다. Unknown만 표시될 수 있습니다.")

    base_options = python.BaseOptions(model_asset_path=FACE_TASK_MODEL_PATH)
    options = vision.FaceDetectorOptions(
        base_options=base_options,
        running_mode=vision.RunningMode.IMAGE,
        min_detection_confidence=0.5,
        min_suppression_threshold=0.3,
    )

    cap = cv2.VideoCapture(video_source)
    if not cap.isOpened():
        print("영상 연결 실패")
        return

    print("영상 연결 성공")
    with vision.FaceDetector.create_from_options(options) as face_detector:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("프레임 수신 실패")
                continue

            _draw_detection_result(frame, yolo_model, face_detector, face_db)
            cv2.imshow("YOLO + MediaPipe Tasks(IMAGE) + InsightFace", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    cap.release()
    cv2.destroyAllWindows()


def _draw_detection_result(frame, yolo_model, face_detector, face_db):
    """데모 프레임에 객체 및 얼굴 인식 결과를 그립니다.

    인자:
        frame: OpenCV BGR 프레임입니다.
        yolo_model: YOLO 객체 감지 모델입니다.
        face_detector: MediaPipe FaceDetector 객체입니다.
        face_db: 등록 얼굴 임베딩 DB입니다.
    반환값:
        없음.
    """

    result = yolo_model(frame, verbose=False)[0]
    for box in result.boxes:
        cls_id = int(box.cls[0])
        conf = float(box.conf[0])
        class_name = yolo_model.names[cls_id]

        if class_name not in TARGET_CLASSES or conf < YOLO_CONF_TH:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame.shape[1], x2)
        y2 = min(frame.shape[0], y2)

        label = f"{class_name} {conf:.2f}"
        box_color = (0, 255, 0)
        if class_name == "person":
            label, box_color = _build_person_face_label(
                frame,
                (x1, y1, x2, y2),
                conf,
                face_detector,
                face_db,
            )

        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
        cv2.putText(
            frame,
            label,
            (x1, max(20, y1 - 10)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            box_color,
            2,
        )


def _build_person_face_label(frame, bbox, conf, face_detector, face_db):
    """사람 객체의 얼굴 인식 라벨과 표시 색상을 생성합니다.

    인자:
        frame: OpenCV BGR 프레임입니다.
        bbox: 사람 객체 바운딩 박스입니다.
        conf: 사람 객체 감지 신뢰도입니다.
        face_detector: MediaPipe FaceDetector 객체입니다.
        face_db: 등록 얼굴 임베딩 DB입니다.
    반환값:
        (라벨 문자열, 색상 튜플)을 반환합니다.
    """

    x1, y1, x2, y2 = bbox
    person_roi = frame[y1:y2, x1:x2]
    face_box = detect_face_with_tasks(face_detector, person_roi)

    if face_box is None:
        return f"person {conf:.2f} / face not found", (0, 255, 0)

    fx1, fy1, fx2, fy2 = face_box
    fx1_global = x1 + fx1
    fy1_global = y1 + fy1
    fx2_global = x1 + fx2
    fy2_global = y1 + fy2
    ex1, ey1, ex2, ey2 = expand_box(
        fx1_global,
        fy1_global,
        fx2_global,
        fy2_global,
        frame.shape[1],
        frame.shape[0],
        scale=0.4,
    )

    face_crop = frame[ey1:ey2, ex1:ex2]
    if face_crop.size <= 0:
        return f"person {conf:.2f} / face crop fail", (0, 255, 0)

    person_name, similarity = recognize_face(face_crop, face_db)
    if person_name != "Unknown":
        return f"{person_name} / person {conf:.2f} / sim {similarity:.2f}", (255, 0, 0)
    return f"Unknown / person {conf:.2f} / sim {similarity:.2f}", (0, 165, 255)


def main():
    """얼굴 인식 데모 실행 진입점입니다.

    인자:
        없음.
    반환값:
        없음.
    """

    run_demo()


if __name__ == "__main__":
    main()
