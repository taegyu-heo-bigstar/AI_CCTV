# AI CCTV

Raspberry Pi 기반 Edge node와 Windows 기반 AI server를 분리해 구성하는 AI CCTV 프로젝트입니다.

## 실행 묶음

| 묶음 | 역할 | 실행 명령 |
|---|---|---|
| Edge node | 카메라 영상 송출, MediaMTX 실행, GStreamer 송출/로컬 백업, MQTT 상태 발행, 백업 복구 ZIP 제공, 네트워크 장애 대응 정책 | `ai-cctv-edge`, `ai-cctv-edge-monitor`, `ai-cctv-edge-backup-recovery` |
| AI server | RTSP 수신/재연결, OpenCV/YOLO 분석, MQTT 상태 구독, 이상 상황 판정, Discord 알림, GUI, 누락 구간 복구 요청 | `ai-cctv-ai-server` |

## 설치

Edge node 실행 환경:

```bash
pip install -e ".[edge-node]"
ai-cctv-edge
```

GStreamer 명령만 확인하려면 다음 옵션을 사용할 수 있습니다.

```bash
ai-cctv-edge --print-command
```

AI server 실행 환경:

```bash
pip install -e ".[ai-server]"
ai-cctv-ai-server
```

Edge node 상태 정보는 MQTT broker를 기준으로 주고받습니다. 기본 broker는 `127.0.0.1:1883`, 기본 topic은 `ai-cctv/edge-node/status`입니다.

```bash
ai-cctv-edge-monitor
python -m ai_cctv.ai_server.monitoring.resource_monitor_client
```

네트워크 단절 후 누락 구간 영상을 복구하려면 Edge node에서 FastAPI 기반 백업 복구 서버를 함께 실행합니다. AI server는 `requests`로 해당 API를 호출하므로 `AI_CCTV_RECOVERY_SERVER_URL`을 지정합니다.

```bash
ai-cctv-edge-backup-recovery
```

```powershell
$env:AI_CCTV_RECOVERY_SERVER_URL="http://192.168.137.2:8002/recover"
ai-cctv-ai-server
```

requirements 파일이 필요한 환경에서는 다음 파일을 사용할 수 있습니다.

```bash
pip install -r requirements/edge-node.txt
pip install -r requirements/ai-server.txt
```

로컬 개발 환경에서 AI server를 바로 실행할 수도 있습니다.

```bash
python main.py
```

## 구조

```text
src/
`-- ai_cctv/
    |-- edge_node/      # Raspberry Pi Edge node 실행 코드
    |   |-- main.py     # Edge node 실행 진입점
    |   |-- runtime.py  # MediaMTX 준비와 GStreamer 실행 조율
    |   |-- mediamtx.py # MediaMTX 다운로드/프로세스 관리
    |   |-- streaming.py # GStreamer 송출/백업 파이프라인 생성
    |   |-- backup_recovery_server.py # 누락 구간 백업 ZIP 제공
    |   |-- monitoring/ # MQTT 자원/전원 상태 발행
    |   `-- local_backup.py # 백업 세그먼트 경로 정책
    `-- ai_server/      # Windows AI server 실행 코드
        |-- server_run.py
        |-- ui/         # PyQt 화면, 설정창, 이벤트 표시
        |-- analysis/   # 영상 입력, RTSP 재연결, 추적, VLM, 이상 상황 판정
        |-- recovery/   # RTSP 장애 구간 백업 복구 요청
        |-- storage/    # 저장 경로와 녹화 관리
        |-- monitoring/ # Edge node MQTT 상태 구독
        |-- alerts/     # Discord 알림과 챗봇 전송
        `-- common/     # 서버 내부 공통 값 객체 재노출
```

## 검증

```bash
python -m compileall src main.py tests
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```

## SSH 유선 연결 실행 절차

라즈베리 파이를 Windows AI server와 유선 Ethernet으로 연결하고 SSH 터미널에서 실행하면, Edge node 프로그램은 시작 직후 표준 출력으로 AI server에 입력할 값을 출력합니다. 자동 IP 감지가 틀리면 실행 전에 `AI_CCTV_EDGE_HOST`를 라즈베리 파이의 유선 IP로 지정합니다.

```bash
export AI_CCTV_EDGE_HOST=192.168.137.2
export AI_CCTV_MQTT_HOST=192.168.137.1
ai-cctv-edge
```

상태 모니터링과 누락 구간 복구까지 함께 쓰려면 별도 SSH 터미널에서 다음 프로세스도 실행합니다.

```bash
export AI_CCTV_EDGE_HOST=192.168.137.2
export AI_CCTV_MQTT_HOST=192.168.137.1
ai-cctv-edge-monitor
```

```bash
export AI_CCTV_EDGE_HOST=192.168.137.2
ai-cctv-edge-backup-recovery
```

출력 예시는 다음 형태입니다.

```text
[AI_CCTV Edge Node Connection]
EDGE_HOST=192.168.137.2
RTSP_URL=rtsp://192.168.137.2:8554/live
MQTT_BROKER=192.168.137.1:1883
MQTT_TOPIC=ai-cctv/edge-node/status
BACKUP_RECOVERY_URL=http://192.168.137.2:8002/recover
BACKUP_DIR=~/backups
```

Windows AI server를 실행하면 메인 관제 창보다 먼저 Edge node 연결 설정 창이 표시됩니다. 위 출력 블록을 붙여넣고 `출력값 적용`을 누른 뒤 `연결 확인 후 시작`을 누르면 RTSP, MQTT broker, 백업 복구 API 접속을 확인합니다. 세 연결이 모두 성공해야 메인 관제 창이 열립니다.

```powershell
ai-cctv-ai-server
```

AI server 진입점은 Windows가 아닌 OS를 감지하면 오류 메시지를 출력하고 즉시 종료합니다. Windows에서는 먼저 PyQt5를 확인하고, PyQt5가 없으면 표준 라이브러리 tkinter 창으로 설치 여부를 묻습니다. 이후 실행 환경을 검사하며 PyTorch, PyQt5, OpenCV, Ultralytics, Transformers, Accelerate, bitsandbytes, HuggingFace Hub, Qwen 관련 패키지, Discord 알림 패키지, 얼굴 식별 패키지, YOLO/Qwen 모델이 없으면 설치 확인 창을 표시합니다. `O - 자동 설치`를 누르면 누락 항목 설치를 시도하고, `X - 설치하지 않음`을 누르면 프로그램을 시작하지 않습니다.

연결 설정 창에서 성공한 값은 자동으로 다음 항목에 반영됩니다.

| 값 | 반영 위치 |
|---|---|
| `RTSP_URL` | 메인 영상 입력 소스 |
| `MQTT_BROKER`, `MQTT_TOPIC` | Edge node 상태 조회 MQTT 구독 설정 |
| `BACKUP_RECOVERY_URL` | RTSP 장애 구간 백업 복구 요청 URL |

Windows 데스크톱의 자체 카메라만 테스트하려면 연결 설정 창에서 `Windows 데스크톱 자체 카메라 사용`을 선택하고 카메라 번호를 입력합니다. 이 경우 RTSP, MQTT, 백업 복구 API 검증은 건너뛰고 OpenCV가 해당 카메라를 열 수 있는지만 확인합니다.
