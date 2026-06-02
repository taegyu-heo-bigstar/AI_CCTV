# rtsp-review 브랜치 실행 안내

이 문서는 원격 브랜치 `rtsp-review` 기준 실행 방법과 사용 이유를 정리한 안내서입니다.
사용자가 입력한 `rtsp-reivew`는 오타로 보이며, 현재 원격 저장소의 실제 브랜치명은 `rtsp-review`입니다.

## 1. 브랜치 목적

`rtsp-review` 브랜치는 라즈베리 파이 카메라 영상을 GStreamer와 MediaMTX로 송출하고, 윈도우 데스크탑 관제 프로그램이 RTSP 스트림을 수신하는 방식을 검증하기 위한 브랜치입니다.

핵심 목적은 다음과 같습니다.

| 목적 | 설명 |
| --- | --- |
| RTSP 송출 검증 | 라즈베리 파이에서 카메라 영상을 네트워크로 실시간 송출합니다. |
| 윈도우 수신 검증 | 윈도우 데스크탑 GUI에서 RTSP 주소를 입력해 영상을 수신합니다. |
| 장애 복구 검증 | 네트워크 장애 구간에 대해 라즈베리 파이 로컬 백업 영상을 요청해 복구합니다. |
| 자원 모니터링 검증 | FastAPI 서버를 통해 CPU, 메모리, 프로세스 사용률을 JSON으로 조회합니다. |

## 2. 이 구조를 사용하는 이유

### 2.1 GStreamer + MediaMTX를 쓰는 이유

라즈베리 파이에서 카메라 영상을 직접 RTSP로 내보내는 방식은 플러그인, 패드 연결, 하드웨어 인코딩 상태에 따라 불안정해질 수 있습니다.
이 브랜치의 `rtspv1.0/stream_and_record.sh`는 다음 구조를 사용합니다.

```text
라즈베리 파이 카메라
  -> GStreamer libcamerasrc
  -> H.264 인코딩
  -> tee 분기
      -> 10초 단위 로컬 TS 백업
      -> RTMP로 로컬 MediaMTX에 송출
  -> MediaMTX가 RTSP로 재송출
```

즉, GStreamer는 카메라 캡처와 인코딩에 집중하고, MediaMTX는 네트워크 스트림 서버 역할을 맡습니다.
이렇게 나누면 RTSP 서버 구현을 직접 유지하지 않아도 되고, 수신 측에서는 일반적인 `rtsp://IP:8554/live` 주소만 사용하면 됩니다.

### 2.2 10초 단위 백업을 쓰는 이유

`stream_and_record.sh`는 `splitmuxsink`를 사용해 영상을 10초 단위 `.ts` 파일로 저장합니다.
네트워크가 끊긴 구간이 발생하면 AI 서버는 장애 시작 시각과 복구 시각을 기준으로 라즈베리 파이에 백업 파일을 요청할 수 있습니다.

짧은 조각 단위로 저장하는 이유는 다음과 같습니다.

| 이유 | 설명 |
| --- | --- |
| 복구 범위 최소화 | 장애 구간과 겹치는 파일만 ZIP으로 받을 수 있습니다. |
| 파일 손상 범위 축소 | 녹화 중 종료되어도 손상 범위가 짧은 조각에 한정됩니다. |
| 병렬 처리 용이 | 송출과 저장을 `tee`로 분리해 실시간 송출 지연을 줄입니다. |

### 2.3 RTSP 수신기에 watchdog을 둔 이유

OpenCV의 `VideoCapture`는 RTSP 연결이 비정상 상태가 되었을 때 오래 멈출 수 있습니다.
`클라이언트 코드/rtsp_receiver.py`는 RTSP 포트를 먼저 TCP로 확인하고, 프레임이 5초 이상 들어오지 않으면 캡처 객체를 해제해 재연결을 유도합니다.

이 방식은 GUI가 응답 없음 상태로 오래 멈추는 문제를 줄이기 위한 방어 로직입니다.

## 3. 폴더별 역할

| 경로 | 역할 |
| --- | --- |
| `rtspv1.0/` | 라즈베리 파이용 RTSP 송출, 10초 백업, 백업 복구 API 테스트 코드입니다. |
| `rtsp/` | 최소 RTSP 송수신 프로토타입입니다. 기능 검증용이며 실제 운용은 `rtspv1.0/` 쪽이 더 가깝습니다. |
| `클라이언트 코드/` | 윈도우 데스크탑에서 실행되는 관제 GUI, RTSP 수신, AI 분석, 복구 요청 코드입니다. |
| `서버 코드/` | FastAPI 기반 자원 모니터링 서버와 장애 대응 보조 코드입니다. |
| `requirements.txt` | 윈도우 데스크탑 관제 프로그램 실행에 필요한 주요 파이썬 패키지 목록입니다. |

