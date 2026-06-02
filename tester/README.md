# Tester 사용법

이 디렉터리는 AI_CCTV 프로젝트의 테스트 전용 자산을 모아 둔 위치입니다.
`src/ai_cctv`에는 운영 런타임만 두고, 테스트 도구와 테스트 문서는 모두 `tester/` 아래에서 관리합니다.

## 구성

| 구분 | 경로 | 목적 |
|---|---|---|
| 자동 회귀 테스트 | `tester/tests/test_project_structure.py` | 구조, 설정, OS guard, RTSP/MQTT/복구 일부 동작 검증 |
| 테스트 Edge 실행체 | `tester/pseudo_edge_node/` | 실제 Raspberry Pi 없이 연결값, MQTT 상태, 복구 API를 흉내 냄 |
| MQTT 상태 publisher | `tester/tools/mock_edge_mqtt_publisher.py` | 외부 MQTT broker에 상태 JSON을 발행해 상태 조회 UI만 수동 검증 |

## 자동 테스트 실행

PowerShell에서 프로젝트 루트로 이동한 뒤 실행합니다.

```powershell
$env:PYTHONPATH="src;."
py -m unittest discover -s tester/tests -t .
```

문법 검사는 다음 명령으로 확인합니다.

```powershell
$env:PYTHONPATH="src;."
py -m compileall src main.py tester
```

## 테스트 Edge 실행체

`tester/pseudo_edge_node`는 AI server가 요구하는 연결값을 출력하고, MQTT 상태 broker와 백업 복구 HTTP endpoint를 제공합니다.
AI server에는 테스트 여부를 알리는 flag를 전달하지 않으며, 출력값은 일반 Edge node 연결 블록과 같은 형식입니다.

```powershell
$env:PYTHONPATH="src;."
py -m tester.pseudo_edge_node.main
```

주요 옵션은 다음과 같습니다.

```powershell
py -m tester.pseudo_edge_node.main --host 127.0.0.1 --rtsp-port 8554 --mqtt-port 1883 --recovery-port 8002
```

주의: 이 실행체의 RTSP 포트는 연결 검증용 stub입니다. 실제 영상 프레임을 송출하지 않으므로 영상 분석까지 검증하려면 실제 Edge node 또는 Windows 로컬 카메라 모드를 사용해야 합니다.

## MQTT 상태 Publisher

외부 MQTT broker가 이미 실행 중일 때 상태 조회 UI만 검증하려면 다음 도구를 사용합니다.

```powershell
$env:PYTHONPATH="src;."
py tester/tools/mock_edge_mqtt_publisher.py --host 127.0.0.1 --port 1883 --topic ai-cctv/edge-node/status
```

기본 동작은 10회 정상 상태 JSON을 발행한 뒤 침묵하는 것입니다.
이 동작으로 상태 조회 UI의 `연결됨`, `조회중`, `연결실패` 전환을 확인할 수 있습니다.

```powershell
py tester/tools/mock_edge_mqtt_publisher.py --max-messages 3 --interval 1
```

## 원칙

테스트 도구는 `tester/` 아래에 둡니다.
자동화된 테스트도 `tester/tests/` 아래에 둡니다.
AI server와 단위 모듈은 테스트 여부를 나타내는 환경 변수, flag, 분기문을 갖지 않습니다.
