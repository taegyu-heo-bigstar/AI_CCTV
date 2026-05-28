# develop 브랜치 대비 refactor 브랜치 변경 설명

이 문서는 `origin/develop...refactor` 기준으로 현재 `refactor` 브랜치가 `develop` 브랜치와 어떻게 달라졌는지 설명합니다. 대상 독자는 프로젝트 구조를 처음 보는 주니어 개발자이며, “무엇을 옮겼는지”보다 “왜 그렇게 책임을 나누었는지”에 초점을 둡니다.

## 1. 전체 요약

`develop` 브랜치는 GUI, 영상 처리, RTSP 송수신, Discord 알림, 실험 자료가 여러 폴더에 섞여 있었습니다. `refactor` 브랜치는 최종 실행 환경을 기준으로 `src/ai_cctv` 패키지를 만들고, 라즈베리 파이에서 실행할 Edge node 코드와 Windows 데스크탑에서 실행할 AI server 코드를 분리했습니다.

| 구분 | develop 브랜치 | refactor 브랜치 |
|---|---|---|
| 프로젝트 형태 | 루트 주변의 여러 스크립트를 직접 실행 | `src/ai_cctv` 중심의 Python 패키지 |
| 실행 단위 | 파일 경로를 기억해서 실행 | `ai-cctv-edge`, `ai-cctv-ai-server` 콘솔 명령 제공 |
| Edge node | RTSP 송출 실험 코드가 독립 폴더에 존재 | `edge_node`에서 GStreamer + MediaMTX 송출 명령 생성 |
| AI server | GUI, 탐지, 알림 코드가 혼재 | `ai_server`, `client`, `anomaly`, `alerts`로 책임 분리 |
| 알림 | 여러 알림 가능성이 설계와 코드에 섞임 | 현시점 구현은 Discord 중심, 확장은 인터페이스로 남김 |
| 레거시 코드 | 오래된 GUI/RTSP/stub 코드가 함께 존재 | 사용 경로가 없는 레거시 파일 제거 |
| 검증 | 구조를 확인하는 자동 테스트 부족 | `tests/test_project_structure.py`로 구조와 핵심 도메인 동작 검증 |

## 2. 배포 목표에 맞춘 구조

최종 시스템은 한 프로그램이 모든 일을 하는 구조가 아닙니다.

| 실행 환경 | 실제 장비 | 주요 책임 |
|---|---|---|
| Edge node | 카메라가 장착된 Raspberry Pi | 카메라 영상 촬영, GStreamer 송출, MediaMTX publish, 네트워크 장애 정책 |
| AI server | Windows 데스크탑 | RTSP 수신, YOLO 분석, 이상 상황 판정, Discord 알림, GUI 표시 |

따라서 코드도 장비 기준으로 먼저 나누고, 그 안에서 세부 책임을 다시 나누었습니다. Raspberry Pi에는 PyQt, YOLO, VLM 같은 무거운 AI server 의존성이 필요하지 않습니다. 반대로 Windows AI server에는 카메라 송출 명령 생성보다 수신, 분석, 알림, UI가 중요합니다.

## 3. 현재 핵심 폴더 책임

```text
src/ai_cctv/
  edge_node/      # Raspberry Pi 실행 묶음
  ai_server/      # Windows AI server 실행 묶음
  client/         # GUI, 영상 처리, 추적, 녹화 구현
  anomaly/        # 이상 상황 판정 규칙과 이벤트
  alerts/         # Discord 알림 메시지와 디스패처
  common/         # 공통 값 객체 재노출
```

이전 리팩터링 과정에서 남아 있던 `src/ai_cctv/server`와 `src/ai_cctv/streaming`은 이번 변경에서 제거했습니다. 두 폴더는 최종 실행 묶음 기준으로 읽기 어렵고, 일부 파일은 `print("test")` 같은 stub 또는 `legacy_*` 이름의 오래된 코드였습니다. 유효한 RTSP 수신 점검 기능은 `src/ai_cctv/ai_server/stream_receiver.py`로 이동했습니다.

## 4. Edge node 변경

Edge node의 핵심 코드는 `src/ai_cctv/edge_node` 아래에만 둡니다.