주의할 점은 이 브랜치가 최신 `refactor` 브랜치처럼 `src/ai_cctv/edge_node`, `src/ai_cctv/ai_server` 구조로 정리되어 있지 않다는 점입니다.
따라서 이 문서에서는 `rtsp-review` 브랜치의 실제 폴더명을 기준으로 안내합니다.

## 4. 전체 실행 순서

권장 순서는 다음과 같습니다.

1. 윈도우 데스크탑과 라즈베리 파이를 같은 유선 또는 무선 네트워크에 연결합니다.
2. 라즈베리 파이에서 카메라 인식 여부를 확인합니다.
3. 라즈베리 파이에서 RTSP 송출 스크립트를 실행합니다.
4. 복구 기능까지 테스트하려면 라즈베리 파이에서 백업 복구 API를 별도 터미널로 실행합니다.
5. 윈도우 데스크탑에서 관제 GUI를 실행합니다.
6. GUI 설정에서 RTSP 주소를 `rtsp://<라즈베리파이IP>:8554/live`로 입력합니다.

## 5. 라즈베리 파이 실행 방법

### 5.1 카메라 확인

먼저 라즈베리 파이에서 카메라가 인식되는지 확인합니다.

```bash
rpicam-hello --list-cameras
```

카메라가 표시되지 않으면 코드 실행 전에 케이블 방향, 카메라 포트 체결 상태, `/boot/firmware/config.txt`의 카메라 설정을 먼저 확인해야 합니다.

### 5.2 시스템 패키지 설치

라즈베리 파이에서 다음 패키지를 설치합니다.

```bash
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav \
                    gstreamer1.0-rtsp libcamera-v4l2 python3-pip wget tar
```

`stream_and_record.sh`는 최초 실행 시 MediaMTX 실행 파일이 없으면 GitHub에서 MediaMTX를 내려받습니다.
따라서 최초 실행 시점에는 라즈베리 파이가 인터넷에 연결되어 있어야 합니다.

### 5.3 RTSP 송출 실행

라즈베리 파이에서 저장소 루트로 이동한 뒤 다음을 실행합니다.

```bash
cd ~/AI_CCTV/rtspv1.0
chmod +x stream_and_record.sh
./stream_and_record.sh
```

정상 실행되면 스크립트가 다음 형태의 주소를 출력합니다.

```text
RTSP Stream endpoint: rtsp://localhost:8554/live
```

이 주소의 `localhost`는 라즈베리 파이 자신을 의미합니다.
윈도우 데스크탑에서 접속할 때는 다음처럼 라즈베리 파이의 실제 IP를 넣어야 합니다.

```text
rtsp://<라즈베리파이IP>:8554/live
```

예시는 다음과 같습니다.

```text
rtsp://192.168.137.2:8554/live
```

### 5.4 백업 복구 API 실행

네트워크 장애 구간 복구까지 테스트하려면 라즈베리 파이에서 두 번째 터미널을 열고 다음을 실행합니다.

```bash
cd ~/AI_CCTV/rtspv1.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install fastapi uvicorn
python backup_api_server.py
```

정상 실행 시 복구 API는 다음 주소에서 대기합니다.

```text
http://<라즈베리파이IP>:8002/recover
```

수동 테스트 예시는 다음과 같습니다.

```bash
curl "http://<라즈베리파이IP>:8002/recover?start=2026-06-02T10:00:00&end=2026-06-02T10:00:20" -o recovered_backups.zip
```

주의할 점이 있습니다.
현재 `stream_and_record.sh`는 실행 위치 기준 `./backups`에 영상을 저장하지만, `backup_api_server.py`는 `~/backups`를 조회합니다.
복구 기능을 테스트하려면 두 경로가 같아야 합니다.

권장 임시 조치는 다음 둘 중 하나입니다.

| 방법 | 설명 |
| --- | --- |
| `~/backups`로 맞추기 | 라즈베리 파이 홈 디렉터리에서 `backups` 폴더를 만들고, 송출 스크립트의 백업 경로도 그 위치로 맞춥니다. |
| API 경로를 맞추기 | `backup_api_server.py`의 `BACKUP_DIR`를 실제 `.ts` 파일이 저장되는 `~/AI_CCTV/rtspv1.0/backups`로 맞춥니다. |

