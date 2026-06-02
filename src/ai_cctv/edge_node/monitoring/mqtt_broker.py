# Edge node 내장 MQTT broker 실행 파일입니다.
# 외부 Mosquitto 설치 없이 Edge node가 상태 broker를 직접 제공합니다.
# paho-mqtt 기반 publisher와 subscriber가 쓰는 최소 MQTT 패킷을 처리합니다.
# AI server는 Edge node가 출력한 MQTT_BROKER 주소로 이 broker에 접속합니다.

"""Edge node 내장 MQTT broker 모듈입니다."""

from dataclasses import dataclass
import os
import socket
import threading
import time


MQTT_CONNECT = 1
MQTT_PUBLISH = 3
MQTT_SUBSCRIBE = 8
MQTT_PINGREQ = 12
MQTT_DISCONNECT = 14
DEFAULT_BROKER_HOST = "0.0.0.0"
DEFAULT_BROKER_PORT = 1883
SUPPORTED_MQTT_QOS_VALUES = (0,)


@dataclass(frozen=True)
class MqttBrokerConfig:
    """Edge node 내장 MQTT broker 실행 설정을 표현합니다.

    인자:
        host: broker가 listen할 호스트 주소입니다.
        port: broker가 listen할 TCP 포트입니다.
    반환값:
        MqttBrokerConfig 인스턴스를 반환합니다.
    """

    host: str = DEFAULT_BROKER_HOST
    port: int = DEFAULT_BROKER_PORT

    @classmethod
    def from_environment(cls):
        """환경 변수에서 MQTT broker 실행 설정을 생성합니다.

        인자:
            없음.
        반환값:
            MqttBrokerConfig 인스턴스를 반환합니다.
        """

        return cls(
            host=os.getenv("AI_CCTV_MQTT_BROKER_HOST", DEFAULT_BROKER_HOST),
            port=int(os.getenv("AI_CCTV_MQTT_PORT", DEFAULT_BROKER_PORT)),
        )


