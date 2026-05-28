# AI CCTV Source Structure

AI CCTV 소스 코드의 파일별 클래스와 함수를 정리한 문서입니다.
정상값과 에러값은 코드의 일반 반환 흐름과 예외 처리 방식을 기준으로 요약했습니다.

## `src/ai_cctv/alerts/dispatcher.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `AlertChannel` | 알림 채널 구현체의 공통 인터페이스입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `send` | 알림 메시지를 채널로 전송합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `DiscordChatBotChannel` | 기존 Discord 챗봇 모듈을 알림 채널로 감쌉니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | Discord 챗봇 채널을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `send` | Discord 챗봇으로 알림 메시지를 전송합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `AlertDispatcher` | 알림 메시지를 등록된 채널로 전달합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 알림 채널 목록을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `add_channel` | 알림 채널을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `dispatch_anomaly` | 이상 상황 이벤트를 알림 메시지로 변환해 전송합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `dispatch` | 알림 메시지를 전체 채널로 전송합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/alerts/message.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `AlertMessage` | 사용자 알림 메시지를 표현합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `from_anomaly_event` | 이상 상황 이벤트에서 알림 메시지를 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `to_text` | 채팅 채널로 보낼 텍스트 메시지를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/anomaly/detector.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `AnomalyRule` | 이상 상황 판단 규칙의 공통 인터페이스입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `evaluate` | 감지 결과를 평가하여 이상 상황 이벤트를 반환합니다. | 결과 목록 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `ObjectPresenceRule` | 특정 객체가 새로 감지되면 이상 상황으로 판단합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 객체 등장 규칙을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `evaluate` | 새로운 객체 추적 ID를 이상 상황 이벤트로 변환합니다. | 결과 목록 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_build_object_key` | 감지 객체를 중복 판단하기 위한 식별자를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `DwellTimeRule` | 객체가 일정 시간 이상 감지되면 이상 상황으로 판단합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 체류 시간 판단 규칙을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `evaluate` | 객체별 체류 시간을 계산하여 이상 상황 이벤트를 생성합니다. | 결과 목록 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_forget_missing_objects` | 현재 프레임에서 사라진 객체의 체류 상태를 정리합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `AnomalyDetector` | 여러 이상 상황 판단 규칙을 실행하는 조정자입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 이상 상황 판단 규칙 목록을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `evaluate` | 감지 결과를 전체 규칙으로 평가합니다. | 결과 목록 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/anomaly/events.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `AnomalyEvent` | 이상 상황 이벤트 정보를 표현합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `to_worker_event` | PyQt VideoWorker 신호로 전달할 이벤트 딕셔너리를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/chat_bot/chat_bot.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `send_msg` | VLM 분석 결과를 Discord 알림 큐에 등록합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `stop` | 알림 worker thread를 종료합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_ensure_worker_started` | 알림 worker thread를 lazy-start 방식으로 시작합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_worker_loop` | 큐에서 메시지를 하나씩 꺼내 Discord 전송 함수로 넘깁니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_normalize_message` | VLM 결과를 Discord에 보낼 수 있는 문자열로 변환합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/chat_bot/discord_bot.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `_read_proj_env_value` | 루트의 .proj_env 파일에서 지정한 값을 읽습니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `DiscordBotSender` | Discord 봇 로그인과 메시지 전송을 담당하는 클래스입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | Discord 전송 객체를 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `start` | Discord client를 시작하고 준비 완료까지 기다립니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `send_message` | Discord 채널로 메시지를 전송합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_send_message_async` | Discord event loop 안에서 실제 메시지를 전송합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `close` | Discord client와 event loop thread를 종료합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_run_event_loop` | 별도 thread에서 Discord client용 asyncio event loop를 실행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `send_message` | 기본 Discord sender를 사용해 메시지를 보냅니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `close` | 기본 Discord sender를 종료합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_split_message` | Discord 전송용으로 긴 문자열을 여러 조각으로 나눕니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/crop_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `CropManager` | CropManager 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `crop_person` | crop_person 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `save_crop` | save_crop 함수의 주요 기능을 수행합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `save_crop_once` | save_crop_once 함수의 주요 기능을 수행합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/example_face_identifier.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `main` | main 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/face_identifier.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `FaceIdentifier` | FaceIdentifier 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `identify_from_path` | identify_from_path 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `identify_from_crop` | identify_from_crop 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_load_known_faces` | _load_known_faces 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_recognize_face` | _recognize_face 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_crop_face_region` | _crop_face_region 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_save_face_crop` | _save_face_crop 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_get_largest_face` | _get_largest_face 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_ensure_bgr_image` | _ensure_bgr_image 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_normalize_embedding` | _normalize_embedding 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_cosine_similarity` | _cosine_similarity 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_no_face_result` | _no_face_result 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 상태 딕셔너리 | 내부 보조 함수 |
| `_no_registered_faces_result` | _no_registered_faces_result 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 상태 딕셔너리 | 내부 보조 함수 |
| `_error_result` | _error_result 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 오류 결과 딕셔너리 | 내부 보조 함수 |