## 6. 윈도우 데스크탑 실행 방법

### 6.1 가상환경 생성

윈도우 PowerShell에서 저장소 루트로 이동한 뒤 실행합니다.

```powershell
py -3.11 -m venv venv311
.\venv311\Scripts\activate
python -m pip install --upgrade pip
```

Python 3.11 사용을 권장합니다.
이 브랜치의 AI 관련 패키지들은 Python 버전에 따라 설치 실패 가능성이 있습니다.

### 6.2 패키지 설치

```powershell
pip install -r requirements.txt
```

CUDA GPU를 사용할 경우 PyTorch는 PC의 CUDA 환경에 맞게 별도로 설치하는 편이 안전합니다.
예를 들어 CUDA 12.1 계열 휠을 쓰려면 다음과 같이 설치합니다.

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

CPU만 사용하는 경우 다음 설치도 가능하지만, YOLO와 VLM 분석 속도가 크게 느려질 수 있습니다.

```powershell
pip install torch torchvision torchaudio
```

### 6.3 관제 GUI 실행

이 브랜치에서 윈도우 관제 GUI의 진입점은 `클라이언트 코드/gui.py`입니다.

```powershell
cd "클라이언트 코드"
python gui.py
```

GUI가 열리면 설정 창에서 RTSP 사용을 선택하고 다음 형태의 주소를 입력합니다.

```text
rtsp://<라즈베리파이IP>:8554/live
```

예시는 다음과 같습니다.

```text
rtsp://192.168.137.2:8554/live
```

라즈베리 파이 없이 윈도우 내장 카메라만 간단히 확인하려면 다음 파일을 사용할 수 있습니다.

```powershell
cd "클라이언트 코드"
python cctv_gui.py
```

다만 `cctv_gui.py`는 RTSP 송수신 구조 전체를 검증하는 용도가 아니라 로컬 카메라 표시를 확인하는 단순 GUI에 가깝습니다.

## 7. 자원 모니터링 서버 실행

자원 모니터링 서버는 FastAPI로 구현되어 있으며, 실행하면 `/monitor/top`에서 JSON을 반환합니다.

```powershell
python "서버 코드\resource_monitor_server.py"
```

기본 포트는 `8001`입니다.
정상 실행 후 다음 주소로 확인할 수 있습니다.

```text
http://127.0.0.1:8001/monitor/top
```

다른 장치에서 접근하려면 방화벽과 네트워크 대역을 확인한 뒤 다음 형태로 접근합니다.

```text
http://<서버IP>:8001/monitor/top
```

반환되는 주요 값은 다음과 같습니다.

| 필드 | 의미 |
| --- | --- |
| `cpu.total_percent` | 전체 CPU 사용률입니다. |
| `memory.total_percent` | 전체 메모리 사용률입니다. |
| `process.pid` | 현재 모니터링 대상 프로세스 ID입니다. |
| `process.cpu_percent` | 대상 프로세스 CPU 사용률입니다. |
| `process.memory_percent` | 대상 프로세스 메모리 사용률입니다. |

## 8. 단독 RTSP 프로토타입 실행

`rtsp/` 폴더는 기능 이해용 단순 RTSP 프로토타입입니다.

라즈베리 파이 또는 리눅스 환경에서 서버를 실행하려면 다음 패키지가 필요합니다.

```bash
sudo apt update
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0
sudo apt install -y gir1.2-gst-rtsp-server-1.0 \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav
```

서버 실행:

```bash
cd ~/AI_CCTV/rtsp
python3 sender.py
```

`sender.py`는 `/stream` 경로로 송출하므로 주소는 다음 형태입니다.

```text
rtsp://<송출장치IP>:8554/stream
```

수신 테스트는 `rtsp/receiver.py`의 `RTSP_URL` 값을 수정한 뒤 실행합니다.

```bash
python receiver.py
```

운용 검증 목적이라면 이 프로토타입보다 `rtspv1.0/stream_and_record.sh` 사용을 권장합니다.
`rtspv1.0` 쪽이 MediaMTX 중계, 백업 저장, 장애 복구 흐름을 포함하기 때문입니다.

## 9. 네트워크 확인 명령

윈도우에서 라즈베리 파이까지 통신되는지 확인합니다.

```powershell
ping <라즈베리파이IP>
Test-NetConnection <라즈베리파이IP> -Port 8554
Test-NetConnection <라즈베리파이IP> -Port 8002
```

라즈베리 파이에서 윈도우까지 통신되는지 확인합니다.

