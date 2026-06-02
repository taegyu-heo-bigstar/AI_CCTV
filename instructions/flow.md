# AI CCTV Flow

이 문서는 Edge node와 AI server 두 실행 묶음을 기준으로 프로젝트 구조와 실행 흐름을 설명합니다.

## Project Layout

```text
AI_CCTV/
|-- main.py                         # 로컬 개발용 AI server 실행 진입점
|-- pyproject.toml                  # 패키지 메타데이터와 실행 명령
|-- requirements/                   # 배포 환경별 requirements 파일
|-- instructions/                   # 구조, 흐름, 변경 설명 문서
|-- legacy/                         # 과거 샘플, 학습 자료, 임시 archive 자료
|-- src/
|   `-- ai_cctv/
|       |-- edge_node/              # Raspberry Pi Edge node 배포 단위
|       |   |-- main.py             # Edge node 실행 진입점
|       |   |-- os_guard.py         # Linux/Debian 계열 실행 환경 확인
|       |   |-- runtime.py          # MediaMTX 준비와 GStreamer 실행 조율
|       |   |-- startup_info.py     # SSH 실행 직후 AI server 설정용 연결 정보 출력
|       |   |-- mediamtx.py         # MediaMTX 다운로드, 설치 확인, 프로세스 관리
|       |   |-- streaming.py        # GStreamer 송출/로컬 백업 파이프라인 생성
|       |   |-- local_backup.py     # 로컬 백업 세그먼트 파일명 정책
|       |   |-- support_processes.py # MQTT broker, MQTT publisher, 복구 API 보조 프로세스 관리
|       |   |-- backup_recovery_server.py # 누락 구간 로컬 백업 ZIP 제공
|       |   |-- monitoring/         # Edge node MQTT broker와 자원/전원 모니터링 publisher
|       |   `-- failover.py         # 네트워크 장애 대응 정책
|       `-- ai_server/              # Windows AI server 배포 단위
|           |-- server_run.py       # AI server 실행 진입점
|           |-- stream_receiver.py  # MediaMTX RTSP 수신 수동 점검 도구
|           |-- connection/         # 시작 전 Edge node 연결 설정과 검증
|           |-- runtime/            # Windows OS guard, 패키지/모델 준비 상태 점검과 자동 설치
|           |-- ui/                 # PyQt 화면, 설정창, 이벤트 표시
|           |-- analysis/           # 영상 입력, RTSP 재연결, 추적, VLM, 이상 상황 판정
|           |-- recovery/           # RTSP 단절 구간 백업 복구 요청
|           |-- storage/            # 저장 경로, 원본 녹화, 이벤트 클립 관리
|           |-- alerts/             # Discord 알림 메시지, 디스패처, 챗봇 전송
|           |-- monitoring/         # Edge node 자원 모니터링 MQTT 구독 클라이언트
|           `-- common/             # 서버 노드 내부 공통 값 객체 재노출
`-- tester/                         # 테스트 도구, pseudo edge, 회귀 테스트, 테스트 문서
    |-- tests/                      # 구조와 도메인 경계 단위 테스트
    |-- tools/                      # 수동 검증 도구
    `-- pseudo_edge_node/           # Windows 테스트용 Edge 유사 실행체
```

## Deployment Bundles

| 실행 묶음 | 설치 extras | console script | 주요 책임 |
|---|---|---|---|
| Edge node | `ai-cctv[edge-node]` | `ai-cctv-edge` | 카메라 송출, MediaMTX 실행, 로컬 백업, 내장 MQTT broker 실행, FastAPI 백업 복구 ZIP 제공, MQTT 자원/전원 상태 발행, 네트워크 장애 대응 정책 |
| AI server | `ai-cctv[ai-server]` | `ai-cctv-ai-server` 또는 `ai-cctv` | RTSP 수신/재연결, OpenCV/YOLO 분석, MQTT 상태 구독, 이상 상황 판정, Discord 알림, GUI, requests 기반 누락 구간 복구 요청 |

## System Flow

