# AI_CCTV rtsp-review 브랜치 설치 및 실행 안내

이 문서는 AI_CCTV 프로젝트를 처음 보는 사람이 `rtsp-review` 브랜치에서 필요한 파일, 패키지, 설치 순서, 실행 방법을 따라 할 수 있도록 정리한 문서입니다.

`rtsp-review` 브랜치의 목표는 라즈베리 파이 카메라 영상을 RTSP로 송출하고, 윈도우 데스크탑 관제 프로그램에서 해당 영상을 수신해 AI 분석과 복구 기능을 테스트하는 것입니다.

## 1. 전체 구성

프로젝트는 크게 두 장치로 나뉩니다.

| 장치 | 역할 | 실행 위치 |
| --- | --- | --- |
| 라즈베리 파이 | 카메라 영상 촬영, RTSP 송출, 장애 구간 백업 저장, 백업 복구 API 제공 | `rtspv1.0/` |
| 윈도우 데스크탑 | RTSP 영상 수신, GUI 표시, AI 분석, 장애 구간 복구 요청 | `클라이언트 코드/` |

기본 영상 흐름은 다음과 같습니다.

```text
라즈베리 파이 카메라
  -> GStreamer
  -> MediaMTX
  -> rtsp://라즈베리파이IP:8554/live
  -> 윈도우 관제 GUI
```

복구 기능을 켜면 다음 흐름도 추가됩니다.

```text
라즈베리 파이 로컬 백업 파일
  -> FastAPI 복구 서버
  -> http://라즈베리파이IP:8002/recover
  -> 윈도우 관제 GUI가 ZIP 다운로드
  -> ffmpeg로 복구 영상 병합
```

## 2. 주요 파일과 역할

| 파일 | 실행 장치 | 역할 | 필요한 이유 |
| --- | --- | --- | --- |
| `requirements.txt` | 윈도우 데스크탑 | GUI, AI 분석, RTSP 수신, 복구 요청에 필요한 파이썬 패키지 목록 | 윈도우 관제 프로그램 실행에 필요합니다. |
| `rtspv1.0/requirements.txt` | 라즈베리 파이 | RTSP 수신 테스트와 FastAPI 복구 서버에 필요한 최소 패키지 목록 | 라즈베리 파이에서 복구 API를 실행할 때 필요합니다. |
| `rtspv1.0/stream_and_record.sh` | 라즈베리 파이 | 카메라 영상을 GStreamer로 읽고 MediaMTX를 통해 RTSP로 송출하며, 동시에 10초 단위 백업을 저장 | 실제 엣지 노드 송출 테스트의 핵심 파일입니다. |
| `rtspv1.0/backup_api_server.py` | 라즈베리 파이 | 장애 시간 구간에 해당하는 백업 `.ts` 파일을 ZIP으로 반환하는 FastAPI 서버 | 네트워크 장애 후 빠진 영상을 복구하기 위해 필요합니다. |
| `rtspv1.0/rtsp_receiver.py` | 테스트 장치 | RTSP 스트림을 단독으로 받아 보는 테스트 코드 | GUI 실행 전 RTSP 송출이 정상인지 확인할 수 있습니다. |
| `클라이언트 코드/gui.py` | 윈도우 데스크탑 | 관제 GUI 메인 실행 파일 | 실제 윈도우 관제 프로그램의 진입점입니다. |
| `클라이언트 코드/settings_window.py` | 윈도우 데스크탑 | 카메라 소스, RTSP 주소 등 설정 UI | 사용자가 RTSP 주소를 입력할 때 사용됩니다. |
| `클라이언트 코드/video_stream.py` | 윈도우 데스크탑 | 로컬 카메라 또는 RTSP 입력을 공통 영상 스트림으로 처리 | GUI가 영상 소스 종류에 상관없이 프레임을 읽도록 합니다. |
| `클라이언트 코드/rtsp_receiver.py` | 윈도우 데스크탑 | RTSP 연결, 재연결, 프레임 수신 watchdog 처리 | RTSP 연결이 끊기거나 멈췄을 때 GUI가 오래 멈추는 문제를 줄입니다. |
| `클라이언트 코드/network_recovery_manager.py` | 윈도우 데스크탑 | 라즈베리 파이에 복구 API 요청을 보내고 ZIP을 받아 ffmpeg로 병합 | 장애 구간 복구 영상을 만들기 위해 필요합니다. |
| `서버 코드/resource_monitor_server.py` | 선택 실행 | CPU, 메모리, 프로세스 사용량을 JSON으로 반환하는 FastAPI 서버 | 자원 모니터링 기능 테스트에 사용합니다. |
| `클라이언트 코드/resource_monitor_client.py` | 선택 실행 | 자원 모니터링 서버에 HTTP 요청을 보내 JSON을 받음 | 모니터링 서버 응답 확인에 사용합니다. |
| `rtsp/sender.py`, `rtsp/receiver.py` | 테스트 장치 | 단순 RTSP 송수신 프로토타입 | `rtspv1.0` 이전의 기본 RTSP 개념 검증용입니다. |

