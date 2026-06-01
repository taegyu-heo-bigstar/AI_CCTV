# AI server 실행에 필요한 Python 패키지와 모델 상태를 점검하는 파일입니다.
# 누락 항목은 사용자 승인 후 pip 설치 또는 모델 다운로드 명령으로 보완합니다.
# 실제 설치는 UI에서 O 버튼을 누른 경우에만 수행되도록 분리합니다.

from dataclasses import dataclass
import importlib.metadata
import importlib.util
import os
from pathlib import Path
import subprocess
import sys


DEFAULT_YOLO_MODEL_PATH = "yolo26s.pt"
DEFAULT_QWEN_MODEL_ID = "Qwen/Qwen2.5-VL-3B-Instruct"


@dataclass(frozen=True)
class RuntimeRequirement:
    """AI server 실행에 필요한 패키지 또는 모델 요구사항을 표현합니다.

    인자:
        name: 화면에 표시할 요구사항 이름입니다.
        kind: package, yolo_model, qwen_model 중 하나의 유형입니다.
        import_name: 패키지 감지에 사용할 import 이름입니다.
        install_spec: pip 설치 또는 모델 다운로드에 사용할 식별자입니다.
        description: 사용자가 이해할 수 있는 요구사항 설명입니다.
        required: 실행 필수 여부입니다.
    반환값:
        RuntimeRequirement 인스턴스를 반환합니다.
    """

    name: str
    kind: str
    import_name: str = ""
    install_spec: str = ""
    description: str = ""
    required: bool = True


@dataclass(frozen=True)
class RuntimeRequirementResult:
    """단일 런타임 요구사항의 점검 결과를 표현합니다.

    인자:
        requirement: 점검한 요구사항입니다.
        installed: 요구사항 충족 여부입니다.
        detail: 버전, 경로, 오류 사유 등 상세 설명입니다.
    반환값:
        RuntimeRequirementResult 인스턴스를 반환합니다.
    """

    requirement: RuntimeRequirement
    installed: bool
    detail: str = ""


@dataclass(frozen=True)
class RuntimeReadinessReport:
    """AI server 런타임 준비 상태 전체 결과를 보관합니다.

    인자:
        results: 요구사항별 점검 결과 목록입니다.
    반환값:
        RuntimeReadinessReport 인스턴스를 반환합니다.
    """

    results: tuple[RuntimeRequirementResult, ...]

    def missing_required(self):
        """누락된 필수 요구사항 목록을 반환합니다.

        인자:
            없음.
        반환값:
            RuntimeRequirementResult 목록을 반환합니다.
        """

        return [
            result
            for result in self.results
            if result.requirement.required and not result.installed
        ]

    def is_ready(self):
        """필수 요구사항이 모두 충족되었는지 반환합니다.

        인자:
            없음.
        반환값:
            실행 가능하면 True, 아니면 False를 반환합니다.
        """

        return not self.missing_required()

    def to_text(self):
        """점검 결과를 UI 표시용 여러 줄 문자열로 변환합니다.

        인자:
            없음.
        반환값:
            요구사항별 상태 문자열을 반환합니다.
        """

        lines = []
        for result in self.results:
            status = "정상" if result.installed else "누락"
            lines.append(f"[{status}] {result.requirement.name}: {result.detail}")
        return "\n".join(lines)


