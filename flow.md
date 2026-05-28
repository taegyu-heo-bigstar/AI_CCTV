# AI CCTV Flow

이 문서는 `refactor` 브랜치 기준 프로젝트 구조와 런타임 흐름을 설명한다.

## Project Layout

```text
AI_CCTV/
├── src/ai_cctv/
│   ├── client/          # PyQt GUI, video processing, VLM, recording, chatbot
│   ├── server/          # server-side helpers
│   └── streaming/       # RTSP sender/receiver utilities
├── docs/                # design notes, study documents, RTSP docs
├── tmp/                 # legacy demos and temporary files
├── scripts/             # operational shell scripts
├── main.py              # local development entrypoint
└── pyproject.toml       # Python package metadata
```

## Runtime Flow

```mermaid
flowchart TD
    User["User"] --> GUI["CCTVMainWindow<br/>client/gui.py"]
    GUI --> Settings["SettingsWindow<br/>client/settings_window.py"]
    GUI --> Worker["VideoWorker<br/>client/video_worker.py"]

    Worker --> Stream["VideoStream<br/>client/video_stream.py"]
    Stream --> Frame["OpenCV frame"]
    Frame --> Tracker["PersonTracker<br/>YOLO + ByteTrack"]
    Tracker --> Persons["Tracked person list"]

    Persons --> BodyCheck["FullBodyChecker"]
    BodyCheck --> State["PersonStateManager"]
    Frame --> Recorder["RecordingManager"]

    BodyCheck --> CropDecision{"Full body<br/>and not cropped?"}
    CropDecision -- "yes" --> Crop["CropManager"]
    Crop --> VLMQueue["VLMWorker queue"]
    VLMQueue --> Analyzer["PersonAnalyzer<br/>Qwen VLM"]
    Analyzer --> State
    Analyzer --> Chatbot["chat_bot"]
    Chatbot --> Discord["DiscordBotSender"]

    State --> Metrics["metrics_ready signal"]
    Worker --> RenderedFrame["frame_ready signal"]
    Worker --> Events["event_ready signal"]

    Metrics --> GUI
    RenderedFrame --> GUI
    Events --> GUI
```

## Responsibility Boundaries

```mermaid
classDiagram
    class CCTVMainWindow {
        +start_video()
        +stop_video()
        +update_frame()
        +add_event()
    }
    class VideoWorker {
        +run()
        +stop()
        -_handle_person()
        -_cleanup()
    }
    class VideoStream {
        +open()
        +read()
        +release()
    }
    class PersonTracker {
        +track(frame)
    }
    class FullBodyChecker {
        +is_full_body_visible(bbox, frame_shape)
    }
    class PersonStateManager {
        +update_person()
        +mark_crop_saved()
        +mark_vlm_done()
        +remove_disappeared_persons()
    }
    class RecordingManager {
        +write_frame(frame)
        +stop_recording()
    }
    class VLMWorker {
        +start()
        +add_task()
        +stop()
    }

    CCTVMainWindow --> VideoWorker
    VideoWorker --> VideoStream
    VideoWorker --> PersonTracker
    VideoWorker --> FullBodyChecker
    VideoWorker --> PersonStateManager
    VideoWorker --> RecordingManager
    VideoWorker --> VLMWorker
```

## Execution

로컬 개발에서는 루트에서 다음 명령으로 실행한다.

```bash
python main.py
```

패키지로 설치한 환경에서는 console script를 사용할 수 있다.

```bash
pip install -e .
ai-cctv
```