## 3. 필요한 준비물

### 3.1 공통 준비물

| 준비물 | 이유 |
| --- | --- |
| Git | 저장소를 내려받고 `rtsp-review` 브랜치로 전환하기 위해 필요합니다. |
| 같은 네트워크 | 윈도우 데스크탑이 라즈베리 파이의 RTSP 주소와 복구 API 주소에 접근해야 합니다. |
| 라즈베리 파이 IP 주소 | 윈도우 GUI에서 `rtsp://라즈베리파이IP:8554/live`를 입력해야 합니다. |

### 3.2 라즈베리 파이 준비물

| 준비물 | 이유 |
| --- | --- |
| Raspberry Pi OS 또는 Debian 계열 리눅스 | `stream_and_record.sh`가 리눅스, GStreamer, libcamera 기반으로 동작합니다. |
| 라즈베리 파이 카메라 | 실제 영상을 촬영하기 위해 필요합니다. |
| 인터넷 연결 | 최초 실행 시 패키지 설치와 MediaMTX 다운로드에 필요합니다. |
| GStreamer 패키지 | 카메라 입력, H.264 인코딩, RTMP 송출, 파일 백업에 필요합니다. |
| MediaMTX | RTMP 입력을 RTSP 스트림으로 변환해 주는 중계 서버입니다. 스크립트가 최초 1회 자동 다운로드합니다. |
| Python 3, pip, venv | 백업 복구 API 서버를 실행하기 위해 필요합니다. |

### 3.3 윈도우 데스크탑 준비물

| 준비물 | 이유 |
| --- | --- |
| Python 3.11 권장 | PyQt5, OpenCV, AI 패키지 설치 안정성을 위해 권장합니다. |
| pip | 파이썬 패키지 설치에 필요합니다. |
| ffmpeg | 복구 ZIP 안의 `.ts` 파일을 하나의 복구 영상으로 병합할 때 필요합니다. |
| NVIDIA GPU와 CUDA 지원 PyTorch 선택 | YOLO, VLM 분석 속도를 높이고 싶을 때 필요합니다. CPU 실행도 가능하지만 느립니다. |

## 4. 저장소 준비

처음 받는 경우 다음 명령을 사용합니다.

```powershell
git clone https://github.com/taegyu-heo-bigstar/AI_CCTV.git
cd AI_CCTV
git switch rtsp-review
```

이미 저장소가 있다면 다음처럼 브랜치만 맞춥니다.

```powershell
cd AI_CCTV
git fetch origin
git switch rtsp-review
git pull origin rtsp-review
```

## 5. 라즈베리 파이 설치

라즈베리 파이에서 실행합니다.

### 5.1 시스템 패키지 설치

