# AI CCTV Structure

? ??? ?? ?? ??? ??? ???? ??? AST ???? ??? ????.

## `src/ai_cctv/ai_server/alerts/chat_bot/chat_bot.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `send_msg` | VLM 분석 결과를 Discord 알림 큐에 등록합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `stop` | 알림 worker thread를 종료합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `_ensure_worker_started` | 알림 worker thread를 lazy-start 방식으로 시작합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `_worker_loop` | 큐에서 메시지를 하나씩 꺼내 Discord 전송 함수로 넘깁니다. | None | ??? ?? ?? ?? | ?? ?? |
| `_normalize_message` | VLM 결과를 Discord에 보낼 수 있는 문자열로 변환합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `_send_to_discord` | Discord 전송 모듈을 지연 import하여 메시지를 전송합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `_close_discord_sender` | Discord 전송 모듈을 지연 import하여 연결을 정리합니다. | None | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/alerts/chat_bot/discord_bot.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `_read_proj_env_value` | 루트의 .proj_env 파일에서 지정한 값을 읽습니다. | '' | ??? ?? ?? ?? | ?? ?? |
| `DiscordBotSender` | Discord 봇 로그인과 메시지 전송을 담당하는 클래스입니다. | DiscordBotSender ???? | RuntimeError, TimeoutError | ?? ?? |
| `DiscordBotSender.__init__` | Discord 전송 객체를 초기화합니다. | None | RuntimeError | ?? ?? |
| `DiscordBotSender.start` | Discord client를 시작하고 준비 완료까지 기다립니다. | None | RuntimeError, TimeoutError | ?? ?? ?? |
| `DiscordBotSender.send_message` | Discord 채널로 메시지를 전송합니다. | None | RuntimeError | ?? ?? ?? |
| `DiscordBotSender._send_message_async` | Discord event loop 안에서 실제 메시지를 전송합니다. | None | RuntimeError | ?? ??, ??? ?? |
| `DiscordBotSender.close` | Discord client와 event loop thread를 종료합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `DiscordBotSender._run_event_loop` | 별도 thread에서 Discord client용 asyncio event loop를 실행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `send_message` | 기본 Discord sender를 사용해 메시지를 보냅니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `close` | 기본 Discord sender를 종료합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `_split_message` | Discord 전송용으로 긴 문자열을 여러 조각으로 나눕니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/alerts/dispatcher.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `NotificationChannel` | 알림 채널 구현체의 공통 인터페이스입니다. | NotificationChannel ???? | NotImplementedError | ?? ?? ?? |
| `NotificationChannel.send` | 알림 메시지를 채널로 전송합니다. | None | NotImplementedError | ?? ?? ?? |
| `DiscordNotificationChannel` | 기존 Discord 챗봇 모듈을 알림 채널로 감쌉니다. | DiscordNotificationChannel ???? | ??? ?? ?? ?? | ??: NotificationChannel, ?? ?? |
| `DiscordNotificationChannel.__init__` | Discord 알림 채널을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `DiscordNotificationChannel.send` | Discord 챗봇으로 알림 메시지를 전송합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `NotificationDispatcher` | 알림 메시지를 등록된 채널로 전달합니다. | NotificationDispatcher ???? | ??? ?? ?? ?? | ?? ?? |
| `NotificationDispatcher.__init__` | 알림 채널 목록을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `NotificationDispatcher.add_channel` | 알림 채널을 추가합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `NotificationDispatcher.dispatch_anomaly_event` | 이상 상황 이벤트를 알림 메시지로 변환해 전송합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `NotificationDispatcher.dispatch` | 알림 메시지를 전체 채널로 전송합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/alerts/message.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `NotificationMessage` | 사용자 알림 메시지를 표현합니다. | NotificationMessage ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `NotificationMessage.from_anomaly_event` | 이상 상황 이벤트에서 알림 메시지를 생성합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ??? ??? |
| `NotificationMessage.to_text` | 채팅 채널로 보낼 텍스트 메시지를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/anomaly/detector.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `AnomalyDetectionRule` | 이상 상황 판정 규칙의 공통 인터페이스입니다. | AnomalyDetectionRule ???? | NotImplementedError | ?? ?? ?? |
| `AnomalyDetectionRule.evaluate_detections` | 감지 결과를 평가하여 이상 상황 이벤트를 반환합니다. | None | NotImplementedError | ?? ?? ?? |
| `ObjectAppearanceRule` | 새로운 대상 객체가 등장하면 이상 상황으로 판단합니다. | ObjectAppearanceRule ???? | ??? ?? ?? ?? | ??: AnomalyDetectionRule, ?? ?? |
| `ObjectAppearanceRule.__init__` | 객체 등장 규칙을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `ObjectAppearanceRule.evaluate_detections` | 아직 보고하지 않은 추적 객체를 이상 상황 이벤트로 변환합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `ObjectAppearanceRule._build_object_key` | 객체 중복 보고를 막기 위한 식별자를 생성합니다. | tuple | ??? ?? ?? ?? | ?? ?? |
| `ObjectAppearanceRule._build_event` | 감지 결과 하나를 이상 상황 이벤트로 변환합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `DwellTimeAnomalyRule` | 객체가 일정 시간 이상 감지되면 이상 상황으로 판단합니다. | DwellTimeAnomalyRule ???? | ??? ?? ?? ?? | ??: AnomalyDetectionRule, ?? ?? |
| `DwellTimeAnomalyRule.__init__` | 체류 시간 판정 규칙을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `DwellTimeAnomalyRule.evaluate_detections` | 객체별 체류 시간을 계산하여 기준 초과 이벤트를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `DwellTimeAnomalyRule._resolve_object_key` | 체류 시간을 추적할 객체 식별자를 결정합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `DwellTimeAnomalyRule._build_event` | 체류 시간 초과 감지 결과를 이상 상황 이벤트로 변환합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `DwellTimeAnomalyRule._forget_missing_objects` | 현재 프레임에서 사라진 객체의 체류 상태를 정리합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `AnomalyRuleEngine` | 여러 이상 상황 판정 규칙을 순서대로 실행합니다. | AnomalyRuleEngine ???? | ??? ?? ?? ?? | ?? ?? |
| `AnomalyRuleEngine.__init__` | 이상 상황 판정 규칙 목록을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `AnomalyRuleEngine.evaluate_detections` | 감지 결과를 전체 규칙으로 평가합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/anomaly/events.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `AnomalyEvent` | 이상 상황 이벤트 정보를 표현합니다. | AnomalyEvent ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `AnomalyEvent.to_worker_event` | PyQt VideoWorker 신호로 전달할 이벤트 딕셔너리를 생성합니다. | dict | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/crop_manager.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `CropManager` | CropManager 클래스의 주요 책임을 수행합니다. | CropManager ???? | ??? ?? ?? ?? | ?? ?? |
| `CropManager.__init__` | __init__ 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `CropManager.crop_person` | crop_person 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `CropManager.save_crop` | save_crop 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `CropManager.save_crop_once` | save_crop_once 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/example_face_identifier.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `main` | main 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/face_identifier.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `FaceIdentifier` | FaceIdentifier 클래스의 주요 책임을 수행합니다. | FaceIdentifier ???? | RuntimeError, ValueError | ?? ?? |
| `FaceIdentifier.__init__` | __init__ 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier.identify_from_path` | identify_from_path 함수의 주요 기능을 수행합니다. | ?? ?? ?? ?? | ValueError | ?? ?? ?? |
| `FaceIdentifier.identify_from_crop` | identify_from_crop 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `FaceIdentifier._load_known_faces` | _load_known_faces 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._recognize_face` | _recognize_face 함수의 주요 기능을 수행합니다. | dict | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._crop_face_region` | _crop_face_region 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._save_face_crop` | _save_face_crop 함수의 주요 기능을 수행합니다. | ?? ?? | RuntimeError | ?? ?? |
| `FaceIdentifier._get_largest_face` | _get_largest_face 함수의 주요 기능을 수행합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._ensure_bgr_image` | _ensure_bgr_image 함수의 주요 기능을 수행합니다. | None | ValueError | ?? ?? |
| `FaceIdentifier._normalize_embedding` | _normalize_embedding 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._cosine_similarity` | _cosine_similarity 함수의 주요 기능을 수행합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._no_face_result` | _no_face_result 함수의 주요 기능을 수행합니다. | dict | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._no_registered_faces_result` | _no_registered_faces_result 함수의 주요 기능을 수행합니다. | dict | ??? ?? ?? ?? | ?? ?? |
| `FaceIdentifier._error_result` | _error_result 함수의 주요 기능을 수행합니다. | dict | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/analysis/face_recognition.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `get_yolo_model` | YOLO 모델을 지연 로딩하여 반환합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `get_face_app` | InsightFace 분석 객체를 지연 로딩하여 반환합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `normalize_embedding` | 얼굴 임베딩 벡터를 정규화합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `cosine_similarity` | 두 정규화 임베딩 사이의 코사인 유사도를 계산합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `get_largest_face` | 검출된 얼굴 목록에서 가장 큰 얼굴을 선택합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `expand_box` | 바운딩 박스를 지정 비율만큼 확장하고 이미지 경계 안으로 보정합니다. | tuple | ??? ?? ?? ?? | ?? ?? ?? |
| `load_known_faces` | 등록 얼굴 폴더에서 인물별 얼굴 임베딩 DB를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `recognize_face` | 얼굴 crop 이미지를 등록 얼굴 DB와 비교합니다. | tuple | ??? ?? ?? ?? | ?? ?? ?? |
| `detect_face_with_tasks` | MediaPipe FaceDetector로 ROI 안의 가장 큰 얼굴 박스를 찾습니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `run_demo` | YOLO와 얼굴 인식을 함께 실행하는 데모 루프를 시작합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `_draw_detection_result` | 데모 프레임에 객체 및 얼굴 인식 결과를 그립니다. | None | ??? ?? ?? ?? | ?? ?? |
| `_build_person_face_label` | 사람 객체의 얼굴 인식 라벨과 표시 색상을 생성합니다. | tuple | ??? ?? ?? ?? | ?? ?? |
| `main` | 얼굴 인식 데모 실행 진입점입니다. | None | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/full_body_checker.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `FullBodyChecker` | FullBodyChecker 클래스의 주요 책임을 수행합니다. | FullBodyChecker ???? | ??? ?? ?? ?? | ?? ?? |
| `FullBodyChecker.__init__` | min_body_height_ratio: | None | ??? ?? ?? ?? | ?? ?? |
| `FullBodyChecker.is_full_body_visible` | bbox: | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `FullBodyChecker.get_status_text` | 화면 표시용 상태 텍스트 | 'PARTIAL' | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/person_state_manager.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonStateManager` | PersonStateManager 클래스의 주요 책임을 수행합니다. | PersonStateManager ???? | ??? ?? ?? ?? | ?? ?? |
| `PersonStateManager.__init__` | __init__ 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `PersonStateManager.create_person_state` | create_person_state 함수의 주요 기능을 수행합니다. | dict | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.update_person` | update_person 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.mark_crop_saved` | mark_crop_saved 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.mark_recording_started` | mark_recording_started 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.mark_recording_stopped` | mark_recording_stopped 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.mark_vlm_done` | VLM 분석 완료 상태 기록 | None | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.get_state` | get_state 함수의 주요 기능을 수행합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.has_crop_saved` | has_crop_saved 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.is_recording` | is_recording 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.is_vlm_done` | is_vlm_done 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonStateManager.remove_disappeared_persons` | remove_disappeared_persons 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/person_tracker.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonTracker` | YOLO와 ByteTrack으로 대상 객체를 추적합니다. | PersonTracker ???? | ??? ?? ?? ?? | ?? ?? |
| `PersonTracker.__init__` | 객체 추적 모델과 대상 클래스 설정을 초기화합니다. | None | YOLO 모델 로딩 오류 | 기본 신뢰도 임계값 0.7, YOLO 지연 import |
| `PersonTracker.track` | 프레임에서 대상 객체를 탐지하고 추적합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/analysis/pipeline/person_frame_processor.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonFrameProcessor` | 추적된 인물 하나에 대한 프레임 처리 책임을 담당합니다. | PersonFrameProcessor ???? | ??? ?? ?? ?? | ?? ?? |
| `PersonFrameProcessor.__init__` | 인물 처리에 필요한 협력 객체를 주입합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `PersonFrameProcessor.process` | 추적 인물 상태를 갱신하고 필요한 화면 주석을 그립니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonFrameProcessor._should_queue_vlm` | VLM 분석 큐 등록 가능 여부를 판단합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `PersonFrameProcessor._queue_vlm` | 전신 crop을 저장하고 VLM 작업 큐에 등록합니다. | list | ??? ?? ?? ?? | ?? ?? |
| `PersonFrameProcessor._draw_annotation` | 프레임 위에 추적 박스와 라벨을 그립니다. | None | ??? ?? ?? ?? | ?? ?? |
| `PersonFrameProcessor._build_event` | 인물 이벤트 딕셔너리를 생성합니다. | dict | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/analysis/video_stream.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `VideoStream` | 웹캠 또는 RTSP 영상 입력을 공통 인터페이스로 감쌉니다. | VideoStream 객체 | 없음 | RTSP 입력은 별도 수신 thread 사용 |
| `VideoStream.__init__` | 입력 소스와 RTSP 수신 상태를 초기화합니다. | None | 없음 | 복구 URL이 있으면 복구 관리자 생성 |
| `VideoStream.open` | 영상 입력을 엽니다. | bool | OpenCV 열기 실패 | RTSP는 수신 thread 시작 후 True |
| `VideoStream.read` | 최신 영상 프레임을 읽습니다. | (bool, frame) | 프레임 없음 | RTSP 장애/복구 상태 기록 |
| `VideoStream.get_fps` | 입력 영상의 FPS를 반환합니다. | 숫자 | 없음 | 알 수 없으면 30 |
| `VideoStream.get_frame_size` | 입력 영상의 프레임 크기를 반환합니다. | tuple | 없음 | 기본 640x480 |
| `VideoStream.is_recovering` | RTSP 입력이 현재 복구 대기 상태인지 반환합니다. | bool | 없음 | UI 상태 메시지에 사용 |
| `VideoStream.get_last_recovery_result` | 마지막 백업 복구 요청 결과를 반환합니다. | dict 또는 None | 없음 | VideoWorker가 UI 이벤트로 표시 |
| `VideoStream.release` | 영상 입력 자원을 해제합니다. | None | 없음 | RTSP receiver와 VideoCapture 정리 |
| `VideoStream._read_rtsp_frame` | RTSP 수신기에서 새 프레임을 가져오고 장애/복구 상태를 기록합니다. | (bool, frame) | 없음 | 내부 함수 |
| `VideoStream._record_rtsp_failure` | RTSP 프레임 미수신 상태를 복구 관리자에 기록합니다. | None | 없음 | 내부 함수 |
| `VideoStream._record_rtsp_recovery` | RTSP 프레임 재수신 상태를 복구 관리자에 기록합니다. | None | 복구 요청 실패 결과 | 내부 함수 |

