# AI CCTV 로컬 개발 실행 파일입니다.
# 설치 없이 루트에서 python main.py로 GUI를 실행합니다.
# src 경로를 임시로 sys.path에 추가한 뒤 패키지 진입점을 호출합니다.

import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ai_cctv.windows_server.main import main


if __name__ == "__main__":
    main()
