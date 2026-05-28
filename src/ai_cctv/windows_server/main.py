# Windows 서버 실행 진입점 파일입니다.
# 기존 PyQt GUI 기반 분석 서버를 명시적인 Windows 서버 명령으로 실행합니다.
# ai-cctv-windows-server console script가 이 main 함수를 호출합니다.

from ai_cctv.client.gui import main as run_gui


def main():
    """Windows 서버 GUI 분석 애플리케이션을 실행합니다.

    인자:
        없음.
    반환값:
        정상적으로는 반환하지 않고 Qt 이벤트 루프 종료 코드를 사용합니다.
    """

    run_gui()


if __name__ == "__main__":
    main()