## `src/ai_cctv/ai_server/analysis/rtsp_receiver.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `RtspFrameSnapshot` | RTSP 수신기가 보관한 최신 프레임 상태를 표현합니다. | RtspFrameSnapshot 객체 | 없음 | dataclass |
| `is_rtsp_source` | 입력 소스가 RTSP URL인지 확인합니다. | bool | 없음 | `rtsp://` 문자열 판정 |
| `check_rtsp_port_open` | RTSP URL의 TCP 포트가 열려 있는지 빠르게 확인합니다. | bool | False | socket timeout 사용 |
| `RtspFrameReceiver` | RTSP 프레임을 백그라운드에서 수신하고 재연결을 관리합니다. | RtspFrameReceiver 객체 | 없음 | OpenCV 장기 대기 완화 |
| `RtspFrameReceiver.__init__` | RTSP 수신 thread, watchdog, 동기화 객체를 초기화합니다. | None | 없음 | 조건 변수와 capture lock 사용 |
| `RtspFrameReceiver.start` | RTSP 수신 thread와 watchdog thread를 시작합니다. | None | thread 시작 오류 | FFmpeg TCP timeout 설정 |
| `RtspFrameReceiver.read_new_frame` | 이전 순번 이후의 최신 프레임을 반환합니다. | RtspFrameSnapshot | 프레임 없음 snapshot | sequence 기반 중복 방지 |
| `RtspFrameReceiver.stop` | RTSP 수신 thread와 watchdog thread를 중지합니다. | None | 없음 | 활성 capture 강제 해제 |
| `RtspFrameReceiver._watchdog_loop` | 프레임 정체가 길어지면 활성 VideoCapture를 강제로 해제합니다. | None | release 오류 | 5초 기본 timeout |
| `RtspFrameReceiver._receive_loop` | RTSP 연결과 프레임 수신을 반복합니다. | None | 연결 실패 메시지 | 내부 재연결 루프 |
| `RtspFrameReceiver._read_capture_until_failure` | 열려 있는 VideoCapture에서 프레임을 읽고 실패 시 루프를 종료합니다. | None | 없음 | 연속 실패 80회 기준 |
| `RtspFrameReceiver._set_active_capture` | watchdog이 감시할 현재 VideoCapture 객체를 등록합니다. | None | 없음 | capture lock 사용 |
| `RtspFrameReceiver._clear_active_capture` | 현재 VideoCapture 객체가 감시 대상이면 등록을 해제합니다. | None | 없음 | 중복 release 방지 |
| `RtspFrameReceiver._has_active_capture` | watchdog이 해제할 수 있는 활성 VideoCapture가 있는지 반환합니다. | bool | 없음 | 내부 상태 확인 |
| `RtspFrameReceiver._is_active_capture` | 전달된 VideoCapture가 현재 감시 대상인지 확인합니다. | bool | 없음 | read 실패 후 즉시 종료 판단 |
| `RtspFrameReceiver._release_active_capture` | watchdog 또는 종료 요청이 활성 VideoCapture를 강제로 해제합니다. | bool | release 오류 | OpenCV read hang 완화 |
| `RtspFrameReceiver._store_frame` | 수신한 최신 프레임을 thread-safe하게 저장합니다. | None | 없음 | frame copy 저장 |
| `RtspFrameReceiver._set_connection_state` | RTSP 연결 상태와 마지막 오류 메시지를 갱신합니다. | None | 없음 | 대기 중인 read 호출 알림 |
| `RtspFrameReceiver._update_capture_metadata` | VideoCapture에서 FPS와 프레임 크기 정보를 읽어 저장합니다. | None | 없음 | 기본값 보정 |

## `src/ai_cctv/ai_server/analysis/video_worker.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `VideoWorker` | 영상 캡처, 추적, 녹화, 선택적 VLM 분석을 조정합니다. | VideoWorker ???? | ??? ?? ?? ?? | ??: QThread, ?? ?? |
| `VideoWorker.__init__` | 영상 처리 스레드와 협력 객체를 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `VideoWorker.run` | 스레드 메인 루프에서 프레임 처리와 신호 발행을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `VideoWorker._start_tracker_loading` | YOLO 추적 모델을 별도 thread에서 비동기로 로드합니다. | None | 없음 | 프리뷰 우선 표시 |
| `VideoWorker._load_tracker` | YOLO 추적 모델을 로드하고 준비되면 분석 루프에 연결합니다. | None | 모델 로딩 오류 | loader thread에서 실행 |
| `VideoWorker._disable_ai_pipeline` | AI 분석 파이프라인을 끄고 CCTV 프리뷰 모드로 전환합니다. | None | 없음 | YOLO/VLM 실패 시 사용 |
| `VideoWorker._record_person_clip` | 추적 인물의 이벤트 클립 저장을 ClipManager에 위임합니다. | None | 없음 | 주석 없는 원본 프레임 저장 |
| `VideoWorker._get_tracker` | 현재 사용할 수 있는 YOLO 추적 모델을 반환합니다. | PersonTracker 또는 None | 없음 | lock으로 보호 |
| `VideoWorker._start_vlm_loading` | VLM 작업자를 별도 thread에서 준비합니다. | None | 없음 | 선택 기능 |
| `VideoWorker._load_vlm_worker` | VLM 작업자를 생성하고 인물 처리 파이프라인에 연결합니다. | None | VLM 준비 오류 | loader thread에서 실행 |
| `VideoWorker._emit_preview_frame` | AI 모델 준비 전 프리뷰 프레임과 기본 지표를 발행합니다. | None | 없음 | 영상 우선 출력 |
| `VideoWorker._emit_stream_wait_status` | RTSP 스트림 복구 대기 상태를 과도하지 않게 UI에 알립니다. | None | 없음 | 5초 간격 제한 |
| `VideoWorker._emit_recovery_result_if_needed` | RTSP 복구 후 백업 ZIP 요청 결과가 있으면 UI 이벤트로 표시합니다. | None | 없음 | 성공/실패 메시지 표시 |
| `VideoWorker.stop` | 영상 처리 루프를 중지하고 스레드 종료를 기다립니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `VideoWorker._cleanup` | 사용 중인 분석 작업자, 녹화기, 영상 스트림을 정리합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `VideoWorker._join_loader_threads` | 모델 로더 thread가 짧은 시간 안에 끝나면 정리합니다. | None | 없음 | 종료 대기 최소화 |
| `VideoWorker._create_default_notification_dispatcher` | 기본 Discord 이상 상황 알림 디스패처를 생성합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/analysis/vlm_person_analyzer.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonAnalyzer` | 운영 코드에서 사용할 인물 이미지 VLM 분석기입니다. | PersonAnalyzer ???? | ??? ?? ?? ?? | ??: QwenPersonAnalyzer |

## `src/ai_cctv/ai_server/analysis/vlm_person_analyzer_qwen.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonAnalyzer` | PersonAnalyzer 클래스의 주요 책임을 수행합니다. | PersonAnalyzer ???? | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer.__init__` | __init__ 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer._build_messages` | _build_messages 함수의 주요 기능을 수행합니다. | list | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer.analyze` | analyze 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonAnalyzer._clean_result` | _clean_result 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/analysis/vlm_person_analyzer_qwen_test.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `PersonAnalyzer` | PersonAnalyzer 클래스의 주요 책임을 수행합니다. | PersonAnalyzer ???? | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer.__init__` | __init__ 함수의 주요 기능을 수행합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer._build_messages` | _build_messages 함수의 주요 기능을 수행합니다. | list | ??? ?? ?? ?? | ?? ?? |
| `PersonAnalyzer.analyze` | analyze 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `PersonAnalyzer._clean_result` | _clean_result 함수의 주요 기능을 수행합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |

## `src/ai_cctv/ai_server/analysis/vlm_worker.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `VLMWorker` | VLM 모델 로딩과 crop 이미지 분석 작업을 관리합니다. | VLMWorker 객체 | 없음 | 준비/실패 이벤트 제공 |
| `VLMWorker.__init__` | VLM 작업 큐, 준비 상태 이벤트, 결과 콜백을 초기화합니다. | None | 없음 | ready/failed event 보유 |
| `VLMWorker.start` | VLM 모델 로딩과 분석 큐 처리를 위한 thread를 시작합니다. | None | thread 시작 오류 | 중복 시작 방지 |
| `VLMWorker.is_ready` | VLM 모델이 분석 가능한 상태인지 반환합니다. | bool | 없음 | ready_event 조회 |
| `VLMWorker.has_failed` | VLM 모델 로딩이 실패했는지 반환합니다. | bool | 없음 | failed_event 조회 |
| `VLMWorker.wait_until_ready` | 지정 시간 동안 VLM 준비 완료를 기다립니다. | bool | 없음 | VideoWorker가 대기/실패 판단에 사용 |
| `VLMWorker.add_task` | VLM 분석 큐에 인물 crop 이미지를 등록합니다. | None | 없음 | 준비 전 작업은 무시 |
| `VLMWorker._run` | VLM 모델을 로딩하고 큐에 등록된 분석 작업을 반복 처리합니다. | None | 모델 로딩/분석 오류 | Discord 알림과 GUI 이벤트 전송 |
| `VLMWorker._emit_result_event` | VLM 분석 결과를 GUI 이벤트 콜백으로 전달합니다. | None | 없음 | `vlm_done` 이벤트 생성 |
| `VLMWorker.stop` | VLM 분석 thread를 중지하고 모델 자원을 정리합니다. | None | 없음 | 종료 대기 포함 |
| `VLMWorker.cleanup` | VLM 분석기와 GPU 캐시 자원을 해제합니다. | None | 없음 | torch 지연 import |