```bash
sudo apt update
sudo apt install -y rpicam-apps python3-pip python3-venv wget tar \
                    gstreamer1.0-tools gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav \
                    gstreamer1.0-rtsp libcamera-v4l2
```

각 패키지가 필요한 이유는 다음과 같습니다.

| 패키지 | 이유 |
| --- | --- |
| `rpicam-apps` | 카메라 인식 여부를 `rpicam-hello`로 확인하기 위해 필요합니다. |
| `gstreamer1.0-*` | 카메라 영상을 읽고 인코딩하고 RTMP로 송출하기 위해 필요합니다. |
| `libcamera-v4l2` | 라즈베리 파이 카메라 입력을 libcamera 기반으로 다루기 위해 필요합니다. |
| `python3-pip`, `python3-venv` | 백업 복구 API용 파이썬 환경을 만들기 위해 필요합니다. |
| `wget`, `tar` | MediaMTX 압축 파일을 내려받고 풀기 위해 필요합니다. |

### 5.2 카메라 인식 확인

```bash
rpicam-hello --list-cameras
```

정상이라면 카메라 모델과 해상도 목록이 출력됩니다.
`No cameras available!`가 나오면 코드 실행 전에 카메라 케이블 방향, 포트 체결, 전원, 카메라 설정을 먼저 확인해야 합니다.

## 6. 라즈베리 파이에서 RTSP 송출 실행

라즈베리 파이에서 저장소가 `~/AI_CCTV`에 있다고 가정합니다.

복구 기능까지 같이 테스트하려면 홈 디렉터리에서 스크립트를 실행하는 것을 권장합니다.
현재 코드 기준 `stream_and_record.sh`는 실행 위치 기준 `./backups`에 백업을 저장하고, `backup_api_server.py`는 `~/backups`를 읽습니다.
따라서 홈 디렉터리에서 실행하면 두 경로가 자연스럽게 `~/backups`로 맞춰집니다.

```bash
cd ~
bash ~/AI_CCTV/rtspv1.0/stream_and_record.sh
```

정상 실행되면 다음과 비슷한 문장이 출력됩니다.

```text
RTSP Stream endpoint: rtsp://localhost:8554/live
```

여기서 `localhost`는 라즈베리 파이 자신을 뜻합니다.
윈도우 데스크탑에서 접속할 때는 반드시 라즈베리 파이의 실제 IP로 바꿔야 합니다.

예시는 다음과 같습니다.

```text
rtsp://192.168.137.2:8554/live
```

라즈베리 파이 IP는 다음 명령으로 확인할 수 있습니다.

```bash
hostname -I
ip addr show eth0
```

무선 네트워크를 쓰는 경우에는 `eth0` 대신 `wlan0`를 확인합니다.

## 7. 라즈베리 파이에서 백업 복구 API 실행

복구 기능을 테스트하려면 RTSP 송출 터미널은 그대로 둔 상태에서, 라즈베리 파이에 새 SSH 터미널을 열어 다음을 실행합니다.

```bash
cd ~/AI_CCTV/rtspv1.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python backup_api_server.py
```

정상 실행되면 복구 API는 다음 주소에서 대기합니다.

```text
http://라즈베리파이IP:8002/recover
```

수동 확인 예시는 다음과 같습니다.

```bash
curl "http://라즈베리파이IP:8002/recover?start=2026-06-02T10:00:00&end=2026-06-02T10:00:20" -o recovered_backups.zip
```

해당 시간대에 백업 파일이 없으면 404 응답이 정상적으로 나올 수 있습니다.

## 8. 윈도우 데스크탑 설치

윈도우 PowerShell에서 실행합니다.

### 8.1 가상환경 생성

