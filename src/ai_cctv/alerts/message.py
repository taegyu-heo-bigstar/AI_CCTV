# AI CCTV 알림 메시지 값 객체 파일입니다.
# 이상 상황 이벤트를 사용자에게 전달할 텍스트와 첨부 정보로 변환합니다.
# 알림 채널 구현체가 같은 메시지 형식을 공유하게 합니다.

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AlertMessage:
    """사용자 알림 메시지를 표현합니다.

    인자:
        title: 알림 제목입니다.
        body: 알림 본문입니다.
        image_path: 첨부할 이미지 경로입니다.
        metadata: 채널별 추가 정보입니다.
    반환값:
        AlertMessage 인스턴스를 반환합니다.
    """

    title: str
    body: str
    image_path: str | None = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_anomaly_event(cls, event):
        """이상 상황 이벤트에서 알림 메시지를 생성합니다.

        인자:
            event: AnomalyEvent 객체입니다.
        반환값:
            AlertMessage 인스턴스를 반환합니다.
        """

        body = (
            f"{event.message}\n"
            f"- 감지 객체: {event.object_name}\n"
            f"- 신뢰도: {event.confidence:.2f}\n"
            f"- 발생 시각: {event.occurred_at:%Y-%m-%d %H:%M:%S}"
        )
        return cls(
            title="[AI CCTV 알림]",
            body=body,
            image_path=event.image_path,
            metadata=event.metadata,
        )

    def to_text(self):
        """채팅 채널로 보낼 텍스트 메시지를 생성합니다.

        인자:
            없음.
        반환값:
            제목과 본문을 결합한 문자열을 반환합니다.
        """

        return f"{self.title}\n{self.body}"