## `src/ai_cctv/ai_server/server_run.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `preload_ai_runtime_libraries` | PyQt 로딩 전에 AI 런타임 네이티브 라이브러리를 초기화합니다. | None | PyTorch 초기화 오류 | torch DLL 로딩 순서 안정화 |
| `main` | Windows OS와 PyQt5 bootstrap을 먼저 확인한 뒤 AI server 관제 GUI 애플리케이션을 실행합니다. | None | 비 Windows 환경 SystemExit, PyQt5 설치 거부, PyTorch 초기화 오류 | OS guard와 최소 GUI 의존성 확인 이후 UI 시작 |

## `src/ai_cctv/ai_server/runtime/__init__.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `RuntimeEnvironmentChecker` | AI server 실행에 필요한 패키지와 모델 점검 클래스를 외부로 노출합니다. | 클래스 참조 | 없음 | `environment_check.py` 재노출 |
| `RuntimeInstaller` | 누락된 패키지와 모델을 설치하는 클래스를 외부로 노출합니다. | 클래스 참조 | 없음 | `environment_check.py` 재노출 |
| `RuntimeRequirement` | 런타임 요구사항 데이터 클래스를 외부로 노출합니다. | 클래스 참조 | 없음 | `environment_check.py` 재노출 |
| `RuntimeRequirementResult` | 런타임 요구사항 점검 결과 클래스를 외부로 노출합니다. | 클래스 참조 | 없음 | `environment_check.py` 재노출 |
| `RuntimeReadinessReport` | 전체 런타임 준비 상태 보고 클래스를 외부로 노출합니다. | 클래스 참조 | 없음 | `environment_check.py` 재노출 |
| `ensure_pyqt5_available` | PyQt5 bootstrap 확인 함수를 외부로 노출합니다. | 함수 참조 | 없음 | `bootstrap.py` 재노출 |
| `ensure_windows_os` | Windows 전용 실행 검증 함수를 외부로 노출합니다. | 함수 참조 | 없음 | `os_guard.py` 재노출 |
| `is_windows_os` | OS 판별 함수를 외부로 노출합니다. | 함수 참조 | 없음 | `os_guard.py` 재노출 |

## `src/ai_cctv/ai_server/runtime/bootstrap.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `ensure_pyqt5_available` | 런타임 점검 창을 띄우기 전에 PyQt5 존재 여부를 확인하고 없으면 설치 여부를 묻습니다. | None | SystemExit(1), RuntimeError | tkinter 기반 bootstrap 창 사용 |
| `_is_pyqt5_available` | 현재 Python 환경에서 PyQt5 import 경로를 찾을 수 있는지 확인합니다. | bool | 없음 | 내부 함수 |
| `_ask_install_pyqt5_with_tkinter` | PyQt5가 없을 때 O/X 선택용 tkinter 창을 표시합니다. | bool | tkinter 사용 불가 시 False | PyQt5 없는 환경의 예외 경로 |
| `_ask_install_pyqt5_with_tkinter.choose_install` | 사용자의 자동 설치 선택을 기록하고 창을 닫습니다. | None | 없음 | 내부 중첩 함수 |
| `_ask_install_pyqt5_with_tkinter.choose_cancel` | 사용자의 설치 거부 선택을 기록하고 창을 닫습니다. | None | 없음 | 내부 중첩 함수 |
| `_install_pyqt5` | 현재 Python 실행 파일을 사용해 PyQt5를 pip로 설치합니다. | None | RuntimeError | `python -m pip install PyQt5` |
| `_show_bootstrap_error` | bootstrap 오류를 가능한 경우 tkinter 메시지 창으로 표시합니다. | None | 없음 | GUI 표시 실패 시 무시 |
| `_print_bootstrap_error` | bootstrap 오류를 표준 오류 또는 지정 스트림에 출력합니다. | None | 없음 | 콘솔 fallback |

## `src/ai_cctv/ai_server/runtime/os_guard.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `is_windows_os` | 현재 또는 전달받은 OS 이름이 Windows인지 판별합니다. | bool | 없음 | 테스트에서 OS 이름 주입 가능 |
| `ensure_windows_os` | AI server가 Windows에서 실행 중인지 확인하고 아니면 오류를 출력한 뒤 종료합니다. | None | SystemExit(1) | `server_run.main`의 첫 관문 |

## `src/ai_cctv/ai_server/runtime/environment_check.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `RuntimeRequirement` | 패키지 또는 모델 요구사항의 이름, 종류, 설치 식별자를 보관합니다. | RuntimeRequirement 객체 | 없음 | dataclass, package/model 공통 표현 |
| `RuntimeRequirementResult` | 단일 요구사항의 설치 여부와 상세 메시지를 보관합니다. | RuntimeRequirementResult 객체 | 없음 | dataclass |
| `RuntimeReadinessReport` | 전체 런타임 요구사항 점검 결과를 보관합니다. | RuntimeReadinessReport 객체 | 없음 | dataclass |
| `RuntimeReadinessReport.missing_required` | 누락된 필수 요구사항 목록을 반환합니다. | RuntimeRequirementResult 목록 | 없음 | 설치 대상 추출 |
| `RuntimeReadinessReport.is_ready` | 필수 요구사항이 모두 준비됐는지 반환합니다. | bool | 없음 | UI 분기 조건 |
| `RuntimeReadinessReport.to_text` | 점검 결과를 여러 줄 문자열로 변환합니다. | 문자열 | 없음 | 설치 확인 창 표시용 |
| `RuntimeEnvironmentChecker` | AI server의 패키지와 모델 캐시 상태를 점검합니다. | RuntimeEnvironmentChecker 객체 | 없음 | 프로젝트 루트 주입 가능 |
| `RuntimeEnvironmentChecker.__init__` | 점검할 요구사항과 프로젝트 루트 경로를 초기화합니다. | None | 없음 | 테스트용 요구사항 주입 가능 |
| `RuntimeEnvironmentChecker.check` | 모든 요구사항을 점검해 준비 상태 보고서를 반환합니다. | RuntimeReadinessReport | 없음 | 시작 시 자동 호출 |
| `RuntimeEnvironmentChecker._check_requirement` | 요구사항 종류에 맞는 점검 함수를 호출합니다. | RuntimeRequirementResult | 알 수 없는 종류 결과 | 내부 함수 |
| `RuntimeEnvironmentChecker._check_package` | Python 패키지 import 가능 여부와 버전을 확인합니다. | RuntimeRequirementResult | 패키지 누락 결과 | `importlib.util.find_spec` 사용 |
| `RuntimeEnvironmentChecker._check_yolo_model` | YOLO 모델 파일 존재 여부를 확인합니다. | RuntimeRequirementResult | 모델 파일 누락 결과 | `AI_CCTV_YOLO_MODEL_PATH` 반영 |
| `RuntimeEnvironmentChecker._check_qwen_model` | Qwen 모델 config가 HuggingFace 캐시에 있는지 확인합니다. | RuntimeRequirementResult | 캐시 누락 결과 | 네트워크 없이 local cache 확인 |
| `RuntimeInstaller` | 누락된 패키지 설치와 모델 다운로드를 수행합니다. | RuntimeInstaller 객체 | 없음 | UI에서 O 선택 시 사용 |
| `RuntimeInstaller.__init__` | 설치 명령에 사용할 Python 실행 파일을 초기화합니다. | None | 없음 | 기본값은 현재 Python |
| `RuntimeInstaller.install_missing` | 누락된 요구사항을 순서대로 설치하거나 다운로드합니다. | 설치 로그 목록 | RuntimeError | package, YOLO, Qwen 종류별 분기 |
| `RuntimeInstaller._install_package` | pip로 Python 패키지를 설치합니다. | 로그 문자열 | RuntimeError | subprocess 기반 |
| `RuntimeInstaller._download_yolo_model` | Ultralytics를 통해 YOLO 모델 준비를 시도합니다. | 로그 문자열 | RuntimeError | 별도 Python 프로세스 사용 |
| `RuntimeInstaller._download_qwen_model` | HuggingFace Hub에서 Qwen 모델 캐시를 다운로드합니다. | 로그 문자열 | RuntimeError | 모델을 메모리에 로드하지 않음 |
| `RuntimeInstaller._run_python_script` | 별도 Python 프로세스로 설치 보조 스크립트를 실행합니다. | None | RuntimeError | stdout/stderr 포함 |
| `build_default_requirements` | AI server 기본 실행 요구사항 목록을 생성합니다. | RuntimeRequirement 목록 | 없음 | 환경 변수로 모델 식별자 변경 가능 |
| `_read_distribution_version` | 설치 식별자에서 패키지 버전을 조회합니다. | 버전 문자열 또는 빈 문자열 | 없음 | 내부 함수 |

## `src/ai_cctv/ai_server/connection/__init__.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeConnectionConfig` | Edge node 연결 설정 객체를 패키지 외부로 노출합니다. | 클래스 참조 | 없음 | `edge_connection.py` 재노출 |
| `EdgeConnectionValidationResult` | Edge node 연결 검증 결과 객체를 패키지 외부로 노출합니다. | 클래스 참조 | 없음 | `edge_connection.py` 재노출 |
| `EdgeConnectionValidator` | Edge node 연결 검증 객체를 패키지 외부로 노출합니다. | 클래스 참조 | 없음 | `edge_connection.py` 재노출 |
| `parse_edge_startup_text` | Edge node 표준 출력 파서 함수를 패키지 외부로 노출합니다. | 함수 참조 | 없음 | UI에서 import 경로 단순화 |

