# develop 브랜치 실행 가이드

이 문서는 `develop` 브랜치를 처음 실행하는 사람을 위한 안내입니다. 현재 `develop`은 `pyproject.toml` 기반 패키지 구조가 아니라, 루트의 `requirements.txt`와 개별 Python 스크립트를 직접 실행하는 구조입니다.

## 1. 전체 구성

| 구분 | 위치 | 역할 | 실행 대상 |
|---|---|---|---|
| AI 관제 UI | `클라이언트 코드/gui.py` | Windows PC에서 영상 수신, YOLO/VLM 분석, 녹화, 클립, Discord 알림, 리소스 모니터링 UI를 실행합니다. | Windows AI 서버 |
| 간단 웹캠 UI 데모 | `클라이언트 코드/cctv_gui.py` | PC 내장/USB 카메라만 표시하는 단순 UI 데모입니다. | Windows 테스트 |
| 리소스 모니터 API | `서버 코드/resource_monitor_server.py` | FastAPI로 CPU/메모리/프로세스 자원 사용률 JSON을 제공합니다. | 별도 서버 또는 테스트 PC |
| RTSP 송출/백업 | `rtspv1.0/stream_and_record.sh` | 라즈베리파이 카메라 영상을 GStreamer로 캡처하고 MediaMTX를 통해 RTSP로 송출하며 10초 단위 백업을 저장합니다. | Raspberry Pi |
| 백업 복구 API | `rtspv1.0/backup_api_server.py` | 네트워크 장애 구간의 라즈베리파이 백업 `.ts` 파일을 ZIP으로 반환합니다. | Raspberry Pi |
| 구 RTSP 예제 | `rtsp/` | 학습/초기 테스트용 RTSP 예제입니다. 현재 메인 실행 경로는 아닙니다. | 참고용 |

## 2. Windows AI 서버 실행

### 2.1 저장소와 브랜치 준비

```powershell
git clone https://github.com/taegyu-heo-bigstar/AI_CCTV.git
cd AI_CCTV
git checkout develop
git pull --ff-only origin develop
```

이미 저장소가 있다면 `git checkout develop` 후 `git pull --ff-only origin develop`만 실행하면 됩니다.

### 2.2 Python 가상환경 생성

`develop`의 README는 Python 3.11 사용을 전제로 합니다. Windows에서는 다음 방식이 가장 안정적입니다.

```powershell
py -3.11 -m venv venv311
.\venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

`python` 명령이 Microsoft Store alias로 잡혀 이상하게 동작한다면 `py` 명령을 사용하십시오.

### 2.3 기본 패키지 설치

```powershell
python -m pip install -r requirements.txt
```

`requirements.txt`에는 PyQt5, OpenCV, Ultralytics, Transformers, FastAPI, psutil, Discord 관련 패키지가 포함되어 있습니다.

### 2.4 PyTorch 설치

PyTorch는 PC의 CUDA/드라이버 상태에 따라 별도 설치하는 편이 안전합니다. NVIDIA GPU와 CUDA 12.1 계열을 사용할 경우:

```powershell
python -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

GPU를 사용하지 않는 CPU 테스트라면:

```powershell
python -m pip install torch torchvision torchaudio
```

설치 확인:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.version.cuda)"
```

### 2.5 모델 및 설정 파일

YOLO 분석을 켜려면 루트 디렉터리에 다음 파일이 있어야 합니다.

```text
yolo26s.pt
```

VLM 분석을 켜면 `Qwen/Qwen2.5-VL-3B-Instruct` 모델을 로드합니다. 최초 실행 시 Hugging Face에서 모델을 내려받을 수 있으므로 인터넷 연결과 충분한 디스크 공간이 필요합니다.

Discord 알림을 사용하려면 루트의 `.proj_env`에 다음 값을 설정합니다.

```text
DISCORD_BOT_TOKEN=replace-me
DISCORD_CHANNEL_ID=123456789012345678
```

Discord 알림을 쓰지 않거나 VLM을 끄고 실행한다면 실제 토큰이 없어도 UI 실행 자체는 가능합니다.

### 2.6 AI 관제 UI 실행

반드시 저장소 루트에서 실행하십시오.

```powershell
python "클라이언트 코드\gui.py"
```

UI가 뜨면 다음 순서로 실행합니다.

1. `설정` 버튼을 누릅니다.
2. `웹캠 사용` 또는 `RTSP 사용`을 선택합니다.
3. 웹캠 테스트는 카메라 번호에 `0`을 입력합니다.
4. 라즈베리파이 RTSP를 사용할 경우 `rtsp://라즈베리파이IP:8554/live`를 입력합니다.
5. 필요에 따라 `YOLO 사람 탐지/추적 사용`, `VLM 의상 분석 사용`을 켜거나 끕니다.
6. 저장 기능을 사용하려면 `저장 설정`에서 저장 위치를 선택합니다.
7. `START`를 눌러 영상 수신을 시작합니다.

### 2.7 간단 웹캠 데모 실행

AI 분석 없이 PC 카메라 표시만 확인하려면 다음을 실행합니다.

```powershell
python "클라이언트 코드\cctv_gui.py"
```

이 파일은 메인 관제 UI가 아니라 OpenCV 카메라 표시용 데모입니다.

## 3. Raspberry Pi RTSP 송출 실행

### 3.1 시스템 패키지 설치

라즈베리파이에서 실행합니다.

