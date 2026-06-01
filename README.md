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
