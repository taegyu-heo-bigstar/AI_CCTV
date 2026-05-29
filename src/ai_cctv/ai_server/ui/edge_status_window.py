# Edge node 상태 조회 창을 정의하는 PyQt 파일입니다.
# AI server UI에서 Edge node 모니터링 API를 호출하고 결과를 시각화합니다.
# 네트워크 요청은 별도 QThread에서 실행해 메인 UI 멈춤을 방지합니다.
# 최신 JSON 값은 표로, 최근 사용률과 배터리 잔량 변화는 선 그래프로 표시합니다.

"""Edge node 상태 조회 PyQt 창입니다."""

from datetime import datetime

from PyQt5.QtCore import QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..monitoring.resource_monitor_client import request_resource_usage


class ResourceMonitorRequestWorker(QThread):
    """Edge node 모니터링 API 요청을 백그라운드에서 수행합니다.

    인자:
        없음.
    반환값:
        ResourceMonitorRequestWorker 인스턴스를 반환합니다.
    """

    result_ready = pyqtSignal(dict)
    error_ready = pyqtSignal(str)

    def run(self):
        """Edge node 자원 사용률을 요청하고 결과 신호를 발생시킵니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            self.result_ready.emit(request_resource_usage())
        except Exception as error:
            self.error_ready.emit(str(error))


class ResourceLineGraph(QWidget):
    """자원 사용률의 시간 흐름을 선 그래프로 표시합니다.

    인자:
        parent: 부모 PyQt 위젯입니다.
    반환값:
        ResourceLineGraph 인스턴스를 반환합니다.
    """

    def __init__(self, parent=None):
        """그래프 상태와 표시할 샘플 목록을 초기화합니다.

        인자:
            parent: 부모 PyQt 위젯입니다.
        반환값:
            없음.
        """

        super().__init__(parent)
        self.samples = []
        self.max_samples = 60
        self.series = [
            ("cpu_total", "CPU", QColor("#38bdf8")),
            ("memory_total", "Memory", QColor("#22c55e")),
            ("process_cpu", "Process CPU", QColor("#facc15")),
            ("process_memory", "Process Memory", QColor("#f97316")),
            ("battery_remaining", "Battery", QColor("#a78bfa")),
        ]
        self.setMinimumHeight(260)

    def sizeHint(self):
        """그래프 위젯의 기본 권장 크기를 반환합니다.

        인자:
            없음.
        반환값:
            QSize 객체를 반환합니다.
        """

        return QSize(780, 280)

    def append_sample(self, resource_usage):
        """자원 사용률 JSON에서 그래프 샘플을 추출해 누적합니다.

        인자:
            resource_usage: Edge node 모니터링 API가 반환한 JSON 딕셔너리입니다.
        반환값:
            없음.
        """

        sample = {
            "time": datetime.now(),
            "cpu_total": self._read_percent(resource_usage, "cpu", "total_percent"),
            "memory_total": self._read_percent(
                resource_usage, "memory", "total_percent"
            ),
            "process_cpu": self._read_percent(
                resource_usage, "process", "cpu_percent"
            ),
            "process_memory": self._read_percent(
                resource_usage, "process", "memory_percent"
            ),
            "battery_remaining": self._read_percent(
                resource_usage, "power", "battery_remaining_percent"
            ),
        }
        self.samples.append(sample)
        if len(self.samples) > self.max_samples:
            self.samples = self.samples[-self.max_samples :]
        self.update()

    def _read_percent(self, resource_usage, section_name, field_name):
        """중첩 JSON에서 백분율 값을 안전하게 읽습니다.

        인자:
            resource_usage: Edge node 모니터링 API가 반환한 JSON 딕셔너리입니다.
            section_name: 값을 읽을 상위 키 이름입니다.
            field_name: 값을 읽을 하위 키 이름입니다.
        반환값:
            float 형태의 백분율 값을 반환합니다.
        """

        value = resource_usage.get(section_name, {}).get(field_name, 0.0)
        if value is None:
            return 0.0
        return float(value)

    def paintEvent(self, event):
        """위젯 영역에 작업 관리자 스타일의 선 그래프를 그립니다.

        인자:
            event: PyQt paint 이벤트 객체입니다.
        반환값:
            없음.
        """

        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#0f172a"))

        graph_rect = self.rect().adjusted(56, 34, -24, -42)
        self._draw_grid(painter, graph_rect)
        self._draw_legend(painter)

        if len(self.samples) < 2:
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(graph_rect, Qt.AlignCenter, "Waiting for samples...")
            return

        for key, _label, color in self.series:
            self._draw_series(painter, graph_rect, key, color)

    def _draw_grid(self, painter, graph_rect):
        """그래프 배경 격자와 축 눈금을 그립니다.

        인자:
            painter: 현재 위젯에 그림을 그리는 QPainter입니다.
            graph_rect: 실제 그래프를 그릴 사각 영역입니다.
        반환값:
            없음.
        """

        painter.setPen(QPen(QColor("#334155"), 1))
        for index in range(6):
            y = graph_rect.top() + graph_rect.height() * index / 5
            painter.drawLine(graph_rect.left(), int(y), graph_rect.right(), int(y))
            value = 100 - index * 20
            painter.setPen(QColor("#94a3b8"))
            painter.drawText(8, int(y) + 5, f"{value}%")
            painter.setPen(QPen(QColor("#334155"), 1))

        for index in range(6):
            x = graph_rect.left() + graph_rect.width() * index / 5
            painter.drawLine(int(x), graph_rect.top(), int(x), graph_rect.bottom())

        painter.setPen(QPen(QColor("#64748b"), 1))
        painter.drawRect(graph_rect)

    def _draw_legend(self, painter):
        """그래프 상단에 각 선의 의미를 표시합니다.

        인자:
            painter: 현재 위젯에 그림을 그리는 QPainter입니다.
        반환값:
            없음.
        """

        x = 58
        painter.setFont(QFont("Arial", 9))
        for _key, label, color in self.series:
            painter.setPen(QPen(color, 4))
            painter.drawLine(x, 18, x + 18, 18)
            painter.setPen(QColor("#e2e8f0"))
            painter.drawText(x + 24, 22, label)
            x += 128

    def _draw_series(self, painter, graph_rect, key, color):
        """지정한 자원 사용률 시리즈를 선으로 그립니다.

        인자:
            painter: 현재 위젯에 그림을 그리는 QPainter입니다.
            graph_rect: 실제 그래프를 그릴 사각 영역입니다.
            key: 샘플 딕셔너리에서 읽을 시리즈 키입니다.
            color: 선 색상입니다.
        반환값:
            없음.
        """

        painter.setPen(QPen(color, 2))
        last_point = None
        sample_count = len(self.samples)
        for index, sample in enumerate(self.samples):
            x = graph_rect.left() + graph_rect.width() * index / (sample_count - 1)
            percent = max(0.0, min(100.0, sample[key]))
            y = graph_rect.bottom() - graph_rect.height() * percent / 100.0
            current_point = (int(x), int(y))
            if last_point is not None:
                painter.drawLine(
                    last_point[0],
                    last_point[1],
                    current_point[0],
                    current_point[1],
                )
            last_point = current_point


class EdgeNodeStatusWindow(QDialog):
    """Edge node 자원 상태를 그래프와 표로 표시하는 창입니다.

    인자:
        parent: 부모 PyQt 위젯입니다.
    반환값:
        EdgeNodeStatusWindow 인스턴스를 반환합니다.
    """

    def __init__(self, parent=None):
        """상태 조회 창의 UI와 주기 조회 타이머를 초기화합니다.

        인자:
            parent: 부모 PyQt 위젯입니다.
        반환값:
            없음.
        """

        super().__init__(parent)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setWindowTitle("엣지 노드 상태 조회")
        self.setMinimumSize(880, 620)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self.failure_count = 0
        self.has_received_response = False
        self.connection_warning_shown = False
        self.is_monitoring_active = False
        self.request_worker = None
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(2000)
        self.refresh_timer.timeout.connect(self.request_resource_status)

        self._build_ui()

    def _build_ui(self):
        """상태 조회 창의 그래프, 표, 제어 버튼을 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        title = QLabel("엣지 노드 상태")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        self.status_label = QLabel("대기 중")
        self.status_label.setStyleSheet("color: #94a3b8; font-weight: bold;")
        self.refresh_button = QPushButton("새로고침")
        self.refresh_button.setStyleSheet(
            "background-color: #0f766e; color: white; padding: 8px 18px; "
            "border-radius: 5px; font-weight: bold;"
        )
        self.refresh_button.clicked.connect(self.request_resource_status)

        header_layout.addWidget(title)
        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_button)
        layout.addLayout(header_layout)

        graph_frame = QFrame()
        graph_frame.setStyleSheet(
            "background-color: #0f172a; border: 1px solid #334155;"
        )
        graph_layout = QVBoxLayout(graph_frame)
        self.graph = ResourceLineGraph()
        graph_layout.addWidget(self.graph)
        layout.addWidget(graph_frame)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["항목", "값"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #111827; color: #e5e7eb; "
            "gridline-color: #334155; border: 1px solid #334155; } "
            "QHeaderView::section { background-color: #1e293b; color: #f8fafc; "
            "padding: 6px; border: none; }"
        )
        self._set_table_rows(self._build_waiting_rows())
        layout.addWidget(self.table, stretch=1)

    def start_monitoring(self):
        """상태 조회 창을 열 때 즉시 조회하고 주기 갱신을 시작합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if not self.is_monitoring_active:
            self.failure_count = 0
            self.has_received_response = False
            self.connection_warning_shown = False
        self.is_monitoring_active = True
        self.request_resource_status()
        self.refresh_timer.start()

    def request_resource_status(self):
        """Edge node 상태 JSON을 백그라운드 요청으로 조회합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if self.request_worker is not None and self.request_worker.isRunning():
            return

        if not self.has_received_response or self.failure_count > 0:
            self.status_label.setText("조회중")
            self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")
        self.request_worker = ResourceMonitorRequestWorker()
        self.request_worker.result_ready.connect(self.handle_resource_status)
        self.request_worker.error_ready.connect(self.handle_resource_error)
        self.request_worker.finished.connect(self._clear_request_worker)
        self.request_worker.start()

    def handle_resource_status(self, resource_usage):
        """성공적으로 수신한 JSON을 그래프와 표에 반영합니다.

        인자:
            resource_usage: Edge node 모니터링 API가 반환한 JSON 딕셔너리입니다.
        반환값:
            없음.
        """

        if not self.is_monitoring_active:
            return

        self.failure_count = 0
        self.has_received_response = True
        self.connection_warning_shown = False
        self.status_label.setText("연결됨")
        self.status_label.setStyleSheet("color: #22c55e; font-weight: bold;")
        self.graph.append_sample(resource_usage)
        self._update_table(resource_usage)

    def handle_resource_error(self, error_message):
        """상태 조회 실패를 누적하고 3회 이상 실패하면 경고를 표시합니다.

        인자:
            error_message: 요청 실패 원인을 설명하는 문자열입니다.
        반환값:
            없음.
        """

        if not self.is_monitoring_active:
            return

        self.failure_count += 1
        if self.failure_count >= 3:
            self.status_label.setText("연결실패")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
        else:
            self.status_label.setText("조회중")
            self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")

        if self.failure_count >= 3 and not self.connection_warning_shown:
            self.connection_warning_shown = True
            QMessageBox.warning(self, "Edge node", "connection lose!")

        if not self.has_received_response:
            self._set_table_rows(self._build_waiting_rows())

    def _clear_request_worker(self):
        """완료된 요청 worker 참조를 정리합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.request_worker = None

    def _update_table(self, resource_usage):
        """최신 자원 사용률 JSON 값을 표 형태로 갱신합니다.

        인자:
            resource_usage: Edge node 모니터링 API가 반환한 JSON 딕셔너리입니다.
        반환값:
            없음.
        """

        self._set_table_rows(self._build_table_rows(resource_usage))

    def _set_table_rows(self, rows):
        """표에 표시할 행 목록을 일괄 반영합니다.

        인자:
            rows: 항목 이름과 표시 값을 담은 튜플 목록입니다.
        반환값:
            없음.
        """

        self.table.setRowCount(len(rows))
        for row_index, (name, value) in enumerate(rows):
            self.table.setItem(row_index, 0, QTableWidgetItem(name))
            self.table.setItem(row_index, 1, QTableWidgetItem(value))

    def _build_waiting_rows(self):
        """정상 응답 전이나 실패 중에도 표 형태를 유지할 대기 행을 생성합니다.

        인자:
            없음.
        반환값:
            항목 이름과 대기 값을 담은 튜플 목록을 반환합니다.
        """

        return [
            ("수집 시간", "응답 대기"),
            ("전체 CPU 사용률", "-"),
            ("전체 Memory 사용률", "-"),
            ("프로세스 ID", "-"),
            ("프로세스 이름", "-"),
            ("프로세스 CPU 사용률", "-"),
            ("프로세스 Memory 사용률", "-"),
            ("배터리 잔량", "-"),
            ("외부 전원 연결", "-"),
            ("USB-C 입력 전압", "-"),
            ("MicroUSB 입력 전압", "-"),
            ("UPS 전원 상태 원본값", "-"),
            ("UPS 읽기 상태", "응답 대기"),
        ]

    def _build_table_rows(self, resource_usage):
        """자원 사용률 JSON을 화면 표시용 행 목록으로 변환합니다.

        인자:
            resource_usage: Edge node 모니터링 API가 반환한 JSON 딕셔너리입니다.
        반환값:
            항목 이름과 표시 값을 담은 튜플 목록을 반환합니다.
        """

        cpu = resource_usage.get("cpu", {})
        memory = resource_usage.get("memory", {})
        process = resource_usage.get("process", {})
        power = resource_usage.get("power", {})
        return [
            ("수집 시간", str(resource_usage.get("collected_at", "-"))),
            ("전체 CPU 사용률", self._format_percent(cpu.get("total_percent"))),
            ("전체 Memory 사용률", self._format_percent(memory.get("total_percent"))),
            ("프로세스 ID", str(process.get("pid", "-"))),
            ("프로세스 이름", str(process.get("name", "-"))),
            ("프로세스 CPU 사용률", self._format_percent(process.get("cpu_percent"))),
            (
                "프로세스 Memory 사용률",
                self._format_percent(process.get("memory_percent")),
            ),
            ("배터리 잔량", self._format_percent(power.get("battery_remaining_percent"))),
            (
                "외부 전원 연결",
                self._format_power_connection(power.get("external_power_connected")),
            ),
            (
                "USB-C 입력 전압",
                self._format_millivolt(power.get("type_c_input_millivolt")),
            ),
            (
                "MicroUSB 입력 전압",
                self._format_millivolt(power.get("micro_usb_input_millivolt")),
            ),
            ("UPS 전원 상태 원본값", str(power.get("power_status_raw", "-"))),
            ("UPS 읽기 상태", self._format_power_status(power)),
        ]

    def _format_percent(self, value):
        """백분율 값을 소수점 한 자리 문자열로 변환합니다.

        인자:
            value: 숫자형 백분율 값입니다.
        반환값:
            백분율 표시 문자열을 반환합니다.
        """

        if value is None:
            return "-"
        return f"{float(value):.1f}%"

    def _format_millivolt(self, value):
        """밀리볼트 단위 전압 값을 화면 표시 문자열로 변환합니다.

        인자:
            value: 밀리볼트 단위 숫자 값입니다.
        반환값:
            전압 표시 문자열을 반환합니다.
        """

        if value is None:
            return "-"
        return f"{int(value)} mV"

    def _format_power_connection(self, value):
        """외부 전원 연결 여부를 한글 상태 문자열로 변환합니다.

        인자:
            value: 외부 전원 연결 여부 bool 값입니다.
        반환값:
            연결 상태 표시 문자열을 반환합니다.
        """

        if value is None:
            return "-"
        return "연결됨" if bool(value) else "미연결"

    def _format_power_status(self, power):
        """UPS 전원 상태 읽기 결과를 화면 표시 문자열로 변환합니다.

        인자:
            power: `/monitor/top` JSON의 power 딕셔너리입니다.
        반환값:
            UPS 읽기 상태 표시 문자열을 반환합니다.
        """

        if not power:
            return "-"
        if power.get("available"):
            return "정상"
        error_message = power.get("error")
        if error_message:
            return f"실패: {error_message}"
        return "실패"

    def closeEvent(self, event):
        """창이 닫힐 때 주기 조회 타이머를 중지합니다.

        인자:
            event: PyQt 닫기 이벤트 객체입니다.
        반환값:
            없음.
        """

        self.refresh_timer.stop()
        self.is_monitoring_active = False
        event.accept()