```powershell
cd AI_CCTV
py -3.11 -m venv venv311
.\venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

만약 `py -3.11`이 동작하지 않으면 다음을 확인합니다.

```powershell
py --version
py -0p
```

### 8.2 파이썬 패키지 설치

```powershell
pip install -r requirements.txt
```

이 명령으로 설치되는 주요 패키지와 이유는 다음과 같습니다.

| 패키지 | 이유 |
| --- | --- |
| `PyQt5` | 관제 GUI 실행에 필요합니다. |
| `opencv-python` | 로컬 카메라와 RTSP 영상 프레임 수신에 필요합니다. |
| `ultralytics` | YOLO 기반 사람 탐지에 필요합니다. |
| `transformers`, `qwen-vl-utils`, `accelerate` | Qwen VLM 기반 상황 분석에 필요합니다. |
| `requests` | 라즈베리 파이 복구 API와 모니터링 API 호출에 필요합니다. |
| `fastapi`, `uvicorn` | 자원 모니터링 서버를 윈도우에서 실행할 때 필요합니다. |
| `psutil` | CPU, 메모리 사용률 수집에 필요합니다. |
| `discord.py` | 이상 상황 알림을 Discord로 보낼 때 필요합니다. |

### 8.3 PyTorch 설치

AI 분석을 사용할 경우 PyTorch가 필요합니다.
GPU를 사용할 수 있다면 CUDA 버전에 맞는 PyTorch를 설치합니다.

예시는 CUDA 12.1 계열입니다.

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

GPU를 사용하지 않는다면 CPU 버전을 설치할 수 있습니다.

```powershell
pip install torch torchvision torchaudio
```

설치 확인:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"
```

### 8.4 ffmpeg 설치 확인

복구 기능은 `.ts` 조각을 하나의 영상으로 병합할 때 `ffmpeg` 실행 파일을 사용합니다.

```powershell
ffmpeg -version
```

명령이 인식되지 않으면 ffmpeg를 설치하고 PATH에 추가해야 합니다.

## 9. 윈도우 데스크탑에서 관제 GUI 실행

라즈베리 파이에서 `stream_and_record.sh`가 실행 중인 상태에서 윈도우 PowerShell을 엽니다.

```powershell
cd AI_CCTV
.\venv311\Scripts\Activate.ps1
cd "클라이언트 코드"
python gui.py
```

GUI가 열리면 설정 창에서 RTSP 사용을 선택하고 다음 형식의 주소를 입력합니다.

```text
rtsp://라즈베리파이IP:8554/live
```

예시:

```text
rtsp://192.168.137.2:8554/live
```

이 주소는 라즈베리 파이 스크립트가 출력하는 `rtsp://localhost:8554/live`에서 `localhost`만 라즈베리 파이 IP로 바꾼 것입니다.

## 10. 윈도우에서 로컬 카메라만 테스트하기

라즈베리 파이 없이 윈도우 데스크탑 자체 카메라만 확인하려면 다음을 실행합니다.

```powershell
cd AI_CCTV
.\venv311\Scripts\Activate.ps1
cd "클라이언트 코드"
python cctv_gui.py
```

이 파일은 RTSP 송출, 복구 API, 라즈베리 파이 연동을 검증하는 용도가 아닙니다.
단순히 윈도우 카메라와 GUI 표시가 가능한지 확인하는 용도입니다.

## 11. 자원 모니터링 서버 실행

자원 모니터링 기능을 확인하려면 다음 파일을 실행합니다.

```powershell
cd AI_CCTV
.\venv311\Scripts\Activate.ps1
python "서버 코드\resource_monitor_server.py"
```

기본 주소는 다음과 같습니다.

```text
http://127.0.0.1:8001/monitor/top
```

클라이언트 코드에서 요청을 보내 확인하려면 다음을 실행합니다.

```powershell
cd "클라이언트 코드"
python resource_monitor_client.py
```

다른 장치의 모니터링 서버를 조회하려면 환경변수로 서버 주소를 지정할 수 있습니다.

```powershell
$env:RESOURCE_MONITOR_SERVER_URL="http://서버IP:8001"
python resource_monitor_client.py
```

## 12. RTSP 단독 테스트