## `src/ai_cctv/client/face_recognition.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `get_yolo_model` | YOLO 모델을 지연 로딩하여 반환합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_face_app` | InsightFace 분석 객체를 지연 로딩하여 반환합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `normalize_embedding` | 얼굴 임베딩 벡터를 정규화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `cosine_similarity` | 두 정규화 임베딩 사이의 코사인 유사도를 계산합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_largest_face` | 검출된 얼굴 목록에서 가장 큰 얼굴을 선택합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `expand_box` | 바운딩 박스를 지정 비율만큼 확장하고 이미지 경계 안으로 보정합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `load_known_faces` | 등록 얼굴 폴더에서 인물별 얼굴 임베딩 DB를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `recognize_face` | 얼굴 crop 이미지를 등록 얼굴 DB와 비교합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `detect_face_with_tasks` | MediaPipe FaceDetector로 ROI 안의 가장 큰 얼굴 박스를 찾습니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `run_demo` | YOLO와 얼굴 인식을 함께 실행하는 데모 루프를 시작합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_draw_detection_result` | 데모 프레임에 객체 및 얼굴 인식 결과를 그립니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_build_person_face_label` | 사람 객체의 얼굴 인식 라벨과 표시 색상을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `main` | 얼굴 인식 데모 실행 진입점입니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/full_body_checker.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `FullBodyChecker` | FullBodyChecker 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | min_body_height_ratio: | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `is_full_body_visible` | bbox: | True 또는 False | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_status_text` | 화면 표시용 상태 텍스트 | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/legacy_cctv_gui.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `CCTVMainWindow` | CCTVMainWindow 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `update_frame` | update_frame 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `closeEvent` | closeEvent 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/person_state_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonStateManager` | PersonStateManager 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `create_person_state` | create_person_state 함수의 주요 기능을 수행합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `update_person` | update_person 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `mark_crop_saved` | mark_crop_saved 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `mark_recording_started` | mark_recording_started 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `mark_recording_stopped` | mark_recording_stopped 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `mark_vlm_done` | VLM 분석 완료 상태 기록 | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_state` | get_state 함수의 주요 기능을 수행합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `has_crop_saved` | has_crop_saved 함수의 주요 기능을 수행합니다. | True 또는 False | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `is_recording` | is_recording 함수의 주요 기능을 수행합니다. | True 또는 False | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `is_vlm_done` | is_vlm_done 함수의 주요 기능을 수행합니다. | True 또는 False | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `remove_disappeared_persons` | remove_disappeared_persons 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/person_tracker.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonTracker` | YOLO와 ByteTrack으로 대상 객체를 추적합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 객체 추적 모델과 대상 클래스 설정을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `track` | 프레임에서 대상 객체를 탐지하고 추적합니다. | 결과 목록 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/pipeline/person_frame_processor.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonFrameProcessor` | 추적된 인물 하나에 대한 프레임 처리 책임을 담당합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 인물 처리에 필요한 협력 객체를 주입합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `process` | 추적 인물 상태를 갱신하고 필요한 화면 주석을 그립니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_should_queue_vlm` | VLM 분석 큐 등록 가능 여부를 판단합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_queue_vlm` | 전신 crop을 저장하고 VLM 작업 큐에 등록합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_draw_annotation` | 프레임 위에 추적 박스와 라벨을 그립니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_build_event` | 인물 이벤트 딕셔너리를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/recording_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `RecordingManager` | 원본 영상 프레임을 시간 단위 MP4 파일로 저장합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 녹화 저장 상태와 기본 경로를 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `start_recording` | 새 MP4 녹화 파일을 시작합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `write_frame` | 프레임을 현재 녹화 파일에 기록합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `stop_recording` | 현재 녹화 파일을 닫고 최종 파일명으로 변경합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/settings_window.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `SettingsWindow` | AI CCTV 실행 설정을 입력받는 PyQt 대화상자입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 설정 창의 초기 상태를 구성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `init_ui` | 설정 창의 좌측 메뉴와 우측 페이지 영역을 구성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_create_menu_panel` | 설정 페이지 전환 메뉴 패널을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `create_menu_button` | 설정 메뉴 버튼을 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `create_basic_page` | 영상 입력과 VLM 사용 여부 설정 페이지를 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_add_input_controls` | 기본 설정 페이지에 영상 입력 컨트롤을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_add_vlm_controls` | 기본 설정 페이지에 VLM 사용 여부 컨트롤을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_label` | 설정 폼 라벨을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_line_edit` | 표준 스타일의 입력 필드를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_basic_save_row` | 기본 설정 저장 버튼 행을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `update_input_mode` | 선택된 입력 방식에 맞춰 입력 필드를 활성화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `save_basic_settings` | 기본 설정 값을 검증하고 대화상자 상태에 반영합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_parse_camera_index` | 웹캠 번호 입력값을 정수로 변환합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_show_basic_error` | 기본 설정 페이지에 오류 메시지를 표시합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `create_empty_page` | 빈 안내 페이지를 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `create_storage_page` | 저장 경로와 원본 녹화 분할 설정 페이지를 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_add_storage_path_controls` | 저장 경로 선택 컨트롤을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_add_original_segment_controls` | 원본 녹화 분할 시간 라디오 버튼을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_storage_save_row` | 저장 설정 적용 버튼 행을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `select_storage_path` | 사용자에게 저장 루트 경로를 선택받고 표준 폴더를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `save_storage_settings` | 저장소 설정 값을 검증하고 대화상자를 완료합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/storage/path_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `StoragePaths` | 저장소 경로 묶음을 표현합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `StoragePathManager` | AI CCTV 저장 폴더 구조를 생성합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 저장 경로 규칙을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `build_paths` | 루트 경로 기준의 표준 저장 경로를 계산합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `ensure_paths` | 표준 저장 폴더를 만들고 경로 묶음을 반환합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/ui/event_presenter.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EventDisplay` | 이벤트 표시 정보를 담는 값 객체입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `EventPresenter` | 이벤트 딕셔너리를 UI 표시 정보로 변환합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `build_display` | 이벤트 유형별 설명과 색상을 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_time_text` | 이벤트 시간 문자열을 가져오거나 현재 시각으로 대체합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/ui/main_window.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `CCTVMainWindow` | AI CCTV 클라이언트의 메인 제어 창입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 메인 창 상태와 UI를 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `init_ui` | 메인 화면의 전체 레이아웃을 구성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_create_header_layout` | 상단 제목과 제어 버튼 레이아웃을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_button` | 표준 스타일의 버튼을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_left_panel` | 카메라 입력 상태 패널을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_center_panel` | 실시간 영상과 지표 패널을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_right_panel` | 이벤트 타임라인과 저장 경로 패널을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `create_metric_box` | 지표 숫자와 라벨을 담는 UI 박스를 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `start_video` | 영상 처리 작업자를 시작하고 신호를 연결합니다. | 성공 시 상태 반영 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `stop_video` | 영상 처리 작업자를 중지하고 카메라 상태를 갱신합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `open_settings` | 설정 창을 열고 적용된 값을 메인 창 상태에 반영합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `update_frame` | OpenCV 프레임을 PyQt 이미지로 변환해 화면에 표시합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `update_metrics` | 영상 처리 지표를 화면에 반영합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `add_event` | 이벤트 타임라인에 새 이벤트 항목을 추가합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `closeEvent` | 창 닫힘 이벤트에서 작업자를 정리합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_set_camera_status_style` | 카메라 상태 라벨의 색상을 설정합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_build_storage_label` | 저장 경로 패널에 표시할 문자열을 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_trim_event_list` | 이벤트 타임라인의 최대 표시 개수를 제한합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `main` | AI CCTV PyQt 애플리케이션을 실행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/video_stream.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `VideoStream` | VideoStream 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `open` | open 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `read` | read 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_fps` | get_fps 함수의 주요 기능을 수행합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `get_frame_size` | get_frame_size 함수의 주요 기능을 수행합니다. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `release` | release 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/client/video_worker.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `VideoWorker` | 영상 캡처, 추적, 녹화, 선택적 VLM 분석을 조정합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 영상 처리 스레드와 협력 객체를 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `run` | 스레드 메인 루프에서 프레임 처리와 신호 발행을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `stop` | 영상 처리 루프를 중지하고 스레드 종료를 기다립니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_cleanup` | 사용 중인 분석 작업자, 녹화기, 영상 스트림을 정리합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_create_default_alert_dispatcher` | 기본 Discord 이상 상황 알림 디스패처를 생성합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/vlm_person_analyzer.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonAnalyzer` | 운영 코드에서 사용할 인물 이미지 VLM 분석기입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |

