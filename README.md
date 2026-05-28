# AI CCTV

Raspberry Pi 기반 Edge node와 Windows 기반 AI server를 분리해 구성하는 AI CCTV 프로젝트입니다.

## 실행 묶음

| 묶음 | 역할 | 실행 명령 |
|---|---|---|
| Edge node | 카메라 영상 송출, GStreamer + MediaMTX RTSP publish, 네트워크 장애 대응 정책 | `ai-cctv-edge` |
| AI server | RTSP 수신, OpenCV/YOLO 분석, 이상 상황 판정, Discord 알림, GUI | `ai-cctv-ai-server` |

## 설치

Edge node 실행 환경:

```bash
pip install -e ".[edge-node]"
ai-cctv-edge
```

전통적인 requirements 파일이 필요한 환경에서는 다음 파일을 사용할 수 있습니다.

```bash
pip install -r requirements/edge-node.txt
```

AI server 실행 환경:

```bash
pip install -e ".[ai-server]"
ai-cctv-ai-server
```

전통적인 requirements 파일이 필요한 환경에서는 다음 파일을 사용할 수 있습니다.

```bash
pip install -r requirements/ai-server.txt
```

로컬 개발 환경에서 AI server를 바로 실행할 수도 있습니다.

```bash
python main.py
```

## 구조

```text
inst/                 # 구조, 흐름, 변경 설명 문서
requirements/         # 실행 환경별 의존성 목록
src/
`-- ai_cctv/
    |-- edge_node/    # Edge node 전용 실행 코드
    `-- ai_server/    # AI server 전용 실행 코드와 서버 소유 하위 도메인
        |-- client/   # GUI, 영상 루프, 추적, 녹화, VLM 분석 구현
        |-- anomaly/  # 이상 상황 판정 규칙과 이벤트
        |-- alerts/   # Discord 중심 알림 계층
        `-- common/   # 서버 노드 내부 공통 값 객체 재노출
```

## 검증

```bash
python -m compileall src main.py tests
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```
