# AI CCTV 알림 채널 디스패처 파일입니다.
# 알림 메시지를 등록된 전송 채널 구현체로 전달합니다.
# 현재 운영 채널은 Discord이며, 채널 확장은 인터페이스 구현으로 분리합니다.

from .message import NotificationMessage


class NotificationChannel:
    """알림 채널 구현체의 공통 인터페이스입니다.

    인자:
        없음.
    반환값:
        NotificationChannel 인스턴스를 반환합니다.
    """

    def send(self, message):
        """알림 메시지를 채널로 전송합니다.

        인자:
            message: NotificationMessage 객체입니다.
        반환값:
            없음.
        """

        raise NotImplementedError


class DiscordNotificationChannel(NotificationChannel):
    """기존 Discord 챗봇 모듈을 알림 채널로 감쌉니다.

    인자:
        chatbot_module: send_msg 함수를 제공하는 챗봇 모듈입니다.
    반환값:
        DiscordNotificationChannel 인스턴스를 반환합니다.
    """

    def __init__(self, chatbot_module):
        """Discord 알림 채널을 초기화합니다.

        인자:
            chatbot_module: send_msg 함수를 제공하는 챗봇 모듈입니다.
        반환값:
            없음.
        """

        self.chatbot_module = chatbot_module

    def send(self, message):
        """Discord 챗봇으로 알림 메시지를 전송합니다.

        인자:
            message: NotificationMessage 객체입니다.
        반환값:
            없음.
        """

        self.chatbot_module.send_msg(message.to_text())


class NotificationDispatcher:
    """알림 메시지를 등록된 채널로 전달합니다.

    인자:
        channels: NotificationChannel 구현체 목록입니다.
    반환값:
        NotificationDispatcher 인스턴스를 반환합니다.
    """

    def __init__(self, channels=None):
        """알림 채널 목록을 초기화합니다.

        인자:
            channels: NotificationChannel 구현체 목록입니다.
        반환값:
            없음.
        """

        self.channels = list(channels or [])

    def add_channel(self, channel):
        """알림 채널을 추가합니다.

        인자:
            channel: NotificationChannel 구현체입니다.
        반환값:
            없음.
        """

        self.channels.append(channel)

    def dispatch_anomaly_event(self, event):
        """이상 상황 이벤트를 알림 메시지로 변환해 전송합니다.

        인자:
            event: AnomalyEvent 객체입니다.
        반환값:
            전송을 시도한 채널 수를 반환합니다.
        """

        message = NotificationMessage.from_anomaly_event(event)
        return self.dispatch(message)

    def dispatch(self, message):
        """알림 메시지를 전체 채널로 전송합니다.

        인자:
            message: NotificationMessage 객체입니다.
        반환값:
            전송을 시도한 채널 수를 반환합니다.
        """

        for channel in self.channels:
            channel.send(message)
        return len(self.channels)
