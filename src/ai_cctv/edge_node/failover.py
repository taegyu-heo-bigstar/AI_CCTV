# Edge node 네트워크 장애 대응 정책 파일입니다.
# 네트워크 상태에 따라 송출, 로컬 저장, 최소 알림 동작을 결정합니다.
# 실제 저장과 알림 구현은 이 정책의 결정값을 사용하는 계층에서 수행합니다.

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeFailoverDecision:
    """네트워크 상태에 따른 Edge node 동작 결정을 표현합니다.

    인자:
        should_stream: Windows 서버로 RTSP 송출을 시도할지 여부입니다.
        should_record_local: Raspberry Pi 로컬 저장을 수행할지 여부입니다.
        should_send_minimal_alert: 최소 알림을 보낼지 여부입니다.
        reason: 동작을 선택한 이유입니다.
    반환값:
        EdgeFailoverDecision 인스턴스를 반환합니다.
    """

    should_stream: bool
    should_record_local: bool
    should_send_minimal_alert: bool
    reason: str


class EdgeNetworkFailoverPolicy:
    """Edge node 네트워크 장애 대응 동작을 결정합니다.

    인자:
        enable_minimal_alert: 장애 시 최소 알림을 사용할지 여부입니다.
    반환값:
        EdgeNetworkFailoverPolicy 인스턴스를 반환합니다.
    """

    def __init__(self, enable_minimal_alert=True):
        """장애 대응 정책을 초기화합니다.

        인자:
            enable_minimal_alert: 장애 시 최소 알림을 사용할지 여부입니다.
        반환값:
            없음.
        """

        self.enable_minimal_alert = enable_minimal_alert

    def decide_for_network(self, network_available):
        """네트워크 상태에 맞는 Edge node 동작을 결정합니다.

        인자:
            network_available: 네트워크 연결 가능 여부입니다.
        반환값:
            EdgeFailoverDecision 객체를 반환합니다.
        """

        if network_available:
            return EdgeFailoverDecision(
                should_stream=True,
                should_record_local=False,
                should_send_minimal_alert=False,
                reason="네트워크 연결 정상",
            )

        return EdgeFailoverDecision(
            should_stream=False,
            should_record_local=True,
            should_send_minimal_alert=self.enable_minimal_alert,
            reason="네트워크 연결 장애",
        )
