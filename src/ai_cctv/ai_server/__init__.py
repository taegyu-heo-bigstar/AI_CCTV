# AI 서버 호환 패키지 파일입니다.
# 실제 AI 서버 실행 묶음은 src/ai_server 패키지에 있습니다.
# 기존 ai_cctv.ai_server import 경로를 유지하기 위해 공개 객체를 재노출합니다.

from ai_server import (
    AlertDispatcher,
    AlertMessage,
    AnomalyDetector,
    DiscordChatBotChannel,
    DwellTimeRule,
    ObjectPresenceRule,
    VideoWorker,
    main,
)

__all__ = [
    "main",
    "AnomalyDetector",
    "DwellTimeRule",
    "ObjectPresenceRule",
    "VideoWorker",
    "AlertDispatcher",
    "AlertMessage",
    "DiscordChatBotChannel",
]
