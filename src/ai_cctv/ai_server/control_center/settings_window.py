# AI CCTV 설정 대화상자를 정의하는 파일입니다.
# 영상 입력, VLM 사용 여부, 저장 경로와 녹화 분할 시간을 설정합니다.
# 저장소 폴더 생성은 StoragePathManager에 위임합니다.

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .storage.path_manager import StoragePathManager


class SettingsWindow(QDialog):
    """AI CCTV 실행 설정을 입력받는 PyQt 대화상자입니다.

    인자:
        parent: 부모 PyQt 위젯입니다.
        video_source: 현재 영상 입력 소스입니다.
        use_vlm: VLM 분석 사용 여부입니다.
        storage_root_path: 사용자가 선택한 저장 루트 경로입니다.
        ai_cctv_path: 실제 AI_CCTV 저장 폴더 경로입니다.
        original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
    반환값:
        SettingsWindow 인스턴스를 반환합니다.
    """

    def __init__(
        self,
        parent=None,
        video_source=0,
        use_vlm=True,
        storage_root_path="",
        ai_cctv_path="",
        original_segment_seconds=10,
    ):
        """설정 창의 초기 상태를 구성합니다.

        인자:
            parent: 부모 PyQt 위젯입니다.
            video_source: 현재 영상 입력 소스입니다.
            use_vlm: VLM 분석 사용 여부입니다.
            storage_root_path: 사용자가 선택한 저장 루트 경로입니다.
            ai_cctv_path: 실제 AI_CCTV 저장 폴더 경로입니다.
            original_segment_seconds: 원본 녹화 파일 분할 초 단위입니다.
        반환값:
            없음.
        """

        super().__init__(parent)
        self.selected_source = video_source
        self.use_vlm = use_vlm
        self.storage_root_path = storage_root_path
        self.ai_cctv_path = ai_cctv_path
        self.original_segment_seconds = original_segment_seconds
        self.storage_path_manager = StoragePathManager()

        self.setWindowTitle("설정")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setFixedSize(1100, 650)
        self.setStyleSheet(
            "background-color: #0f172a; color: #f8fafc; font-family: Arial;"
        )
        self.init_ui()

    def init_ui(self):
        """설정 창의 좌측 메뉴와 우측 페이지 영역을 구성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        menu_panel = self._create_menu_panel()
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background-color: #1e293b; border-radius: 10px;")
        self.pages.addWidget(self.create_basic_page())
        self.pages.addWidget(self.create_storage_page())

        self.btn_basic.clicked.connect(lambda: self.pages.setCurrentIndex(0))
        self.btn_storage.clicked.connect(lambda: self.pages.setCurrentIndex(1))

        main_layout.addWidget(menu_panel)
        main_layout.addWidget(self.pages, stretch=1)

    def _create_menu_panel(self):
        """설정 페이지 전환 메뉴 패널을 생성합니다.

        인자:
            없음.
        반환값:
            QFrame 객체를 반환합니다.
        """

        menu_panel = QFrame()
        menu_panel.setFixedWidth(200)
        menu_panel.setStyleSheet("background-color: #1e293b; border-radius: 10px;")

        menu_layout = QVBoxLayout(menu_panel)
        menu_layout.setSpacing(10)

        title = QLabel("설정")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        menu_layout.addWidget(title)

        self.btn_basic = self.create_menu_button("기본 설정")
        self.btn_storage = self.create_menu_button("저장 설정")
        menu_layout.addWidget(self.btn_basic)
        menu_layout.addWidget(self.btn_storage)
        menu_layout.addStretch()
        return menu_panel

    def create_menu_button(self, text):
        """설정 메뉴 버튼을 생성합니다.

        인자:
            text: 버튼에 표시할 문자열입니다.
        반환값:
            QPushButton 객체를 반환합니다.
        """

        button = QPushButton(text)
        button.setFixedHeight(45)
        button.setStyleSheet(
            "background-color: #0f172a; color: #f8fafc; "
            "border-radius: 6px; font-size: 15px; text-align: left; padding-left: 15px;"
        )
        return button

    def create_basic_page(self):
        """영상 입력과 VLM 사용 여부 설정 페이지를 생성합니다.

        인자:
            없음.
        반환값:
            QWidget 페이지 객체를 반환합니다.
        """

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("기본 설정")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("카메라 입력 방식과 VLM 사용 여부를 설정합니다.")
        desc.setStyleSheet("font-size: 15px; color: #94a3b8;")
        layout.addWidget(desc)

        input_box = QFrame()
        input_box.setStyleSheet("background-color: #0f172a; border-radius: 8px;")
        input_layout = QVBoxLayout(input_box)
        input_layout.setContentsMargins(20, 20, 20, 20)
        input_layout.setSpacing(15)

        self._add_input_controls(input_layout)
        self._add_vlm_controls(input_layout)
        layout.addWidget(input_box)
        layout.addLayout(self._create_basic_save_row())

        self.result_label = QLabel("")
        self.result_label.setStyleSheet("font-size: 14px; color: #22c55e;")
        layout.addWidget(self.result_label)
        layout.addStretch()
        return page

    def _add_input_controls(self, layout):
        """기본 설정 페이지에 영상 입력 컨트롤을 추가합니다.

        인자:
            layout: 컨트롤을 추가할 QVBoxLayout 객체입니다.
        반환값:
            없음.
        """

        mode_label = QLabel("카메라 입력 방식")
        mode_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(mode_label)

        self.radio_webcam = QRadioButton("웹캠 사용")
        self.radio_rtsp = QRadioButton("RTSP 사용")
        radio_style = "QRadioButton { font-size: 15px; color: #f8fafc; spacing: 8px; }"
        self.radio_webcam.setStyleSheet(radio_style)
        self.radio_rtsp.setStyleSheet(radio_style)

        self.input_mode_group = QButtonGroup(self)
        self.input_mode_group.addButton(self.radio_webcam)
        self.input_mode_group.addButton(self.radio_rtsp)

        layout.addWidget(self.radio_webcam)
        layout.addWidget(self._create_label("카메라 번호", left_padding=True))

        self.camera_index_input = self._create_line_edit("예: 0")
        layout.addWidget(self.camera_index_input)
        layout.addWidget(self.radio_rtsp)
        layout.addWidget(self._create_label("RTSP 주소", left_padding=True))

        self.rtsp_input = self._create_line_edit("예: rtsp://192.168.10.2:8554/stream")
        layout.addWidget(self.rtsp_input)

        if isinstance(self.selected_source, int):
            self.radio_webcam.setChecked(True)
            self.camera_index_input.setText(str(self.selected_source))
        else:
            self.radio_rtsp.setChecked(True)
            self.rtsp_input.setText(str(self.selected_source))

        self.update_input_mode()
        self.radio_webcam.toggled.connect(self.update_input_mode)
        self.radio_rtsp.toggled.connect(self.update_input_mode)

    def _add_vlm_controls(self, layout):
        """기본 설정 페이지에 VLM 사용 여부 컨트롤을 추가합니다.

        인자:
            layout: 컨트롤을 추가할 QVBoxLayout 객체입니다.
        반환값:
            없음.
        """

        vlm_label = QLabel("AI 분석")
        vlm_label.setStyleSheet("font-size: 17px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(vlm_label)

        self.vlm_checkbox = QCheckBox("VLM 영상 분석 사용")
        self.vlm_checkbox.setChecked(self.use_vlm)
        self.vlm_checkbox.setStyleSheet(
            "QCheckBox { font-size: 15px; color: #f8fafc; spacing: 8px; }"
        )
        layout.addWidget(self.vlm_checkbox)

    def _create_label(self, text, left_padding=False):
        """설정 폼 라벨을 생성합니다.

        인자:
            text: 라벨 텍스트입니다.
            left_padding: 라디오 버튼 하위 항목처럼 들여쓸지 여부입니다.
        반환값:
            QLabel 객체를 반환합니다.
        """

        label = QLabel(text)
        padding = " padding-left: 24px;" if left_padding else ""
        label.setStyleSheet(f"font-size: 15px; font-weight: bold;{padding}")
        return label

    def _create_line_edit(self, placeholder):
        """표준 스타일의 입력 필드를 생성합니다.

        인자:
            placeholder: 입력 필드 안내 문자열입니다.
        반환값:
            QLineEdit 객체를 반환합니다.
        """

        line_edit = QLineEdit()
        line_edit.setMinimumHeight(40)
        line_edit.setPlaceholderText(placeholder)
        line_edit.setStyleSheet(
            "background-color: #1e293b; color: #f8fafc; "
            "border: 1px solid #334155; border-radius: 6px; "
            "padding: 10px; font-size: 14px;"
        )
        return line_edit

    def _create_basic_save_row(self):
        """기본 설정 저장 버튼 행을 생성합니다.

        인자:
            없음.
        반환값:
            QHBoxLayout 객체를 반환합니다.
        """

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_save = QPushButton("저장")
        self.btn_save.setStyleSheet(
            "background-color: #2563eb; color: white; "
            "padding: 10px 24px; border-radius: 6px; font-weight: bold;"
        )
        self.btn_save.clicked.connect(self.save_basic_settings)
        button_layout.addWidget(self.btn_save)
        return button_layout

    def update_input_mode(self):
        """선택된 입력 방식에 맞춰 입력 필드를 활성화합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        rtsp_selected = self.radio_rtsp.isChecked()
        self.rtsp_input.setEnabled(rtsp_selected)
        self.camera_index_input.setEnabled(not rtsp_selected)

    def save_basic_settings(self):
        """기본 설정 값을 검증하고 대화상자 상태에 반영합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        self.result_label.setStyleSheet("font-size: 14px; color: #22c55e;")
        if self.radio_webcam.isChecked():
            source = self._parse_camera_index()
            if source is None:
                return
        else:
            source = self.rtsp_input.text().strip()
            if not source:
                self._show_basic_error("RTSP 주소를 입력하세요.")
                return

        self.selected_source = source
        self.use_vlm = self.vlm_checkbox.isChecked()
        self.accept()

    def _parse_camera_index(self):
        """웹캠 번호 입력값을 정수로 변환합니다.

        인자:
            없음.
        반환값:
            성공하면 정수 카메라 번호, 실패하면 None을 반환합니다.
        """

        camera_index_text = self.camera_index_input.text().strip()
        if not camera_index_text:
            self._show_basic_error("카메라 번호를 입력하세요.")
            return None
        try:
            return int(camera_index_text)
        except ValueError:
            self._show_basic_error("카메라 번호는 숫자로 입력하세요.")
            return None

    def _show_basic_error(self, message):
        """기본 설정 페이지에 오류 메시지를 표시합니다.

        인자:
            message: 표시할 오류 메시지입니다.
        반환값:
            없음.
        """

        self.result_label.setStyleSheet("font-size: 14px; color: #ef4444;")
        self.result_label.setText(message)

    def create_empty_page(self, title_text, desc_text):
        """빈 안내 페이지를 생성합니다.

        인자:
            title_text: 페이지 제목 문자열입니다.
            desc_text: 페이지 설명 문자열입니다.
        반환값:
            QWidget 페이지 객체를 반환합니다.
        """

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        desc = QLabel(desc_text)
        desc.setStyleSheet("font-size: 16px; color: #94a3b8;")
        desc.setAlignment(Qt.AlignTop)

        layout.addWidget(title)
        layout.addSpacing(20)
        layout.addWidget(desc)
        layout.addStretch()
        return page

    def create_storage_page(self):
        """저장 경로와 원본 녹화 분할 설정 페이지를 생성합니다.

        인자:
            없음.
        반환값:
            QWidget 페이지 객체를 반환합니다.
        """

        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("저장 설정")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("원본 영상과 이벤트 클립 저장 방식을 설정합니다.")
        desc.setStyleSheet("font-size: 15px; color: #94a3b8;")
        layout.addWidget(desc)

        storage_box = QFrame()
        storage_box.setStyleSheet("background-color: #0f172a; border-radius: 8px;")
        storage_layout = QVBoxLayout(storage_box)
        storage_layout.setContentsMargins(20, 20, 20, 20)
        storage_layout.setSpacing(18)

        self._add_storage_path_controls(storage_layout)
        self._add_original_segment_controls(storage_layout)
        self.storage_result_label = QLabel("")
        self.storage_result_label.setStyleSheet("font-size: 14px; color: #22c55e;")
        storage_layout.addWidget(self.storage_result_label)

        layout.addWidget(storage_box)
        layout.addLayout(self._create_storage_save_row())
        self.storage_save_result = QLabel("")
        self.storage_save_result.setStyleSheet("font-size: 14px; color: #22c55e;")
        layout.addWidget(self.storage_save_result)
        layout.addStretch()
        return page

    def _add_storage_path_controls(self, layout):
        """저장 경로 선택 컨트롤을 추가합니다.

        인자:
            layout: 컨트롤을 추가할 QVBoxLayout 객체입니다.
        반환값:
            없음.
        """

        path_label = QLabel("영상 저장 경로 설정")
        path_label.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(path_label)

        path_desc = QLabel(
            "위치를 선택하면 해당 위치에 AI_CCTV 폴더가 생성되고,\n"
            "하위 폴더로 original_records와 event_clips 폴더가 생성됩니다."
        )
        path_desc.setStyleSheet("font-size: 14px; color: #94a3b8;")
        layout.addWidget(path_desc)

        path_row = QHBoxLayout()
        self.storage_path_input = self._create_line_edit("저장 위치를 선택하세요.")
        self.storage_path_input.setReadOnly(True)
        if self.ai_cctv_path:
            self.storage_path_input.setText(self.ai_cctv_path)

        self.btn_select_storage_path = QPushButton("위치 선택")
        self.btn_select_storage_path.setMinimumHeight(40)
        self.btn_select_storage_path.setStyleSheet(
            "background-color: #2563eb; color: white; padding: 8px 18px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.btn_select_storage_path.clicked.connect(self.select_storage_path)

        path_row.addWidget(self.storage_path_input, stretch=1)
        path_row.addWidget(self.btn_select_storage_path)
        layout.addLayout(path_row)

    def _add_original_segment_controls(self, layout):
        """원본 녹화 분할 시간 라디오 버튼을 추가합니다.

        인자:
            layout: 컨트롤을 추가할 QVBoxLayout 객체입니다.
        반환값:
            없음.
        """

        original_unit_label = QLabel("원본 영상 저장 단위")
        original_unit_label.setStyleSheet(
            "font-size: 17px; font-weight: bold; margin-top: 10px;"
        )
        layout.addWidget(original_unit_label)

        self.original_10s_radio = QRadioButton("10초")
        self.original_30s_radio = QRadioButton("30초")
        self.original_1m_radio = QRadioButton("1분")
        self.original_unit_group = QButtonGroup(self)

        radio_row = QHBoxLayout()
        for radio in [
            self.original_10s_radio,
            self.original_30s_radio,
            self.original_1m_radio,
        ]:
            self.original_unit_group.addButton(radio)
            radio.setStyleSheet(
                "QRadioButton { font-size: 15px; color: #f8fafc; spacing: 8px; }"
            )
            radio_row.addWidget(radio)
        radio_row.addStretch()
        layout.addLayout(radio_row)

        if self.original_segment_seconds == 10:
            self.original_10s_radio.setChecked(True)
        elif self.original_segment_seconds == 30:
            self.original_30s_radio.setChecked(True)
        else:
            self.original_1m_radio.setChecked(True)

    def _create_storage_save_row(self):
        """저장 설정 적용 버튼 행을 생성합니다.

        인자:
            없음.
        반환값:
            QHBoxLayout 객체를 반환합니다.
        """

        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.btn_storage_save = QPushButton("적용")
        self.btn_storage_save.setStyleSheet(
            "background-color: #2563eb; color: white; padding: 10px 24px; "
            "border-radius: 6px; font-weight: bold;"
        )
        self.btn_storage_save.clicked.connect(self.save_storage_settings)
        button_layout.addWidget(self.btn_storage_save)
        return button_layout

    def select_storage_path(self):
        """사용자에게 저장 루트 경로를 선택받고 표준 폴더를 생성합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        selected_path = QFileDialog.getExistingDirectory(self, "영상 저장 위치 선택")
        if not selected_path:
            return

        storage_paths = self.storage_path_manager.ensure_paths(selected_path)
        self.storage_root_path = storage_paths.root_path
        self.ai_cctv_path = storage_paths.ai_cctv_path

        self.storage_path_input.setText(storage_paths.ai_cctv_path)
        self.storage_result_label.setText("저장 폴더가 생성되었습니다.")

    def save_storage_settings(self):
        """저장소 설정 값을 검증하고 대화상자를 완료합니다.

        인자:
            없음.
        반환값:
            없음.
        """

        if not self.ai_cctv_path:
            self.storage_save_result.setStyleSheet("font-size: 14px; color: #ef4444;")
            self.storage_save_result.setText("저장 경로를 먼저 선택하세요.")
            return

        if self.original_10s_radio.isChecked():
            self.original_segment_seconds = 10
        elif self.original_30s_radio.isChecked():
            self.original_segment_seconds = 30
        else:
            self.original_segment_seconds = 60

        self.storage_save_result.setStyleSheet("font-size: 14px; color: #22c55e;")
        self.storage_save_result.setText("저장 설정이 적용되었습니다.")
        self.accept()
