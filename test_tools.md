# 테스트 도구 사용법

이 문서는 AI_CCTV 프로젝트에서 사용하는 테스트 도구의 역할과 실행 방법을 정리합니다.
테스트 도구는 production 코드와 구분해서 사용하며, 실제 Edge node 없이 AI server 기능을 확인할 때는 `pseudo_edge_node`를 우선 사용합니다.

## 테스트 도구 분류

| 구분 | 경로 | 목적 | 권장 사용 시점 |
|---|---|---|---|
| 자동 테스트 | `tests/test_project_structure.py` | 구조, 설정, OS guard, RTSP/MQTT/복구 일부 동작 검증 | 코드 수정 후 기본 회귀 확인 |
| Pseudo Edge node | `src/ai_cctv/pseudo_edge_node/` | Windows에서 Edge node 없이 RTSP/MQTT/복구 endpoint를 흉내 냄 | AI server UI와 연결 흐름 통합 테스트 |
| Mock MQTT publisher | `tools/mock_edge_mqtt_publisher.py` | MQTT 상태 조회 UI만 수동 검증 | 외부 MQTT broker와 상태 조회 창만 따로 확인 |

## 자동 테스트 실행

PowerShell에서 프로젝트 루트로 이동한 뒤 실행합니다.

```powershell
$env:PYTHONPATH="src"
py -m unittest discover -s tests
```

컴파일 수준의 문법 검사는 다음 명령으로 확인합니다.

```powershell
$env:PYTHONPATH="src"
py -m compileall src tests tools
```

## Pseudo Edge node 실행

`ai-cctv-pseudo-edge`는 Windows에서 실제 Raspberry Pi 없이 AI server의 Edge node 연결 흐름을 테스트하기 위한 도구입니다.
RTSP 포트 stub, 최소 MQTT broker, backup recovery HTTP endpoint를 함께 실행합니다.

설치형 명령으로 실행하려면 먼저 editable install을 수행합니다.

```powershell
py -m pip install -e ".[pseudo-edge-node]"
ai-cctv-pseudo-edge
```

설치형 명령이 아직 PATH에 잡히지 않았다면 모듈 방식으로 실행합니다.

```powershell
$env:PYTHONPATH="src"
py -m ai_cctv.pseudo_edge_node.main
```

실행하면 AI server 연결 UI에 붙여 넣을 수 있는 연결 정보가 표준 출력으로 표시됩니다.
AI server 실행 시 Edge node 연결 입력 창에 해당 값을 붙여 넣으면 pseudo mode로 연결됩니다.

주요 옵션은 다음과 같습니다.

```powershell
py -m ai_cctv.pseudo_edge_node.main --host 127.0.0.1 --rtsp-port 8554 --mqtt-port 1883 --recovery-port 8002
```

주의할 점은 pseudo RTSP가 실제 영상 스트림을 송출하는 MediaMTX/GStreamer 대체물이 아니라는 것입니다.
AI server는 pseudo flag가 켜진 경우 내부 synthetic frame 경로로 프레임을 생성합니다.

## Mock MQTT publisher 실행

`tools/mock_edge_mqtt_publisher.py`는 Edge node 상태 조회 UI만 빠르게 확인하기 위한 수동 도구입니다.
별도의 MQTT broker가 먼저 실행되어 있어야 합니다.

```powershell
$env:PYTHONPATH="src"
py tools/mock_edge_mqtt_publisher.py --host 127.0.0.1 --port 1883 --topic ai-cctv/edge-node/status
```

기본 동작은 10회 정상 상태 JSON을 발행한 뒤 침묵하는 것입니다.
이 동작으로 상태 조회 UI의 `연결됨`, `조회중`, `연결실패` 전환을 확인할 수 있습니다.

발행 횟수와 간격은 옵션으로 바꿀 수 있습니다.

```powershell
py tools/mock_edge_mqtt_publisher.py --max-messages 3 --interval 1
```

## AI server 단독 테스트 기준

실제 Edge node 없이 테스트하려면 다음 두 방식 중 하나를 사용합니다.

| 방식 | 확인 가능한 기능 | 한계 |
|---|---|---|
| Windows 로컬 카메라 | AI 분석, UI start/stop, local camera 입력 | RTSP, MQTT, backup recovery는 확인 불가 |
| Pseudo Edge node | Edge 연결 UI, MQTT 상태 조회, pseudo frame, backup recovery endpoint | 실제 Raspberry Pi 카메라, GStreamer, MediaMTX 송출 품질은 확인 불가 |

## 파일 배치 원칙

테스트 보조 도구는 `tools/` 아래에 둡니다.
자동화된 회귀 테스트는 `tests/` 아래에 둡니다.
`src/` 아래에는 runtime에서 import되는 production 모듈만 둡니다.
따라서 `src/` 내부 파일명에는 `_test.py`를 사용하지 않습니다.
