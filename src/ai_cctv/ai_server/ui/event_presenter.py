# CCTV 이벤트를 화면 표시용 문구와 색상으로 변환하는 파일입니다.
# GUI 위젯 생성과 이벤트 해석 책임을 분리하기 위해 사용합니다.
# 입력 이벤트 딕셔너리를 UI가 바로 사용할 수 있는 값 객체로 바꿉니다.

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EventDisplay:
    """이벤트 표시 정보를 담는 값 객체입니다.

    인자:
        description: 화면에 표시할 이벤트 설명입니다.
        color: 시간 텍스트에 적용할 색상 코드입니다.
        event_type: 원본 이벤트 유형입니다.
    반환값:
        dataclass 생성자는 EventDisplay 인스턴스를 반환합니다.
    """

    description: str
    color: str
    event_type: str


class EventPresenter:
    """이벤트 딕셔너리를 UI 표시 정보로 변환합니다.

    인자:
        없음.
    반환값:
        EventPresenter 인스턴스를 반환합니다.
    """

    def build_display(self, event):
        """이벤트 유형별 설명과 색상을 생성합니다.

        인자:
            event: VideoWorker가 전달한 이벤트 딕셔너리입니다.
        반환값:
            EventDisplay 객체를 반환합니다.
        """

        event_type = event.get("type", "unknown")
        person_id = event.get("person_id", "-")

        if event_type == "appear":
            return EventDisplay(f"ID {person_id} appeared", "#22c55e", event_type)
        if event_type == "disappear":
            return EventDisplay(f"ID {person_id} disappeared", "#f97316", event_type)
        if event_type == "error":
            return EventDisplay(event.get("message", "Error"), "#ef4444", event_type)
        if event_type == "status":
            return EventDisplay(event.get("message", "Status"), "#38bdf8", event_type)
        if event_type == "network_failure":
            return EventDisplay(
                event.get("message", "네트워크 장애 감지"),
                "#facc15",
                event_type,
            )
        if event_type == "network_recovered":
            return EventDisplay(
                event.get("message", "네트워크 연결 복구"),
                "#38bdf8",
                event_type,
            )
        if event_type == "anomaly":
            message = event.get("message", "Anomaly detected")
            return EventDisplay(message, "#facc15", event_type)
        if event_type == "vlm_queue":
            return EventDisplay(f"ID {person_id} VLM 분석 대기열 등록", "#a855f7", event_type)
        if event_type == "vlm_done":
            message = event.get("message", "")
            return EventDisplay(f"ID {person_id} VLM 분석 완료\n{message}", "#a855f7", event_type)

        return EventDisplay(f"ID {person_id} {event_type}", "#38bdf8", event_type)

    def get_time_text(self, event):
        """이벤트 시간 문자열을 가져오거나 현재 시각으로 대체합니다.

        인자:
            event: 시간 값이 포함될 수 있는 이벤트 딕셔너리입니다.
        반환값:
            HH:MM:SS 형식의 문자열을 반환합니다.
        """

        return event.get("time", datetime.now().strftime("%H:%M:%S"))