## `src/ai_cctv/ai_server/connection/edge_connection.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeConnectionConfig` | AI server가 Edge node에 접속하는 데 필요한 RTSP, MQTT, 백업 복구 설정을 보관합니다. | EdgeConnectionConfig 객체 | 없음 | dataclass |
| `EdgeConnectionConfig.from_environment` | 환경 변수에서 AI server 연결 설정을 생성합니다. | EdgeConnectionConfig 객체 | 잘못된 포트 값 | 기존 환경 변수 호환 |
| `EdgeConnectionConfig.apply_environment` | 현재 연결 설정을 기존 AI server 코드가 읽는 환경 변수에 반영합니다. | None | 환경 변수 설정 오류 | MQTT/복구/RTSP 값 반영 |
| `EdgeConnectionConfig.video_source` | Edge node 모드에서는 RTSP URL을, Windows 로컬 카메라 모드에서는 카메라 인덱스를 반환합니다. | RTSP URL 또는 정수 인덱스 | 없음 | `VideoWorker` 입력 소스 분기 |
| `EdgeConnectionValidationResult` | Edge node 연결 검증 결과를 표현합니다. | EdgeConnectionValidationResult 객체 | 없음 | dataclass |
| `EdgeConnectionValidationResult.message` | 검증 결과를 화면 표시용 문자열로 변환합니다. | 문자열 | 없음 | 실패 사유 줄바꿈 |
| `EdgeConnectionValidator` | RTSP, MQTT, 백업 복구 API의 접속 가능 여부를 검증합니다. | EdgeConnectionValidator 객체 | 없음 | UI와 검증 책임 분리 |
| `EdgeConnectionValidator.__init__` | 연결 검증 제한 시간을 초기화합니다. | None | 없음 | 테스트 시 timeout 주입 가능 |
| `EdgeConnectionValidator.validate` | Edge node 연결 설정의 필수 접속 가능 여부를 검증합니다. | EdgeConnectionValidationResult | 네트워크 실패 결과 | 메인 창 시작 조건 |
| `EdgeConnectionValidator._validate_local_camera` | Windows 로컬 카메라 인덱스를 OpenCV로 열 수 있는지 검증합니다. | 오류 목록 | 없음 | 로컬 카메라 모드 전용 |
| `EdgeConnectionValidator._validate_rtsp` | RTSP URL 형식과 TCP 포트 접근 가능 여부를 검증합니다. | 오류 목록 | 없음 | 내부 함수 |
| `EdgeConnectionValidator._validate_mqtt` | MQTT broker TCP 포트 접근 가능 여부를 검증합니다. | 오류 목록 | 없음 | 내부 함수 |
| `EdgeConnectionValidator._validate_backup_recovery` | 백업 복구 HTTP endpoint 접근 가능 여부를 검증합니다. | 오류 목록 | 없음 | HTTP 4xx는 연결 성공으로 판단 |
| `parse_edge_startup_text` | Edge node 표준 출력 블록에서 AI server 연결 설정을 추출합니다. | EdgeConnectionConfig 객체 | ValueError | 출력 블록 붙여넣기 지원 |
| `_parse_key_value_lines` | 여러 줄 문자열에서 KEY=VALUE 형식의 값을 추출합니다. | dict | 없음 | 내부 함수 |
| `_normalize_key` | 환경 변수 또는 출력 항목 이름을 내부 키로 정규화합니다. | 문자열 | 없음 | PowerShell `$env:` 제거 |
| `_split_host_port` | host:port 문자열을 호스트와 포트로 분리합니다. | tuple | 없음 | MQTT_BROKER 해석 |

## `src/ai_cctv/ai_server/recovery/network_recovery_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `NetworkRecoveryConfig` | 네트워크 복구 요청 설정을 표현합니다. | NetworkRecoveryConfig 객체 | 없음 | dataclass |
| `NetworkRecoveryManager` | RTSP 단절 시작/복구 시각을 기록하고 누락 영상 ZIP을 요청합니다. | NetworkRecoveryManager 객체 | 없음 | requests 사용 |
| `NetworkRecoveryManager.__init__` | 복구 요청 상태와 중복 요청 방지 목록을 초기화합니다. | None | 없음 | 요청 구간 set 보관 |
| `NetworkRecoveryManager.has_active_failure` | 현재 기록 중인 네트워크 장애 구간이 있는지 반환합니다. | bool | 없음 | 복구 시점 판단 |
| `NetworkRecoveryManager.record_failure` | 네트워크 장애 시작 시각을 기록합니다. | dict | 없음 | 중복 시작 방지 |
| `NetworkRecoveryManager.record_recovery` | 네트워크 복구 시각을 기록하고 필요하면 백업 ZIP을 요청합니다. | dict | 요청 실패 결과 | 최소 장애 시간/중복 구간 확인 |
| `NetworkRecoveryManager.build_payload` | 복구 요청에 사용할 시작/종료 시각 payload를 생성합니다. | dict | 없음 | ISO 초 단위 문자열 |
| `NetworkRecoveryManager.request_recovery` | Edge node FastAPI 복구 서버에 ZIP 파일을 요청하고 저장합니다. | dict | requests/HTTP/네트워크 오류 | query params 사용 |
| `NetworkRecoveryManager._save_file_response` | HTTP 응답 파일명을 해석하고 ZIP 파일을 저장합니다. | Path | 파일 저장 오류 | 중복 파일명 보정 |
| `NetworkRecoveryManager._get_response_filename` | Content-Disposition 헤더에서 파일명을 추출합니다. | 문자열 또는 None | 없음 | RFC 5987 일부 지원 |
| `NetworkRecoveryManager._make_default_filename` | 복구 응답에 파일명이 없을 때 사용할 기본 파일명을 생성합니다. | 문자열 | 없음 | 카메라 ID와 시간 포함 |
| `NetworkRecoveryManager._get_unique_save_path` | 같은 파일명이 있을 때 번호를 붙인 저장 경로를 반환합니다. | Path | 없음 | 덮어쓰기 방지 |
| `NetworkRecoveryManager._get_request_key` | 중복 요청 확인에 사용할 키를 생성합니다. | tuple | 없음 | 카메라 ID와 시간 구간 |
| `NetworkRecoveryManager._format_time` | datetime 값을 초 단위 ISO 문자열로 변환합니다. | 문자열 | 없음 | microsecond 제거 |
| `NetworkRecoveryManager._sanitize_filename` | 파일명에서 경로와 Windows 금지 문자를 제거합니다. | 문자열 | 없음 | 보안 보정 |
| `build_network_recovery_manager_from_env` | 환경 변수 기준으로 NetworkRecoveryManager를 생성합니다. | NetworkRecoveryManager 또는 None | ValueError | URL이 없으면 비활성화 |

## `src/ai_cctv/ai_server/monitoring/resource_monitor_client.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `MqttResourceMonitorConfig` | AI server의 MQTT 상태 수신 설정을 표현합니다. | MqttResourceMonitorConfig 인스턴스 | 없음 | broker, topic, timeout, stale 기준 포함 |
| `MqttResourceMonitorConfig.from_environment` | 환경 변수에서 MQTT 수신 설정을 생성합니다. | MqttResourceMonitorConfig 인스턴스 | ValueError | `AI_CCTV_MQTT_*` 환경 변수 지원 |
| `ResourceMonitorClient` | Edge node MQTT 상태 topic 구독 책임을 담당합니다. | ResourceMonitorClient 인스턴스 | 없음 | 공유 클라이언트로 연결 재사용 |
| `ResourceMonitorClient.__init__` | MQTT 클라이언트, 수신 캐시, 동기화 이벤트를 초기화합니다. | None | 없음 | paho-mqtt callback 등록 |
| `ResourceMonitorClient.matches_config` | 현재 클라이언트 설정과 새 설정이 같은지 비교합니다. | bool | 없음 | 환경 변수 변경 시 재생성 판단 |
| `ResourceMonitorClient.start` | MQTT broker에 접속하고 상태 topic 구독을 시작합니다. | None | MQTT 연결 오류 | background loop 시작 |
| `ResourceMonitorClient.request_resource_usage` | 최신 MQTT 상태 JSON을 반환하거나 새 메시지를 기다립니다. | dict | RuntimeError | stale 메시지는 실패로 처리 |
| `ResourceMonitorClient.stop` | MQTT 구독 loop와 broker 연결을 종료합니다. | None | MQTT 종료 오류 | 상태 조회 창 종료 시 호출 가능 |
| `ResourceMonitorClient._handle_connect` | MQTT 연결 완료 시 상태 topic을 구독합니다. | None | 연결 실패 메시지 | paho v1/v2 callback 호환 |
| `ResourceMonitorClient._handle_message` | MQTT payload를 JSON 딕셔너리로 변환해 캐시에 저장합니다. | None | JSON 해석 오류 | worker 대기 이벤트 해제 |
| `ResourceMonitorClient._get_fresh_resource_usage` | 최신 캐시가 유효하면 복사본을 반환합니다. | dict 또는 None | 없음 | stale 기준 적용 |
| `build_monitor_client` | 환경 변수 기준으로 공유 MQTT 클라이언트를 생성합니다. | ResourceMonitorClient 인스턴스 | 없음 | 설정 변경 시 기존 연결 종료 |
| `request_resource_usage` | 공유 MQTT 클라이언트로 Edge node 자원 상태를 수신합니다. | dict | RuntimeError | UI worker에서 호출 |
| `stop_monitor_client` | 공유 MQTT 클라이언트 연결을 종료합니다. | None | 없음 | 상태 조회 창 closeEvent에서 호출 |
| `print_resource_usage` | 자원 사용률 응답을 JSON 문자열로 출력합니다. | None | JSON 직렬화 오류 | 한글 출력 보존 |
| `_create_mqtt_client` | paho-mqtt 버전에 맞는 MQTT 클라이언트를 생성합니다. | MQTT Client | ImportError | Callback API v1/v2 호환 |
| `_to_int_reason_code` | paho 연결 결과 코드를 정수로 변환합니다. | int | ValueError | v2 ReasonCode 대응 |
| `main` | Edge node MQTT 상태 메시지를 한 번 수신해 콘솔에 출력합니다. | None | RuntimeError | `python -m` 실행 진입점 |

## `src/ai_cctv/edge_node/monitoring/resource_monitor_publisher.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `MqttResourceMonitorConfig` | Edge node의 MQTT 상태 발행 설정을 표현합니다. | MqttResourceMonitorConfig 인스턴스 | 없음 | broker, topic, QoS, retain 포함 |
| `MqttResourceMonitorConfig.from_environment` | 환경 변수에서 MQTT 발행 설정을 생성합니다. | MqttResourceMonitorConfig 인스턴스 | ValueError | `AI_CCTV_MQTT_*` 환경 변수 지원 |
| `ResourceUsageCollector` | Edge node 전체 시스템, 지정 프로세스, UPS 전원 상태 수집 책임을 담당합니다. | ResourceUsageCollector 인스턴스 | 없음 | 기본 프로세스 ID는 현재 publisher 프로세스 |
| `ResourceUsageCollector.__init__` | 수집 대상 프로세스 ID, CPU 샘플링 시간, 전원 상태 provider를 초기화합니다. | None | 없음 | 전원 provider 미주입 시 기본 캐시 provider 생성 |
| `ResourceUsageCollector.collect` | 전체 CPU, 전체 메모리, 대상 프로세스, UPS 전원 상태를 딕셔너리로 반환합니다. | dict | RuntimeError | `power` 섹션을 함께 포함 |
| `ResourceUsageCollector._get_process` | psutil 기준 모니터링 대상 프로세스 객체를 반환합니다. | psutil.Process | RuntimeError | 프로세스 없음/권한 오류를 한글 메시지로 변환 |
| `MqttResourceMonitorPublisher` | 수집한 자원 상태를 MQTT broker로 주기 발행합니다. | MqttResourceMonitorPublisher 인스턴스 | 없음 | Edge node 실행 보조 프로세스 |
| `MqttResourceMonitorPublisher.__init__` | MQTT 발행 설정, 수집기, MQTT 클라이언트를 초기화합니다. | None | ImportError | paho-mqtt 필요 |
| `MqttResourceMonitorPublisher.publish_once` | 자원 상태를 한 번 수집해 MQTT topic으로 발행합니다. | dict | MQTT 발행 오류 | retain 옵션 지원 |
| `MqttResourceMonitorPublisher.run_forever` | broker에 접속한 뒤 설정 주기마다 상태를 발행합니다. | 반환 없음 | MQTT 연결/발행 오류 | 기본 2초 주기 |
| `MqttResourceMonitorPublisher.stop` | MQTT loop와 broker 연결을 종료합니다. | None | MQTT 종료 오류 | KeyboardInterrupt 처리 |
| `build_resource_usage_collector_from_environment` | 환경 변수 기준으로 자원 수집기를 생성합니다. | ResourceUsageCollector 인스턴스 | ValueError | `AI_CCTV_MONITOR_PROCESS_ID` 지원 |
| `build_resource_monitor_publisher` | 환경 변수 기준으로 MQTT publisher를 생성합니다. | MqttResourceMonitorPublisher 인스턴스 | ImportError | 실행 진입점에서 사용 |
| `_create_mqtt_client` | paho-mqtt 버전에 맞는 MQTT 클라이언트를 생성합니다. | MQTT Client | ImportError | Callback API v1/v2 호환 |
| `_load_psutil_module` | 설치된 psutil 모듈을 실제 수집 시점에 불러옵니다. | psutil 모듈 | ImportError | 테스트 import와 런타임 의존 분리 |
| `_read_bool_env` | 환경 변수 문자열을 bool 값으로 변환합니다. | bool | 없음 | retain 설정 처리 |
| `main` | Edge node 자원 상태 MQTT 발행 루프를 실행합니다. | 반환 없음 | MQTT 연결/발행 오류 | `python -m` 실행 진입점 |

