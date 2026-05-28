# AI server 실행 진입점 파일입니다.
# 설치된 console script와 루트 main.py가 서버 GUI 실행을 이 진입점에 위임합니다.
# 실제 GUI 구성은 ai_cctv.ai_server.client.gui가 담당합니다.

"""AI server 실행 진입점입니다."""


def main():
    """AI server GUI 분석 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        없음.
    """

    from .client.gui import main as run_gui

    run_gui()


if __name__ == "__main__":
    main()
