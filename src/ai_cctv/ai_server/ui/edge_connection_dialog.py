# AI server 시작 전 Edge node 연결값을 입력받는 PyQt 대화상자입니다.
# Edge node 표준 출력 블록을 붙여넣어 RTSP, MQTT, 복구 URL 필드를 채울 수 있습니다.
# 연결 검증이 성공한 경우에만 메인 관제 창이 시작되도록 결과를 반환합니다.
# 실패 시 사용자가 값을 수정하고 다시 검증할 수 있게 같은 창에 머무릅니다.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from ..connection import (
    EdgeConnectionConfig,
    EdgeConnectionValidator,
    parse_edge_startup_text,
)


class EdgeConnectionDialog(QDialog):
    """AI server 시작 전 Edge node 연결 설정을 입력받고 검증합니다.

    인자:
        parent: 부모 PyQt 위젯입니다.
        validator: 연결 검증을 수행할 EdgeConnectionValidator 객체입니다.
    반환값:
        EdgeConnectionDialog 인스턴스를 반환합니다.
    """

    def __init__(self, parent=None, validator=None):
        """연결 입력 대화상자의 상태와 UI를 초기화합니다.

        인자:
            parent: 부모 PyQt 위젯입니다.
            validator: 연결 검증을 수행할 EdgeConnectionValidator 객체입니다.
        반환값:
            없음.
        """

        super().__init__(parent)
        self.validator = validator or EdgeConnectionValidator()
        self.connection_config = None
        self.default_config = EdgeConnectionConfig.from_environment()
        self.setWindowTitle("Edge node 연결 설정")
        self.setMinimumWidth(680)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setStyleSheet(
            "QDialog { background-color: #0f172a; color: #f8fafc; } "
            "QLineEdit, QTextEdit { background-color: #111827; color: #e5e7eb; "
            "border: 1px solid #334155; border-radius: 4px; padding: 6px; } "
            "QLabel { color: #e5e7eb; }"
        )
        self._build_ui()
        self._populate_fields(self.default_config)

    def _build_ui(self):
        """연결 입력 대화상자의 전체 UI를 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title_label = QLabel("Edge node 연결값을 입력하세요")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title_label)

        guide_label = QLabel(
            "라즈베리 파이에서 출력된 [AI_CCTV Edge Node Connection] 값을 붙여넣거나 "
            "각 필드를 직접 입력한 뒤 연결 확인을 누르세요."
        )
        guide_label.setWordWrap(True)
        guide_label.setStyleSheet("color: #94a3b8;")
        layout.addWidget(guide_label)

        self.startup_text_edit = QTextEdit()
        self.startup_text_edit.setPlaceholderText("Edge node 표준 출력 블록을 여기에 붙여넣기")
        self.startup_text_edit.setFixedHeight(120)
        layout.addWidget(self.startup_text_edit)

        parse_button = self._create_button("출력값 적용", "#0f766e")
        parse_button.clicked.connect(self.apply_startup_text)
        layout.addWidget(parse_button, alignment=Qt.AlignRight)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)
        self.rtsp_url_input = QLineEdit()
        self.mqtt_host_input = QLineEdit()
        self.mqtt_port_input = QLineEdit()
        self.mqtt_topic_input = QLineEdit()
        self.backup_recovery_url_input = QLineEdit()
        form_layout.addRow("RTSP_URL", self.rtsp_url_input)
        form_layout.addRow("MQTT_HOST", self.mqtt_host_input)
        form_layout.addRow("MQTT_PORT", self.mqtt_port_input)
        form_layout.addRow("MQTT_TOPIC", self.mqtt_topic_input)
        form_layout.addRow("BACKUP_RECOVERY_URL", self.backup_recovery_url_input)
        layout.addLayout(form_layout)

        self.status_label = QLabel("연결 확인 전입니다.")
        self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")
        layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        cancel_button = self._create_button("종료", "#475569")
        cancel_button.clicked.connect(self.reject)
        self.connect_button = self._create_button("연결 확인 후 시작", "#166534")
        self.connect_button.clicked.connect(self.validate_and_accept)
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.connect_button)
        layout.addLayout(button_layout)

    def _create_button(self, text, background_color):
        """대화상자에서 사용할 공통 버튼을 생성합니다.

        인자:
            text: 버튼에 표시할 문자열입니다.
            background_color: 버튼 배경 색상 코드입니다.
        반환값:
            QPushButton 객체를 반환합니다.
        """

        button = QPushButton(text)
        button.setStyleSheet(
            f"background-color: {background_color}; color: white; "
            "padding: 8px 18px; border-radius: 5px; font-weight: bold;"
        )
        return button

    def apply_startup_text(self):
        """붙여넣은 Edge node 표준 출력값을 입력 필드에 반영합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            config = parse_edge_startup_text(
                self.startup_text_edit.toPlainText(),
                base_config=self._read_form_config(),
            )
        except ValueError as error:
            QMessageBox.warning(self, "입력 오류", str(error))
            return

        self._populate_fields(config)
        self.status_label.setText("출력값을 입력 필드에 반영했습니다.")
        self.status_label.setStyleSheet("color: #38bdf8; font-weight: bold;")

    def validate_and_accept(self):
        """입력된 연결값을 검증하고 성공하면 대화상자를 종료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        try:
            config = self._read_form_config()
        except ValueError as error:
            QMessageBox.warning(self, "입력 오류", str(error))
            return

        self._set_pending_state()
        result = self.validator.validate(config)
        if not result.success:
            self.status_label.setText("연결 검증 실패")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            QMessageBox.warning(self, "Edge node 연결 실패", result.message())
            self.connect_button.setEnabled(True)
            return

        config.apply_environment()
        self.connection_config = config
        self.status_label.setText("연결 성공. 메인 프로그램을 시작합니다.")
        self.status_label.setStyleSheet("color: #22c55e; font-weight: bold;")
        QApplication.processEvents()
        self.accept()

    def _set_pending_state(self):
        """연결 검증 진행 중 UI 상태를 표시합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.connect_button.setEnabled(False)
        self.status_label.setText("RTSP, MQTT, 백업 복구 API 연결을 확인하는 중입니다.")
        self.status_label.setStyleSheet("color: #facc15; font-weight: bold;")
        QApplication.processEvents()

    def _read_form_config(self):
        """현재 입력 필드 값을 EdgeConnectionConfig로 변환합니다.

        인자:
            없음.
        반환값:
            EdgeConnectionConfig 인스턴스를 반환합니다.
        """

        try:
            mqtt_port = int(self.mqtt_port_input.text().strip())
        except ValueError as error:
            raise ValueError("MQTT_PORT는 정수여야 합니다.") from error

        return EdgeConnectionConfig(
            rtsp_url=self.rtsp_url_input.text().strip(),
            mqtt_host=self.mqtt_host_input.text().strip(),
            mqtt_port=mqtt_port,
            mqtt_topic=self.mqtt_topic_input.text().strip(),
            backup_recovery_url=self.backup_recovery_url_input.text().strip(),
        )

    def _populate_fields(self, config):
        """연결 설정 객체의 값을 입력 필드에 표시합니다.

        인자:
            config: 표시할 EdgeConnectionConfig 인스턴스입니다.
        반환값:
            없음.
        """

        self.rtsp_url_input.setText(config.rtsp_url)
        self.mqtt_host_input.setText(config.mqtt_host)
        self.mqtt_port_input.setText(str(config.mqtt_port))
        self.mqtt_topic_input.setText(config.mqtt_topic)
        self.backup_recovery_url_input.setText(config.backup_recovery_url)