## `src/ai_cctv/edge_node/monitoring/power_status.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `PowerStatusSnapshot` | UPS Plus 전원 상태 한 번의 측정값을 표현합니다. | PowerStatusSnapshot 인스턴스 | 없음 | dataclass, JSON 변환 가능 |
| `PowerStatusSnapshot.to_dict` | 전원 상태 스냅샷을 JSON 직렬화 가능한 딕셔너리로 변환합니다. | dict | 없음 | `battery_remaining_percent`, `external_power_connected` 포함 |
| `PowerStatusSnapshot.unavailable` | UPS 값을 읽을 수 없을 때 사용할 실패 스냅샷을 생성합니다. | PowerStatusSnapshot 인스턴스 | 없음 | `available=False`와 오류 메시지 포함 |
| `UpsPlusPowerReader` | 52Pi EP-0136 UPS Plus I2C 레지스터 읽기 책임을 담당합니다. | UpsPlusPowerReader 인스턴스 | 없음 | 기본 I2C 주소 `0x17` |
| `UpsPlusPowerReader.__init__` | I2C 버스, 장치 주소, 외부 전원 판단 전압 기준을 초기화합니다. | None | 없음 | 기본 버스 1, 기준 4000mV |
| `UpsPlusPowerReader.read_snapshot` | 배터리 잔량, USB-C/MicroUSB 입력 전압, 전원 상태 원본값을 읽습니다. | PowerStatusSnapshot 인스턴스 | 실패 스냅샷 | SMBus 오류를 MQTT 발행 장애로 전파하지 않음 |
| `UpsPlusPowerReader._open_bus` | SMBus 인스턴스를 열어 I2C 통신을 준비합니다. | SMBus 인스턴스 | RuntimeError | `smbus2` 우선, `smbus` fallback |
| `UpsPlusPowerReader._read_percent` | 배터리 잔량 레지스터 `0x13-0x14`를 백분율로 읽습니다. | int | SMBus 읽기 오류 | 0~100 범위로 보정 |
| `UpsPlusPowerReader._read_word` | 연속된 저위/고위 바이트 레지스터를 16비트 정수로 읽습니다. | int | SMBus 읽기 오류 | EP-0136 데모 코드의 little-endian 조합 기준 |
| `UpsPlusPowerReader._read_byte` | UPS Plus 단일 레지스터 바이트 값을 읽습니다. | int | SMBus 읽기 오류 | `read_byte_data` 사용 |
| `CachedPowerStatusProvider` | UPS Plus 전원 상태를 일정 시간 캐시합니다. | CachedPowerStatusProvider 인스턴스 | 없음 | 반복 MQTT 발행 시 I2C 접근 감소 |
| `CachedPowerStatusProvider.__init__` | 전원 상태 리더, 캐시 유지 시간, 동기화 lock을 초기화합니다. | None | 없음 | 기본 캐시 2초 |
| `CachedPowerStatusProvider.get_snapshot` | 캐시가 유효하면 저장값을, 아니면 새 UPS 측정값을 반환합니다. | PowerStatusSnapshot 인스턴스 | 실패 스냅샷 | thread lock으로 동시 요청 보호 |
| `CachedPowerStatusProvider._is_cache_fresh` | 현재 캐시가 재사용 가능한지 판단합니다. | bool | 없음 | monotonic 시간 기준 |
| `_load_smbus_class` | 설치된 SMBus 구현체를 찾아 반환합니다. | SMBus 클래스 | RuntimeError | `smbus2` 또는 `smbus` 필요 |

## `src/ai_cctv/ai_server/storage/clip_manager.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `ClipManager` | 추적 인물별 이벤트 클립 저장을 담당합니다. | ClipManager 객체 | 없음 | `event_clips` 하위 폴더 사용 |
| `ClipManager.__init__` | 클립 저장 경로와 인물별 클립 상태를 초기화합니다. | None | 경로 생성 오류 | FPS 기본값 보정 |
| `ClipManager.update_person` | 현재 프레임을 해당 인물의 이벤트 클립에 기록합니다. | None | writer 생성 실패 | 클립 분할과 crop 복사 처리 |
| `ClipManager.finish_person` | 인물 추적이 끝났을 때 클립 파일과 궤적 이미지를 마감합니다. | None | 없음 | 추적 종료 시 호출 |
| `ClipManager.finish_all` | 현재 열려 있는 모든 인물 클립을 마감합니다. | None | 없음 | 작업자 종료 시 호출 |
| `ClipManager._create_person_state` | 새 인물 클립 저장 상태와 전용 폴더를 생성합니다. | dict | 경로 생성 오류 | 중복 폴더명 회피 |
| `ClipManager._start_new_clip` | 인물 상태에 새 MP4 클립 writer를 연결합니다. | None | writer 생성 실패 | `mp4v` 코덱 사용 |
| `ClipManager._close_writer` | 인물 상태에 연결된 클립 writer를 닫습니다. | None | 없음 | writer release 처리 |
| `ClipManager._should_rotate_clip` | 현재 클립 파일을 새 파일로 분리해야 하는지 판단합니다. | bool | 없음 | 기본 10초 단위 |
| `ClipManager._save_trajectory_image` | 마지막 프레임 위에 인물 이동 궤적 이미지를 저장합니다. | None | 이미지 저장 실패 | `trajectory.jpg` 생성 |
| `ClipManager._copy_crop_once` | 인물 전신 crop 이미지를 클립 폴더에 한 번만 복사합니다. | None | 복사 실패 | `full_crop.jpg` 생성 |
| `ClipManager._get_bbox_center` | 바운딩 박스의 중심 좌표를 계산합니다. | tuple | 형 변환 오류 | 궤적 좌표 생성 |
| `ClipManager._get_frame_size` | 프레임에서 VideoWriter용 크기 튜플을 계산합니다. | tuple | 잘못된 프레임 | `(width, height)` 반환 |
| `ClipManager._get_unique_folder_path` | 중복되지 않는 인물 클립 폴더 경로를 생성합니다. | 문자열 | 없음 | `_2`, `_3` 접미사 사용 |

