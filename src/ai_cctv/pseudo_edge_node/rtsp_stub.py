# pseudo Edge node용 RTSP 포트 stub 파일입니다.
# AI server의 Edge 연결 검증이 RTSP TCP 포트를 확인할 수 있도록 listen socket을 제공합니다.
# 실제 영상 프레임은 AI server의 pseudo synthetic frame 분기가 생성합니다.
# 일반 RTSP client가 접속하면 OPTIONS, DESCRIBE 같은 기본 요청에 200 OK를 응답합니다.

import socket
import threading


class RtspPortStub:
    """RTSP TCP 포트를 열어 pseudo Edge node의 영상 송출 포트를 흉내 냅니다.

    인자:
        host: listen할 호스트입니다.
        port: listen할 RTSP TCP 포트입니다.
        path: DESCRIBE 응답에 표시할 stream 경로입니다.
    반환값:
        RtspPortStub 인스턴스를 반환합니다.
    """

    def __init__(self, host="127.0.0.1", port=8554, path="live"):
        """RTSP stub socket 상태를 초기화합니다.

        인자:
            host: listen할 호스트입니다.
            port: listen할 RTSP TCP 포트입니다.
            path: stream 경로입니다.
        반환값:
            없음.
        """

        self.host = host
        self.port = int(port)
        self.path = path.strip("/")
        self.server_socket = None
        self.running = False
        self.thread = None

    def start(self):
        """RTSP stub listen thread를 시작합니다.

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
            name="PseudoRtspPortStub",
            daemon=True,
        )
        self.thread.start()

    def stop(self):
        """RTSP stub listen socket을 종료합니다.

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
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(timeout=2)

    def _accept_loop(self):
        """RTSP TCP 접속을 수락하고 요청 처리 thread를 생성합니다.

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

            thread = threading.Thread(
                target=self._handle_client,
                args=(client,),
                name="PseudoRtspClient",
                daemon=True,
            )
            thread.start()

    def _handle_client(self, client):
        """단일 RTSP client 요청에 최소 응답을 반환합니다.

        인자:
            client: 연결된 TCP socket입니다.
        반환값:
            없음.
        """

        with client:
            client.settimeout(1.0)
            try:
                request = client.recv(4096).decode("utf-8", errors="ignore")
            except OSError:
                return

            if not request:
                return

            cseq = extract_cseq(request)
            if request.upper().startswith("DESCRIBE"):
                response = build_describe_response(cseq, self.path)
            else:
                response = build_ok_response(cseq)

            try:
                client.sendall(response.encode("utf-8"))
            except OSError:
                return


def extract_cseq(request_text):
    """RTSP 요청에서 CSeq 값을 추출합니다.

    인자:
        request_text: client가 보낸 RTSP 요청 문자열입니다.
    반환값:
        CSeq 문자열을 반환하며 없으면 1을 반환합니다.
    """

    for line in request_text.splitlines():
        if line.lower().startswith("cseq:"):
            return line.split(":", 1)[1].strip()
    return "1"


def build_ok_response(cseq):
    """일반 RTSP 요청에 대한 200 OK 응답을 생성합니다.

    인자:
        cseq: 응답에 포함할 CSeq 값입니다.
    반환값:
        RTSP 200 OK 응답 문자열을 반환합니다.
    """

    return f"RTSP/1.0 200 OK\r\nCSeq: {cseq}\r\n\r\n"


def build_describe_response(cseq, path):
    """DESCRIBE 요청에 대한 SDP 포함 응답을 생성합니다.

    인자:
        cseq: 응답에 포함할 CSeq 값입니다.
        path: SDP에 표시할 stream 경로입니다.
    반환값:
        SDP body가 포함된 RTSP 200 OK 응답 문자열을 반환합니다.
    """

    sdp = "\r\n".join(
        [
            "v=0",
            "o=- 0 0 IN IP4 127.0.0.1",
            "s=AI CCTV Pseudo Edge",
            "t=0 0",
            "m=video 0 RTP/AVP 96",
            "a=rtpmap:96 H264/90000",
            f"a=control:{path}",
            "",
        ]
    )
    return (
        f"RTSP/1.0 200 OK\r\nCSeq: {cseq}\r\n"
        "Content-Type: application/sdp\r\n"
        f"Content-Length: {len(sdp.encode('utf-8'))}\r\n\r\n{sdp}"
    )