```mermaid
flowchart LR
    Camera["Camera Module"] --> Pi["Raspberry Pi 4B"]
    Pi --> EdgeMain["ai_cctv/edge_node/main.py"]
    EdgeMain --> EdgeOsGuard["ensure_supported_edge_os"]
    EdgeOsGuard --> EdgeRuntime["EdgeNodeRuntime"]
    EdgeRuntime --> StartupInfo["EdgeConnectionInfo startup output"]
    EdgeRuntime --> SupportProcessManager["EdgeSupportProcessManager"]
    Pi --> UpsPlus["52Pi EP-0136 UPS Plus"]
    EdgeRuntime --> MediaMtxManager["MediaMtxInstaller / MediaMtxProcessManager"]
    EdgeRuntime --> BackupConfig["LocalBackupConfig"]
    EdgeRuntime --> StreamBuilder["MediaMtxGStreamerCommandBuilder"]
    SupportProcessManager --> EdgeMqttBroker["edge_node/monitoring/mqtt_broker.py"]
    SupportProcessManager --> MonitorPublisher["edge_node/monitoring/resource_monitor_publisher.py"]
    SupportProcessManager --> BackupRecoveryServer["FastAPI backup_recovery_server.py"]
    Pi --> Failover["EdgeNetworkFailoverPolicy"]
    StreamBuilder --> BackupFiles["10초 단위 로컬 TS 백업"]
    BackupRecoveryServer --> BackupFiles
    StreamBuilder --> MediaMTX["로컬 MediaMTX RTMP publish"]
    MediaMTX --> RTSP["RTSP Stream"]
    EdgeMqttBroker --> MQTTBroker["Edge node MQTT Broker"]
    MonitorPublisher --> MQTTBroker
    RTSP --> ServerRun["ai_cctv/ai_server/server_run.py"]
    ServerRun --> OsGuard["ensure_windows_os"]
    ServerRun --> PyQtBootstrap["ensure_pyqt5_available"]
    ServerRun --> EdgeConnectionDialog["ui/edge_connection_dialog.py"]
    EdgeConnectionDialog --> EdgeConnectionValidator["EdgeConnectionValidator"]
    EdgeConnectionValidator --> RTSP
    EdgeConnectionValidator --> LocalCamera["Windows local camera"]
    EdgeConnectionValidator --> MQTTBroker
    EdgeConnectionValidator --> BackupRecoveryServer
    EdgeConnectionDialog --> RuntimeReadiness["RuntimeReadinessDialog"]
    RuntimeReadiness --> RuntimeChecker["RuntimeEnvironmentChecker"]
    RuntimeReadiness --> RuntimeInstaller["RuntimeInstaller"]
    RuntimeReadiness --> MainWindow["ai_server/ui/main_window.py"]
    MainWindow --> EdgeStatusWindow["ui/edge_status_window.py"]
    EdgeStatusWindow --> MonitorClient["ResourceMonitorClient"]
    MonitorClient --> MQTTBroker
    MonitorPublisher --> ResourceCollector["ResourceUsageCollector"]
    ResourceCollector --> PowerProvider["CachedPowerStatusProvider"]
    PowerProvider --> PowerReader["UpsPlusPowerReader"]
    PowerReader --> UpsPlus
    ResourceCollector --> ResourceJson["CPU/Memory/Process/Power JSON"]
    MainWindow --> SettingsWindow["ui/settings_window.py"]
    SettingsWindow --> RuntimeOptions["YOLO/VLM on-off, 클립 길이, 저장 경로"]
    MainWindow --> VideoWorker["ai_server/analysis/video_worker.py"]
    VideoWorker --> VideoStream["VideoStream"]
    VideoStream --> RtspReceiver["RtspFrameReceiver"]
    VideoStream --> RecoveryManager["NetworkRecoveryManager"]
    RecoveryManager -- "requests GET /recover" --> BackupRecoveryServer
    VideoWorker --> Tracker["PersonTracker"]
    Tracker --> Processor["PersonFrameProcessor"]
    Tracker --> RuleEngine["AnomalyRuleEngine"]
    VideoWorker --> VLMWorker["VLMWorker ready/failed 대기"]
    VideoWorker --> Storage["storage/recording_manager.py"]
    VideoWorker --> ClipManager["storage/clip_manager.py"]
    ClipManager --> EventClips["event_clips/person별 MP4와 trajectory.jpg"]
    RuleEngine --> Event["AnomalyEvent"]
    Event --> Dispatcher["NotificationDispatcher"]
    Dispatcher --> Discord["alerts/chat_bot"]
    Processor --> GUI["CCTVMainWindow"]
```