## `src/ai_cctv/client/vlm_person_analyzer_qwen.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonAnalyzer` | PersonAnalyzer 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_build_messages` | _build_messages 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `analyze` | analyze 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_clean_result` | _clean_result 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/vlm_person_analyzer_qwen_test.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PersonAnalyzer` | PersonAnalyzer 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_build_messages` | _build_messages 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `analyze` | analyze 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_clean_result` | _clean_result 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/client/vlm_worker.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `VLMWorker` | VLMWorker 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `start` | start 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `add_task` | add_task 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_run` | _run 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `stop` | stop 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `cleanup` | cleanup 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/edge_pi/failover.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `FailoverAction` | 네트워크 상태에 따른 엣지 장치 동작을 표현합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `NetworkFailoverPolicy` | Raspberry Pi 네트워크 장애 대응 동작을 결정합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 장애 대응 정책을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `decide` | 네트워크 상태에 맞는 엣지 장치 동작을 결정합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/edge_pi/main.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `build_default_streaming_command` | 기본 Raspberry Pi 송출 명령을 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `main` | Raspberry Pi 실행용 송출 명령을 출력합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/edge_pi/streaming.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PiStreamingConfig` | Raspberry Pi GStreamer 영상 송출 설정을 표현합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `GStreamerMediaMtxCommandBuilder` | GStreamer 기반 MediaMTX 송출 명령을 생성합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | 송출 명령 생성 설정을 초기화합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `build_command` | GStreamer 송출 명령 인자 목록을 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `build_shell_text` | 문서와 운영 스크립트에 표시할 송출 명령 문자열을 생성합니다. | 생성된 객체 또는 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `RpicamMediaMtxCommandBuilder` | 기존 import 호환을 위한 GStreamer 명령 생성기 별칭입니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |

