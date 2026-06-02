# pseudo Edge node용 최소 MQTT broker 파일입니다.
# AI server의 paho-mqtt subscriber가 접속하고 subscribe할 수 있는 최소 프로토콜만 구현합니다.
# CONNECT, SUBSCRIBE, PINGREQ, DISCONNECT 패킷을 처리하고 상태 JSON을 QoS 0 PUBLISH로 전송합니다.
# 외부 mosquitto 설치 없이 Windows 단일 PC에서 상태 조회 UI를 테스트하기 위한 구성입니다.

import socket
import threading


MQTT_CONNECT = 1
MQTT_PUBLISH = 3
MQTT_SUBSCRIBE = 8
MQTT_PINGREQ = 12
MQTT_DISCONNECT = 14


class TinyMqttBroker:
    """AI server 상태 구독 테스트를 위한 최소 MQTT broker입니다.

    인자:
        host: broker가 listen할 호스트입니다.
        port: broker가 listen할 TCP 포트입니다.
    반환값:
        TinyMqttBroker 인스턴스를 반환합니다.
    """

    def __init__(self, host="127.0.0.1", port=1883):
        """broker socket과 client 보관 상태를 초기화합니다.

        인자:
            host: broker가 listen할 호스트입니다.
            port: broker가 listen할 TCP 포트입니다.
        반환값:
            없음.
        """

        self.host = host
        self.port = int(port)
        self.server_socket = None
        self.running = False
        self.thread = None
        self.clients = set()
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
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.server_socket.settimeout(0.5)
        self.running = True
        self.thread = threading.Thread(
            target=self._accept_loop,
            name="TinyMqttBroker",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """MQTT broker와 연결된 client socket을 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.running = False
        if self.server_socket is not None:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

        with self.lock:
            clients = list(self.clients)
            self.clients.clear()

        for client in clients:
            _close_socket(client)

        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2)

    def publish(self, topic, payload, retain=True):
        """현재 subscribe 중인 client에게 상태 JSON을 발행합니다.

        인자:
            topic: 발행할 MQTT topic입니다.
            payload: UTF-8로 보낼 문자열 payload입니다.
            retain: retain flag를 설정할지 여부입니다.
        반환값:
            전송을 시도한 client 수를 반환합니다.
        """

        packet = build_publish_packet(topic, payload, retain=retain)
        with self.lock:
            clients = list(self.clients)

        delivered = 0
        for client in clients:
            try:
                client.sendall(packet)
                delivered += 1
            except OSError:
                self._remove_client(client)
        return delivered

    def _accept_loop(self):
        """client 접속을 수락하고 handler thread를 생성합니다.

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
                name="TinyMqttClient",
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
                packet_type, payload = read_mqtt_packet(client)
                if packet_type == MQTT_CONNECT:
                    client.sendall(b"\x20\x02\x00\x00")
                    continue
                if packet_type == MQTT_SUBSCRIBE:
                    packet_id = payload[:2] if len(payload) >= 2 else b"\x00\x01"
                    with self.lock:
                        self.clients.add(client)
                    client.sendall(b"\x90\x03" + packet_id + b"\x00")
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

    def _remove_client(self, client):
        """client 목록에서 지정한 socket을 제거합니다.

        인자:
            client: 제거할 TCP socket입니다.
        반환값:
            없음.
        """

        with self.lock:
            self.clients.discard(client)


def read_mqtt_packet(client):
    """socket에서 MQTT fixed header와 payload를 읽습니다.

    인자:
        client: MQTT client TCP socket입니다.
    반환값:
        packet type 정수와 payload bytes 튜플을 반환합니다.
    """

    first = read_exact(client, 1)
    remaining_length = read_remaining_length(client)
    payload = read_exact(client, remaining_length)
    return first[0] >> 4, payload


def read_exact(client, byte_count):
    """지정한 byte 수만큼 socket에서 읽습니다.

    인자:
        client: 데이터를 읽을 TCP socket입니다.
        byte_count: 읽어야 할 byte 수입니다.
    반환값:
        지정한 길이의 bytes를 반환합니다.
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
    """MQTT remaining length 필드를 읽어 정수로 변환합니다.

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


def build_publish_packet(topic, payload, retain=True):
    """QoS 0 MQTT PUBLISH packet을 생성합니다.

    인자:
        topic: 발행할 MQTT topic입니다.
        payload: 문자열 또는 bytes payload입니다.
        retain: retain flag를 설정할지 여부입니다.
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
    """socket shutdown과 close를 조용히 수행합니다.

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