class TinyMqttBroker:
    """Edge node 상태 발행과 AI server 구독을 위한 최소 MQTT broker입니다.

    인자:
        config: broker listen 설정입니다.
    반환값:
        TinyMqttBroker 인스턴스를 반환합니다.
    """

    def __init__(self, config=None):
        """broker socket과 구독자 저장소를 초기화합니다.

        인자:
            config: broker listen 설정이며 없으면 기본 설정을 사용합니다.
        반환값:
            없음.
        """

        self.config = config or MqttBrokerConfig()
        self.server_socket = None
        self.running = False
        self.accept_thread = None
        self.subscribers = {}
        self.retained_packets = {}
        self.lock = threading.Lock()

    def start(self):
        """MQTT broker listen thread를 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.running:
            return

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.config.host, int(self.config.port)))
        self.server_socket.listen()
        self.server_socket.settimeout(0.5)
        self.running = True
        self.accept_thread = threading.Thread(
            target=self._accept_loop,
            name="EdgeTinyMqttBroker",
            daemon=True,
        )
        self.accept_thread.start()

    def run_forever(self):
        """MQTT broker를 시작하고 종료 신호까지 대기합니다.

        인자:
            없음.
        반환값:
            정상적으로는 반환하지 않습니다.
        """

        self.start()
        try:
            while self.running:
                time.sleep(0.5)
        finally:
            self.stop()

    def stop(self):
        """MQTT broker와 연결된 client socket을 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False
        if self.server_socket is not None:
            _close_socket(self.server_socket)
            self.server_socket = None

        with self.lock:
            clients = {
                client
                for topic_clients in self.subscribers.values()
                for client in topic_clients
            }
            self.subscribers.clear()

        for client in clients:
            _close_socket(client)

        if self.accept_thread is not None and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=2)

    def _accept_loop(self):
        """client 접속을 수락하고 처리 thread를 생성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        while self.running and self.server_socket is not None:
            try:
                client, _address = self.server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            client.settimeout(1.0)
            thread = threading.Thread(
                target=self._handle_client,
                args=(client,),
                name="EdgeTinyMqttClient",
                daemon=True,
            )
            thread.start()

    def _handle_client(self, client):
        """단일 MQTT client의 기본 패킷을 처리합니다.

        인자:
            client: 연결된 TCP socket입니다.
        반환값:
            없음.
        """

        try:
            while self.running:
                fixed_header, payload = read_mqtt_packet(client)
                packet_type = fixed_header >> 4
                flags = fixed_header & 0x0F
                if packet_type == MQTT_CONNECT:
                    client.sendall(b"\x20\x02\x00\x00")
                    continue
                if packet_type == MQTT_SUBSCRIBE:
                    self._handle_subscribe(client, payload)
                    continue
                if packet_type == MQTT_PUBLISH:
                    qos = (flags >> 1) & 0x03
                    if qos not in SUPPORTED_MQTT_QOS_VALUES:
                        break
                    self._handle_publish(payload, retain=bool(flags & 0x01))
                    continue
                if packet_type == MQTT_PINGREQ:
                    client.sendall(b"\xd0\x00")
                    continue
                if packet_type == MQTT_DISCONNECT:
                    break
        except OSError:
            pass
        finally:
            self._remove_client(client)
            _close_socket(client)

    def _handle_subscribe(self, client, payload):
        """SUBSCRIBE 패킷을 처리하고 retained 메시지를 즉시 전달합니다.

        인자:
            client: 구독 요청을 보낸 socket입니다.
            payload: MQTT SUBSCRIBE payload입니다.
        반환값:
            없음.
        """

        packet_id = payload[:2] if len(payload) >= 2 else b"\x00\x01"
        topics = parse_subscribe_topics(payload[2:])
        with self.lock:
            for topic in topics:
                self.subscribers.setdefault(topic, set()).add(client)
        client.sendall(b"\x90\x03" + packet_id + b"\x00")
        for topic in topics:
            retained_packet = self.retained_packets.get(topic)
            if retained_packet:
                client.sendall(retained_packet)

    def _handle_publish(self, payload, retain=False):
        """PUBLISH 패킷을 구독자에게 전달합니다.

        인자:
            payload: MQTT PUBLISH payload입니다.
            retain: retained 메시지로 보관할지 여부입니다.
        반환값:
            없음.
        """

        topic, message = parse_publish_payload(payload)
        packet = build_publish_packet(topic, message, retain=retain)
        if retain:
            with self.lock:
                self.retained_packets[topic] = packet

        self._publish_to_subscribers(topic, packet)

    def _publish_to_subscribers(self, topic, packet):
        """topic을 구독 중인 client에게 PUBLISH packet을 전달합니다.

        인자:
            topic: 발행 topic입니다.
            packet: 전송할 MQTT PUBLISH packet입니다.
        반환값:
            전달을 시도한 client 수를 반환합니다.
        """

        with self.lock:
            clients = list(self.subscribers.get(topic, set()))

        delivered_count = 0
        for client in clients:
            try:
                client.sendall(packet)
                delivered_count += 1
            except OSError:
                self._remove_client(client)
        return delivered_count

    def _remove_client(self, client):
        """모든 구독 목록에서 지정한 client를 제거합니다.

        인자:
            client: 제거할 socket입니다.
        반환값:
            없음.
        """

        with self.lock:
            for clients in self.subscribers.values():
                clients.discard(client)


def read_mqtt_packet(client):
    """socket에서 MQTT fixed header와 payload를 읽습니다.

    인자:
        client: MQTT client TCP socket입니다.
    반환값:
        fixed header 첫 바이트와 payload bytes 튜플을 반환합니다.
    """

    first_byte = read_exact(client, 1)[0]
    remaining_length = read_remaining_length(client)
    payload = read_exact(client, remaining_length)
    return first_byte, payload


def read_exact(client, byte_count):
    """지정한 byte 수만큼 socket에서 읽습니다.

    인자:
        client: 데이터를 읽을 TCP socket입니다.
        byte_count: 읽어야 하는 byte 수입니다.
    반환값:
        읽은 bytes 값을 반환합니다.
    """

    chunks = []
    remaining = byte_count
    while remaining > 0:
        chunk = client.recv(remaining)
        if not chunk:
            raise OSError("MQTT client 연결이 종료되었습니다.")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def read_remaining_length(client):
    """MQTT remaining length 필드를 정수로 읽습니다.

    인자:
        client: 데이터를 읽을 TCP socket입니다.
    반환값:
        remaining length 정수를 반환합니다.
    """

    multiplier = 1
    value = 0
    while True:
        encoded_byte = read_exact(client, 1)[0]
        value += (encoded_byte & 127) * multiplier
        if encoded_byte & 128 == 0:
            return value
        multiplier *= 128
        if multiplier > 128 * 128 * 128:
            raise OSError("MQTT remaining length가 너무 깁니다.")


def parse_subscribe_topics(payload):
    """SUBSCRIBE payload에서 topic 목록을 추출합니다.

    인자:
        payload: packet id를 제외한 SUBSCRIBE payload입니다.
    반환값:
        topic 문자열 목록을 반환합니다.
    """

    topics = []
    offset = 0
    while offset + 3 <= len(payload):
        topic_length = int.from_bytes(payload[offset : offset + 2], "big")
        offset += 2
        topic = payload[offset : offset + topic_length].decode("utf-8")
        offset += topic_length
        offset += 1
        topics.append(topic)
    return topics


def parse_publish_payload(payload):
    """PUBLISH payload에서 topic과 message를 분리합니다.

    인자:
        payload: MQTT PUBLISH payload입니다.
    반환값:
        topic 문자열과 message bytes 튜플을 반환합니다.
    """

    if len(payload) < 2:
        raise OSError("MQTT PUBLISH payload가 너무 짧습니다.")
    topic_length = int.from_bytes(payload[:2], "big")
    topic_start = 2
    topic_end = topic_start + topic_length
    topic = payload[topic_start:topic_end].decode("utf-8")
    message = payload[topic_end:]
    return topic, message


def build_publish_packet(topic, payload, retain=True):
    """QoS 0 MQTT PUBLISH packet을 생성합니다.

    인자:
        topic: 발행할 MQTT topic입니다.
        payload: 문자열 또는 bytes payload입니다.
        retain: retain flag 설정 여부입니다.
    반환값:
        MQTT PUBLISH packet bytes를 반환합니다.
    """

    topic_bytes = topic.encode("utf-8")
    payload_bytes = payload if isinstance(payload, bytes) else payload.encode("utf-8")
    variable_header = len(topic_bytes).to_bytes(2, "big") + topic_bytes
    fixed_header = bytes([0x31 if retain else 0x30])
    remaining_length = encode_remaining_length(len(variable_header) + len(payload_bytes))
    return fixed_header + remaining_length + variable_header + payload_bytes


def encode_remaining_length(value):
    """MQTT remaining length 정수를 variable byte 형식으로 인코딩합니다.

    인자:
        value: 인코딩할 remaining length 정수입니다.
    반환값:
        MQTT variable byte integer bytes를 반환합니다.
    """

    encoded = bytearray()
    while True:
        encoded_byte = value % 128
        value //= 128
        if value > 0:
            encoded_byte |= 128
        encoded.append(encoded_byte)
        if value == 0:
            return bytes(encoded)


def _close_socket(sock):
    """socket shutdown과 close를 안전하게 수행합니다.

    인자:
        sock: 종료할 socket입니다.
    반환값:
        없음.
    """

    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    try:
        sock.close()
    except OSError:
        pass


def main():
    """Edge node 내장 MQTT broker를 실행합니다.

    인자:
        없음.
    반환값:
        정상적으로는 반환하지 않습니다.
    """

    from ..os_guard import ensure_supported_edge_os

    ensure_supported_edge_os()
    config = MqttBrokerConfig.from_environment()
    broker = TinyMqttBroker(config)
    print(
        f"[AI_CCTV MQTT Broker] listening on {config.host}:{config.port}",
        flush=True,
    )
    try:
        broker.run_forever()
    except KeyboardInterrupt:
        broker.stop()


if __name__ == "__main__":
    main()