## `src/ai_cctv/ai_server/storage/path_manager.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `StoragePaths` | 저장소 경로 묶음을 표현합니다. | StoragePaths ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `StoragePathManager` | AI CCTV 저장 폴더 구조를 생성합니다. | StoragePathManager ???? | ??? ?? ?? ?? | ?? ?? |
| `StoragePathManager.__init__` | 저장 경로 규칙을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `StoragePathManager.build_paths` | 루트 경로 기준의 표준 저장 경로를 계산합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `StoragePathManager.ensure_paths` | 표준 저장 폴더를 만들고 경로 묶음을 반환합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/storage/recording_manager.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `RecordingManager` | 원본 영상 프레임을 시간 단위 MP4 파일로 저장합니다. | RecordingManager ???? | ??? ?? ?? ?? | ?? ?? |
| `RecordingManager.__init__` | 녹화 저장 상태와 기본 경로를 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `RecordingManager.start_recording` | 새 MP4 녹화 파일을 시작합니다. | True | ??? ?? ?? ?? | ?? ?? ?? |
| `RecordingManager.write_frame` | 프레임을 현재 녹화 파일에 기록합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `RecordingManager.stop_recording` | 현재 녹화 파일을 닫고 최종 파일명으로 변경합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/stream_receiver.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `RtspPreviewSession` | RTSP 스트림을 OpenCV 창으로 미리보기하는 세션입니다. | RtspPreviewSession ???? | ??? ?? ?? ?? | ?? ?? |
| `RtspPreviewSession.__init__` | RTSP 미리보기 세션을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `RtspPreviewSession.run` | RTSP 스트림을 수신하여 OpenCV 창에 표시합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `RtspPreviewSession._configure_low_latency_capture` | OpenCV FFMPEG 수신 옵션을 낮은 지연 설정으로 구성합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `RtspPreviewSession._show_frames` | VideoCapture에서 프레임을 읽어 미리보기 창에 표시합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `preview_rtsp_stream` | RTSP 미리보기 세션을 생성해 실행합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `main` | 기본 RTSP URL로 수신 미리보기를 실행합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/ui/event_presenter.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EventDisplay` | 이벤트 표시 정보를 담는 값 객체입니다. | EventDisplay ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `EventPresenter` | 이벤트 딕셔너리를 UI 표시 정보로 변환합니다. | EventPresenter ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `EventPresenter.build_display` | 이벤트 유형별 설명과 색상을 생성합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | `vlm_done` 결과 표시 지원 |
| `EventPresenter.get_time_text` | 이벤트 시간 문자열을 가져오거나 현재 시각으로 대체합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/ai_server/ui/edge_status_window.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `ResourceMonitorRequestWorker` | Edge node MQTT 상태 메시지 수신을 UI와 분리된 QThread에서 수행합니다. | ResourceMonitorRequestWorker 인스턴스 | 수신 예외 문자열 | UI 멈춤 방지 |
| `ResourceMonitorRequestWorker.run` | 자원 사용률 수신 결과 또는 오류를 PyQt 신호로 전달합니다. | None | error_ready 신호 | 백그라운드 실행 |
| `ResourceLineGraph` | 최근 자원 사용률과 배터리 잔량 샘플을 작업 관리자 형태의 선 그래프로 표시합니다. | ResourceLineGraph 인스턴스 | 없음 | CPU, Memory, Process CPU/Memory, Battery 표시 |
| `ResourceLineGraph.__init__` | 그래프 샘플 목록과 시리즈 색상을 초기화합니다. | None | 없음 | 최대 60개 샘플 유지 |
| `ResourceLineGraph.sizeHint` | 그래프 위젯의 권장 크기를 반환합니다. | QSize | 없음 | PyQt 레이아웃용 |
| `ResourceLineGraph.append_sample` | 수신 JSON에서 백분율 값을 추출해 그래프 샘플로 누적합니다. | None | 값 변환 오류 | 화면 갱신 호출 |
| `ResourceLineGraph._read_percent` | 중첩 JSON에서 백분율 값을 안전하게 읽습니다. | float | 값 변환 오류 | 누락 값은 0 처리 |
| `ResourceLineGraph.paintEvent` | 그래프 배경, 격자, 범례, 선을 그립니다. | None | 없음 | 샘플 2개 미만이면 대기 문구 표시 |
| `ResourceLineGraph._draw_grid` | 그래프 격자와 0~100% 축 눈금을 그립니다. | None | 없음 | QPainter 사용 |
| `ResourceLineGraph._draw_legend` | 그래프 상단에 시리즈 범례를 표시합니다. | None | 없음 | 색상별 선 의미 표시 |
| `ResourceLineGraph._draw_series` | 지정한 사용률 시리즈를 선으로 연결해 그립니다. | None | 없음 | 0~100% 범위로 클램프 |
| `EdgeNodeStatusWindow` | Edge node 상태 조회 버튼으로 열리는 그래프/표 표시 창입니다. | EdgeNodeStatusWindow 인스턴스 | 없음 | 2초 주기 자동 조회 |
| `EdgeNodeStatusWindow.__init__` | 상태 조회 창의 UI 상태와 타이머를 초기화합니다. | None | 없음 | 응답 수신 여부 보관, Windows `?` 버튼 제거 |
| `EdgeNodeStatusWindow._build_ui` | 제목, 새로고침 버튼, 그래프, 표를 구성합니다. | None | 없음 | 표는 읽기 전용 |
| `EdgeNodeStatusWindow.start_monitoring` | 창이 열릴 때 즉시 조회하고 주기 갱신을 시작합니다. | None | 요청 실패 | 타이머 시작 |
| `EdgeNodeStatusWindow.request_resource_status` | Edge node 상태 JSON 수신 worker를 시작합니다. | None | 수신 실패 신호 | 중복 수신 방지 |
| `EdgeNodeStatusWindow.handle_resource_status` | 성공 JSON을 그래프와 표에 반영하고 실패 횟수를 초기화합니다. | None | 없음 | 상태를 `연결됨`으로 표시 |
| `EdgeNodeStatusWindow.handle_resource_error` | 조회 실패를 누적하고 상태 라벨과 경고를 갱신합니다. | None | 없음 | 1~2회 실패는 `조회중`, 3회 이상은 `연결실패` |
| `EdgeNodeStatusWindow._clear_request_worker` | 완료된 요청 worker 참조를 정리합니다. | None | 없음 | 다음 요청 허용 |
| `EdgeNodeStatusWindow._update_table` | 최신 정상 JSON 값을 표로 표시합니다. | None | 없음 | 실패 시 기존 표 유지 |
| `EdgeNodeStatusWindow._set_table_rows` | 표에 표시할 행 목록을 일괄 반영합니다. | None | 없음 | 고정 행 구조 유지 |
| `EdgeNodeStatusWindow._build_waiting_rows` | 정상 응답 전이나 실패 중에도 표 형태를 유지할 대기 행을 생성합니다. | list | 없음 | 자원 지표와 UPS 전원 항목 유지 |
| `EdgeNodeStatusWindow._build_table_rows` | 자원 사용률과 UPS 전원 상태 JSON을 표 행 목록으로 변환합니다. | list | 없음 | 전체/프로세스/전원 지표 분리 |
| `EdgeNodeStatusWindow._format_percent` | 숫자 백분율을 소수점 한 자리 문자열로 변환합니다. | 문자열 | 값 변환 오류 | None은 `-` 표시 |
| `EdgeNodeStatusWindow._format_millivolt` | 밀리볼트 전압 값을 화면 표시 문자열로 변환합니다. | 문자열 | 값 변환 오류 | None은 `-` 표시 |
| `EdgeNodeStatusWindow._format_power_connection` | 외부 전원 연결 여부를 한글 상태 문자열로 변환합니다. | 문자열 | 없음 | True는 `연결됨`, False는 `미연결` |
| `EdgeNodeStatusWindow._format_power_status` | UPS 전원 상태 읽기 결과를 화면 표시 문자열로 변환합니다. | 문자열 | 없음 | 읽기 실패 원인을 표에 표시 |
| `EdgeNodeStatusWindow.closeEvent` | 창이 닫힐 때 주기 조회 타이머와 MQTT 연결을 중지합니다. | None | 없음 | 백그라운드 갱신 중단 |

## `src/ai_cctv/ai_server/ui/main_window.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `CCTVMainWindow` | AI CCTV 클라이언트의 메인 제어 창입니다. | CCTVMainWindow ???? | ??? ?? ?? ?? | ??: QMainWindow, ?? ?? |
| `CCTVMainWindow.__init__` | 메인 창 상태와 UI를 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow.init_ui` | 메인 화면의 전체 레이아웃을 구성합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow._create_header_layout` | 상단 제목과 제어 버튼 레이아웃을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._create_button` | 표준 스타일의 버튼을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._set_run_button_state` | 영상 실행 상태에 맞춰 START와 STOP 버튼을 하이라이팅합니다. | None | 없음 | 실행/정지 상태 표시 |
| `CCTVMainWindow._build_run_button_style` | 실행 상태 버튼의 활성/비활성 스타일을 생성합니다. | 문자열 | 없음 | 상태별 버튼 스타일 |
| `CCTVMainWindow._create_left_panel` | 카메라 입력 상태 패널을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._create_center_panel` | 실시간 영상과 지표 패널을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._create_right_panel` | 이벤트 타임라인과 저장 경로 패널을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow.create_metric_box` | 지표 숫자와 라벨을 담는 UI 박스를 생성합니다. | dict | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.start_video` | 영상 처리 작업자를 시작하고 신호를 연결합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.stop_video` | 영상 처리 작업자를 중지하고 카메라 상태를 갱신합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.open_settings` | 설정 창을 열고 적용된 값을 메인 창 상태에 반영합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.open_edge_status` | Edge node 상태 조회 창을 열고 모니터링 요청을 시작합니다. | None | 모니터링 창 생성 오류 | 헤더 버튼에서 호출 |
| `CCTVMainWindow._resolve_initial_video_source` | 시작 전 검증된 연결 설정에서 RTSP URL 또는 Windows 로컬 카메라 인덱스를 결정합니다. | RTSP URL 또는 정수 인덱스 | 없음 | Edge node/로컬 카메라 분기 |
| `CCTVMainWindow.update_frame` | OpenCV 프레임을 PyQt 이미지로 변환해 화면에 표시합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.show_loading_screen` | 영상 영역에 현재 준비 단계 로딩 문구를 표시합니다. | None | 없음 | VideoWorker loading_ready 신호 수신 |
| `CCTVMainWindow.show_idle_screen` | 영상 영역을 실행 전 기본 대기 화면으로 되돌립니다. | None | 없음 | STOP 또는 시작 실패 시 호출 |
| `CCTVMainWindow.update_metrics` | 영상 처리 지표를 화면에 반영합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.add_event` | 이벤트 타임라인에 새 이벤트 항목을 추가합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow.closeEvent` | 창 닫힘 이벤트에서 작업자를 정리합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `CCTVMainWindow._set_camera_status_style` | 카메라 상태 라벨의 색상을 설정합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._handle_video_start_failure` | 영상 처리 작업자 시작 실패를 화면 상태와 이벤트로 표시합니다. | None | 없음 | UI 프로세스 종료 방지 |
| `CCTVMainWindow._handle_worker_finished` | 영상 작업자가 예기치 않게 종료된 경우 UI 상태를 정리합니다. | None | 없음 | 스트림 열기 실패 후 상태 정리 |
| `CCTVMainWindow._build_storage_label` | 저장 경로 패널에 표시할 문자열을 생성합니다. | 'Storage path\nNo storage path selected.\n\nSelect a location in Settings > Storage.' | ??? ?? ?? ?? | ?? ?? |
| `CCTVMainWindow._trim_event_list` | 이벤트 타임라인의 최대 표시 개수를 제한합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `main` | 런타임 준비 상태 확인 UI와 연결 입력 UI를 순서대로 표시한 뒤 AI CCTV PyQt 애플리케이션을 실행합니다. | None | 설치 거부, 연결 검증 실패, AI 런타임 초기화 오류 | 메인 창 생성 전 필수 조건 검증 |

## `src/ai_cctv/ai_server/ui/edge_connection_dialog.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeConnectionDialog` | AI server 시작 전 Edge node 연결 설정을 입력받고 검증합니다. | EdgeConnectionDialog 객체 | 없음 | QDialog |
| `EdgeConnectionDialog.__init__` | 연결 입력 대화상자의 상태와 UI를 초기화합니다. | None | 환경 변수 포트 해석 오류 | 기본값 자동 입력 |
| `EdgeConnectionDialog._build_ui` | 연결 입력 대화상자의 전체 UI를 구성합니다. | None | PyQt 위젯 생성 오류 | 붙여넣기 영역과 필드 제공 |
| `EdgeConnectionDialog._create_button` | 대화상자에서 사용할 공통 버튼을 생성합니다. | QPushButton | 없음 | 공통 스타일 |
| `EdgeConnectionDialog.apply_startup_text` | 붙여넣은 Edge node 표준 출력값을 입력 필드에 반영합니다. | None | ValueError | 출력값 적용 버튼 |
| `EdgeConnectionDialog.validate_and_accept` | 입력된 연결값을 검증하고 성공하면 대화상자를 종료합니다. | None | 연결 검증 실패 | 성공 시 환경 변수 반영 |
| `EdgeConnectionDialog.update_input_mode` | Edge node RTSP 모드와 Windows 로컬 카메라 모드에 맞게 입력 필드를 활성화합니다. | None | 없음 | 로컬 카메라 선택 시 Edge 값 입력 비활성화 |
| `EdgeConnectionDialog._set_pending_state` | 연결 검증 진행 중 UI 상태를 표시합니다. | None | 없음 | 중복 클릭 방지 |
| `EdgeConnectionDialog._read_form_config` | 현재 입력 필드 값을 EdgeConnectionConfig로 변환합니다. | EdgeConnectionConfig 객체 | ValueError | MQTT 포트 정수 검증 |
| `EdgeConnectionDialog._populate_fields` | 연결 설정 객체의 값을 입력 필드에 표시합니다. | None | 없음 | 표준 출력 파싱 결과 반영 |

## `src/ai_cctv/ai_server/ui/runtime_readiness_dialog.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `RuntimeReadinessDialog` | AI server 실행 전 누락된 패키지와 모델을 보여주고 자동 설치 여부를 묻습니다. | RuntimeReadinessDialog 객체 | 없음 | QDialog |
| `RuntimeReadinessDialog.__init__` | 런타임 점검 보고서, 점검기, 설치기와 UI 상태를 초기화합니다. | None | 없음 | 설치 재시도 후 재점검 가능 |
| `RuntimeReadinessDialog._build_ui` | 누락 항목 설명, 점검 결과, O/X 버튼 UI를 구성합니다. | None | PyQt 위젯 생성 오류 | 설치 동의 흐름 담당 |
| `RuntimeReadinessDialog._create_button` | 런타임 준비 대화상자의 버튼을 생성합니다. | QPushButton | 없음 | 공통 버튼 스타일 |
| `RuntimeReadinessDialog.install_and_recheck` | 누락 항목을 설치한 뒤 다시 점검하고 준비 완료 시 대화상자를 닫습니다. | None | 설치 RuntimeError | O 버튼 동작 |
| `RuntimeReadinessDialog._build_report_text` | 런타임 준비 상태 보고서를 표시 문자열로 변환합니다. | 문자열 | 없음 | 상세 점검 결과 표시 |
| `ensure_runtime_readiness` | 런타임 요구사항을 점검하고 누락 시 설치 확인 대화상자를 실행합니다. | bool | 설치 실패 또는 사용자 거부 | `main_window.main`에서 호출 |