GUI를 켜기 전에 RTSP 송출만 확인하고 싶다면 다음 방법을 사용할 수 있습니다.

### 12.1 라즈베리 파이 송출 확인

윈도우에서 포트가 열려 있는지 확인합니다.

```powershell
Test-NetConnection 라즈베리파이IP -Port 8554
```

`TcpTestSucceeded : True`가 나오면 RTSP 포트에 접근할 수 있습니다.

### 12.2 OpenCV 수신 테스트

`rtspv1.0/rtsp_receiver.py`의 `RTSP_URL` 값을 실제 주소로 바꾼 뒤 실행합니다.

```powershell
python rtspv1.0\rtsp_receiver.py
```

예시 주소:

```text
rtsp://192.168.137.2:8554/live
```

## 13. 실행 순서 요약

처음 실행한다면 다음 순서대로 진행합니다.

1. 라즈베리 파이와 윈도우 데스크탑을 같은 네트워크에 연결합니다.
2. 라즈베리 파이에서 `rpicam-hello --list-cameras`로 카메라 인식을 확인합니다.
3. 라즈베리 파이에서 `bash ~/AI_CCTV/rtspv1.0/stream_and_record.sh`를 실행합니다.
4. 라즈베리 파이에 새 터미널을 열고 `python backup_api_server.py`를 실행합니다.
5. 윈도우에서 `Test-NetConnection 라즈베리파이IP -Port 8554`로 RTSP 포트를 확인합니다.
6. 윈도우에서 `클라이언트 코드/gui.py`를 실행합니다.
7. GUI 설정에서 `rtsp://라즈베리파이IP:8554/live`를 입력합니다.
8. 영상 표시와 AI 분석 동작을 확인합니다.

## 14. 자주 발생하는 문제

| 문제 | 원인 | 해결 |
| --- | --- | --- |
| `rpicam-hello: command not found` | `rpicam-apps`가 설치되지 않음 | `sudo apt install -y rpicam-apps`를 실행합니다. |
| `No cameras available!` | 카메라가 인식되지 않음 | 케이블 방향, 포트 체결, 카메라 설정, 재부팅을 확인합니다. |
| MediaMTX 다운로드 실패 | 라즈베리 파이에 인터넷 연결이 없음 | DNS, 라우팅, 유선 또는 무선 인터넷 연결을 확인합니다. |
| 윈도우 GUI에서 영상이 안 나옴 | RTSP 주소가 잘못됨 | `localhost`가 아니라 `라즈베리파이IP`를 넣었는지 확인합니다. |
| `Test-NetConnection` 실패 | 네트워크 또는 방화벽 문제 | 같은 네트워크인지, 라즈베리 파이에서 스크립트가 실행 중인지, 포트 `8554`가 열려 있는지 확인합니다. |
| 복구 API가 404 반환 | 해당 시간대 백업 파일이 없음 | 송출 스크립트 실행 위치와 `~/backups`에 `.ts` 파일이 생성되는지 확인합니다. |
| 복구 병합 실패 | `ffmpeg`가 설치되지 않음 | 윈도우에서 `ffmpeg -version`이 동작하도록 설치하고 PATH를 설정합니다. |
| PyTorch DLL 오류 | PyTorch, CUDA, 드라이버 조합 문제 | `python -c "import torch"`가 먼저 성공하는지 확인하고, CUDA에 맞는 PyTorch를 다시 설치합니다. |

## 15. 처음 보는 사람이 기억해야 할 핵심

가장 중요한 실행 주소는 하나입니다.

```text
rtsp://라즈베리파이IP:8554/live
```

라즈베리 파이에서는 이 주소를 만들기 위해 `stream_and_record.sh`를 실행합니다.
윈도우에서는 이 주소를 GUI 설정에 입력합니다.
복구 기능까지 확인하려면 라즈베리 파이에서 `backup_api_server.py`도 같이 실행합니다.