class RuntimeEnvironmentChecker:
    """AI server 실행 전 필요한 패키지와 모델 상태를 점검합니다.

    인자:
        requirements: 점검할 요구사항 목록입니다.
        project_root: 모델 파일 탐색 기준 경로입니다.
    반환값:
        RuntimeEnvironmentChecker 인스턴스를 반환합니다.
    """

    def __init__(self, requirements=None, project_root=None):
        """런타임 점검 대상과 모델 탐색 기준 경로를 초기화합니다.

        인자:
            requirements: 점검할 요구사항 목록입니다.
            project_root: 모델 파일 탐색 기준 경로입니다.
        반환값:
            없음.
        """

        self.requirements = tuple(
            requirements if requirements is not None else build_default_requirements()
        )
        self.project_root = Path(project_root or Path.cwd())

    def check(self):
        """모든 런타임 요구사항을 점검합니다.

        인자:
            없음.
        반환값:
            RuntimeReadinessReport 인스턴스를 반환합니다.
        """

        return RuntimeReadinessReport(
            results=tuple(self._check_requirement(item) for item in self.requirements)
        )

    def _check_requirement(self, requirement):
        """요구사항 유형에 맞는 점검 함수를 호출합니다.

        인자:
            requirement: 점검할 RuntimeRequirement 인스턴스입니다.
        반환값:
            RuntimeRequirementResult 인스턴스를 반환합니다.
        """

        if requirement.kind == "package":
            return self._check_package(requirement)
        if requirement.kind == "yolo_model":
            return self._check_yolo_model(requirement)
        if requirement.kind == "qwen_model":
            return self._check_qwen_model(requirement)
        return RuntimeRequirementResult(requirement, False, "알 수 없는 요구사항 유형")

    def _check_package(self, requirement):
        """Python 패키지 설치 여부와 버전을 점검합니다.

        인자:
            requirement: 점검할 package 요구사항입니다.
        반환값:
            RuntimeRequirementResult 인스턴스를 반환합니다.
        """

        try:
            spec = importlib.util.find_spec(requirement.import_name)
        except (ImportError, ModuleNotFoundError, ValueError):
            spec = None

        if spec is None:
            return RuntimeRequirementResult(requirement, False, "패키지를 찾을 수 없습니다.")

        version = _read_distribution_version(requirement.install_spec)
        detail = f"설치됨{f' ({version})' if version else ''}"
        return RuntimeRequirementResult(requirement, True, detail)

    def _check_yolo_model(self, requirement):
        """YOLO 모델 파일 존재 여부를 점검합니다.

        인자:
            requirement: 점검할 YOLO 모델 요구사항입니다.
        반환값:
            RuntimeRequirementResult 인스턴스를 반환합니다.
        """

        model_path = Path(os.getenv("AI_CCTV_YOLO_MODEL_PATH", requirement.install_spec))
        if not model_path.is_absolute():
            model_path = self.project_root / model_path

        if model_path.is_file():
            return RuntimeRequirementResult(requirement, True, str(model_path))
        return RuntimeRequirementResult(requirement, False, f"모델 파일 없음: {model_path}")

    def _check_qwen_model(self, requirement):
        """Qwen VLM 모델 캐시 존재 여부를 점검합니다.

        인자:
            requirement: 점검할 Qwen 모델 요구사항입니다.
        반환값:
            RuntimeRequirementResult 인스턴스를 반환합니다.
        """

        model_id = os.getenv("AI_CCTV_QWEN_MODEL_ID", requirement.install_spec)
        try:
            from transformers.utils import cached_file

            cached_path = cached_file(model_id, "config.json", local_files_only=True)
        except Exception as error:
            return RuntimeRequirementResult(
                requirement,
                False,
                f"HuggingFace 캐시 없음: {model_id} ({error})",
            )
        return RuntimeRequirementResult(requirement, True, f"캐시 확인: {cached_path}")


