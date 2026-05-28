# AI server 실행 진입점 파일입니다.
# 설치된 console script와 루트 main.py가 이 진입점을 호출합니다.
# 실제 GUI 구성은 ai_cctv.client.gui에 위임합니다.

"""AI 서버 실행 진입점입니다."""

from ai_cctv.client.gui import main as run_gui


def main():
    """AI 서버 GUI 분석 애플리케이션을 실행합니다."""

    run_gui()


if __name__ == "__main__":
    main()