| 파일 | 책임 |
|---|---|
| `main.py` | 기본 GStreamer 송출 명령을 출력하는 실행 진입점 |
| `streaming.py` | MediaMTX에 publish할 GStreamer 명령 인자 생성 |
| `failover.py` | 네트워크 장애 시 송출/로컬 저장/최소 알림 정책 결정 |

이름도 책임 중심으로 바꾸었습니다.

| 이전 이름 | 현재 이름 | 이유 |
|---|---|---|
| `PiStreamingConfig` | `EdgeStreamConfig` | Raspberry Pi라는 장비명보다 Edge node 송출 설정이라는 책임을 드러냄 |
| `GStreamerMediaMtxCommandBuilder` | `MediaMtxGStreamerCommandBuilder` | MediaMTX publish를 위한 GStreamer 명령 생성기임을 명확히 함 |
| `build_command()` | `build_command_args()` | 반환값이 문자열이 아니라 subprocess용 인자 목록임을 드러냄 |
| `build_shell_text()` | `build_shell_command_text()` | 운영자가 보는 셸 명령 문자열임을 명확히 함 |
| `NetworkFailoverPolicy` | `EdgeNetworkFailoverPolicy` | AI server가 아니라 Edge node의 장애 정책임을 명확히 함 |
| `FailoverAction` | `EdgeFailoverDecision` | 정책이 “실행”하는 것이 아니라 “결정값”을 반환한다는 점을 드러냄 |

## 5. AI server 변경

AI server는 `src/ai_cctv/ai_server`가 실행 묶음의 입구 역할을 합니다. 실제 GUI와 영상 처리 구현은 `client`에 남기고, 이상 상황 판단은 `anomaly`, 알림 전송은 `alerts`로 분리했습니다.

| 파일 | 책임 |
|---|---|
| `ai_server/main.py` | GUI 기반 AI server 실행 |
| `ai_server/analysis.py` | 분석 계층 public API 재노출 |
| `ai_server/alerts.py` | 알림 계층 public API 재노출 |
| `ai_server/stream_receiver.py` | MediaMTX RTSP 수신 수동 점검 |

`VideoWorker`는 여전히 전체 프레임 처리 루프를 조정하지만, 이상 상황 판정과 알림 전송의 실제 책임은 주입된 객체로 분리했습니다. 내부 이름도 `anomaly_rule_engine`, `notification_dispatcher`로 바꾸어 어떤 객체가 어떤 일을 하는지 드러나게 했습니다.

## 6. 이상 상황 판정 변경

`anomaly.detector`는 “감지 결과를 이상 상황 이벤트로 바꾸는 순수 판정 계층”입니다. GUI, 영상 수신, Discord 전송을 알지 않습니다.

| 이전 이름 | 현재 이름 | 이유 |
|---|---|---|
| `AnomalyDetector` | `AnomalyRuleEngine` | 여러 규칙을 실행하는 엔진 역할임을 명확히 함 |
| `ObjectPresenceRule` | `ObjectAppearanceRule` | 객체가 “존재한다”가 아니라 “새로 등장했다”는 이벤트 조건을 표현 |
| `DwellTimeRule` | `DwellTimeAnomalyRule` | 체류 시간 초과가 이상 상황 규칙임을 명확히 함 |
| `evaluate()` | `evaluate_detections()` | 입력이 YOLO 감지 결과 목록임을 드러냄 |

주니어 개발자가 이 계층을 수정할 때의 기준은 단순합니다. 새로운 이상 상황 조건을 추가한다면 `AnomalyDetectionRule`을 구현하고, 그 규칙을 `AnomalyRuleEngine`에 넣으면 됩니다. Discord 전송이나 UI 업데이트 코드는 이 계층에 넣지 않습니다.

## 7. 알림 변경

현시점에서 이상 상황 알림은 Discord로만 보냅니다. 다만 추후 확장을 위해 전송 채널 인터페이스는 유지했습니다.