class RuntimeInstaller:
    """누락된 AI server 런타임 요구사항을 설치하거나 다운로드합니다.

    인자:
        python_executable: pip와 다운로드 명령에 사용할 Python 실행 파일입니다.
    반환값:
        RuntimeInstaller 인스턴스를 반환합니다.
    """

    def __init__(self, python_executable=None):
        """설치 명령에 사용할 Python 실행 파일을 초기화합니다.

        인자:
            python_executable: Python 실행 파일 경로입니다.
        반환값:
            없음.
        """

        self.python_executable = python_executable or sys.executable

    def install_missing(self, missing_results):
        """누락된 요구사항 목록을 순서대로 설치합니다.

        인자:
            missing_results: RuntimeRequirementResult 목록입니다.
        반환값:
            설치 로그 문자열 목록을 반환합니다.
        """

        logs = []
        for result in missing_results:
            requirement = result.requirement
            if requirement.kind == "package":
                logs.append(self._install_package(requirement.install_spec))
            elif requirement.kind == "yolo_model":
                logs.append(self._download_yolo_model(requirement.install_spec))
            elif requirement.kind == "qwen_model":
                logs.append(self._download_qwen_model(requirement.install_spec))
        return logs

    def _install_package(self, install_spec):
        """pip로 Python 패키지를 설치합니다.

        인자:
            install_spec: pip install에 전달할 패키지 식별자입니다.
        반환값:
            설치 결과 로그 문자열을 반환합니다.
        """

        command = [self.python_executable, "-m", "pip", "install", install_spec]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(
                f"패키지 설치 실패: {install_spec}\n{completed.stderr or completed.stdout}"
            )
        return f"패키지 설치 완료: {install_spec}"

    def _download_yolo_model(self, model_path):
        """Ultralytics를 통해 YOLO 모델 로딩 또는 다운로드를 시도합니다.

        인자:
            model_path: YOLO 모델 파일 경로 또는 모델 이름입니다.
        반환값:
            다운로드 결과 로그 문자열을 반환합니다.
        """

        script = (
            "from ultralytics import YOLO; "
            f"YOLO({model_path!r}); "
            "print('YOLO model ready')"
        )
        self._run_python_script(script, f"YOLO 모델 준비 실패: {model_path}")
        return f"YOLO 모델 준비 완료: {model_path}"

    def _download_qwen_model(self, model_id):
        """Transformers를 통해 Qwen 모델 캐시 다운로드를 시도합니다.

        인자:
            model_id: HuggingFace 모델 식별자입니다.
        반환값:
            다운로드 결과 로그 문자열을 반환합니다.
        """

        script = (
            "from huggingface_hub import snapshot_download; "
            f"snapshot_download({model_id!r}); "
            "print('Qwen model ready')"
        )
        self._run_python_script(script, f"Qwen 모델 다운로드 실패: {model_id}")
        return f"Qwen 모델 다운로드 완료: {model_id}"

    def _run_python_script(self, script, failure_message):
        """별도 Python 프로세스로 모델 준비 스크립트를 실행합니다.

        인자:
            script: python -c에 전달할 스크립트 문자열입니다.
            failure_message: 실패 시 표시할 오류 메시지 접두어입니다.
        반환값:
            없음.
        """

        command = [self.python_executable, "-c", script]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            raise RuntimeError(f"{failure_message}\n{completed.stderr or completed.stdout}")


def build_startup_requirements(use_edge_node=True):
    """AI server 창을 여는 데 필요한 최소 요구사항 목록을 생성합니다.

    인자:
        use_edge_node: Edge node 연결 기능을 사용할지 여부입니다.
    반환값:
        RuntimeRequirement 목록을 반환합니다.
    """

    requirements = [
        RuntimeRequirement("PyQt5", "package", "PyQt5", "PyQt5", "GUI 실행"),
        RuntimeRequirement("OpenCV", "package", "cv2", "opencv-python", "영상 입력 처리"),
        RuntimeRequirement("NumPy", "package", "numpy", "numpy", "영상 배열 처리"),
    ]
    if use_edge_node:
        requirements.extend([
            RuntimeRequirement("requests", "package", "requests", "requests", "백업 복구 요청"),
            RuntimeRequirement("paho-mqtt", "package", "paho.mqtt.client", "paho-mqtt", "Edge 상태 MQTT"),
            RuntimeRequirement("psutil", "package", "psutil", "psutil", "자원 상태 처리"),
        ])
    return requirements


