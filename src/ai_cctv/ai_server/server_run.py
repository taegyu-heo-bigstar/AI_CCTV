# AI server 실행 진입점 파일입니다.
# 서버 노드 실행 명령은 OS와 PyQt 최소 조건을 확인한 뒤 관제 UI를 시작합니다.
# 영상 분석, 저장, 알림 구현은 각각 analysis, storage, alerts 패키지에 분리되어 있습니다.

"""AI server 실행 진입점입니다."""

from .runtime import ensure_pyqt5_available, ensure_windows_os


def main():
    """AI server 관제 GUI 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    ensure_windows_os()
    ensure_pyqt5_available()

    from .ui.main_window import main as run_main_window
    run_main_window()


if __name__ == "__main__":
    main()