## Responsibility Boundaries

```mermaid
classDiagram
    class MediaMtxGStreamerCommandBuilder {
        +build_command_args()
        +build_shell_command_text()
    }

    class EdgeNodeRuntime {
        +build_command_args()
        +run()
        +stop()
    }

    class EdgeSupportProcessManager {
        +start_backup_recovery(backup_dir)
        +start_resource_monitor(monitored_process_id)
        +stop()
    }

    class EdgeOsGuard {
        +ensure_supported_edge_os()
        +is_supported_edge_os()
    }

    class EdgeConnectionInfo {
        +to_terminal_text()
    }

    class MediaMtxInstaller {
        +is_installed()
        +ensure_installed()
    }

    class MediaMtxProcessManager {
        +is_running()
        +start()
        +stop()
    }

    class LocalBackupConfig {
        +ensure_directory()
        +build_segment_pattern(started_at)
        +segment_duration_nanoseconds()
    }

    class BackupSegmentFinder {
        +find_segments(start_time, end_time)
    }

    class BackupRecoveryService {
        +recover(start_text, end_text)
    }

    class EdgeNetworkFailoverPolicy {
        +decide_for_network(network_available)
    }

    class CCTVMainWindow {
        +start_video()
        +stop_video()
        +open_edge_status()
        +show_loading_screen(message)
        +show_idle_screen()
        +add_event(event)
    }

    class EdgeConnectionDialog {
        +apply_startup_text()
        +validate_and_accept()
        +update_input_mode()
    }

    class EdgeConnectionValidator {
        +validate(config)
    }

    class EdgeConnectionConfig {
        +from_environment()
        +apply_environment()
        +video_source()
    }

    class RuntimeEnvironmentChecker {
        +check()
    }

    class PyQtBootstrap {
        +ensure_pyqt5_available()
    }

    class RuntimeReadinessDialog {
        +install_and_recheck()
    }

    class RuntimeInstaller {
        +install_missing(missing_results)
    }

    class SettingsWindow {
        +update_ai_mode()
        +save_basic_settings()
        +save_storage_settings()
    }

    class VideoWorker {
        +run()
        +stop()
        -_disable_ai_pipeline(message)
        -_record_person_clip(person, frame)
        -_emit_stream_wait_status()
        -_emit_recovery_result_if_needed()
        -_create_default_notification_dispatcher()
        -_cleanup()
    }

    class RtspFrameReceiver {
        +start()
        +read_new_frame(last_sequence)
        +stop()
        -_watchdog_loop()
        -_release_active_capture(reason)
    }

    class NetworkRecoveryManager {
        +record_failure(failed_time)
        +record_recovery(recovered_time)
        +request_recovery(payload)
    }

    class VLMWorker {
        +is_ready()
        +has_failed()
        +wait_until_ready(timeout)
        +add_task(person_id, crop_path)
        -_emit_result_event(person_id, result)
    }

    class ClipManager {
        +update_person(person_id, frame, bbox, crop_path)
        +finish_person(person_id)
        +finish_all()
    }

    class AnomalyRuleEngine {
        +evaluate_detections(detections, evaluated_at)
    }

    class NotificationDispatcher {
        +dispatch_anomaly_event(event)
        +dispatch(message)
    }

    class ResourceUsageCollector {
        +collect()
        -_get_process()
    }

    class MqttResourceMonitorPublisher {
        +publish_once()
        +run_forever()
        +stop()
    }

    class MqttResourceMonitorConfig {
        +from_environment()
    }

    class CachedPowerStatusProvider {
        +get_snapshot()
        -_is_cache_fresh(now)
    }

    class UpsPlusPowerReader {
        +read_snapshot()
        -_open_bus()
        -_read_percent(bus)
        -_read_word(bus, low_register, high_register)
        -_read_byte(bus, register_address)
    }

    class PowerStatusSnapshot {
        +to_dict()
        +unavailable(error)
    }

    class ResourceMonitorClient {
        +start()
        +request_resource_usage()
        +stop()
    }

    class EdgeNodeStatusWindow {
        +start_monitoring()
        +request_resource_status()
        +handle_resource_status(resource_usage)
        +handle_resource_error(error_message)
    }

    class ResourceLineGraph {
        +append_sample(resource_usage)
    }

    EdgeOsGuard --> EdgeNodeRuntime
    EdgeNodeRuntime --> MediaMtxInstaller
    EdgeNodeRuntime --> MediaMtxProcessManager
    EdgeNodeRuntime --> LocalBackupConfig
    EdgeNodeRuntime --> MediaMtxGStreamerCommandBuilder
    EdgeNodeRuntime --> EdgeConnectionInfo
    EdgeNodeRuntime --> EdgeSupportProcessManager
    EdgeNodeRuntime --> EdgeNetworkFailoverPolicy
    BackupRecoveryService --> BackupSegmentFinder
    EdgeConnectionDialog --> EdgeConnectionValidator
    EdgeConnectionDialog --> EdgeConnectionConfig
    EdgeConnectionValidator --> EdgeConnectionConfig
    RuntimeReadinessDialog --> RuntimeEnvironmentChecker
    RuntimeReadinessDialog --> RuntimeInstaller
    CCTVMainWindow --> SettingsWindow
    CCTVMainWindow --> VideoWorker
    CCTVMainWindow --> EdgeNodeStatusWindow
    EdgeNodeStatusWindow --> ResourceMonitorClient
    EdgeNodeStatusWindow --> ResourceLineGraph
    VideoWorker --> AnomalyRuleEngine
    VideoWorker --> NotificationDispatcher
    VideoWorker --> ClipManager
    VideoWorker --> VLMWorker
    VideoWorker --> RtspFrameReceiver
    VideoWorker --> NetworkRecoveryManager
    MqttResourceMonitorPublisher --> ResourceUsageCollector
    MqttResourceMonitorPublisher --> MqttResourceMonitorConfig
    ResourceUsageCollector --> CachedPowerStatusProvider
    CachedPowerStatusProvider --> UpsPlusPowerReader
    UpsPlusPowerReader --> PowerStatusSnapshot
```