## `src/ai_cctv/ai_server/ui/settings_window.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `SettingsWindow` | AI CCTV 실행 설정을 입력받는 PyQt 대화상자입니다. | SettingsWindow ???? | ??? ?? ?? ?? | ??: QDialog, ?? ?? |
| `SettingsWindow.__init__` | 설정 창의 초기 상태를 구성합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow.init_ui` | 설정 창의 좌측 메뉴와 우측 페이지 영역을 구성합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow._create_menu_panel` | 설정 페이지 전환 메뉴 패널을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow.create_menu_button` | 설정 메뉴 버튼을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow.select_page` | 설정 페이지를 전환하고 좌측 메뉴 선택 상태를 갱신합니다. | None | 없음 | sidebar 하이라이트 갱신 |
| `SettingsWindow._update_menu_highlight` | 현재 선택된 설정 메뉴 버튼을 하이라이팅합니다. | None | 없음 | 선택 버튼 스타일 적용 |
| `SettingsWindow._build_menu_button_style` | 설정 메뉴 버튼의 선택 여부에 따른 스타일 문자열을 생성합니다. | 문자열 | 없음 | 선택/비선택 스타일 분리 |
| `SettingsWindow.create_basic_page` | 영상 입력과 AI 분석 사용 여부 설정 페이지를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow._add_input_controls` | 기본 설정 페이지에 영상 입력 컨트롤을 추가합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._add_ai_controls` | 기본 설정 페이지에 YOLO와 VLM 사용 여부 컨트롤을 추가합니다. | None | 없음 | YOLO off 시 VLM 비활성화 |
| `SettingsWindow._create_label` | 설정 폼 라벨을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._create_line_edit` | 표준 스타일의 입력 필드를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._create_basic_save_row` | 기본 설정 저장 버튼 행을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow.update_input_mode` | 선택된 입력 방식에 맞춰 입력 필드를 활성화합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow.update_ai_mode` | YOLO 사용 여부에 맞춰 VLM 옵션 활성 상태를 동기화합니다. | None | 없음 | VLM 종속 옵션 처리 |
| `SettingsWindow.save_basic_settings` | 기본 설정 값을 검증하고 대화상자 상태에 반영합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow._parse_camera_index` | 웹캠 번호 입력값을 정수로 변환합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._show_basic_error` | 기본 설정 페이지에 오류 메시지를 표시합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow.create_empty_page` | 빈 안내 페이지를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow.create_storage_page` | 저장 경로, 원본 녹화 분할, 이벤트 클립 분할 설정 페이지를 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow._add_storage_path_controls` | 저장 경로 선택 컨트롤을 추가합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._add_original_segment_controls` | 원본 녹화 분할 시간 라디오 버튼을 추가합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow._add_clip_segment_controls` | 이벤트 클립 분할 시간 라디오 버튼을 추가합니다. | None | 없음 | 10초/30초/전체 이벤트 |
| `SettingsWindow._create_storage_save_row` | 저장 설정 저장 버튼 행을 생성합니다. | ?? ?? | ??? ?? ?? ?? | ?? ?? |
| `SettingsWindow.select_storage_path` | 사용자에게 저장 루트 경로를 선택받고 표준 폴더를 생성합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `SettingsWindow.save_storage_settings` | 저장소 설정 값을 검증하고 대화상자를 완료합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/edge_node/failover.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `EdgeFailoverDecision` | 네트워크 상태에 따른 Edge node 동작 결정을 표현합니다. | EdgeFailoverDecision ???? | ??? ?? ?? ?? | ?? ?? ?? |
| `EdgeNetworkFailoverPolicy` | Edge node 네트워크 장애 대응 동작을 결정합니다. | EdgeNetworkFailoverPolicy ???? | ??? ?? ?? ?? | ?? ?? |
| `EdgeNetworkFailoverPolicy.__init__` | 장애 대응 정책을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `EdgeNetworkFailoverPolicy.decide_for_network` | 네트워크 상태에 맞는 Edge node 동작을 결정합니다. | ?? ?? ?? ?? | ??? ?? ?? ?? | ?? ?? ?? |

## `src/ai_cctv/edge_node/backup_recovery_server.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `BackupRecoveryArchive` | 복구 요청으로 생성된 임시 ZIP 파일 정보를 표현합니다. | BackupRecoveryArchive 객체 | 없음 | dataclass |
| `BackupSegmentFinder` | 로컬 백업 폴더에서 시간 구간과 겹치는 TS 세그먼트를 찾습니다. | BackupSegmentFinder 객체 | 없음 | 파일 mtime 기준 |
| `BackupSegmentFinder.__init__` | 백업 탐색 위치와 세그먼트 길이를 초기화합니다. | None | 없음 | 기본 10초 |
| `BackupSegmentFinder.find_segments` | 요청 시간대와 겹치는 TS 백업 파일 목록을 반환합니다. | list | FileNotFoundError | `.ts` 파일만 탐색 |
| `BackupSegmentFinder._ranges_overlap` | 두 시간 구간이 겹치는지 확인합니다. | bool | 없음 | 내부 함수 |
| `BackupRecoveryService` | 복구 요청 시간을 검증하고 대상 백업 파일을 ZIP으로 묶습니다. | BackupRecoveryService 객체 | 없음 | HTTP handler와 분리 |
| `BackupRecoveryService.__init__` | 백업 세그먼트 탐색 의존 객체를 저장합니다. | None | 없음 | 테스트 가능 |
| `BackupRecoveryService.recover` | 요청 구간에 해당하는 백업 세그먼트 ZIP을 생성합니다. | BackupRecoveryArchive | ValueError, FileNotFoundError | ISO 8601 시간 사용 |
| `BackupRecoveryService._parse_iso_datetime` | ISO 8601 시각 문자열을 datetime으로 변환합니다. | datetime | ValueError | 입력 검증 |
| `BackupRecoveryService._build_archive` | 대상 TS 파일 목록을 임시 ZIP 파일로 묶습니다. | BackupRecoveryArchive | zip 생성 오류 | 전송 후 삭제 대상 |
| `remove_temp_file` | 파일 전송 완료 후 임시 ZIP 파일을 삭제합니다. | None | 삭제 오류 로그 | FastAPI BackgroundTasks에서 호출 |
| `create_backup_recovery_app` | BackupRecoveryService를 사용하는 FastAPI 앱을 생성합니다. | FastAPI app | ImportError | `/recover` endpoint 등록 |
| `create_backup_recovery_app.recover_backups` | 요청 시간대와 겹치는 백업 TS 파일을 ZIP으로 반환합니다. | FileResponse | HTTPException | start/end query 사용 |
| `build_backup_recovery_app` | 환경 설정을 반영한 FastAPI 백업 복구 앱을 생성합니다. | FastAPI app | ImportError | backup_dir 주입 |
| `main` | 환경 변수 기준으로 Edge node 백업 복구 FastAPI 서버를 실행합니다. | 반환 없음 | uvicorn 실행 오류 | `ai-cctv-edge-backup-recovery` 진입점 |

## `src/ai_cctv/edge_node/main.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `build_default_edge_stream_command` | 기본 Edge node 송출 명령 문자열을 생성합니다. | 문자열 | 런타임 구성 오류 | 명령 확인용 보조 함수 |
| `build_argument_parser` | Edge node 실행 옵션 파서를 생성합니다. | ArgumentParser | 없음 | `--print-command` 옵션 제공 |
| `main` | Edge node 런타임을 실행합니다. | None | 하위 프로세스 실행 오류 | 기본 동작은 실제 송출 실행 |

## `src/ai_cctv/edge_node/local_backup.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `LocalBackupConfig` | Edge node 로컬 백업 저장 정책을 표현합니다. | LocalBackupConfig 객체 | 없음 | dataclass |
| `LocalBackupConfig.ensure_directory` | 백업 저장 폴더를 생성하고 경로를 반환합니다. | Path | 권한/경로 오류 | `mkdir -p` 대체 |
| `LocalBackupConfig.build_segment_pattern` | splitmuxsink 백업 세그먼트 파일명 패턴을 생성합니다. | 문자열 | 없음 | `%05d.ts` 패턴 사용 |
| `LocalBackupConfig.segment_duration_nanoseconds` | 백업 세그먼트 길이를 나노초로 변환합니다. | 정수 | 없음 | 기본 10초 |

## `src/ai_cctv/edge_node/mediamtx.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `MediaMtxConfig` | MediaMTX 설치와 실행 경로 설정을 표현합니다. | MediaMtxConfig 객체 | 없음 | dataclass |
| `MediaMtxConfig.work_path` | MediaMTX 작업 폴더 경로를 반환합니다. | Path | 없음 | property |
| `MediaMtxConfig.binary_path` | MediaMTX 실행 파일 경로를 반환합니다. | Path | 없음 | property |
| `MediaMtxConfig.config_path` | MediaMTX 설정 파일 경로를 반환합니다. | Path | 없음 | property |
| `MediaMtxConfig.log_path` | MediaMTX 로그 파일 경로를 반환합니다. | Path | 없음 | property |
| `MediaMtxReleaseResolver` | Raspberry Pi 아키텍처에 맞는 MediaMTX 다운로드 주소를 결정합니다. | MediaMtxReleaseResolver 객체 | 없음 | ARM 전용 |
| `MediaMtxReleaseResolver.__init__` | 릴리스 주소 결정에 사용할 설정을 초기화합니다. | None | 없음 | 설정 주입 가능 |
| `MediaMtxReleaseResolver.resolve_download_url` | 현재 장비 아키텍처에 맞는 MediaMTX 압축 파일 URL을 반환합니다. | URL 문자열 | ValueError | aarch64, arm 계열 지원 |
| `MediaMtxInstaller` | MediaMTX 실행 파일과 설정 파일의 존재를 보장합니다. | MediaMtxInstaller 객체 | 없음 | 다운로드 책임 |
| `MediaMtxInstaller.__init__` | MediaMTX 설치 준비 객체를 초기화합니다. | None | 없음 | resolver 주입 가능 |
| `MediaMtxInstaller.is_installed` | MediaMTX 실행 파일과 설정 파일 존재 여부를 확인합니다. | bool | 없음 | 네트워크 사용 없음 |
| `MediaMtxInstaller.ensure_installed` | MediaMTX가 없으면 다운로드하고 압축을 해제합니다. | Path | 네트워크/압축 오류 | GitHub 릴리스 사용 |
| `MediaMtxInstaller._extract_required_files` | 압축 파일에서 실행 파일과 설정 파일만 추출합니다. | None | tar 오류 | 내부 함수 |
| `MediaMtxInstaller._make_binary_executable` | MediaMTX 실행 파일에 실행 권한을 부여합니다. | None | 권한 오류 | Linux에서만 동작 |
| `MediaMtxProcessManager` | MediaMTX 프로세스의 실행 상태를 관리합니다. | MediaMtxProcessManager 객체 | 없음 | Popen 기반 |
| `MediaMtxProcessManager.__init__` | MediaMTX 프로세스 관리 상태를 초기화합니다. | None | 없음 | 로그 핸들 보관 |
| `MediaMtxProcessManager.is_running` | MediaMTX 프로세스가 이미 실행 중인지 확인합니다. | bool | 없음 | pgrep 사용 가능 |
| `MediaMtxProcessManager.start` | MediaMTX를 백그라운드 프로세스로 실행합니다. | Popen 또는 None | 실행 파일 오류 | 이미 실행 중이면 None |
| `MediaMtxProcessManager.stop` | 이 관리자가 실행한 MediaMTX 프로세스를 종료합니다. | None | 프로세스 종료 오류 | 로그 핸들 정리 |

## `src/ai_cctv/edge_node/runtime.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeNodeRuntime` | Edge node 송출 프로세스의 실행 흐름을 조율합니다. | EdgeNodeRuntime 객체 | 없음 | 의존 객체 주입 가능 |
| `EdgeNodeRuntime.__init__` | Edge node 런타임 의존 객체를 초기화합니다. | None | 없음 | 기본 MediaMTX 설정 생성 |
| `EdgeNodeRuntime.build_command_args` | 현재 런타임 설정으로 GStreamer 실행 인자를 생성합니다. | list | 없음 | 테스트 가능 |
| `EdgeNodeRuntime.run` | 시작 연결 정보를 출력한 뒤 MediaMTX와 GStreamer를 순서대로 실행하고 종료 시 정리합니다. | 종료 코드 | 하위 프로세스 오류 | 실제 실행 진입점 |
| `EdgeNodeRuntime.stop` | GStreamer와 MediaMTX 프로세스를 종료합니다. | None | 프로세스 종료 오류 | finally에서 호출 |
| `EdgeNodeRuntime._install_signal_handlers` | 운영체제 종료 신호를 정리 동작에 연결합니다. | None | signal 등록 오류 | 내부 함수 |
| `EdgeNodeRuntime._handle_stop_signal` | 종료 신호를 받으면 하위 프로세스를 정리합니다. | None | SystemExit | 내부 함수 |
| `build_default_edge_runtime` | 기본 설정 Edge node 런타임을 생성합니다. | EdgeNodeRuntime 객체 | 없음 | main.py에서 사용 |