| 이전 이름 | 현재 이름 | 이유 |
|---|---|---|
| `AlertMessage` | `NotificationMessage` | 채널에 전달되는 일반 알림 메시지 값 객체임을 표현 |
| `AlertChannel` | `NotificationChannel` | 알림 전송 채널의 공통 인터페이스임을 표현 |
| `DiscordChatBotChannel` | `DiscordNotificationChannel` | Discord 전송 채널임을 직접 표현 |
| `AlertDispatcher` | `NotificationDispatcher` | 메시지를 여러 채널로 분배하는 책임을 표현 |
| `dispatch_anomaly()` | `dispatch_anomaly_event()` | 입력값이 이상 상황 이벤트임을 명확히 함 |

중요한 점은 “Discord 외 알림을 지금 구현하지 않는다”는 것입니다. 다른 방식은 확장 지점으로만 열어두고, 현재 실행 경로는 Discord 중심으로 단순하게 유지했습니다.

## 8. 제거한 코드

다음 파일은 현재 실행 경로에서 사용되지 않거나, 최종 구조의 책임 경계를 흐리기 때문에 제거했습니다.

| 제거 파일 | 제거 이유 |
|---|---|
| `src/ai_cctv/client/legacy_cctv_gui.py` | 현재 GUI 진입점은 `client/gui.py`와 `client/ui/main_window.py`이며 레거시 GUI는 사용 경로가 없음 |
| `src/ai_cctv/server/fail_over.py` | `print("test")` 수준의 stub로 실제 서버 기능이 아님 |
| `src/ai_cctv/streaming/sender.py` | Edge node 송출 책임은 `edge_node/streaming.py`로 통합 |
| `src/ai_cctv/streaming/receiver.py` | RTSP 수신 점검은 AI server 책임으로 이동 |
| `src/ai_cctv/streaming/legacy_rtsp_receiver.py` | legacy 수신 구현으로 현재 구조와 중복 |

삭제 기준은 “파일이 낡았는가”가 아니라 “현재 목표 구조에서 명확한 책임과 호출 경로가 있는가”입니다.

## 9. 테스트와 문서 변경

`tests/test_project_structure.py`는 다음을 검증합니다.

| 검증 항목 | 의미 |
|---|---|
| 객체 등장 규칙은 같은 추적 ID를 한 번만 보고 | 이상 상황 중복 알림 방지 |
| 체류 시간 규칙은 기준 시간 이후 이벤트 생성 | 시간 기반 이상 상황 판정 유지 |
| 알림 디스패처는 이상 상황 이벤트를 메시지로 전송 | Discord 전송 전 단계의 메시지 변환 유지 |
| Edge failover 정책은 장애 시 로컬 저장과 최소 알림 선택 | Raspberry Pi 장애 대응 정책 유지 |
| GStreamer 명령은 MediaMTX RTSP 목적지를 포함 | 송출 구조가 GStreamer + MediaMTX 기준임을 유지 |
| 배포 묶음과 레거시 파일 제거 상태 확인 | Edge node와 AI server 중심 구조 유지 |

문서는 다음 기준으로 갱신했습니다.

| 문서 | 역할 |
|---|---|
| `inst/flow.md` | 실행 흐름과 책임 경계를 새 이름 기준으로 설명 |
| `inst/structure.md` | 실제 AST를 읽어 파일별 클래스/함수 표를 생성 |
| `inst/change.md` | develop 대비 구조 변경과 설계 이유 설명 |

## 10. 개발자가 따라야 할 기준

새 코드를 추가할 때는 먼저 실행 위치를 결정해야 합니다.

| 질문 | 들어갈 위치 |
|---|---|
| Raspberry Pi에서 카메라 송출이나 장애 대응에 필요한가? | `edge_node` |
| Windows AI server 실행 진입점이나 수신 점검인가? | `ai_server` |
| GUI, 영상 루프, 추적, 녹화 구현인가? | `client` |
| 감지 결과를 이상 상황으로 판정하는 규칙인가? | `anomaly` |
| Discord 알림 메시지와 전송인가? | `alerts` |
| 여러 계층이 함께 쓰는 값 객체 재노출인가? | `common` |

이 기준을 지키면 폴더 수가 많아도 구조가 흐트러지지 않습니다. 반대로 `server`, `streaming`, `legacy`처럼 실행 묶음과 책임이 동시에 애매한 폴더를 다시 만들면 프로젝트를 읽는 사람이 어떤 파일이 실제 운영 코드인지 판단하기 어려워집니다.
