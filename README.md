# AI CCTV

Raspberry Pi 기반 Edge node와 Windows 기반 AI server를 분리해 구성하는 AI CCTV 프로젝트입니다.

## 실행 묶음

| 묶음 | 역할 | 실행 명령 |
|---|---|---|
| Edge node | 카메라 영상 송출, MediaMTX 실행, GStreamer 송출/로컬 백업, 네트워크 장애 대응 정책 | `ai-cctv-edge` |
| AI server | RTSP 수신, OpenCV/YOLO 분석, 이상 상황 판정, Discord 알림, GUI | `ai-cctv-ai-server` |

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
    |   `-- local_backup.py # 백업 세그먼트 경로 정책
    `-- ai_server/      # Windows AI server 실행 코드
        |-- server_run.py
        |-- ui/         # PyQt 화면, 설정창, 이벤트 표시
        |-- analysis/   # 영상 입력, 추적, VLM, 이상 상황 판정
        |-- storage/    # 저장 경로와 녹화 관리
        |-- alerts/     # Discord 알림과 챗봇 전송
        `-- common/     # 서버 내부 공통 값 객체 재노출
```

## 검증

```bash
python -m compileall src main.py tests
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```
