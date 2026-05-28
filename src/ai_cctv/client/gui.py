# AI CCTV 메인 GUI 호환 진입점 파일입니다.
# 실제 PyQt 메인 창 구현은 client.ui.main_window에 있습니다.
# 기존 pyproject console script와 main.py import 경로를 유지합니다.

from .ui.main_window import CCTVMainWindow, main


__all__ = ["CCTVMainWindow", "main"]


if __name__ == "__main__":
    main()