## Execution

```bash
pip install -e ".[edge-node]"
ai-cctv-edge
```

기본 `ai-cctv-edge`는 RTSP 송출과 함께 내장 MQTT broker, MQTT 상태 발행, 백업 복구 API를 보조 프로세스로 실행합니다. 송출 명령만 확인하려면 `ai-cctv-edge --print-command`, RTSP 단독 점검은 `ai-cctv-edge --no-support-services`를 사용합니다.

```bash
pip install -e ".[ai-server]"
ai-cctv-ai-server
```

MQTT 상태 발행을 단독 점검하려면 Edge node에서 `ai-cctv-edge-mqtt-broker`, `ai-cctv-edge-monitor`를 별도 터미널로 실행하고 AI server에서 `python -m ai_cctv.ai_server.monitoring.resource_monitor_client`를 실행할 수 있습니다.

네트워크 단절 구간 복구 서버 실행 예시는 다음과 같습니다.

```bash
ai-cctv-edge-backup-recovery
```

AI server에서 복구 요청을 활성화하려면 다음 환경 변수를 지정합니다.

```powershell
$env:AI_CCTV_RECOVERY_SERVER_URL="http://192.168.137.2:8002/recover"
ai-cctv-ai-server
```

SSH로 Edge node에 접속해 실행하는 경우 `ai-cctv-edge`는 시작 직후 다음 표준 출력 블록을 표시합니다. AI server는 이 값 중 `RTSP_URL`, `MQTT_BROKER`, `MQTT_TOPIC`, `BACKUP_RECOVERY_URL`을 연결 설정 창에 입력해 사용합니다.