## `src/ai_cctv/edge_node/startup_info.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeConnectionInfo` | AI server가 Edge node에 접속하기 위해 필요한 RTSP, MQTT, 백업 복구 주소를 보관합니다. | EdgeConnectionInfo 객체 | 없음 | dataclass |
| `EdgeConnectionInfo.to_terminal_text` | 운영자가 복사할 수 있는 표준 연결 정보 블록을 생성합니다. | 문자열 | 없음 | PowerShell 설정 예시 포함 |
| `build_edge_connection_info` | 환경 변수와 호출 인자를 합쳐 Edge node 연결 정보를 생성합니다. | EdgeConnectionInfo 객체 | 잘못된 정수 환경 변수 | MQTT, RTSP, 백업 복구 설정 통합 |
| `print_edge_connection_info` | Edge node 연결 정보를 표준 출력 또는 지정 스트림에 즉시 출력합니다. | EdgeConnectionInfo 객체 | 출력 스트림 오류 | flush=True 사용 |
| `resolve_edge_host` | AI server가 접속할 Edge node 호스트 값을 결정합니다. | IP 또는 호스트 문자열 | 없음 | 명시값, SSH, 인터페이스, UDP 라우팅 순서 |
| `_build_rtsp_url` | MediaMTX 기본 RTSP 주소를 생성합니다. | RTSP URL 문자열 | 잘못된 포트 환경 변수 | 내부 함수 |
| `_resolve_int` | 명시값 또는 환경 변수를 정수로 해석합니다. | int | ValueError | 내부 함수 |
| `_read_ssh_server_host` | SSH_CONNECTION 환경 변수에서 서버 측 IP를 읽습니다. | IP 문자열 또는 None | 없음 | SSH 접속 실행에 우선 사용 |
| `_read_interface_host` | 지정한 Linux 네트워크 인터페이스의 IPv4 주소를 조회합니다. | IP 문자열 또는 None | ip 명령 실행 오류는 None 처리 | AI_CCTV_EDGE_INTERFACE 지원 |
| `_detect_host_by_udp_probe` | UDP 라우팅 결과로 로컬 IPv4 주소를 추정합니다. | IP 문자열 또는 None | 소켓 오류는 None 처리 | 패킷 전송 없이 라우팅만 확인 |
| `_read_hostname_host` | 호스트 이름 해석 결과에서 외부 접속 가능한 IPv4 주소를 찾습니다. | IP 문자열 또는 None | 이름 해석 오류는 None 처리 | 마지막 자동 감지 후보 |
| `_is_loopback_host` | 호스트 값이 loopback 주소인지 판단합니다. | bool | 없음 | localhost, 127.*, ::1 처리 |

## `src/ai_cctv/edge_node/streaming.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `EdgeStreamConfig` | Edge node 영상 송출 파이프라인 설정을 표현합니다. | EdgeStreamConfig 객체 | 없음 | dataclass |
| `MediaMtxGStreamerCommandBuilder` | GStreamer 기반 백업과 MediaMTX 송출 명령을 생성합니다. | MediaMtxGStreamerCommandBuilder 객체 | 없음 | 명령 생성 전용 |
| `MediaMtxGStreamerCommandBuilder.__init__` | 송출 명령 생성 설정을 초기화합니다. | None | 없음 | 백업 설정 주입 가능 |
| `MediaMtxGStreamerCommandBuilder.build_command_args` | GStreamer 백업 및 송출 명령 인자 목록을 생성합니다. | list | 없음 | tee, splitmuxsink, rtmpsink 포함 |
| `MediaMtxGStreamerCommandBuilder.build_shell_command_text` | 운영자가 확인할 수 있는 GStreamer 명령 문자열을 생성합니다. | 문자열 | 없음 | `--print-command`에서 사용 |

## `test_mqtt.py`

| 이름 | 기능 | 정상값 | 에러값 | 기타 특징 |
|---|---|---|---|---|
| `MockResourceState` | UI 검증용 모의 자원 사용률 상태를 생성하고 보관합니다. | MockResourceState 인스턴스 | 없음 | 실제 Edge node 없이 사용 |
| `MockResourceState.__init__` | publisher 시작 시각, 응답용 PID, 정상 발행 횟수 제한을 초기화합니다. | None | 없음 | PID 기본값은 현재 프로세스 |
| `MockResourceState.can_publish` | 정상 JSON 메시지를 더 발행할 수 있는지 판단합니다. | bool | 없음 | 기본 10회까지 True |
| `MockResourceState.build_message` | MQTT로 발행할 모의 CPU, memory, process, power JSON을 생성합니다. | dict | 없음 | 발행마다 값이 변하고 성공 횟수 증가 |
| `MockResourceState._wave` | 사인파 기반의 0~100 범위 백분율 값을 계산합니다. | float | 없음 | 그래프 변화 확인용 |
| `MockMqttResourcePublisher` | 모의 Edge node 상태를 MQTT topic으로 발행합니다. | MockMqttResourcePublisher 인스턴스 | 없음 | 실제 Edge node 없이 사용 |
| `MockMqttResourcePublisher.__init__` | broker 접속 정보와 모의 상태 생성기를 초기화합니다. | None | ImportError | paho-mqtt 필요 |
| `MockMqttResourcePublisher.run` | MQTT broker에 연결한 뒤 모의 상태 메시지를 발행합니다. | 반환 없음 | MQTT 연결/발행 오류 | 10회 이후 발행 중단 |
| `build_argument_parser` | 모의 publisher 실행용 명령행 인자 파서를 생성합니다. | ArgumentParser | 없음 | `--host`, `--port`, `--topic`, `--interval` 지원 |
| `_create_mqtt_client` | paho-mqtt 버전에 맞는 MQTT 클라이언트를 생성합니다. | MQTT Client | ImportError | Callback API v1/v2 호환 |
| `main` | 명령행 인자를 읽고 모의 MQTT publisher를 시작합니다. | None | MQTT 실행 오류 | 임시 테스트 진입점 |

## `tests/test_project_structure.py`

| ?? | ?? | ??? | ??? | ?? ?? |
|---|---|---|---|---|
| `FakeSmbus` | UPS Plus 전원 리더 테스트용 가짜 SMBus입니다. | FakeSmbus 인스턴스 | 없음 | 하드웨어 없이 레지스터 값을 주입 |
| `FakeSmbus.__init__` | 가짜 레지스터 저장소와 close 호출 여부를 초기화합니다. | None | 없음 | 테스트 전용 |
| `FakeSmbus.read_byte_data` | 지정한 레지스터의 가짜 바이트 값을 반환합니다. | int | KeyError | 실제 SMBus 메서드 형태 모방 |
| `FakeSmbus.close` | 가짜 SMBus가 닫혔음을 기록합니다. | None | 없음 | 리더의 close 처리 검증 |
| `FakeUpsPlusPowerReader` | 가짜 SMBus를 주입받는 UPS Plus 전원 리더입니다. | FakeUpsPlusPowerReader 인스턴스 | 없음 | `UpsPlusPowerReader` 상속 |
| `FakeUpsPlusPowerReader.__init__` | 가짜 SMBus를 저장하고 기본 UPS Plus 리더 설정을 초기화합니다. | None | 없음 | 테스트 전용 |
| `FakeUpsPlusPowerReader._open_bus` | 테스트용 가짜 SMBus를 반환합니다. | FakeSmbus 인스턴스 | 없음 | 실제 I2C 접근 없음 |
| `FailingUpsPlusPowerReader` | I2C 열기 실패를 재현하는 UPS Plus 전원 리더입니다. | FailingUpsPlusPowerReader 인스턴스 | 없음 | 실패 스냅샷 검증용 |
| `FailingUpsPlusPowerReader._open_bus` | I2C 버스 열기 실패를 발생시킵니다. | 반환 없음 | RuntimeError | 테스트 전용 |
| `MemoryNotificationChannel` | 테스트용 메모리 알림 채널입니다. | MemoryNotificationChannel ???? | ??? ?? ?? ?? | ??: NotificationChannel, ?? ?? |
| `MemoryNotificationChannel.__init__` | 전송 메시지 저장 목록을 초기화합니다. | None | ??? ?? ?? ?? | ?? ?? |
| `MemoryNotificationChannel.send` | 전송된 알림 메시지를 메모리에 저장합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest` | 문서 기준 구조 보강 모듈을 검증합니다. | ProjectStructureTest ???? | ??? ?? ?? ?? | ??: TestCase |
| `ProjectStructureTest.test_object_appearance_rule_emits_once_per_track` | 동일 추적 ID에 대한 객체 등장 이벤트가 한 번만 생성되는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_dwell_time_rule_emits_after_threshold` | 체류 시간 초과 규칙이 임계 시간 이후 이벤트를 생성하는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_notification_dispatcher_sends_anomaly_message` | 이상 상황 이벤트가 알림 메시지로 변환되어 채널로 전달되는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_edge_failover_policy_matches_project_document` | 네트워크 장애 시 로컬 저장과 최소 알림을 선택하는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_gstreamer_mediamtx_command_streams_and_records` | GStreamer 명령이 MediaMTX 송출과 로컬 백업을 함께 수행하는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_mediamtx_release_resolver_selects_raspberry_pi_package` | Raspberry Pi 아키텍처에 맞는 MediaMTX 패키지 URL을 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_ups_plus_power_reader_reads_battery_and_external_power` | UPS Plus 레지스터에서 배터리 잔량과 외부 전원 상태를 해석하는지 검증합니다. | None | AssertionError | 가짜 SMBus 사용 |
| `ProjectStructureTest.test_ups_plus_power_reader_reports_unavailable_on_i2c_error` | UPS Plus I2C 접근 실패가 사용 불가 스냅샷으로 변환되는지 검증합니다. | None | AssertionError | 실패 리더 사용 |
| `ProjectStructureTest.test_console_scripts_are_split_by_deployment_bundle` | Edge node와 AI server 실행 진입점이 분리되어 있는지 검증합니다. | None | ??? ?? ?? ?? | ?? ?? ?? |
| `ProjectStructureTest.test_rtsp_source_detection` | RTSP URL과 일반 카메라 번호를 구분하는지 검증합니다. | None | AssertionError | RTSP receiver 보조 함수 검증 |
| `ProjectStructureTest.test_rtsp_receiver_watchdog_releases_active_capture` | RTSP watchdog이 활성 VideoCapture를 강제 해제하는지 검증합니다. | None | AssertionError | Mock capture 사용 |
| `ProjectStructureTest.test_network_recovery_manager_skips_when_url_missing` | 복구 서버 URL이 없을 때 네트워크 요청 없이 실패 사유를 반환하는지 검증합니다. | None | AssertionError | 외부 네트워크 불필요 |
| `ProjectStructureTest.test_backup_recovery_service_archives_overlapping_segments` | 요청 시간대와 겹치는 TS 백업 파일을 ZIP으로 묶는지 검증합니다. | None | AssertionError | 임시 파일 기반 |
| `ProjectStructureTest.test_resource_monitor_mqtt_defaults_match_between_nodes` | Edge node와 AI server의 기본 MQTT 접속 설정이 일치하는지 검증합니다. | None | AssertionError | 상태 topic 불일치 방지 |
| `ProjectStructureTest.test_edge_connection_info_prints_ai_server_settings` | Edge node 시작 정보가 AI server 설정값을 포함하는지 검증합니다. | None | AssertionError | SSH 실행 안내 출력 회귀 방지 |
| `ProjectStructureTest.test_ai_server_parses_edge_startup_connection_text` | AI server 시작 UI가 Edge node 표준 출력값을 설정 객체로 해석하는지 검증합니다. | None | AssertionError | 연결 UI 붙여넣기 회귀 방지 |
| `ProjectStructureTest.test_ai_server_os_guard_accepts_only_windows` | AI server OS guard가 Windows만 허용하고 Linux를 종료 처리하는지 검증합니다. | None | AssertionError | OS 분기 회귀 방지 |
| `ProjectStructureTest.test_pyqt5_bootstrap_installs_only_when_user_accepts` | PyQt5 bootstrap이 사용자가 동의한 경우에만 설치 함수를 호출하는지 검증합니다. | None | AssertionError | GUI 점검 창 진입 전 최소 의존성 검증 |
| `ProjectStructureTest.test_local_camera_connection_config_uses_camera_index` | 로컬 카메라 모드에서 영상 소스가 카메라 인덱스로 반환되는지 검증합니다. | None | AssertionError | Edge node 없는 테스트 경로 보장 |
| `ProjectStructureTest.test_runtime_readiness_report_finds_missing_required_items` | 런타임 준비 보고서가 누락된 필수 요구사항을 찾는지 검증합니다. | None | AssertionError | 자동 설치 대상 산출 검증 |
