# develop 브랜치 대비 refactor 브랜치 변경 설명

이 문서는 `origin/develop...refactor` 기준으로 현재 `refactor` 브랜치가 `develop` 브랜치와 어떻게 달라졌는지 설명합니다. 대상 독자는 프로젝트 구조를 처음 보는 주니어 개발자이며, “무엇을 옮겼는지”보다 “왜 그렇게 책임을 나누었는지”에 초점을 둡니다.

## 1. 전체 요약

`develop` 브랜치는 GUI, 영상 처리, RTSP 송수신, Discord 알림, 실험 자료가 여러 폴더에 섞여 있었습니다. `refactor` 브랜치는 최종 실행 환경을 기준으로 `src/ai_cctv` 패키지를 만들고, 라즈베리 파이에서 실행할 Edge node 코드와 Windows 데스크탑에서 실행할 AI server 코드를 분리했습니다.

이번 변경에서는 서버 노드가 소유하는 `client`, `anomaly`, `alerts`, `common` 패키지를 모두 `src/ai_cctv/ai_server` 아래로 이동했습니다. 이제 `src/ai_cctv` 바로 아래에는 실제 실행 노드인 `edge_node`와 `ai_server`만 남습니다.

| 구분 | develop 브랜치 | refactor 브랜치 |
|---|---|---|
| 프로젝트 형태 | 루트 주변의 여러 스크립트를 직접 실행 | `src/ai_cctv` 중심의 Python 패키지 |
| 실행 단위 | 파일 경로를 기억해서 실행 | `ai-cctv-edge`, `ai-cctv-ai-server` 콘솔 명령 제공 |
| Edge node | RTSP 송출 실험 코드가 독립 폴더에 존재 | `edge_node`에서 GStreamer + MediaMTX 송출 명령 생성 |
| AI server | GUI, 탐지, 알림 코드가 혼재 | `ai_server/client`, `ai_server/anomaly`, `ai_server/alerts`로 서버 내부 책임 분리 |
| 알림 | 여러 알림 가능성이 설계와 코드에 섞임 | 현시점 구현은 Discord 중심, 확장은 인터페이스로 남김 |
| 레거시 코드 | 오래된 GUI/RTSP/stub 코드가 함께 존재 | 사용 경로가 없는 레거시 파일 제거 |
| 검증 | 구조를 확인하는 자동 테스트 부족 | `tests/test_project_structure.py`로 구조와 핵심 도메인 동작 검증 |

## 2. 배포 목표에 맞춘 구조

최종 시스템은 한 프로그램이 모든 일을 하는 구조가 아닙니다.

| 실행 환경 | 실제 장비 | 주요 책임 |
|---|---|---|
| Edge node | 카메라가 장착된 Raspberry Pi | 카메라 영상 촬영, GStreamer 송출, MediaMTX publish, 네트워크 장애 정책 |
| AI server | Windows 데스크탑 | RTSP 수신, YOLO 분석, 이상 상황 판정, Discord 알림, GUI 표시 |

따라서 최상위 소스 구조도 두 노드 기준으로 읽혀야 합니다.

```text
src/ai_cctv/
  edge_node/      # Raspberry Pi 실행 묶음
  ai_server/      # Windows AI server 실행 묶음
```

서버 노드 내부는 다시 책임별로 나뉩니다.

```text
src/ai_cctv/ai_server/
  client/         # GUI, 영상 루프, 추적, 녹화, VLM 구현
  anomaly/        # 이상 상황 판정 규칙과 이벤트
  alerts/         # Discord 알림 메시지와 디스패처
  common/         # 서버 노드 내부 공통 값 객체 재노출
```

이 구조는 배포 단위와 폴더 구조를 1:1에 가깝게 맞춥니다. 라즈베리 파이에 올릴 코드는 `edge_node`를 보면 되고, Windows 서버에 올릴 코드는 `ai_server`를 보면 됩니다.

## 3. Edge node 변경

Edge node의 핵심 코드는 `src/ai_cctv/edge_node` 아래에만 둡니다.

| 파일 | 책임 |
|---|---|
| `main.py` | 기본 GStreamer 송출 명령을 출력하는 실행 진입점 |
| `streaming.py` | MediaMTX에 publish할 GStreamer 명령 인자 생성 |
| `failover.py` | 네트워크 장애 시 송출/로컬 저장/최소 알림 정책 결정 |

