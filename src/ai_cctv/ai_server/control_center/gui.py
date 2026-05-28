# AI CCTV 메인 GUI 지연 진입점 파일입니다.
# 실제 PyQt 메인 창 구현은 control_center.ui.main_window에 있습니다.
# GUI 의존성은 실행 시점에만 import하여 서버 패키지 import 부작용을 줄입니다.

__all__ = ["CCTVMainWindow", "main"]


def main():
    """AI server 관제 GUI 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    from .ui.main_window import main as run_main_window

    run_main_window()


def __getattr__(name):
    """지연 import 방식으로 메인 윈도우 클래스를 제공합니다.

    인자:
        name: 조회할 모듈 속성명입니다.
    반환값:
        CCTVMainWindow 클래스 객체를 반환합니다.
    """

    if name == "CCTVMainWindow":
        from .ui.main_window import CCTVMainWindow

        return CCTVMainWindow
    raise AttributeError(name)


if __name__ == "__main__":
    main()