## `src/ai_cctv/streaming/legacy_rtsp_receiver.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `check_server_port_open` | RTSP 서버의 TCP 포트(기본 8554)가 현재 물리적으로 열려 있는지 사전에 노크해 보는 함수. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `RTSPReceiver` | 라즈베리파이 RTSP 스트림을 백그라운드 스레드에서 수신하고, | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `start` | 수신기와 watchdog 백그라운드 스레드를 개시하는 함수. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `_watchdog_loop` | RTSP 연결은 성공했으나, 소켓 장애로 인해 내부적으로 프레임 공급이 5초 이상 중단되었을 때, | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `_receive_loop` | [영상 수신 및 재연결 내부 스레드] | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |
| `get_frame` | GUI 대시보드나 AI 추론 모델이 메인 루프에서 호출하는 외부용 함수. | 조회된 값 | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `stop` | 프로그램 종료 시 외부에서 안전하게 수집 전담 스레드와 감시 스레드를 정지시키는 해제 함수. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `main` | main 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/streaming/receiver.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `receive_rtsp` | RTSP 스트림을 수신하여 OpenCV 창에 표시합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
| `main` | RTSP 수신 데모를 실행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |

## `src/ai_cctv/streaming/sender.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `CameraRTSPServer` | CameraRTSPServer 클래스의 주요 책임을 수행합니다. | 인스턴스 생성 | 초기화 실패 시 예외 | 객체 지향 책임 단위 |
| `__init__` | __init__ 함수의 주요 기능을 수행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 내부 보조 함수 |

## `src/ai_cctv/windows_server/main.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `main` | Windows 서버 GUI 분석 애플리케이션을 실행합니다. | 처리 결과 또는 None | 실패 시 None, False, 예외 또는 오류 이벤트 | 공개 호출 함수 |
