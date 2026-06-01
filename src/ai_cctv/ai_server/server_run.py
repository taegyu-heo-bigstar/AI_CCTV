# AI server 실행 진입점 파일입니다.
# 서버 노드 실행 명령은 PyTorch DLL을 먼저 준비한 뒤 PyQt 관제 UI를 시작합니다.
# 영상 분석, 저장, 알림 구현은 각각 analysis, storage, alerts 패키지에 분리되어 있습니다.

"""AI server 실행 진입점입니다."""


def preload_ai_runtime_libraries():
    """PyQt 로딩 전에 AI 런타임 네이티브 라이브러리를 초기화합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    try:
        import torch
    except Exception as exc:
        raise RuntimeError(
            "PyTorch 런타임 초기화에 실패했습니다. torch 설치와 CUDA DLL 구성을 확인하세요."
        ) from exc

    _ = torch.__version__


def main():
    """AI server 관제 GUI 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    from .ui.main_window import main as run_main_window

    run_main_window(pre_start_callback=preload_ai_runtime_libraries)


if __name__ == "__main__":
    main()