```bash
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav \
                    gstreamer1.0-rtsp libcamera-v4l2 python3-pip wget tar
```

카메라 확인:

```bash
rpicam-hello --list-cameras
```

카메라가 보이지 않으면 케이블 방향, 카메라 커넥터 체결, `/boot/firmware/config.txt`의 `camera_auto_detect=1` 설정, 재부팅 여부를 확인하십시오.

### 3.2 RTSP 송출 시작

`stream_and_record.sh`는 실행 위치 기준 `./backups`에 백업 조각을 저장합니다. 백업 API와 경로를 맞추기 위해 `rtspv1.0` 디렉터리 안에서 실행하십시오.

```bash
cd ~/AI_CCTV/rtspv1.0
chmod +x stream_and_record.sh
./stream_and_record.sh
```

스크립트는 필요한 경우 MediaMTX를 내려받고, GStreamer 파이프라인을 시작합니다. PC에서 접속할 주소는 다음 형태입니다.

```text
rtsp://라즈베리파이IP:8554/live
```

라즈베리파이 IP는 다음 명령으로 확인할 수 있습니다.

```bash
hostname -I
```

## 4. Raspberry Pi 백업 복구 API 실행

네트워크 장애 복구 기능을 테스트하려면 RTSP 송출과 별도 터미널에서 백업 API 서버를 실행합니다.

```bash
cd ~/AI_CCTV
python3 -m venv .rpi_api_env
source .rpi_api_env/bin/activate
python -m pip install --upgrade pip
python -m pip install -r rtspv1.0/requirements.txt
python rtspv1.0/backup_api_server.py
```

API 서버는 `0.0.0.0:8002`에서 실행됩니다. Windows AI 서버는 RTSP 주소의 호스트를 기준으로 다음 복구 URL을 만듭니다.

```text
http://라즈베리파이IP:8002/recover
```

백업 파일은 `rtspv1.0/backups` 아래의 `.ts` 파일을 대상으로 합니다.

## 5. 리소스 모니터링 API 실행

FastAPI 기반 리소스 모니터링 서버는 다음과 같이 실행합니다.

```powershell
python "서버 코드\resource_monitor_server.py"
```

기본 포트는 `8001`입니다. 단독 호출 테스트:

```powershell
python "클라이언트 코드\resource_monitor_client.py"
```

다른 주소를 조회하려면 환경변수를 지정합니다.

```powershell
$env:RESOURCE_MONITOR_SERVER_URL="http://서버IP:8001"
python "클라이언트 코드\resource_monitor_client.py"
```

현재 `클라이언트 코드/resource_monitor_window.py`의 기본 화면은 사용자 PC 자원 정보를 로컬에서 직접 수집합니다. 스마트 CCTV 쪽 모니터링 화면은 연결 대기 표시 중심입니다.

## 6. 권장 실행 순서

라즈베리파이와 Windows AI 서버를 함께 테스트할 때는 다음 순서가 가장 명확합니다.

1. 라즈베리파이에서 `rtspv1.0/stream_and_record.sh` 실행
2. 라즈베리파이에서 `rtspv1.0/backup_api_server.py` 실행
3. Windows에서 `python "클라이언트 코드\gui.py"` 실행
4. UI 설정에서 `RTSP 사용` 선택
5. `rtsp://라즈베리파이IP:8554/live` 입력
6. 저장 경로 선택
7. `START` 실행

PC 단독 테스트는 라즈베리파이 없이 다음만 실행하면 됩니다.

```powershell
python "클라이언트 코드\gui.py"
```

설정에서 `웹캠 사용`, 카메라 번호 `0`을 선택하십시오.

## 7. 자주 발생하는 문제

### `ai-cctv-*` 명령이 인식되지 않음

`develop` 브랜치는 패키지 엔트리포인트가 없습니다. `ai-cctv-server`, `ai-cctv-edge` 같은 명령이 아니라 Python 파일을 직접 실행해야 합니다.

```powershell
python "클라이언트 코드\gui.py"
```

### PyQt5 platform plugin 오류

`클라이언트 코드/gui.py`는 시작 시 Qt plugin 경로를 `C:\qt_plugins`로 설정합니다. 해당 경로가 없거나 맞지 않으면 PyQt5의 `platforms` 플러그인 오류가 날 수 있습니다. 이 경우 PyQt5가 설치된 실제 plugin 경로를 확인해 `C:\qt_plugins`에 맞추거나, 코드의 `QT_QPA_PLATFORM_PLUGIN_PATH`, `QT_PLUGIN_PATH` 설정을 환경에 맞게 조정해야 합니다.

### RTSP가 열리지 않음

라즈베리파이에서 다음을 확인하십시오.

```bash
hostname -I
ss -lntp | grep 8554
```

Windows에서 다음 형태의 주소를 UI에 입력해야 합니다.

```text
rtsp://라즈베리파이IP:8554/live
```

### YOLO 모델 파일 오류

루트에 `yolo26s.pt`가 없으면 YOLO 초기화가 실패할 수 있습니다. 메인 UI는 실패 시 CCTV 모드로 전환하려고 하지만, 정상 AI 분석을 위해서는 모델 파일을 루트에 두십시오.

### VLM 로딩이 오래 걸림

VLM은 Qwen 계열 모델을 사용하므로 최초 다운로드와 로딩에 시간이 걸립니다. 단순 영상 수신 테스트는 설정에서 VLM을 끄고 실행하는 것이 좋습니다.

