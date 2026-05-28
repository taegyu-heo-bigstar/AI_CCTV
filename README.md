# AI CCTV

Raspberry Pi 기반 CCTV 송출 장치와 Windows 서버 기반 AI 영상 분석기를 분리해 구성하는 프로젝트입니다.

## 실행 묶음

| 묶음 | 역할 | 실행 명령 |
|---|---|---|
| Raspberry Pi | 카메라 영상 송출, GStreamer + MediaMTX RTSP publish, 네트워크 장애 정책 | `ai-cctv-edge` |
| Windows 서버 | RTSP 수신, OpenCV/YOLO 분석, 이상 상황 판단, Discord 알림, GUI | `ai-cctv-windows-server` |

## 설치

Raspberry Pi 실행 환경:

```bash
pip install -e ".[edge-pi]"
ai-cctv-edge
```

Windows 서버 실행 환경:

```bash
pip install -e ".[windows-server]"
ai-cctv-windows-server
```

로컬 개발 환경에서 기존 방식으로 Windows 서버를 실행할 수도 있습니다.

```bash
python main.py
```

## 구조

```text
src/ai_cctv/
├─ common/          # 공통 이벤트/메시지 값 객체
├─ edge_pi/         # Raspberry Pi 전용 실행 코드
├─ windows_server/  # Windows 서버 전용 실행 코드
├─ client/          # Windows GUI/영상 분석 구현
├─ anomaly/         # 이상 상황 판단 규칙
├─ alerts/          # Discord 중심 알림 계층
└─ edge/            # 기존 import 호환 레이어
```

## 검증

```bash
python -m compileall src main.py tests
$env:PYTHONPATH="src"; python -m unittest discover -s tests
```
