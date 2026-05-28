# Edge node 실행 진입점 호환 파일입니다.
# 실제 Edge node 실행 진입점은 src/edge_node/main.py에 있습니다.
# 기존 ai_cctv.edge_pi.main import 경로를 유지합니다.

from edge_node.main import build_default_streaming_command, main

__all__ = ["main", "build_default_streaming_command"]


if __name__ == "__main__":
    main()
