# AI 서버 실행 진입점 호환 파일입니다.
# 실제 AI 서버 실행 진입점은 src/ai_server/main.py에 있습니다.
# 기존 ai_cctv.ai_server.main import 경로를 유지합니다.

from ai_server.main import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