## 4. AI server 변경

AI server는 `src/ai_cctv/ai_server` 아래에 서버 노드 실행 코드와 서버 노드 소유 도메인을 모두 포함합니다.

| 경로 | 책임 |
|---|---|
| `ai_server/main.py` | GUI 기반 AI server 실행 |
| `ai_server/analysis.py` | 분석 계층 public API 재노출 |
| `ai_server/stream_receiver.py` | MediaMTX RTSP 수신 수동 점검 |
| `ai_server/client/` | PyQt GUI, OpenCV 영상 루프, YOLO 추적, 녹화, VLM 분석 |
| `ai_server/anomaly/` | 감지 결과를 이상 상황 이벤트로 변환 |
| `ai_server/alerts/` | 이상 상황 이벤트를 Discord 알림 메시지로 전송 |
| `ai_server/common/` | 서버 내부에서 공유하는 값 객체 재노출 |

`ai_server/__init__.py`는 의도적으로 가볍게 유지합니다. 테스트나 하위 패키지 import 시점에 PyQt, YOLO, VLM 같은 무거운 의존성이 로드되지 않도록 하기 위해서입니다. 실제 GUI 실행은 `ai_server/main.py`의 `main()` 안에서 지연 import합니다.

## 5. 이상 상황 판정 변경

`ai_server/anomaly/detector.py`는 감지 결과를 이상 상황 이벤트로 바꾸는 순수 판정 계층입니다. GUI, 영상 수신, Discord 전송을 알지 않습니다.

| 이름 | 역할 |
|---|---|
| `AnomalyRuleEngine` | 여러 이상 상황 규칙을 순서대로 실행 |
| `ObjectAppearanceRule` | 새 객체 등장 이벤트를 한 번만 생성 |
| `DwellTimeAnomalyRule` | 기준 시간 이상 머문 객체를 이상 상황으로 판정 |

## 6. 알림 변경

현시점에서 이상 상황 알림은 Discord로만 보냅니다. 다만 추후 확장을 위해 전송 채널 인터페이스는 유지했습니다.

| 이름 | 역할 |
|---|---|
| `NotificationMessage` | 채널로 보낼 알림 메시지 값 객체 |
| `NotificationChannel` | 알림 전송 채널 공통 인터페이스 |
| `DiscordNotificationChannel` | 기존 Discord 챗봇 모듈 어댑터 |
| `NotificationDispatcher` | 알림 메시지를 등록 채널로 전달 |

## 7. 제거한 코드

다음 파일은 현재 실행 경로에서 사용되지 않거나, 최종 구조의 책임 경계를 흐리기 때문에 제거했습니다.

| 제거 파일 | 제거 이유 |
|---|---|
| `src/ai_cctv/ai_server/client/legacy_cctv_gui.py` | 현재 GUI 진입점은 `ai_server/client/gui.py`와 `ai_server/client/ui/main_window.py` |
| `src/ai_cctv/server/fail_over.py` | `print("test")` 수준의 stub로 실제 서버 기능이 아님 |
| `src/ai_cctv/streaming/sender.py` | Edge node 송출 책임은 `edge_node/streaming.py`로 통합 |
| `src/ai_cctv/streaming/receiver.py` | RTSP 수신 점검은 `ai_server/stream_receiver.py`로 이동 |
| `src/ai_cctv/streaming/legacy_rtsp_receiver.py` | legacy 수신 구현으로 현재 구조와 중복 |

## 8. 개발자가 따라야 할 기준

새 코드를 추가할 때는 먼저 실행 위치를 결정해야 합니다.

| 질문 | 들어갈 위치 |
|---|---|
| Raspberry Pi에서 카메라 송출이나 장애 대응에 필요한가? | `src/ai_cctv/edge_node` |
| Windows AI server 실행, 수신, 분석, UI, 알림에 필요한가? | `src/ai_cctv/ai_server` |
| 서버 내부 GUI/영상 처리 구현인가? | `src/ai_cctv/ai_server/client` |
| 서버 내부 이상 상황 판정 규칙인가? | `src/ai_cctv/ai_server/anomaly` |
| 서버 내부 Discord 알림인가? | `src/ai_cctv/ai_server/alerts` |

이 기준을 지키면 최상위 `src/ai_cctv`는 두 노드만 보여주고, 세부 책임은 각 노드 내부에서만 확장됩니다.