def build_analysis_requirements(
    use_yolo=True,
    use_vlm=False,
    include_discord=True,
    include_face=False,
):
    """선택한 AI 분석 기능 실행에 필요한 요구사항 목록을 생성합니다.

    인자:
        use_yolo: YOLO 사람 탐지와 추적을 사용할지 여부입니다.
        use_vlm: Qwen VLM 분석을 사용할지 여부입니다.
        include_discord: Discord 이상 상황 알림 패키지를 포함할지 여부입니다.
        include_face: 얼굴 식별 관련 패키지를 포함할지 여부입니다.
    반환값:
        RuntimeRequirement 목록을 반환합니다.
    """

    yolo_model = os.getenv("AI_CCTV_YOLO_MODEL_PATH", DEFAULT_YOLO_MODEL_PATH)
    qwen_model = os.getenv("AI_CCTV_QWEN_MODEL_ID", DEFAULT_QWEN_MODEL_ID)
    requirements = []
    if use_yolo or use_vlm or include_face:
        requirements.append(
            RuntimeRequirement("PyTorch", "package", "torch", "torch", "AI 추론 런타임")
        )
    if use_yolo:
        requirements.extend([
            RuntimeRequirement("Ultralytics", "package", "ultralytics", "ultralytics", "YOLO 추적"),
            RuntimeRequirement("YOLO 모델", "yolo_model", install_spec=yolo_model, description="사람 탐지 모델"),
        ])
    if use_vlm:
        requirements.extend([
            RuntimeRequirement("Transformers", "package", "transformers", "transformers>=4.51.0", "Qwen VLM"),
            RuntimeRequirement("Accelerate", "package", "accelerate", "accelerate", "Qwen device map"),
            RuntimeRequirement("bitsandbytes", "package", "bitsandbytes", "bitsandbytes", "Qwen 4bit 로딩"),
            RuntimeRequirement("huggingface-hub", "package", "huggingface_hub", "huggingface-hub", "Qwen 모델 캐시 다운로드"),
            RuntimeRequirement("Pillow", "package", "PIL", "pillow", "이미지 처리"),
            RuntimeRequirement("qwen-vl-utils", "package", "qwen_vl_utils", "qwen-vl-utils", "Qwen 입력 처리"),
            RuntimeRequirement("Qwen VLM 모델", "qwen_model", install_spec=qwen_model, description="사람 속성 분석 모델"),
        ])
    if include_discord and use_yolo:
        requirements.append(
            RuntimeRequirement("discord.py", "package", "discord", "discord.py>=2.0.0", "Discord 이상 상황 알림")
        )
    if include_face:
        requirements.extend([
            RuntimeRequirement("InsightFace", "package", "insightface", "insightface", "얼굴 식별"),
            RuntimeRequirement("ONNX Runtime", "package", "onnxruntime", "onnxruntime", "InsightFace 추론"),
        ])
    return _deduplicate_requirements(requirements)


def build_default_requirements():
    """AI server 기본 실행 요구사항 목록을 생성합니다.

    인자:
        없음.
    반환값:
        RuntimeRequirement 목록을 반환합니다.
    """

    return _deduplicate_requirements(
        build_startup_requirements(use_edge_node=True)
        + build_analysis_requirements(use_yolo=True, use_vlm=False)
    )


def _deduplicate_requirements(requirements):
    """동일한 요구사항이 중복 등록되지 않도록 목록을 정리합니다.

    인자:
        requirements: 정리할 RuntimeRequirement 목록입니다.
    반환값:
        중복이 제거된 RuntimeRequirement 목록을 반환합니다.
    """

    unique_requirements = []
    seen_keys = set()
    for requirement in requirements:
        key = (
            requirement.name,
            requirement.kind,
            requirement.import_name,
            requirement.install_spec,
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        unique_requirements.append(requirement)
    return unique_requirements


def _read_distribution_version(install_spec):
    """pip 설치 식별자에서 패키지 버전 문자열을 조회합니다.

    인자:
        install_spec: pip 설치 식별자입니다.
    반환값:
        버전 문자열 또는 빈 문자열을 반환합니다.
    """

    package_name = install_spec.split("==", 1)[0].split(">=", 1)[0].split("[", 1)[0]
    normalized_name = package_name.strip()
    aliases = {
        "opencv-python": "opencv-python",
        "pillow": "Pillow",
        "paho-mqtt": "paho-mqtt",
        "qwen-vl-utils": "qwen-vl-utils",
    }
    try:
        return importlib.metadata.version(aliases.get(normalized_name, normalized_name))
    except importlib.metadata.PackageNotFoundError:
        return ""