```bash
ping -c 3 <윈도우IP>
```

RTSP 포트 `8554`가 열려 있어야 윈도우 GUI가 영상을 받을 수 있습니다.
백업 복구까지 테스트하려면 FastAPI 포트 `8002`도 열려 있어야 합니다.

## 10. 장애 상황별 점검

| 증상 | 확인할 내용 |
| --- | --- |
| `No cameras available` | 카메라 케이블 방향, 카메라 포트 체결, `rpicam-hello --list-cameras`, 카메라 설정을 확인합니다. |
| GUI에서 영상이 안 나옴 | RTSP 주소의 IP와 경로가 맞는지 확인합니다. `rtsp://<라즈베리파이IP>:8554/live` 형식이어야 합니다. |
| `Test-NetConnection` 실패 | 라즈베리 파이와 윈도우가 같은 네트워크인지, 방화벽이 포트를 막지 않는지 확인합니다. |
| 복구 ZIP이 404 | 백업 `.ts` 파일이 있는지, 요청 시간이 파일 수정 시간과 겹치는지, `BACKUP_DIR` 경로가 실제 저장 경로와 같은지 확인합니다. |
| OpenCV 수신이 멈춤 | 이 브랜치는 watchdog 재연결 로직이 있으므로 잠시 기다린 뒤 재연결 로그를 확인합니다. |
| MediaMTX 다운로드 실패 | 라즈베리 파이의 인터넷 연결과 DNS를 먼저 확인합니다. 최초 1회 다운로드가 필요합니다. |

## 11. refactor 브랜치와 다른 점

| 항목 | rtsp-review | refactor |
| --- | --- | --- |
| 폴더 구조 | `클라이언트 코드`, `서버 코드`, `rtspv1.0`처럼 실험 단계 폴더명이 남아 있습니다. | `src/ai_cctv/edge_node`, `src/ai_cctv/ai_server` 중심으로 역할이 분리되어 있습니다. |
| 실행 방식 | 개별 스크립트와 GUI 파일을 직접 실행합니다. | 패키지 진입점과 노드별 실행 흐름을 정리하는 방향입니다. |
| RTSP 송출 | `stream_and_record.sh`가 GStreamer와 MediaMTX를 직접 실행합니다. | 구조화된 edge node 실행기로 흡수하는 방향이 적합합니다. |
| 복구 API | FastAPI 서버가 별도 파일로 존재합니다. | edge node 내부 기능으로 통합하는 방향이 적합합니다. |
| 문서 상태 | 기존 문서 일부가 인코딩 깨짐을 포함합니다. | 국문 주석과 구조 문서 갱신을 목표로 정리 중입니다. |

## 12. 권장 테스트 시나리오

가장 기본적인 RTSP 테스트는 다음 순서로 진행합니다.

1. 라즈베리 파이에서 `rpicam-hello --list-cameras`로 카메라를 확인합니다.
2. 라즈베리 파이에서 `rtspv1.0/stream_and_record.sh`를 실행합니다.
3. 윈도우에서 `Test-NetConnection <라즈베리파이IP> -Port 8554`를 실행합니다.
4. 윈도우에서 `클라이언트 코드/gui.py`를 실행합니다.
5. GUI 설정에서 `rtsp://<라즈베리파이IP>:8554/live`를 입력합니다.
6. 영상이 표시되는지 확인합니다.

장애 복구까지 테스트하려면 다음을 추가합니다.

1. 라즈베리 파이에서 `backup_api_server.py`를 실행합니다.
2. 윈도우에서 RTSP 수신 중 네트워크를 잠시 끊습니다.
3. 다시 네트워크를 연결합니다.
4. GUI 로그 또는 복구 영상 저장 폴더를 확인합니다.

## 13. 현재 브랜치 기준 평가

잘된 점은 GStreamer, MediaMTX, RTSP 수신, 백업 복구 API가 기능 단위로 직접 검증 가능하다는 점입니다.
특히 실시간 송출과 로컬 백업을 동시에 처리하는 구조는 네트워크 장애를 고려한 CCTV 프로젝트 방향에 맞습니다.

부족한 점은 폴더 구조가 최신 프로젝트 구조와 다르고, `BACKUP_DIR` 같은 경로 설정이 파일마다 일관되지 않으며, 일부 IP와 URL 예시가 하드코딩되어 있다는 점입니다.
따라서 이 브랜치는 최종 배포 구조라기보다 RTSP 송출과 장애 복구 기능을 검증하기 위한 참고 브랜치로 보는 것이 적절합니다.