```text
[AI_CCTV Edge Node Connection]
EDGE_HOST=192.168.137.2
RTSP_URL=rtsp://192.168.137.2:8554/live
MQTT_BROKER=192.168.137.2:1883
MQTT_TOPIC=ai-cctv/edge-node/status
BACKUP_RECOVERY_URL=http://192.168.137.2:8002/recover
BACKUP_DIR=~/backups
```

Edge node는 host를 자동 추정하지 않습니다. 실행 전에 `.env`의 `AI_CCTV_EDGE_HOST`에 AI server가 접근할 수 있는 유선 IP를 지정해야 합니다. SSH 세션 IP, 인터페이스 조회, UDP 라우팅, hostname 해석은 `future/edge_host_auto_detection.md`에 차후 구현점으로 분리했습니다.

Edge node의 `ai-cctv-edge`, `ai-cctv-edge-mqtt-broker`, `ai-cctv-edge-monitor`, `ai-cctv-edge-backup-recovery` 진입점은 실행 직후 `ensure_supported_edge_os`를 호출합니다. Windows나 macOS는 즉시 종료되며, `/etc/os-release`에서 배포판을 확인할 수 있는 Linux 환경은 Debian, Raspbian, Ubuntu 계열만 허용합니다. 배포판 정보를 읽을 수 없는 최소 Linux 환경은 Linux 커널 실행 환경으로 보고 허용합니다. 기본 `ai-cctv-edge` 실행은 MediaMTX와 GStreamer 외에도 MQTT broker, MQTT 상태 publisher, FastAPI 백업 복구 서버를 보조 프로세스로 함께 실행합니다. RTSP 송출만 단독 점검하려면 `ai-cctv-edge --no-support-services`를 사용합니다.

AI server는 `server_run.main` 진입 직후 Windows OS 여부를 확인합니다. Windows가 아니면 한국어 오류 메시지를 표준 오류로 출력하고 종료합니다. Windows에서는 먼저 PyQt5가 있는지 확인하고, 없으면 표준 라이브러리 tkinter 창으로 PyQt5 설치 여부를 묻습니다. PyQt5가 준비되면 `EdgeConnectionDialog`가 먼저 표시됩니다. 연결 모드가 정해진 뒤 `RuntimeEnvironmentChecker`가 해당 모드에 필요한 최소 패키지만 점검합니다. 패키지 점검은 경로 존재뿐 아니라 별도 Python 프로세스의 실제 import까지 확인해 DLL 초기화 실패를 누락 상태로 분류합니다. YOLO, Qwen VLM, Discord 알림처럼 분석 시작 때 필요한 항목은 사용자가 영상 시작을 누를 때 선택된 옵션에 맞춰 다시 점검합니다. 누락 항목이 있으면 `RuntimeReadinessDialog`가 표시되고, 사용자가 `O - 자동 설치`를 누른 경우에만 `RuntimeInstallWorker`가 백그라운드에서 `RuntimeInstaller`를 실행해 pip 설치와 모델 다운로드를 시도합니다.

Edge node 모드에서는 Edge node 표준 출력 블록을 붙여넣거나 RTSP, MQTT, 백업 복구 URL을 직접 입력하고, `EdgeConnectionValidator`가 RTSP 포트, MQTT broker 포트, 백업 복구 `/health` endpoint 연결을 모두 확인해야 `CCTVMainWindow`가 생성됩니다. Windows 데스크톱 자체 카메라 모드에서는 로컬 카메라 인덱스를 입력하고 OpenCV가 해당 카메라를 열 수 있는지만 검증합니다. 검증에 성공한 값은 Edge node 모드에서만 `AI_CCTV_MQTT_*`, `AI_CCTV_RECOVERY_SERVER_URL`, `AI_CCTV_RTSP_URL` 환경 변수에 반영됩니다. 로컬 카메라 모드는 Edge 관련 환경 변수를 제거하고 `AI_CCTV_LOCAL_CAMERA_INDEX`만 반영합니다.

검증 명령은 다음과 같습니다.

```bash
python -m compileall src main.py tester
$env:PYTHONPATH="src;."; python -m unittest discover -s tester/tests -t .
```
