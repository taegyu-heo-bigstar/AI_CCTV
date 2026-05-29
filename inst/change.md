# develop 브랜치 대비 refactor 브랜치 변경 설명

이 문서는 `origin/develop...refactor` 기준으로 현재 `refactor` 브랜치가 `develop` 브랜치와 어떻게 달라졌는지 설명합니다. 대상 독자는 프로젝트 구조를 처음 보는 주니어 개발자입니다.

## 1. 전체 요약

`develop` 브랜치는 GUI, 영상 처리, RTSP 송수신, Discord 알림, 실험 자료가 여러 폴더에 섞여 있었습니다. `refactor` 브랜치는 최종 실행 환경을 기준으로 코드를 `Edge node`와 `AI server` 두 묶음으로 나눕니다.

현재 `src/ai_cctv` 바로 아래에는 실제 실행 노드만 남습니다.

```text
src/ai_cctv/
  edge_node/
  ai_server/
```

## 2. AI server 구조

AI server 내부는 더 이상 `control_center` 같은 중간 폴더로 감싸지 않습니다. 서버 노드의 1차 책임을 바로 드러내도록 나눴습니다.

```text
src/ai_cctv/ai_server/
  server_run.py      # 서버 실행 진입점
  ui/                # PyQt 화면, 설정창, 이벤트 표시
  analysis/          # 영상 입력, 추적, VLM, 이상 상황 판정
  storage/           # 저장 경로와 녹화 관리
  alerts/            # Discord 알림과 챗봇 전송
  common/            # 서버 내부 공통 값 객체 재노출
  stream_receiver.py # RTSP 수동 점검 도구
```

이 구조의 기준은 다음과 같습니다.

| 질문 | 위치 |
|---|---|
| 화면, 설정창, 이벤트 표시인가? | `ai_server/ui` |
| 영상 입력, 사람 추적, VLM, 이상 상황 판정인가? | `ai_server/analysis` |
| 저장 경로 생성이나 녹화 관리인가? | `ai_server/storage` |
| Discord 알림 메시지와 전송인가? | `ai_server/alerts` |
| 서버 실행을 시작하는 진입점인가? | `ai_server/server_run.py` |

## 2-1. Edge node 구조

Edge node는 더 이상 루트 `scripts/stream_and_record.sh`에 운영 책임을 두지 않습니다. Bash 스크립트가 하던 MediaMTX 준비, 송출, 로컬 백업 책임을 Python 패키지 내부로 옮겼습니다.

```text
src/ai_cctv/edge_node/
  main.py          # ai-cctv-edge 실행 진입점
  runtime.py       # MediaMTX 준비 후 GStreamer 실행
  mediamtx.py      # MediaMTX 다운로드, 설치 확인, 프로세스 관리
  streaming.py     # GStreamer tee 기반 송출/백업 파이프라인 생성
  local_backup.py  # 백업 폴더와 10초 세그먼트 파일명 정책
  failover.py      # 네트워크 장애 시 동작 정책
```

`ai-cctv-edge`는 실제 Raspberry Pi 런타임을 실행합니다. 명령만 확인해야 할 때는 `ai-cctv-edge --print-command`를 사용합니다.

## 3. 실행 진입점 변경

기존 서버 실행 진입점은 `ai_cctv.ai_server.main:main`이었습니다. 이제는 역할을 더 명확히 하기 위해 `server_run.py`를 사용합니다.

| 명령 | 현재 진입점 |
|---|---|
| `ai-cctv` | `ai_cctv.ai_server.server_run:main` |
| `ai-cctv-ai-server` | `ai_cctv.ai_server.server_run:main` |

루트 `main.py`와 `python -m ai_cctv`도 같은 서버 실행 진입점을 호출합니다.

## 4. 주요 이동

| 이전 위치 | 현재 위치 | 이유 |
|---|---|---|
| `scripts/stream_and_record.sh` | `edge_node/runtime.py`, `edge_node/mediamtx.py`, `edge_node/streaming.py`, `edge_node/local_backup.py` | 엣지 노드 운영 책임을 Python 배포 단위 안으로 통합 |
| `ai_server/control_center/ui` | `ai_server/ui` | UI는 서버 노드의 1차 책임이므로 바로 드러냄 |
| `ai_server/control_center/storage` | `ai_server/storage` | 저장/녹화 책임을 분석 루프에서 분리 |
| `ai_server/control_center/video_worker.py` | `ai_server/analysis/video_worker.py` | 영상 처리 루프는 분석 책임에 속함 |
| `ai_server/control_center/person_tracker.py` | `ai_server/analysis/person_tracker.py` | YOLO 추적은 분석 책임에 속함 |
| `ai_server/anomaly` | `ai_server/analysis/anomaly` | 이상 상황 판정도 분석 파이프라인 내부 책임 |
| `ai_server/main.py` | `ai_server/server_run.py` | 서버 실행 파일임을 이름으로 명확히 함 |

## 5. 알림 구조

Discord 전송 구현은 `alerts` 아래에 있습니다.

```text
ai_server/alerts/
  dispatcher.py
  message.py
  chat_bot/
```

`analysis` 계층은 이상 상황 이벤트를 만들고, `alerts` 계층은 그 이벤트를 Discord 메시지로 전송합니다. 이 분리 덕분에 영상 분석 코드가 Discord API 세부 구현을 직접 알 필요가 없습니다.

## 6. 검증 기준

`tests/test_project_structure.py`는 다음을 확인합니다.

| 검증 항목 | 의미 |
|---|---|
| Edge node와 AI server 실행 진입점 분리 | 배포 단위가 명확함 |
| Edge node Python 런타임 존재 | 라즈베리 파이 송출/백업 기능이 패키지 내부에 있음 |
| `server_run.py` 존재 | 서버 실행 진입점이 명확함 |
| `ui`, `analysis`, `storage`, `alerts` 존재 | 서버 책임이 1차 폴더로 드러남 |
| `control_center`, `main.py`, `analysis.py` 제거 | 애매한 중간 계층과 모호한 파일 제거 |
| 이상 상황/알림/Edge 송출 단위 동작 | 핵심 기능이 유지됨 |
